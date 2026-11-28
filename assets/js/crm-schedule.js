(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const rpc = (name, body) => window.CARTOGRAFUNK_CRM.rpc(name, body);
  const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  const blocks = { '09': '09:00–11:00', '12': '12:00–14:00', '16': '16:00–18:00', '19': '19:00–21:00' };
  const state = { invitations: [], groups: [], courseName: '', voteTemplate: '' };
  const today = new Intl.DateTimeFormat('sv-SE', { year: 'numeric', month: '2-digit',
    day: '2-digit', timeZone: 'America/Mexico_City' }).format(new Date());
  $('scheduleStart').min = today;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text != null) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  }

  function status(text, kind = '') {
    $('scheduleStatus').textContent = text;
    $('scheduleStatus').dataset.state = kind;
  }

  function pollUrl(token) {
    return `${location.origin}/horarios#${token}`;
  }

  function scheduleFor(startDate, dayNumber) {
    const date = new Date(`${startDate}T12:00:00Z`);
    const weekday = date.getUTCDay() || 7;
    date.setUTCDate(date.getUTCDate() + (dayNumber - weekday + 7) % 7);
    return [0, 1, 2].map(week => {
      const session = new Date(date);
      session.setUTCDate(session.getUTCDate() + week * 7);
      return session.toISOString().slice(0, 10);
    });
  }

  function endTime(hour, minutes) {
    const total = Number(hour) * 60 + minutes;
    return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
  }

  function proposeGroups(invitations) {
    const voters = invitations.filter(person => person.respondio_at && person.opciones.length);
    if (!voters.length) return { groups: [], days: [] };
    let best = null;

    for (let mask = 1; mask < 128; mask++) {
      const chosenDays = days.map((_, index) => index + 1).filter(day => mask & (1 << (day - 1)));
      if (best && chosenDays.length > best.days.length) continue;
      if (!voters.every(person => person.opciones.some(option => chosenDays.includes(Number(option[0]))))) continue;

      const remaining = new Set(voters.map(person => person.inscripcion_id));
      const groups = [];
      while (remaining.size) {
        const candidates = [...new Set(voters.flatMap(person => person.opciones))]
          .filter(option => chosenDays.includes(Number(option[0])))
          .map(option => ({
            option,
            people: voters.filter(person => remaining.has(person.inscripcion_id) && person.opciones.includes(option)),
          }))
          .filter(candidate => candidate.people.length)
          .sort((a, b) => b.people.length - a.people.length ||
            b.people.filter(person => person.precio_completo).length - a.people.filter(person => person.precio_completo).length ||
            a.option.localeCompare(b.option));
        if (!candidates.length) break;
        const chosen = candidates[0];
        groups.push({ option: chosen.option, people: chosen.people.sort((a, b) =>
          Number(b.precio_completo) - Number(a.precio_completo) || a.nombre.localeCompare(b.nombre)) });
        chosen.people.forEach(person => remaining.delete(person.inscripcion_id));
      }
      if (remaining.size) continue;
      const proposal = { days: chosenDays, groups };
      if (!best || proposal.days.length < best.days.length ||
        (proposal.days.length === best.days.length && proposal.groups.length < best.groups.length)) best = proposal;
    }
    return best || { groups: [], days: [] };
  }

  function renderGroups() {
    const invitations = state.invitations.filter(person => person.pago_habilitado !== false);
    const responded = invitations.filter(person => person.respondio_at);
    const withSlots = responded.filter(person => person.opciones.length);
    const pending = invitations.length - responded.length;
    const withoutSlots = responded.length - withSlots.length;
    const proposal = proposeGroups(invitations);
    state.groups = proposal.groups;

    const awaitingPayment = state.invitations.length - invitations.length;
    $('scheduleOverview').textContent = `${invitations.length} personas con acceso · ${responded.length} respondieron · ${pending} pendientes` +
      (awaitingPayment ? ` · ${awaitingPayment} esperan pago` : '') +
      (withoutSlots ? ` · ${withoutSlots} sin bloque compatible` : '') +
      (proposal.days.length ? ` · ${proposal.days.length} día(s) de la semana propuestos` : '');

    const container = $('scheduleGroups');
    container.replaceChildren();
    if (!proposal.groups.length) {
      container.append(node('p', 'Cuando haya respuestas con horarios, aquí aparecerán los grupos sugeridos.'));
    }
    const startDate = $('scheduleStart').value;
    const duration = Number($('scheduleDuration').value);
    for (let index = 0; index < proposal.groups.length; index++) {
      const group = proposal.groups[index];
      const [day, hour] = group.option.split('-');
      const card = node('article', null, 'schedule-group');
      card.append(node('h4', `Grupo ${index + 1} · ${days[Number(day) - 1]} ${blocks[hour]}`),
        node('p', `${group.people.length} persona(s) · mismo bloque cada semana`));
      if (startDate) {
        const dates = scheduleFor(startDate, Number(day));
        card.append(node('p', `Tres sesiones: ${dates.join(' · ')} · ${hour}:00–${endTime(hour, duration)} (CDMX)`));
      }
      const list = node('ul');
      group.people.forEach(person => {
        const label = `${person.nombre}${person.precio_completo ? ' · precio completo' : ''}`;
        list.append(node('li', label));
      });
      card.append(list);
      container.append(card);
    }
    $('copyAgenda').hidden = !(invitations.length && pending === 0 && withoutSlots === 0 &&
      proposal.groups.length && startDate);
    if (pending || withoutSlots) {
      container.append(node('p', 'La propuesta es preliminar: espera las respuestas pendientes y resuelve los horarios sin bloque antes de crear invitaciones.'));
    }
  }

  function renderInvitations() {
    const container = $('scheduleInvites');
    container.replaceChildren();
    for (const person of state.invitations) {
      const row = node('div', null, 'schedule-invite');
      const identity = node('div');
      identity.append(node('strong', person.nombre), node('small', person.email));
      if (person.precio_completo) identity.append(node('span', 'Precio completo', 'schedule-priority'));
      const answer = person.respondio_at
        ? person.opciones.length ? `Respondió · ${person.opciones.length} bloques` : 'Respondió sin bloques'
        : 'Pendiente de respuesta';
      row.append(identity, node('span', answer));
      if (person.pago_habilitado === false) {
        row.append(node('span', 'Espera pago verificado'));
      } else if (person.token) {
        const copy = node('button', 'Copiar enlace', 'secondary-button');
        copy.type = 'button';
        copy.addEventListener('click', async () => {
          try { await navigator.clipboard.writeText(pollUrl(person.token)); status(`Enlace de ${person.nombre} copiado.`, 'success'); }
          catch { status('No se pudo copiar. Intenta desde un navegador con acceso al portapapeles.', 'error'); }
        });
        row.append(copy);
        const rawDigits = String(person.whatsapp || '').replace(/\D/g, '');
        const digits = rawDigits.length === 10 ? `52${rawDigits}` : rawDigits;
        if (/^\d{10,15}$/.test(digits)) {
          const link = node('a', 'Abrir WhatsApp');
          const values = { nombre: person.nombre, curso: state.courseName,
            enlace_personal: pollUrl(person.token) };
          const message = state.voteTemplate.replace(/{{([a-z_]+)}}/g, (_, key) => values[key] || '');
          link.href = `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          row.append(link);
        }
      } else row.append(node('span', 'Genera los enlaces para invitar'));
      container.append(row);
    }
  }

  async function load(generate) {
    const courseId = $('scheduleCourse').value;
    if (!courseId) { status('Selecciona un curso.', 'error'); return; }
    $('scheduleLoad').disabled = true;
    $('scheduleGenerate').disabled = true;
    status(generate ? 'Generando enlaces…' : 'Cargando respuestas…');
    try {
      state.courseName = $('scheduleCourse').selectedOptions[0].textContent;
      const template = await fetch('/templates/votacion_horarios.txt');
      if (!template.ok) throw new Error('No se pudo cargar el mensaje de votación.');
      state.voteTemplate = await template.text();
      state.invitations = await rpc('crm_invitaciones_horario', {
        p_curso_id: courseId, p_generar: generate,
      });
      $('scheduleResults').hidden = false;
      renderInvitations();
      renderGroups();
      status(generate ? 'Enlaces listos. Compártelos con cada persona.' : 'Respuestas actualizadas.', 'success');
    } catch (error) { status(error.message, 'error'); }
    finally { $('scheduleLoad').disabled = false; $('scheduleGenerate').disabled = false; }
  }

  function agendaText() {
    const duration = Number($('scheduleDuration').value);
    const lines = [
      `Crear reuniones de ${state.courseName} en el calendario de cartografunk@gmail.com.`,
      'Zona horaria: America/Mexico_City. Crea un Google Meet distinto por sesión e invita a los correos del grupo.',
      'Revisa el plan antes de enviar invitaciones.', '',
    ];
    for (let index = 0; index < state.groups.length; index++) {
      const group = state.groups[index];
      const [day, hour] = group.option.split('-');
      const dates = scheduleFor($('scheduleStart').value, Number(day));
      lines.push(`Grupo ${index + 1} — ${days[Number(day) - 1]} ${blocks[hour]}`);
      lines.push(`Invitados: ${group.people.map(person => person.email).join(', ')}`);
      dates.forEach((date, session) => lines.push(`Sesión ${session + 1}: ${date} ${hour}:00–${endTime(hour, duration)}`));
      lines.push('');
    }
    return lines.join('\n');
  }

  $('scheduleLoad').addEventListener('click', () => load(false));
  $('scheduleGenerate').addEventListener('click', () => load(true));
  $('scheduleStart').addEventListener('change', renderGroups);
  $('scheduleDuration').addEventListener('change', renderGroups);
  $('copyAgenda').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(agendaText()); status('Agenda copiada. Revísala antes de crear las reuniones.', 'success'); }
    catch { status('No se pudo copiar la agenda.', 'error'); }
  });
})();
