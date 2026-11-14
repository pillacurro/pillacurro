import sqlite3, json, threading
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
_tl = threading.local()  # usuario activo en este hilo: cada usuario tiene su propia carpeta y base de datos


def set_user(uid):
    _tl.uid = uid


def udir():
    uid = getattr(_tl, "uid", None)
    d = DATA / "users" / str(uid) if uid else DATA
    d.mkdir(parents=True, exist_ok=True)
    return d


def acc():
    """Base de cuentas (usuarios)."""
    DATA.mkdir(exist_ok=True)
    c = sqlite3.connect(DATA / "accounts.db")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, name TEXT, pw TEXT, provider TEXT DEFAULT 'local', provider_id TEXT, avatar TEXT DEFAULT '', created TEXT DEFAULT CURRENT_TIMESTAMP)")
    return c


def user_ids():
    with acc() as c:
        return [r["id"] for r in c.execute("SELECT id FROM users")]
STATES = ["Enviada", "Vista", "Respuesta", "Entrevista", "Oferta", "Cerrada", "Descartada", "Pendiente", "Externa"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, company TEXT, role TEXT, url TEXT, portal TEXT,
  fit INTEGER, state TEXT DEFAULT 'Pendiente', notes TEXT DEFAULT '', response TEXT DEFAULT '',
  response_date TEXT DEFAULT '', next_step TEXT DEFAULT '', cv_used TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, answer TEXT, source TEXT DEFAULT 'usuario',
  needs_review INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT DEFAULT CURRENT_TIMESTAMP, kind TEXT, title TEXT,
  detail TEXT, status TEXT DEFAULT 'pendiente', decision_note TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, started TEXT, ended TEXT, status TEXT, log TEXT DEFAULT '[]');
CREATE TABLE IF NOT EXISTS templates (name TEXT PRIMARY KEY, body TEXT);
"""

DEFAULT_TEMPLATES = {
    "nota_personal": "Hola, equipo de {empresa}:\n\nMe interesa el puesto de {puesto} porque {motivo_real}. {experiencia_relevante}\nTengo disponibilidad {disponibilidad}. Quedo a su disposición.\n\n{nombre}",
    "correo_reclutador": "Asunto: Candidatura {puesto}\n\nHola {contacto}:\n\nMe pongo en contacto por la oferta de {puesto}. Adjunto mi CV. {experiencia_relevante}\n\nSaludos,\n{nombre}",
    "seguimiento_7_dias": "Hola {contacto}:\n\nEscribí hace una semana por el puesto de {puesto} y sigo interesado/a. ¿Hay novedades sobre el proceso?\n\nGracias,\n{nombre}",
    "agradecimiento_entrevista": "Hola {contacto}:\n\nGracias por la conversación de hoy sobre {puesto}. Confirmo mi interés por {motivo_real}. Quedo atento/a a los siguientes pasos.\n\n{nombre}",
}
# (pregunta, respuesta, origen, requiere_revision)
DEFAULT_ANSWERS = [
    ("Años de experiencia en una tecnología que NO está en el perfil", "0 (sin experiencia profesional)", "regla", 0),
    ("¿Tiene experiencia con X? (X no está en el perfil)", "No", "regla", 0),
    ("Nivel de idioma", "El nivel real del perfil; nunca subirlo. Si la oferta exige más, descartar.", "regla", 0),
    ("Disponibilidad para incorporarse", "", "pendiente de rellenar", 1),
    ("Expectativa salarial (cifra única)", "", "pendiente de rellenar", 1),
    ("¿Autorizado/a a trabajar en el país de la oferta?", "", "pendiente de rellenar", 1),
]


def conn():
    c = sqlite3.connect(udir() / "app.db")
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        for k, v in DEFAULT_TEMPLATES.items():
            c.execute("INSERT OR IGNORE INTO templates VALUES (?,?)", (k, v))
        if not c.execute("SELECT 1 FROM answers LIMIT 1").fetchone():
            c.executemany("INSERT INTO answers (question,answer,source,needs_review) VALUES (?,?,?,?)", DEFAULT_ANSWERS)


def kv_get(key, default=None):
    with conn() as c:
        r = c.execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return json.loads(r["v"]) if r else default


def kv_set(key, value):
    with conn() as c:
        c.execute("INSERT INTO kv VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                  (key, json.dumps(value, ensure_ascii=False)))


def rows(sql, args=()):
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]
