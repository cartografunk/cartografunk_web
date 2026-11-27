(() => {
  const config = window.CARTOGRAFUNK_SUPABASE;
  const form = document.getElementById('availabilityForm');
  const status = document.getElementById('availabilityStatus');
  const token = location.hash.slice(1).trim();
  const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  const blocks = [
    ['09', '09:00–11:00'], ['12', '12:00–14:00'],
    ['16', '16:00–18:00'], ['19', '19:00–21:00'],
  ];

  function setStatus(text, state = '') {
    status.textContent = text;
    status.dataset.state = state;
  }

  async function rpc(name, payload) {
    const response = await fetch(`${config.url}/rest/v1/rpc/${name}`, {
      method: 'POST',
      headers: { apikey: config.publishableKey, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(name === 'ver_horarios'
      ? 'Este enlace no está disponible. Solicita uno nuevo a Cartografunk.'
      : 'No se pudo guardar tu disponibilidad. Intenta de nuevo.');
    return data;
  }

  function draw(saved) {
    const container = document.getElementById('days');
    for (let index = 0; index < days.length; index++) {
      const fieldset = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = days[index];
      fieldset.append(legend);
      const grid = document.createElement('div');
      grid.className = 'slot-grid';
      for (const [hour, label] of blocks) {
        const option = document.createElement('label');
        option.className = 'slot';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'horario';
        checkbox.value = `${index + 1}-${hour}`;
        checkbox.checked = saved.includes(checkbox.value);
        option.append(checkbox, document.createTextNode(label));
        grid.append(option);
      }
      fieldset.append(grid);
      container.append(fieldset);
    }
  }

  async function load() {
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(token)) {
      setStatus('Este enlace de votación no es válido. Solicita uno nuevo a Cartografunk.', 'error');
      return;
    }
    try {
      const data = await rpc('ver_horarios', { p_token: token });
      document.getElementById('courseName').textContent = data.curso;
      document.getElementById('availabilityComment').value = data.comentario || '';
      draw(data.opciones || []);
      form.hidden = false;
      if (data.respondio_at) setStatus('Ya recibimos una respuesta. Puedes actualizarla si cambió tu disponibilidad.', 'success');
    } catch (error) { setStatus(error.message, 'error'); }
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const options = [...form.querySelectorAll('input[name="horario"]:checked')].map(input => input.value);
    const comment = document.getElementById('availabilityComment').value.trim();
    if (!options.length && !comment) {
      setStatus('Marca al menos un horario o escribe cuándo sí puedes.', 'error');
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    setStatus('Guardando…');
    try {
      await rpc('guardar_horarios', { p_token: token, p_opciones: options, p_comentario: comment || null });
      setStatus('¡Gracias! Guardamos tu disponibilidad. Te avisaremos antes de confirmar fechas y reuniones.', 'success');
    } catch (error) { setStatus(error.message, 'error'); }
    finally { button.disabled = false; }
  });

  load();
})();
