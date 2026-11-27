import { argsFrom, loadPeople, numberArg, readJson, validatePeople, writeOut } from '../pipeline/common.mjs';
import { planInvitations, executePlan } from './lib.mjs';

async function main() {
  const args = argsFrom(process.argv.slice(2));
  if (!args.confirmados) throw new Error('Indica --confirmados grupos-confirmados.json.');
  const people = validatePeople(await loadPeople(args));
  const confirmed = await readJson(args.confirmados);
  const plan = planInvitations(people, confirmed, numberArg(args.duracion, 120, 30, 240));
  console.log(`${plan.events.length} eventos preparados para ${new Set(plan.events.flatMap(event => event.attendees.map(a => a.email))).size} personas; ${plan.omitted.length} personas omitidas.`);
  if (!args.apply) {
    console.log('Dry-run: no se creó ningún evento ni se envió ninguna invitación.');
    return;
  }
  const { calendarClient } = await import('./google.mjs');
  const { sessionStore } = await import('./sessions.mjs');
  const results = await executePlan(plan, { calendar: calendarClient, sessions: sessionStore });
  console.log(await writeOut('resultado-invitaciones.json', { resultados: results, omitidos: plan.omitted }));
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
