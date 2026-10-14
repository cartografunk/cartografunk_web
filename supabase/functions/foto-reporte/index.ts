import { json, preflight, rpc, serviceConfig, serviceHeaders } from '../_shared/reporte-agua.ts'

const FOLIO = /^AGUA-[0-9]{8}-[A-F0-9]{12}$/

Deno.serve(async (request) => {
  const options = preflight(request, 'GET, OPTIONS')
  if (options) return options
  if (request.method !== 'GET') return json(request, { error: 'Método no permitido.' }, 405, 'GET, OPTIONS')

  const folio = new URL(request.url).searchParams.get('folio') ?? ''
  if (!FOLIO.test(folio)) return json(request, { error: 'Foto no disponible.' }, 404, 'GET, OPTIONS')

  try {
    const ruta = await rpc<string | null>('ruta_foto_reporte_agua', { p_folio: folio })
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
