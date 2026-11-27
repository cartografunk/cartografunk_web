import { json, preflight, serviceConfig, serviceHeaders } from '../_shared/reporte-agua.ts'
import { MIME, validAmount, validReceipt } from './validation.ts'

const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const COURSE = 'a77e51c2-441a-4bac-9a25-922aa99ab323'
const BUCKET = 'comprobantes-cursos'

async function rest<T>(route: string, method = 'GET', body?: BodyInit, contentType?: string, auth?: string): Promise<T> {
  const { url, key } = serviceConfig()
  const response = await fetch(`${url}${route}`, {
    method,
    headers: { ...serviceHeaders(key), ...(contentType ? { 'Content-Type': contentType } : {}),
      ...(auth ? { Authorization: auth } : {}) },
    body,
  })
  if (!response.ok) throw new Error(`Supabase HTTP ${response.status}`)
  const text = await response.text()
  return (text ? JSON.parse(text) : null) as T
}

async function enrollment(token: string): Promise<string | null> {
  if (!ID.test(token)) return null
  const access = await rest<Array<{ inscripcion_id: string }>>(
    `/rest/v1/crm_enlaces_pago?select=inscripcion_id&token=eq.${token}&limit=1`)
  const id = access[0]?.inscripcion_id
  if (!id) return null
  const rows = await rest<Array<{ estatus: string; curso_id: string }>>(
    `/rest/v1/inscripciones?select=estatus,curso_id&id=eq.${id}&limit=1`)
  if (rows[0]?.curso_id !== COURSE || !['interesado', 'contactado', 'inscrito', 'pagado'].includes(rows[0]?.estatus)) return null
  return id
}

async function paymentStatus(id: string) {
  const rows = await rest<Array<{ monto_mxn: number; estado: string }>>(
    `/rest/v1/crm_pagos?select=monto_mxn,estado&inscripcion_id=eq.${id}`)
  const verified = rows.filter(row => row.estado === 'verificado')
    .reduce((sum, row) => sum + row.monto_mxn, 0)
  return { verificado_mxn: verified, saldo_mxn: Math.max(0, 1500 - verified),
    comprobantes_en_revision: rows.filter(row => row.estado === 'pendiente').length,
    comprobantes_totales: rows.length }
}

async function admin(request: Request): Promise<boolean> {
  const token = request.headers.get('authorization')
  const { url } = serviceConfig()
  if (!token?.startsWith('Bearer ')) return false
  const namedKeys = JSON.parse(Deno.env.get('SUPABASE_PUBLISHABLE_KEYS') ?? '{}') as Record<string, string>
  const publicKey = Deno.env.get('SUPABASE_ANON_KEY')
    ?? Deno.env.get('SUPABASE_PUBLISHABLE_KEY') ?? namedKeys.default
  if (!publicKey) return false
  const response = await fetch(`${url}/rest/v1/rpc/crm_resumen`, {
    method: 'POST',
    headers: { apikey: publicKey,
      Authorization: token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ p_curso_id: null, p_desde: null, p_hasta: null }),
  })
  return response.ok
}

Deno.serve(async (request) => {
  const options = preflight(request, 'POST, OPTIONS')
  if (options) return options
  if (request.method !== 'POST') return json(request, { error: 'Método no permitido.' }, 405, 'POST, OPTIONS')
  try {
    const type = request.headers.get('content-type') ?? ''
    if (type.startsWith('application/json')) {
      const body = await request.json()
      if (body.action === 'preview') {
        if (!await admin(request) || !ID.test(body.pago_id ?? ''))
          return json(request, { error: 'Acceso no autorizado.' }, 403)
        const rows = await rest<Array<{ comprobante_path: string }>>(
          `/rest/v1/crm_pagos?select=comprobante_path&id=eq.${body.pago_id}&limit=1`)
        if (!rows[0]) return json(request, { error: 'Comprobante no encontrado.' }, 404)
        const { url, key } = serviceConfig()
        const signed = await fetch(`${url}/storage/v1/object/sign/${BUCKET}/${rows[0].comprobante_path}`, {
          method: 'POST', headers: { ...serviceHeaders(key), 'Content-Type': 'application/json' },
          body: JSON.stringify({ expiresIn: 120 }),
        })
        if (!signed.ok) throw new Error(`Firma HTTP ${signed.status}`)
        const data = await signed.json() as { signedURL: string }
        const signedUrl = new URL(data.signedURL.startsWith('/object/')
          ? `/storage/v1${data.signedURL}` : data.signedURL, url)
        if (signedUrl.origin !== new URL(url).origin) throw new Error('URL firmada inesperada')
        return json(request, { url: signedUrl.toString() })
      }
      if (body.action === 'status') {
        const id = await enrollment(body.token ?? '')
        if (!id) return json(request, { error: 'Enlace no disponible.' }, 404)
        const account = Deno.env.get('CARTOFUNK_TRANSFER_ACCOUNT')
        if (!account || !/^\d{18}$/.test(account)) throw new Error('Cuenta de transferencia no configurada')
        return json(request, { cuenta_transferencia: account, costo_mxn: 1500,
          anticipo_sugerido_mxn: 450, ...(await paymentStatus(id)) })
      }
      return json(request, { error: 'Acción inválida.' }, 400)
    }
    if (!type.startsWith('multipart/form-data')) return json(request, { error: 'Formato inválido.' }, 415)
    if (Number(request.headers.get('content-length') || 0) > 6 * 1024 * 1024)
      return json(request, { error: 'El archivo supera el límite de 5 MB.' }, 413)
    const form = await request.formData()
    const id = await enrollment(String(form.get('token') ?? ''))
    if (!id) return json(request, { error: 'Enlace no disponible.' }, 404)
    const amount = Number(form.get('monto_mxn'))
    const file = form.get('comprobante')
    if (!(file instanceof File) || !validAmount(amount, 1500) || !await validReceipt(file))
      return json(request, { error: 'Monto o archivo inválido. Usa JPG, PNG o PDF de hasta 5 MB.' }, 400)
    const current = await paymentStatus(id)
    if (current.comprobantes_en_revision >= 3 || current.comprobantes_totales >= 10 || !validAmount(amount, current.saldo_mxn))
      return json(request, { error: 'Ya hay comprobantes en revisión o el monto excede el saldo.' }, 400)
    const { url, key } = serviceConfig()
    const path = `${id}/${crypto.randomUUID()}.${MIME[file.type]}`
    const uploaded = await fetch(`${url}/storage/v1/object/${BUCKET}/${path}`, {
      method: 'POST', headers: { ...serviceHeaders(key), 'Content-Type': file.type,
        'x-upsert': 'false' }, body: file,
    })
    if (!uploaded.ok) throw new Error(`Carga HTTP ${uploaded.status}`)
    try {
      await rest('/rest/v1/crm_pagos', 'POST', JSON.stringify({
        inscripcion_id: id, monto_mxn: amount, comprobante_path: path,
      }), 'application/json')
    } catch (error) {
      await fetch(`${url}/storage/v1/object/${BUCKET}/${path}`, {
        method: 'DELETE', headers: serviceHeaders(key),
      }).catch(() => {})
      throw error
    }
    return json(request, { recibido: true,
      mensaje: 'Recibimos tu comprobante. Revisaremos la transferencia antes de confirmar tu lugar.' })
  } catch (error) {
    console.error('Error en comprobante-curso', error)
    return json(request, { error: 'No pudimos completar la solicitud. Intenta más tarde.' }, 503)
  }
})
