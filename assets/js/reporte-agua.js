(() => {
  const config = window.CARTOGRAFUNK_SUPABASE;
  const form = document.getElementById('reporteAguaForm');
  if (!form || !config || !window.L) return;

  const $ = id => document.getElementById(id);
  const draftKey = 'cartografunk.reporteAgua.borrador.v1';
  const center = [20.674, -103.35];
  const areaProvisional = { minLat: 20.35, maxLat: 21, minLng: -103.85, maxLng: -102.95 };
  const state = { step: 1, lat: null, lng: null, locationConfirmed: false, photo: null, photoUrl: null, turnstile: '', widget: null, sending: false };
  const steps = [...document.querySelectorAll('.agua-step')];
  const progress = [...document.querySelectorAll('.agua-progress li')];
  const today = new Date();
  $('fechaReporte').value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  const pinMap = L.map('mapaPin', { scrollWheelZoom: false }).setView(center, 12);
  const publicMap = L.map('mapaPublico', { scrollWheelZoom: false }).setView(center, 11);
  for (const map of [pinMap, publicMap]) {
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
  }
  let pin = null;

  function status(message, kind = 'error') {
    $('formEstado').textContent = message;
    $('formEstado').dataset.state = kind;
  }

  function putPin(lat, lng, zoom = 16) {
    state.lat = lat;
    state.lng = lng;
    state.locationConfirmed = false;
    if (!pin) {
      pin = L.marker([lat, lng], { draggable: true, keyboard: true }).addTo(pinMap);
      pin.on('dragend', () => {
        const p = pin.getLatLng();
        putPin(p.lat, p.lng, pinMap.getZoom());
      });
    } else pin.setLatLng([lat, lng]);
    pinMap.setView([lat, lng], zoom);
    $('ubicacionTexto').textContent = `Pin en ${lat.toFixed(5)}, ${lng.toFixed(5)}. Muévelo si hace falta y confirma el punto.`;
    saveDraft();
  }
  pinMap.on('click', event => putPin(event.latlng.lat, event.latlng.lng, pinMap.getZoom()));
  $('confirmarUbicacion').addEventListener('click', () => {
    if (state.lat === null || state.lng === null) { status('Primero marca un punto en el mapa.'); return; }
    if (state.lat < areaProvisional.minLat || state.lat > areaProvisional.maxLat
        || state.lng < areaProvisional.minLng || state.lng > areaProvisional.maxLng) {
      status('El punto está fuera del área provisional de Guadalajara. Ajusta el pin.'); return;
    }
    state.locationConfirmed = true;
    $('ubicacionTexto').textContent = `Punto confirmado: ${state.lat.toFixed(5)}, ${state.lng.toFixed(5)}.`;
    status('Punto confirmado. Ya puedes seguir.', 'success');
  });

  function showStep(step, focusHeading = true) {
    state.step = step;
    steps.forEach((section, index) => { section.hidden = index !== step - 1; });
    progress.forEach((item, index) => {
      if (index === step - 1) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    });
    $('pasoActual').textContent = `Paso ${step} de 4`;
    $('pasoAnterior').hidden = step === 1;
    $('pasoSiguiente').hidden = step === 4;
    $('enviarReporte').hidden = step !== 4;
    status('', '');
    if (step === 1) setTimeout(() => pinMap.invalidateSize(), 0);
    if (focusHeading) {
      const heading = steps[step - 1].querySelector('h3');
      heading.setAttribute('tabindex', '-1');
      heading.focus();
    }
  }

  function validStep(step) {
    if (step === 1) {
      if (state.lat === null || state.lng === null) {
        status('Marca el lugar en el mapa antes de seguir.'); return false;
      }
      if (state.lat < areaProvisional.minLat || state.lat > areaProvisional.maxLat
          || state.lng < areaProvisional.minLng || state.lng > areaProvisional.maxLng) {
        status('El punto está fuera del área provisional de Guadalajara. Ajusta el pin.'); return false;
      }
      if (!state.locationConfirmed) {
        status('Confirma el punto elegido antes de seguir.'); return false;
      }
    }
    if (step === 2 && !state.photo) {
      status('Agrega una foto válida antes de seguir.'); return false;
    }
    if (step === 3) {
      const note = $('notaReporte').value.trim();
      if (!$('categoriaReporte').value || !note || note.length > 500 || !$('fechaReporte').value) {
        status('Selecciona una categoría, escribe una nota y elige la fecha.'); return false;
      }
    }
    if (step === 4) {
      const email = $('emailReporte').value.trim();
      const phone = $('telefonoReporte').value.trim();
      if ((email || phone) && !$('consentimientoContacto').checked) {
        status('Acepta el uso de tus datos de contacto o deja esos campos vacíos.'); return false;
      }
      if (!$('consentimientoPublicacion').checked) {
        status('Necesitamos tu consentimiento para revisar y publicar el reporte.'); return false;
      }
      if (!state.turnstile) {
        status('Completa la verificación de seguridad.'); return false;
      }
    }
    return true;
  }

  $('pasoSiguiente').addEventListener('click', () => {
    if (validStep(state.step)) showStep(Math.min(4, state.step + 1));
  });
  $('pasoAnterior').addEventListener('click', () => showStep(Math.max(1, state.step - 1)));

  $('usarUbicacion').addEventListener('click', () => {
    if (!navigator.geolocation) { status('Este navegador no puede obtener tu ubicación. Marca el punto en el mapa.'); return; }
    status('Buscando tu ubicación…', 'success');
    navigator.geolocation.getCurrentPosition(
      position => { putPin(position.coords.latitude, position.coords.longitude); status('Ubicación encontrada. Ajusta el pin si hace falta.', 'success'); },
      error => status(error.code === 1
        ? 'No diste permiso de ubicación. Puedes marcar el punto en el mapa o buscar una dirección.'
        : 'No pudimos obtener tu ubicación. Marca el punto en el mapa.'),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 },
    );
  });

  $('buscarDireccionBoton').addEventListener('click', async () => {
    const q = $('buscarDireccion').value.trim();
    if (q.length < 3) { status('Escribe al menos tres caracteres para buscar.'); return; }
    const list = $('resultadosDireccion');
    list.replaceChildren();
    status('Buscando dirección…', 'success');
    try {
      const response = await fetch(`${config.url}/functions/v1/geocode?q=${encodeURIComponent(q)}`, {
        headers: { apikey: config.publishableKey },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || 'No pudimos buscar la dirección.');
      for (const result of body.resultados || []) {
        const item = document.createElement('li');
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = result.direccion;
        button.addEventListener('click', () => {
          putPin(result.lat, result.lng);
          list.replaceChildren();
          status('Ajusta el pin en el mapa para confirmar el lugar.', 'success');
        });
        item.append(button);
        list.append(item);
      }
      if (!list.children.length) status('No encontramos una dirección dentro del área provisional. Marca el punto en el mapa.');
      else status('Elige un resultado y ajusta el pin.', 'success');
    } catch (error) { status(error.message || 'No pudimos buscar la dirección.'); }
  });

  async function compressPhoto(file) {
    if (file.size > 20 * 1024 * 1024) throw new Error('Elige una foto de menos de 20 MB para comprimirla.');
    const image = await createImageBitmap(file);
    try {
      const ratio = Math.min(1, 1600 / Math.max(image.width, image.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(image.width * ratio));
      canvas.height = Math.max(1, Math.round(image.height * ratio));
      const context = canvas.getContext('2d');
      context.fillStyle = '#fff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .8));
      if (!blob || blob.size > 5 * 1024 * 1024) throw new Error('La foto sigue pesando más de 5 MB. Elige otra.');
      return new File([blob], 'reporte.jpg', { type: 'image/jpeg' });
    } finally { image.close(); }
  }

  $('fotoReporte').addEventListener('change', async event => {
    state.photo = null;
    const file = event.target.files?.[0];
    if (!file) return;
    $('fotoTexto').textContent = 'Preparando la foto…';
    try {
      state.photo = await compressPhoto(file);
      if (state.photoUrl) URL.revokeObjectURL(state.photoUrl);
      state.photoUrl = URL.createObjectURL(state.photo);
      $('fotoVista').src = state.photoUrl;
      $('fotoVista').hidden = false;
      $('fotoTexto').textContent = `Foto lista (${(state.photo.size / 1024 / 1024).toFixed(2)} MB), sin metadatos EXIF.`;
    } catch (error) {
      $('fotoVista').hidden = true;
      $('fotoTexto').textContent = error.message || 'No pudimos preparar la foto.';
      status($('fotoTexto').textContent);
    }
  });

  function saveDraft() {
    try {
      localStorage.setItem(draftKey, JSON.stringify({
        lat: state.lat, lng: state.lng, calle: $('calleTexto').value,
        categoria: $('categoriaReporte').value, nota: $('notaReporte').value,
        fecha: $('fechaReporte').value,
      }));
    } catch { /* El navegador puede bloquear almacenamiento local. */ }
  }
  function restoreDraft() {
    try {
      const draft = JSON.parse(localStorage.getItem(draftKey) || 'null');
      if (!draft) return;
      for (const [key, id] of [['calle', 'calleTexto'], ['categoria', 'categoriaReporte'],
        ['nota', 'notaReporte'], ['fecha', 'fechaReporte']]) {
        if (typeof draft[key] === 'string') $(id).value = draft[key];
      }
      if (Number.isFinite(draft.lat) && Number.isFinite(draft.lng)) putPin(draft.lat, draft.lng, 13);
      $('notaCuenta').textContent = `${$('notaReporte').value.length} de 500 caracteres`;
    } catch { /* Un borrador dañado no debe impedir el formulario. */ }
  }
  form.addEventListener('input', event => {
    if (event.target.id === 'notaReporte') $('notaCuenta').textContent = `${$('notaReporte').value.length} de 500 caracteres`;
    saveDraft();
  });

  async function loadCategories() {
    try {
      const response = await fetch(`${config.url}/functions/v1/enviar-reporte`, {
        headers: { apikey: config.publishableKey },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error);
      for (const category of body.categorias || []) {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.nombre;
        $('categoriaReporte').append(option);
      }
      restoreDraft();
    } catch { status('No pudimos cargar las categorías. Recarga la página antes de enviar.'); }
  }

  function loadTurnstile() {
    const siteKey = window.CARTOGRAFUNK_TURNSTILE_SITE_KEY;
    if (!siteKey) {
      $('turnstileAyuda').textContent = 'El envío aún no está disponible: falta configurar Turnstile.';
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    script.async = true;
    script.onload = () => {
      state.widget = window.turnstile.render('#turnstileWidget', {
        sitekey: siteKey,
        action: 'enviar_reporte',
        callback: token => { state.turnstile = token; $('turnstileAyuda').textContent = 'Verificación completa.'; },
        'expired-callback': () => { state.turnstile = ''; $('turnstileAyuda').textContent = 'La verificación venció. Hazla de nuevo.'; },
      });
      $('turnstileAyuda').textContent = 'Completa la verificación antes de enviar.';
    };
    script.onerror = () => { $('turnstileAyuda').textContent = 'No pudimos cargar la verificación. Revisa tu conexión.'; };
    document.head.append(script);
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (state.sending || !validStep(4)) return;
    state.sending = true;
    $('enviarReporte').disabled = true;
    status('Enviando reporte…', 'success');
    const data = new FormData();
    data.set('lat', String(state.lat));
    data.set('lng', String(state.lng));
    data.set('categoria_id', $('categoriaReporte').value);
    data.set('nota', $('notaReporte').value.trim());
    data.set('fecha_observacion', $('fechaReporte').value);
    data.set('calle_texto', $('calleTexto').value.trim());
    data.set('email', $('emailReporte').value.trim());
    data.set('telefono', $('telefonoReporte').value.trim());
    data.set('consentimiento_publicacion', 'si');
    if ($('consentimientoContacto').checked) data.set('consentimiento_contacto', 'si');
    data.set('turnstile_token', state.turnstile);
    data.set('foto', state.photo, 'reporte.jpg');
    try {
      const response = await fetch(`${config.url}/functions/v1/enviar-reporte`, {
        method: 'POST', headers: { apikey: config.publishableKey }, body: data,
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || 'No pudimos enviar el reporte.');
      $('folioReporte').textContent = body.folio;
      form.hidden = true;
      $('reporteExito').hidden = false;
      try { localStorage.removeItem(draftKey); } catch { /* Sin almacenamiento local. */ }
      status('', '');
    } catch (error) {
      status(error.message || 'No pudimos enviar el reporte.');
      state.turnstile = '';
      if (state.widget !== null && window.turnstile) window.turnstile.reset(state.widget);
    } finally {
      state.sending = false;
      $('enviarReporte').disabled = false;
    }
  });

  function popupContent(row) {
    const box = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = row.categoria_nombre;
    const note = document.createElement('p');
    note.textContent = row.nota;
    const date = document.createElement('small');
    date.textContent = new Date(row.fecha_observacion).toLocaleDateString('es-MX', { timeZone: 'UTC' });
    const photo = document.createElement('div');
    photo.textContent = 'Cargando foto…';
    box.append(title, note, date, photo);
    fetch(`${config.url}/functions/v1/foto-reporte?folio=${encodeURIComponent(row.folio)}`, {
      headers: { apikey: config.publishableKey },
    }).then(async response => {
      if (!response.ok) throw new Error('Foto no disponible');
      const body = await response.json();
      const img = document.createElement('img');
      img.src = body.url;
      img.alt = `Foto del reporte ${row.folio}`;
      img.loading = 'lazy';
      img.onerror = () => { photo.textContent = 'No se pudo cargar la foto.'; };
      photo.replaceChildren(img);
    }).catch(() => { photo.textContent = 'Foto no disponible.'; });
    return box;
  }

  async function loadPublicMap() {
    const clusters = L.markerClusterGroup({ chunkedLoading: true, showCoverageOnHover: false });
    publicMap.addLayer(clusters);
    let loaded = 0;
    try {
      for (let page = 0; page < 20; page++) {
        const from = page * 500;
        const response = await fetch(`${config.url}/rest/v1/reportes_agua_publicos?select=folio,geom_publica,categoria_nombre,nota,fecha_observacion&order=created_at.desc&limit=500&offset=${from}`, {
          headers: { apikey: config.publishableKey },
        });
        if (!response.ok) throw new Error('No se pudo cargar el mapa.');
        const rows = await response.json();
        for (const row of rows) {
          const point = row.geom_publica?.coordinates;
          if (!Array.isArray(point) || point.length !== 2) continue;
          if (!Number.isFinite(point[0]) || !Number.isFinite(point[1])) continue;
          L.marker([point[1], point[0]]).on('click', event => {
            event.target.bindPopup(popupContent(row), { maxWidth: 250 }).openPopup();
          }).addTo(clusters);
          loaded++;
        }
        if (rows.length < 500) break;
      }
      $('mapaEstado').textContent = loaded
        ? `${loaded} reporte${loaded === 1 ? '' : 's'} publicado${loaded === 1 ? '' : 's'}. Ubicaciones aproximadas.`
        : 'Aún no hay reportes publicados.';
    } catch { $('mapaEstado').textContent = 'No pudimos cargar los reportes. Intenta recargar la página.'; }
  }

  loadCategories();
  loadTurnstile();
  loadPublicMap();
  showStep(1, false);
})();
