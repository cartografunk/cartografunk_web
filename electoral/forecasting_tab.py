"""Vista aislada del ensayo retrospectivo de forecasting local."""

from pathlib import Path

import pandas as pd
import streamlit as st

from electoral.diagnostico_forecast import (
    MODELOS_CON_INTERVALO, PARTIDOS, cargar_benchmark, diagnostico_secciones,
)


@st.cache_data(max_entries=2)
def _cargar(carpeta: Path) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    return cargar_benchmark(carpeta)


def mostrar_diagnostico_forecast(estado: int, root: Path) -> None:
    st.subheader("Forecasting · prueba retrospectiva 2024")
    st.caption("Diputaciones locales MR · unidad: sección · Querétaro es el filtro de muestra. Reparto fraccionario de coaliciones por partido.")
    if estado != 22:
        st.info("Selecciona Querétaro en el filtro de muestra para abrir este ensayo local.")
        return
    carpeta = root / "data/electoral/ieeq_local"
    required = ("benchmark_partidos_2024.json", "benchmark_partidos_2024_seccion.parquet",
                "crosswalk_qro_2018_2021_2024_referencias.parquet")
    if not all((carpeta / name).exists() for name in required):
        st.info("El diagnóstico requiere archivos locales del benchmark y cruce territorial; se oculta cuando faltan.")
        return
    informe, predicciones, cruce = _cargar(carpeta)
    partido = st.selectbox("Partido del ensayo", PARTIDOS, index=PARTIDOS.index("MORENA"), key="forecast_partido")
    modelo = st.selectbox("Método", MODELOS_CON_INTERVALO, index=1,
                         format_func=lambda x: "Ridge" if x == "ridge" else "Persistencia 2021",
                         key="forecast_modelo")
    datos = diagnostico_secciones(informe, predicciones, cruce, partido, modelo)
    cobertura = informe["universo"]["comparable"]
    partido_info = informe["resultados"][modelo]["por_partido"][partido]
    metricas = st.columns(3)
    metricas[0].metric("Secciones comparables", f"{cobertura['secciones']}/{informe['universo']['total_secciones']}")
    metricas[1].metric("Lista nominal cubierta", f"{cobertura['cobertura_lista_nominal_pct']:.1f} %")
    metricas[2].metric("MAE de cuota del partido", f"{partido_info['mae_pct']:.1f} pp")
    sin_modelo = informe["universo"]["total_secciones"] - cobertura["secciones"]
    sustantivo = "sección queda" if sin_modelo == 1 else "secciones quedan"
    st.caption(f"{sin_modelo} {sustantivo} sin modelo por cambio territorial. El estado sólo filtra la muestra; no se muestran resultados agregados por estado, municipio o distrito.")
    st.warning("Ensayo retrospectivo, no pronóstico validado. “Lidera” compara siete partidos con serie 2018–2024; no equivale a ganar la candidatura MR. El intervalo nominal 90 % no alcanzó esa cobertura en todos los partidos.")
    resumen = datos.LECTURA.value_counts()
    st.write(
        f"{int(resumen.get('Lidera entre siete partidos', 0))} secciones: lidera · "
        f"{int(resumen.get('No lidera entre siete partidos', 0))}: no lidera · "
        f"{int(resumen.get('Indeterminado: intervalo cruza empate', 0))}: indeterminado · "
        f"{int(resumen.get('Sin modelo: sección modificada', 0))}: sin modelo."
    )
    st.caption(f"En el resultado observado lideró en {partido_info['lideres_observados']} de las {cobertura['secciones']} comparables; "
               f"el método detectó {partido_info['lideres_detectados']}. "
               "Esto mide desempeño retrospectivo, no confianza futura.")
    vista = datos.rename(columns={
        "ID_SECCION": "Sección", "LECTURA": "Lectura del ensayo",
        "CUOTA_PREDICHA_PCT": "Cuota estimada (%)", "CUOTA_OBSERVADA_PCT": "Cuota observada 2024 (%)",
        "MARGEN_PREDICHO_PP": "Margen estimado (pp)", "MARGEN_OBSERVADO_PP": "Margen observado 2024 (pp)",
        "LIMITE_INFERIOR_PP": "Límite inferior (pp)", "LIMITE_SUPERIOR_PP": "Límite superior (pp)",
    })[["Sección", "Lectura del ensayo", "Cuota estimada (%)", "Cuota observada 2024 (%)",
        "Margen estimado (pp)", "Margen observado 2024 (pp)", "Límite inferior (pp)", "Límite superior (pp)"]]
    st.dataframe(vista, hide_index=True, width="stretch",
                 alt="Diagnóstico retrospectivo por sección con predicción, resultado observado y abstenciones")
    st.subheader("Leer una sección")
    seccion = st.selectbox("Sección del ensayo", datos.ID_SECCION.tolist(), key="forecast_seccion")
    fila = datos.set_index("ID_SECCION").loc[seccion]
    if pd.isna(fila.MARGEN_PREDICHO_PP):
        st.info("Esta sección no recibió estimación: su perímetro cambió entre los cortes comparados. El encarte no permite repartir su voto anterior.")
    else:
        base_2021 = predicciones.loc[
            predicciones.ID_SECCION.eq(seccion) & predicciones.PARTIDO.eq(partido)
            & predicciones.MODELO.eq("persistencia")
        ]
        if len(base_2021) != 1:
            raise ValueError("Falta la cuota 2021 usada como referencia")
        cuota_2021 = float(base_2021.iloc[0].CUOTA_PREDICHA_PCT)
        cambio = fila.CUOTA_PREDICHA_PCT - cuota_2021
        st.write(
            f"En 2021, la cuota atribuida a {partido} fue {cuota_2021:.1f} %. "
            f"{modelo.capitalize()} estimó {fila.CUOTA_PREDICHA_PCT:.1f} % para 2024 "
            f"({cambio:+.1f} puntos). El margen estimado frente al mayor de los otros "
            f"seis partidos fue {fila.MARGEN_PREDICHO_PP:+.1f} puntos; su intervalo "
            f"histórico va de {fila.LIMITE_INFERIOR_PP:+.1f} a {fila.LIMITE_SUPERIOR_PP:+.1f}. "
            f"Lectura: {fila.LECTURA.lower()}."
        )
        st.caption("Esta explicación describe las entradas y la salida del método; asociación, no causa. El resultado observado de 2024 está en la tabla para comprobar el ensayo.")
    st.download_button("Descargar diagnóstico por sección", vista.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"diagnostico_forecast_{partido}_{modelo}_2024.csv", mime="text/csv")
    with st.expander("Avanzado · método y límites"):
        st.write("El método aprende de la transición 2018→2021 y estima 2024 con la cuota, participación y lista nominal de 2021. "
                 "El intervalo se calibró con errores históricos. CPV 2020 no entra al modelo; el bloque «¿Por qué?» "
                 "de la app describe asociaciones CPV 2020 vs votos 2024, no explica causalmente esta predicción.")
        st.write(f"Semianchura del intervalo: {partido_info['intervalo_90_semianchura_pp']:.1f} pp. "
                 f"Cobertura observada en 2024: {partido_info['cobertura_empirica_intervalo_pct']:.1f} %. ")
        st.caption("Los 19 IDs desaparecidos y 81 nuevos se auditan por separado. El domicilio de casilla no redistribuye electores ni votos. "
                   "NO VERIFICADO: equivalencia exacta del marco 2018, desempeño prospectivo, reparto entero distrital y reasignación de personas en las secciones modificadas.")
