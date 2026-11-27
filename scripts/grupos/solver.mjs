import { blockDay, suggested, validBlock } from '../pipeline/common.mjs';

export const BLOCKS = Array.from({ length: 7 }, (_, day) =>
  ['09', '12', '16', '19'].map(hour => `${day + 1}-${hour}`)).flat();

function assign(people, blocks, cupo) {
  const members = new Map(blocks.map(block => [block, []]));
  const byPerson = new Map();
  const ordered = [...people].sort((a, b) =>
    a.options.filter(option => blocks.includes(option)).length - b.options.filter(option => blocks.includes(option)).length ||
    a.id.localeCompare(b.id));

  function place(person, visited) {
    const options = person.options.filter(option => blocks.includes(option))
      .sort((a, b) => members.get(a).length - members.get(b).length || a.localeCompare(b));
    for (const block of options) {
      if (visited.has(block)) continue;
      visited.add(block);
      const group = members.get(block);
      if (group.length < cupo) {
        group.push(person);
        byPerson.set(person.id, block);
        return true;
      }
      for (let i = 0; i < group.length; i++) {
        const displaced = group[i];
        group.splice(i, 1);
        byPerson.delete(displaced.id);
        if (place(displaced, visited)) {
          group.push(person);
          byPerson.set(person.id, block);
          return true;
        }
        group.splice(i, 0, displaced);
        byPerson.set(displaced.id, block);
      }
    }
    return false;
  }
  for (const person of ordered) place(person, new Set());
  const groups = [...members].filter(([, list]) => list.length)
    .map(([block, list]) => ({ block, ids: list.map(person => person.id).sort(), size: list.length }));
  return { groups, assigned: byPerson };
}

function candidates(people, maxGroups, cupo) {
  const relevant = BLOCKS.filter(block => people.some(person => person.options.includes(block)));
  const current = [];
  const proposals = [];
  function choose(start) {
    if (current.length) {
      const result = assign(people, current, cupo);
      const days = new Set(result.groups.map(group => blockDay(group.block))).size;
      if (result.groups.length) {
        const sizes = result.groups.map(group => group.size);
        const imbalance = Math.max(...sizes) - Math.min(...sizes);
        proposals.push({ ...result, coverage: result.assigned.size, days,
          groupCount: result.groups.length, imbalance,
          suggestedCount: result.groups.filter(group => suggested(group.block)).length });
      }
    }
    if (current.length >= maxGroups) return;
    for (let index = start; index < relevant.length; index++) {
      current.push(relevant[index]);
      choose(index + 1);
      current.pop();
    }
  }
  choose(0);
  return proposals;
}

export function solve(people, { maxGroups = 4, cupo = Infinity, coverageTarget = 0.85,
  includeContacted = false } = {}) {
  if (!Number.isInteger(maxGroups) || maxGroups < 1 || maxGroups > 5)
    throw new Error('--max-grupos debe estar entre 1 y 5.');
  if (cupo !== Infinity && (!Number.isInteger(cupo) || cupo < 1))
    throw new Error('--cupo debe ser un entero positivo.');
  if (coverageTarget < 0 || coverageTarget > 1) throw new Error('Cobertura objetivo fuera de 0..1.');
  const eligible = people.filter(person => ['inscrito', 'pagado', ...(includeContacted ? ['contactado'] : [])].includes(person.estatus));
  for (const person of eligible) {
    const vote = person.disponibilidad;
    if (vote && (!Array.isArray(vote.opciones) || vote.opciones.some(option => !validBlock(option)) ||
      (vote.sin_bloques && vote.opciones.length)))
      throw new Error(`Disponibilidad inválida para ID ${person.id}.`);
  }
  const schedulable = eligible.map(person => ({ ...person,
    options: [...new Set(person.disponibilidad?.opciones || [])].sort() }))
    .filter(person => person.disponibilidad?.respondio_at && !person.disponibilidad?.sin_bloques && person.options.length);
  const proposals = candidates(schedulable, maxGroups, cupo);
  const targetCount = Math.ceil(eligible.length * coverageTarget);
  const viable = proposals.filter(proposal => proposal.coverage >= targetCount);
  const pool = viable.length ? viable : proposals;
  pool.sort((a, b) =>
    (viable.length ? a.days - b.days : b.coverage - a.coverage) ||
    a.days - b.days || a.groupCount - b.groupCount || a.imbalance - b.imbalance ||
    b.suggestedCount - a.suggestedCount ||
    a.groups.map(group => group.block).join(',').localeCompare(b.groups.map(group => group.block).join(',')));
  const best = pool[0] || { groups: [], assigned: new Map(), coverage: 0, days: 0, groupCount: 0 };
  const pareto = Array.from({ length: 7 }, (_, index) => ({
    max_dias: index + 1,
    cobertura_maxima: Math.max(0, ...proposals.filter(proposal => proposal.days <= index + 1)
      .map(proposal => proposal.coverage)),
  }));
  const unassigned = eligible.filter(person => !best.assigned.has(person.id)).map(person => ({
    id: person.id,
    motivo: !person.disponibilidad?.respondio_at ? 'sin respuesta'
      : person.disponibilidad.sin_bloques || !(person.disponibilidad.opciones || []).length
        ? 'sin horario común' : 'sin horario común o cupo',
  }));
  const lateAfter = Date.parse('2026-11-30T02:00:00Z');
  return {
    objetivo: coverageTarget, objetivo_alcanzado: best.coverage >= targetCount,
    elegibles: eligible.length, cobertura: best.coverage, dias: best.days,
    grupos: best.groups, no_cubiertos: unassigned, pareto,
    votos_tardios: eligible.filter(person =>
      person.disponibilidad?.respondio_at && Date.parse(person.disponibilidad.respondio_at) > lateAfter)
      .map(person => person.id),
  };
}
