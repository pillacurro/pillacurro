"""Extracción heurística de un perfil a partir del texto de un CV (PDF/DOCX/TXT) para CUALQUIER sector.
Sin servicios externos: todo local y gratuito. El resultado es un BORRADOR que el usuario confirma."""
import re, datetime
from pathlib import Path

# sector -> habilidades típicas, puestos (puesto, término de búsqueda, habilidades que lo sustentan) y palabras que delatan el sector
SECTORS = {
    "Tecnología": {
        "words": ["desarrollador", "programador", "software", "informátic", "sistemas", "ingeniero informático", "devops"],
        "skills": ["PHP", "Symfony", "Laravel", "JavaScript", "TypeScript", "Vue", "React", "Angular", "Node.js", "Python", "Java", ".NET", "C#", "Go",
                   "SQL", "MySQL", "PostgreSQL", "Oracle", "SQL Server", "MongoDB", "Docker", "Kubernetes", "AWS", "Azure", "Git", "Linux", "Windows",
                   "Active Directory", "Microsoft 365", "Jira", "Scrum", "Power BI", "ETL", "QA", "Selenium", "SAP", "Salesforce"],
        "roles": [("Desarrollador/a backend", "desarrollador", ["PHP", "Symfony", "Laravel", "Python", "Java", ".NET", "C#", "Go", "Node.js"]),
                  ("Desarrollador/a frontend", "desarrollador frontend", ["Vue", "React", "Angular", "TypeScript", "JavaScript"]),
                  ("Analista programador/a", "analista programador", ["SQL", "Oracle", "SQL Server", "MySQL", "PostgreSQL", "ETL"]),
                  ("Analista de datos", "analista de datos", ["SQL", "Power BI", "Python", "ETL"]),
                  ("Soporte técnico / Help desk", "soporte técnico", ["Windows", "Active Directory", "Microsoft 365"]),
                  ("Administrador/a de sistemas", "administrador de sistemas", ["Linux", "Windows", "Active Directory"]),
                  ("DevOps / Cloud", "devops", ["Docker", "Kubernetes", "AWS", "Azure"]),
                  ("QA / Tester", "QA tester", ["QA", "Selenium"])]},
    "Administración y finanzas": {
        "words": ["administrativ", "contab", "finanzas", "facturas", "tesorer"],
        "skills": ["Excel", "Contabilidad", "Facturación", "Nóminas", "Tesorería", "Fiscalidad", "Conciliación bancaria", "Archivo", "Atención telefónica", "SAP", "A3", "Sage"],
        "roles": [("Administrativo/a", "administrativo", ["Excel", "Facturación", "Archivo"]), ("Contable", "contable", ["Contabilidad", "Fiscalidad", "Conciliación bancaria"]),
                  ("Técnico/a de nóminas", "nóminas", ["Nóminas"]), ("Auxiliar administrativo/a", "auxiliar administrativo", ["Archivo", "Atención telefónica"]),
                  ("Asistente de dirección", "asistente de dirección", ["Atención telefónica", "Archivo"])]},
    "Comercio y ventas": {
        "words": ["ventas", "comercial", "tienda", "dependiente", "captación"],
        "skills": ["Venta consultiva", "Negociación", "CRM", "Prospección", "Captación de clientes", "Caja / TPV", "Merchandising", "Gestión de pedidos", "Atención al cliente"],
        "roles": [("Comercial / Ventas", "comercial", ["Venta consultiva", "Negociación", "Prospección", "CRM"]), ("Dependiente/a", "dependiente", ["Caja / TPV", "Merchandising", "Atención al cliente"]),
                  ("Responsable de tienda", "responsable de tienda", ["Merchandising", "Gestión de pedidos"]), ("Teleoperador/a comercial", "teleoperador comercial", ["Captación de clientes"])]},
    "Atención al cliente": {
        "words": ["atención al cliente", "call center", "teleoperador", "contact center"],
        "skills": ["Atención telefónica", "Gestión de incidencias", "Zendesk", "CRM", "Resolución de conflictos", "Chat y email", "Atención al cliente"],
        "roles": [("Atención al cliente", "atención al cliente", ["Atención al cliente", "Gestión de incidencias"]), ("Teleoperador/a", "teleoperador", ["Atención telefónica"]),
                  ("Soporte al cliente (chat/email)", "soporte al cliente", ["Zendesk", "Chat y email"]), ("Recepcionista", "recepcionista", ["Atención telefónica"])]},
    "Hostelería y turismo": {
        "words": ["hostelería", "camarer", "cocina", "hotel", "restaurante", "turismo"],
        "skills": ["Cocina", "Servicio de mesa", "Barra / bar", "Coctelería", "Recepción de hotel", "Reservas", "Gestión de eventos", "Manipulación de alimentos"],
        "roles": [("Camarero/a", "camarero", ["Servicio de mesa", "Barra / bar", "Coctelería"]), ("Cocinero/a", "cocinero", ["Cocina", "Manipulación de alimentos"]),
                  ("Recepcionista de hotel", "recepcionista hotel", ["Recepción de hotel", "Reservas"]), ("Ayudante de cocina", "ayudante de cocina", ["Cocina"]), ("Jefe/a de sala", "jefe de sala", ["Servicio de mesa", "Gestión de eventos"])]},
    "Salud y cuidados": {
        "words": ["hospital", "enfermer", "sanitari", "paciente", "clínica", "geriátric"],
        "skills": ["Enfermería", "Cuidados geriátricos", "Primeros auxilios", "Historia clínica", "Farmacia", "Fisioterapia", "Atención al paciente", "Gestión de citas"],
        "roles": [("Enfermero/a", "enfermero", ["Enfermería", "Historia clínica"]), ("Auxiliar de enfermería (TCAE)", "auxiliar de enfermería", ["Cuidados geriátricos", "Atención al paciente"]),
                  ("Fisioterapeuta", "fisioterapeuta", ["Fisioterapia"]), ("Auxiliar de farmacia", "auxiliar de farmacia", ["Farmacia"]), ("Gerocultor/a", "gerocultor", ["Cuidados geriátricos"])]},
    "Educación": {
        "words": ["docente", "colegio", "alumnos", "profesor", "maestro", "enseñanza"],
        "skills": ["Docencia", "Programación didáctica", "Gestión de aula", "Tutorías", "Educación infantil", "Educación especial", "Formación online"],
        "roles": [("Profesor/a", "profesor", ["Docencia", "Programación didáctica"]), ("Maestro/a de infantil", "maestro infantil", ["Educación infantil"]),
                  ("Formador/a", "formador", ["Formación online", "Docencia"]), ("Monitor/a", "monitor", ["Gestión de aula"]), ("Educador/a social", "educador social", ["Educación especial", "Tutorías"])]},
    "Logística y transporte": {
        "words": ["almacén", "logística", "transporte", "reparto", "mercancías"],
        "skills": ["Carretilla elevadora", "Gestión de almacén", "Picking", "Permiso de conducir C/CE", "Rutas", "Inventario", "Transporte internacional", "ERP"],
        "roles": [("Mozo/a de almacén", "mozo de almacén", ["Picking", "Gestión de almacén", "Inventario"]), ("Carretillero/a", "carretillero", ["Carretilla elevadora"]),
                  ("Conductor/a", "conductor", ["Permiso de conducir C/CE", "Rutas"]), ("Técnico/a de logística", "técnico logística", ["Transporte internacional", "ERP"]), ("Repartidor/a", "repartidor", ["Rutas"])]},
    "Construcción e industria": {
        "words": ["obra", "taller", "industria", "mantenimiento", "operario"],
        "skills": ["Soldadura", "Electricidad", "Fontanería", "Mantenimiento", "PRL", "AutoCAD", "Lectura de planos", "Control de calidad", "Carpintería", "Albañilería", "Maquinaria"],
        "roles": [("Electricista", "electricista", ["Electricidad"]), ("Soldador/a", "soldador", ["Soldadura"]), ("Técnico/a de mantenimiento", "técnico de mantenimiento", ["Mantenimiento", "Maquinaria"]),
                  ("Oficial de obra", "oficial de obra", ["Albañilería", "Lectura de planos", "PRL"]), ("Delineante", "delineante", ["AutoCAD", "Lectura de planos"]), ("Operario/a de producción", "operario de producción", ["Control de calidad", "Maquinaria"])]},
    "Marketing y comunicación": {
        "words": ["marketing", "redes sociales", "comunicación", "contenidos", "publicidad"],
        "skills": ["SEO", "SEM", "Redes sociales", "Google Analytics", "Copywriting", "Email marketing", "Community management", "Meta Ads", "Canva", "Redacción"],
        "roles": [("Community manager", "community manager", ["Redes sociales", "Community management", "Canva"]), ("Especialista SEO/SEM", "seo sem", ["SEO", "SEM", "Google Analytics"]),
                  ("Redactor/a de contenidos", "redactor contenidos", ["Redacción", "Copywriting"]), ("Marketing digital", "marketing digital", ["Email marketing", "Meta Ads"])]},
    "Diseño y creatividad": {
        "words": ["diseño", "creativ", "fotograf", "ilustraci"],
        "skills": ["Photoshop", "Illustrator", "InDesign", "Figma", "Premiere", "Diseño gráfico", "Fotografía", "Edición de vídeo", "Ilustración", "UX/UI"],
        "roles": [("Diseñador/a gráfico/a", "diseñador gráfico", ["Photoshop", "Illustrator", "InDesign", "Diseño gráfico"]), ("Diseñador/a UX/UI", "diseñador ux ui", ["Figma", "UX/UI"]),
                  ("Editor/a de vídeo", "editor de vídeo", ["Premiere", "Edición de vídeo"]), ("Fotógrafo/a", "fotógrafo", ["Fotografía"])]},
    "Recursos humanos y legal": {
        "words": ["recursos humanos", "selección de personal", "abogad", "jurídic", "derecho"],
        "skills": ["Selección de personal", "Contratos", "Derecho laboral", "Formación", "Prevención de riesgos", "Compliance", "Mediación", "Nóminas"],
        "roles": [("Técnico/a de RRHH", "recursos humanos", ["Selección de personal", "Formación", "Nóminas"]), ("Abogado/a", "abogado", ["Derecho laboral", "Contratos", "Compliance"]),
                  ("Asesor/a laboral", "asesor laboral", ["Derecho laboral", "Nóminas"]), ("Paralegal", "paralegal", ["Contratos"])]},
    "Otro": {
        "words": [],
        "skills": ["Atención al cliente", "Trabajo en equipo", "Office", "Excel", "Idiomas", "Carnet de conducir", "Limpieza", "Cuidado de personas"],
        "roles": [("Auxiliar administrativo/a", "auxiliar administrativo", ["Office", "Excel"]), ("Atención al cliente", "atención al cliente", ["Atención al cliente"]),
                  ("Operario/a / Peón", "operario", ["Trabajo en equipo"]), ("Personal de limpieza", "limpieza", ["Limpieza"]), ("Cuidador/a de personas", "cuidador", ["Cuidado de personas"])]},
}
ALIAS = {"Enfermería": r"enfermer[íiao]", "Contabilidad": r"contab", "Docencia": r"docen|enseñanza|dar clases", "Atención al cliente": r"atenci[óo]n al cliente|customer (service|support)",
         "Facturación": r"factura", "Nóminas": r"n[óo]minas?", "Cocina": r"cocin", "Fisioterapia": r"fisioterap", "Redes sociales": r"redes sociales|social media",
         "Soldadura": r"solda", "Electricidad": r"electricidad|instalaciones el[ée]ctricas", "Gestión de almacén": r"almac[ée]n", "Carretilla elevadora": r"carretilla",
         "Selección de personal": r"selecci[óo]n de personal|recruit", "Excel": r"\bexcel\b", "Office": r"\boffice\b|microsoft office"}
CASE_SENSITIVE = {"Go", "QA", "SAP", "C#", "A3"}
LEVELS = [(r"nativ|materna|native", "Nativo"), (r"\bc2\b|proficiency|biling", "C2"), (r"\bc1\b|advanced|avanzado", "C1"),
          (r"\bb2\b|upper.?intermediate", "B2"), (r"\bb1\b|intermedio|intermediate|medio", "B1"),
          (r"\ba2\b|elementary|básico|basic", "A2"), (r"\ba1\b", "A1")]
LANGS = {"Inglés": r"ingl[eé]s|english", "Español": r"espa[ñn]ol|spanish|castellano", "Francés": r"franc[eé]s|french",
         "Alemán": r"alem[aá]n|german", "Portugués": r"portugu[eé]s|portuguese", "Catalán": r"catal[aá]n|catalan",
         "Euskera": r"euskera|vasco", "Gallego": r"gallego"}


def catalog():
    return {s: {"skills": d["skills"], "roles": [r[0] for r in d["roles"]]} for s, d in SECTORS.items()}


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    if ext == ".docx":
        import docx
        return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return path.read_text(encoding="utf-8", errors="ignore")


def _total_years(text: str):
    cands = [int(m) for m in re.findall(r"(\d{1,2})\s*\+?\s*(?:años|years)", text, re.I)]
    yrs = [int(y) for y in re.findall(r"\b((?:19[89]|20[0-4])\d)\b\s*[-–—]\s*(?:(?:19|20)\d\d|actual|presente|present|hoy|now)", text, re.I)]
    if yrs:
        cands.append(datetime.date.today().year - min(yrs))
    cands = [c for c in cands if 0 < c < 45]
    return max(cands) if cands else None


def _skill_years(text: str, skill: str):
    s = ALIAS.get(skill) or re.escape(skill)
    m = re.search(rf"(?:{s})[^\n,;]{{0,25}}?(\d{{1,2}})\s*\+?\s*(?:años|years)", text, re.I) or \
        re.search(rf"(\d{{1,2}})\s*\+?\s*(?:años|years)[^\n,;]{{0,25}}?(?:{s})", text, re.I)
    return int(m.group(1)) if m else None


def _has(text: str, skill: str) -> bool:
    pat = ALIAS.get(skill) or r"(?<![\w])" + re.escape(skill) + r"(?![\w+#])"
    return bool(re.search(pat, text, 0 if skill in CASE_SENSITIVE else re.I))


def parse_cv(text: str) -> dict:
    """Perfil preconfigurado a partir del CV subido: contacto, sector, habilidades, idiomas y años."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+\d{1,3}[\s.-]?)?(?:\d[\s.-]?){9,11}", text)
    linkedin = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w%-]+", text, re.I)
    name = next((l for l in lines[:6] if 2 <= len(l.split()) <= 5 and not re.search(r"@|\d|http", l)), "")
    low = text.lower()
    hits, seen = {}, {}
    for sec, d in SECTORS.items():
        hs = [s for s in d["skills"] if _has(text, s)]
        hits[sec] = hs
        seen[sec] = len(hs) * 2 + sum(low.count(w) for w in d["words"])
    sector = max((s for s in SECTORS if s != "Otro"), key=lambda s: seen[s])
    sector = sector if seen[sector] > 0 else "Otro"
    skills, names = [], set()
    for sec in SECTORS:
        for s in hits[sec]:
            if s not in names:
                names.add(s)
                skills.append({"name": s, "years": _skill_years(text, s), "notes": ""})
    langs = []
    for lang, pat in LANGS.items():
        for l in lines:
            if re.search(pat, l, re.I) and len(l) < 80:
                langs.append({"name": lang, "level": next((v for p, v in LEVELS if re.search(p, l, re.I)), "")})
                break
    return {
        "confirmed": False, "from_cv": True, "sector": sector,
        "personal": {"name": name, "email": email.group(0) if email else "",
                     "phone": phone.group(0).strip() if phone else "", "city": "",
                     "linkedin": linkedin.group(0) if linkedin else ""},
        "summary": " ".join(lines[1:4])[:300],
        "total_years": _total_years(text),
        "skills": skills, "languages": langs,
        "education": "", "certifications": [], "work_authorization": "", "needs_sponsorship": "",
        "notes": "Borrador automático a partir de tu CV: revisa TODO. Lo que quede vacío, el agente preguntará (nunca adivina).",
    }


def suggest_orientation(profile: dict) -> dict:
    """Orienta la búsqueda hacia el campo/sector del CV. Solo si el perfil viene de un CV subido."""
    empty = {"seniority": "sin datos", "sector": "", "core_stack": [], "roles": [], "avoid_main_stack": [], "languages": [], "tip": ""}
    if not profile.get("from_cv"):
        return empty
    sector = profile.get("sector") or "Otro"
    skills = {s["name"]: (s.get("years") or 0) for s in profile.get("skills", [])}
    yrs = profile.get("total_years")
    seniority = "sin datos" if yrs is None else "junior" if yrs < 2 else "mid" if yrs < 5 else "senior"
    core = [n for n, y in sorted(skills.items(), key=lambda kv: -kv[1])][:5]
    roles = []
    for role, term, techs in SECTORS.get(sector, SECTORS["Otro"])["roles"]:
        hit = sorted((t for t in techs if t in skills), key=lambda t: -skills[t])
        score = sum(1 + min(skills[t], 10) / 5 for t in hit)
        lvl = {"junior": " junior", "senior": " senior"}.get(seniority, "")
        qs = [f"{term} {t}" for t in hit[:2]] + [f"{term}{lvl}".strip()]
        roles.append({"role": role, "score": round(score, 1), "skills": hit[:5], "queries": qs})
    roles.sort(key=lambda r: -r["score"])
    roles = [r for r in roles if r["score"] > 0] or roles[:3]
    langs_cv = [f"{l['name']} {l.get('level') or '?'}" for l in profile.get("languages", [])]
    avoid = []
    if sector == "Tecnología":
        avoid = sorted({"PHP", "Java", ".NET", "Python", "Go", "C#"} - skills.keys())
    return {"seniority": seniority, "sector": sector, "core_stack": core, "roles": roles[:4], "avoid_main_stack": avoid, "languages": langs_cv,
            "tip": ("Con poca experiencia prioriza puestos de entrada o con formación; no descartes por 'años' hasta 2." if seniority == "junior" else
                    "Prioriza ofertas de tu sector que usen tus habilidades fuertes; descarta las que exijan como principal algo que no tienes." if core else
                    "Añade tus habilidades para afinar la búsqueda.")}
