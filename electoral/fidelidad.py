"""Bloques base para medir voto consolidado por partido entre elecciones.

Este módulo NO fija la definición de "fidelidad". Calcula, por sección y
partido, el porcentaje de votos válidos de cada elección con el reparto de
coaliciones ``A_propios`` (partes iguales; el residuo entero va al integrante
con más votos propios) y resume su estabilidad entre elecciones. El umbral o
criterio que convierte estos números en "sección fiel" queda pendiente.
"""

from __future__ import annotations

import pandas as pd

from electoral.reparto import COALICIONES, repartir_coalicion

PARTIDOS = tuple(
    partido for grupo in COALICIONES.values() for partido in grupo["partidos"]
) + ("MC",)


def votos_por_partido(df: pd.DataFrame) -> pd.DataFrame:
    """Votos por partido y sección con coaliciones repartidas (A_propios).

    Solo filas ``con_resultado``; la llave ``ID_SECCION`` debe ser única.
    """
    d = df.loc[df["estado"].eq("con_resultado")]
    if d["ID_SECCION"].duplicated().any():
        raise ValueError("ID_SECCION duplicado entre filas con resultado")
    r = repartir_coalicion(d, "A_propios")
    salida = pd.DataFrame(index=r["ID_SECCION"].to_numpy())
    salida.index.name = "ID_SECCION"
    for partido in PARTIDOS:
        columna = "MC" if partido == "MC" else f"rep_{partido}"
        salida[partido] = r[columna].astype("int64").to_numpy()
    salida["VALIDOS"] = r["NUM_VOTOS_VALIDOS"].astype("int64").to_numpy()
    return salida


def porcentaje_por_partido(df: pd.DataFrame) -> pd.DataFrame:
    """Porcentaje de votos válidos por partido y sección (0-100)."""
    v = votos_por_partido(df)
    validos = v["VALIDOS"].where(v["VALIDOS"] > 0)
    return v[list(PARTIDOS)].div(validos, axis=0) * 100


def panel(elecciones: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Porcentajes en formato largo: ID_SECCION, partido, eleccion, pct, votos.

    Solo conserva secciones con resultado en todas las elecciones dadas.
    """
    if len(elecciones) < 2:
        raise ValueError("Se necesitan al menos dos elecciones")
    pcts = {n: porcentaje_por_partido(d) for n, d in elecciones.items()}
    votos = {n: votos_por_partido(d) for n, d in elecciones.items()}
    comunes = None
    for tabla in pcts.values():
        comunes = tabla.index if comunes is None else comunes.intersection(tabla.index)
    piezas = []
    for nombre in elecciones:
        p = pcts[nombre].loc[comunes].stack().rename("pct").reset_index()
        p.columns = ["ID_SECCION", "partido", "pct"]
        v = votos[nombre].loc[comunes, list(PARTIDOS)].stack().rename("votos").reset_index()
        v.columns = ["ID_SECCION", "partido", "votos"]
        p = p.merge(v, on=["ID_SECCION", "partido"])
        p["eleccion"] = nombre
        piezas.append(p)
    return pd.concat(piezas, ignore_index=True)


def estabilidad(largo: pd.DataFrame) -> pd.DataFrame:
    """Resumen por sección y partido entre elecciones.

    ``piso_pct`` y ``piso_votos`` son el mínimo observado entre elecciones: lo
    que el partido conserva en todas. ``rango_pp`` es máximo menos mínimo en
    puntos porcentuales. Son métricas candidatas, no una definición validada.
    """
    g = largo.groupby(["ID_SECCION", "partido"])
    salida = g["pct"].agg(
        media_pct="mean", desv_pct=lambda s: s.std(ddof=0), piso_pct="min", techo_pct="max"
    )
    salida["rango_pp"] = salida["techo_pct"] - salida["piso_pct"]
    salida["piso_votos"] = g["votos"].min()
    salida["n_elecciones"] = g["pct"].count()
    return salida.reset_index()
