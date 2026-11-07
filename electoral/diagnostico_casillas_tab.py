"""Vista de patrones CPV y esfuerzo exploratorio por casilla local."""

from pathlib import Path

import pandas as pd
import streamlit as st

from electoral.diagnostico_casillas import (
    cobertura, costo_hipotetico, evaluar_partido, incorporar_apoyo_minimo,
    perfil_cpv, preparar_casillas, proponer_esfuerzo,
)
from electoral.reparto_ieeq import PARTIDOS_COMUNES


@st.cache_data(max_entries=2)
def _cargar(root: Path) -> pd.DataFrame:
    carpeta = root / "data/electoral/ieeq_local"
    preparado = carpeta / "diagnostico_casillas_cpv_2024.parquet"
    if preparado.exists():
        return pd.read_parquet(preparado)
    encarte = carpeta / "encarte_qro_2024_claves.parquet"
    return preparar_casillas(
        pd.read_parquet(carpeta / "dip_local_mr_2024_casilla.parquet"),
        pd.read_parquet(carpeta / "crosswalk_qro_2018_2021_2024_referencias.parquet"),
        pd.read_parquet(root / "data/electoral/cpv_2020_seccion.parquet"),
        pd.read_parquet(encarte) if encarte.exists() else None,
    )


@st.cache_data(max_entries=2)
def _cargar_apoyo(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path, columns=["ID_SECCION", "partido", "piso_pct", "ID_ESTADO"])


def mostrar_diagnostico_casillas(estado: int, root: Path) -> None:
    st.subheader("¿Dónde vale la pena actuar? · diagnóstico por casilla")
    st.caption("Diputaciones locales MR 2024 · CPV 2020 vs votos 2024 · asociación, no causa. "
               "Querétaro es filtro de muestra; las filas son casillas B/C/E, no promedios estatales.")
    if estado != 22:
        st.info("Selecciona Querétaro en el filtro de muestra para abrir este piloto.")
        return
    carpeta = root / "data/electoral/ieeq_local"
    necesarios = (carpeta / "dip_local_mr_2024_casilla.parquet",
                  carpeta / "crosswalk_qro_2018_2021_2024_referencias.parquet",
                  root / "data/electoral/cpv_2020_seccion.parquet")
    if not all(p.exists() for p in necesarios):
        st.info("Faltan archivos locales IEEQ, cruce cartográfico o CPV; el diagnóstico se oculta.")
        return
    partido = st.selectbox("Partido", PARTIDOS_COMUNES, index=PARTIDOS_COMUNES.index("MORENA"),
                           key="casillas_partido")
    base = proponer_esfuerzo(evaluar_partido(_cargar(root), partido))
    apoyo_path = root / "data/electoral/fidelidad_estado.parquet"
    if apoyo_path.exists():
        apoyo = _cargar_apoyo(apoyo_path)
        base = incorporar_apoyo_minimo(base, apoyo.loc[apoyo.ID_ESTADO.eq(22)], partido)
    else:
        base["APOYO_MINIMO_FEDERAL_2024_PCT"] = float("nan")
    cub = cobertura(base)
    a, b, c = st.columns(3)
    a.metric("Casillas con CPV comparable", f"{cub['casillas_cpv']:,}/{cub['casillas']:,}")
    b.metric("Secciones con CPV comparable", f"{cub['secciones_cpv']:,}/{cub['secciones']:,}")
    c.metric("Lista nominal cubierta", f"{cub['lista_nominal_pct']:.1f} %")
    st.caption("Las casillas especiales S y el voto anticipado A quedan fuera: su sección de instalación "
               "no identifica la residencia del votante. Una extraordinaria E recibe CPV de la sección, "
               "sin perfil propio de su área de atención verificado. La etiqueta E1C1, E1C2… "
               "se recupera del JSON del propio IEEQ; el encarte aporta la localidad de instalación. "
               "Reparto de marcas de coalición en "
               "fracciones iguales: atribución analítica, no cómputo oficial por partido.")

    perfil = perfil_cpv(base, max_frases=3)
    st.markdown("#### ¿Por qué aparecen estos patrones?")
    st.caption("Las clases comparan el liderazgo del partido entre siete partidos atribuidos en cada casilla; "
               "no la victoria de la candidatura de coalición. Victoria sólida: ≥10 puntos; derrota "
               "competitiva: hasta 10 puntos de desventaja. Los umbrales son exploratorios.")
    if perfil["frases"]:
        for frase in perfil["frases"][:5]:
            st.write(frase)
    else:
        st.info("No hay suficientes secciones comparables para contrastar clases.")
    st.caption("Cada sección cuenta una vez por clase aunque tenga varias casillas. "
               f"{perfil['n_secciones_en_varias_clases']} contribuciones adicionales pertenecen a secciones "
               "que tienen casillas en más de una clase. Son asociaciones ecológicas descriptivas.")

    st.markdown("#### Esfuerzo a explorar")
    st.caption("La propuesta usa votos observados, abstención y distancia al liderazgo entre partidos. "
               "El apoyo mínimo es el menor porcentaje del partido en tres boletas federales de 2024 "
               "de la misma sección; no mide fidelidad de personas. Es una hipótesis de campaña; "
               "ni la abstención ni el costo supuesto equivalen a votos captables.")
    costo_texto = st.text_input("Costo supuesto por voto adicional (opcional, MXN)", value="",
                               key="casillas_costo")
    if costo_texto.strip():
        try:
            base = costo_hipotetico(base, float(costo_texto.replace(",", ".")))
        except ValueError:
            st.warning("Ingresa un costo numérico mayor o igual a cero.")
            base["COSTO_HIPOTETICO"] = float("nan")
    else:
        base["COSTO_HIPOTETICO"] = float("nan")
    vista = base[["ID_SECCION", "CASILLA_ETIQUETA", "LOCALIDAD_INSTALACION", "FILA_FUENTE", "CLASE", "VOTOS_PARTIDO",
                  "RIVAL", "VOTOS_RIVAL", "MARGEN_PP", "VOTOS_PARA_LIDERAR", "ABSTENCION",
                  "ALCANZABLE_ABSTENCION", "VOTOS_SOBRE_LISTA", "APOYO_MINIMO_FEDERAL_2024_PCT", "COSTO_HIPOTETICO",
                  "CPV_COMPARABLE", "ACCION_HIPOTESIS"]].rename(columns={
        "ID_SECCION": "Sección", "CASILLA_ETIQUETA": "Casilla",
        "LOCALIDAD_INSTALACION": "Localidad de instalación", "FILA_FUENTE": "Fila IEEQ",
        "CLASE": "Clase", "VOTOS_PARTIDO": "Votos partido", "RIVAL": "Rival",
        "VOTOS_RIVAL": "Votos rival", "MARGEN_PP": "Margen (pp)",
        "VOTOS_PARA_LIDERAR": "Votos para liderar", "ABSTENCION": "Abstención",
        "ALCANZABLE_ABSTENCION": "Faltante ≤ abstención", "CPV_COMPARABLE": "CPV comparable",
        "VOTOS_SOBRE_LISTA": "Votos sobre lista",
        "APOYO_MINIMO_FEDERAL_2024_PCT": "Apoyo mínimo federal 2024 (%)",
        "COSTO_HIPOTETICO": "Costo hipotético (MXN)",
        "ACCION_HIPOTESIS": "Esfuerzo a probar",
    })
    st.dataframe(vista, hide_index=True, width="stretch",
                 alt="Diagnóstico por casilla, margen de partido, abstención y esfuerzo hipotético")
    with st.expander("Avanzado · las 15 variables y cobertura", on_change="rerun") as avanzado:
        if avanzado.open:
            st.dataframe(perfil["tabla"], hide_index=True, width="stretch",
                         alt="Medias CPV y diferencias estandarizadas por clase de casilla")
            st.write("Casillas sin CPV comparable por clase:", cub["sin_cpv_por_clase"])
            st.caption("Las diferencias estandarizadas describen contraste entre clases, sin p-valores. "
                       "Las 165 secciones con perímetro no comparable se mantienen en la tabla de casillas "
                       "para diagnóstico electoral, pero se excluyen del perfil CPV.")
