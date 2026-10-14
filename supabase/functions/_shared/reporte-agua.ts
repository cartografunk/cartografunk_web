const origins = new Set([
  'https://cartografunk.com',
  'https://www.cartografunk.com',
  'https://cartografunk.github.io',
])

export const AMG_PROVISIONAL = {
  minLng: -103.85,
  maxLng: -102.95,
  minLat: 20.35,
  maxLat: 21.0,
} as const

export function dentroDelAmg(lng: number, lat: number): boolean {
  return Number.isFinite(lng) && Number.isFinite(lat)
    && lng >= AMG_PROVISIONAL.minLng && lng <= AMG_PROVISIONAL.maxLng
    && lat >= AMG_PROVISIONAL.minLat && lat <= AMG_PROVISIONAL.maxLat
}

function originPermitido(origin: string | null): string {
  if (origin && (origins.has(origin) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin))) {
    return origin
  }
  return 'https://cartografunk.com'
}

export function headersCors(request: Request, methods: string): HeadersInit {
  return {
    'Access-Control-Allow-Origin': originPermitido(request.headers.get('origin')),
    'Access-Control-Allow-Headers': 'apikey, authorization, content-type, x-client-info',
    'Access-Control-Allow-Methods': methods,
    'Vary': 'Origin',
  }
}

export function json(request: Request, body: unknown, status = 200, methods = 'GET, POST, OPTIONS'): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...headersCors(request, methods), 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  })
}

export function preflight(request: Request, methods: string): Response | null {
  if (request.method !== 'OPTIONS') return null
  return new Response(null, { status: 204, headers: headersCors(request, methods) })
}

export function serviceConfig(): { url: string; key: string } {
  const url = Deno.env.get('SUPABASE_URL')
  const key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  if (!url || !key) throw new Error('Falta la configuración de Supabase')
  return { url: url.replace(/\/$/, ''), key }
}

export function serviceHeaders(key: string): Record<string, string> {
  return { apikey: key, Authorization: `Bearer ${key}` }
}

export async function rpc<T>(name: string, body: Record<string, unknown>): Promise<T> {
  const { url, key } = serviceConfig()
  const response = await fetch(`${url}/rest/v1/rpc/${name}`, {
    method: 'POST',
    headers: { ...serviceHeaders(key), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`RPC ${name}: ${response.status}`)
  return await response.json() as T
}

function ipDeSolicitud(request: Request): string | null {
  const candidate = request.headers.get('cf-connecting-ip')
    ?? request.headers.get('x-forwarded-for')?.split(',')[0]
    ?? request.headers.get('x-real-ip')
  if (!candidate || candidate.length > 45 || !/^[0-9a-fA-F:.]+$/.test(candidate)) return null
  return candidate.toLowerCase()
}

export async function consumirLimite(request: Request, accion: 'enviar' | 'geocode', limite: number): Promise<boolean> {
  const ip = ipDeSolicitud(request)
  const salt = Deno.env.get('RATE_LIMIT_SALT')
  if (!ip || !salt) throw new Error('No se puede verificar el límite de envíos')
  const bytes = new TextEncoder().encode(`${salt}:${ip}`)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  const hash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('')
  return await rpc<boolean>('consumir_limite_reporte_agua', {
    p_ip_hash: hash,
    p_accion: accion,
    p_limite: limite,
  })
}
