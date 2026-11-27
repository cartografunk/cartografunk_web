(() => {
  'use strict';

  const config = window.CARTOGRAFUNK_SUPABASE;
  const sessionKey = 'cartografunk-crm-session';
  const $ = id => document.getElementById(id);
  const stages = [
    ['interesado', 'Interesado'], ['contactado', 'Contactado'],
    ['inscrito', 'Inscrito'], ['pagado', 'Pagado'],
    ['completado', 'Completado'], ['perdido', 'Perdido'],
  ];
  const stageNames = Object.fromEntries(stages);
  const state = { session: null, summary: null, rows: [], totalRows: 0, offset: 0,
    limit: 50, queue: null, selected: null, listRequest: 0 };

  function message(id, text, kind = '') {
    const node = $(id);
    node.textContent = text;
    node.dataset.state = kind;
  }

  function showDashboard(visible) {
    $('loginView').hidden = visible;
    $('dashboardView').hidden = !visible;
    $('logoutButton').hidden = !visible;
  }

  function saveSession(value) {
    state.session = value;
    if (value) sessionStorage.setItem(sessionKey, JSON.stringify(value));
    else sessionStorage.removeItem(sessionKey);
  }

  async function authRequest(path, body, token) {
    const response = await fetch(`${config.url}/auth/v1/${path}`, {
      method: 'POST',
      headers: {
        apikey: config.publishableKey,
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.msg || data.error_description || data.message || 'No se pudo iniciar sesión.');
    return data;
  }

  async function accessToken() {
    if (!state.session) throw new Error('Inicia sesión para continuar.');
    if (Date.now() < state.session.expiresAt - 60_000) return state.session.accessToken;
    const data = await authRequest('token?grant_type=refresh_token', {
      refresh_token: state.session.refreshToken,
    });
    saveSession({ accessToken: data.access_token, refreshToken: data.refresh_token,
      expiresAt: Date.now() + data.expires_in * 1000 });
    return state.session.accessToken;
  }

  async function rpc(name, body) {
    const response = await fetch(`${config.url}/rest/v1/rpc/${name}`, {
      method: 'POST',
      headers: {
        apikey: config.publishableKey,
        Authorization: `Bearer ${await accessToken()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        throw new Error('Esta cuenta no tiene acceso al panel.');
      }
      throw new Error(data?.message || 'No se pudieron cargar los datos.');
    }
    return data;
  }

  const number = value => new Intl.NumberFormat('es-MX').format(Number(value) || 0);
  const formatDate = value => value ? new Intl.DateTimeFormat('es-MX', {
    day: 'numeric', month: 'short', year: 'numeric', timeZone: 'America/Mexico_City',
  }).format(new Date(value)) : '—';
  const formatDateTime = value => value ? new Intl.DateTimeFormat('es-MX', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Mexico_City',
  }).format(new Date(value)) : 'Sin programar';

  function node(tag, className, value) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (value != null) element.textContent = String(value);
    return element;
  }

  function filters() {
    return {
      p_curso_id: $('courseFilter').value || null,
      p_desde: $('dateFrom').value || null,
      p_hasta: $('dateTo').value || null,
    };
  }

  function renderSummary(data) {
    state.summary = data;
    const summary = data.resumen;
    $('metricTotal').textContent = number(summary.total);
    $('metricUncontacted').textContent = number(summary.sin_primer_contacto);
    $('metricOverdue').textContent = number(summary.vencidos);
    $('metricScholarships').textContent = number(summary.becas);
    $('priorityUncontacted').textContent = number(summary.sin_primer_contacto);
    $('priorityOverdue').textContent = number(summary.vencidos);
    $('priorityUnscheduled').textContent = number(summary.sin_programar);

    const courseSelect = $('courseFilter');
    const current = courseSelect.value;
    courseSelect.replaceChildren(new Option('Todos los cursos', ''));
    for (const course of data.cursos) courseSelect.add(new Option(course.nombre, course.id));
    courseSelect.value = current;

    const scheduleSelect = $('scheduleCourse');
    const scheduleCurrent = scheduleSelect.value;
    scheduleSelect.replaceChildren(new Option('Selecciona un curso', ''));
    for (const course of data.cursos) scheduleSelect.add(new Option(course.nombre, course.id));
    scheduleSelect.value = scheduleCurrent || data.cursos.find(course => course.nombre.startsWith('Agentes de IA'))?.id || '';

    const container = $('funnelRows');
    container.replaceChildren();
    const max = Math.max(1, ...stages.map(([key]) => Number(summary[key]) || 0));
    for (const [key, label] of stages) {
      const row = node('div', 'funnel-row');
      row.dataset.stage = key;
      row.append(node('span', '', label));
      const track = node('div', 'funnel-track');
      const fill = node('div', 'funnel-fill');
      fill.style.width = `${Math.max(0, Number(summary[key]) || 0) / max * 100}%`;
      track.append(fill);
      row.append(track, node('strong', '', number(summary[key])));
      container.append(row);
    }

    const total = Number(summary.total) || 0;
    const rates = [
      ['Contactados', Number(summary.contactado) + Number(summary.inscrito) + Number(summary.pagado) + Number(summary.completado)],
      ['Inscritos', Number(summary.inscrito) + Number(summary.pagado) + Number(summary.completado)],
      ['Pagados', Number(summary.pagado) + Number(summary.completado)],
    ];
    const rateBox = $('conversionRates');
    rateBox.replaceChildren();
    for (const [label, reached] of rates) {
      const item = node('span');
      item.append(node('strong', '', `${total ? Math.round(reached / total * 100) : 0}%`),
        document.createTextNode(` ${label.toLowerCase()} o en etapa posterior`));
      rateBox.append(item);
    }

    const daily = new Map((data.tendencia_30d || []).map(item => [item.dia, Number(item.total) || 0]));
    const dayKey = new Intl.DateTimeFormat('sv-SE', { year: 'numeric', month: '2-digit',
      day: '2-digit', timeZone: 'America/Mexico_City' });
    const weeks = Array.from({ length: 4 }, (_, week) => {
      let count = 0;
      for (let day = 0; day < 7; day++) {
        const date = new Date(Date.now() - (27 - week * 7 - day) * 86_400_000);
        count += daily.get(dayKey.format(date)) || 0;
      }
      return count;
    });
    const trend = $('trendBars');
    trend.replaceChildren();
    const trendMax = Math.max(1, ...weeks);
    for (let index = 0; index < weeks.length; index++) {
      const column = node('div', 'trend-week');
      const bar = node('span', 'bar');
      bar.style.height = `${Math.max(3, weeks[index] / trendMax * 100)}px`;
      column.append(node('strong', '', number(weeks[index])), bar,
        node('span', '', index === 3 ? 'Últimos 7 días' : `Hace ${4 - index} sem.`));
      trend.append(column);
    }
  }

  async function loadSummary() {
    const data = await rpc('crm_resumen', filters());
    renderSummary(data);
  }

  function renderRows(data) {
    state.rows = data.filas;
    state.totalRows = Number(data.total) || 0;
    const body = $('leadsBody');
    body.replaceChildren();
    if (!state.rows.length) {
      const row = node('tr');
      const cell = node('td', '', 'No hay inscripciones con estos filtros.');
      cell.colSpan = 7;
      row.append(cell);
      body.append(row);
    }
    for (const lead of state.rows) {
      const row = node('tr');
      const paymentChoice = lead.respuestas?.solicita_beca;
      if (paymentChoice === false) row.className = 'lead-priority';
      const person = node('td');
      person.append(node('strong', '', lead.nombre), node('small', '', lead.email));
      const status = node('span', 'status-pill', stageNames[lead.estatus] || lead.estatus);
      status.dataset.status = lead.estatus;
      const statusCell = node('td');
      statusCell.append(status);
      const closed = lead.estatus === 'completado' || lead.estatus === 'perdido';
      const due = node('td', !closed && lead.proximo_contacto_at && new Date(lead.proximo_contacto_at) < new Date()
        ? 'due-overdue' : 'due-unscheduled', closed ? 'Cerrado' : formatDateTime(lead.proximo_contacto_at));
      const actionCell = node('td');
      const action = node('button', 'text-button', 'Abrir ficha');
      action.type = 'button';
      action.addEventListener('click', () => openLead(lead));
      actionCell.append(action);
      const payment = node('span', 'payment-label', paymentChoice === false ? 'Precio completo' :
        paymentChoice === true ? 'Solicita beca' : 'Sin dato');
      payment.dataset.choice = paymentChoice === false ? 'full' : paymentChoice === true ? 'beca' : 'unknown';
      const paymentCell = node('td');
      paymentCell.append(payment);
      row.append(person, node('td', '', lead.curso), paymentCell, statusCell, due,
        node('td', '', formatDate(lead.created_at)), actionCell);
      body.append(row);
    }
    const first = state.totalRows ? state.offset + 1 : 0;
    const last = Math.min(state.offset + state.limit, state.totalRows);
    const queueNames = { precio_completo: 'precio completo', sin_contacto: 'sin primer contacto', vencidos: 'vencidos', sin_programar: 'sin programar' };
    $('resultCount').textContent = `${number(state.totalRows)} resultados${state.queue ? ` · ${queueNames[state.queue]}` : ''}`;
    $('pageLabel').textContent = `${first}–${last} de ${number(state.totalRows)}`;
    $('prevPage').disabled = state.offset === 0;
    $('nextPage').disabled = state.offset + state.limit >= state.totalRows;
  }

  async function loadRows() {
    const request = ++state.listRequest;
    const base = {
      ...filters(),
      p_estatus: $('statusFilter').value || null,
      p_busqueda: $('searchInput').value.trim() || null,
      p_limit: state.limit,
      p_offset: state.offset,
    };
    const data = state.queue === 'precio_completo'
      ? await rpc('crm_prioridad_precio', base)
      : await rpc('crm_listar_inscripciones', {
        ...base, p_cola: state.queue || ($('pendingOnly').checked ? 'pendientes' : null),
      });
    if (request === state.listRequest) renderRows(data);
  }

  async function loadPriorityCount() {
    const data = await rpc('crm_prioridad_precio', {
      ...filters(), p_estatus: null, p_busqueda: null, p_limit: 1, p_offset: 0,
    });
    $('priorityFullPrice').textContent = number(data.total);
  }

  async function refreshAll() {
    message('dashboardStatus', 'Cargando datos…');
    try {
      await Promise.all([loadSummary(), loadRows(), loadPriorityCount()]);
      message('dashboardStatus', 'Datos actualizados.', 'success');
    } catch (error) {
      message('dashboardStatus', error.message, 'error');
    }
  }

  function setLink(id, text, href) {
    const link = $(id);
    link.textContent = text || '—';
    link.removeAttribute('href');
    if (href) link.href = href;
  }

  function renderAnswers(answers) {
    const box = $('leadAnswers');
    box.replaceChildren();
    if (!answers || typeof answers !== 'object') return;
    const labels = {
      edad: 'Edad', residencia: 'Residencia', solicita_beca: 'Solicita beca',
      aporte_mxn: 'Puede pagar', propuesta_intercambio: 'Propuesta de colaboración',
      experiencia_qgis: 'Experiencia con QGIS', horario_preferido: 'Horario preferido',
      que_descubrir: 'Qué quiere descubrir', primera_palabra: 'Palabra sobre mapas',
      creencia_a_probar: 'Creencia a poner a prueba',
    };
    const list = node('dl');
    for (const [key, label] of Object.entries(labels)) {
      const raw = answers[key];
      if (raw == null || raw === '') continue;
      const value = key === 'solicita_beca' ? (raw ? 'Sí' : 'No') :
        key === 'aporte_mxn' ? `$${number(raw)} MXN` : raw;
      list.append(node('dt', '', label), node('dd', '', value));
    }
    if (list.childElementCount) box.append(node('h3', '', 'Datos del registro'), list);
  }

  async function loadHistory(id) {
    const history = await rpc('crm_historial', { p_inscripcion_id: id });
    const list = $('historyList');
    list.replaceChildren();
    if (!history.length) {
      list.append(node('li', '', 'Aún no hay actividades registradas en este panel.'));
      return;
    }
    for (const item of history) {
      const entry = node('li');
      entry.append(node('strong', '', item.tipo === 'nota' ? 'Nota interna' : item.tipo),
        node('time', '', formatDateTime(item.created_at)));
      if (item.estatus_anterior !== item.estatus_nuevo) {
        entry.append(node('span', '', `${stageNames[item.estatus_anterior]} → ${stageNames[item.estatus_nuevo]}`));
      }
      entry.append(node('p', '', item.nota));
      if (item.proximo_contacto_at) entry.append(node('small', '', `Próximo: ${formatDateTime(item.proximo_contacto_at)}`));
      list.append(entry);
    }
  }

  async function openLead(lead) {
    state.selected = lead;
    $('leadTitle').textContent = lead.nombre;
    $('leadCourse').textContent = lead.curso;
    $('leadCreated').textContent = formatDate(lead.created_at);
    $('leadInstagram').textContent = lead.instagram || '—';
    $('leadLastContact').textContent = lead.ultimo_contacto || 'No registrado';
    setLink('leadEmail', lead.email, `mailto:${lead.email}`);
    const digits = (lead.whatsapp || '').replace(/\D/g, '');
    setLink('leadWhatsapp', lead.whatsapp, digits ? `https://wa.me/${digits}` : null);
    renderAnswers(lead.respuestas);
    $('followupStatus').value = lead.estatus;
    $('followupType').value = 'nota';
    $('followupNext').value = lead.proximo_contacto_at ? localDateTime(lead.proximo_contacto_at) : '';
    updateNextContactField();
    $('followupNote').value = '';
    message('followupMessage', '');
    $('historyList').replaceChildren(node('li', '', 'Cargando historial…'));
    $('leadDialog').showModal();
    document.dispatchEvent(new CustomEvent('crm:lead', { detail: { id: lead.id, curso: lead.curso,
      nombre: lead.nombre, solicitaBeca: lead.respuestas?.solicita_beca === true } }));
    try { await loadHistory(lead.id); }
    catch (error) { $('historyList').replaceChildren(node('li', '', error.message)); }
  }

  function localDateTime(value) {
    const date = new Date(value);
    const pad = part => String(part).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }

  function updateNextContactField() {
    const closed = ['completado', 'perdido'].includes($('followupStatus').value);
    $('followupNext').disabled = closed;
    if (closed) $('followupNext').value = '';
  }

  async function saveFollowup(event) {
    event.preventDefault();
    if (!state.selected || !$('followupForm').reportValidity()) return;
    if (!$('followupNote').value.trim()) {
      message('followupMessage', 'Escribe una nota sobre el seguimiento.', 'error');
      return;
    }
    const button = $('followupForm').querySelector('button[type="submit"]');
    button.disabled = true;
    message('followupMessage', 'Guardando…');
    try {
      const nextContact = $('followupNext').disabled || !$('followupNext').value
        ? null : new Date($('followupNext').value).toISOString();
      await rpc('crm_guardar_seguimiento', {
        p_inscripcion_id: state.selected.id,
        p_estatus: $('followupStatus').value,
        p_tipo: $('followupType').value,
        p_nota: $('followupNote').value.trim(),
        p_proximo_contacto_at: nextContact,
      });
      state.selected.estatus = $('followupStatus').value;
      state.selected.proximo_contacto_at = nextContact;
      $('followupNote').value = '';
      message('followupMessage', 'Seguimiento guardado.', 'success');
      await Promise.all([loadHistory(state.selected.id), refreshAll()]);
    } catch (error) {
      message('followupMessage', error.message, 'error');
    } finally { button.disabled = false; }
  }

  function debounce(fn, delay) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
  }

  async function signIn(event) {
    event.preventDefault();
    const button = $('loginForm').querySelector('button[type="submit"]');
    button.disabled = true;
    message('loginStatus', 'Verificando cuenta…');
    try {
      const data = await authRequest('token?grant_type=password', {
        email: $('loginEmail').value.trim().toLowerCase(),
        password: $('loginPassword').value,
      });
      saveSession({ accessToken: data.access_token, refreshToken: data.refresh_token,
        expiresAt: Date.now() + data.expires_in * 1000 });
      await rpc('crm_resumen', { p_curso_id: null, p_desde: null, p_hasta: null });
      $('loginPassword').value = '';
      showDashboard(true);
      await refreshAll();
    } catch (error) {
      saveSession(null);
      message('loginStatus', error.message, 'error');
    } finally { button.disabled = false; }
  }

  async function signOut() {
    const token = state.session?.accessToken;
    saveSession(null);
    showDashboard(false);
    if (token) authRequest('logout', {}, token).catch(() => {});
  }

  $('loginForm').addEventListener('submit', signIn);
  $('logoutButton').addEventListener('click', signOut);
  $('refreshButton').addEventListener('click', refreshAll);
  $('applyFilters').addEventListener('click', () => { state.offset = 0; refreshAll(); });
  $('statusFilter').addEventListener('change', () => { state.queue = null; state.offset = 0; loadRows().catch(error => message('dashboardStatus', error.message, 'error')); });
  $('pendingOnly').addEventListener('change', () => { state.queue = null; state.offset = 0; loadRows().catch(error => message('dashboardStatus', error.message, 'error')); });
  $('searchInput').addEventListener('input', debounce(() => { state.offset = 0; loadRows().catch(error => message('dashboardStatus', error.message, 'error')); }, 300));
  $('prevPage').addEventListener('click', () => { state.offset = Math.max(0, state.offset - state.limit); loadRows().catch(error => message('dashboardStatus', error.message, 'error')); });
  $('nextPage').addEventListener('click', () => { state.offset += state.limit; loadRows().catch(error => message('dashboardStatus', error.message, 'error')); });
  document.querySelectorAll('[data-queue]').forEach(button => button.addEventListener('click', () => {
    state.queue = button.dataset.queue === 'fullprice' ? 'precio_completo' :
      button.dataset.queue === 'uncontacted' ? 'sin_contacto' :
      button.dataset.queue === 'overdue' ? 'vencidos' : 'sin_programar';
    $('pendingOnly').checked = false;
    $('statusFilter').value = '';
    state.offset = 0;
    $('leadsTitle').scrollIntoView({ behavior: 'smooth' });
    loadRows().catch(error => message('dashboardStatus', error.message, 'error'));
  }));
  $('closeDialog').addEventListener('click', () => $('leadDialog').close());
  $('followupStatus').addEventListener('change', updateNextContactField);
  $('followupForm').addEventListener('submit', saveFollowup);

  document.addEventListener('crm:payment-updated', () => {
    if (state.selected) loadHistory(state.selected.id).catch(() => {});
    refreshAll();
  });

  window.CARTOGRAFUNK_CRM = Object.freeze({ rpc, accessToken });

  try {
    const stored = JSON.parse(sessionStorage.getItem(sessionKey) || 'null');
    if (stored?.accessToken && stored?.refreshToken) {
      state.session = stored;
      accessToken().then(() => rpc('crm_resumen', { p_curso_id: null, p_desde: null, p_hasta: null }))
        .then(() => { showDashboard(true); return refreshAll(); })
        .catch(() => { saveSession(null); showDashboard(false); });
    }
  } catch { sessionStorage.removeItem(sessionKey); }
})();
