import { json, preflight, rpc, serviceConfig, serviceHeaders } from '../_shared/reporte-agua.ts'

const PUBLIC_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

Deno.serve(async (request) => {
  const options = preflight(request, 'GET, OPTIONS')
  if (options) return options
  if (request.method !== 'GET') return json(request, { error: 'Método no permitido.' }, 405, 'GET, OPTIONS')

  const publicId = new URL(request.url).searchParams.get('public_id') ?? ''
  if (!PUBLIC_ID.test(publicId)) return json(request, { error: 'Foto no disponible.' }, 404, 'GET, OPTIONS')

  try {
    const ruta = await rpc<string | null>('ruta_foto_reporte_agua', { p_public_id: publicId })
    if (!ruta) return json(request, { error: 'Foto no disponible.' }, 404, 'GET, OPTIONS')

    const { url, key } = serviceConfig()
    const firmado = await fetch(`${url}/storage/v1/object/sign/reporte-agua-fotos/${encodeURIComponent(ruta)}`, {
      method: 'POST',
      headers: { ...serviceHeaders(key), 'Content-Type': 'application/json' },
      body: JSON.stringify({ expiresIn: 120 }),
    })
    if (!firmado.ok) throw new Error(`No se pudo firmar la foto: ${firmado.status}`)
    const result = await firmado.json() as { signedURL?: string }
    if (!result.signedURL) throw new Error('Storage no devolvió URL firmada')
    const fotoUrl = new URL(
      result.signedURL.startsWith('/object/') ? `/storage/v1${result.signedURL}` : result.signedURL,
      url,
    )
    if (fotoUrl.origin !== new URL(url).origin) throw new Error('URL firmada inesperada')
    return json(request, { url: fotoUrl.toString(), expira_en_segundos: 120 }, 200, 'GET, OPTIONS')
  } catch (error) {
    console.error('No se pudo servir la foto', error)
    return json(request, { error: 'Foto no disponible.' }, 503, 'GET, OPTIONS')
  }
})
