"""Ensayo temporal por partido: 2018→2021 entrena, 2024 evalúa una sola vez.

Usa CPV 2020 a escala de sección sólo donde el crosswalk geométrico permite
comparar la sección. La salida es retrospectiva; no es un pronóstico futuro.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from scripts.benchmark_ieeq_partidos import DATA, P, features, margen, matriz, pct, ridge_predict


ROOT = Path(__file__).resolve().parents[1]
CPV = ROOT / "data/electoral/cpv_2020_seccion.parquet"
OUT_JSON = DATA / "benchmark_ml_cpv_2024.json"
OUT_PARQUET = DATA / "benchmark_ml_cpv_2024_seccion.parquet"


def tabla_features(previous: pd.DataFrame, cpv: pd.DataFrame) -> pd.DataFrame:
    """Alinea CPV por ID_SECCION; no permite duplicados ni llaves ausentes."""
    if previous.index.has_duplicates or cpv.ID_SECCION.duplicated().any():
        raise ValueError("ID_SECCION duplicado")
    if not previous.index.isin(cpv.ID_SECCION).all():
        raise ValueError("Falta clave CPV para al menos una sección de la muestra")
    rates = cpv.set_index("ID_SECCION").reindex(previous.index)
    shares = previous[[f"pct_{p}" for p in P]].rename(columns=lambda c: "prev_" + c)
    other = pd.DataFrame({
        "prev_participacion": previous.participacion,
        "prev_log_lista_nominal": np.log1p(previous.LISTA_NOMINAL),
    }, index=previous.index)
    result = pd.concat([shares, other, rates], axis=1)
    if not np.isfinite(result.iloc[:, :len(P) + 2].to_numpy(float)).all():
        raise ValueError("Historia electoral no finita")
    return result


def limitar_total(cuotas: np.ndarray) -> np.ndarray:
    """Las siete cuotas modeladas dejan sitio a partidos sin serie completa."""
    clipped = np.clip(cuotas, 0, 100)
    factor = np.maximum(clipped.sum(axis=1, keepdims=True) / 100, 1)
    return clipped / factor


def train_predict(train_x: pd.DataFrame, train_y: np.ndarray,
                  eval_x: pd.DataFrame, previous_train: np.ndarray | None = None,
                  previous_eval: np.ndarray | None = None) -> np.ndarray:
    if list(train_x.columns) != list(eval_x.columns):
        raise ValueError("Columnas de entrenamiento y evaluación distintas")
    if (previous_train is None) != (previous_eval is None):
        raise ValueError("La cuota previa debe existir en ambos años")
    change = previous_train is not None
    target = train_y - previous_train if change else train_y
    prediction = np.empty((len(eval_x), len(P)), dtype=float)
    for j in range(len(P)):
        model = HistGradientBoostingRegressor(
            max_iter=150, max_leaf_nodes=8, min_samples_leaf=30,
            learning_rate=0.05, l2_regularization=10.0, random_state=0,
        )
        model.fit(train_x, target[:, j])
        prediction[:, j] = model.predict(eval_x)
    if change:
        prediction += previous_eval
    return limitar_total(prediction)


def metrics(estimate: np.ndarray, actual: np.ndarray) -> dict:
    predicted_margin, actual_margin = margen(estimate), margen(actual)
    by_party = {}
    for j, party in enumerate(P):
        observed = actual_margin[:, j] > 0
        predicted = predicted_margin[:, j] > 0
        tp = int((observed & predicted).sum())
        fp = int((~observed & predicted).sum())
        by_party[party] = {
            "mae_cuota_pp": float(np.abs(estimate[:, j] - actual[:, j]).mean()),
            "sesgo_observado_menos_predicho_pp": float((actual[:, j] - estimate[:, j]).mean()),
            "lideres_observados": int(observed.sum()),
            "lideres_predichos": int(predicted.sum()),
            "lideres_detectados": tp,
            "falsos_lideres": fp,
            "precision_liderazgo_pct": float(100 * tp / (tp + fp)) if tp + fp else None,
            "recall_liderazgo_pct": float(100 * tp / observed.sum()) if observed.any() else None,
        }
    return {
        "mae_cuota_macro_pp": float(np.abs(estimate - actual).mean()),
        "mae_margen_macro_pp": float(np.abs(predicted_margin - actual_margin).mean()),
        "por_partido": by_party,
    }


def run() -> dict:
    d18, d21, d24 = (matriz(y) for y in (2018, 2021, 2024))
    cross = pd.read_parquet(DATA / "crosswalk_qro_2018_2021_2024_referencias.parquet")
    ids_train = pd.Index(cross.loc[cross.ESTABLE_EN_AMBAS_REFERENCIAS, "ID_SECCION"])
    ids_eval = pd.Index(cross.loc[cross.CATEGORIA.eq("sin_cambio_cartografico_referencia"), "ID_SECCION"])
    cpv = pd.read_parquet(CPV)
    prior18, observed21 = d18.loc[ids_train], pct(d21.loc[ids_train])
    prior21, observed24 = d21.loc[ids_eval], pct(d24.loc[ids_eval])
    train_x = tabla_features(prior18, cpv)
    eval_x = tabla_features(prior21, cpv)
    prior18_shares, prior21_shares = pct(prior18), pct(prior21)
    ridge_raw = ridge_predict(
            np.column_stack((pct(prior18), features(prior18))), observed21,
            np.column_stack((pct(prior21), features(prior21))),
        )
    models = {
        "persistencia": prior21_shares,
        "ridge_sin_cpv": limitar_total(ridge_raw),
        "hist_gradient_boosting_cpv": train_predict(train_x, observed21, eval_x),
        "hist_gradient_boosting_delta_cpv": train_predict(
            train_x, observed21, eval_x, prior18_shares, prior21_shares),
    }
    report = {
        "muestra": "Querétaro; secciones comparables, no resultados agregados por estado",
        "entrenamiento_2018_2021_secciones": len(ids_train),
        "evaluacion_2024_secciones": len(ids_eval),
        "evaluacion_2024_lista_nominal": int(d24.loc[ids_eval, "LISTA_NOMINAL"].sum()),
        "universo_2024_secciones": len(d24),
        "universo_2024_lista_nominal": int(d24.LISTA_NOMINAL.sum()),
        "variables_cpv": [c for c in cpv if c != "ID_SECCION"],
        "secciones_cpv_todas_las_tasas_nulas_entrenamiento": int(
            train_x[cpv.columns.drop("ID_SECCION")].isna().all(axis=1).sum()),
        "secciones_cpv_todas_las_tasas_nulas_evaluacion": int(
            eval_x[cpv.columns.drop("ID_SECCION")].isna().all(axis=1).sum()),
        "ajuste_cuotas": "Si la suma predicha de siete partidos excede 100 %, se reescala proporcionalmente a 100 %; el resto queda para otros partidos.",
        "ridge_filas_reescaladas": int((ridge_raw.sum(axis=1) > 100).sum()),
        "modelos": {name: metrics(pred, observed24) for name, pred in models.items()},
        "limites": [
            "Ensayo retrospectivo; 2024 se usó sólo para medir errores.",
            "CPV 2020 describe la sección, no a votantes individuales ni a casillas E.",
            "El reparto de combinaciones entre partidos es fraccionario y analítico.",
            "Liderazgo sólo entre siete partidos con serie completa, no victoria legal de candidatura.",
            "No hay porcentaje de confianza prospectiva ni validación en otras elecciones.",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = []
    for name, pred in models.items():
        pm, om = margen(pred), margen(observed24)
        rows.extend({
            "ID_SECCION": section, "PARTIDO": party, "MODELO": name,
            "CUOTA_PREDICHA_PCT": float(pred[i, j]),
            "CUOTA_OBSERVADA_PCT": float(observed24[i, j]),
            "MARGEN_PREDICHO_PP": float(pm[i, j]),
            "MARGEN_OBSERVADO_PP": float(om[i, j]),
        } for i, section in enumerate(ids_eval) for j, party in enumerate(P))
    pd.DataFrame(rows).to_parquet(OUT_PARQUET, index=False)
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps({"cobertura": result["evaluacion_2024_secciones"],
                      "mae": {k: v["mae_cuota_macro_pp"] for k, v in result["modelos"].items()},
                      "morena": {k: v["por_partido"]["MORENA"] for k, v in result["modelos"].items()}},
                     ensure_ascii=False, indent=2))
