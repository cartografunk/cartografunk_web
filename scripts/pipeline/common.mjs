import fs from 'node:fs/promises';
import path from 'node:path';

export const COURSE_ID = 'a77e51c2-441a-4bac-9a25-922aa99ab323';
export const COURSE_TITLE = 'Agentes de IA para hacer mi tesis y todo lo que no quiero hacer';
export const OUT_DIR = path.resolve('out');

export function argsFrom(argv) {
  const result = {};
  const flags = new Set(['apply', 'supabase', 'incluir-contactados']);
  for (let i = 0; i < argv.length; i++) {
    const part = argv[i];
    if (!part.startsWith('--')) throw new Error(`Argumento inesperado: ${part}`);
    const [key, inline] = part.slice(2).split('=', 2);
    if (flags.has(key)) {
      if (inline !== undefined || (argv[i + 1] && !argv[i + 1].startsWith('--')))
        throw new Error(`--${key} no acepta valor; úsalo solo como bandera.`);
      result[key] = true;
      continue;
    }
    if (inline !== undefined) result[key] = inline;
    else if (argv[i + 1] && !argv[i + 1].startsWith('--')) result[key] = argv[++i];
    else result[key] = true;
  }
  return result;
}

export function numberArg(value, fallback, min, max = Infinity) {
  if (value === undefined) return fallback;
  const n = Number(value);
  if (!Number.isFinite(n) || n < min || n > max) throw new Error(`Valor numérico inválido: ${value}`);
  return n;
}

export async function readJson(file) {
  return JSON.parse(await fs.readFile(path.resolve(file), 'utf8'));
}

export async function writeOut(name, value) {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const target = path.join(OUT_DIR, name);
  await fs.writeFile(target, typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n', { mode: 0o600 });
  return target;
}

async function getRows(table, select, filter = '') {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error('Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.');
  const response = await fetch(`${url}/rest/v1/${table}?select=${encodeURIComponent(select)}${filter}`, {
    headers: { apikey: key, Authorization: `Bearer ${key}` },
  });
  if (!response.ok) throw new Error(`Supabase ${table}: HTTP ${response.status}`);
  return response.json();
}

export async function loadPeople(args) {
  if (args.input) {
    const data = await readJson(args.input);
    if (!Array.isArray(data.inscripciones)) throw new Error('El JSON debe contener inscripciones[].');
    return data.inscripciones;
  }
  if (!args.supabase) throw new Error('Indica --input archivo.json o --supabase --apply.');
  if (!args.apply) throw new Error('Leer datos reales requiere --apply.');
  const course = args['course-id'] || COURSE_ID;
  const rows = await getRows('inscripciones', 'id,usuario_id,estatus,created_at,respuestas,pago_comprobado,beca_aprobada,mensaje_variante,primer_mensaje_at,primera_respuesta_at', `&curso_id=eq.${course}`);
  const ids = rows.map(row => row.usuario_id);
  const inscriptionIds = rows.map(row => row.id);
  if (!rows.length) return [];
  const users = await getRows('usuarios', 'id,nombre,email,whatsapp', `&id=in.(${ids.join(',')})`);
  const votes = await getRows('crm_disponibilidad', 'inscripcion_id,opciones,sin_bloques,respondio_at', `&inscripcion_id=in.(${inscriptionIds.join(',')})`);
  const payments = await getRows('crm_pagos', 'inscripcion_id,monto_mxn,estado', `&inscripcion_id=in.(${inscriptionIds.join(',')})`);
  const byUser = new Map(users.map(user => [user.id, user]));
  const byVote = new Map(votes.map(vote => [vote.inscripcion_id, vote]));
  const verified = new Map();
  for (const payment of payments) if (payment.estado === 'verificado')
    verified.set(payment.inscripcion_id,
      (verified.get(payment.inscripcion_id) || 0) + Number(payment.monto_mxn));
  return rows.map(row => ({ ...row, ...byUser.get(row.usuario_id), id: row.id,
    pago_comprobado: (verified.get(row.id) || 0) >=
      (row.respuestas?.solicita_beca === true && row.beca_aprobada
        ? Number(row.respuestas.aporte_mxn) || Infinity : 450),
    monto_verificado_mxn: verified.get(row.id) || 0,
    disponibilidad: byVote.get(row.id) || null }));
}

export function validatePeople(people) {
  const seen = new Set();
  for (const person of people) {
    if (typeof person.id !== 'string' || !person.id) throw new Error('Inscripción sin id.');
    if (seen.has(person.id)) throw new Error(`ID de inscripción duplicado: ${person.id}`);
    seen.add(person.id);
  }
  return people;
}

export const blockDay = block => Number(block.split('-')[0]);
export const suggested = block => {
  const [day, hour] = block.split('-');
  return Number(day) <= 5 ? hour === '19' : ['09', '12', '16'].includes(hour);
};
export const validBlock = block => /^[1-7]-(09|12|16|19)$/.test(block);
