(() => {
  const form = document.getElementById('aiCourseForm');
  if (!form) return;

  const config = window.CARTOGRAFUNK_SUPABASE;
  const button = form.querySelector('button[type="submit"]');
  const status = document.getElementById('aiCourseFormStatus');
  const fullPrice = document.getElementById('aiFullPrice');
  const scholarship = document.getElementById('aiScholarship');
  const scholarshipFields = document.getElementById('aiScholarshipFields');
  const contribution = document.getElementById('aiContribution');
  const exchange = document.getElementById('aiExchange');
  let pending = false;
  let complete = false;

  function updateScholarshipFields() {
    const requested = scholarship.checked;
    scholarshipFields.hidden = !requested;
    contribution.disabled = !requested;
    contribution.required = requested;
    exchange.disabled = !requested;
    exchange.required = requested;
    if (!requested) {
      contribution.value = '';
      exchange.value = '';
    }
  }

  function publicKey(key) {
    if (typeof key !== 'string') return false;
    if (key.startsWith('sb_publishable_')) return true;
    try {
      const payload = key.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(payload)).role === 'anon';
    } catch { return false; }
  }

  fullPrice.addEventListener('change', updateScholarshipFields);
  scholarship.addEventListener('change', updateScholarshipFields);
  updateScholarshipFields();

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (pending || complete || !form.reportValidity()) return;
    status.textContent = '';
    status.dataset.state = '';

    if (!publicKey(config?.publishableKey)) {
      status.textContent = 'El registro aún no está disponible. Escríbenos a cartografunk@gmail.com.';
      status.dataset.state = 'error';
      return;
    }

    const data = new FormData(form);
    const value = name => String(data.get(name) || '').trim();
    const age = Number(value('edad'));
    const amount = scholarship.checked ? Number(value('aporte_mxn')) : null;
    if (!Number.isInteger(age) || age < 1 || age > 120 ||
        (scholarship.checked && (!Number.isInteger(amount) || amount < 1 || amount > 1499 || !value('propuesta_intercambio')))) {
      status.textContent = 'Revisa tu edad y, si solicitas beca, el monto y tu propuesta.';
      status.dataset.state = 'error';
      return;
    }

    pending = true;
    button.disabled = true;
    button.textContent = 'Enviando…';
    form.setAttribute('aria-busy', 'true');
    try {
      const headers = {
        apikey: config.publishableKey,
        'Content-Type': 'application/json',
        Prefer: 'return=representation',
      };
      if (!config.publishableKey.startsWith('sb_publishable_')) {
        headers.Authorization = `Bearer ${config.publishableKey}`;
      }
      const response = await fetch(`${config.url}/rest/v1/rpc/registrar_inscripcion_agentes_ia`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          p_email: value('email').toLowerCase(),
          p_nombre: value('nombre'),
          p_edad: age,
          p_residencia: value('residencia'),
          p_whatsapp: value('whatsapp'),
          p_instagram: value('instagram') || null,
          p_solicita_beca: scholarship.checked,
          p_aporte_mxn: amount,
          p_propuesta_intercambio: scholarship.checked ? value('propuesta_intercambio') : null,
        }),
      });
      if (!response.ok) throw new Error('No se pudo guardar tu registro. Intenta de nuevo o escríbenos a cartografunk@gmail.com.');
      complete = true;
      form.reset();
      updateScholarshipFields();
      status.dataset.state = 'success';
      status.textContent = '¡Registro recibido! Te contactaremos con los detalles. Si solicitaste beca, revisaremos tu propuesta contigo.';
      button.textContent = 'Registro enviado';
    } catch (error) {
      status.dataset.state = 'error';
      status.textContent = error instanceof TypeError
        ? 'No pudimos confirmar el envío. Revisa tu conexión e intenta de nuevo.' : error.message;
      button.textContent = 'Enviar registro';
    } finally {
      pending = false;
      button.disabled = complete;
      form.removeAttribute('aria-busy');
    }
  });
})();
