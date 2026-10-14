import { consumirLimite, dentroDelAmg, json, preflight } from '../_shared/reporte-agua.ts'

type GoogleResult = {
  formatted_address?: string
  geometry?: { location?: { lat?: number; lng?: number } }
}

Deno.serve(async (request) => {
  const options = preflight(request, 'GET, OPTIONS')
  if (options) return options
  if (request.method !== 'GET') return json(request, { error: 'Método no permitido.' }, 405, 'GET, OPTIONS')

  const consulta = (new URL(request.url).searchParams.get('q') ?? '').trim()
  if (consulta.length < 3 || consulta.length > 160) {
    return json(request, { error: 'Escribe una dirección de 3 a 160 caracteres.' }, 400, 'GET, OPTIONS')
  }
  const key = Deno.env.get('GOOGLE_MAPS_API_KEY')
  if (!key) return json(request, { error: 'La búsqueda de direcciones aún no está disponible.' }, 503, 'GET, OPTIONS')

  try {
    if (!await consumirLimite(request, 'geocode', 30)) {
      return json(request, { error: 'Llegaste al límite de búsquedas por hora.' }, 429, 'GET, OPTIONS')
    }
    const url = new URL('https://maps.googleapis.com/maps/api/geocode/json')
    url.search = new URLSearchParams({
      address: consulta,
      components: 'country:MX',
      bounds: '20.35,-103.85|21.0,-102.95',
      language: 'es',
      region: 'mx',
      key,
    }).toString()
    const response = await fetch(url)
    if (!response.ok) throw new Error(`Google Geocoding: ${response.status}`)
    const body = await response.json() as { status?: string; results?: GoogleResult[] }
    if (body.status === 'ZERO_RESULTS') return json(request, { resultados: [] }, 200, 'GET, OPTIONS')
    if (body.status !== 'OK') throw new Error(`Google Geocoding: ${body.status}`)
    const resultados = (body.results ?? []).flatMap((result) => {
      const lat = result.geometry?.location?.lat
      const lng = result.geometry?.location?.lng
      const direccion = result.formatted_address
      return typeof lat === 'number' && typeof lng === 'number' && direccion
        && dentroDelAmg(lng, lat) ? [{ lat, lng, direccion }] : []
    }).slice(0, 5)
    return json(request, { resultados }, 200, 'GET, OPTIONS')
  } catch (error) {
    console.error('No se pudo geocodificar', error)
    return json(request, { error: 'No pudimos buscar la dirección. Intenta de nuevo.' }, 503, 'GET, OPTIONS')
  }
})
