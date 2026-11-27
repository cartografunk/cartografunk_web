import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { argsFrom, readJson, validatePeople } from './common.mjs';
import { solve } from '../grupos/solver.mjs';
import { eventId, executePlan, planInvitations } from '../invitaciones/lib.mjs';

const fixture = (await readJson('fixtures/pipeline.json')).inscripciones;
const person = (id, options, extra = {}) => ({ id, estatus: 'inscrito',
  disponibilidad: { opciones: options, sin_bloques: false, respondio_at: '2026-11-28T00:00:00Z' }, ...extra });

test('--apply requiere bandera explícita sin valor', () => {
  assert.equal(argsFrom(['--apply']).apply, true);
  assert.throws(() => argsFrom(['--apply=false']), /no acepta valor/);
  assert.throws(() => argsFrom(['--apply', 'false']), /no acepta valor/);
});

test('un día con dos grupos cubre a todos', () => {
  const result = solve([person('a', ['6-09']), person('b', ['6-12'])], { coverageTarget: 1 });
  assert.equal(result.dias, 1);
  assert.equal(result.grupos.length, 2);
  assert.equal(result.cobertura, 2);
});

test('sin coincidencia, cupo y cobertura parcial', () => {
  const input = [person('a', ['6-09']), person('b', ['7-09'])];
  assert.equal(solve(input, { maxGroups: 1, coverageTarget: 1 }).cobertura, 1);
  assert.equal(solve([person('a', ['6-09']), person('b', ['6-09'])],
    { cupo: 1, coverageTarget: 1 }).cobertura, 1);
});

test('sin respuesta, ninguno, votos tardíos y estatus', () => {
  const result = solve(fixture, { coverageTarget: 0.5 });
  assert.equal(result.elegibles, 4);
  assert.ok(result.no_cubiertos.some(row => row.id === 'p04' && row.motivo === 'sin horario común'));
  assert.deepEqual(result.votos_tardios, ['p02']);
  assert.equal(solve(fixture, { includeContacted: true }).elegibles, 5);
  assert.equal(solve(fixture, { includeContacted: true }).no_cubiertos.find(row => row.id === 'p05').motivo, 'sin respuesta');
});

test('duplicados rechazados y desempate determinista', () => {
  assert.throws(() => validatePeople([person('a', []), person('a', [])]), /duplicado/);
  const input = [person('a', ['6-09', '7-09']), person('b', ['6-09', '7-09'])];
  assert.deepEqual(solve(input, { coverageTarget: 1 }).grupos, solve([...input].reverse(), { coverageTarget: 1 }).grupos);
  assert.throws(() => solve([person('a', ['8-09'])]), /inválida/);
});

test('mensajes locales alternan A/B y generan enlaces sin enviar', async () => {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'cartofunk-pipeline-'));
  try {
    await fs.cp(path.join(root, 'templates'), path.join(temp, 'templates'), { recursive: true });
    const input = path.join(temp, 'input.json');
    const records = [0, 1].map(index => ({ id: `p${index}`, estatus: 'interesado',
      created_at: `2026-11-27T12:0${index}:00Z`, nombre: `Persona ${index}`,
      whatsapp: '5'.repeat(10), respuestas: { solicita_beca: false } }));
    await fs.writeFile(input, JSON.stringify({ inscripciones: records }));
    const command = spawnSync(process.execPath, [path.join(root, 'scripts/mensajes/index.mjs'),
      '--input', input, '--tipo', 'primer-contacto', '--plazo', '1 de diciembre', '--apply'],
    { cwd: temp, encoding: 'utf8' });
    assert.equal(command.status, 0, command.stderr);
    const output = JSON.parse(await fs.readFile(path.join(temp, 'out', 'mensajes-primer-contacto.json'), 'utf8'));
    assert.deepEqual(output.mensajes.map(row => row.variante), ['A', 'B']);
    assert.ok(output.mensajes.every(row => row.enlace.startsWith('https://wa.me/')));
  } finally { await fs.rm(temp, { recursive: true, force: true }); }
});

test('invitaciones omiten impagos y usan fechas explícitas', () => {
  const people = fixture.map(p => ({ ...p, email: `${p.id}@${'example.invalid'}` }));
  const confirmed = { grupos: [{ grupo: 'g1', bloque: '6-09', confirmado: false,
    fechas: ['2026-12-12', '2026-12-19', '2026-12-26'], ids: ['p01', 'p03', 'p04'] }] };
  const plan = planInvitations(people, confirmed);
  assert.equal(plan.events.length, 3);
  assert.equal(plan.events[0].attendees.length, 2);
  assert.equal(plan.omitted[0].id, 'p04');
  assert.match(plan.events[0].calendarBody.summary, /^Pendiente/);
  assert.match(eventId('g1', 1), /^[a-v0-9]+$/);
  assert.throws(() => planInvitations(people, { grupos: [{ ...confirmed.grupos[0], fechas: ['2026-12-12', '2026-12-20', '2026-12-26'] }] }), /coincide|consecutivas/);
});

test('Calendar mock: crea una vez y retira Pendiente solo por confirmación manual', async () => {
  const people = [person('a', ['6-09'], { pago_comprobado: true, email: ['a', 'example.invalid'].join('@') })];
  const group = { grupo: 'g1', bloque: '6-09', fechas: ['2026-12-12', '2026-12-19', '2026-12-26'], ids: ['a'] };
  const events = new Map();
  const saved = new Map();
  const calendar = {
    async insert(body) { assert.equal(body.guestsCanSeeOtherGuests, false); events.set(body.id, { ...body, hangoutLink: 'https://meet.google.com/fake' }); return events.get(body.id); },
    async get(id) { return events.get(id); },
    async patch(id, body) { events.set(id, { ...events.get(id), ...body }); return events.get(id); },
  };
  const sessions = {
    async exists(g, n) { return saved.get(`${g}:${n}`); },
    async save(row) { saved.set(`${row.grupo}:${row.numero_sesion}`, row); },
  };
  const first = await executePlan(planInvitations(people, { grupos: [group] }), { calendar, sessions, sleep: async () => {} });
  assert.equal(first.filter(row => row.estado === 'creada').length, 3);
  await executePlan(planInvitations(people, { grupos: [group] }), { calendar, sessions, sleep: async () => {} });
  assert.equal(events.size, 3);
  const confirmed = await executePlan(planInvitations(people, { grupos: [{ ...group, confirmado: true }] }), { calendar, sessions, sleep: async () => {} });
  assert.equal(confirmed.filter(row => row.estado === 'confirmada').length, 3);
  assert.ok([...events.values()].every(event => !event.summary.startsWith('Pendiente')));
});

test('Calendar mock: reintenta 429 y recupera evento tras 409', async () => {
  const people = [person('a', ['6-09'], { pago_comprobado: true, email: ['a', 'example.invalid'].join('@') })];
  const plan = planInvitations(people, { grupos: [{ grupo: 'g2', bloque: '6-09',
    fechas: ['2026-12-12', '2026-12-19', '2026-12-26'], ids: ['a'] }] });
  plan.events = plan.events.slice(0, 2);
  let calls = 0;
  const saved = [];
  const calendar = {
    async insert(body) {
      calls++;
      if (calls === 1) throw Object.assign(new Error('rate limit'), { status: 429 });
      if (calls === 3) throw Object.assign(new Error('exists'), { status: 409 });
      return { ...body, hangoutLink: 'https://meet.google.com/fake' };
    },
    async get(id) { return { id, hangoutLink: 'https://meet.google.com/fake' }; },
  };
  const sessions = { async exists() { return null; }, async save(row) { saved.push(row); } };
  const result = await executePlan(plan, { calendar, sessions, sleep: async () => {} });
  assert.equal(result.filter(row => row.estado === 'creada').length, 2);
  assert.equal(saved.length, 2);
});
