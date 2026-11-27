export const MIME: Record<string, string> = {
  'image/jpeg': 'jpg', 'image/png': 'png', 'application/pdf': 'pdf',
}

export async function validReceipt(file: File): Promise<boolean> {
  if (!MIME[file.type] || file.size < 1 || file.size > 5 * 1024 * 1024) return false
  const magic = new Uint8Array(await file.slice(0, 8).arrayBuffer())
  if (file.type === 'application/pdf')
    return String.fromCharCode(...magic.slice(0, 5)) === '%PDF-'
  if (file.type === 'image/png')
    return [137, 80, 78, 71, 13, 10, 26, 10].every((byte, i) => magic[i] === byte)
  return magic[0] === 255 && magic[1] === 216 && magic[2] === 255
}

export function validAmount(amount: number, remaining: number): boolean {
  return Number.isInteger(amount) && amount >= 1 && amount <= 1500 && amount <= remaining
}
