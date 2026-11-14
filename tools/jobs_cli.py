"""CLI mínima para que el agente hable con el backend local (sin dependencias, solo stdlib).
Requiere la app arrancada (python app/server.py).

  python tools/jobs_cli.py profile                      # imprime PROFILE.md (hechos + criterios)
  python tools/jobs_cli.py check "Empresa" [url]        # ¿ya postulada en los últimos N días?
  python tools/jobs_cli.py add "Empresa" "Puesto" --url U --fit 72 --state Enviada --portal LinkedIn --notes "..." --cv cv.pdf
  python tools/jobs_cli.py update ID --state Entrevista --response "..." --next "..."
  python tools/jobs_cli.py portal NAME ok|falta         # sesión del portal iniciada o caducada
  python tools/jobs_cli.py schedule                     # búsquedas programadas por el usuario (con cron)
  python tools/jobs_cli.py progress "Buscando en InfoJobs"   # avisa al usuario de lo que haces
  python tools/jobs_cli.py list                         # postulaciones registradas (JSON)
  python tools/jobs_cli.py answers                      # diccionario de respuestas (JSON)
  python tools/jobs_cli.py ask KIND "Título" "Detalle"  # KIND: consent_ia | dato_nuevo | mensaje_reclutador | otro
  python tools/jobs_cli.py approvals [pendiente|aprobado|rechazado]
  python tools/jobs_cli.py export                       # regenera el Excel
"""
import sys, json, argparse, urllib.request, urllib.error, urllib.parse

BASE = "http://127.0.0.1:5000"


def call(path, method="GET", data=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.read().decode()
    except urllib.error.URLError:
        sys.exit("La app no está arrancada: ejecuta  python app/server.py")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd, rest = a[0], a[1:]
    if cmd == "profile":
        print(call("/api/agent-profile"))
    elif cmd == "check":
        q = urllib.parse.urlencode({"company": rest[0], "url": rest[1] if len(rest) > 1 else ""})
        print(call("/api/applications/check?" + q))
    elif cmd == "add":
        p = argparse.ArgumentParser()
        p.add_argument("company"); p.add_argument("role")
        for k in ("url", "portal", "state", "notes", "cv"):
            p.add_argument("--" + k, default="")
        p.add_argument("--fit", type=int); p.add_argument("--force", action="store_true")
        n = p.parse_args(rest)
        d = {"company": n.company, "role": n.role, "url": n.url, "portal": n.portal, "state": n.state or "Pendiente",
             "notes": n.notes, "cv_used": n.cv, "fit": n.fit}
        if n.force:
            d["force"] = True
        print(call("/api/applications", "POST", d))
    elif cmd == "update":
        p = argparse.ArgumentParser()
        p.add_argument("id", type=int)
        for k in ("state", "response", "next", "notes", "response_date"):
            p.add_argument("--" + k)
        n = vars(p.parse_args(rest))
        i = n.pop("id")
        n["next_step"] = n.pop("next")
        print(call(f"/api/applications/{i}", "PATCH", {k: v for k, v in n.items() if v is not None}))
    elif cmd == "portal":  # portal NAME ok|falta  -> marca si hay sesión iniciada
        print(call("/api/portals/" + urllib.parse.quote(rest[0]), "PATCH", {"access": rest[1] == "ok"}))
    elif cmd == "schedule":  # búsquedas programadas (JSON con cron) para crear como tareas programadas
        print(call("/api/schedules"))
    elif cmd == "progress":  # progress "qué estoy haciendo" -> lo ve el usuario en pantalla
        print(call("/api/runs/current/log", "POST", {"msg": " ".join(rest)}))
    elif cmd == "list":
        print(call("/api/applications"))
    elif cmd == "answers":
        print(call("/api/answers"))
    elif cmd == "ask":
        print(call("/api/approvals", "POST", {"kind": rest[0], "title": rest[1], "detail": rest[2] if len(rest) > 2 else ""}))
    elif cmd == "approvals":
        print(call("/api/approvals" + (f"?status={rest[0]}" if rest else "")))
    elif cmd == "export":
        call("/api/export.xlsx")
        print("Excel regenerado en data/seguimiento_postulaciones.xlsx")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
