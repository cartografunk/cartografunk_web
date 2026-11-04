"""Portada y explicación de los métodos disponibles en el laboratorio."""

import streamlit as st


def mostrar_portada(eleccion: str) -> None:
    """Presenta el alcance y las fórmulas sin ejecutar cálculos adicionales."""
    st.html("""
<style>
.le-hero{position:relative;isolation:isolate;overflow:hidden;background:radial-gradient(circle at 86% 0%,#302042 0%,#1a1729 50%,#141323 100%);color:#f7f5fa;border:1px solid #513865;border-radius:18px;padding:clamp(26px,3vw,42px);font-family:Arial,Helvetica,sans-serif}
.le-hero:after{content:"";position:absolute;left:0;right:0;bottom:0;height:6px;background:linear-gradient(90deg,#3c84bb 0 34%,#e9bd53 34% 67%,#d45851 67%)}
.le-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(270px,.8fr);align-items:center;gap:22px}
.le-title{font-size:clamp(3.25rem,6vw,6.8rem);line-height:.91;letter-spacing:-.065em;margin:8px 0 12px;font-weight:900;max-width:11ch}
.le-title span{color:#e1b8ff}
.le-map{width:100%;min-height:220px;opacity:.78;transform:rotate(-4deg);filter:drop-shadow(0 12px 18px rgba(0,0,0,.2));background:url('/app/static/mexico_estados.svg') center/contain no-repeat}
.le-rail{display:flex;gap:22px;flex-wrap:wrap;border-top:1px solid #584569;padding-top:18px;margin-top:14px;font-size:13px;color:#e1d7e8}
.le-rail strong{color:#d990ff;margin-right:7px;font-variant-numeric:tabular-nums}
@media(max-width:760px){.le-hero{padding:26px 22px}.le-grid{grid-template-columns:1fr}.le-title{font-size:clamp(3rem,12vw,5rem);margin:8px 0}.le-map{width:300px;max-width:100%;min-height:180px;margin:0 auto}.le-rail{gap:10px 22px}}
</style>
<section class="le-hero" aria-label="Presentación del Laboratorio Electoral">
  <div class="le-grid">
    <div>
      <h2 class="le-title">Laboratorio<br><span>Electoral</span></h2>
    </div>
    <div class="le-map" aria-label="Contornos estatales de México"></div>
  </div>
  <div class="le-rail"><span><strong>01</strong> Rentabilidad</span><span><strong>02</strong> Apoyo mínimo</span><span><strong>03</strong> Priorización</span><span><strong>04</strong> CPV - próximo</span></div>
</section>
""")

    st.markdown("### Tres formas de leer el territorio")
    st.caption(
        f"Cobertura actual: {eleccion}. Los resultados de otros años aún no están integrados. "
        "Diagnóstico exploratorio con datos agregados, tablas y descarga."
    )

    rent, apoyo, prioridad = st.tabs([
        "01 - Rentabilidad electoral", "02 - Apoyo mínimo (base electoral)",
        "03 - Priorización",
    ])
    with rent:
        st.subheader("Rentabilidad electoral")
        st.write(
            "El cálculo compara candidaturas en cada sección. Para una coalición, se suman "
            "los votos marcados por cada partido integrante y por cada combinación de esos partidos. "
            "Una candidatura individual conserva sus propios votos. Cada marca entra una sola vez "
            "en el total de su candidatura."
        )
        st.latex(r"V_{c,s}=\sum_{p\in P_c}V_{p,s}+\sum_{m\in M_c}V_{m,s}")
        st.caption(
            "V: votos de la candidatura c en la sección s. P: partidos integrantes. "
            "M: combinaciones de la misma candidatura registradas para esa elección y unidad."
        )
        st.write(
            "Después se ordenan las candidaturas activas de la sección. "
            "V₁ es el total más alto y V₂ el segundo más alto. "
            "Hay victoria solo si supera a V₂; si comparte el primer lugar, hay empate."
        )
        st.latex(r"V_{1,s}=\max_c V_{c,s}")
        st.write(
            "En caso de victoria, el margen mide la ventaja sobre el segundo lugar. "
            "En caso de derrota o empate, el faltante mide la distancia al primer lugar "
            "(cero votos cuando hay empate)."
        )
        st.latex(r"M_s=V_{c,s}-V_{2,s}\quad(\mathrm{victoria})")
        st.latex(r"F_s=V_{1,s}-V_{c,s}\quad(\mathrm{derrota\ o\ empate})")
        st.write(
            "El margen y el faltante en puntos porcentuales dividen esa diferencia entre "
            "los votos válidos de la sección. Para superar al primer lugar se necesita "
            "el faltante más un voto. En un empate, se necesita uno."
        )
        st.latex(r"m_s=100\frac{M_s}{V_{\mathrm{validos},s}}")
        st.latex(r"f_s=100\frac{F_s}{V_{\mathrm{validos},s}}")
        st.latex(r"G_s=F_s+1")
        st.markdown("#### Abstención corregida")
        st.write(
            "Para comparar esa meta con la abstención, se descuentan del total los votos "
            "de casillas especiales, que tienen lista nominal igual a cero."
        )
        st.latex(r"A_s=LN_s-(V_{\mathrm{total},s}-V_{S,s})")
        st.caption(
            "LN: lista nominal de la sección. V total: votos registrados. "
            "V S: votos de casillas especiales no anuladas."
        )
        st.caption(
            "Clases actuales: victoria sólida desde 15 pp de margen; derrota competitiva por debajo "
            "de 5 pp, derrota intermedia de 5 a menos de 15 pp y derrota lejana desde 15 pp."
        )
    with apoyo:
        st.subheader("Apoyo mínimo observado")
        st.write(
            "Para cada partido y sección se estima su porcentaje de votos válidos en las tres "
            "elecciones federales de 2024. El apoyo mínimo es el menor de esos tres porcentajes; "
            "el rango muestra cuánto cambió entre boletas."
        )
        st.latex(r"P_{p,s,e}=100\frac{V^A_{p,s,e}}{V_{\mathrm{validos},s,e}}")
        st.latex(r"\mathrm{piso}_{p,s}=\min_{e\in\{P,D,S\}}P_{p,s,e}")
        st.latex(r"R_{p,s}=\max_e P_{p,s,e}-\min_e P_{p,s,e}")
        st.write(
            "Las etiquetas «Bastión» y «Base fuerte» son una propuesta provisional: "
            "comparan el apoyo mínimo con el percentil del partido en el estado o en el país. "
            "Una sección volátil rebasa el umbral de Tukey del rango de su grupo."
        )
        st.caption(
            "El reparto A_propios de votos de coalición entre partidos es experimental. "
            "«Base electoral» nombra una medida agregada de 2024; no demuestra fidelidad individual."
        )
    with prioridad:
        st.subheader("Priorización de secciones")
        st.write(
            "El simulador ordena secciones con derrota o empate que tienen abstención positiva. "
            "Puedes indicar un costo estimado por voto, cambiarlo por sección, descartar secciones "
            "y probar un presupuesto. Son supuestos tuyos para comparar escenarios."
        )
        st.latex(r"C_s=(F_s+1)c_s")
        st.caption("Cₛ: costo estimado de la sección; cₛ: costo por voto supuesto por el usuario.")
        st.write(
            "La meta de un distrito usa su faltante agregado más un voto. El simulador compara "
            "esa meta con la abstención disponible de las secciones no descartadas, ordenadas por costo."
        )
        st.caption("No estima que una persona se abstuvo por una causa específica ni predice que votará por una candidatura.")

    st.html("""
<aside style="border-left:3px solid #b44fff;background:#1b1627;border-radius:8px;
  padding:15px 19px;color:#e5daec;font-family:Arial,Helvetica,sans-serif;line-height:1.45">
  <strong style="color:#e1b8ff;letter-spacing:.08em;font-size:12px">04 - PRÓXIMO CRUCE</strong><br>
  Datos sociodemográficos del Censo de Población y Vivienda (CPV).
  Aún no están integrados en este laboratorio.
</aside>
""")
