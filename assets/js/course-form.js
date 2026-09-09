(() => {
  const form = document.getElementById('courseForm');
  if (!form) return;
  const button = form.querySelector('button[type="submit"]');
  const status = document.getElementById('courseFormStatus');
  const config = window.CARTOGRAFUNK_SUPABASE;
  const experiences = ['Nunca', 'Lo abrí una vez', 'Nivel básico', 'Nivel intermedio', 'Nivel avanzado'];
  const schedules = ['Entre semana - Matutino', 'Entre semana - Vespertino', 'Sábado', 'Domingo'];
  let pending = false;
  let complete = false;

  function publicKey(key) {
    if (typeof key !== 'string') return false;
    if (key.startsWith('sb_publishable_')) return true;
    try {
      const payload = key.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(payload)).role === 'anon';
    } catch { return false; }
  }

  async function post(resource, body, prefer) {
    const headers = {
      apikey: config.publishableKey,
      'Content-Type': 'application/json',
      Prefer: prefer,
    };
    if (!config.publishableKey.startsWith('sb_publishable_')) {
      headers.Authorization = `Bearer ${config.publishableKey}`;
    }
    const response = await fetch(`${config.url}/rest/v1/${resource}`, {
      method: 'POST', headers, body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error('No se pudo guardar tu solicitud. Intenta de nuevo; si persiste, contáctanos por el grupo informativo.');
    return response.status === 204 ? null : response.text().then(text => text ? JSON.parse(text) : null);
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (pending || complete || !form.reportValidity()) return;
    status.textContent = '';
    status.dataset.state = '';
    if (!publicKey(config?.publishableKey)) {
      status.textContent = 'El registro aún no está disponible. Contáctanos por el grupo informativo.';
      status.dataset.state = 'error';
      return;
    }
    const data = new FormData(form);
    const value = name => String(data.get(name) || '').trim();
    if (!value('nombre') || !experiences.includes(value('experiencia_qgis')) || !schedules.includes(value('horario_preferido'))) {
      status.textContent = 'Completa tu nombre y selecciona una experiencia y un horario válidos.';
      status.dataset.state = 'error';
      return;
    }
    pending = true;
    button.disabled = true;
    button.textContent = 'Enviando…';
    form.setAttribute('aria-busy', 'true');
    try {
      // REST equivalent of supabase.rpc('registrar_inscripcion', params).
      await post('rpc/registrar_inscripcion', {
        p_email: value('email').toLowerCase(),
        p_nombre: value('nombre'),
        p_instagram: value('instagram') || null,
        p_whatsapp: value('whatsapp'),
        p_curso_id: '334bf0e8-14fb-4511-a68c-308ed3b75a23',
        p_experiencia_qgis: value('experiencia_qgis'),
        p_horario_preferido: value('horario_preferido'),
        p_que_descubrir: value('que_descubrir'),
        p_primera_palabra: value('primera_palabra'),
        p_creencia_a_probar: value('creencia_a_probar'),
      }, 'return=representation');
      complete = true;
      form.reset();
      status.dataset.state = 'success';
      status.textContent = '¡Solicitud enviada! Te contactaremos para confirmar horarios y los siguientes pasos.';
      button.textContent = 'Solicitud enviada';
    } catch (error) {
      status.dataset.state = 'error';
      status.textContent = error instanceof TypeError
        ? 'No pudimos confirmar el envío. Revisa tu conexión e intenta de nuevo.' : error.message;
      button.textContent = 'Enviar solicitud';
    } finally {
      pending = false;
      button.disabled = complete;
      form.removeAttribute('aria-busy');
    }
  });
})();
