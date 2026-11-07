"""Benchmark retrospectivo exploratorio IEEQ por partido y sección.

Protocolo sellado: docs/electoral/PROTOCOLO_RETROSPECTIVO_QRO_2024_V1_2.md.
No usa CPV 2020 ni resultados 2024 para ajustar los modelos.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from electoral.reparto_ieeq import COMBINACIONES, PARTIDOS_COMUNES, PROPIOS, atribuir_partidos


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/electoral/ieeq_local"
P = PARTIDOS_COMUNES


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matriz(anio: int) -> pd.DataFrame:
    raw = pd.read_parquet(DATA / f"dip_local_mr_{anio}_seccion_bce.parquet")
    rep = atribuir_partidos(raw, anio)
    if rep.ID_SECCION.duplicated().any():
        raise ValueError(f"ID_SECCION duplicado en {anio}")
    for partido in PROPIOS[anio]:
        rep[f"pct_{partido}"] = 100 * rep[partido] / rep.VOTOS_VALIDOS.replace(0, np.nan)
    rep["participacion"] = rep.TOTAL_VOTOS / rep.LISTA_NOMINAL.replace(0, np.nan)
    return rep.set_index("ID_SECCION")


def margen(cuotas: np.ndarray) -> np.ndarray:
    """Margen por partido contra el mayor de los otros seis partidos comunes."""
    n, m = cuotas.shape
    resultado = np.empty((n, m))
    for j in range(m):
        resultado[:, j] = cuotas[:, j] - np.max(np.delete(cuotas, j, axis=1), axis=1)
    return resultado


def features(frame: pd.DataFrame) -> np.ndarray:
    return np.column_stack((frame["participacion"].to_numpy(float),
                            np.log1p(frame["LISTA_NOMINAL"].to_numpy(float))))


def ridge_predict(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray) -> np.ndarray:
    pred = np.zeros((len(test_x), len(P)))
    for j in range(len(P)):
        model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
        model.fit(np.column_stack((train_x[:, j], train_x[:, -2:])), train_y[:, j])
        pred[:, j] = model.predict(np.column_stack((test_x[:, j], test_x[:, -2:])))
    return np.clip(pred, 0, 100)


def pct(frame: pd.DataFrame) -> np.ndarray:
    return frame[[f"pct_{p}" for p in P]].to_numpy(float)


def cobertura(ids: pd.Index, nominal: pd.Series, total_n: int, total_nominal: float) -> dict:
    return {"secciones": int(len(ids)), "cobertura_secciones_pct": float(100 * len(ids) / total_n),
            "lista_nominal": int(nominal.loc[ids].sum()),
            "cobertura_lista_nominal_pct": float(100 * nominal.loc[ids].sum() / total_nominal)}


def run() -> dict:
    d18, d21, d24 = (matriz(y) for y in (2018, 2021, 2024))
    cross = pd.read_parquet(DATA / "crosswalk_qro_2018_2021_2024_referencias.parquet").set_index("ID_SECCION")
    expected = set(d24.index)
    if set(cross.index) != expected:
        raise ValueError("Universo 2024 diferente del crosswalk sellado")
    ids_eval = cross.index[cross.CATEGORIA.eq("sin_cambio_cartografico_referencia")]
    ids_train = cross.index[cross.ESTABLE_EN_AMBAS_REFERENCIAS]
    if len(ids_eval) != 788 or len(ids_train) != 654:
        raise ValueError("Cobertura distinta del protocolo")
    if not set(ids_eval).issubset(d21.index) or not set(ids_train).issubset(d18.index):
        raise ValueError("Faltan secciones históricas")
    total_n, total_nominal = len(d24), d24.LISTA_NOMINAL.sum()
    base_cov = cobertura(ids_eval, d24.LISTA_NOMINAL, total_n, total_nominal)

    # Distrito de 2018 es sólo grupo de validación; no aparece en las salidas.
    cas18 = pd.read_parquet(DATA / "dip_local_mr_2018_casilla.parquet")
    cas18 = cas18.loc[cas18.TIPO_NORMALIZADO.isin(("B", "C", "E"))]
    distritos = cas18.groupby("ID_SECCION").ID_DISTRITO_LOCAL.first().reindex(ids_train)
    if distritos.isna().any():
        raise ValueError("Falta distrito de entrenamiento")

    x18, y21 = pct(d18.loc[ids_train]), pct(d21.loc[ids_train])
    x21, y24 = pct(d21.loc[ids_eval]), pct(d24.loc[ids_eval])
    fx18 = np.column_stack((x18, features(d18.loc[ids_train])))
    fx21 = np.column_stack((x21, features(d21.loc[ids_eval])))
    if not np.isfinite(np.concatenate((fx18.ravel(), fx21.ravel(), y21.ravel(), y24.ravel()))).all():
        raise ValueError("Datos no finitos en universo comparable")

    pred = {
        "persistencia": x21.copy(),
        "media_2021": np.tile(y21.mean(axis=0), (len(ids_eval), 1)),
        "swing_2018_2021": np.clip(x21 + (y21 - x18).mean(axis=0), 0, 100),
        "ridge": ridge_predict(fx18, y21, fx21),
    }
    # Residuales de entrenamiento; Ridge usa predicción fuera de distrito.
    oof = np.full_like(y21, np.nan)
    folds = GroupKFold(n_splits=5)
    for fit, test in folds.split(fx18, y21, groups=distritos.to_numpy()):
        oof[test] = ridge_predict(fx18[fit], y21[fit], fx18[test])
    if np.isnan(oof).any():
        raise ValueError("Folds incompletos")
    q = {
        "persistencia": np.quantile(np.abs(margen(y21) - margen(x18)), .90, axis=0),
        "ridge": np.quantile(np.abs(margen(y21) - margen(oof)), .90, axis=0),
    }
    observ_margen = margen(y24)
    report = {
        "protocolo_v1_2_sha256": sha(ROOT / "docs/electoral/PROTOCOLO_RETROSPECTIVO_QRO_2024_V1_2.md"),
        "mapa_columnas": {str(y): {k: list(v) for k, v in COMBINACIONES[y].items()} for y in (2018, 2021, 2024)},
        "universo": {"total_secciones": total_n, "total_lista_nominal": int(total_nominal),
                     "comparable": base_cov,
                     "territorialmente_modificadas": cobertura(cross.index.difference(ids_eval), d24.LISTA_NOMINAL, total_n, total_nominal),
                     "entrenamiento_cadena": int(len(ids_train))},
        "resultados": {},
        "advertencias": ["Evaluación retrospectiva exploratoria, no pronóstico validado.",
                          "El reparto seccional fraccionario no asigna sobrantes enteros a secciones.",
                          "Liderazgo evaluado entre siete partidos con serie completa, no victoria de candidatura.",
                          "Los residuos 2018→2021 pueden no calibrar 2021→2024."]}
    otros_2024 = [p for p in PROPIOS[2024] if p not in P]
    max_otro = d24.loc[ids_eval, [f"pct_{p}" for p in otros_2024]].max(axis=1).to_numpy()
    report["universo"]["secciones_lideradas_por_partido_sin_serie"] = int(
        (max_otro > y24.max(axis=1)).sum())
    report["universo"]["sin_dato_en_siete_partidos"] = 0
    judiciales = {"22-0518", "22-0536", "22-0727", "22-0882", "22-0885"}
    mask_cadena = np.asarray(ids_eval.isin(ids_train))
    mask_sin_judiciales = np.asarray(~ids_eval.isin(judiciales))
    filas = []
    for nombre, valores in pred.items():
        mae = np.mean(np.abs(valores - y24), axis=0)
        pred_margen = margen(valores)
        mae_margen = np.mean(np.abs(pred_margen - observ_margen), axis=0)
        result = {"cobertura_base": base_cov, "mae_pct_macro": float(mae.mean()),
                  "mae_margen_pp_macro": float(mae_margen.mean()),
                  "sensibilidad_cadena_654": {
                      "cobertura": cobertura(ids_eval[mask_cadena], d24.LISTA_NOMINAL, total_n, total_nominal),
                      "mae_pct_macro": float(np.abs(valores[mask_cadena] - y24[mask_cadena]).mean(axis=0).mean())},
                  "sensibilidad_sin_cinco_secciones_judiciales": {
                      "cobertura": cobertura(ids_eval[mask_sin_judiciales], d24.LISTA_NOMINAL, total_n, total_nominal),
                      "mae_pct_macro": float(np.abs(valores[mask_sin_judiciales] - y24[mask_sin_judiciales]).mean(axis=0).mean())},
                  "por_partido": {p: {"mae_pct": float(mae[j]), "mae_margen_pp": float(mae_margen[j])}
                                   for j, p in enumerate(P)}}
        if nombre in q:
            for j, party in enumerate(P):
                lo = pred_margen[:, j] - q[nombre][j]
                hi = pred_margen[:, j] + q[nombre][j]
                decide = (lo > 0) | (hi < 0)
                acertado = np.sign(pred_margen[decide, j]) == np.sign(observ_margen[decide, j])
                pred_lidera = lo > 0
                acierto_positivos = observ_margen[pred_lidera, j] > 0
                verdaderos_lideres = observ_margen[:, j] > 0
                verdaderos_positivos = int((pred_lidera & verdaderos_lideres).sum())
                c = cobertura(ids_eval[decide], d24.LISTA_NOMINAL, total_n, total_nominal)
                result["por_partido"][party].update({
                    "intervalo_90_semianchura_pp": float(q[nombre][j]),
                    "cobertura_empirica_intervalo_pct": float(100 * np.mean((observ_margen[:, j] >= lo) & (observ_margen[:, j] <= hi))),
                    "liderazgo_emitido": c,
                    "abstencion_cruza_empate": int((~decide).sum()),
                    "acierto_entre_emitidos_pct": float(100 * acertado.mean()) if len(acertado) else None,
                    "predice_lidera": int(pred_lidera.sum()),
                    "precision_predice_lidera_pct": float(100 * acierto_positivos.mean()) if len(acierto_positivos) else None,
                    "lideres_observados": int(verdaderos_lideres.sum()),
                    "lideres_detectados": verdaderos_positivos,
                    "recall_liderazgo_pct": float(100 * verdaderos_positivos / verdaderos_lideres.sum()) if verdaderos_lideres.any() else None,
                    "predice_no_lidera": int((hi < 0).sum()),
                })
        report["resultados"][nombre] = result
        for i, section in enumerate(ids_eval):
            for j, party in enumerate(P):
                filas.append({"ID_SECCION": section, "PARTIDO": party, "MODELO": nombre,
                              "CUOTA_OBSERVADA_PCT": y24[i, j], "CUOTA_PREDICHA_PCT": valores[i, j],
                              "MARGEN_OBSERVADO_PP": observ_margen[i, j], "MARGEN_PREDICHO_PP": pred_margen[i, j]})
    report["estado"] = "calculado"
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "benchmark_partidos_2024.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(filas).to_parquet(DATA / "benchmark_partidos_2024_seccion.parquet", index=False)
    return report


if __name__ == "__main__":
    resultado = run()
    print(json.dumps({"universo": resultado["universo"],
                      "mae_macro": {k: v["mae_pct_macro"] for k, v in resultado["resultados"].items()}},
                     indent=2, ensure_ascii=False))
