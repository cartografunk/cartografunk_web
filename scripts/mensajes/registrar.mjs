import { argsFrom, readJson } from '../pipeline/common.mjs';

async function main() {
  const args = argsFrom(process.argv.slice(2));
  if (!args.input) throw new Error('Indica --input archivo-registro.json.');
  const data = await readJson(args.input);
  if (!Array.isArray(data.registros)) throw new Error('El archivo necesita registros[].');
  for (const row of data.registros) {
    if (!/^[0-9a-f-]{36}$/i.test(row.id || '')) throw new Error('ID inválido.');
    for (const field of ['primer_mensaje_at', 'primera_respuesta_at']) {
      if (row[field] && Number.isNaN(Date.parse(row[field]))) throw new Error(`Fecha inválida: ${field}`);
    }
    if (!row.primer_mensaje_at && !row.primera_respuesta_at) throw new Error('Registro sin fecha.');
  }
  console.log(`${data.registros.length} registros de actividad preparados. No se envió ningún mensaje.`);
  if (!args.apply) { console.log('Dry-run: --apply actualiza solo las fechas indicadas.'); return; }
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error('Faltan variables de Supabase.');
  for (const row of data.registros) {
    const body = Object.fromEntries(['primer_mensaje_at', 'primera_respuesta_at']
      .filter(field => row[field]).map(field => [field, row[field]]));
    const response = await fetch(`${url}/rest/v1/inscripciones?id=eq.${row.id}`, {
      method: 'PATCH', headers: { apikey: key, Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json', Prefer: 'return=minimal' },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`No se pudo registrar ID ${row.id}: HTTP ${response.status}`);
  }
  console.log('Fechas registradas.');
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
