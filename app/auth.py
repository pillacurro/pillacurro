"""Cuentas de usuario: registro/inicio de sesión locales y con Google o LinkedIn (OpenID Connect).
Cada usuario tiene su carpeta data/users/<id>/ (BD, CV, navegador). Las claves OAuth las pone quien instala la app
(data/oauth.json o variables de entorno); sin ellas, los botones de Google/LinkedIn salen desactivados."""
import json, os, re, secrets, shutil, urllib.parse, urllib.request
from pathlib import Path
from flask import Blueprint, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import db

bp = Blueprint("auth", __name__)
PROVIDERS = {
    "google": dict(auth="https://accounts.google.com/o/oauth2/v2/auth", token="https://oauth2.googleapis.com/token",
                   info="https://openidconnect.googleapis.com/v1/userinfo", scope="openid email profile"),
    "linkedin": dict(auth="https://www.linkedin.com/oauth/v2/authorization", token="https://www.linkedin.com/oauth/v2/accessToken",
                     info="https://api.linkedin.com/v2/userinfo", scope="openid profile email"),
}


def secret_key():
    if os.environ.get("PILLACURRO_SECRET"):
        return os.environ["PILLACURRO_SECRET"]
    f = db.DATA / "secret.key"
    db.DATA.mkdir(exist_ok=True)
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


def cfg(p):
    f = db.DATA / "oauth.json"
    j = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    j = j.get(p, {})
    cid = os.environ.get(f"PILLACURRO_{p.upper()}_CLIENT_ID") or j.get("client_id")
    sec = os.environ.get(f"PILLACURRO_{p.upper()}_CLIENT_SECRET") or j.get("client_secret")
    return (cid, sec) if cid and sec else None


def public(u):
    return {"id": u["id"], "email": u["email"], "name": u["name"], "provider": u["provider"], "avatar": u["avatar"]}


def login_user(uid):
    session.clear()
    session["uid"] = uid
    session.permanent = True
    db.set_user(uid)
    db.init()


def adopt_legacy(uid):
    """La primera cuenta hereda los datos del modo anterior (sin usuarios): BD y CV de data/."""
    old = db.DATA / "app.db"
    if old.exists() and len(db.user_ids()) == 1:
        dest = db.DATA / "users" / str(uid)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), dest / "app.db")
        if (db.DATA / "cv").exists():
            shutil.move(str(db.DATA / "cv"), dest / "cv")
        for n in ("PROFILE.md", "seguimiento_postulaciones.xlsx"):
            if (db.DATA / n).exists():
                shutil.move(str(db.DATA / n), dest / n)


def create_user(email, name, pw=None, provider="local", pid=None, avatar=""):
    with db.acc() as c:
        cur = c.execute("INSERT INTO users (email,name,pw,provider,provider_id,avatar) VALUES (?,?,?,?,?,?)",
                        (email.lower(), name, generate_password_hash(pw) if pw else None, provider, pid, avatar))
        uid = cur.lastrowid
    adopt_legacy(uid)
    db.set_user(uid)
    db.init()
    if not db.kv_get("profile"):
        db.kv_set("profile", {"confirmed": False, "from_cv": False, "personal": {"name": name, "email": email.lower()},
                              "skills": [], "languages": [], "source": provider})
    return uid


@bp.get("/api/auth/providers")
def providers():
    return jsonify({**{p: bool(cfg(p)) for p in PROVIDERS}, "online": os.environ.get("PILLACURRO_ONLINE") == "1"})


@bp.post("/api/auth/oauth-config")
def oauth_config():
    """Guarda las claves OAuth de Google/LinkedIn (solo si aún no hay cuentas o ya has iniciado sesión)."""
    if db.user_ids() and not session.get("uid"):
        return jsonify(error="Inicia sesión para cambiar esto"), 401
    d = request.get_json(silent=True) or {}
    p, cid, sec = d.get("provider"), str(d.get("client_id", "")).strip(), str(d.get("client_secret", "")).strip()
    if p not in PROVIDERS or not cid or not sec:
        return jsonify(error="Rellena el ID y la clave secreta"), 400
    f = db.DATA / "oauth.json"
    j = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    j[p] = {"client_id": cid, "client_secret": sec}
    db.DATA.mkdir(exist_ok=True)
    f.write_text(json.dumps(j), encoding="utf-8")
    return jsonify(ok=True)


@bp.get("/api/auth/me")
def me():
    uid = session.get("uid")
    with db.acc() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone() if uid else None
    return (jsonify(public(u)), 200) if u else (jsonify(error="no-session"), 401)


@bp.post("/api/auth/register")
def register():
    d = request.get_json(silent=True) or {}
    email, pw, name = str(d.get("email", "")).strip().lower(), str(d.get("password", "")), str(d.get("name", "")).strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify(error="Escribe un email válido"), 400
    if len(pw) < 8:
        return jsonify(error="La contraseña debe tener al menos 8 caracteres"), 400
    with db.acc() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            return jsonify(error="Ese email ya tiene cuenta. Inicia sesión."), 409
    uid = create_user(email, name or email.split("@")[0], pw)
    login_user(uid)
    return jsonify(ok=True), 201


@bp.post("/api/auth/login")
def login():
    d = request.get_json(silent=True) or {}
    with db.acc() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (str(d.get("email", "")).strip().lower(),)).fetchone()
    if not u or not u["pw"] or not check_password_hash(u["pw"], str(d.get("password", ""))):
        return jsonify(error="Email o contraseña incorrectos"), 401
    login_user(u["id"])
    return jsonify(ok=True)


@bp.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@bp.put("/api/auth/password")
def change_password():
    d = request.get_json(silent=True) or {}
    with db.acc() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (session.get("uid"),)).fetchone()
        if not u or not u["pw"] or not check_password_hash(u["pw"], str(d.get("old", ""))):
            return jsonify(error="La contraseña actual no es correcta"), 400
        if len(str(d.get("new", ""))) < 8:
            return jsonify(error="La nueva contraseña debe tener al menos 8 caracteres"), 400
        c.execute("UPDATE users SET pw=? WHERE id=?", (generate_password_hash(d["new"]), u["id"]))
    return jsonify(ok=True)


@bp.delete("/api/auth/me")
def delete_account():
    uid = session.get("uid")
    if not uid:
        return jsonify(error="no-session"), 401
    with db.acc() as c:
        c.execute("DELETE FROM users WHERE id=?", (uid,))
    shutil.rmtree(db.DATA / "users" / str(uid), ignore_errors=True)
    session.clear()
    return jsonify(ok=True)


def redirect_uri(p):
    return (os.environ.get("PILLACURRO_BASE_URL") or request.host_url.rstrip("/")) + f"/auth/{p}/callback"


@bp.get("/auth/<p>")
def oauth_start(p):
    if p not in PROVIDERS or not cfg(p):
        return redirect("/?auth_error=" + urllib.parse.quote("Ese acceso aún no está configurado"))
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    session["oauth_mode"] = "register" if request.args.get("mode") == "register" else "login"
    q = urllib.parse.urlencode({"response_type": "code", "client_id": cfg(p)[0], "redirect_uri": redirect_uri(p),
                                "scope": PROVIDERS[p]["scope"], "state": state, **({"prompt": "select_account"} if p == "google" else {})})
    return redirect(PROVIDERS[p]["auth"] + "?" + q)


def _post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    return json.load(urllib.request.urlopen(req, timeout=20))


@bp.get("/auth/gmail")
def gmail_start():
    """Pide permiso de SOLO LECTURA del correo; el usuario debe tener sesión iniciada."""
    if not session.get("uid") or not cfg("google"):
        return redirect("/")
    state = secrets.token_urlsafe(16)
    session["oauth_state"], session["oauth_purpose"] = state, "gmail"
    with db.acc() as c:
        u = c.execute("SELECT email FROM users WHERE id=?", (session["uid"],)).fetchone()
    q = urllib.parse.urlencode({"response_type": "code", "client_id": cfg("google")[0], "redirect_uri": redirect_uri("google"),
                                "scope": "openid email https://www.googleapis.com/auth/gmail.readonly", "state": state,
                                "access_type": "offline", "prompt": "consent select_account",
                                **({"login_hint": u["email"]} if u and "@sin-email" not in u["email"] else {})})
    return redirect(PROVIDERS["google"]["auth"] + "?" + q)


@bp.get("/api/gmail")
def gmail_status():
    db.set_user(session.get("uid"))
    return jsonify(connected=bool((db.kv_get("gmail") or {}).get("refresh_token")), available=bool(cfg("google")))


@bp.delete("/api/gmail")
def gmail_disconnect():
    db.set_user(session.get("uid"))
    g = db.kv_get("gmail") or {}
    if g.get("refresh_token"):
        try:
            _post("https://oauth2.googleapis.com/revoke", {"token": g["refresh_token"]})
        except Exception:
            pass
    db.kv_set("gmail", {})
    crit = db.kv_get("criteria", {}) or {}
    crit["gmail_read"] = False
    db.kv_set("criteria", crit)
    return jsonify(ok=True)


@bp.get("/auth/<p>/callback")
def oauth_callback(p):
    if p not in PROVIDERS or not cfg(p) or request.args.get("state") != session.pop("oauth_state", None) or not request.args.get("code"):
        session.pop("oauth_purpose", None)
        return redirect("/?auth_error=" + urllib.parse.quote("No se pudo iniciar sesión (acceso cancelado o caducado)"))
    if session.pop("oauth_purpose", None) == "gmail" and p == "google" and session.get("uid"):
        try:
            cid, sec = cfg("google")
            tok = _post(PROVIDERS["google"]["token"], {"grant_type": "authorization_code", "code": request.args["code"],
                                                       "redirect_uri": redirect_uri("google"), "client_id": cid, "client_secret": sec})
            db.set_user(session["uid"])
            db.kv_set("gmail", {"refresh_token": tok.get("refresh_token", ""), "scope": tok.get("scope", "")})
            return redirect("/?gmail=ok")
        except Exception as e:
            return redirect("/?gmail=error")
    try:
        cid, sec = cfg(p)
        tok = _post(PROVIDERS[p]["token"], {"grant_type": "authorization_code", "code": request.args["code"], "redirect_uri": redirect_uri(p),
                                             "client_id": cid, "client_secret": sec})
        req = urllib.request.Request(PROVIDERS[p]["info"], headers={"Authorization": "Bearer " + tok["access_token"]})
        info = json.load(urllib.request.urlopen(req, timeout=20))
    except Exception as e:
        return redirect("/?auth_error=" + urllib.parse.quote(f"Error con {p}: {e}"))
    email, pid = (info.get("email") or "").lower(), info.get("sub")
    name = info.get("name") or " ".join(x for x in (info.get("given_name"), info.get("family_name")) if x) or (email.split("@")[0] if email else "")
    with db.acc() as c:
        u = c.execute("SELECT * FROM users WHERE provider=? AND provider_id=?", (p, pid)).fetchone() or \
            (c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone() if email else None)
    mode = session.pop("oauth_mode", "login")
    if not u and mode == "login":
        return redirect("/?auth_mode=register&auth_error=" + urllib.parse.quote("No tienes cuenta todavía. Pulsa «Registrarse» para crearla."))
    uid = u["id"] if u else create_user(email or f"{p}-{pid}@sin-email.local", name, None, p, pid, info.get("picture", ""))
    login_user(uid)
    if p == "linkedin":
        pr = db.kv_get("profile", {}) or {}
        pr["linkedin_connected"] = True
        db.kv_set("profile", pr)
    return redirect("/")
