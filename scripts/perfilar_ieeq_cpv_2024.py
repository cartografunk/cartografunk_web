"""Genera perfiles de secciones CPV 2020 y los cruza con votos 2024."""

from __future__ import annotations

import json

import pandas as pd

from electoral.perfilamiento_cpv import agrupar_cpv
from scripts.benchmark_ieeq_ml_cpv import CPV, DATA


def run() -> dict:
    cross = pd.read_parquet(DATA / "crosswalk_qro_2018_2021_2024_referencias.parquet")
    ids = pd.Index(cross.loc[cross.CATEGORIA.eq("sin_cambio_cartografico_referencia"), "ID_SECCION"])
    cpv = pd.read_parquet(CPV)
    asignacion, reporte = agrupar_cpv(cpv, ids)
    asignacion.to_parquet(DATA / "perfilamiento_cpv_2024_seccion.parquet", index=False)
    (DATA / "perfilamiento_cpv_2024.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return reporte


if __name__ == "__main__":
    report = run()
    print(json.dumps({"secciones_con_perfil": report["secciones_con_perfil"],
                      "secciones_sin_tasas_cpv": report["secciones_sin_tasas_cpv"],
                      "tamanos": {k: v["secciones"] for k, v in report["perfiles"].items()}},
                     ensure_ascii=False, indent=2))
