"""Backend local de la Microapp búsqueda de trabajo (Flask + SQLite). Solo escucha en 127.0.0.1."""
import sys, datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, send_file, abort, session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
import db
import runner
import auth
from cv_parser import extract_text, parse_cv, suggest_orientation, catalog
from tools import export_excel

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = auth.secret_key()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=30))
app.register_blueprint(auth.bp)


@app.before_request
def guard():
    """Todo salvo la portada, los estáticos y el acceso exige sesión; fija la carpeta del usuario activo."""
    p = request.path
    db.set_user(None)
    if p == "/" or p.startswith("/static/") or p.startswith("/auth/") or p in ("/api/auth/login", "/api/auth/register", "/api/auth/providers", "/api/auth/oauth-config", "/api/auth/logout", "/api/auth/me") and request.method != "DELETE":
        if p == "/api/auth/me" and session.get("uid"):
            db.set_user(session["uid"])
        return None
    uid = session.get("uid")
    if not uid:
        return jsonify(error="no-session"), 401
    db.set_user(uid)
    db.init()
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


class _CvDir:  # carpeta de CV del usuario activo
    def __truediv__(self, x): return db.udir() / "cv" / x
    def mkdir(self, **k): (db.udir() / "cv").mkdir(**k)
    def __fspath__(self): return str(db.udir() / "cv")


CV_DIR = _CvDir()
ALLOWED = {".pdf", ".docx", ".txt", ".md"}
DEFAULT_CRITERIA = {"demo": False, "modes": ["remoto"], "zones": [], "min_salary": None, "max_salary": None, "salary_currency": "EUR",
                    "contracts": ["jornada completa"], "languages": [], "roles": [], "dealbreakers": [],
                    "min_fit": 55, "auto_apply": False, "gmail_read": False, "access": {}, "max_per_session": 20, "sites": ["LinkedIn", "InfoJobs", "Indeed"], "dedup_days": 30}


def body():
    return request.get_json(silent=True) or {}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------- CV y perfil ----------
@app.post("/api/cv")
def upload_cv():
    f = request.files.get("file")
    if not f or Path(f.filename).suffix.lower() not in ALLOWED:
        return jsonify(error="Sube un PDF, DOCX o TXT"), 400
    CV_DIR.mkdir(parents=True, exist_ok=True)
    dest = CV_DIR / ("cv_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + Path(f.filename).suffix.lower())
    f.save(dest)
    try:
        text = extract_text(dest)
    except Exception as e:  # PDF escaneado, cifrado, etc.
        return jsonify(error=f"No se pudo leer el archivo: {e}"), 422
    if len(text.strip()) < 50:
        return jsonify(error="El CV no contiene texto extraíble (¿PDF escaneado?). Rellena el perfil a mano."), 422
    profile = parse_cv(text)
    profile["cv_files"] = (db.kv_get("profile", {}) or {}).get("cv_files", []) + [dest.name]
    db.kv_set("profile", profile)
    # Solo con CV subido: preconfigura los puestos buscados según su campo/sector
    crit = {**DEFAULT_CRITERIA, **db.kv_get("criteria", {})}
    if not crit["roles"]:
        crit["roles"] = [r["role"] for r in suggest_orientation(profile)["roles"]]
        db.kv_set("criteria", crit)
    write_agent_profile()
    return jsonify(profile)


@app.post("/api/cv/build")
def build_cv():
    """Crea un CV (DOCX) con lo que el usuario escribe en el asistente. No inventa nada."""
    import docx
    d = body()
    pe, ex = d.get("personal", {}), [e for e in d.get("experiences", []) if e.get("company") or e.get("role")]
    if not pe.get("name"):
        return jsonify(error="Escribe al menos tu nombre"), 400
    doc = docx.Document()
    doc.add_heading(pe["name"], 0)
    doc.add_paragraph(" · ".join(x for x in (pe.get("email"), pe.get("phone"), pe.get("city")) if x))
    if d.get("target"):
        doc.add_paragraph(d["target"]).runs[0].bold = True
    if d.get("summary"):
        doc.add_heading("Perfil", 1)
        doc.add_paragraph(d["summary"])
    if ex:
        doc.add_heading("Experiencia", 1)
        for e in ex:
            doc.add_paragraph(f"{e.get('role', '')} — {e.get('company', '')} ({e.get('from', '')} - {e.get('to', '')})").runs[0].bold = True
            if e.get("desc"):
                doc.add_paragraph(e["desc"])
    if d.get("education") or d.get("education_title"):
        doc.add_heading("Formación", 1)
        doc.add_paragraph(" — ".join(x for x in (d.get("education"), d.get("education_title")) if x))
    if d.get("skills"):
        doc.add_heading("Habilidades", 1)
        doc.add_paragraph(", ".join(s["name"] + (f" ({s['years']} años)" if s.get("years") else "") for s in d["skills"]))
    if d.get("languages"):
        doc.add_heading("Idiomas", 1)
        doc.add_paragraph(", ".join(f"{l['name']} ({l.get('level') or '—'})" for l in d["languages"]))
    CV_DIR.mkdir(parents=True, exist_ok=True)
    dest = CV_DIR / ("cv_creado_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".docx")
    doc.save(dest)
    starts = [int(e["from"]) for e in ex if str(e.get("from", "")).isdigit()]
    old = db.kv_get("profile", {}) or {}
    profile = {"confirmed": False, "from_cv": False, "sector": d.get("sector", ""), "personal": pe, "summary": d.get("summary", ""),
               "total_years": (datetime.date.today().year - min(starts)) if starts else 0, "skills": d.get("skills", []),
               "languages": d.get("languages", []), "education": d.get("education", ""), "certifications": [],
               "work_authorization": "", "needs_sponsorship": "", "experiences": ex, "cv_files": old.get("cv_files", []) + [dest.name],
               "notes": "CV creado en el asistente con tus propias respuestas. Revisa los datos."}
    db.kv_set("profile", profile)
    return jsonify(profile)


@app.get("/api/cv/file/<name>")
def get_cv_file(name):
    return send_from_directory(CV_DIR, name, as_attachment=True)


@app.get("/api/profile")
def get_profile():
    return jsonify(db.kv_get("profile", {}))


@app.put("/api/profile")
def put_profile():
    p = body()
    db.kv_set("profile", p)
    write_agent_profile()
    return jsonify(p)


@app.get("/api/catalog")
def get_catalog():
    return jsonify(catalog())


@app.get("/api/orientation")
def orientation():
    return jsonify(suggest_orientation(db.kv_get("profile", {}) or {}))


@app.get("/api/criteria")
def get_criteria():
    return jsonify({**DEFAULT_CRITERIA, **db.kv_get("criteria", {})})


@app.put("/api/criteria")
def put_criteria():
    c = body()
    db.kv_set("criteria", c)
    write_agent_profile()
    return jsonify(c)


@app.get("/api/agent-profile")
def agent_profile():
    return write_agent_profile(), 200, {"Content-Type": "text/markdown; charset=utf-8"}


def write_agent_profile():
    """Genera data/PROFILE.md: la única fuente de hechos que lee el agente."""
    p = db.kv_get("profile", {}) or {}
    c = {**DEFAULT_CRITERIA, **db.kv_get("criteria", {})}
    pe = p.get("personal", {})
    L = ["# PROFILE (generado por la app; no editar a mano, edítalo en la app)", ""]
    L.append(f"Perfil confirmado por el usuario: {'SÍ' if p.get('confirmed') else 'NO (no postular hasta confirmar)'}")
    L += ["", "## Datos", *(f"- {k}: {pe.get(k) or '(vacío: preguntar)'}" for k in ("name", "email", "phone", "city", "linkedin"))]
    L.append(f"- Años totales de experiencia: {p.get('total_years') if p.get('total_years') is not None else '(vacío: preguntar)'}")
    L.append(f"- Autorización de trabajo: {p.get('work_authorization') or '(vacío: preguntar)'}; necesita patrocinio: {p.get('needs_sponsorship') or '(vacío: preguntar)'}")
    L.append(f"- Estudios: {p.get('education') or '(vacío)'}")
    L.append(f"- Certificaciones reales: {', '.join(p.get('certifications', [])) or 'ninguna'}")
    L += ["", "## Idiomas (nivel REAL; nunca subirlo)", *(f"- {l['name']}: {l.get('level') or '(vacío: preguntar)'}" for l in p.get("languages", []))]
    L += ["", f"## Habilidades (sector: {p.get('sector') or 'sin indicar'}; única fuente para responder 'años de experiencia'; lo que no esté aquí = 0)",
          "| Habilidad | Años | Notas |", "|---|---|---|",
          *(f"| {s['name']} | {s['years'] if s.get('years') is not None else '?'} | {s.get('notes', '')} |" for s in p.get("skills", []))]
    o = suggest_orientation(p)
    L += ["", "## Orientación de la búsqueda (derivada del CV; úsala para elegir consultas y puntuar)",
          f"- Nivel: {o['seniority']} · Sector: {o['sector'] or 'sin indicar'} · Habilidades fuertes: {', '.join(o['core_stack']) or '(sin datos)'}",
          *(f"- Puesto sugerido: {r['role']} (apoyado en {', '.join(r['skills'])}). Consultas: {'; '.join(r['queries'])}" for r in o["roles"]),
          *([f"- Descartar si el stack PRINCIPAL exigido es: {', '.join(o['avoid_main_stack'])} (salvo encaje parcial claro)"] if o["avoid_main_stack"] else []),
          f"- Idiomas del CV: {', '.join(o['languages']) or '(sin datos)'}", f"- Consejo: {o['tip']}"]
    L += ["", "## Criterios",
          f"- Puestos objetivo: {', '.join(c['roles']) or '(vacío)'}",
          f"- Modalidad (orden de preferencia): {', '.join(c['modes'])}",
          f"- Zonas: {', '.join(c['zones']) or '(vacío)'}",
          f"- Salario esperado (bruto/año): {c['min_salary'] or '?'} - {c['max_salary'] or '?'} {c['salary_currency']}. Si un formulario pide una cifra única, usa el mínimo del rango; no postules a ofertas que paguen claramente menos que el mínimo",
          f"- Contrato: {', '.join(c['contracts'])}",
          f"- Idiomas de las ofertas: {', '.join(c['languages']) or '(cualquiera compatible con mis niveles)'}",
          f"- Líneas rojas (descartar siempre): {', '.join(c['dealbreakers']) or '(ninguna definida)'}",
          f"- Postulación automática autorizada por el usuario: {'SÍ (postular solo si encaje >= mínimo)' if c.get('auto_apply') else 'NO (dejar en Pendiente y pedir aprobación por oferta con ask otro)'}",
          f"- Lectura de Gmail autorizada por el usuario: {'SÍ (solo lectura)' if c.get('gmail_read') else 'NO (no leer el correo)'}",
          f"- Encaje mínimo: {c['min_fit']} · máximo por sesión: {c['max_per_session']} · sin repetir empresa en {c['dedup_days']} días",
          f"- Portales CON sesión iniciada (los únicos donde buscar): {', '.join(x for x in c['sites'] if c['access'].get(x)) or '(ninguno)'}",
          f"- Portales elegidos SIN sesión (avisar al usuario, no buscar): {', '.join(x for x in c['sites'] if not c['access'].get(x)) or '(ninguno)'}",
          f"- CVs disponibles (carpeta data/cv): {', '.join(p.get('cv_files', [])) or '(ninguno)'}"]
    sch = [s for s in schedules() if s.get("enabled", True)]
    L += ["", "## Búsquedas programadas por el usuario (crear/actualizar como tareas programadas; cron local)",
          *(f"- {x}  ({', '.join(s['days']) or 'todos los días'} {' '.join(s['times'])})" for s in sch for x in cron_of(s)),
          *([] if sch else ["- (ninguna)"])]
    txt = "\n".join(L) + "\n"
    (db.udir() / "PROFILE.md").write_text(txt, encoding="utf-8")
    return txt


# ---------- Portales y puesta en marcha ----------
PORTALS = [
    {"name": "LinkedIn", "url": "https://www.linkedin.com/login", "note": "Solicitud sencilla"},
    {"name": "InfoJobs", "url": "https://www.infojobs.net/", "note": "Principal en España"},
    {"name": "Tecnoempleo", "url": "https://www.tecnoempleo.com/", "note": "Sector tecnológico"},
    {"name": "Indeed", "url": "https://es.indeed.com/", "note": "Puede pedir verificación"},
    {"name": "Infoempleo", "url": "https://www.infoempleo.com/", "note": ""},
    {"name": "Trabajos.com", "url": "https://www.trabajos.com/", "note": ""},
    {"name": "Get on Board", "url": "https://www.getonbrd.com/", "note": "Sector tecnológico"},
    {"name": "Manfred", "url": "https://www.getmanfred.com/", "note": "Sector tecnológico"},
    {"name": "Jooble", "url": "https://es.jooble.org/", "note": "Solo para descubrir ofertas"},
]


DEMO = "Modo demostración"
PORTALS.append({"name": DEMO, "url": "", "note": "Ofertas de ejemplo para probar sin ningún portal"})


@app.get("/api/portals")
def get_portals():
    c = criteria()
    return jsonify([{**p, "selected": p["name"] in c["sites"], "access": bool(c["access"].get(p["name"])) or p["name"] == DEMO} for p in PORTALS])


@app.post("/api/portals/<name>/connect")
def connect_portal(name):
    """Abre una ventana real del navegador del motor para que el usuario inicie sesión él mismo. No se guarda ninguna contraseña."""
    p = next((x for x in PORTALS if x["name"] == name and x["url"]), None)
    if not p:
        return jsonify(error="Portal desconocido"), 404
    uid = session["uid"]

    def done():
        db.set_user(uid)
        c = criteria()
        c["access"][name] = True
        db.kv_set("criteria", c)
    try:
        import playwright  # noqa
    except ImportError:
        return jsonify(error="Falta el motor de navegación (una sola vez): pip install playwright && playwright install chromium", code="engine"), 501
    runner.connect_portal(uid, name, p["url"], done)
    return jsonify(ok=True)


@app.patch("/api/portals/<name>")
def patch_portal(name):
    c = {**DEFAULT_CRITERIA, **db.kv_get("criteria", {})}
    d = body()
    if "access" in d:
        c["access"][name] = bool(d["access"])
    if "selected" in d:
        c["sites"] = [s for s in c["sites"] if s != name] + ([name] if d["selected"] else [])
    db.kv_set("criteria", c)
    write_agent_profile()
    return jsonify(ok=True)


@app.get("/api/setup")
def get_setup():
    return jsonify(done=bool(db.kv_get("setup_done", False)))


@app.put("/api/setup")
def put_setup():
    db.kv_set("setup_done", bool(body().get("done", True)))
    return jsonify(ok=True)


# ---------- Búsquedas programadas ----------
DOW = {"Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4, "Viernes": 5, "Sábado": 6, "Domingo": 0}


def cron_of(s):
    """Una expresión cron por hora elegida. days=[] => todos los días."""
    dow = ",".join(str(DOW[d]) for d in s.get("days", []) if d in DOW) or "*"
    out = []
    for t in s.get("times", []):
        try:
            h, m = t.split(":")
            out.append(f"{int(m)} {int(h)} * * {dow}")
        except ValueError:
            pass
    return out


DEFAULT_SCHEDULES = [{"times": ["09:00", "20:00"], "days": [], "enabled": True}]  # 2 al día por defecto


def schedules():
    return db.kv_get("schedules", DEFAULT_SCHEDULES)


@app.get("/api/schedules")
def get_schedules():
    return jsonify([{**s, "cron": cron_of(s)} for s in schedules()])


@app.put("/api/schedules")
def put_schedules():
    lst = body().get("schedules", [])
    db.kv_set("schedules", [{"times": s.get("times", []), "days": s.get("days", []), "enabled": bool(s.get("enabled", True))} for s in lst])
    write_agent_profile()
    return jsonify(ok=True)


# ---------- Motor de navegación (se instala una vez, gratis) ----------
ENGINE = {"installing": False, "log": ""}


def engine_installed():
    try:
        import importlib.util
        return importlib.util.find_spec("playwright") is not None
    except Exception:
        return False


@app.get("/api/engine/status")
def engine_status():
    return jsonify(installed=engine_installed() and not ENGINE["installing"], installing=ENGINE["installing"], log=ENGINE["log"][-300:])


@app.post("/api/engine/install")
def engine_install():
    if ENGINE["installing"]:
        return jsonify(ok=True)
    import subprocess, threading

    def work():
        ENGINE.update(installing=True, log="Instalando el motor de navegación…")
        try:
            for cmd in ([sys.executable, "-m", "pip", "install", "playwright"], [sys.executable, "-m", "playwright", "install", "chromium"]):
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=1500)
                ENGINE["log"] = (r.stdout + r.stderr)[-300:]
                if r.returncode:
                    break
        finally:
            ENGINE["installing"] = False
    threading.Thread(target=work, daemon=True).start()
    return jsonify(ok=True)


# ---------- Lanzar búsqueda (motor propio, sin Claude) ----------
def criteria():
    return {**DEFAULT_CRITERIA, **db.kv_get("criteria", {})}


def readiness():
    """Qué falta para poder lanzar una búsqueda."""
    p = db.kv_get("profile", {}) or {}
    c = criteria()
    pe = p.get("personal", {})
    ok_portal = any(c["access"].get(s) or s == DEMO for s in c["sites"])
    return [m for ok, m in [(pe.get("name"), "tu nombre"), (pe.get("email"), "tu email"), (pe.get("phone"), "tu teléfono"), (pe.get("city"), "tu provincia"),
                            (p.get("sector"), "tu sector"), (p.get("work_authorization"), "tu permiso de trabajo"), (c["roles"], "qué puestos buscas"),
                            (c["modes"], "la modalidad"), (ok_portal, "al menos un portal conectado"),
                            (p.get("confirmed"), "confirmar que tu perfil es veraz")] if not ok]


@app.get("/api/ready")
def ready():
    m = readiness()
    return jsonify(ready=not m, missing=m)


def run_row(r):
    import json as _j
    return {**r, "log": _j.loads(r["log"] or "[]")} if r else None


@app.get("/api/runs/current")
def current_run():
    r = db.rows("SELECT * FROM runs ORDER BY id DESC LIMIT 1")
    return jsonify(run_row(r[0]) if r else None)


@app.post("/api/runs")
def launch_run():
    m = readiness()
    if m:
        return jsonify(error="Falta: " + ", ".join(m)), 409
    try:
        rid = runner.start(session["uid"], criteria, readiness)
    except RuntimeError as e:
        return jsonify(error=str(e)), 409
    return jsonify(id=rid), 201


@app.post("/api/runs/<int:i>/stop")
def stop_run(i):
    runner.stop(i)
    return jsonify(ok=True)


# ---------- Postulaciones ----------
APP_FIELDS = ["date", "company", "role", "url", "portal", "fit", "state", "notes", "response", "response_date", "next_step", "cv_used"]


@app.get("/api/applications")
def list_apps():
    return jsonify(db.rows("SELECT * FROM applications ORDER BY date DESC, id DESC"))


@app.post("/api/applications")
def add_app():
    d = body()
    if not d.get("company") or not d.get("role"):
        return jsonify(error="company y role son obligatorios"), 400
    d.setdefault("date", datetime.date.today().isoformat())
    if d.get("state") and d["state"] not in db.STATES:
        return jsonify(error=f"state debe ser uno de {db.STATES}"), 400
    dup = find_duplicate(d["company"], d.get("url", ""))
    if dup and not d.get("force"):
        return jsonify(error="duplicado", duplicate=dup), 409
    cols = [k for k in APP_FIELDS if k in d]
    with db.conn() as c:
        cur = c.execute(f"INSERT INTO applications ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", [d[k] for k in cols])
    return jsonify(id=cur.lastrowid), 201


@app.patch("/api/applications/<int:i>")
def patch_app(i):
    d = {k: v for k, v in body().items() if k in APP_FIELDS}
    if d.get("state") and d["state"] not in db.STATES:
        return jsonify(error="estado inválido"), 400
    if d:
        with db.conn() as c:
            c.execute(f"UPDATE applications SET {','.join(k + '=?' for k in d)} WHERE id=?", [*d.values(), i])
    return jsonify(ok=True)


@app.delete("/api/applications/<int:i>")
def del_app(i):
    with db.conn() as c:
        c.execute("DELETE FROM applications WHERE id=?", (i,))
    return jsonify(ok=True)


def find_duplicate(company, url=""):
    days = {**DEFAULT_CRITERIA, **db.kv_get("criteria", {})}["dedup_days"]
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    r = db.rows("SELECT id,date,company,role,state FROM applications WHERE state NOT IN ('Descartada') AND "
                "((lower(company)=lower(?) AND date>=?) OR (url!='' AND url=?)) LIMIT 1", (company, since, url))
    return r[0] if r else None


@app.get("/api/applications/check")
def check_dup():
    """El agente llama aquí ANTES de abrir/postular: evita repetir empresa en N días."""
    dup = find_duplicate(request.args.get("company", ""), request.args.get("url", ""))
    return jsonify(duplicate=dup)


# ---------- Respuestas, plantillas, aprobaciones ----------
@app.get("/api/answers")
def list_answers():
    return jsonify(db.rows("SELECT * FROM answers ORDER BY id"))


@app.post("/api/answers")
def add_answer():
    d = body()
    with db.conn() as c:
        cur = c.execute("INSERT INTO answers (question,answer,source,needs_review) VALUES (?,?,?,?)",
                        (d.get("question", ""), d.get("answer", ""), d.get("source", "usuario"), int(d.get("needs_review", 0))))
    return jsonify(id=cur.lastrowid), 201


@app.put("/api/answers/<int:i>")
def put_answer(i):
    d = body()
    with db.conn() as c:
        c.execute("UPDATE answers SET question=?,answer=?,needs_review=? WHERE id=?",
                  (d.get("question", ""), d.get("answer", ""), int(d.get("needs_review", 0)), i))
    return jsonify(ok=True)


@app.delete("/api/answers/<int:i>")
def del_answer(i):
    with db.conn() as c:
        c.execute("DELETE FROM answers WHERE id=?", (i,))
    return jsonify(ok=True)


@app.get("/api/templates")
def list_templates():
    return jsonify(db.rows("SELECT * FROM templates ORDER BY name"))


@app.put("/api/templates/<name>")
def put_template(name):
    with db.conn() as c:
        c.execute("INSERT INTO templates VALUES (?,?) ON CONFLICT(name) DO UPDATE SET body=excluded.body", (name, body().get("body", "")))
    return jsonify(ok=True)


APPROVAL_KINDS = {"postular": "Permiso para postular", "consent_ia": "Consentimiento de entrevista con IA", "dato_nuevo": "Dato nuevo / pregunta sin respuesta",
                  "mensaje_reclutador": "Mensaje a reclutador", "otro": "Otro"}


@app.get("/api/approvals")
def list_approvals():
    st = request.args.get("status")
    return jsonify(db.rows("SELECT * FROM approvals" + (" WHERE status=?" if st else "") + " ORDER BY id DESC", (st,) if st else ()))


@app.post("/api/approvals")
def add_approval():
    d = body()
    if d.get("kind") not in APPROVAL_KINDS:
        return jsonify(error=f"kind debe ser uno de {list(APPROVAL_KINDS)}"), 400
    with db.conn() as c:
        cur = c.execute("INSERT INTO approvals (kind,title,detail) VALUES (?,?,?)", (d["kind"], d.get("title", ""), d.get("detail", "")))
    return jsonify(id=cur.lastrowid), 201


@app.patch("/api/approvals/<int:i>")
def decide_approval(i):
    d = body()
    if d.get("status") not in ("aprobado", "rechazado", "pendiente"):
        return jsonify(error="status inválido"), 400
    with db.conn() as c:
        c.execute("UPDATE approvals SET status=?, decision_note=? WHERE id=?", (d["status"], d.get("decision_note", ""), i))
    row = db.rows("SELECT * FROM approvals WHERE id=?", (i,))
    if row and row[0]["kind"] == "postular":
        import json as _j
        info = _j.loads(row[0]["detail"] or "{}")
        if d["status"] == "aprobado":
            runner.apply_approved(session["uid"], info.get("app_id"), False)
        elif d["status"] == "rechazado":
            with db.conn() as c:
                c.execute("UPDATE applications SET state='Descartada', notes=notes||' | Rechazada por ti.' WHERE id=?", (info.get("app_id"),))
    return jsonify(ok=True)


# ---------- Estadísticas y Excel ----------
@app.get("/api/stats")
def stats():
    apps = export_excel.load_apps(db.udir() / "app.db")
    out = {"total": len(apps), "by_state": {}, "by_portal": {}, "by_fit": {}}
    for a in apps:
        out["by_state"][a["state"]] = out["by_state"].get(a["state"], 0) + 1
        if a["state"] in export_excel.SENT:
            for key, k in (("by_portal", export_excel.portal_of(a)), ("by_fit", export_excel.bucket(a["fit"]))):
                x = out[key].setdefault(k, {"sent": 0, "answered": 0})
                x["sent"] += 1
                x["answered"] += a["state"] in export_excel.REAL
    return jsonify(out)


@app.get("/api/export.xlsx")
def export_xlsx():
    path, _ = export_excel.export(db.udir() / "seguimiento_postulaciones.xlsx", db.udir() / "app.db")
    return send_file(path, as_attachment=True, download_name="seguimiento_postulaciones.xlsx")


if __name__ == "__main__":
    import threading
    threading.Thread(target=runner.scheduler, args=(db.user_ids, lambda: schedules(), criteria, readiness), daemon=True).start()
    print("Microapp en http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
