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
    const minimum = Number(data.anticipo_minimo_mxn) || 450;
    const pendingScholarship = data.solicita_beca && !data.beca_aprobada;
    $('paymentSummary').textContent = pendingScholarship
      ? `Beca pendiente · Aporte propuesto: ${money(data.aporte_mxn)}`
      : `Costo acordado: ${money(cost)} · Verificado: ${money(paid)} · Saldo: ${money(Math.max(0, cost - paid))}` +
        (paid >= minimum ? ' · Lugar apartado' : ' · Pago por verificar');
    $('scholarshipApproval').hidden = !pendingScholarship;
    $('scholarshipAmount').textContent = pendingScholarship
      ? `La persona propuso pagar ${money(data.aporte_mxn)}. Aprueba la beca antes de enviar el enlace de pago.` : '';
    $('copyPaymentLink').hidden = pendingScholarship || paid >= minimum;
    $('copyPaymentLink').textContent = data.solicita_beca ? 'Copiar mensaje de beca aprobada' : 'Copiar mensaje de anticipo';
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
      $('scholarshipApproval').hidden = true;
      return;
    }
    $('copyPaymentLink').hidden = true;
    $('scholarshipApproval').hidden = true;
    try { await load(selected.id); }
    catch (error) { status(error.message, 'error'); }
  });

  $('approveScholarship').addEventListener('click', async () => {
    if (!selected || !selected.solicitaBeca || !Number.isInteger(selected.aporteMxn)
      || selected.aporteMxn < 1 || selected.aporteMxn >= 1500) {
      status('Revisa el monto propuesto antes de aprobar.', 'error'); return;
    }
    const note = $('scholarshipNote').value.trim();
    if (!note) { status('Escribe una nota para registrar el acuerdo.', 'error'); return; }
    const button = $('approveScholarship');
    button.disabled = true;
    try {
      await crm.rpc('crm_marcar_pago_beca', { p_inscripcion_id: selected.id,
        p_pago_comprobado: null, p_beca_aprobada: true, p_nota: note });
      await load(selected.id);
      status('Beca aprobada. Ya puedes copiar el mensaje de pago.', 'success');
      document.dispatchEvent(new Event('crm:payment-updated'));
    } catch (error) { status(error.message, 'error'); }
    finally { button.disabled = false; }
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
      const templateResponse = await fetch(selected.solicitaBeca
        ? '/templates/beca_aprobada.txt' : '/templates/primer_contacto_a.txt');
      if (!templateResponse.ok) throw new Error('No se pudo cargar la plantilla de mensaje.');
      const values = { nombre: selected.nombre, curso: selected.curso,
        aporte_mxn: String(selected.aporteMxn),
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
