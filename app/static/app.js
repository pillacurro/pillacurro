const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const api = async (u, m = 'GET', b) => {
  const r = await fetch(u, { method: m, headers: b ? { 'Content-Type': 'application/json' } : {}, body: b ? JSON.stringify(b) : undefined });
  const j = await r.json().catch(() => ({})); if (r.status === 401 && j.error === 'no-session') { if (!$('#ago')) showAuth(); throw Object.assign(new Error('no-session'), { data: j }); } if (!r.ok) throw Object.assign(new Error(j.error || r.statusText), { data: j }); return j;
};
const STATES = ['Enviada', 'Vista', 'Respuesta', 'Entrevista', 'Oferta', 'Cerrada', 'Descartada', 'Pendiente', 'Externa'];
const PROV = ['Toda España', 'A Coruña', 'Álava', 'Albacete', 'Alicante', 'Almería', 'Asturias', 'Ávila', 'Badajoz', 'Barcelona', 'Burgos', 'Cáceres', 'Cádiz', 'Cantabria', 'Castellón', 'Ciudad Real', 'Córdoba', 'Cuenca', 'Girona', 'Granada', 'Guadalajara', 'Gipuzkoa', 'Huelva', 'Huesca', 'Islas Baleares', 'Jaén', 'La Rioja', 'Las Palmas', 'León', 'Lleida', 'Lugo', 'Madrid', 'Málaga', 'Murcia', 'Navarra', 'Ourense', 'Palencia', 'Pontevedra', 'Salamanca', 'S. C. Tenerife', 'Segovia', 'Sevilla', 'Soria', 'Tarragona', 'Teruel', 'Toledo', 'Valencia', 'Valladolid', 'Bizkaia', 'Zamora', 'Zaragoza'];
const ROLES = ['Desarrollador/a backend', 'Desarrollador/a frontend', 'Desarrollador/a full stack', 'Analista programador/a', 'Analista de datos', 'Soporte técnico / Help desk', 'Administrador/a de sistemas', 'DevOps / Cloud', 'QA / Tester', 'Project manager / Scrum', 'Diseñador/a UX/UI', 'Marketing digital', 'Administrativo/a', 'Atención al cliente', 'Comercial / Ventas'];
const TECH = ['PHP', 'Symfony', 'Laravel', 'JavaScript', 'TypeScript', 'Vue', 'React', 'Angular', 'Node.js', 'Python', 'Java', '.NET', 'C#', 'Go', 'SQL', 'MySQL', 'PostgreSQL', 'Oracle', 'SQL Server', 'MongoDB', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Git', 'Linux', 'Excel', 'Power BI', 'ETL', 'Windows', 'Active Directory', 'Microsoft 365', 'Jira', 'Scrum', 'Figma', 'SAP', 'Salesforce'];
const LANG = ['Español', 'Inglés', 'Francés', 'Alemán', 'Portugués', 'Catalán', 'Euskera', 'Gallego'];
const LVL = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Nativo'];
const DEAL = ['Turnos de noche', 'Solo comisión', 'Autónomo / freelance', 'Cambio de residencia', 'Guardias', 'Inglés fluido exigido', 'Viajar mucho', 'Fines de semana'];
let CAT = {};
const ALL = k => [...new Set(Object.values(CAT).flatMap(s => s[k]))];
const skillOpts = sec => (CAT[sec]?.skills || ALL('skills'));
const roleOpts = sec => (CAT[sec]?.roles || ALL('roles'));
const range = (a, b, st = 1) => Array.from({ length: Math.floor((b - a) / st) + 1 }, (_, i) => a + i * st);
const SAL = range(15000, 120000, 5000).map(x => [x, x.toLocaleString('es-ES') + ' €']);
const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const HORAS = range(6, 23).flatMap(h => ['00', '30'].map(m => String(h).padStart(2, '0') + ':' + m));
const HELP = {
  lanzar: ['Lanzar búsqueda', 'Es el botón de arrancar. Se enciende cuando ya me has contado todo lo necesario. Al pulsarlo salgo a buscar trabajo y te voy contando lo que hago.'],
  acceso: ['Tu cuenta', 'Tu cuenta es solo tuya: nadie más ve tu CV ni tus búsquedas. Puedes entrar con tu email, con Google o con LinkedIn.'],
  perfil: ['Tu perfil', 'Aquí está tu cuenta y lo que sé de ti: a qué te dedicas, qué sabes hacer y qué trabajo buscas. Puedes cambiarlo cuando quieras o cerrar sesión.'],
  estado: ['Tu resumen', 'Aquí ves cómo vas, como el marcador de un juego: si tu perfil está listo, cuántas solicitudes has mandado y si algo espera tu OK.'],
  portales: ['Los portales', 'Son las webs donde se publican trabajos, como tiendas donde se ven ofertas. En verde están las que ya puedes usar (porque entraste con tu cuenta). En rojo, las que aún no. Yo nunca escribo tus contraseñas: entras tú.'],
  programar: ['Programar búsquedas', 'Es como poner una alarma. Tú dices a qué horas quieres que busque trabajo por ti y yo lo hago solo, sin que lo pidas cada vez.'],
  post: ['Postulaciones', 'Es tu lista de los trabajos a los que ya has dicho "me interesa". Ves a qué empresa, cuándo y cómo va cada una: enviada, entrevista, oferta…'],
  pend: ['Pendientes de aprobar', 'Antes de hacer algo importante, como aceptar una entrevista con inteligencia artificial o escribirle a alguien, te lo pregunto. Sin tu "Aprobar" no lo hago.'],
  config: ['Configuración', 'Aquí cambias lo que me contaste: tu CV, qué trabajo quieres, dónde y cuánto. Pulsa un paso y lo arreglas.'],
  resp: ['Respuestas a cuestionarios', 'Las empresas hacen preguntas, como "¿sabes usar X?". Aquí guardo las respuestas, siempre verdaderas. Si no sé algo, te lo pregunto en vez de inventarlo.'],
  plant: ['Plantillas de mensajes', 'Son mensajes ya escritos con huecos, como una carta a la que solo le cambias el nombre. Me ahorran tiempo, pero nunca envío nada sin tu permiso.'],
  orient: ['Según tu CV', 'Leí tu CV, vi a qué te dedicas y adivino en qué trabajos puedes encajar mejor, como un amigo que te dice "tú eres bueno en esto". Puedes usar mis ideas o elegir las tuyas.'],
  cv: ['Tu CV', 'El CV es la hoja donde cuentas quién eres y qué sabes hacer. Súbelo y yo leo los datos para no hacértelos escribir. Si no tienes, te ayudo a crear uno.'],
  datos: ['Tus datos', 'Tu nombre, dónde vives y cuánto has trabajado. Las empresas los piden siempre, y así no tienes que escribirlos cada vez.'],
  tec: ['Habilidades e idiomas', 'Las cosas que sabes hacer o usar y los idiomas que hablas, con el nivel de verdad. Si algo no lo sabes, no lo pongo: las empresas valoran la verdad.'],
  busca: ['Qué buscas', 'Dime qué trabajo te gustaría y cómo: en casa (remoto), en la oficina o mezclado. Así busco solo lo que te interesa.'],
  donde: ['Dónde y cuánto', 'En qué ciudades puedes trabajar y cuánto dinero quieres ganar (un mínimo y un máximo). Las líneas rojas son cosas que nunca aceptarías.'],
  permisos: ['Permisos', 'Tú mandas. Decides si puedo mandar solicitudes solo o si primero te pregunto, y si puedo mirar tu correo (solo mirar) para ver si te contestaron.'],
};
const hq = k => `<button class="q" data-help="${k}" title="¿Qué es esto?">?</button>`;
function help(k) {
  const [t, d] = HELP[k] || ['', '']; $('#help')?.remove(); const o = document.createElement('div'); o.id = 'help'; o.className = 'ov'; o.style.zIndex = 20;
  o.innerHTML = `<div class="modal" style="max-width:420px"><h2>${esc(t)}</h2><p style="font-size:17px">${esc(d)}</p><div class="foot" style="justify-content:flex-end"><button class="b" id="hok">¡Entendido!</button></div></div>`;
  document.body.appendChild(o); $('#hok').onclick = () => o.remove(); o.onmousedown = e => { if (e.target === o) o.remove(); };
}
document.addEventListener('click', e => { const k = e.target.dataset?.help; if (k) { e.stopPropagation(); help(k); } }, true);
const cap = m => m[0].toUpperCase() + m.slice(1);

// ---------- componentes ----------
const opt = o => Array.isArray(o) ? o : [o, o];
const sel = (id, opts, val, ph) => `<select id="${id}">${ph ? `<option value="">${ph}</option>` : ''}${opts.map(opt).map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(val ?? '') ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select>`;
// chips: selector desplegable + etiquetas que se quitan al pulsar
function chips(el, opts, vals, other) {
  const v = [...vals]; const draw = () => {
    el.innerHTML = `<select><option value="">+ Añadir…</option>${opts.filter(o => !v.includes(o)).map(o => `<option>${esc(o)}</option>`).join('')}${other ? '<option value="__o">Otro…</option>' : ''}</select>
    <div class="chips">${v.map((x, i) => `<span class="chip" data-i="${i}">${esc(x)} ✕</span>`).join('')}</div>`;
    $('select', el).onchange = e => { let x = e.target.value; if (x === '__o') x = (prompt('Escríbelo') || '').trim(); if (x && !v.includes(x)) v.push(x); draw(); };
    el.querySelectorAll('.chip').forEach(c => c.onclick = () => { v.splice(+c.dataset.i, 1); draw(); });
  }; draw(); return { get: () => v };
}
// filas (tecnología/idioma + valor)
function rows(el, opts, vals, vopts, vph) {
  let v = vals.map(x => ({ ...x })); const draw = () => {
    el.innerHTML = v.map((x, i) => `<div class="r2"><select data-k="${i}">${[...new Set([x.n, ...opts])].map(o => `<option ${o === x.n ? 'selected' : ''}>${esc(o)}</option>`).join('')}<option value="__o">Otra…</option></select>
      <select data-v="${i}"><option value="">${vph}</option>${vopts.map(opt).map(([a, b]) => `<option value="${a}" ${String(a) === String(x.v ?? '') ? 'selected' : ''}>${b}</option>`).join('')}</select><button class="s" data-d="${i}">✕</button></div>`).join('') +
      `<button class="s" data-add>+ Añadir</button>`;
    el.querySelectorAll('[data-k]').forEach(s => s.onchange = () => { if (s.value === '__o') { const t = (prompt('Escríbela') || '').trim(); if (t) v[+s.dataset.k].n = t; draw(); } else v[+s.dataset.k].n = s.value; });
    el.querySelectorAll('[data-v]').forEach(s => s.onchange = () => v[+s.dataset.v].v = s.value);
    el.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { v.splice(+b.dataset.d, 1); draw(); });
    $('[data-add]', el).onclick = () => { const free = opts.find(o => !v.some(x => x.n === o)); v.push({ n: free || opts[0], v: '' }); draw(); };
  }; draw(); return { get: () => v };
}
const flash = (el, t, bad) => { el.innerHTML = `<span class="${bad ? 'err' : 'msg'}">${esc(t)}</span>`; };

// ---------- asistente (modal) ----------
let W; // {p, c, step, only, ports}
const STEPS = ['cv', 'datos', 'tec', 'busca', 'donde', 'portales', 'permisos'];
const TITLES = { cv: 'Tu CV', datos: 'Tus datos', tec: 'Habilidades e idiomas', busca: 'Qué buscas', donde: 'Dónde y cuánto', portales: 'Portales', permisos: 'Permisos' };
async function openWizard(step = 0, only = false) {
  W = { p: await api('/api/profile'), c: await api('/api/criteria'), step, only, ports: await api('/api/portals') };
  W.p.personal ||= {}; W.p.skills ||= []; W.p.languages ||= [];
  let ov = $('#wiz'); if (!ov) { ov = document.createElement('div'); ov.id = 'wiz'; ov.className = 'ov'; document.body.appendChild(ov); }
  wiz();
}
const closeWizard = () => { $('#wiz')?.remove(); show(); };
// cerrar sin terminar: no vuelve a saltar solo; Inicio avisa de que falta configurar
const dismiss = async () => { await api('/api/setup', 'PUT', { done: true }); closeWizard(); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') { if ($('#help')) $('#help').remove(); else if ($('#wiz')) dismiss(); } });
document.addEventListener('mousedown', e => { if (e.target.id === 'wiz') dismiss(); });
let G = {}; // componentes del paso actual
function wiz() {
  const k = STEPS[W.step], p = W.p, pe = p.personal, c = W.c; G = {};
  const dots = W.only ? '' : `<div class="dots">${STEPS.map((_, i) => `<i class="${i <= W.step ? 'on' : ''}"></i>`).join('')}</div>`;
  const B = {
    cv: () => `<p>Sube tu CV (PDF, DOCX o TXT) y rellenaré lo que pueda. Se lee en tu equipo; no se envía a nadie.</p>
      <input type="file" id="cv" accept=".pdf,.docx,.txt"><div id="cvm"></div>
      <p><button class="s" id="mk">¿No tienes CV? Créalo en segundos</button></p>
      <p class="hint">${pe.name ? '✓ Ya hay un perfil cargado. Puedes subir otro CV para reemplazarlo.' : 'Sin CV puedes seguir y rellenar los datos a mano.'}</p>`,
    datos: () => `<div class="row"><div><label>Nombre</label><input id="n" value="${esc(pe.name)}"></div><div><label>Email</label><input id="e" value="${esc(pe.email)}"></div>
      <div><label>Teléfono</label><input id="t" value="${esc(pe.phone)}"></div><div><label>Provincia donde vives</label>${sel('ci', PROV.slice(1), pe.city, 'Elige…')}</div>
      <div><label>Sector profesional</label>${sel('sc', Object.keys(CAT), p.sector, 'Elige…')}</div>
      <div><label>Años de experiencia</label>${sel('ty', range(0, 30), p.total_years, 'Elige…')}</div>
      <div><label>Estudios</label>${sel('ed', ['ESO / Bachillerato', 'FP Grado Medio', 'FP Grado Superior', 'Grado universitario', 'Máster', 'Doctorado', 'Autodidacta'], p.education, 'Elige…')}</div>
      <div><label>¿Puedes trabajar en España?</label>${sel('wa', ['Sí, nacionalidad española/UE', 'Sí, con permiso de trabajo', 'No'], p.work_authorization, 'Elige…')}</div>
      <div><label>¿Necesitas patrocinio de visado?</label>${sel('sp', ['No', 'Sí'], p.needs_sponsorship, 'Elige…')}</div></div>`,
    tec: () => `<label>Habilidades y años REALES de experiencia (lo que no pongas se responderá "0 años")</label><div id="sk"></div><label>Idiomas y nivel REAL</label><div id="la"></div>`,
    busca: () => `<div id="orient"></div><label>Puestos que buscas</label><div id="ro"></div><label>Modalidad (por orden de preferencia)</label><div id="mo"></div><label>Contrato</label><div id="co"></div>`,
    donde: () => `<label>Zonas</label><div id="zo"></div><label>Salario esperado (bruto/año): rango</label><div class="row">${sel('sa', SAL, c.min_salary, 'Desde…')}${sel('sb', SAL, c.max_salary, 'Hasta…')}</div>
      <label>Idiomas de las ofertas</label><div id="li"></div><label>Líneas rojas (nunca postular)</label><div id="de"></div>`,
    portales: () => `<p class="hint">Marca dónde quieres buscar y en cuáles ya tienes la sesión iniciada en tu Chrome. Yo nunca escribo contraseñas ni creo cuentas.</p>` +
      W.ports.map(x => `<div class="pt ${x.selected ? (x.access ? 'ok' : 'no') : ''}" style="margin:6px 0"><label style="margin:0;color:inherit"><input type="checkbox" style="width:auto" data-s="${esc(x.name)}" ${x.selected ? 'checked' : ''}> <b style="display:inline">${esc(x.name)}</b> <span class="hint">${esc(x.note)}</span></label>
      ${x.selected ? `<label style="margin:4px 0 0;color:inherit"><input type="checkbox" style="width:auto" data-a="${esc(x.name)}" ${x.access ? 'checked' : ''}> Ya tengo sesión iniciada · <a href="${x.url}" target="_blank" rel="noopener noreferrer">abrir</a></label>` : ''}</div>`).join(''),
    permisos: () => `<label>¿Postular automáticamente?</label>${sel('au', [['false', 'No: apruebo yo cada oferta'], ['true', 'Sí: postular solo si el encaje llega al mínimo']], String(!!c.auto_apply))}
      <label>¿Leer tu Gmail para detectar respuestas? (solo lectura)</label>${sel('gm', [['false', 'No'], ['true', 'Sí, solo lectura']], String(!!c.gmail_read))}
      <div class="row"><div><label>Encaje mínimo</label>${sel('mf', range(30, 90, 5), c.min_fit)}</div><div><label>Máx. postulaciones por sesión</label>${sel('mx', [5, 10, 20, 30, 50], c.max_per_session)}</div></div>
      <p><label style="color:inherit"><input type="checkbox" id="cf" style="width:auto" ${p.confirmed ? 'checked' : ''}> Confirmo que mi perfil es veraz. Sin esto no se postula.</label></p>`,
  };
  const last = W.step === STEPS.length - 1;
  $('#wiz').innerHTML = `<div class="modal"><button class="s" id="x" title="Cerrar" style="float:right">✕</button>${dots}<h2>${W.only ? '' : `Paso ${W.step + 1} de ${STEPS.length} · `}${TITLES[k]} ${hq(k)}</h2><div>${B[k]()}</div>
    <div class="foot"><span>${W.step > 0 && !W.only ? '<button class="s" id="bk">← Atrás</button>' : '<button class="s" id="cl">Cerrar</button>'}</span><button class="b" id="nx">${last || W.only ? 'Guardar' : 'Siguiente →'}</button></div></div>`;
  if (k === 'cv') $('#mk').onclick = buildCV;
  if (k === 'cv') $('#cv').onchange = async e => {
    const fd = new FormData(); fd.append('file', e.target.files[0]); flash($('#cvm'), 'Leyendo…');
    try { const r = await fetch('/api/cv', { method: 'POST', body: fd }); const j = await r.json(); if (!r.ok) throw new Error(j.error); W.p = j; W.p.personal ||= {}; W.p.skills ||= []; W.p.languages ||= []; flash($('#cvm'), '✓ CV leído. Revisa los datos en los siguientes pasos.'); }
    catch (x) { flash($('#cvm'), x.message, 1); }
  };
  if (k === 'tec') {
    G.sk = rows($('#sk'), skillOpts(p.sector), p.skills.map(s => ({ n: s.name, v: s.years ?? '' })), range(0, 25).map(x => [x, x + (x === 1 ? ' año' : ' años')]), 'Años…');
    G.la = rows($('#la'), LANG, p.languages.map(l => ({ n: l.name, v: l.level || '' })), LVL, 'Nivel…');
  }
  if (k === 'busca') { showOrientation(); G.ro = chips($('#ro'), roleOpts(p.sector), c.roles, true); G.mo = chips($('#mo'), ['Remoto', 'Híbrido', 'Presencial'], c.modes.map(cap), false); G.co = chips($('#co'), ['Jornada completa', 'Media jornada', 'Prácticas', 'Temporal'], c.contracts.map(cap), false); }
  if (k === 'donde') { G.zo = chips($('#zo'), PROV, c.zones, false); G.li = chips($('#li'), ['Español', 'Inglés', 'Catalán', 'Euskera', 'Gallego'], c.languages.map(cap), false); G.de = chips($('#de'), DEAL, c.dealbreakers, true); }
  if (k === 'portales') $('.modal').onchange = async e => {
    const d = e.target.dataset; if (!d.s && !d.a) return;
    await api('/api/portals/' + encodeURIComponent(d.s || d.a), 'PATCH', d.s ? { selected: e.target.checked } : { access: e.target.checked });
    W.ports = await api('/api/portals'); wiz();
  };
  $('#x').onclick = dismiss; if ($('#cl')) $('#cl').onclick = dismiss;
  if ($('#bk')) $('#bk').onclick = () => { collect(); W.step--; wiz(); };
  const modal = $('.modal'); ['input', 'change', 'click'].forEach(ev => modal.addEventListener(ev, () => setTimeout(markMissing, 0))); markMissing();
  $('#nx').onclick = async () => { collect(); if (last || W.only) { await saveAll(); closeWizard(); } else { W.step++; wiz(); } };
}
async function showOrientation() {
  const o = await api('/api/orientation'); if (!o.roles.length) { $('#orient').innerHTML = '<p class="hint">Si subes tu CV, te sugeriré por dónde orientar la búsqueda según tu campo.</p>'; return; }
  $('#orient').innerHTML = `<div class="card" style="background:var(--bg)"><b>🧭 Según tu CV</b> <span class="tag">${esc(o.sector)}</span> ${hq('orient')} <span class="tag">${esc(o.seniority)}</span> <span class="tag">${esc(o.core_stack.join(' · '))}</span>
    <ul style="margin:6px 0;padding-left:18px">${o.roles.map(r => `<li><b>${esc(r.role)}</b> <span class="hint">(${esc(r.skills.join(', '))})</span></li>`).join('')}</ul>
    <p class="hint" style="margin:0 0 6px">${esc(o.tip)}</p><button class="s" id="useo">Usar estas sugerencias</button></div>`;
  $('#useo').onclick = () => { collect(); W.c.roles = [...new Set([...W.c.roles, ...o.roles.map(r => r.role)])]; G.ro = chips($('#ro'), roleOpts(W.p.sector), W.c.roles, true); };
}
// ---------- creador de CV (para quien no tiene) ----------
function buildCV() {
  const p = W.p, pe = p.personal; let ex = [{ company: '', role: '', from: '', to: 'Actual', desc: '' }], none = false, G2 = {};
  const years = range(new Date().getFullYear() - 40, new Date().getFullYear()).reverse();
  const draw = () => {
    $('#wiz').innerHTML = `<div class="modal"><button class="s" id="x" style="float:right">✕</button><h2>Crea tu CV en 2 minutos</h2>
      <p class="hint">Solo escribo lo que me cuentes: no invento nada. Lo que no sepas, déjalo vacío.</p>
      <div class="row"><div><label>Nombre completo</label><input id="n" value="${esc(pe.name)}"></div><div><label>Email</label><input id="e" value="${esc(pe.email)}"></div>
      <div><label>Teléfono</label><input id="t" value="${esc(pe.phone)}"></div><div><label>Provincia</label>${sel('ci', PROV.slice(1), pe.city, 'Elige…')}</div>
      <div><label>Sector profesional</label>${sel('sc', Object.keys(CAT), W.keep?.sc ?? p.sector, 'Elige…')}</div><div><label>Puesto que buscas</label>${sel('tg', roleOpts(W.keep?.sc ?? p.sector), W.keep?.tg, 'Elige…')}</div><div><label>Estudios</label>${sel('ed', ['ESO / Bachillerato', 'FP Grado Medio', 'FP Grado Superior', 'Grado universitario', 'Máster', 'Doctorado', 'Autodidacta'], W.keep?.ed, 'Elige…')}</div></div>
      <label>Título o curso (opcional)</label><input id="et" placeholder="p. ej. Grado en Informática, FP DAW…" value="${esc(W.keep?.et)}">
      <label>Experiencia laboral</label><label style="color:inherit"><input type="checkbox" id="no" style="width:auto" ${none ? 'checked' : ''}> No tengo experiencia laboral</label>
      <div id="exs">${none ? '' : ex.map((x, i) => `<div class="card" style="padding:8px"><div class="row"><input data-f="company" data-i="${i}" placeholder="Empresa" value="${esc(x.company)}"><input data-f="role" data-i="${i}" placeholder="Puesto" value="${esc(x.role)}">
        <select data-f="from" data-i="${i}"><option value="">Desde…</option>${years.map(y => `<option ${String(y) === String(x.from) ? 'selected' : ''}>${y}</option>`).join('')}</select>
        <select data-f="to" data-i="${i}"><option>Actual</option>${years.map(y => `<option ${String(y) === String(x.to) ? 'selected' : ''}>${y}</option>`).join('')}</select></div>
        <textarea data-f="desc" data-i="${i}" rows="2" placeholder="¿Qué hacías? (1-2 frases reales)">${esc(x.desc)}</textarea></div>`).join('') + '<button class="s" id="ae">+ Otra experiencia</button>'}</div>
      <label>Habilidades y años de experiencia</label><div id="sk"></div><label>Idiomas</label><div id="la"></div>
      <label>Sobre ti (2-3 frases, opcional)</label><textarea id="su" rows="3" placeholder="Qué sabes hacer y qué buscas">${esc(W.keep?.su)}</textarea>
      <div class="foot"><button class="s" id="cancel">← Volver</button><button class="b" id="go">Crear mi CV</button></div><div id="bm"></div></div>`;
    G2.sk = rows($('#sk'), skillOpts(W.keep?.sc ?? p.sector), (W.keep?.sk || p.skills.map(s => ({ n: s.name, v: s.years ?? '' }))), range(0, 25).map(x => [x, x + (x === 1 ? ' año' : ' años')]), 'Años…');
    G2.la = rows($('#la'), LANG, W.keep?.la || (p.languages.length ? p.languages.map(l => ({ n: l.name, v: l.level || '' })) : [{ n: 'Español', v: 'Nativo' }]), LVL, 'Nivel…');
    $('#x').onclick = dismiss; $('#cancel').onclick = () => wiz();
    $('#sc').onchange = () => { grab(); draw(); };
    $('#no').onchange = e => { grab(); none = e.target.checked; draw(); };
    if ($('#ae')) $('#ae').onclick = () => { grab(); ex.push({ company: '', role: '', from: '', to: 'Actual', desc: '' }); draw(); };
    $('#go').onclick = go;
  };
  const grab = () => { document.querySelectorAll('[data-f]').forEach(i => ex[+i.dataset.i][i.dataset.f] = i.value); pe.name = $('#n').value; pe.email = $('#e').value; pe.phone = $('#t').value; pe.city = $('#ci').value; W.keep = { sc: $('#sc').value, tg: $('#tg').value, ed: $('#ed').value, et: $('#et').value, su: $('#su').value, sk: G2.sk.get(), la: G2.la.get() }; };
  const go = async () => {
    grab(); const k = W.keep;
    const data = { personal: pe, sector: k.sc, target: k.tg, summary: k.su, experiences: none ? [] : ex, education: k.ed, education_title: k.et,
      skills: k.sk.map(x => ({ name: x.n, years: x.v === '' ? null : +x.v, notes: '' })), languages: k.la.map(x => ({ name: x.n, level: x.v })) };
    try {
      W.p = await api('/api/cv/build', 'POST', data); W.p.personal ||= {}; W.p.skills ||= []; W.p.languages ||= [];
      $('#bm').innerHTML = `<p class="msg">✓ CV creado: <a href="/api/cv/file/${encodeURIComponent(W.p.cv_files.at(-1))}">descargar (.docx)</a></p><p><button class="b" id="cont">Continuar →</button></p>`;
      $('#cont').onclick = () => { W.step = 1; wiz(); };
    } catch (x) { flash($('#bm'), x.message, 1); }
  };
  draw();
}
// marca en rojo lo que falta en el paso actual
function markMissing() {
  const k = STEPS[W.step], bad = [];
  const lab = el => ['ro', 'mo', 'co', 'zo'].includes(el.id) ? el.previousElementSibling : el.parentElement.querySelector('label');
  const mark = (id, isBad) => { const el = $('#' + id); if (!el) return; el.classList.toggle('miss', isBad); const l = lab(el); if (l && l.tagName === 'LABEL') l.classList.toggle('miss-l', isBad); if (isBad) bad.push(id); };
  if (k === 'datos') ['n', 'e', 't', 'ci', 'sc', 'ty', 'ed', 'wa', 'sp'].forEach(id => mark(id, ($('#' + id)?.value ?? '') === ''));
  if (k === 'busca' && G.ro) { mark('ro', !G.ro.get().length); mark('mo', !G.mo.get().length); mark('co', !G.co.get().length); }
  if (k === 'donde' && G.zo) mark('zo', !G.zo.get().length);
  if (k === 'permisos') { const cf = $('#cf'); cf.closest('p').classList.toggle('miss', !cf.checked); if (!cf.checked) bad.push('cf'); }
  let n = $('#missn'); if (!n) { n = document.createElement('p'); n.id = 'missn'; n.className = 'err'; $('.modal h2').after(n); }
  n.textContent = bad.length ? '🔴 Los campos en rojo faltan para completar tu perfil.' : '';
}
function collect() {
  const k = STEPS[W.step], p = W.p, c = W.c, v = id => $('#' + id)?.value;
  if (k === 'datos') { Object.assign(p.personal, { name: v('n'), email: v('e'), phone: v('t'), city: v('ci') }); p.sector = v('sc'); p.total_years = v('ty') === '' ? null : +v('ty'); p.education = v('ed'); p.work_authorization = v('wa'); p.needs_sponsorship = v('sp'); }
  if (k === 'tec') { p.skills = G.sk.get().map(x => ({ name: x.n, years: x.v === '' ? null : +x.v, notes: p.skills.find(s => s.name === x.n)?.notes || '' })); p.languages = G.la.get().map(x => ({ name: x.n, level: x.v })); }
  if (k === 'busca' && G.ro) { c.roles = G.ro.get(); c.modes = G.mo.get().map(x => x.toLowerCase()); c.contracts = G.co.get().map(x => x.toLowerCase()); }
  if (k === 'donde') { c.zones = G.zo.get(); c.min_salary = v('sa') === '' ? null : +v('sa'); c.max_salary = v('sb') === '' ? null : +v('sb'); if (c.min_salary && c.max_salary && c.max_salary < c.min_salary) [c.min_salary, c.max_salary] = [c.max_salary, c.min_salary]; c.languages = G.li.get().map(x => x.toLowerCase()); c.dealbreakers = G.de.get(); }
  if (k === 'permisos') { c.auto_apply = v('au') === 'true'; c.gmail_read = v('gm') === 'true'; c.min_fit = +v('mf'); c.max_per_session = +v('mx'); p.confirmed = $('#cf').checked; }
}
async function saveAll() {
  const cur = await api('/api/criteria'); // los portales se guardan al marcarlos: no los pisamos
  await api('/api/criteria', 'PUT', { ...W.c, sites: cur.sites, access: cur.access });
  await api('/api/profile', 'PUT', W.p); await api('/api/setup', 'PUT', { done: true });
}

// ---------- vistas ----------
let tab = location.hash.slice(1) || 'inicio';
const TABS = { inicio: 'Inicio', perfil: 'Perfil', post: 'Postulaciones', pend: 'Pendientes de aprobar', ajustes: 'Ajustes' };
function nav() {
  $('#nav').innerHTML = Object.entries(TABS).map(([k, v]) => `<button class="${k === tab ? 'on' : ''}" data-t="${k}">${v}</button>`).join('');
  $('#nav').onclick = e => { const t = e.target.dataset.t; if (t) { tab = t; location.hash = t; show(); } };
}
async function show() { nav(); notify(); $('#main').innerHTML = ''; $('#main').onclick = $('#main').onchange = null; await (views[tab] || views.inicio)(); }

// ---------- búsquedas programadas ----------
async function schedCard() {
  let list = await api('/api/schedules'); const el = $('#sch');
  const save = async () => { await api('/api/schedules', 'PUT', { schedules: list }); schedCard(); };
  const label = s => `${s.days.length ? s.days.join(', ') : 'Todos los días'} · ${s.times.join(' y ')}`;
  el.innerHTML = `<h2>⏰ Programar búsquedas ${hq('programar')}</h2><p class="hint">Elige cuántas veces y cuándo busca el agente. Se ejecutan solas mientras PillaCurro esté abierta en tu equipo. Por defecto solo busca y te pide permiso: nunca postula sin que lo apruebes.</p>
    ${list.map((s, i) => `<div class="pt ${s.enabled ? 'ok' : ''}" style="margin:6px 0"><b style="display:inline">${esc(label(s))}</b> <span class="hint">(${s.times.length} ${s.days.length ? 'por día elegido' : 'al día'})</span>
      <label style="display:inline;color:inherit;margin-left:8px"><input type="checkbox" style="width:auto" data-en="${i}" ${s.enabled ? 'checked' : ''}> activa</label> <button class="s" data-rm="${i}">✕</button></div>`).join('') || '<p class="hint">Aún no hay búsquedas programadas.</p>'}
    <div class="row" style="margin-top:8px"><div><label>Frecuencia</label>${sel('sf', [['dia', 'Todos los días'], ['semana', 'Días concretos de la semana']], 'dia')}</div>
      <div><label>¿Cuántas búsquedas por día?</label>${sel('sn', range(1, 6), 1)}</div></div>
    <div id="sh" class="row"></div><div id="sd"></div><p><button class="b" id="sadd">+ Añadir programación</button></p>`;
  let days = chips($('#sd'), DIAS, [], false); $('#sd').hidden = true;
  const hours = () => { const n = +$('#sn').value, prev = [...document.querySelectorAll('#sh select')].map(x => x.value); $('#sh').innerHTML = range(1, n).map(i => `<div><label>Hora ${i}</label>${sel('h' + i, HORAS, prev[i - 1] || ['09:00', '20:00', '13:00', '17:00', '11:00', '22:00'][i - 1])}</div>`).join(''); };
  hours(); $('#sn').onchange = hours; $('#sf').onchange = e => { $('#sd').hidden = e.target.value !== 'semana'; };
  $('#sadd').onclick = () => { const times = [...document.querySelectorAll('#sh select')].map(x => x.value).sort(); list.push({ times: [...new Set(times)], days: $('#sf').value === 'semana' ? DIAS.filter(d => days.get().includes(d)) : [], enabled: true }); save(); };
  el.onclick = e => { const r = e.target.dataset.rm; if (r !== undefined) { list.splice(+r, 1); save(); } };
  el.onchange = e => { const i = e.target.dataset.en; if (i !== undefined) { list[+i].enabled = e.target.checked; save(); } };
}

// ---------- búsqueda en marcha: modal con lo que hace el agente ----------
let runTimer = null;
async function launch() {
  try { await api('/api/runs', 'POST'); }
  catch (x) {
    if (!/en marcha/.test(x.message)) { alert(x.message); return; }
  }
  openRun(); show();
}
function openRun() {
  $('#runchip')?.remove(); let ov = $('#runov'); if (ov) return;
  ov = document.createElement('div'); ov.id = 'runov'; ov.className = 'ov'; document.body.appendChild(ov);
  const close = () => { clearInterval(runTimer); ov.remove(); watchRun(); };
  ov.onmousedown = e => { if (e.target === ov) close(); };
  const draw = async () => {
    const r = await api('/api/runs/current'); if (!r) return;
    const live = r.status === 'en curso', box = $('#runlog');
    const atBottom = !box || box.scrollTop + box.clientHeight >= box.scrollHeight - 30;
    ov.innerHTML = `<div class="modal"><button class="s" id="rx" title="Cerrar (la búsqueda sigue)" style="float:right">✕</button><h2>${live ? '🔎 Buscando trabajo para ti…' : r.status === 'terminada' ? '✅ Búsqueda terminada' : r.status === 'detenida' ? '⏹️ Búsqueda detenida' : '⚠️ La búsqueda tuvo un problema'}</h2>
      <p class="hint">${live ? 'Esto es lo que estoy haciendo ahora mismo. Puedes cerrar esta ventana: sigo trabajando.' : 'Aquí tienes lo que hice.'}</p>
      <div id="runlog" style="max-height:48vh;overflow:auto;border:1px solid var(--bd);border-radius:8px;padding:8px;font-size:14px">${r.log.map(l => `<div><span class="hint">${esc(l.t)}</span> ${esc(l.msg)}</div>`).join('')}</div>
      <div class="foot">${live ? `<button class="s" id="rs">⏹ Detener búsqueda</button>` : '<span></span>'}<button class="b" id="rc">${live ? 'Cerrar' : 'Ver postulaciones'}</button></div></div>`;
    const nb = $('#runlog'); if (atBottom) nb.scrollTop = nb.scrollHeight;
    $('#rx').onclick = close; $('#rc').onclick = () => { close(); if (!live) { tab = 'post'; location.hash = 'post'; show(); } };
    if (live) $('#rs').onclick = async () => { await api(`/api/runs/${r.id}/stop`, 'POST'); draw(); };
    else clearInterval(runTimer);
  };
  draw(); runTimer = setInterval(draw, 2000);
}
// pastilla "búsqueda en curso" cuando el modal está cerrado
let watching = null;
function watchRun() {
  clearInterval(watching);
  const chk = async () => {
    if ($('#runov')) return; const r = await api('/api/runs/current').catch(() => null); let chip = $('#runchip');
    if (r && r.status === 'en curso') { if (!chip) { chip = document.createElement('button'); chip.id = 'runchip'; chip.className = 'b'; chip.style.cssText = 'position:fixed;left:14px;bottom:14px;z-index:8'; chip.onclick = openRun; document.body.appendChild(chip); } chip.textContent = '🔎 Búsqueda en curso — ver'; }
    else { chip?.remove(); if (!r || r.status !== 'en curso') clearInterval(watching); }
  };
  chk(); watching = setInterval(chk, 4000);
}
// ---------- avisos tipo Teams: aparecen abajo, se minimizan y quedan pendientes hasta que el usuario los cierre ----------
const gs = (s, k) => { try { return JSON.parse(s.getItem(k) || '[]'); } catch (e) { return []; } };
const ss = (s, k, v) => { try { s.setItem(k, JSON.stringify(v)); } catch (e) {} };
const closedL = () => gs(localStorage, 'pc_closed'), shownS = () => gs(sessionStorage, 'pc_shown');
let NOTES = [], OPEN = null;
async function notify() {
  const [p, c, ports, ap] = await Promise.all([api('/api/profile'), api('/api/criteria'), api('/api/portals'), api('/api/approvals?status=pendiente')]);
  const pe = p.personal || {}, n = [], chosen = ports.filter(x => x.selected), miss = chosen.filter(x => !x.access);
  if (!pe.name) n.push({ id: 'cv', icon: '📄', t: 'Falta tu CV', m: 'Sube tu CV o crea uno en un momento para empezar.', b: 'Subir o crear CV', f: () => openWizard(0) });
  else {
    const falta = [!pe.name && 'nombre', !pe.email && 'email', !pe.phone && 'teléfono', !pe.city && 'provincia', !p.sector && 'sector', p.total_years == null && 'años de experiencia', !p.education && 'estudios', !p.work_authorization && 'permiso de trabajo', !p.needs_sponsorship && 'visado'].filter(Boolean);
    if (falta.length) n.push({ id: 'datos:' + falta.join(), icon: '📝', t: 'Faltan datos', m: 'Completa: ' + falta.join(', ') + '.', b: 'Completar', f: () => openWizard(1, true) });
    if (!c.roles.length) n.push({ id: 'roles', icon: '🔎', t: 'Elige qué buscas', m: 'Aún no has indicado qué puestos te interesan.', b: 'Elegir', f: () => openWizard(3, true) });
    if (!p.confirmed) n.push({ id: 'confirmar', icon: '✅', t: 'Confirma tu perfil', m: 'Sin confirmar que es veraz no puedo postular por ti.', b: 'Confirmar', f: () => openWizard(6, true) });
  }
  if (!chosen.length) n.push({ id: 'sin-portales', icon: '🌐', t: 'Elige portales', m: 'Marca dónde quieres que busque.', b: 'Elegir portales', f: () => openWizard(5, true) });
  else if (miss.length) n.push({ id: 'portales:' + miss.map(x => x.name).join(), icon: '🔴', t: `Faltan ${miss.length} portal${miss.length > 1 ? 'es' : ''} por iniciar sesión`, m: miss.map(x => x.name).join(', ') + '. Entra tú en tu navegador; yo nunca escribo contraseñas.', b: 'Ver portales', f: () => { tab = 'inicio'; location.hash = 'inicio'; show(); } });
  if (ap.length) n.push({ id: 'aprobar:' + ap.length, icon: '🔔', t: `${ap.length} cosa${ap.length > 1 ? 's' : ''} esperan tu decisión`, m: 'Aprueba o rechaza lo pendiente.', b: 'Revisar', f: () => { tab = 'pend'; location.hash = 'pend'; show(); } });
  NOTES = n.filter(x => !closedL().includes(x.id)); renderToasts();
}
function renderToasts() {
  let box = $('#toasts'); if (!box) { box = document.createElement('div'); box.id = 'toasts'; document.body.appendChild(box); }
  if (OPEN === null) { const fresh = NOTES.find(x => !shownS().includes(x.id)); if (fresh) { OPEN = fresh.id; ss(sessionStorage, 'pc_shown', [...shownS(), fresh.id]); const id = fresh.id; setTimeout(() => { if (OPEN === id) { OPEN = null; renderToasts(); } }, 8000); } }
  box.innerHTML = NOTES.map(x => x.id === OPEN
    ? `<div class="toast"><button class="s tx" data-tc="${esc(x.id)}" title="Cerrar">✕</button><b>${x.icon} ${esc(x.t)}</b><div class="hint">${esc(x.m)}</div><p style="margin:8px 0 0"><button class="b" data-ta="${esc(x.id)}">${esc(x.b)}</button> <button class="s" data-tm="${esc(x.id)}">Minimizar</button></p></div>`
    : `<div class="toast min" data-te="${esc(x.id)}" title="${esc(x.m)}">${x.icon} ${esc(x.t)} <button class="s tx" data-tc="${esc(x.id)}" title="Cerrar">✕</button></div>`).join('');
  box.onclick = e => {
    const d = e.target.dataset, f = id => NOTES.find(x => x.id === id);
    if (d.tc) { e.stopPropagation(); ss(localStorage, 'pc_closed', [...closedL(), d.tc]); NOTES = NOTES.filter(x => x.id !== d.tc); if (OPEN === d.tc) OPEN = null; renderToasts(); }
    else if (d.ta) { f(d.ta).f(); OPEN = null; renderToasts(); }
    else if (d.tm) { OPEN = null; renderToasts(); }
    else { const t = e.target.closest('[data-te]'); if (t) { OPEN = t.dataset.te; renderToasts(); } }
  };
}

// ---------- conectar portales con el navegador propio de la app ----------
function engineModal(then) {
  $('#engov')?.remove(); const ov = document.createElement('div'); ov.id = 'engov'; ov.className = 'ov'; document.body.appendChild(ov);
  ov.innerHTML = `<div class="modal" style="max-width:440px"><button class="s" id="ex" style="float:right">✕</button><h2>Instalar el navegador de la app 🧰</h2>
    <p>Para abrir los portales de empleo necesito un navegador propio (gratuito, unos 150 MB, solo una vez). Tú no tienes que escribir nada.</p><p id="em" class="hint"></p>
    <div class="foot" style="justify-content:flex-end"><button class="b" id="ei">Instalar ahora</button></div></div>`;
  let t; const close = () => { clearInterval(t); ov.remove(); }; $('#ex').onclick = close;
  $('#ei').onclick = async () => {
    $('#ei').disabled = true; $('#em').textContent = 'Instalando… puede tardar unos minutos.'; await api('/api/engine/install', 'POST');
    t = setInterval(async () => { const s = await api('/api/engine/status'); if (s.installed) { close(); then && then(); } else if (!s.installing) { $('#em').textContent = 'No se pudo instalar: ' + s.log; $('#ei').disabled = false; clearInterval(t); } }, 3000);
  };
}
async function connectPortal(name) {
  try { await api('/api/portals/' + encodeURIComponent(name) + '/connect', 'POST'); }
  catch (x) { if (x.data?.code === 'engine') return engineModal(() => connectPortal(name)); return alert(x.message); }
  alert('Se ha abierto una ventana con ' + name + '. Inicia sesión ahí tú mismo y ciérrala cuando termines: lo marcaré como conectado.');
  const t = setInterval(async () => { const p = (await api('/api/portals')).find(x => x.name === name); if (p?.access) { clearInterval(t); show(); } }, 3000);
}
function detailHtml(r) {
  if (r.kind !== 'postular') return `<pre style="white-space:pre-wrap;font:inherit">${esc(r.detail)}</pre>`;
  let d = {}; try { d = JSON.parse(r.detail); } catch (e) { }
  return `<ul style="margin:6px 0;padding-left:18px">${(d.why || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul>${d.url && !d.url.startsWith('demo://') ? `<a href="${esc(d.url)}" target="_blank" rel="noopener noreferrer">Ver la oferta</a>` : '<span class="hint">Oferta de demostración</span>'}`;
}

// ---------- acceso: crear cuenta / iniciar sesión (email, Google o LinkedIn) ----------
let ME = null;
const OA = {
  google: { n: 'Google', url: 'https://console.cloud.google.com/apis/credentials', steps: ['Entra en Google Cloud Console con tu cuenta de Google y crea un proyecto (gratis).', 'Pantalla de consentimiento OAuth → tipo «Externo» → rellena nombre y tu email.', 'Credenciales → Crear credenciales → «ID de cliente de OAuth» → tipo «Aplicación web».', 'En «URI de redirección autorizados» pega la dirección de abajo.', 'Copia el ID de cliente y el secreto y pégalos aquí.'] },
  linkedin: { n: 'LinkedIn', url: 'https://www.linkedin.com/developers/apps', steps: ['Entra en LinkedIn Developers y pulsa «Create app» (necesita una página de empresa de LinkedIn, puede ser una vacía).', 'En la pestaña Products añade «Sign In with LinkedIn using OpenID Connect».', 'En Auth → «Authorized redirect URLs» pega la dirección de abajo.', 'Copia el Client ID y el Primary Client Secret y pégalos aquí.'] },
};
function oauthSetup(p) {
  const o = OA[p]; $('#oaov')?.remove(); const ov = document.createElement('div'); ov.id = 'oaov'; ov.className = 'ov'; document.body.appendChild(ov);
  const uri = location.origin + '/auth/' + p + '/callback';
  ov.innerHTML = `<div class="modal"><button class="s" id="ox" style="float:right">✕</button><h2>Activar ${o.n} (solo una vez)</h2>
    <p class="hint">${o.n} exige que cada app tenga sus propias claves. Es gratis y se hace en unos minutos. Yo no puedo crearlas por ti porque son de tu cuenta.</p>
    <ol>${o.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol><p><a href="${o.url}" target="_blank" rel="noopener noreferrer">Abrir ${o.n} →</a></p>
    <label>Dirección de redirección (cópiala tal cual)</label><input id="ou" readonly value="${esc(uri)}" onclick="this.select()">
    <label>ID de cliente</label><input id="oi" autocomplete="off"><label>Secreto de cliente</label><input id="os" type="password" autocomplete="off"><p id="om"></p>
    <div class="foot" style="justify-content:flex-end"><button class="b" id="og">Guardar y activar</button></div></div>`;
  $('#ox').onclick = () => ov.remove();
  $('#og').onclick = async () => { try { await fetch('/api/auth/oauth-config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider: p, client_id: $('#oi').value, client_secret: $('#os').value }) }).then(async r => { const j = await r.json(); if (!r.ok) throw new Error(j.error); }); ov.remove(); showAuth(); } catch (x) { flash($('#om'), x.message, 1); } };
}
async function showAuth(mode = 'login') {
  $('#nav').innerHTML = ''; $('#me').innerHTML = ''; $('#wiz')?.remove();
  const prov = await fetch('/api/auth/providers').then(r => r.json()); const err = new URLSearchParams(location.search).get('auth_error');
  const reg = mode === 'register';
  $('#main').innerHTML = `<div class="card" style="max-width:420px;margin:30px auto"><h2 style="font-size:20px">${reg ? 'Crea tu cuenta' : 'Inicia sesión'} ${hq('acceso')}</h2>
    ${err ? `<p class="err">${esc(err)}</p>` : ''}
    <button class="s" id="gg" style="width:100%;margin:4px 0">${prov.google ? 'Continuar con Google' : 'Activar Google (1 vez)'}</button>
    <button class="s" id="li" style="width:100%;margin:4px 0">${prov.linkedin ? 'Continuar con LinkedIn' : 'Activar LinkedIn (1 vez)'}</button>
    ${prov.online ? '<p class="hint" style="background:rgba(178,106,0,.15);padding:8px;border-radius:6px">⚠️ Versión de pruebas online: no subas datos sensibles. Los datos pueden borrarse al actualizar la app.</p>' : ''}
    ${prov.google && prov.linkedin ? '' : '<p class="hint">Para entrar con Google o LinkedIn hay que activarlos una sola vez (pulsa el botón y te guío).</p>'}
    <p class="hint" style="text-align:center">— o con tu email —</p>
    ${reg ? '<label>Tu nombre</label><input id="an">' : ''}<label>Email</label><input id="ae" type="email" autocomplete="email"><label>Contraseña ${reg ? '(mínimo 8 caracteres)' : ''}</label><input id="ap" type="password" autocomplete="${reg ? 'new-password' : 'current-password'}">
    <p id="am"></p><button class="b" id="ago" style="width:100%">${reg ? 'Crear cuenta' : 'Entrar'}</button>
    <p class="hint" style="text-align:center"><a href="#" id="asw">${reg ? 'Ya tengo cuenta' : 'Crear una cuenta nueva'}</a></p></div>`;
  $('#gg').onclick = () => prov.google ? location.href = '/auth/google' : oauthSetup('google'); $('#li').onclick = () => prov.linkedin ? location.href = '/auth/linkedin' : oauthSetup('linkedin');
  $('#asw').onclick = e => { e.preventDefault(); history.replaceState(null, '', location.pathname); showAuth(reg ? 'login' : 'register'); };
  const go = async () => {
    try { await fetch('/api/auth/' + (reg ? 'register' : 'login'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: $('#an')?.value, email: $('#ae').value, password: $('#ap').value }) }).then(async r => { const j = await r.json(); if (!r.ok) throw new Error(j.error); });
      history.replaceState(null, '', location.pathname); boot(); } catch (x) { flash($('#am'), x.message, 1); }
  };
  $('#ago').onclick = go; $('#ap').onkeydown = e => { if (e.key === 'Enter') go(); };
}
async function boot() {
  const r = await fetch('/api/auth/me'); if (!r.ok) return showAuth();
  ME = await r.json(); CAT = await api('/api/catalog');
  $('#me').innerHTML = `<button class="s" data-t="perfil" title="Mi perfil">${ME.avatar ? `<img src="${esc(ME.avatar)}" alt="" style="width:18px;height:18px;border-radius:50%;vertical-align:middle"> ` : '👤 '}${esc(ME.name || ME.email)}</button>`;
  $('#me').onclick = () => { tab = 'perfil'; location.hash = 'perfil'; show(); };
  await show(); watchRun(); if (!(await api('/api/setup')).done) openWizard(0);
}
async function bootOldUnused() {}

const views = {
  async perfil() {
    const [p, o, c] = await Promise.all([api('/api/profile'), api('/api/orientation'), api('/api/criteria')]); const pe = p.personal || {};
    $('#main').innerHTML = `<div class="card"><h2>Mi cuenta ${hq('perfil')}</h2>
      <p><b style="font-size:17px">${esc(ME.name)}</b><br><span class="hint">${esc(ME.email)}</span> <span class="tag">${ME.provider === 'local' ? 'email' : esc(ME.provider)}</span></p>
      <p><button class="s" id="lo">Cerrar sesión</button> ${ME.provider === 'local' ? '<button class="s" id="pw">Cambiar contraseña</button> ' : ''}<button class="s" id="del" style="color:#c62828">Eliminar mi cuenta y mis datos</button></p><div id="pm"></div></div>
    <div class="card"><h2>Mi perfil profesional</h2>
      <p>${p.confirmed ? '✅ Confirmado' : '⚠️ Sin confirmar'} · <b>${esc(p.sector || 'Sin sector')}</b> · ${p.total_years ?? '?'} años · ${esc(pe.city || 'sin provincia')}</p>
      <div class="chips">${(p.skills || []).map(s => `<span class="tag">${esc(s.name)}${s.years ? ' · ' + s.years + 'a' : ''}</span>`).join('') || '<span class="hint">Sin habilidades todavía</span>'}</div>
      <p class="hint">Idiomas: ${(p.languages || []).map(l => esc(l.name + ' ' + (l.level || ''))).join(', ') || '—'} · Busco: ${esc((c.roles || []).join(', ') || '—')}</p>
      <p><button class="b" id="ep">Editar mi perfil</button> <button class="s" id="nc">Subir otro CV</button></p></div>
    <div class="card"><h2>Importar desde LinkedIn</h2>
      <p class="hint">${p.linkedin_connected ? '✅ Has entrado con LinkedIn: ya tengo tu nombre y email. ' : ''}LinkedIn no deja leer tu trayectoria directamente. Para orientar la app a tu sector, descarga tu perfil: en LinkedIn abre tu perfil → <b>Más</b> → <b>Guardar como PDF</b>, y súbelo aquí.</p>
      <input type="file" id="lipdf" accept=".pdf"><div id="lim"></div></div>
    ${o.roles?.length ? `<div class="card"><h2>🧭 Orientación según tu perfil ${hq('orient')}</h2><p><span class="tag">${esc(o.sector)}</span> <span class="tag">${esc(o.seniority)}</span></p><ul>${o.roles.map(r => `<li><b>${esc(r.role)}</b> <span class="hint">(${esc(r.skills.join(', '))})</span></li>`).join('')}</ul><p class="hint">${esc(o.tip)}</p></div>` : ''}`;
    $('#lo').onclick = async () => { await api('/api/auth/logout', 'POST'); ME = null; location.hash = ''; boot(); };
    $('#ep').onclick = () => openWizard(1, true); $('#nc').onclick = () => openWizard(0, true);
    if ($('#pw')) $('#pw').onclick = async () => { const old = prompt('Contraseña actual'); if (!old) return; const nw = prompt('Contraseña nueva (mínimo 8 caracteres)'); if (!nw) return; try { await api('/api/auth/password', 'PUT', { old, new: nw }); flash($('#pm'), 'Contraseña cambiada'); } catch (x) { flash($('#pm'), x.message, 1); } };
    $('#del').onclick = async () => { if (confirm('Se borrarán tu cuenta, tu CV y todas tus postulaciones. No se puede deshacer. ¿Seguro?')) { await api('/api/auth/me', 'DELETE'); ME = null; boot(); } };
    $('#lipdf').onchange = async e => { const fd = new FormData(); fd.append('file', e.target.files[0]); flash($('#lim'), 'Leyendo…'); const r = await fetch('/api/cv', { method: 'POST', body: fd }); const j = await r.json(); if (!r.ok) return flash($('#lim'), j.error, 1); flash($('#lim'), '✓ Perfil leído y orientación actualizada'); setTimeout(show, 800); };
  },

  async inicio() {
    const [ports, s, ap, p] = await Promise.all([api('/api/portals'), api('/api/stats'), api('/api/approvals?status=pendiente'), api('/api/profile')]);
    const chosen = ports.filter(x => x.selected), falta = chosen.filter(x => !x.access).length;
    $('#main').innerHTML = `
    <div class="card"><h2>Estado ${hq('estado')}</h2>
      ${p.confirmed ? '' : '<p class="hint">Aún no has terminado de configurar PillaCurro: pulsa el botón de abajo cuando quieras.</p>'}<p>${p.confirmed ? '✅ Perfil confirmado' : '⚠️ Perfil sin confirmar'} · ${s.total} postulaciones · ${(s.by_state.Entrevista || 0)} entrevistas · ${ap.length ? `<b>${ap.length} esperando tu decisión</b>` : 'nada pendiente de aprobar'}</p>
      <p><button class="b big" id="go" disabled>🚀 Lanzar búsqueda</button> ${hq('lanzar')}</p><div id="gomiss"></div>
      <button class="s" id="wz">⚙️ Configurar paso a paso</button></div>
    <div class="card" id="sch"></div>
    <div class="card"><h2>Portales donde buscaré y postularé ${hq('portales')}</h2>
      <p class="hint"><span class="tag" style="border-color:#2e7d32">verde</span> con acceso · <span class="tag" style="border-color:#c62828">rojo</span> falta iniciar sesión ${falta ? `· <b>faltan ${falta}</b>` : ''}</p>
      <div class="grid">${chosen.map(x => `<div class="pt ${x.access ? 'ok' : 'no'}"><b>${x.access ? '🟢' : '🔴'} ${esc(x.name)}</b><span class="hint">${x.access ? 'Acceso listo' : 'Falta iniciar sesión'}</span>
        <p style="margin:6px 0 0">${x.url ? `<button class="s" data-conn="${esc(x.name)}">Conectar</button> · <label style="display:inline;color:inherit"><input type="checkbox" style="width:auto" data-a="${esc(x.name)}" ${x.access ? 'checked' : ''}> ya tengo sesión</label>` : ''}</p></div>`).join('') || '<p class="hint">Aún no has elegido portales.</p>'}</div>
      <p><button class="b" id="pp">Elegir portales</button></p></div>`;
    schedCard();
    const rd = await api('/api/ready'), go = $('#go'); go.disabled = !rd.ready;
    $('#gomiss').innerHTML = rd.ready ? '<p class="msg" style="margin:0 0 8px">✅ Todo listo para buscar</p>' : `<p class="err" style="margin:0 0 8px">🔴 Para lanzar la búsqueda te falta: ${esc(rd.missing.join(', '))}.</p>`;
    go.onclick = launch;
    $('#wz').onclick = () => openWizard(0); $('#pp').onclick = () => openWizard(5, true);
    $('#main').onclick = e => { const n = e.target.dataset.conn; if (n) connectPortal(n); };
    $('#main').onchange = async e => { const n = e.target.dataset.a; if (n) { await api('/api/portals/' + encodeURIComponent(n), 'PATCH', { access: e.target.checked }); show(); } };
  },

  async post() {
    const a = await api('/api/applications');
    $('#main').innerHTML = `<div class="card"><h2>Postulaciones ${hq('post')}</h2><p><a href="/api/export.xlsx" style="text-decoration:none;color:inherit;padding:6px 10px;border:1px solid var(--bd);border-radius:6px">⬇ Excel con estadísticas</a></p>
      <div class="tbl"><table><tr><th>Fecha</th><th>Empresa</th><th>Puesto</th><th>Encaje</th><th>Estado</th><th>Notas</th></tr>
      ${a.map(r => `<tr><td>${esc(r.date)}</td><td>${esc(r.company)}</td><td>${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.role)}</a>` : esc(r.role)}</td><td>${esc(r.fit)}</td>
      <td><select data-id="${r.id}">${STATES.map(s => `<option ${s === r.state ? 'selected' : ''}>${s}</option>`).join('')}</select></td><td>${esc(r.notes)}</td></tr>`).join('') || '<tr><td colspan=6 class="hint">Todavía no hay postulaciones. Cuando el agente postule, aparecerán aquí.</td></tr>'}</table></div></div>`;
    $('#main').onchange = async e => { if (e.target.dataset.id) await api('/api/applications/' + e.target.dataset.id, 'PATCH', { state: e.target.value }); };
  },

  async pend() {
    const a = await api('/api/approvals');
    const K = { postular: 'Permiso para postular', consent_ia: 'Entrevista con IA', dato_nuevo: 'Dato que falta', mensaje_reclutador: 'Mensaje a reclutador', otro: 'Aprobar oferta' };
    $('#main').innerHTML = `<div class="card"><h2>Necesito tu decisión ${hq('pend')}</h2><p class="hint">Sin tu "Aprobar" no hago nada sensible.</p>
      ${a.map(r => `<div class="card"><span class="tag">${K[r.kind] || r.kind}</span> <span class="tag">${r.status}</span> <b>${esc(r.title)}</b>
      ${detailHtml(r)}
      ${r.status === 'pendiente' ? `<input data-n="${r.id}" placeholder="Respuesta o nota (opcional)"><p><button class="b" data-a="${r.id}:aprobado">${r.kind === 'postular' ? 'Sí, puedes postular' : 'Aprobar'}</button> <button class="s" data-a="${r.id}:rechazado">Rechazar</button></p>` : `<p class="hint">${esc(r.decision_note)}</p>`}</div>`).join('') || '<p class="hint">Nada pendiente 🎉</p>'}</div>`;
    $('#main').onclick = async e => { const d = e.target.dataset.a; if (!d) return; const [id, status] = d.split(':'); await api('/api/approvals/' + id, 'PATCH', { status, decision_note: $(`[data-n="${id}"]`).value }); show(); };
  },

  async ajustes() {
    const [a, t] = await Promise.all([api('/api/answers'), api('/api/templates')]);
    $('#main').innerHTML = `<div class="card"><h2>Configuración ${hq('config')}</h2><div class="grid">${STEPS.map((k, i) => `<button class="s" data-w="${i}">${TITLES[k]}</button>`).join('')}</div></div>
      <div class="card"><h2>Respuestas a cuestionarios ${hq('resp')}</h2><p class="hint">Veraces por defecto. Las marcadas "revisar" no se usan hasta que las rellenes.</p>
      <div class="tbl"><table><tr><th>Pregunta</th><th>Respuesta</th><th>Revisar</th><th></th></tr>${a.map(r => `<tr><td><input class="q" value="${esc(r.question)}"></td><td><input class="r" value="${esc(r.answer)}"></td><td><input type="checkbox" class="v" style="width:auto" ${r.needs_review ? 'checked' : ''}></td>
      <td data-id="${r.id}"><button class="s" data-save>Guardar</button> <button class="s" data-del>✕</button></td></tr>`).join('')}</table></div><p><button class="s" id="addq">+ Añadir</button></p></div>
      <div class="card"><h2>Plantillas de mensajes ${hq('plant')}</h2><p class="hint">Variables: {empresa} {puesto} {contacto} {nombre} {motivo_real} {experiencia_relevante} {disponibilidad}. Nunca se envía nada sin tu aprobación.</p>
      ${t.map(x => `<label>${esc(x.name)}</label><textarea rows="5" data-t="${esc(x.name)}">${esc(x.body)}</textarea><button class="s" data-s="${esc(x.name)}">Guardar</button>`).join('')}</div>`;
    $('#main').onclick = async e => {
      const d = e.target.dataset, tr = e.target.closest('tr');
      if (d.w !== undefined) openWizard(+d.w, true);
      if ('save' in d) { await api('/api/answers/' + tr.lastElementChild.dataset.id, 'PUT', { question: $('.q', tr).value, answer: $('.r', tr).value, needs_review: $('.v', tr).checked ? 1 : 0 }); e.target.textContent = '✓'; }
      if ('del' in d) { await api('/api/answers/' + tr.lastElementChild.dataset.id, 'DELETE'); show(); }
      if (d.s) { await api('/api/templates/' + d.s, 'PUT', { body: $(`[data-t="${d.s}"]`).value }); e.target.textContent = 'Guardado ✓'; }
    };
    $('#addq').onclick = async () => { await api('/api/answers', 'POST', { question: 'Nueva pregunta', answer: '', needs_review: 1 }); show(); };
  },
};
boot();

