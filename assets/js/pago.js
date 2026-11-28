(() => {
  'use strict';
  const config = window.CARTOGRAFUNK_SUPABASE;
  const token = location.hash.slice(1).trim();
  const $ = id => document.getElementById(id);
  const money = value => `$${new Intl.NumberFormat('es-MX').format(value)} MXN`;
  const status = (text, state = '') => {
    $('paymentStatus').textContent = text;
    $('paymentStatus').dataset.state = state;
  };

  async function request(body) {
    const response = await fetch(`${config.url}/functions/v1/comprobante-curso`, {
      method: 'POST', headers: { apikey: config.publishableKey,
        ...(typeof body === 'string' ? { 'Content-Type': 'application/json' } : {}) }, body,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'No pudimos completar la solicitud.');
    return data;
  }

  async function load() {
    if (!/^[0-9a-f-]{36}$/i.test(token)) {
      status('Este enlace no está disponible. Solicita uno nuevo a Cartografunk.', 'error');
      return;
    }
    try {
      const data = await request(JSON.stringify({ action: 'status', token }));
      $('paymentIntro').textContent = data.beca_aprobada
        ? `Aprobé tu beca por ${money(data.costo_mxn)}. Cubre ese monto y sube tu comprobante para apartar tu lugar.`
        : `El curso cuesta ${money(data.costo_mxn)}. Puedes apartar tu lugar con ${money(data.anticipo_sugerido_mxn)}. El resto puedes cubrirlo con facilidades antes de la última sesión; si necesitas otro acuerdo, escríbeme.`;
      $('paymentAccount').textContent = data.cuenta_transferencia;
      $('paymentVerified').textContent = money(data.verificado_mxn);
      $('paymentBalance').textContent = money(data.saldo_mxn);
      $('paymentAmount').max = data.saldo_mxn;
      $('paymentAmount').value = Math.min(data.anticipo_sugerido_mxn, data.saldo_mxn);
      $('pendingNote').textContent = data.comprobantes_en_revision
        ? `${data.comprobantes_en_revision} comprobante(s) en revisión. Te avisaré al verificar la transferencia.` : '';
      $('paymentForm').hidden = data.saldo_mxn === 0 || data.comprobantes_en_revision >= 3 || data.comprobantes_totales >= 10;
      $('paymentInfo').hidden = false;
      status('Puedes enviar tu comprobante de forma segura.', 'success');
    } catch (error) { status(error.message, 'error'); }
  }

  $('paymentForm').addEventListener('submit', async event => {
    event.preventDefault();
    const file = $('paymentFile').files[0];
    if (!file || file.size > 5 * 1024 * 1024 || !['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)) {
      status('Usa un archivo JPG, PNG o PDF de hasta 5 MB.', 'error');
      return;
    }
    const button = $('paymentForm').querySelector('button[type="submit"]');
    button.disabled = true;
    status('Enviando comprobante…');
    try {
      const form = new FormData($('paymentForm'));
      form.set('token', token);
      const result = await request(form);
      $('paymentForm').reset();
      await load();
      status(result.mensaje, 'success');
    } catch (error) { status(error.message, 'error'); }
    finally { button.disabled = false; }
  });
  $('copyAccount').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('paymentAccount').textContent);
      status('Cuenta copiada.', 'success');
    } catch { status('No se pudo copiar la cuenta. Puedes seleccionarla manualmente.', 'error'); }
  });
  load();
})();
