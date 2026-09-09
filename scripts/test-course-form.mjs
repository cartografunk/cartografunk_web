import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const source = readFileSync(new URL('../assets/js/course-form.js', import.meta.url), 'utf8');
const values = {
  email: ' TEST@example.com ', nombre: ' Nombre ', instagram: '@test', whatsapp: '123',
  experiencia_qgis: 'Lo abrí una vez', horario_preferido: 'Entre semana - Matutino',
  que_descubrir: 'Mi ciudad', primera_palabra: 'Territorio', creencia_a_probar: 'Distancias',
};
function setup({ key = 'sb_publishable_test', failAt, fields = values } = {}) {
  const calls = [];
  const button = {};
  const status = { dataset: {} };
  let submit;
  let resets = 0;
  const form = {
    querySelector: () => button, reportValidity: () => true,
    setAttribute() {}, removeAttribute() {}, reset() { resets++; },
    addEventListener: (_, listener) => { submit = listener; },
  };
  vm.runInNewContext(source, {
    document: { getElementById: id => id === 'courseForm' ? form : status },
    window: { CARTOGRAFUNK_SUPABASE: { url: 'https://test.supabase.co', publishableKey: key } },
    atob, FormData: class { get(name) { return fields[name]; } },
    fetch: async (url, options) => {
      calls.push({ url, ...options, body: JSON.parse(options.body) });
      return {
        ok: calls.length !== failAt, status: 200,
        text: async () => JSON.stringify(null),
      };
    },
  });
  return { calls, button, status, submit: () => submit({ preventDefault() {} }), resets: () => resets };
}

const success = setup();
await Promise.all([success.submit(), success.submit()]);
assert.equal(success.calls.length, 1);
assert.match(success.calls[0].url, /rpc\/registrar_inscripcion$/);
assert.equal(success.calls[0].headers.Authorization, undefined);
assert.deepEqual(success.calls[0].body, {
  p_email: 'test@example.com', p_nombre: 'Nombre', p_instagram: '@test', p_whatsapp: '123',
  p_curso_id: '334bf0e8-14fb-4511-a68c-308ed3b75a23',
  ...Object.fromEntries(['experiencia_qgis', 'horario_preferido', 'que_descubrir', 'primera_palabra', 'creencia_a_probar'].map(key => [`p_${key}`, values[key]])),
});
assert.equal(success.resets(), 1);
await success.submit();
assert.equal(success.calls.length, 1);
const failure = setup({ failAt: 1 });
await failure.submit();
assert.equal(failure.status.dataset.state, 'error');
assert.equal(failure.resets(), 0);
assert.equal(failure.button.disabled, false);
await failure.submit();
assert.equal(failure.resets(), 1);
const noInstagram = setup({ fields: { ...values, instagram: ' ' } });
await noInstagram.submit();
assert.equal(noInstagram.calls[0].body.p_instagram, null);
for (const key of ['', 'sb_secret_test', `x.${btoa(JSON.stringify({ role: 'service_role' }))}.x`]) {
  const test = setup({ key });
  await test.submit();
  assert.equal(test.calls.length, 0);
}
const anon = setup({ key: `x.${btoa(JSON.stringify({ role: 'anon' }))}.x` });
await anon.submit();
assert.match(anon.calls[0].headers.Authorization, /^Bearer /);
const invalid = setup({ fields: { ...values, experiencia_qgis: 'Avanzado' } });
await invalid.submit();
assert.equal(invalid.calls.length, 0);
console.log('Course form: payloads, duplicate submits, failures, key roles and enum validation passed.');
