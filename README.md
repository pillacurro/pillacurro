# PillaCurro (Microapp búsqueda de trabajo)

App **gratuita y local, sin Claude ni servicios de pago**, que busca ofertas por ti, las puntúa 0–100 contra tu perfil y **te pide permiso antes de postular** (por defecto nunca postula sola). Para cualquier persona y sector. Sin datos personales en el repositorio: todo vive en `data/` (ignorado por git).

## Flujo de usuario
1. **Cuenta**: creas una cuenta con email, **Google** o **LinkedIn** (o inicias sesión). Cada usuario tiene sus datos aislados en `data/users/<id>/`.
2. **Perfil**: subes tu CV (o el PDF de tu perfil de LinkedIn: *Más → Guardar como PDF*) y la app detecta tu sector, habilidades, idiomas y años y orienta la búsqueda a tu campo. Sin CV, un asistente te ayuda a crear uno. Lo revisas y confirmas.
3. **Criterios y portales**: puestos, modalidad, zona, salario (rango), idiomas, líneas rojas. Conectas cada portal iniciando sesión **tú** en una ventana del navegador de la app (la app nunca ve ni guarda tu contraseña).
4. **Buscar**: el botón *Lanzar búsqueda* se activa cuando tienes lo necesario (o se ejecuta solo a las horas que programes, mientras la app esté abierta). Un modal muestra lo que va haciendo.
5. **Permiso**: cada oferta que encaja aparece en *Pendientes de aprobar*. Solo si pulsas *Sí, puedes postular* se procede. Consentimientos de entrevistas con IA, datos nuevos y mensajes a reclutadores también esperan tu decisión.
6. **Seguimiento**: tabla de postulaciones con estados, estadísticas por portal y por encaje, Excel, respuestas a cuestionarios y plantillas de mensajes.

## Arquitectura
```
 Navegador (JS vanilla)  ──►  Flask (app/server.py, 127.0.0.1:5000)
                               ├─ auth.py      cuentas: email · Google · LinkedIn (OpenID Connect), sesión por cookie
                               ├─ db.py        SQLite por usuario (data/users/<id>/app.db) + data/accounts.db
                               ├─ cv_parser.py sectores, habilidades, orientación (heurística local)
                               ├─ runner.py    motor de búsqueda: Playwright (navegador del usuario) + puntuación + permisos + programador
                               └─ tools/export_excel.py
```
| Pieza | Decisión |
|---|---|
| Coste | 0 €: Python + Flask + SQLite + Playwright (libre). Sin APIs de pago. |
| Motor | Navegador propio (Playwright) con perfil persistente por usuario: sus sesiones, sin contraseñas guardadas. Se instala con un clic desde la app. |
| Postular | Por defecto **nunca**: cada candidatura pasa por *Pendientes de aprobar*. Tras tu permiso, hoy abre la oferta en tu navegador para que la envíes (asistido). El envío automático por portal llega por conectores (ver PLAN). |
| Cuentas | Hash de contraseña (werkzeug), cookie HttpOnly/SameSite. Google/LinkedIn necesitan claves OAuth de quien instala la app. |
| Anti-bot | No se salta CAPTCHA/Cloudflare: si aparece, el motor se detiene en ese portal y te avisa. |

## Arranque en local
Requisitos: Python 3.10+.
```bash
pip install -r requirements.txt
python app/server.py
```
Abre http://127.0.0.1:5000 y crea tu cuenta. En Windows también vale `run.bat`.
Si ya tenías datos del modo anterior (sin cuentas), **la primera cuenta que crees los hereda**.

### Activar Google / LinkedIn (opcional, una vez)
Crea una aplicación OAuth en [Google Cloud Console](https://console.cloud.google.com/apis/credentials) y/o en [LinkedIn Developers](https://www.linkedin.com/developers/apps) (producto *Sign In with LinkedIn using OpenID Connect*) con estas URL de redirección:
- `http://127.0.0.1:5000/auth/google/callback`
- `http://127.0.0.1:5000/auth/linkedin/callback`

Y guarda las claves en `data/oauth.json`:
```json
{"google": {"client_id": "…", "client_secret": "…"}, "linkedin": {"client_id": "…", "client_secret": "…"}}
```
(o con las variables `PILLACURRO_GOOGLE_CLIENT_ID/SECRET`, `PILLACURRO_LINKEDIN_CLIENT_ID/SECRET`). Nota: LinkedIn solo entrega nombre, email y foto; la trayectoria se obtiene del PDF de tu perfil.

### Probar sin ningún portal
En *Elegir portales* marca **Modo demostración**: genera ofertas de ejemplo y recorre todo el flujo (puntuación, permisos, registro) sin tocar ninguna web.

## Estructura
```
app/       server.py · auth.py · db.py · cv_parser.py · runner.py · static/ (index.html, app.js)
tools/     export_excel.py
agente/    (heredado) instrucciones para usar un agente de Claude en lugar del motor propio; opcional
data/      (local, ignorado por git) cuentas, BD y CV por usuario, Excel
referencia/ solo lectura; contiene datos personales: NO se publica
PLAN.md    fases y decisiones
```

## Uso responsable
La app no salta CAPTCHA ni verificaciones anti-bot, no guarda contraseñas y no postula sin permiso del usuario. Respeta las condiciones de uso de cada portal; automatizar acciones puede estar prohibido en algunos. Úsala con ritmo pausado y bajo tu responsabilidad. Licencia MIT.

## Límites conocidos
- Los selectores de cada portal cambian: la búsqueda en portales reales es **experimental** y debe afinarse conector a conector. El modo demostración valida el resto del flujo.
- Portales con verificación anti-bot (Cloudflare/CAPTCHA) no se pueden automatizar: la app lo respeta y te avisa.
- Automatizar portales puede ir contra sus condiciones de uso (p. ej. LinkedIn): úsalo con ritmo pausado y bajo tu responsabilidad.
- El extractor de CV es heurístico: da un borrador que confirmas tú.
