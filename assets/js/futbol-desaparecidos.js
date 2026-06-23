/**
 * futbol-desaparecidos.js
 * Visualizador: Fútbol y Personas Desaparecidas en México
 * Cartografunk · 2024
 *
 * Fuente de datos: goles_y_desaparecidos_final.csv
 * Período cubierto: 2000–2017
 * Requiere: Chart.js (cargado antes de este script)
 */

(function () {
  "use strict";

  /* ── Datos ── */
  const RAW = [
    { y: 2000, total: 48,    desp: 34,    goles: 31 },
    { y: 2001, total: 36,    desp: 26,    goles: 24 },
    { y: 2002, total: 46,    desp: 38,    goles: 17 },
    { y: 2003, total: 42,    desp: 32,    goles: 19 },
    { y: 2004, total: 60,    desp: 30,    goles: 41 },
    { y: 2005, total: 120,   desp: 96,    goles: 53 },
    { y: 2006, total: 612,   desp: 178,   goles: 42 },
    { y: 2007, total: 5200,  desp: 1272,  goles: 48 },
    { y: 2008, total: 5588,  desp: 1604,  goles: 46 },
    { y: 2009, total: 8572,  desp: 2764,  goles: 42 },
    { y: 2010, total: 12144, desp: 6458,  goles: 43 },
    { y: 2011, total: 17856, desp: 8228,  goles: 59 },
    { y: 2012, total: 18686, desp: 6584,  goles: 31 },
    { y: 2013, total: 27772, desp: 7302,  goles: 38 },
    { y: 2014, total: 27922, desp: 7582,  goles: 38 },
    { y: 2015, total: 22424, desp: 6554,  goles: 48 },
    { y: 2016, total: 21292, desp: 9084,  goles: 33 },
    { y: 2017, total: 21198, desp: 11040, goles: 39 },
  ];

  const VIEWS = {
    all:    RAW,
    pre:    RAW.filter(d => d.y <= 2005),
    crisis: RAW.filter(d => d.y >= 2006 && d.y <= 2012),
    post:   RAW.filter(d => d.y >= 2013),
  };

  let chart = null;
  let currentView = "all";

  /* ── Métricas de resumen ── */
  function calcMetrics(data) {
    return {
      total: data.reduce((s, d) => s + d.total, 0),
      desp:  data.reduce((s, d) => s + d.desp,  0),
    };
  }

  function updateMetrics(data) {
    const m = calcMetrics(data);
    const elTotal = document.getElementById("fd-metric-total");
    const elDesp  = document.getElementById("fd-metric-desp");
    if (elTotal) elTotal.textContent = m.total.toLocaleString("es-MX");
    if (elDesp)  elDesp.textContent  = m.desp.toLocaleString("es-MX");
  }

  /* ── Construcción de la gráfica ── */
  function buildChart(data) {
    const canvas = document.getElementById("fd-chart");
    if (!canvas) return;

    const tickColor = "#f2eeff";
    const gridColor = "rgba(160,80,255,0.12)";

    if (chart) chart.destroy();

    chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: data.map(d => d.y),
        datasets: [
          {
            label: "Casos registrados",
            data: data.map(d => d.total),
            backgroundColor: "#b44fff",
            yAxisID: "y",
            order: 2,
            borderRadius: 2,
          },
          {
            label: "Personas desaparecidas",
            data: data.map(d => d.desp),
            backgroundColor: "rgba(208,112,255,0.45)",
            yAxisID: "y",
            order: 3,
            borderRadius: 2,
          },
          {
            label: "Goles selección",
            data: data.map(d => d.goles),
            type: "line",
            borderColor: "#EF9F27",
            backgroundColor: "rgba(239,159,39,0.12)",
            borderDash: [5, 3],
            borderWidth: 2,
            pointBackgroundColor: "#EF9F27",
            pointRadius: 3,
            yAxisID: "y2",
            tension: 0.3,
            order: 1,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => {
                const v = ctx.raw;
                if (ctx.datasetIndex === 2) return ` Goles selección: ${v}`;
                if (ctx.datasetIndex === 0) return ` Casos registrados: ${v.toLocaleString("es-MX")}`;
                return ` Personas desaparecidas: ${v.toLocaleString("es-MX")}`;
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: tickColor,
              font: { family: "DM Mono, monospace", size: 11 },
              autoSkip: false,
              maxRotation: 45,
            },
            grid: { color: gridColor },
          },
          y: {
            position: "left",
            ticks: {
              color: tickColor,
              font: { size: 11 },
              callback: v => v >= 1000 ? (v / 1000).toFixed(0) + "k" : v,
            },
            grid: { color: gridColor },
            title: {
              display: true,
              text: "Personas",
              font: { size: 11 },
              color: tickColor,
            },
          },
          y2: {
            position: "right",
            ticks: {
              color: "#EF9F27",
              font: { size: 11 },
            },
            grid: { drawOnChartArea: false },
            title: {
              display: true,
              text: "Goles",
              font: { size: 11 },
              color: "#BA7517",
            },
            min: 0,
            max: 80,
          },
        },
      },
    });
  }

  /* ── Control de vistas ── */
  function setView(v) {
    currentView = v;
    document.querySelectorAll(".fd-filter[data-view]").forEach(btn => {
      btn.setAttribute("aria-pressed", btn.dataset.view === v ? "true" : "false");
    });
    const data = VIEWS[v] || RAW;
    buildChart(data);
    updateMetrics(data);
  }

  /* ── Init ── */
  function init() {
    if (typeof Chart === "undefined") {
      console.warn("futbol-desaparecidos.js: Chart.js no está cargado.");
      return;
    }

    /* Bind buttons */
    document.querySelectorAll(".fd-filter[data-view]").forEach(btn => {
      btn.addEventListener("click", () => setView(btn.dataset.view));
    });

    buildChart(RAW);
    updateMetrics(RAW);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
