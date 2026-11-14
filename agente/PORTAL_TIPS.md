# Trucos por portal (genéricos, sin datos personales)

Origen: proyecto real de búsqueda de empleo, limpiado. Añade aquí lo que aprendas; nada personal.

## Claude in Chrome (básico)
- Empieza cada sesión con `tabs_context_mcp` (crear si no hay). Los grupos de pestañas se reinician entre conversaciones.
- Las refs de `find`/`read_page` caducan rápido: vuelve a buscar justo antes de pulsar. Tras navegar o hacer scroll, recalcula coordenadas con `getBoundingClientRect()` (tras `scrollIntoView({block:'center'})`).
- Prefiere `get_page_text`, `read_page`, `find` y JavaScript corto. Sin capturas de pantalla al usuario.
- Si dice "page still loading" o "Detached", lee el estado con JS (`document.querySelector('main').innerText`) en vez de repetir la acción.
- Si no conecta: Chrome abierto con la misma cuenta de Claude y la extensión instalada. El aviso de "depurando este navegador" es normal.
- Algunos portales detectan clics `.click()` por JS (p. ej. con Cloudflare): usa clics reales por coordenadas y, si salta la verificación, no la saltes: avisa.

## LinkedIn
- Búsqueda: `https://www.linkedin.com/jobs/search-results/?keywords=<palabras>&geoId=<id región>&f_AL=true&f_TPR=r86400` (`f_AL=true` solicitud sencilla; `r86400` 24 h, `r172800` 48 h, `r604800` 7 días). Busca tu `geoId` una vez a mano y copia la URL.
- El filtro de modalidad por URL no es fiable: lee en la tarjeta (Remoto / Híbrido / Presencial).
- Ordenar por "más recientes" a veces ignora las palabras clave; prueba relevancia + filtro de fecha.
- Ficha `/jobs/view/<id>/`: espera ~2,5 s, pulsa "Solicitud sencilla"/"Easy Apply", comprueba que se abre el modal ("1/N páginas"), avanza Siguiente → Revisar → Enviar. Éxito: "Solicitud enviada".
- Respuestas de texto: setter nativo de `value` + eventos `input` y `change`. Radios: `.click()` en el input, **por orden de grupo** (las etiquetas Sí/No se repiten). Selects: `.value` + `change`.
- En Revisar, desmarca "Seguir a la empresa". LinkedIn prerrellena años de experiencia a veces mal: corrige con tu perfil.
- La lista está virtualizada: haz scroll para cargar más. Páginas en blanco = límite de ritmo: espera unos minutos.
- "Solicitar en el sitio web de la empresa" suele llevar a un ATS sin cuenta (Greenhouse, Lever, Ashby…): puede servir; si pide cuenta → "Externa".
- Subir un CV sin diálogo nativo: leer el archivo en base64, crear un `File` con `DataTransfer` sobre `input[type=file]` y lanzar `change`.

## Indeed
- Cloudflare / "Security Check" al abrir varias ofertas seguidas: no lo saltes; espacia las peticiones, y si persiste avisa.
- Rechaza cookies. "Solicitar ahora" abre smartapply.indeed.com (CV del perfil Indeed, preguntas, Revisar, Enviar). No marques alertas.
- Clics por `ref` a veces no hacen nada: usa coordenadas.

## Portales locales y de nicho
- InfoJobs / Tecnoempleo (España) y equivalentes: el usuario inicia sesión. Pueden tener entrevistas con IA (consentimiento → solo el usuario decide). Tecnoempleo puede disparar Cloudflare con clics por JS.
- Algunos portales caducan la sesión: avisa y sigue con otro.
- Agregadores (Jooble, Google Empleos): úsalos solo para descubrir; postula en la web original de la empresa, no en el agregador de pago/cuenta.
- Marketplaces de freelance, portales que cobran por postular o que redirigen a otro país: descártalos.

## Formularios de empresa (Greenhouse, Lever, Ashby, Viterbit, JOIN…)
- Normalmente sin cuenta. Sube el CV con `file_upload` si el diálogo lo permite; si no, lo sube el usuario. "¿Autorizado a trabajar?" veraz. Casillas opcionales de retención de datos: sin marcar. Rechaza cookies.
- Fechas en formato local; salario a menudo solo numérico.
- Desplegables personalizados (react-select, select2): ábrelos, escribe en el buscador, elige y verifica el valor.

## Correo
- Gmail: `newer_than:2d (interview OR application OR offer OR entrevista OR candidatura OR proceso)`. "Candidatura vista"/"proceso cerrado" son automáticos (Vista/Cerrada).

## General
- "80 % de coincidencia" del portal no es tu encaje: lee los requisitos.
- Ojo con freelance disfrazado, solo comisión y consultoras que ocultan al cliente.
- Ritmo pausado; nunca reabrir ofertas del registro o de la hoja "Descartadas".
