/**
 * Cartografunk — Hero Map D3
 * Mapa de México con animación "scan" secuencial de estados
 * Archivos: data/estados.geojson, data/division_estatal.geojson
 *
 * Uso: <script src="js/hero-map.js"></script>
 * Requiere: D3 v7 cargado antes en el HTML
 * Target: <div id="hero-map"></div>
 */

(function () {
  "use strict";

  /* ─── Paleta desde variables CSS del sitio ─────────────────────────── */
  const C = {
    bg:           "#080810",
    fill_base:    "rgba(160, 80, 255, 0.04)",   // estado en reposo
    fill_hover:   "rgba(180, 79, 255, 0.22)",   // hover manual
    fill_active:  "rgba(208, 112, 255, 0.38)",  // estado "encendido" en scan
    stroke_div:   "rgba(255, 255, 255, 0.25)",   // division_estatal lines
    glow:         "#b44fff",
  };

  /* ─── Config animación ─────────────────────────────────────────────── */
  const CFG = {
    scanInterval:  90,    // ms entre estado y estado en el scan
    scanHold:      420,   // ms que un estado permanece "encendido"
    scanFade:      600,   // ms de fade-out del encendido
    scanLoopDelay: 2800,  // ms de pausa antes de reiniciar el loop
    scanRandom:    true,  // true = orden aleatorio, false = geográfico
  };

  /* ─── Bootstrap ────────────────────────────────────────────────────── */
  function init() {
    const container = document.getElementById("hero-map");
    if (!container) return;

    const W = container.clientWidth  || window.innerWidth;
    const H = container.clientHeight || Math.round(W * 0.52);

    /* SVG */
    const svg = d3.select(container)
      .append("svg")
      .attr("viewBox", `0 0 ${W} ${H}`)
      .attr("preserveAspectRatio", "xMidYMid meet")
      .style("width", "100%")
      .style("height", "100%")
      .style("background", "transparent");

    /* Defs: filtro glow reutilizable */
    const defs = svg.append("defs");

    const glow = defs.append("filter")
      .attr("id", "state-glow")
      .attr("x", "-30%").attr("y", "-30%")
      .attr("width", "160%").attr("height", "160%");

    glow.append("feGaussianBlur")
      .attr("in", "SourceGraphic")
      .attr("stdDeviation", "6")
      .attr("result", "blur");

    const feMerge = glow.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "blur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    /* Grupos — orden de capas */
    const gStates = svg.append("g").attr("class", "layer-states");
    const gLines  = svg.append("g").attr("class", "layer-division");

    /* Carga de datos */
    Promise.all([
      d3.json("data/estados.geojson"),
      d3.json("data/division_estatal.geojson"),
    ]).then(([estadosGeo, divisionGeo]) => {
      build(svg, gStates, gLines, estadosGeo, divisionGeo, W, H);
    }).catch(err => {
      console.warn("[CartografunkMap] No se pudieron cargar los GeoJSON:", err);
    });
  }

  /* ─── Build ────────────────────────────────────────────────────────── */
  function build(svg, gStates, gLines, estadosGeo, divisionGeo, W, H) {

    /* Proyección ajustada al contenedor */
    const projection = d3.geoMercator()
      .fitExtent([[W * 0.05, H * 0.05], [W * 0.95, H * 0.95]], estadosGeo);

    const path = d3.geoPath().projection(projection);

    /* ── Polígonos de estados ── */
    const statePaths = gStates.selectAll("path")
      .data(estadosGeo.features)
      .join("path")
      .attr("class", "estado")
      .attr("d", path)
      .attr("fill", C.fill_base)
      .attr("stroke", C.stroke_state)
      .attr("stroke-width", 0.5)
      .style("cursor", "crosshair")
      .style("transition", "fill 0.2s ease");

    /* Hover manual (sin interferir con el scan) */
    statePaths
      .on("mouseenter", function () {
        const el = d3.select(this);
        if (!el.classed("scanning")) {
          el.attr("fill", C.fill_hover);
        }
      })
      .on("mouseleave", function () {
        const el = d3.select(this);
        if (!el.classed("scanning")) {
          el.attr("fill", C.fill_base);
        }
      });

    /* ── Líneas de división estatal ── */
    gLines.selectAll("path")
      .data(divisionGeo.features)
      .join("path")
      .attr("class", "division-line")
      .attr("d", path)
      .attr("fill", "none")
      .attr("stroke", C.stroke_div)
      .attr("stroke-width", 0.8)
      .attr("stroke-linejoin", "round");

    /* ── Animación scan ── */
    const nodes = statePaths.nodes();
    startScan(nodes);
  }

  /* ─── Scan loop ────────────────────────────────────────────────────── */
  function startScan(nodes) {
    let order = nodes.map((_, i) => i);
    if (CFG.scanRandom) shuffle(order);

    let idx = 0;
    let timeouts = [];

    function fireNext() {
      if (idx >= order.length) {
        // Pausa antes de reiniciar
        const t = setTimeout(() => {
          if (CFG.scanRandom) shuffle(order);
          idx = 0;
          fireNext();
        }, CFG.scanLoopDelay);
        timeouts.push(t);
        return;
      }

      const el = d3.select(nodes[order[idx]]);
      idx++;

      /* Encender */
      el.classed("scanning", true)
        .attr("fill", C.fill_active)
        .attr("filter", "url(#state-glow)");

      /* Apagar después de scanHold ms */
      const t1 = setTimeout(() => {
        el.transition()
          .duration(CFG.scanFade)
          .attr("fill", C.fill_base)
          .on("end", () => {
            el.classed("scanning", false)
              .attr("filter", null);
          });
      }, CFG.scanHold);

      timeouts.push(t1);

      /* Siguiente estado */
      const t2 = setTimeout(fireNext, CFG.scanInterval);
      timeouts.push(t2);
    }

    fireNext();

    /* Cleanup si el elemento se remueve del DOM */
    return () => timeouts.forEach(clearTimeout);
  }

  /* ─── Utils ────────────────────────────────────────────────────────── */
  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }

  /* ─── Entry point ──────────────────────────────────────────────────── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
