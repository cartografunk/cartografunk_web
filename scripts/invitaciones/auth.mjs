import { createHash, randomBytes } from 'node:crypto';
import { createServer } from 'node:http';
import fs from 'node:fs/promises';
import { googleCredentials } from './google.mjs';

const { client, tokenPath } = await googleCredentials();
const state = randomBytes(24).toString('hex');
const verifier = randomBytes(40).toString('base64url');
const challenge = createHash('sha256').update(verifier).digest('base64url');
const server = createServer();
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const redirect = `http://127.0.0.1:${server.address().port}`;
const url = new URL('https://accounts.google.com/o/oauth2/v2/auth');
url.search = new URLSearchParams({ client_id: client.client_id, redirect_uri: redirect,
  response_type: 'code', scope: 'https://www.googleapis.com/auth/calendar.events',
  access_type: 'offline', prompt: 'consent', state,
  code_challenge: challenge, code_challenge_method: 'S256' }).toString();
console.log(`Abre este enlace y autoriza desde la cuenta organizadora:\n${url}`);

try {
  const code = await Promise.race([
    new Promise((resolve, reject) => server.on('request', (request, response) => {
      const params = new URL(request.url, redirect).searchParams;
      response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      response.end('<p>Puedes cerrar esta pestaña y volver a la terminal.</p>');
      if (params.get('state') !== state || !params.get('code')) reject(new Error('OAuth cancelado o estado inválido.'));
      else resolve(params.get('code'));
    })),
    new Promise((_, reject) => setTimeout(() => reject(new Error('OAuth expiró después de 5 minutos.')), 300000)),
  ]);
  const response = await fetch('https://oauth2.googleapis.com/token', { method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ code, client_id: client.client_id,
      client_secret: client.client_secret, redirect_uri: redirect,
      grant_type: 'authorization_code', code_verifier: verifier }) });
  if (!response.ok) throw new Error(`Google OAuth: HTTP ${response.status}`);
  const token = await response.json();
  if (!token.refresh_token) throw new Error('Google no devolvió refresh_token. Revisa el consentimiento.');
  await fs.writeFile(tokenPath, JSON.stringify({ ...token,
    expires_at: Date.now() + token.expires_in * 1000 }, null, 2) + '\n', { mode: 0o600 });
  console.log('Autorización guardada fuera del repositorio.');
} finally { server.close(); }
