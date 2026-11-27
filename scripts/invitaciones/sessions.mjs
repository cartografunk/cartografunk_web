function settings() {
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY)
    throw new Error('Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.');
  return { url: process.env.SUPABASE_URL, key: process.env.SUPABASE_SERVICE_ROLE_KEY };
}

async function request(route, method = 'GET', body) {
  const { url, key } = settings();
  const response = await fetch(`${url}/rest/v1/sesiones${route}`, {
    method, headers: { apikey: key, Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=representation' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error(`Supabase sesiones: HTTP ${response.status}`);
  return response.json();
}

export const sessionStore = {
  async exists(group, number) {
    const rows = await request(`?select=evento_id,meet_url&grupo=eq.${encodeURIComponent(group)}&numero_sesion=eq.${number}`);
    return rows[0] || null;
  },
  save: session => request('?on_conflict=grupo,numero_sesion', 'POST', session),
};
