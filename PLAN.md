# PLAN

## Fases
**Fase 1 — MVP (hecha en la sesión 1)**: Flask+SQLite, subida de CV con extracción heurística, perfil editable/confirmable, criterios, registro de postulaciones con detección de duplicados (30 días), diccionario de respuestas, plantillas, cola de aprobaciones, estadísticas, export a Excel, `agente/CLAUDE.md` genérico, CLI `jobs_cli.py`.

**Fase 2 — Perfil y agente fiables**
- Extracción de perfil con LLM (Claude vía agente o API opcional) en lugar de regex; años por tecnología a partir de fechas de cada puesto.
- `PROFILE.md` con CV por variante (ES/EN/…) y regla "qué CV para qué oferta".
- Skill/subagente de búsqueda por portal con checklist y verificación de que el perfil está confirmado.
- Diccionario de respuestas que aprende: cada pregunta nueva resuelta por el usuario se guarda (con "revisar").
- Tests (pytest) de API y parser; CI mínima.

**Fase 3 — UX y seguimiento**
- Frontend Vue 3 (Vite) sobre la misma API; wizard inicial (CV → perfil → criterios).
- Lectura de Gmail para respuestas: conector del agente + tarea programada diaria, con actualización de estados y aviso de entrevistas.
- Tareas programadas de búsqueda (p. ej. 2 veces al día) y alertas por correo → postulación rápida (lo más valioso del proyecto real).
- Preparación de entrevistas: preguntas probables por oferta, repaso de lo postulado, notas de proceso.
- Plantillas con variables rellenadas automáticamente y vista previa.

**Fase 4 — Distribución**
- Empaquetado fácil para no técnicos (instalador / Docker / `pipx`), multiusuario local (varios perfiles), i18n (ES/EN), documentación pública.
- Limpieza final de `referencia/` y publicación.

## Principio: la app es 100 % gratuita (decisión del usuario, 2026-11-14)
- Cero costes obligatorios: código abierto, SQLite local, sin servicios de pago, sin suscripciones, sin cuotas por usuario. Búsquedas, programaciones, Excel, estadísticas y plantillas incluidos.
- Extracción del CV: heurística local gratuita por defecto. El LLM por API (pago por uso del propio usuario) es **opcional**, nunca requisito.
- Programaciones: por defecto 2 al día (09:00 y 20:00). Se ejecutan con las tareas programadas de Claude (las del plan que el usuario ya tenga) o, en Fase 2, con el programador del sistema (Programador de tareas de Windows / cron) sin coste extra.
- Hosting multiusuario (Fase 2b): solo con infraestructura gratuita o autohospedada; si alguna vez hay coste, nunca se traslada al usuario.

## Decisiones tomadas (con criterio, revisables)
| Decisión | Elegida | Motivo |
|---|---|---|
| Stack | Flask + SQLite + JS vanilla | Mínima fricción; Python lo dominas; Vue llega en Fase 3 |
| Dónde corre la búsqueda | En el agente (Claude Code + Chrome), no en el servidor | Usa las sesiones reales del usuario y evita automatizar login/CAPTCHA |
| Persistencia | SQLite en `data/` (no markdown) | Consultas, duplicados y estadísticas; el Excel es una exportación |
| Extracción de CV | Heurística local en MVP | Privacidad y cero coste; el usuario confirma todo |
| Duplicados | Misma empresa en 30 días o misma URL → bloquea (salvo `--force`) | Lección del proyecto real; configurable |
| Encaje | 0–100: stack 40, nivel/años 20, idioma 15, modalidad/zona 15, salario/contrato 10; líneas rojas descartan siempre | Reproducible y explicable |
| Defaults honestos | Tecnología ausente = "No"/0 años; idioma = nivel real; dato desconocido → pregunta, nunca inventa | Regla de oro del proyecto |
| Aprobaciones | Cola en la app; el agente no actúa sin "aprobado" | Consentimiento IA, datos nuevos y mensajes siempre del usuario |
| Seguridad | Solo 127.0.0.1, sin auth | App monousuario local; si se expone, hace falta auth (Fase 4) |
| Sin capturas | El agente lee con JS/`read_page` | Regla permanente del usuario |

## Giro de arquitectura (2026-11-14): la app NO usa Claude
- Decisión del usuario: la app busca y postula por sí misma (motor propio con Playwright), con cuentas (email/Google/LinkedIn) y sección Perfil. **Por defecto nunca postula**: pide permiso por oferta; la postulación automática solo con permiso general explícito.
- Hecho en esta versión: cuentas multiusuario con datos aislados, sección Perfil, importación del PDF de LinkedIn, motor de búsqueda + puntuación + cola de permisos + programador interno, conexión de portales con ventana real del usuario, modo demostración.
- **Siguiente (Fase 2)**: (1) conectores por portal con selectores verificados (LinkedIn Easy Apply, InfoJobs, Tecnoempleo, Indeed) y envío automático solo con permiso; (2) lectura de Gmail con OAuth propio (solo lectura); (3) cuestionarios: responder con el diccionario veraz y pedir lo que falte; (4) CV por variante; (5) tests y CI.
- Riesgos a asumir: los portales cambian su HTML y pueden prohibir la automatización en sus términos; Google/LinkedIn exigen que quien instala cree sus claves OAuth.
- `agente/` queda como alternativa opcional (agente de Claude), no como parte de la app.

## Respuestas del usuario (2026-11-14)
1. **Multiusuario**: sí. Implicación: cuentas + auth + datos aislados por usuario (Fase 2b: usuarios, login, `user_id` en todas las tablas, CVs cifrados en reposo). El agente seguirá corriendo en el equipo de cada usuario (usa SUS sesiones de portal) y hablará con la API con un token personal.
2. **LLM permitido** para extraer el CV (API de Anthropic, clave en config; consentimiento explícito del usuario antes de enviar su CV).
3. **España** primero: InfoJobs, Tecnoempleo, LinkedIn, Indeed, Infoempleo, Jooble (solo descubrir).
4. **Postulación automática solo con permiso del usuario**: ajuste `auto_apply` (hecho en Criterios, por defecto NO; el agente lo lee en PROFILE.md).

5. **Idioma**: solo español de momento (preparar textos para i18n en Fase 4).
6. **Repositorio**: se publicará. Antes: `referencia/` fuera (ya en `.gitignore`; ojo, `referencia/Kit_busqueda_empleo_portable/.git` tiene su propio historial con datos personales: no subirlo), revisar que no haya datos personales en ningún archivo, añadir LICENSE y aviso de uso responsable (no saltar CAPTCHA, respetar términos de los portales).
7. **Frontend**: migrar a Vue 3 en Fase 3.
8. **Gmail**: lectura vía conector del agente, solo con autorización explícita del usuario (ajuste en Criterios, por defecto NO; solo lectura; nunca responde sin aprobación). OAuth propio queda para cuando sea app alojada multiusuario.

## Decisiones abiertas
Ninguna por ahora.
