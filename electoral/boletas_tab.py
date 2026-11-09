"""Explorador de boletas locales y federales conservadas por año y cargo."""

from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from electoral.dashboard_casillas import _cargar_puntos


@st.cache_data(max_entries=1)
def _datos(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = root / "data/electoral/ieeq_local"
    return (pd.read_parquet(base / "boletas_qro_2018_2024_seccion.parquet"),
            pd.read_parquet(base / "votos_opcion_qro_2018_2024_seccion.parquet"))


@st.cache_data(max_entries=1)
def _indice_casillas(root: Path) -> pd.DataFrame:
    return pd.read_parquet(root / "data/electoral/ieeq_local/boletas_qro_2018_2024_casilla.parquet",
                           columns=["ANIO", "CARGO", "ID_MUNICIPIO"])


def apoyo_minimo_directo(boletas: pd.DataFrame, votos: pd.DataFrame,
                         partido: str, municipio: int | None = None,
                         extras: pd.DataFrame | None = None) -> pd.DataFrame:
    """Mínimo de marca directa por partido entre boletas de 2024.

    Cada porcentaje usa los votos válidos de su propia boleta. Las marcas de
    coalición permanecen en otras opciones y no se imputan al partido.
    """
    b = boletas.loc[boletas.ANIO.eq(2024) & boletas.CARGO.isin(
        ("ayuntamiento", "senado"))].copy()
    if municipio is not None:
        b = b.loc[b.ID_MUNICIPIO.eq(municipio)]
    v = votos.loc[votos.ANIO.eq(2024) & votos.CARGO.isin(
        ("ayuntamiento", "senado"))].copy()
    if municipio is not None:
        v = v.loc[v.ID_MUNICIPIO.eq(municipio)]
    validos = v.groupby(["CARGO", "ID_SECCION"], as_index=False).VOTOS.sum().rename(
        columns={"VOTOS": "VOTOS_VALIDOS"})
    propio = v.loc[v.OPCION.eq(partido), ["CARGO", "ID_SECCION", "VOTOS"]]
    tasas = b[["CARGO", "ID_SECCION"]].merge(validos, on=["CARGO", "ID_SECCION"],
                                               validate="one_to_one")
    tasas = tasas.merge(propio, on=["CARGO", "ID_SECCION"], how="left",
                         validate="one_to_one")
    tasas["PCT"] = 100 * tasas.VOTOS / tasas.VOTOS_VALIDOS.where(tasas.VOTOS_VALIDOS.gt(0))
    if extras is not None and not extras.empty:
        otras = extras[["CARGO", "ID_SECCION", "VOTOS_VALIDOS", "VOTOS"]].copy()
        otras["PCT"] = 100 * otras.VOTOS / otras.VOTOS_VALIDOS.where(otras.VOTOS_VALIDOS.gt(0))
        tasas = pd.concat([tasas, otras], ignore_index=True)
    wide = tasas.pivot(index="ID_SECCION", columns="CARGO", values="PCT")
    wide.columns = [f"PCT_{c.upper()}" for c in wide.columns]
    wide = wide.reset_index()
    cols = list(wide.columns.drop("ID_SECCION"))
    if all(c in wide for c in cols):
        wide["APOYO_MINIMO_DIRECTO_PCT"] = wide[cols].min(axis=1, skipna=False)
        wide["RANGO_ENTRE_BOLETAS_PP"] = wide[cols].max(axis=1) - wide[cols].min(axis=1)
    return wide


@st.cache_data(max_entries=16)
def _otras_boletas_2024(root: Path, partido: str) -> pd.DataFrame:
    fuentes = {
        "presidencia": root / "data/electoral/presidencia_2024_seccion.parquet",
        "dip_federal": root / "data/electoral/diputaciones_2024_seccion.parquet",
        "dip_local": root / "data/electoral/ieeq_local/dip_local_mr_2024_seccion_bce.parquet",
    }
    filas = []
    for cargo, path in fuentes.items():
        if not path.exists():
            continue
        d = pd.read_parquet(path)
        if cargo == "dip_local":
            d = d.loc[d.ID_SECCION.str.startswith("22-")].copy()
            validos = d.TOTAL_VOTOS - d.NULOS - d.NO_REGISTRADAS
        else:
            d = d.loc[d.ID_ESTADO.eq(22) & d.SECCION.gt(0)].copy()
            validos = d.NUM_VOTOS_VALIDOS
        filas.append(pd.DataFrame({"CARGO": cargo, "ID_SECCION": d.ID_SECCION,
                                   "VOTOS_VALIDOS": validos, "VOTOS": d[partido]}))
    return pd.concat(filas, ignore_index=True) if filas else pd.DataFrame()


def _casillas_ayuntamiento_2024(root: Path, municipio: int, opcion: str) -> None:
    path = root / "data/electoral/ieeq_local/ayuntamiento_2024_casilla.parquet"
    if not path.exists():
        return
    cas = pd.read_parquet(path)
    cas = cas.loc[cas.ID_MUNICIPIO.eq(municipio)].reset_index(drop=True)
    if cas.empty or opcion not in cas:
        return
    st.markdown("#### Casillas de Ayuntamiento 2024")
    st.caption("Cada fila es una casilla B/C/E. Su punto es la sede de instalación 2024; "
               "el CPV pertenece a la sección. Selecciona una fila o un punto.")
    cas["VOTOS_OPCION"] = pd.to_numeric(cas[opcion], errors="coerce").fillna(0)
    puntos = _cargar_puntos(root / "data/electoral/ieeq_local/casillas_2024_puntos.parquet")
    mapa = cas[["ID_SECCION", "CASILLA_ETIQUETA", "VOTOS_OPCION"]].merge(
        puntos[["ID_SECCION", "CASILLA_ETIQUETA", "LATITUD", "LONGITUD"]],
        on=["ID_SECCION", "CASILLA_ETIQUETA"], how="inner", validate="one_to_one")
    seleccion = st.session_state.get("boletas_casilla_seleccionada")
    if seleccion and not ((cas.ID_SECCION.eq(seleccion[0])
                           & cas.CASILLA_ETIQUETA.eq(seleccion[1])).any()):
        seleccion = None
    punto = mapa.loc[mapa.ID_SECCION.eq(seleccion[0])
                     & mapa.CASILLA_ETIQUETA.eq(seleccion[1])] if seleccion else mapa.iloc[0:0]
    punto = punto.iloc[0] if len(punto) else None
    col_mapa, col_tabla = st.columns([1.2, 1], gap="medium")
    with col_mapa:
        if mapa.empty:
            st.info("No hay sedes puntuales para estas casillas; conserva la tabla por casilla.")
        else:
            capas = [pdk.Layer("ScatterplotLayer", id="casillas", data=mapa.to_dict("records"),
                               get_position="[LONGITUD, LATITUD]", get_radius=55,
                               radius_min_pixels=5, radius_max_pixels=13,
                               get_fill_color=[248, 170, 74, 210], pickable=True)]
            if punto is not None:
                capas.append(pdk.Layer("ScatterplotLayer", id="casilla_activa", pickable=False,
                                       data=[{"LATITUD": float(punto.LATITUD),
                                              "LONGITUD": float(punto.LONGITUD)}],
                                       get_position="[LONGITUD, LATITUD]", get_radius=105,
                                       radius_min_pixels=11, radius_max_pixels=19,
                                       get_fill_color=[255, 255, 255, 35],
                                       get_line_color=[255, 255, 255, 255],
                                       line_width_min_pixels=3, stroked=True))
            evento_mapa = st.pydeck_chart(
                pdk.Deck(layers=capas, map_style=None,
                         initial_view_state=pdk.ViewState(
                             latitude=float(punto.LATITUD) if punto is not None else 20.6,
                             longitude=float(punto.LONGITUD) if punto is not None else -100.4,
                             zoom=13.5 if punto is not None else 10),
                         tooltip={"text": "Sección {ID_SECCION} · casilla {CASILLA_ETIQUETA}\n"
                                          "Votos de opción: {VOTOS_OPCION}"}),
                height=420, on_select="rerun", selection_mode="single-object",
                key=f"boletas_mapa_{municipio}_{opcion}_{seleccion}",
                alt="Casillas de Ayuntamiento 2024; selecciona una para verla en la tabla")
            objetos = evento_mapa.selection.objects.get("casillas", [])
            if objetos:
                clave = (str(objetos[0]["ID_SECCION"]), str(objetos[0]["CASILLA_ETIQUETA"]))
                if clave != st.session_state.get("boletas_ultimo_click_mapa"):
                    st.session_state["boletas_ultimo_click_mapa"] = clave
                    st.session_state["boletas_casilla_seleccionada"] = clave
                    st.rerun()
    with col_tabla:
        tabla = cas[["ID_SECCION", "CASILLA_ETIQUETA", "VOTOS_OPCION", "TOTAL_VOTOS",
                     "LISTA_NOMINAL"]].copy()
        tabla.insert(0, "", ["●" if seleccion == (s, c) else "" for s, c in
                              zip(tabla.ID_SECCION, tabla.CASILLA_ETIQUETA)])
        evento_tabla = st.dataframe(tabla, hide_index=True, width="stretch", height=420,
                                    on_select="rerun", selection_mode="single-row",
                                    key=f"boletas_tabla_{municipio}_{opcion}",
                                    alt="Casillas; selecciona una para centrar el mapa")
        indices = evento_tabla.selection.rows
        if indices and 0 <= indices[0] < len(cas):
            fila = cas.iloc[indices[0]]
            clave = (str(fila.ID_SECCION), str(fila.CASILLA_ETIQUETA))
            if clave != st.session_state.get("boletas_ultimo_click_tabla"):
                st.session_state["boletas_ultimo_click_tabla"] = clave
                st.session_state["boletas_casilla_seleccionada"] = clave
                st.rerun()
    if seleccion:
        fila = cas.loc[cas.ID_SECCION.eq(seleccion[0])
                       & cas.CASILLA_ETIQUETA.eq(seleccion[1])]
        if len(fila):
            st.info(f"Sección {seleccion[0]} · casilla {seleccion[1]} · "
                    f"{int(fila.iloc[0].VOTOS_OPCION)} votos de {opcion}. "
                    + ("Sede marcada y mapa centrado." if punto is not None
                       else "Sin sede puntual cotejada; se conserva la clave de sección."))


def _casillas_historicas(root: Path, anio: int, cargo: str,
                         municipio: int | None, opcion: str) -> None:
    path = root / "data/electoral/ieeq_local/boletas_qro_2018_2024_casilla.parquet"
    if not path.exists():
        return
    cas = pd.read_parquet(path)
    cas = cas.loc[cas.ANIO.eq(anio) & cas.CARGO.eq(cargo)].copy()
    if municipio is not None:
        cas = cas.loc[cas.ID_MUNICIPIO.eq(municipio)]
    if cas.empty or opcion not in cas:
        return
    cas["VOTOS_OPCION"] = pd.to_numeric(cas[opcion], errors="coerce").fillna(0)
    st.markdown(f"#### Casillas de {cargo} {anio}")
    st.caption("La casilla sigue siendo la unidad de voto. Las sedes 2024 no se reutilizan "
               "como ubicación de casillas históricas: la dirección y el territorio pudieron cambiar.")
    tabla = cas[["ID_SECCION", "CASILLA_ETIQUETA", "VOTOS_OPCION", "TOTAL_VOTOS",
                 "LISTA_NOMINAL"]].reset_index(drop=True)
    evento = st.dataframe(tabla, hide_index=True, width="stretch", height=420,
                          on_select="rerun", selection_mode="single-row",
                          key=f"boletas_historicas_{anio}_{cargo}_{municipio}_{opcion}",
                          alt="Resultados por casilla de la elección histórica elegida")
    if evento.selection.rows:
        fila = tabla.iloc[evento.selection.rows[0]]
        st.info(f"Sección {fila.ID_SECCION} · casilla {fila.CASILLA_ETIQUETA} · "
                f"{int(fila.VOTOS_OPCION)} votos de {opcion}. "
                "Ubicación puntual histórica aún sin cotejar.")


def mostrar_explorador_boletas(root: Path) -> None:
    base = root / "data/electoral/ieeq_local"
    if not (base / "boletas_qro_2018_2024_seccion.parquet").exists():
        st.info("Falta construir el panel local: python scripts/build_ieeq_boletas.py")
        return
    boletas, votos = _datos(root)
    st.subheader("Boletas y antecedentes · Querétaro")
    st.write("Explora casillas por cargo y año. La sección enlaza el contexto territorial y el CPV; "
             "cada boleta conserva sus opciones de voto.")
    pares = sorted(set(zip(boletas.ANIO, boletas.CARGO)), reverse=True)
    control_eleccion, control_municipio, control_opcion = st.columns(3)
    with control_eleccion:
        anio, cargo = st.selectbox("Elección", pares,
                                   format_func=lambda p: f"{p[0]} · {p[1].capitalize()}",
                                   index=pares.index((2024, "ayuntamiento")),
                                   key="explorador_eleccion")
    b = boletas.loc[boletas.ANIO.eq(anio) & boletas.CARGO.eq(cargo)].copy()
    v = votos.loc[votos.ANIO.eq(anio) & votos.CARGO.eq(cargo)].copy()
    if cargo == "ayuntamiento":
        municipios = sorted(b.ID_MUNICIPIO.unique())
        with control_municipio:
            municipio = st.selectbox("Municipio de la boleta", municipios,
                                      index=municipios.index(14) if 14 in municipios else 0,
                                      format_func=lambda n: "Querétaro (14)" if n == 14 else f"Municipio {int(n)}",
                                      key="explorador_municipio")
        b = b.loc[b.ID_MUNICIPIO.eq(municipio)]
        v = v.loc[v.ID_MUNICIPIO.eq(municipio)]
    else:
        municipio = None
    opciones = sorted(v.OPCION.unique())
    with control_opcion:
        opcion = st.selectbox("Opción marcada en la boleta", opciones,
                              index=opciones.index("PAN") if "PAN" in opciones else 0,
                              key="explorador_opcion")
    validos = v.groupby("ID_SECCION", as_index=False).VOTOS.sum().rename(
        columns={"VOTOS": "VOTOS_VALIDOS"})
    elegido = v.loc[v.OPCION.eq(opcion), ["ID_SECCION", "VOTOS"]]
    vista = b.merge(validos, on="ID_SECCION", validate="one_to_one").merge(
        elegido, on="ID_SECCION", how="left", validate="one_to_one")
    vista["CUOTA_PCT"] = 100 * vista.VOTOS / vista.VOTOS_VALIDOS.where(vista.VOTOS_VALIDOS.gt(0))
    a, c, d = st.columns(3)
    if cargo in ("ayuntamiento", "gubernatura"):
        indice = _indice_casillas(root)
        mascara = indice.ANIO.eq(anio) & indice.CARGO.eq(cargo)
        if municipio is not None:
            mascara &= indice.ID_MUNICIPIO.eq(municipio)
        a.metric("Casillas", f"{int(mascara.sum()):,}", help=f"{len(vista):,} secciones")
    else:
        a.metric("Secciones", f"{len(vista):,}")
    c.metric("Votos de la opción", f"{int(vista.VOTOS.sum()):,}")
    d.metric("Cuota de la opción", f"{100 * vista.VOTOS.sum() / vista.VOTOS_VALIDOS.sum():.1f} %")
    st.caption("La opción puede ser partido, coalición o candidatura independiente. "
               "La cuota usa votos válidos de esta boleta, no lista nominal.")
    if anio == 2024 and opcion in ("PAN", "PRI", "PRD", "MC", "PVEM", "MORENA", "PT"):
        extras = _otras_boletas_2024(root, opcion)
        if municipio is not None:
            extras = extras.loc[extras.ID_SECCION.isin(vista.ID_SECCION)]
        piso = apoyo_minimo_directo(boletas, votos, opcion, municipio, extras)
        vista = vista.merge(piso, on="ID_SECCION", how="left", validate="one_to_one")
        con_piso = vista.APOYO_MINIMO_DIRECTO_PCT.notna()
        st.markdown("#### Apoyo mínimo observado al partido")
        st.write("El menor porcentaje de **marca directa al mismo partido** entre Ayuntamiento, "
                 "Senado, Presidencia y diputaciones federal y local de 2024, sección por sección. "
                 "Las combinaciones de "
                 "coalición se muestran por separado y no se reparten aquí.")
        x, y = st.columns(2)
        x.metric("Secciones con cinco boletas", f"{int(con_piso.sum()):,}/{len(vista):,}")
        y.metric("Mediana del mínimo", f"{vista.APOYO_MINIMO_DIRECTO_PCT.median():.1f} %")
        st.caption("Es un mínimo descriptivo entre elecciones, no identifica a las mismas personas "
                   "ni prueba que voten por el partido sin importar la candidatura.")
    columnas = ["ID_SECCION", "VOTOS", "CUOTA_PCT", "TOTAL_VOTOS", "LISTA_NOMINAL"]
    if "APOYO_MINIMO_DIRECTO_PCT" in vista:
        columnas += [c for c in vista if c.startswith("PCT_")]
        columnas += ["APOYO_MINIMO_DIRECTO_PCT"]
    if anio == 2024 and cargo == "ayuntamiento":
        _casillas_ayuntamiento_2024(root, municipio, opcion)
    elif cargo in ("ayuntamiento", "gubernatura"):
        _casillas_historicas(root, anio, cargo, municipio, opcion)
    with st.expander("Resumen por sección · Avanzado"):
        st.dataframe(vista[columnas], hide_index=True, width="stretch", height=460,
                     alt="Resultados por sección de la opción y la elección elegidas")
    st.caption("CPV 2020 se enlaza sólo para secciones 2024 con geometría comparable. "
               "El cotejo histórico 2018/2021→2024 requiere la correspondencia territorial; "
               "coincidir en número de sección no basta.")
