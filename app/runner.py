"""Motor de búsqueda propio de PillaCurro (sin Claude, gratuito y local).
Busca ofertas con el navegador del propio usuario (sesiones que él inicia), las puntúa 0-100 contra su perfil,
y por defecto NUNCA postula: deja cada candidatura en 'Pendientes de aprobar'. Solo con permiso explícito se envía."""
import os, re, json, time, datetime, threading, urllib.parse
from pathlib import Path
import db

STOP = {}      # run_id -> Event
ACTIVE = {}    # uid -> run_id
LAST_FIRED = {}

PORTAL_SEARCH = {  # plantilla de búsqueda y patrón de enlaces de oferta (experimental: los portales cambian su HTML)
    "LinkedIn": ("https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}&f_TPR=r86400", r"/jobs/view/"),
    "InfoJobs": ("https://www.infojobs.net/ofertas-trabajo?keyword={q}", r"/of-i"),
    "Tecnoempleo": ("https://www.tecnoempleo.com/ofertas-trabajo/?te={q}&ord=2", r"/(oferta|ofertas)-trabajo/"),
    "Indeed": ("https://es.indeed.com/jobs?q={q}&l={loc}&fromage=1", r"/(viewjob|rc/clk|pagead)"),
    "Infoempleo": ("https://www.infoempleo.com/trabajo/?q={q}", r"/ofertas-trabajo/"),
    "Trabajos.com": ("https://www.trabajos.com/ofertas-empleo?q={q}", r"/oferta"),
    "Get on Board": ("https://www.getonbrd.com/jobs?query={q}", r"/jobs/"),
    "Manfred": ("https://www.getmanfred.com/ofertas-empleo?query={q}", r"/ofertas"),
    "Jooble": ("https://es.jooble.org/trabajo-{q}", r"/desc/"),
}
MODES = {"remoto": ["remoto", "teletrabajo", "100% remoto", "remote"], "híbrido": ["híbrido", "hibrido", "hybrid"], "presencial": ["presencial", "on-site", "en oficina"]}


# ---------- registro de lo que hace el motor ----------
def add_log(run_id, msg):
    with db.conn() as c:
        row = c.execute("SELECT log FROM runs WHERE id=?", (run_id,)).fetchone()
        log = json.loads(row["log"]) if row else []
        log.append({"t": datetime.datetime.now().strftime("%H:%M:%S"), "msg": msg})
        c.execute("UPDATE runs SET log=? WHERE id=?", (json.dumps(log[-300:], ensure_ascii=False), run_id))


# ---------- puntuación 0-100 ----------
def detect_mode(text):
    t = text.lower()
    return next((m for m, ws in MODES.items() if any(w in t for w in ws)), "")


def score(profile, crit, offer):
    """Devuelve (puntos 0-100, motivos). Las líneas rojas descartan siempre."""
    text = f"{offer.get('title', '')} {offer.get('desc', '')}".lower()
    for d in crit.get("dealbreakers", []):
        key = d.lower().split(" / ")[0]
        if key and key in text:
            return 0, [f"línea roja: {d}"]
    skills = [s["name"] for s in profile.get("skills", [])]
    hits = [s for s in skills if re.search(r"(?<![\w])" + re.escape(s.lower()) + r"(?![\w])", text)]
    pts, why = 0, []
    s_skill = min(40, round(40 * len(hits) / max(3, min(len(skills), 6)))) if skills else 0
    pts += s_skill
    why.append(f"habilidades que coinciden: {', '.join(hits[:5]) or 'ninguna'}")
    title = offer.get("title", "").lower()
    role_words = {w for r in crit.get("roles", []) for w in re.split(r"[\s/()]+", r.lower()) if len(w) > 3}
    if role_words & set(re.split(r"[\s/,\-()]+", title)):
        pts += 25
        why.append("el puesto encaja con lo que buscas")
    mode = offer.get("mode") or detect_mode(text)
    modes = crit.get("modes", [])
    if mode and mode in modes:
        pts += 15 if modes.index(mode) == 0 else 10
        why.append(f"modalidad {mode}")
    elif mode:
        why.append(f"modalidad {mode} (no es tu preferida)")
    else:
        pts += 5
    zones = [z.lower() for z in crit.get("zones", [])]
    if mode == "remoto" or "toda españa" in zones or any(z in text or z in offer.get("place", "").lower() for z in zones):
        pts += 10
    sal = offer.get("salary")
    if sal is None:
        pts += 5
    elif crit.get("min_salary") and sal >= crit["min_salary"]:
        pts += 10
        why.append("el sueldo llega a tu mínimo")
    elif crit.get("min_salary"):
        why.append("el sueldo no llega a tu mínimo")
    elif sal:
        pts += 10
    return min(100, pts), why


# ---------- conectores ----------
def demo_offers(profile, crit):
    """Ofertas de ejemplo para probar el flujo completo sin ningún portal (modo demostración)."""
    roles = crit.get("roles") or ["Puesto de ejemplo"]
    sk = [s["name"] for s in profile.get("skills", [])][:4] or ["trabajo en equipo"]
    out = []
    for i, r in enumerate(roles[:3]):
        out.append({"title": r, "company": f"Empresa Demo {i + 1}", "place": "Madrid", "mode": "remoto", "salary": 28000 + i * 3000,
                    "url": f"demo://oferta/{i + 1}", "desc": f"Buscamos {r}. Valoramos {', '.join(sk)}. Incorporación inmediata."})
    out.append({"title": "Comercial a comisión", "company": "Empresa Demo 9", "place": "Valencia", "mode": "presencial", "salary": None,
                "url": "demo://oferta/9", "desc": "Trabajo solo comisión, viajar mucho."})
    return out


class Browser:
    """Navegador del propio usuario (perfil persistente: sus sesiones se guardan en su carpeta). Requiere Playwright."""
    def __init__(self, headless=True):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        self.ctx = self.pw.chromium.launch_persistent_context(str(db.udir() / "browser"), headless=headless, locale="es-ES")

    def close(self):
        try:
            self.ctx.close(); self.pw.stop()
        except Exception:
            pass


def web_search(br, portal, query, loc):
    tpl, pat = PORTAL_SEARCH[portal]
    page = br.ctx.new_page()
    try:
        page.goto(tpl.format(q=urllib.parse.quote(query), loc=urllib.parse.quote(loc)), timeout=30000)
        page.wait_for_timeout(2500)
        if re.search(r"captcha|verifica que eres|security check|cloudflare", page.content()[:6000], re.I):
            return None  # verificación anti-bot: no se salta
        offers, seen = [], set()
        for a in page.query_selector_all("a[href]")[:400]:
            href = a.get_attribute("href") or ""
            if not re.search(pat, href):
                continue
            url = urllib.parse.urljoin(page.url, href).split("?")[0]
            title = (a.inner_text() or "").strip().split("\n")[0]
            if len(title) < 6 or url in seen:
                continue
            seen.add(url)
            card = a.evaluate("e => (e.closest('li,article,div') || e).innerText").strip()[:600]
            lines = [l for l in card.split("\n") if l.strip()]
            offers.append({"title": title, "company": next((l for l in lines if l != title and len(l) < 60), ""), "place": "", "url": url,
                           "desc": card, "mode": detect_mode(card), "salary": None})
        return offers[:25]
    finally:
        page.close()


# ---------- ejecución ----------
def readiness_ok(get_ready):
    return not get_ready()


def start(uid, get_crit, get_ready, source="manual"):
    if uid in ACTIVE:
        raise RuntimeError("Ya hay una búsqueda en marcha")
    db.set_user(uid)
    with db.conn() as c:
        rid = c.execute("INSERT INTO runs (started, status, log) VALUES (?,?,?)", (datetime.datetime.now().isoformat(timespec="seconds"), "en curso", "[]")).lastrowid
    ACTIVE[uid] = rid
    STOP[rid] = threading.Event()
    threading.Thread(target=_run, args=(uid, rid, get_crit, source), daemon=True).start()
    return rid


def stop(run_id):
    if run_id in STOP:
        STOP[run_id].set()


def _run(uid, rid, get_crit, source):
    db.set_user(uid)
    ev, status = STOP[rid], "terminada"
    try:
        profile, crit = db.kv_get("profile", {}) or {}, get_crit()
        add_log(rid, "🚀 Empiezo a buscar" + (" (búsqueda programada)" if source == "programada" else ""))
        from cv_parser import suggest_orientation
        ori = suggest_orientation(profile)
        queries = [q for r in ori["roles"] for q in r["queries"][:1]] or [r.lower() for r in crit.get("roles", [])]
        queries = (queries or ["empleo"])[:4]
        loc = (crit.get("zones") or [""])[0].replace("Toda España", "España") or profile.get("personal", {}).get("city", "") or "España"
        found = kept = 0
        browser = None
        for portal in crit.get("sites", []):
            if ev.is_set():
                break
            demo = portal == "Modo demostración"
            if not demo and not crit.get("access", {}).get(portal):
                continue
            if not demo and os.environ.get("PILLACURRO_ONLINE") == "1":
                add_log(rid, f"ℹ️ {portal}: en la versión online solo funciona el modo demostración. Para portales reales usa la app en tu equipo.")
                continue
            add_log(rid, f"🌐 {'Probando con ofertas de ejemplo' if demo else 'Abriendo ' + portal}")
            offers = []
            if demo:
                offers = demo_offers(profile, crit)
            else:
                try:
                    browser = browser or Browser(headless=True)
                except Exception as e:
                    add_log(rid, f"⚠️ No puedo abrir el navegador del motor ({type(e).__name__}). Instálalo una vez: pip install playwright && playwright install chromium")
                    break
                for q in queries:
                    if ev.is_set():
                        break
                    add_log(rid, f"🔎 Buscando «{q}» en {portal}")
                    try:
                        r = web_search(browser, portal, q, loc)
                    except Exception as e:
                        add_log(rid, f"⚠️ {portal}: no pude leer la búsqueda ({type(e).__name__})"); continue
                    if r is None:
                        add_log(rid, f"🛑 {portal} pide verificación anti-bot: no la salto. Entra tú y repite más tarde."); break
                    offers += r
                    time.sleep(2)
            for o in offers:
                if ev.is_set():
                    break
                found += 1
                if _dup(o, crit):
                    continue
                pts, why = score(profile, crit, o)
                if pts < crit.get("min_fit", 55):
                    _save(o, portal, pts, "Descartada", "; ".join(why))
                    add_log(rid, f"➖ Descarto «{o['title']}» ({o['company']}): encaje {pts}")
                    continue
                if kept >= crit.get("max_per_session", 20):
                    _save(o, portal, pts, "Pendiente", "Guardada: se alcanzó el máximo de la sesión. " + "; ".join(why))
                    continue
                kept += 1
                aid = _save(o, portal, pts, "Pendiente", "; ".join(why))
                add_log(rid, f"⭐ «{o['title']}» en {o['company']}: encaje {pts}. Te pido permiso para postular.")
                with db.conn() as c:
                    c.execute("INSERT INTO approvals (kind,title,detail) VALUES (?,?,?)",
                              ("postular", f"Postular a «{o['title']}» · {o['company']} (encaje {pts})", json.dumps({"app_id": aid, "url": o["url"], "why": why}, ensure_ascii=False)))
        if browser:
            browser.close()
        add_log(rid, f"✅ Terminé: {found} ofertas vistas, {kept} esperan tu permiso para postular." if not ev.is_set() else "⏹️ Búsqueda detenida")
        if ev.is_set():
            status = "detenida"
    except Exception as e:
        status = "error"
        add_log(rid, f"⚠️ Algo falló: {type(e).__name__}: {e}")
    finally:
        with db.conn() as c:
            c.execute("UPDATE runs SET status=?, ended=? WHERE id=?", (status, datetime.datetime.now().isoformat(timespec="seconds"), rid))
        ACTIVE.pop(uid, None)
        STOP.pop(rid, None)


def _dup(o, crit):
    since = (datetime.date.today() - datetime.timedelta(days=crit.get("dedup_days", 30))).isoformat()
    return bool(db.rows("SELECT 1 FROM applications WHERE (url!='' AND url=?) OR (lower(company)=lower(?) AND company!='' AND date>=? AND state!='Descartada') LIMIT 1",
                        (o.get("url", ""), o.get("company", ""), since)))


def _save(o, portal, pts, state, notes):
    with db.conn() as c:
        return c.execute("INSERT INTO applications (date,company,role,url,portal,fit,state,notes) VALUES (?,?,?,?,?,?,?,?)",
                         (datetime.date.today().isoformat(), o.get("company", ""), o["title"], o.get("url", ""), portal, pts, state, notes)).lastrowid


# ---------- postular (solo tras aprobar) ----------
def apply_approved(uid, app_id, auto_allowed):
    """Tras la aprobación del usuario. Hoy: abre la oferta en SU navegador para que la envíe (asistido).
    El envío automático por portal llega como conector específico y exige además el permiso general de postulación automática."""
    db.set_user(uid)
    a = db.rows("SELECT * FROM applications WHERE id=?", (app_id,))
    if not a:
        return "no encontrada"
    a = a[0]
    note = (a["notes"] or "") + " | Aprobada por ti."
    if a["url"].startswith("demo://"):
        state, note = "Enviada", note + " (demostración: no se envía nada real)"
    else:
        state, note = "Pendiente", note + " Ábrela y envíala tú (envío automático: próximamente por portal)."
    with db.conn() as c:
        c.execute("UPDATE applications SET state=?, notes=? WHERE id=?", (state, note, app_id))
    return state


# ---------- conectar un portal (el usuario inicia sesión él mismo en una ventana real) ----------
def connect_portal(uid, name, url, on_done):
    def work():
        db.set_user(uid)
        try:
            br = Browser(headless=False)
        except Exception:
            return
        try:
            page = br.ctx.new_page()
            page.goto(url)
            while br.ctx.pages:  # espera a que el usuario cierre la ventana
                time.sleep(1)
        except Exception:
            pass
        finally:
            br.close()
            on_done()
    threading.Thread(target=work, daemon=True).start()


# ---------- programador interno ----------
def scheduler(get_users, get_schedules, get_crit, get_ready):
    """Cada minuto comprueba las programaciones de cada usuario (mientras la app esté abierta)."""
    DOW = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    while True:
        now = datetime.datetime.now()
        key = now.strftime("%Y-%m-%d %H:%M")
        for uid in get_users():
            try:
                db.set_user(uid)
                for s in get_schedules():
                    if not s.get("enabled", True) or now.strftime("%H:%M") not in s.get("times", []):
                        continue
                    if s.get("days") and DOW[now.weekday()] not in s["days"]:
                        continue
                    if LAST_FIRED.get(uid) == key or uid in ACTIVE:
                        continue
                    LAST_FIRED[uid] = key
                    if not get_ready():
                        start(uid, get_crit, get_ready, "programada")
            except Exception:
                pass
        time.sleep(20)
