import fs from 'node:fs/promises';
import path from 'node:path';

function outsideRepo(file) {
  if (!file) throw new Error('Indica rutas GOOGLE_OAUTH_CLIENT_FILE y GOOGLE_OAUTH_TOKEN_FILE fuera del repo.');
  const resolved = path.resolve(file);
  const relative = path.relative(process.cwd(), resolved);
  if (!relative.startsWith('..') && !path.isAbsolute(relative))
    throw new Error('Los archivos OAuth deben estar fuera del repositorio.');
  return resolved;
}

export async function googleCredentials() {
  const clientPath = outsideRepo(process.env.GOOGLE_OAUTH_CLIENT_FILE);
  const tokenPath = outsideRepo(process.env.GOOGLE_OAUTH_TOKEN_FILE);
  const client = (JSON.parse(await fs.readFile(clientPath, 'utf8'))).installed;
  if (!client?.client_id || !client?.client_secret) throw new Error('Cliente OAuth de escritorio inválido.');
  return { client, tokenPath };
}

export async function accessToken() {
  const { client, tokenPath } = await googleCredentials();
  const saved = JSON.parse(await fs.readFile(tokenPath, 'utf8'));
  if (saved.access_token && saved.expires_at > Date.now() + 60000) return saved.access_token;
  if (!saved.refresh_token) throw new Error('Falta refresh_token. Ejecuta auth.mjs de nuevo.');
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: client.client_id,
      client_secret: client.client_secret, refresh_token: saved.refresh_token,
      grant_type: 'refresh_token' }),
  });
  if (!response.ok) throw new Error(`Google OAuth: HTTP ${response.status}`);
  const fresh = await response.json();
  const updated = { ...saved, ...fresh, expires_at: Date.now() + fresh.expires_in * 1000 };
  await fs.writeFile(tokenPath, JSON.stringify(updated, null, 2) + '\n', { mode: 0o600 });
  return updated.access_token;
}

async function calendarRequest(method, eventId, body) {
  const route = eventId ? `/${encodeURIComponent(eventId)}` : '';
  const query = method === 'GET' ? '' : '?conferenceDataVersion=1&sendUpdates=all';
  const url = `https://www.googleapis.com/calendar/v3/calendars/primary/events${route}${query}`;
  const response = await fetch(url, { method, headers: {
    Authorization: `Bearer ${await accessToken()}`, 'Content-Type': 'application/json',
  }, body: body ? JSON.stringify(body) : undefined });
  if (!response.ok) { const error = new Error(`Calendar HTTP ${response.status}`); error.status = response.status; throw error; }
  return response.json();
}

export const calendarClient = {
  insert: body => calendarRequest('POST', null, body),
  get: id => calendarRequest('GET', id),
  patch: (id, body) => calendarRequest('PATCH', id, body),
};
