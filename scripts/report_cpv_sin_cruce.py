"""Audita secciones sin ECEG por estado y clase; escribe CSV documental."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from electoral.analisis_demo import analizar_candidatura  # noqa: E402

DATA = ROOT / "data" / "electoral"
SALIDA = ROOT / "docs" / "electoral" / "cpv_sin_cruce_por_estado_clase.csv"


def resumir(df: pd.DataFrame, tipo: str, eleccion: str, candidatura: str,
            claves: set[str]) -> pd.DataFrame:
    base = df[["ID_SECCION", "ID_ESTADO", "clase"]].copy()
    base["clase"] = base["clase"].astype("object").fillna("sin_clase")
    base["sin_cpv"] = ~base.ID_SECCION.isin(claves)
    tabla = base.groupby(["ID_ESTADO", "clase"], observed=True).agg(
        secciones=("ID_SECCION", "size"), sin_cpv=("sin_cpv", "sum")).reset_index()
    tabla["tipo"] = tipo
    tabla["eleccion"] = eleccion
    tabla["candidatura_o_partido"] = candidatura
    tabla["pct_sin_cpv"] = 100 * tabla.sin_cpv / tabla.secciones
    total_faltante = tabla.groupby("ID_ESTADO").sin_cpv.transform("sum")
    tasa_base = total_faltante / tabla.groupby("ID_ESTADO").secciones.transform("sum")
    tabla["pct_de_faltantes_estado"] = 100 * tabla.sin_cpv / total_faltante.where(total_faltante.gt(0))
    tabla["razon_tasa_vs_estado"] = (tabla.sin_cpv / tabla.secciones) / tasa_base.where(tasa_base.gt(0))
    return tabla


def construir() -> pd.DataFrame:
    claves = set(pd.read_parquet(DATA / "cpv_2020_seccion.parquet", columns=["ID_SECCION"]).ID_SECCION)
    piezas = []
    for eleccion in ("presidencia", "diputaciones", "senadurias"):
        df = pd.read_parquet(DATA / f"{eleccion}_2024_seccion.parquet")
        df = df.loc[df.estado.ne("extranjero")]
        candidaturas = [c for c in df if c.startswith("cand_") and df[c].notna().any()]
        for candidatura in candidaturas:
            res = analizar_candidatura(df, candidatura)
            piezas.append(resumir(res, "candidatura", eleccion, candidatura, claves))
    apoyo = pd.read_parquet(DATA / "fidelidad_estado.parquet",
                             columns=["ID_SECCION", "ID_ESTADO", "partido", "clase"])
    for partido, tabla in apoyo.groupby("partido", sort=True):
        piezas.append(resumir(tabla, "apoyo_minimo", "tres_boletas", partido, claves))
    salida = pd.concat(piezas, ignore_index=True)
    salida = salida[["tipo", "eleccion", "candidatura_o_partido", "ID_ESTADO", "clase",
                     "secciones", "sin_cpv", "pct_sin_cpv", "pct_de_faltantes_estado", "razon_tasa_vs_estado"]]
    salida.to_csv(SALIDA, index=False, encoding="utf-8-sig")
    return salida


if __name__ == "__main__":
    tabla = construir()
    print(f"{len(tabla)} filas en {SALIDA}")
    for (tipo, eleccion), grupo in tabla.groupby(["tipo", "eleccion"]):
        print(tipo, eleccion, "sin CPV:", int(grupo.sin_cpv.sum()),
              "clase de mayor tasa:", grupo.groupby("clase").apply(
                  lambda x: x.sin_cpv.sum() / x.secciones.sum(), include_groups=False
              ).idxmax())
