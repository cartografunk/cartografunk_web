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
  const noSlots = document.getElementById('noSlots');
  const recommended = (day, hour) => day <= 5 ? hour === '19' : ['09', '12', '16'].includes(hour);
  const closingTime = Date.parse('2026-12-07T02:00:00Z');

  function setStatus(text, state = '') {
    status.textContent = text;
    status.dataset.state = state;
  }

  async function rpc(name, payload) {
    let response;
    try {
      response = await fetch(`${config.url}/rest/v1/rpc/${name}`, {
        method: 'POST',
        headers: { apikey: config.publishableKey, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        cache: 'no-store',
      });
    } catch {
      throw new Error('Sin conexión. Revisa tu internet e intenta de nuevo.');
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      if (data?.message === 'La votación está cerrada')
        throw new Error('La votación ya cerró. Te escribiremos con tu grupo.');
      if (data?.message === 'Enlace inválido o vencido' || name === 'ver_horarios')
        throw new Error('Este enlace no está disponible. Solicita uno nuevo a Cartografunk.');
      throw new Error('No se pudo guardar tu disponibilidad. Intenta de nuevo.');
    }
    return data;
  }

  function drawGroup(container, saved, showRecommended) {
    for (let index = 0; index < days.length; index++) {
      const dayBlocks = blocks.filter(([hour]) => recommended(index + 1, hour) === showRecommended);
      if (!dayBlocks.length) continue;
      const fieldset = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = days[index];
      fieldset.append(legend);
      const grid = document.createElement('div');
      grid.className = 'slot-grid';
      for (const [hour, label] of dayBlocks) {
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

  function draw(saved) {
    const container = document.getElementById('days');
    const intro = document.createElement('p');
    intro.className = 'schedule-section-title';
    intro.textContent = 'Horarios sugeridos';
    container.append(intro);
    drawGroup(container, saved, true);
    const more = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Ver más horarios';
    more.append(summary);
    drawGroup(more, saved, false);
    more.open = saved.some(value => {
      const [day, hour] = value.split('-');
      return !recommended(Number(day), hour);
    });
    container.append(more);
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
      noSlots.checked = Boolean(data.sin_bloques);
      form.hidden = Date.now() >= closingTime;
      if (form.hidden) {
        setStatus('La votación ya cerró. Te escribiremos con tu grupo.', 'success');
        return;
      }
      if (data.respondio_at) setStatus('Ya recibimos una respuesta. Puedes actualizarla si cambió tu disponibilidad.', 'success');
    } catch (error) { setStatus(error.message, 'error'); }
  }

  form.addEventListener('change', event => {
    if (event.target === noSlots && noSlots.checked) {
      form.querySelectorAll('input[name="horario"]').forEach(input => { input.checked = false; });
    } else if (event.target.matches('input[name="horario"]') && event.target.checked) {
      noSlots.checked = false;
    }
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (Date.now() >= closingTime) {
      form.hidden = true;
      setStatus('La votación ya cerró. Te escribiremos con tu grupo.', 'error');
      return;
    }
    const options = [...form.querySelectorAll('input[name="horario"]:checked')].map(input => input.value);
    const comment = document.getElementById('availabilityComment').value.trim();
    if (!options.length && !noSlots.checked && !comment) {
      setStatus('Marca al menos un horario, indica que ninguno te sirve o escribe cuándo sí puedes.', 'error');
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    setStatus('Guardando…');
    try {
      await rpc('guardar_horarios_v2', { p_token: token, p_opciones: options,
        p_sin_bloques: noSlots.checked, p_comentario: comment || null });
      setStatus('¡Gracias! Guardamos tu disponibilidad. Te avisaremos antes de confirmar fechas y reuniones.', 'success');
    } catch (error) { setStatus(error.message, 'error'); }
    finally { button.disabled = false; }
  });

  load();
})();
