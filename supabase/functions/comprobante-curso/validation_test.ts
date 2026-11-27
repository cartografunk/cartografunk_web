import { validAmount, validReceipt } from './validation.ts'

Deno.test('anticipo parcial y saldo', () => {
  if (!validAmount(450, 1500) || !validAmount(1050, 1050)
    || validAmount(1501, 1500) || validAmount(451, 450) || validAmount(0, 1500))
    throw new Error('Validación de monto incorrecta')
})

Deno.test('solo acepta tipo y firma de comprobante coherentes', async () => {
  const jpg = new File([new Uint8Array([255, 216, 255, 0])], 'proof.jpg', { type: 'image/jpeg' })
  const fake = new File([new Uint8Array([1, 2, 3])], 'fake.jpg', { type: 'image/jpeg' })
  if (!await validReceipt(jpg) || await validReceipt(fake))
    throw new Error('Validación de archivo incorrecta')
})
