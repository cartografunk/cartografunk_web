import { createHash } from 'node:crypto';
import { COURSE_TITLE, validBlock } from '../pipeline/common.mjs';

const WEEKDAYS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
const ZONE = 'America/Mexico_City';

export function eventId(group, session) {
  return `cf${createHash('sha256').update(`${group}:${session}`).digest('hex').slice(0, 30)}`;
}

export function planInvitations(people, confirmed, duration = 120) {
  if (!Number.isInteger(duration) || duration < 30 || duration > 240)
    throw new Error('Duración inválida.');
  const byId = new Map(people.map(person => [person.id, person]));
  const events = [];
  const omitted = [];
  const groups = confirmed.grupos;
  if (!Array.isArray(groups)) throw new Error('grupos-confirmados.json necesita grupos[].');
  const groupNames = new Set();
  for (const group of groups) {
    if (!group.grupo || groupNames.has(group.grupo)) throw new Error('Nombre de grupo ausente o duplicado.');
    groupNames.add(group.grupo);
    if (!validBlock(group.bloque) || !Array.isArray(group.fechas) || group.fechas.length !== 3 || !Array.isArray(group.ids))
      throw new Error(`Grupo ${group.grupo}: bloque, tres fechas explícitas e IDs son obligatorios.`);
    const [day, hour] = group.bloque.split('-');
    const dates = group.fechas.map(value => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error(`Fecha inválida en ${group.grupo}.`);
      const d = new Date(`${value}T12:00:00Z`);
      if (Number.isNaN(d.getTime()) || d.toISOString().slice(0, 10) !== value || (d.getUTCDay() || 7) !== Number(day))
        throw new Error(`Fecha ${value} no coincide con ${WEEKDAYS[Number(day) - 1]}.`);
      return d;
    });
    if (dates[1].getTime() - dates[0].getTime() !== 7 * 86400000 ||
        dates[2].getTime() - dates[1].getTime() !== 7 * 86400000)
      throw new Error(`Grupo ${group.grupo}: las tres fechas deben ser semanas consecutivas.`);
    const emails = [];
    const seen = new Set();
    for (const id of group.ids) {
      if (seen.has(id)) throw new Error(`ID duplicado en ${group.grupo}: ${id}`);
      seen.add(id);
      const person = byId.get(id);
      if (!person) { omitted.push({ id, motivo: 'inscripción ausente' }); continue; }
      if (!person.pago_comprobado) {
        omitted.push({ id, motivo: 'sin pago comprobado' }); continue;
      }
      if (!person.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(person.email)) {
        omitted.push({ id, motivo: 'correo inválido' }); continue;
      }
      emails.push(person.email);
    }
    if (!emails.length) continue;
    for (let session = 1; session <= 3; session++) {
      const date = group.fechas[session - 1];
      const start = `${date}T${hour}:00:00-06:00`;
      const end = new Date(Date.parse(start) + duration * 60000);
      const localEnd = new Date(end.getTime() - 6 * 3600000).toISOString().slice(0, 19) + '-06:00';
      const id = eventId(group.grupo, session);
      const title = `${COURSE_TITLE} · Sesión ${session}/3 · ${group.grupo}`;
      events.push({ grupo: group.grupo, numero_sesion: session, eventId: id,
        inicio: start, fin: localEnd, confirmado: group.confirmado === true, title,
        attendees: emails.map(email => ({ email })),
        calendarBody: {
          id, summary: group.confirmado === true ? title : `Pendiente · ${title}`,
          description: `${COURSE_TITLE}. Si tienes algún problema, responde a la invitación del organizador.`,
          start: { dateTime: start, timeZone: ZONE },
          end: { dateTime: localEnd, timeZone: ZONE },
          attendees: emails.map(email => ({ email })),
          guestsCanSeeOtherGuests: false,
          guestsCanInviteOthers: false,
          guestsCanModify: false,
          conferenceData: { createRequest: { requestId: `${id}m`, conferenceSolutionKey: { type: 'hangoutsMeet' } } },
        },
      });
    }
  }
  return { events, omitted };
}

export async function executePlan(plan, { calendar, sessions, sleep = ms => new Promise(resolve => setTimeout(resolve, ms)) }) {
  const results = [];
  async function retry(operation) {
    for (let attempt = 0; attempt < 4; attempt++) {
      try { return await operation(); }
      catch (error) {
        if (![403, 429].includes(error.status) || attempt === 3) throw error;
        await sleep(500 * 2 ** attempt);
      }
    }
  }
  for (const event of plan.events) {
    try {
      const existing = await sessions.exists(event.grupo, event.numero_sesion);
      if (existing) {
        if (event.confirmado) {
          const current = await retry(() => calendar.get(existing.evento_id || event.eventId));
          if (current.summary !== event.title) {
            await retry(() => calendar.patch(existing.evento_id || event.eventId, { summary: event.title }));
            results.push({ grupo: event.grupo, numero_sesion: event.numero_sesion, estado: 'confirmada' });
            continue;
          }
        }
        results.push({ grupo: event.grupo, numero_sesion: event.numero_sesion, estado: 'ya registrada' });
        continue;
      }
      let created;
      try { created = await retry(() => calendar.insert(event.calendarBody)); }
      catch (error) {
        if (error.status !== 409) throw error;
        created = await retry(() => calendar.get(event.eventId));
      }
      for (let attempt = 0; attempt < 3 && !created?.hangoutLink; attempt++) {
        await sleep(1000 * 2 ** attempt);
        created = await retry(() => calendar.get(event.eventId));
      }
      const meetUrl = created?.hangoutLink || created?.conferenceData?.entryPoints?.find(point => point.entryPointType === 'video')?.uri;
      if (!meetUrl) throw new Error('Meet pendiente de generación');
      await sessions.save({ grupo: event.grupo, numero_sesion: event.numero_sesion,
        inicio: event.inicio, fin: event.fin, evento_id: event.eventId,
        meet_url: meetUrl });
      results.push({ grupo: event.grupo, numero_sesion: event.numero_sesion, estado: 'creada' });
    } catch (error) {
      results.push({ grupo: event.grupo, numero_sesion: event.numero_sesion,
        estado: 'error', detalle: `HTTP ${error.status || 'desconocido'}` });
    }
  }
  return results;
}
