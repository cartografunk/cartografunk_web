const MAX_BYTES = 5 * 1024 * 1024
const pngSignature = [137, 80, 78, 71, 13, 10, 26, 10]
const decoder = new TextDecoder('ascii')

function errorImagen(): never {
  throw new Error('La foto debe ser JPEG, PNG o WebP, sin metadatos de ubicación.')
}

function limpiarJpeg(bytes: Uint8Array): Uint8Array | null {
  if (bytes.length < 4 || bytes[0] !== 0xff || bytes[1] !== 0xd8
      || bytes.at(-2) !== 0xff || bytes.at(-1) !== 0xd9) return null
  let offset = 2
  let encontroSof = false
  const partes: Uint8Array[] = [bytes.slice(0, 2)]
  while (offset < bytes.length - 2) {
    const inicio = offset
    if (bytes[offset++] !== 0xff) return null
    while (bytes[offset] === 0xff) offset++
    const marker = bytes[offset++]
    if (marker === 0xda) {
      if (!encontroSof || offset + 2 > bytes.length) return null
      const length = (bytes[offset] << 8) | bytes[offset + 1]
      if (length < 2 || offset + length > bytes.length - 2) return null
      for (let i = offset; i < bytes.length - 1; i++) {
        if (bytes[i] === 0xff && (bytes[i + 1] === 0xfe
            || (bytes[i + 1] >= 0xe0 && bytes[i + 1] <= 0xef))) return null
      }
      partes.push(bytes.slice(inicio))
      const result = new Uint8Array(partes.reduce((total, parte) => total + parte.length, 0))
      let salida = 0
      for (const parte of partes) { result.set(parte, salida); salida += parte.length }
      return result
    }
    if (marker === 0xd8 || marker === 0xd9 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) return null
    if (offset + 2 > bytes.length) return null
    const length = (bytes[offset] << 8) | bytes[offset + 1]
    if (length < 2 || offset + length > bytes.length) return null
    if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) encontroSof = true
    if (marker !== 0xfe && !(marker >= 0xe0 && marker <= 0xef)) partes.push(bytes.slice(inicio, offset + length))
    offset += length
  }
  return null
}

function pngSeguro(bytes: Uint8Array): boolean {
  if (bytes.length < 20 || !pngSignature.every((value, index) => bytes[index] === value)) return false
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  let offset = 8
  let encontroImagen = false
  let encontroFin = false
  const permitidos = new Set(['IHDR', 'PLTE', 'IDAT', 'IEND', 'tRNS'])
  while (offset + 12 <= bytes.length) {
    const length = view.getUint32(offset)
    const tipo = decoder.decode(bytes.slice(offset + 4, offset + 8))
    if (!permitidos.has(tipo) || length > bytes.length - offset - 12) return false
    if (tipo === 'IDAT') encontroImagen = true
    offset += length + 12
    if (tipo === 'IEND') {
      encontroFin = true
      break
    }
  }
  return encontroImagen && encontroFin && offset === bytes.length
}

function webpSeguro(bytes: Uint8Array): boolean {
  if (bytes.length < 20 || decoder.decode(bytes.slice(0, 4)) !== 'RIFF'
      || decoder.decode(bytes.slice(8, 12)) !== 'WEBP') return false
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  if (view.getUint32(4, true) !== bytes.length - 8) return false
  const permitidos = new Set(['VP8 ', 'VP8L', 'VP8X', 'ALPH', 'ANIM', 'ANMF'])
  let offset = 12
  let encontroImagen = false
  while (offset + 8 <= bytes.length) {
    const tipo = decoder.decode(bytes.slice(offset, offset + 4))
    const length = view.getUint32(offset + 4, true)
    if (!permitidos.has(tipo) || length > bytes.length - offset - 8) return false
    if (tipo === 'VP8X' && (length < 10 || (bytes[offset + 8] & 0x2c) !== 0)) return false
    if (tipo === 'VP8 ' || tipo === 'VP8L' || tipo === 'ANMF') encontroImagen = true
    offset += 8 + length + (length % 2)
  }
  return encontroImagen && offset === bytes.length
}

export async function validarFoto(file: File): Promise<{ bytes: Uint8Array; mime: string; extension: string }> {
  if (file.size < 100 || file.size > MAX_BYTES) {
    throw new Error('La foto debe pesar menos de 5 MB.')
  }
  const bytes = new Uint8Array(await file.arrayBuffer())
  const jpeg = limpiarJpeg(bytes)
  if (jpeg) return { bytes: jpeg, mime: 'image/jpeg', extension: 'jpg' }
  if (pngSeguro(bytes)) return { bytes, mime: 'image/png', extension: 'png' }
  if (webpSeguro(bytes)) return { bytes, mime: 'image/webp', extension: 'webp' }
  return errorImagen()
}
