"""Perfiles CPV por sección y contraste electoral; asociación, no causa."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from electoral.cpv import ETIQUETAS


def agrupar_cpv(cpv: pd.DataFrame, ids: pd.Index, n_perfiles: int = 5) -> tuple[pd.DataFrame, dict]:
    """Forma grupos sólo con CPV, sin usar votos de ningún año."""
    columnas = list(ETIQUETAS)
    if cpv.ID_SECCION.duplicated().any() or ids.has_duplicates:
        raise ValueError("ID_SECCION duplicado")
    if not ids.isin(cpv.ID_SECCION).all():
        raise ValueError("Faltan claves CPV de la muestra")
    tasas = cpv.set_index("ID_SECCION").loc[ids, columnas].apply(pd.to_numeric, errors="coerce")
    disponible = tasas.notna().any(axis=1)
    tasas = tasas.loc[disponible]
    if len(tasas) < n_perfiles or n_perfiles < 2:
        raise ValueError("Muestra insuficiente para perfiles")
    matriz = SimpleImputer(strategy="median").fit_transform(tasas)
    z = StandardScaler().fit_transform(matriz)
    labels = KMeans(n_clusters=n_perfiles, n_init=20, random_state=0).fit_predict(np.clip(z, -3, 3))
    tamaños = pd.Series(labels).value_counts().sort_values(ascending=False)
    orden = {int(raw): rank for rank, raw in enumerate(tamaños.index, start=1)}
    asignacion = pd.DataFrame({"ID_SECCION": tasas.index,
                               "PERFIL_CPV": [orden[int(label)] for label in labels]})
    medias = tasas.assign(PERFIL_CPV=asignacion.PERFIL_CPV.to_numpy()).groupby("PERFIL_CPV").mean()
    global_mean = tasas.mean()
    global_std = tasas.std(ddof=0).replace(0, np.nan)
    perfiles = {}
    for profile, row in medias.iterrows():
        d = ((row - global_mean) / global_std).dropna()
        rasgos = []
        for variable in d.abs().nlargest(3).index:
            rasgos.append({"variable": variable, "etiqueta": ETIQUETAS[variable],
                           "direccion": "mayor" if d[variable] > 0 else "menor",
                           "desviacion_estandarizada": float(d[variable])})
        perfiles[str(profile)] = {"secciones": int((asignacion.PERFIL_CPV == profile).sum()),
                                 "rasgos": rasgos}
    return asignacion, {"perfiles": perfiles, "secciones_sin_tasas_cpv": int((~disponible).sum()),
                        "secciones_con_perfil": len(asignacion),
                        "nota": "K-means usa sólo 15 tasas CPV 2020; grupos descriptivos de secciones, no tipos de votante."}


def resumir_partido(asignacion: pd.DataFrame, predicciones: pd.DataFrame,
                    partido: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ubica derrotas cercanas y falsos liderazgos; no estima votos captables."""
    pred = predicciones.loc[
        predicciones.PARTIDO.eq(partido)
        & predicciones.MODELO.eq("hist_gradient_boosting_cpv"),
        ["ID_SECCION", "CUOTA_OBSERVADA_PCT", "MARGEN_OBSERVADO_PP", "MARGEN_PREDICHO_PP"],
    ]
    if pred.ID_SECCION.duplicated().any() or asignacion.ID_SECCION.duplicated().any():
        raise ValueError("ID_SECCION duplicado")
    base = asignacion.merge(pred, on="ID_SECCION", validate="one_to_one")
    if len(base) != len(asignacion):
        raise ValueError("Faltan predicciones para secciones perfiladas")
    base["DERROTA_CERCANA"] = base.MARGEN_OBSERVADO_PP.lt(0) & base.MARGEN_OBSERVADO_PP.ge(-5)
    base["FALSO_LIDERAZGO_ML"] = base.MARGEN_PREDICHO_PP.gt(0) & base.MARGEN_OBSERVADO_PP.le(0)
    base["REVISAR_OPORTUNIDAD"] = base.DERROTA_CERCANA & base.FALSO_LIDERAZGO_ML
    base["LIDERA_OBSERVADO"] = base.MARGEN_OBSERVADO_PP.gt(0)
    summary = base.groupby("PERFIL_CPV", as_index=False).agg(
        secciones=("ID_SECCION", "size"),
        cuota_observada_media_pct=("CUOTA_OBSERVADA_PCT", "mean"),
        lidera_observado=("LIDERA_OBSERVADO", "sum"),
        derrotas_cercanas=("DERROTA_CERCANA", "sum"),
        falsos_liderazgos_ml=("FALSO_LIDERAZGO_ML", "sum"),
        revisar_oportunidad=("REVISAR_OPORTUNIDAD", "sum"),
    )
    return summary, base
