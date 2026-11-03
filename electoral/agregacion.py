"""Agregados territoriales de resultados y rentabilidad electoral."""

import pandas as pd

from electoral.clasificacion import CLASES, Umbrales, clasificar
from electoral.rentabilidad import rentabilidad


CLAVES = {
    "distrito": ("ID_ESTADO", "ID_DISTRITO_FEDERAL"),
    "municipio": ("ID_ESTADO", "ID_MUNICIPIO", "MUNICIPIO"),
    "estado": ("ID_ESTADO",),
}


def agregar(
    df: pd.DataFrame,
    nivel: str,
    candidaturas: list[str] | tuple[str, ...],
    evaluar: str,
    umbrales: Umbrales = Umbrales(),
) -> pd.DataFrame:
    """Suma secciones terrestres y recalcula el ranking sobre cada suma."""
    if nivel not in CLAVES:
        raise ValueError(f"Nivel desconocido: {nivel}")
    claves = list(CLAVES[nivel])
    candidaturas = list(candidaturas)
    territoriales = df.loc[df["estado"].ne("extranjero")]
    con_resultado = territoriales.loc[territoriales["estado"].eq("con_resultado")]

    grupos = territoriales.groupby(claves, dropna=False, sort=True)
    conteos = grupos["estado"].agg(
        n_secciones="size",
        n_con_resultado=lambda s: s.eq("con_resultado").sum(),
        n_sin_resultado=lambda s: s.eq("sin_resultado").sum(),
    ).reset_index()

    sumables = [*candidaturas, "NUM_VOTOS_VALIDOS", "TOTAL_VOTOS", "LISTA_NOMINAL"]
    sumables = list(dict.fromkeys(sumables))
    votadas = con_resultado[claves + sumables].copy()
    for clase in CLASES:
        votadas[f"n_{clase}"] = con_resultado["clase"].eq(clase).astype("int64")
    votadas["votos_para_ganar_perdida_competitiva"] = con_resultado[
        "votos_para_ganar"
    ].where(con_resultado["clase"].eq("perdida_competitiva"), 0).fillna(0)
    votadas["n_votos_sobre_lista"] = con_resultado["votos_sobre_lista"].eq(True).fillna(False).astype("int64")
    columnas_suma = votadas.columns.difference(claves).tolist()
    sumas = votadas.groupby(claves, dropna=False, sort=True)[columnas_suma].sum().reset_index()

    agregado = conteos.merge(sumas, on=claves, how="left", validate="one_to_one")
    agregado[columnas_suma] = agregado[columnas_suma].fillna(0)
    for columna in [f"n_{clase}" for clase in CLASES] + ["n_votos_sobre_lista"]:
        agregado[columna] = agregado[columna].astype("int64")
    agregado["estado"] = "con_resultado"
    return clasificar(rentabilidad(agregado, candidaturas, evaluar), umbrales)
