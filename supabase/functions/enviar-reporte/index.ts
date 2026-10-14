import {
  consumirLimite, dentroDelAmg, json, preflight, rpc,
  serviceConfig, serviceHeaders,
} from '../_shared/reporte-agua.ts'
import { validarFoto } from '../_shared/imagen-reporte.ts'

type Categoria = { id: string; codigo: string; nombre: string }
const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const MAX_MULTIPART = 6 * 1024 * 1024
const hostnamesTurnstile = new Set([
  'cartografunk.com', 'www.cartografunk.com', 'cartografunk.github.io',
  'localhost', '127.0.0.1',
])

function texto(data: FormData, key: string): string {
  const value = data.get(key)
  return typeof value === 'string' ? value.trim() : ''
}

async function formularioLimitado(request: Request): Promise<FormData> {
  if (!request.body) throw new Error('Sin datos')
  const reader = request.body.getReader()
  const chunks: Uint8Array[] = []
  let size = 0
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      size += value.byteLength
      if (size > MAX_MULTIPART) throw new Error('Demasiado grande')
      chunks.push(value)
    }
  } finally {
    reader.releaseLock()
  }
  const bytes = new Uint8Array(size)
  let offset = 0
  for (const chunk of chunks) {
    bytes.set(chunk, offset)
    offset += chunk.byteLength
  }
  return await new Request(request.url, {
    method: 'POST',
    headers: { 'content-type': request.headers.get('content-type') ?? '' },
    body: bytes.buffer,
  }).formData()
}

async function verificarTurnstile(token: string): Promise<boolean> {
  const secret = Deno.env.get('TURNSTILE_SECRET_KEY')
  if (!secret) throw new Error('Falta TURNSTILE_SECRET_KEY')
  const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: new URLSearchParams({ secret, response: token }),
  })
  if (!response.ok) throw new Error('No se pudo verificar Turnstile')
  const result = await response.json() as { success?: boolean; action?: string; hostname?: string }
  return result.success === true && result.action === 'enviar_reporte'
    && typeof result.hostname === 'string' && hostnamesTurnstile.has(result.hostname)
}

function hoyEnGuadalajara(): string {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('es-MX', {
    timeZone: 'America/Mexico_City', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date()).map(part => [part.type, part.value]))
  return `${parts.year}-${parts.month}-${parts.day}`
}

Deno.serve(async (request) => {
  const options = preflight(request, 'GET, POST, OPTIONS')
  if (options) return options

  if (request.method === 'GET') {
    try {
      const categorias = await rpc<Categoria[]>('categorias_reporte_agua', {})
      return json(request, { categorias })
    } catch (error) {
      console.error('Categorías no disponibles', error)
      return json(request, { error: 'No pudimos cargar las categorías.' }, 503)
    }
  }
  if (request.method !== 'POST') return json(request, { error: 'Método no permitido.' }, 405)
  if (!request.headers.get('content-type')?.startsWith('multipart/form-data')) {
    return json(request, { error: 'Envía el formulario con una foto.' }, 415)
  }
  const declaredSize = Number(request.headers.get('content-length') ?? 0)
  if (declaredSize > MAX_MULTIPART) return json(request, { error: 'La foto supera el límite de 5 MB.' }, 413)

  try {
    const data = await formularioLimitado(request)
    const lat = Number(texto(data, 'lat'))
    const lng = Number(texto(data, 'lng'))
    const categoriaId = texto(data, 'categoria_id')
    const nota = texto(data, 'nota')
    const calle = texto(data, 'calle_texto')
    const fechaTexto = texto(data, 'fecha_observacion')
    const fecha = new Date(`${fechaTexto}T12:00:00Z`)
    const contactoAutorizado = texto(data, 'consentimiento_contacto') === 'si'
    const email = contactoAutorizado ? texto(data, 'email') : ''
    const telefono = contactoAutorizado ? texto(data, 'telefono') : ''
    const token = texto(data, 'turnstile_token')
    const foto = data.get('foto')

    if (!dentroDelAmg(lng, lat)) return json(request, { error: 'El punto está fuera del área provisional de Guadalajara.' }, 400)
    if (!ID.test(categoriaId) || nota.length < 1 || nota.length > 500 || calle.length > 200) {
      return json(request, { error: 'Revisa la categoría, la nota y la calle.' }, 400)
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(fechaTexto)
        || Number.isNaN(fecha.getTime()) || fecha.toISOString().slice(0, 10) !== fechaTexto
        || fechaTexto > hoyEnGuadalajara()
        || fecha.getTime() < Date.now() - 366 * 86400000) {
      return json(request, { error: 'Revisa la fecha aproximada.' }, 400)
    }
    if (email.length > 254 || telefono.length > 40
        || (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) {
      return json(request, { error: 'Revisa los datos de contacto.' }, 400)
    }
    if (texto(data, 'consentimiento_publicacion') !== 'si') {
      return json(request, { error: 'Falta tu consentimiento.' }, 400)
    }
    if (!token || token.length > 2048 || !(foto instanceof File)) {
      return json(request, { error: 'Falta la foto o la verificación de seguridad.' }, 400)
    }
    if (!await verificarTurnstile(token)) {
      return json(request, { error: 'No pudimos verificar la seguridad. Intenta de nuevo.' }, 403)
    }
    if (!await consumirLimite(request, 'enviar', 5)) {
      return json(request, { error: 'Llegaste al límite de cinco reportes por hora. Intenta más tarde.' }, 429)
    }

    let validada: Awaited<ReturnType<typeof validarFoto>>
    try {
      validada = await validarFoto(foto)
    } catch (error) {
      const message = error instanceof Error && [
        'La foto debe pesar menos de 5 MB.',
        'La foto debe ser JPEG, PNG o WebP, sin metadatos de ubicación.',
      ].includes(error.message) ? error.message : 'La foto no es válida.'
      return json(request, { error: message }, 400)
    }

    const id = crypto.randomUUID()
    const ruta = `${id}.${validada.extension}`
    const { url, key } = serviceConfig()
    const objetoUrl = `${url}/storage/v1/object/reporte-agua-fotos/${ruta}`
    const upload = await fetch(objetoUrl, {
      method: 'POST',
      headers: { ...serviceHeaders(key), 'Content-Type': validada.mime, 'x-upsert': 'false' },
      body: validada.bytes.buffer as ArrayBuffer,
    })
    if (!upload.ok) throw new Error(`No se pudo guardar la foto: ${upload.status}`)

    try {
      const folio = await rpc<string>('crear_reporte_agua', {
        p_id: id,
        p_lng: lng,
        p_lat: lat,
        p_categoria_id: categoriaId,
        p_nota: nota,
        p_fecha_observacion: fecha.toISOString(),
        p_calle_texto: calle || null,
        p_foto_ruta: ruta,
        p_email: email || null,
        p_telefono: telefono || null,
        p_consentimiento_contacto_at: contactoAutorizado && (email || telefono) ? new Date().toISOString() : null,
      })
      return json(request, { folio }, 201)
    } catch (error) {
      const cleanup = await fetch(objetoUrl, { method: 'DELETE', headers: serviceHeaders(key) })
      if (!cleanup.ok) console.error('No se pudo retirar una foto huérfana', ruta, cleanup.status)
      throw error
    }
  } catch (error) {
    if (error instanceof Error && error.message === 'Demasiado grande') {
      return json(request, { error: 'La foto supera el límite de 5 MB.' }, 413)
    }
    console.error('No se pudo enviar el reporte', error)
    return json(request, { error: 'No pudimos guardar el reporte. Intenta de nuevo.' }, 503)
  }
})
