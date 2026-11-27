(() => {
  'use strict';
  const config = window.CARTOGRAFUNK_SUPABASE;
  const crm = window.CARTOGRAFUNK_CRM;
  const $ = id => document.getElementById(id);
  const money = value => `$${new Intl.NumberFormat('es-MX').format(Number(value) || 0)} MXN`;
  let selected = null;

  function status(text, kind = '') {
    $('paymentActionStatus').textContent = text;
    $('paymentActionStatus').dataset.state = kind;
  }

  function node(tag, text) {
    const element = document.createElement(tag);
    if (text != null) element.textContent = String(text);
    return element;
  }

  async function preview(id) {
    const tab = window.open('about:blank', '_blank');
    if (tab) tab.opener = null;
    try {
      const response = await fetch(`${config.url}/functions/v1/comprobante-curso`, {
        method: 'POST', headers: { apikey: config.publishableKey,
          Authorization: `Bearer ${await crm.accessToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'preview', pago_id: id }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'No se pudo abrir el comprobante.');
      if (tab) tab.location.href = data.url;
      else throw new Error('Permite ventanas emergentes para abrir el comprobante.');
    } catch (error) { if (tab) tab.close(); throw error; }
  }

  async function review(payment, approved, note, button) {
    if (!note.trim()) { status('Escribe una nota de revisión.', 'error'); return; }
    button.disabled = true;
    status('Guardando revisión…');
    try {
      await crm.rpc('crm_revisar_pago', { p_pago_id: payment.id,
        p_aprobar: approved, p_nota: note.trim() });
      status(approved ? 'Transferencia verificada.' : 'Comprobante rechazado.', 'success');
      await load(selected.id);
      document.dispatchEvent(new Event('crm:payment-updated'));
    } catch (error) { status(error.message, 'error'); }
    finally { button.disabled = false; }
  }

  function render(data) {
    const paid = Number(data.verificado_mxn) || 0;
    const cost = Number(data.costo_mxn) || 1500;
    $('paymentSummary').textContent = `Verificado: ${money(paid)} · Saldo al precio publicado: ${money(Math.max(0, cost - paid))}` +
      (paid >= 450 ? ' · Anticipo cubierto' : ' · Anticipo aún no cubierto');
    const container = $('paymentEntries');
    container.replaceChildren();
    if (!data.pagos.length) { container.append(node('p', 'Aún no hay comprobantes.')); return; }
    for (const payment of data.pagos) {
      const card = node('article');
      card.className = 'payment-entry';
      card.append(node('strong', `${money(payment.monto_mxn)} · ${payment.estado}`),
        node('small', new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short',
          timeZone: 'America/Mexico_City' }).format(new Date(payment.recibido_at))));
      const actions = node('div');
      actions.className = 'payment-actions';
      const view = node('button', 'Ver comprobante');
      view.type = 'button';
      view.className = 'secondary-button';
      view.addEventListener('click', () => preview(payment.id).catch(error => status(error.message, 'error')));
      actions.append(view);
      if (payment.estado === 'pendiente') {
        const note = node('textarea');
        note.maxLength = 1500;
        note.placeholder = 'Referencia comprobada o motivo del rechazo';
        note.setAttribute('aria-label', `Nota de revisión para pago de ${money(payment.monto_mxn)}`);
        const approve = node('button', 'Verifiqué la transferencia');
        approve.type = 'button';
        approve.className = 'primary-button';
        approve.addEventListener('click', () => review(payment, true, note.value, approve));
        const reject = node('button', 'Rechazar comprobante');
        reject.type = 'button';
        reject.className = 'secondary-button';
        reject.addEventListener('click', () => review(payment, false, note.value, reject));
        actions.append(note, approve, reject);
      } else if (payment.nota_revision) card.append(node('p', payment.nota_revision));
      card.append(actions);
      container.append(card);
    }
  }

  async function load(id) {
    const data = await crm.rpc('crm_pagos_detalle', { p_inscripcion_id: id });
    if (selected?.id === id) render(data);
  }

  document.addEventListener('crm:lead', async event => {
    selected = event.detail;
    $('paymentSummary').textContent = 'Cargando pagos…';
    $('paymentEntries').replaceChildren();
    status('');
    if (!selected.curso.startsWith('Agentes de IA')) {
      $('paymentSummary').textContent = 'El registro de anticipos está disponible para el curso de agentes de IA.';
      $('copyPaymentLink').hidden = true;
      return;
    }
    if (selected.solicitaBeca) {
      $('paymentSummary').textContent = 'Esta persona solicitó beca. Acuerda el importe antes de enviar instrucciones de pago.';
      $('copyPaymentLink').hidden = true;
      return;
    }
    $('copyPaymentLink').hidden = false;
    try { await load(selected.id); }
    catch (error) { status(error.message, 'error'); }
  });

  $('copyPaymentLink').addEventListener('click', async () => {
    if (!selected) return;
    const button = $('copyPaymentLink');
    button.disabled = true;
    try {
      const token = await crm.rpc('crm_enlace_pago', { p_inscripcion_id: selected.id });
      const link = `${location.origin}/pago#${token}`;
      const response = await fetch(`${config.url}/functions/v1/comprobante-curso`, {
        method: 'POST', headers: { apikey: config.publishableKey,
          'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'status', token }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'No se pudo preparar el mensaje.');
      const templateResponse = await fetch('/templates/primer_contacto_a.txt');
      if (!templateResponse.ok) throw new Error('No se pudo cargar la plantilla de mensaje.');
      const values = { nombre: selected.nombre, curso: selected.curso,
        cuenta_transferencia: data.cuenta_transferencia, enlace_pago: link };
      const template = await templateResponse.text();
      const text = template.replace(/{{([a-z_]+)}}/g, (_, key) => {
        if (!values[key]) throw new Error(`Falta ${key} en la plantilla.`);
        return values[key];
      }).trim();
      await navigator.clipboard.writeText(text);
      status('Mensaje personalizado copiado. Revísalo antes de enviarlo.', 'success');
    } catch (error) { status(error.message, 'error'); }
    finally { button.disabled = false; }
  });
})();
