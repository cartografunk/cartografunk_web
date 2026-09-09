(() => {
  const status = document.getElementById('metaInsightsStatus');
  if (!status) return;
  const endpoint = window.CARTOGRAFUNK_INSIGHTS_ENDPOINT;
  if (!endpoint) return;
  fetch(endpoint).then(response => {
    if (!response.ok) throw new Error('insights unavailable');
    return response.json();
  }).then(payload => {
    status.textContent = `Métricas actualizadas automáticamente · ${new Date(payload.fetched_at).toLocaleDateString('es-MX')}`;
  }).catch(() => {
    status.textContent = 'Métricas verificadas manualmente · actualización automática no disponible';
  });
})();
