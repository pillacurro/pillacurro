"""Exporta las postulaciones (SQLite) a Excel: hojas Seguimiento, Resumen, Descartadas y Estadísticas.
Adaptado de referencia/gen_seguimiento.py: sin rutas ni datos personales; lee de la BD de la app.

Uso:  python tools/export_excel.py [salida.xlsx]     (por defecto data/seguimiento_postulaciones.xlsx)
"""
import sys, sqlite3
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "app.db"
STATES = ["Enviada", "Vista", "Respuesta", "Entrevista", "Oferta", "Cerrada", "Descartada", "Pendiente", "Externa"]
SENT = {"Enviada", "Vista", "Respuesta", "Entrevista", "Oferta", "Cerrada"}
SEEN = {"Vista", "Respuesta", "Entrevista", "Oferta", "Cerrada"}
REAL = {"Respuesta", "Entrevista", "Oferta"}
HEAD = PatternFill("solid", fgColor="1F3A5F")
COLORS = {"Enviada": "DDEBF7", "Descartada": "F2F2F2", "Pendiente": "FFF2CC", "Externa": "FCE4D6",
          "Entrevista": "C6E0B4", "Oferta": "A9D08E"}
PORTALS = [("linkedin", "LinkedIn"), ("infojobs", "InfoJobs"), ("tecnoempleo", "Tecnoempleo"), ("indeed", "Indeed"),
           ("jooble", "Jooble"), ("getonbrd", "Get on Board"), ("manfred", "Manfred"), ("mailto", "Correo directo")]


def portal_of(row):
    if row.get("portal"):
        return row["portal"]
    t = (str(row.get("url") or "") + " " + str(row.get("role") or "")).lower()
    return next((v for k, v in PORTALS if k in t), "Web empresa / otros")


def bucket(f):
    try:
        f = int(f)
    except (TypeError, ValueError):
        return "sin dato"
    return "75+" if f >= 75 else "65-74" if f >= 65 else "55-64" if f >= 55 else "<55"


def style_head(ws_row):
    for c in ws_row:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD
        c.alignment = Alignment(vertical="center", wrap_text=True)


def build_workbook(apps):
    wb = Workbook()
    ws = wb.active
    ws.title = "Seguimiento"
    ws.append(["Fecha", "Empresa", "Puesto", "Enlace", "Portal", "Encaje", "Estado", "Notas", "Respuesta de la empresa",
               "Fecha respuesta", "Siguiente paso", "CV usado"])
    for a in apps:
        ws.append([a["date"], a["company"], a["role"], a["url"], portal_of(a), a["fit"], a["state"], a["notes"],
                   a["response"], a["response_date"], a["next_step"], a["cv_used"]])
    style_head(ws[1])
    for i, w in enumerate([11, 26, 40, 36, 16, 8, 12, 60, 28, 14, 30, 22], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=c.column in (3, 8, 9, 11))
        col = COLORS.get(row[6].value)
        if col:
            row[6].fill = PatternFill("solid", fgColor=col)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    n = max(ws.max_row, 2)
    dv = DataValidation(type="list", formula1='"' + ",".join(STATES) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{n}")

    rs = wb.create_sheet("Resumen")
    rs.append(["Indicador", "Valor"])
    rs.append(["Total filas", f"=COUNTA(Seguimiento!A2:A{n})"])
    for s in STATES:
        rs.append([s, f'=COUNTIF(Seguimiento!G2:G{n},"{s}")'])
    cnt = lambda s: f'COUNTIF(Seguimiento!G2:G{n},"{s}")'
    num = "+".join(cnt(s) for s in REAL)
    den = "+".join(cnt(s) for s in SENT)
    rs.append(["Tasa de respuesta (Respuesta+Entrevista+Oferta / todas las enviadas)", f"=IFERROR(({num})/({den}),0)"])
    rs.cell(rs.max_row, 2).number_format = "0.0%"
    rs.column_dimensions["A"].width = 70
    rs.column_dimensions["B"].width = 14
    style_head(rs[1])

    ds = wb.create_sheet("Descartadas")
    ds.append(["Empresa", "Puesto", "Fecha", "Motivo"])
    seen = set()
    for a in apps:
        k = (a["company"], a["role"])
        if a["state"] == "Descartada" and k not in seen:
            seen.add(k)
            ds.append([a["company"], a["role"], a["date"], (a["notes"] or "")[:200]])
    for i, w in enumerate([30, 50, 11, 90], 1):
        ds.column_dimensions[get_column_letter(i)].width = w
    style_head(ds[1])
    ds.freeze_panes = "A2"

    st = wb.create_sheet("Estadísticas")

    def block(title, keyf):
        st.append([title, "Enviadas", "Con vista/respuesta", "Respuesta real/entrevista/oferta", "% respuesta"])
        style_head(st[st.max_row])
        agg = {}
        for a in apps:
            if a["state"] not in SENT:
                continue
            x = agg.setdefault(keyf(a), [0, 0, 0])
            x[0] += 1
            x[1] += a["state"] in SEEN
            x[2] += a["state"] in REAL
        for k, x in sorted(agg.items(), key=lambda kv: -kv[1][0]):
            st.append([k, x[0], x[1], x[2], x[2] / x[0] if x[0] else 0])
            st.cell(st.max_row, 5).number_format = "0.0%"
        st.append([])

    block("Por portal", portal_of)
    block("Por encaje", lambda a: bucket(a["fit"]))
    st.append(["Lectura: mover esfuerzo a los portales/tramos con mayor % de respuesta. Revisar cada semana."])
    st.column_dimensions["A"].width = 34
    for col in "BCDE":
        st.column_dimensions[col].width = 24
    return wb


def load_apps(db=None):
    db = db or DB
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    r = [dict(x) for x in c.execute("SELECT * FROM applications ORDER BY date, id")]
    c.close()
    return r


def export(out=None, db=None):
    db = db or DB
    out = Path(out) if out else ROOT / "data" / "seguimiento_postulaciones.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    apps = load_apps(db)
    build_workbook(apps).save(out)
    return out, len(apps)


if __name__ == "__main__":
    path, n = export(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"{n} filas -> {path}")
