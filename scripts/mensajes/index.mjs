import fs from 'node:fs/promises';
import path from 'node:path';
import { argsFrom, COURSE_TITLE, loadPeople, readJson, validatePeople, writeOut } from '../pipeline/common.mjs';

const names = {
  'primer-contacto': ['primer_contacto_a', 'primer_contacto_b'],
  beca: ['acuse_beca'], grupo: ['grupo_propuesto'], sesion: ['enlace_sesion'],
  'recordatorio-24h': ['recordatorio_24h'], 'recordatorio-1h': ['recordatorio_1h'],
};

function render(template, values) {
  return template.replace(/{{([a-z_]+)}}/g, (_, key) => {
    if (values[key] === undefined || values[key] === null || values[key] === '')
      throw new Error(`Falta variable ${key}`);
    return String(values[key]);
  }).trim();
}

function report(people) {
  const since = Date.now() - 7 * 86400000;
  const rows = ['A', 'B'].map(variante => {
    const members = people.filter(person => person.mensaje_variante === variante &&
      person.primer_mensaje_at && Date.parse(person.primer_mensaje_at) >= since);
    return { variante, enviados: members.filter(person => person.primer_mensaje_at).length,
      respondidos: members.filter(person => person.primera_respuesta_at &&
        Date.parse(person.primera_respuesta_at) >= since).length,
      quejas: members.filter(person => person.queja === true).length };
  });
  const stop = rows.some(row => row.quejas > 0) ||
    (rows.every(row => row.enviados >= 10) && rows[0].respondidos !== rows[1].respondidos);
  return { fecha: new Date().toISOString().slice(0, 10), variantes: rows,
    detener_ab: stop, nota: 'Señal cualitativa; sin inferencia estadística.' };
}

async function saveVariants(people, args) {
  if (!args.supabase || !args.apply) return;
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  for (const person of people) {
    if (!person.assignedVariant || person.mensaje_variante) continue;
    const response = await fetch(`${url}/rest/v1/inscripciones?id=eq.${person.id}&mensaje_variante=is.null`, {
      method: 'PATCH',
      headers: { apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
      body: JSON.stringify({ mensaje_variante: person.assignedVariant }),
    });
    if (!response.ok) throw new Error(`No se pudo guardar variante para ID ${person.id}: HTTP ${response.status}`);
  }
}

async function main() {
  const args = argsFrom(process.argv.slice(2));
  const kind = args.tipo || 'primer-contacto';
  if (!names[kind]) throw new Error(`--tipo debe ser: ${Object.keys(names).join(', ')}`);
  const people = validatePeople(await loadPeople(args));
  const confirmed = args.confirmados ? await readJson(args.confirmados) : {};
  const byId = new Map((confirmed.inscripciones || []).map(row => [row.id, row]));
  const ordered = [...people].sort((a, b) =>
    String(a.created_at).localeCompare(String(b.created_at)) || a.id.localeCompare(b.id));
  const templates = await Promise.all(names[kind].map(async name =>
    fs.readFile(path.resolve('templates', `${name}.txt`), 'utf8')));
  const result = [];
  const skipped = [];
  let variantIndex = 0;
  for (const person of ordered) {
    if (kind === 'primer-contacto' && person.respuestas?.solicita_beca !== false) continue;
    if (kind === 'beca' && person.respuestas?.solicita_beca !== true) continue;
    const detail = byId.get(person.id) || {};
    const expectedVariant = kind === 'primer-contacto' ? (variantIndex++ % 2 ? 'B' : 'A') : null;
    const variant = kind === 'primer-contacto' ? (person.mensaje_variante || expectedVariant) : null;
    if (variant) person.assignedVariant = variant;
    const template = templates[variant === 'B' ? 1 : 0];
    try {
      const text = render(template, { ...person, ...detail, curso: COURSE_TITLE,
        plazo: args.plazo, numero_sesion: detail.numero_sesion });
      const phone = String(person.whatsapp || '').replace(/\D/g, '');
      if (!/^\d{10,15}$/.test(phone)) throw new Error('WhatsApp inválido o ausente');
      result.push({ id: person.id, variante: variant, texto: text,
        enlace: `https://wa.me/${phone}?text=${encodeURIComponent(text)}` });
    } catch (error) { skipped.push({ id: person.id, motivo: error.message }); }
  }
  const weekly = report(ordered);
  console.log(`${kind}: ${result.length} textos preparados; ${skipped.length} omitidos. No se envió ningún mensaje.`);
  if (!args.apply) {
    console.log('Dry-run: añade --apply para crear archivos locales y, con --supabase, guardar variantes.');
    return;
  }
  await saveVariants(ordered.filter(person => result.some(row => row.id === person.id)), args);
  console.log(await writeOut(`mensajes-${kind}.json`, { mensajes: result, omitidos: skipped }));
  console.log(await writeOut('reporte-ab-semanal.json', weekly));
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
