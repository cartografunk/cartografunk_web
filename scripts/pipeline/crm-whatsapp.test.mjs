import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(import.meta.dirname, '../..');
const source = await fs.readFile(path.join(root, 'assets/js/crm-payments.js'), 'utf8');
const course = 'Agentes de IA para hacer mi tesis y todo lo que no quiero hacer';

async function draft(lead, detail) {
  const listeners = new Map();
  const elements = new Map();
  const tabs = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      dataset: {}, addEventListener() {}, replaceChildren() {}, hidden: false,
      textContent: '', disabled: false,
    });
    return elements.get(id);
  };
  const context = {
    document: { getElementById: element, addEventListener(name, listener) { listeners.set(name, listener); },
      dispatchEvent(event) { listeners.get(event.type)?.(event); } },
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
    window: {
      CARTOGRAFUNK_SUPABASE: { url: 'https://example.invalid', publishableKey: 'public' },
      CARTOGRAFUNK_CRM: {
        async rpc(name) {
          if (name === 'crm_pagos_detalle') return detail;
          if (name === 'crm_enlace_pago') return '00000000-0000-4000-8000-000000000001';
          if (name === 'crm_invitaciones_horario') return [{ inscripcion_id: lead.id,
            token: '00000000-0000-4000-8000-000000000002', respondio_at: null }];
          throw new Error(name);
        },
      },
      open() {
        const tab = { location: { href: '' }, opener: null, close() { this.closed = true; } };
        tabs.push(tab);
        return tab;
      },
    },
    location: { origin: 'https://cartografunk.com' },
    navigator: { clipboard: { async writeText() {} } },
    async fetch(url) {
      if (url.startsWith('/templates/')) {
        const name = url.split('/').at(-1);
        return { ok: true, async text() { return fs.readFile(path.join(root, 'templates', name), 'utf8'); } };
      }
      return { ok: true, async json() { return { cuenta_transferencia: '0'.repeat(18) }; } };
    },
  };
  vm.runInNewContext(source, context);
  const button = { disabled: false };
  await listeners.get('crm:whatsapp')({ detail: { lead, button } });
  assert.equal(tabs.length, 1);
  assert.equal(tabs[0].closed, undefined, element('dashboardStatus').textContent);
  assert.equal(button.disabled, false);
  const url = new URL(tabs[0].location.href);
  assert.equal(url.hostname, 'wa.me');
  assert.equal(url.pathname, '/525555555555');
  return url.searchParams.get('text');
}

const lead = { id: 'lead', nombre: 'Ana', curso: course, curso_id: 'course',
  whatsapp: '5555555555', estatus: 'interesado', respuestas: { solicita_beca: false } };

test('WhatsApp de la lista prepara pago completo con enlace personal', async () => {
  const message = await draft(lead, { verificado_mxn: 0, anticipo_minimo_mxn: 450,
    solicita_beca: false, beca_aprobada: false, pagos: [] });
  assert.match(message, /\$450 MXN/);
  assert.match(message, /\/pago#00000000-0000-4000-8000-000000000001/);
});

test('WhatsApp de la lista usa acuse cuando la beca sigue pendiente', async () => {
  const message = await draft({ ...lead, respuestas: { solicita_beca: true, aporte_mxn: 600 } },
    { verificado_mxn: 0, anticipo_minimo_mxn: 450,
      solicita_beca: true, beca_aprobada: false, pagos: [] });
  assert.match(message, /Recibí tu solicitud de beca/);
  assert.doesNotMatch(message, /transferencia a/);
});

test('WhatsApp de la lista usa votación después del pago verificado', async () => {
  const message = await draft(lead, { verificado_mxn: 450, anticipo_minimo_mxn: 450,
    solicita_beca: false, beca_aprobada: false, pagos: [] });
  assert.match(message, /\/horarios#00000000-0000-4000-8000-000000000002/);
  assert.doesNotMatch(message, /transferencia a/);
});
