import { argsFrom, loadPeople, numberArg, validatePeople, writeOut } from '../pipeline/common.mjs';
import { solve } from './solver.mjs';

async function main() {
  const args = argsFrom(process.argv.slice(2));
  const people = validatePeople(await loadPeople(args));
  const result = solve(people, {
    maxGroups: numberArg(args['max-grupos'], 4, 1, 5),
    cupo: numberArg(args.cupo, Infinity, 1),
    coverageTarget: numberArg(args['cobertura-objetivo'], 0.85, 0, 1),
    includeContacted: Boolean(args['incluir-contactados']),
  });
  const json = await writeOut('propuesta-grupos.json', result);
  const lines = [
    `Elegibles: ${result.elegibles}. Cubiertos: ${result.cobertura}. Días distintos: ${result.dias}.`,
    result.objetivo_alcanzado ? 'Se alcanzó la cobertura objetivo.' : 'No se alcanzó la cobertura objetivo; se muestra la máxima posible.',
    '', 'Grupos:',
    ...result.grupos.map((group, index) => `${index + 1}. ${group.block} · ${group.size} · IDs: ${group.ids.join(', ')}`),
    '', 'No cubiertos:', ...result.no_cubiertos.map(person => `${person.id}: ${person.motivo}`),
    '', 'Votos posteriores al 29 nov, 20:00 CDMX:', ...result.votos_tardios,
    '', 'Cobertura máxima con hasta N días:',
    ...result.pareto.map(row => `${row.max_dias} ${row.max_dias === 1 ? 'día' : 'días'}: ${row.cobertura_maxima}/${result.elegibles}`),
  ];
  const report = await writeOut('propuesta-grupos.txt', lines.join('\n') + '\n');
  console.log(`Propuesta local: ${json}\nResumen local: ${report}`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
