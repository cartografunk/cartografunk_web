"""Evalúa el benchmark 2024 sobre grupos 2021↔2024 sin repartir votos.

Comparación exploratoria posterior al benchmark sellado por sección. Usa el
mismo entrenamiento 2018→2021 y deja 2024 sólo como evaluación.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.benchmark_ieeq_partidos import DATA, P, features, margen, matriz, pct, ridge_predict


def matriz_grupos(path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path).set_index("ID_GRUPO_2021_2024")
    for partido in P:
        x[f"pct_{partido}"] = 100 * x[partido] / x.VOTOS_VALIDOS.replace(0, np.nan)
    x["participacion"] = x.TOTAL_VOTOS / x.LISTA_NOMINAL.replace(0, np.nan)
    return x


def run(data: Path = DATA) -> dict:
    d18, d21 = matriz(2018), matriz(2021)
    cross = pd.read_parquet(data / "crosswalk_qro_2018_2021_2024_referencias.parquet")
    ids_train = pd.Index(cross.loc[cross.ESTABLE_EN_AMBAS_REFERENCIAS, "ID_SECCION"])
    g21 = matriz_grupos(data / "dip_local_mr_2021_agrupado_2021_2024.parquet")
    g24 = matriz_grupos(data / "dip_local_mr_2024_agrupado_2021_2024.parquet")
    if set(g21.index) != set(g24.index):
        raise ValueError("Los grupos no tienen ambos años")
    g24 = g24.loc[g21.index]
    train_x, train_y = pct(d18.loc[ids_train]), pct(d21.loc[ids_train])
    eval_x, eval_y = pct(g21), pct(g24)
    fx_train = np.column_stack((train_x, features(d18.loc[ids_train])))
    fx_eval = np.column_stack((eval_x, features(g21)))
    if not np.isfinite(np.concatenate((fx_train.ravel(), fx_eval.ravel(), train_y.ravel(), eval_y.ravel()))).all():
        raise ValueError("Hay tasas no finitas en grupos")
    predicciones = {"persistencia": eval_x,
                    "ridge": ridge_predict(fx_train, train_y, fx_eval)}
    observ_margen = margen(eval_y)
    filas, resultados = [], {}
    for modelo, estimado in predicciones.items():
        pred_margen = margen(estimado)
        resultados[modelo] = {
            "mae_cuota_macro_pp": float(np.mean(np.abs(estimado - eval_y))),
            "mae_margen_macro_pp": float(np.mean(np.abs(pred_margen - observ_margen))),
            "por_partido": {},
        }
        for j, partido in enumerate(P):
            observed_leads = observ_margen[:, j] > 0
            predicted_leads = pred_margen[:, j] > 0
            resultados[modelo]["por_partido"][partido] = {
                "mae_cuota_pp": float(np.mean(np.abs(estimado[:, j] - eval_y[:, j]))),
                "lideres_observados_grupos": int(observed_leads.sum()),
                "lideres_detectados_grupos": int((observed_leads & predicted_leads).sum()),
                "falsos_lideres_grupos": int((~observed_leads & predicted_leads).sum()),
            }
            filas.extend({"ID_GRUPO_2021_2024": group, "PARTIDO": partido,
                         "MODELO": modelo, "CUOTA_2021_PCT": float(eval_x[i, j]),
                         "CUOTA_2024_OBSERVADA_PCT": float(eval_y[i, j]),
                         "CUOTA_2024_ESTIMADA_PCT": float(estimado[i, j]),
                         "MARGEN_2024_OBSERVADO_PP": float(observ_margen[i, j]),
                         "MARGEN_2024_ESTIMADO_PP": float(pred_margen[i, j])}
                        for i, group in enumerate(g21.index))
    result = {
        "grupos": len(g21),
        "lista_nominal_2024": int(g24.LISTA_NOMINAL.sum()),
        "entrenamiento_secciones": len(ids_train),
        "resultados": resultados,
        "nota": "Ensayo retrospectivo a escala de grupo seccional; los 33 grupos reconfigurados no producen predicción por sección hija.",
    }
    (data / "benchmark_partidos_grupos_2024.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(filas).to_parquet(data / "benchmark_partidos_grupos_2024.parquet", index=False)
    return result


if __name__ == "__main__":
    report = run()
    print(json.dumps({"grupos": report["grupos"], "lista_nominal_2024": report["lista_nominal_2024"],
                      "mae": {k: v["mae_cuota_macro_pp"] for k, v in report["resultados"].items()},
                      "morena": {k: v["por_partido"]["MORENA"] for k, v in report["resultados"].items()}},
                     indent=2, ensure_ascii=False))
