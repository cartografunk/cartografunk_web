"""Compara tres tamaños de variables CPV en el mismo holdout de 2024.

Entrena 2018→2021 y evalúa 2021→2024 sobre secciones comparables.
Los campos ECEG completos son una exploración de amplitud, no variables elegidas
por utilidad electoral. No modifica el benchmark anterior.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.audit_eceg_cpv_qro import CANDIDATOS
from scripts.benchmark_ieeq_ml_cpv import metrics, tabla_features, train_predict
from scripts.benchmark_ieeq_partidos import DATA, matriz, pct


ROOT = Path(__file__).resolve().parents[1]
CPV = ROOT / "data/electoral/cpv_2020_seccion.parquet"
COMPLETO = ROOT / "data/electoral/eceg_2020_seccion.parquet"
SALIDA = DATA / "benchmark_ml_cpv_expandido_2024.json"
PREDICCIONES = DATA / "benchmark_ml_cpv_expandido_2024_seccion.parquet"
EXCLUIR = {"ID", "ENTIDAD", "DISTRITO", "MUNICIPIO", "SECCION", "TIPO"}


def preparar_fuentes(claves: set[str]) -> dict[str, pd.DataFrame]:
    tasas_15 = pd.read_parquet(CPV)
    eceg = pd.read_parquet(COMPLETO)
    eceg = eceg.loc[eceg.ID_SECCION.isin(claves)].copy()
    if eceg.ID_SECCION.duplicated().any() or set(eceg.ID_SECCION) != claves:
        raise ValueError("ECEG completo no cubre uno a uno el universo comparable")
    eceg = eceg.set_index("ID_SECCION")
    nuevas = pd.DataFrame(index=eceg.index)
    for columna, (_, denominador) in CANDIDATOS.items():
        tasa = 100 * eceg[columna] / eceg[denominador].where(eceg[denominador].gt(0))
        nuevas[f"nuevo_pct_{columna.lower()}"] = tasa.where(tasa.between(0, 100))
    campos = eceg.drop(columns=["ID_ENTIDAD", *EXCLUIR]).select_dtypes("number")
    campos = campos.rename(columns=lambda c: f"eceg_{c.lower()}")
    if campos.isna().all().any():
        campos = campos.drop(columns=campos.columns[campos.isna().all()])
    base = tasas_15.loc[tasas_15.ID_SECCION.isin(claves)].set_index("ID_SECCION")
    return {
        "15_tasas": base.reset_index(),
        "27_tasas": base.join(nuevas, validate="one_to_one").reset_index(),
        "todos_campos": base.join(nuevas, validate="one_to_one")
                            .join(campos, validate="one_to_one").reset_index(),
    }


def run() -> dict:
    d18, d21, d24 = (matriz(y) for y in (2018, 2021, 2024))
    cross = pd.read_parquet(DATA / "crosswalk_qro_2018_2021_2024_referencias.parquet")
    ids_train = pd.Index(cross.loc[cross.ESTABLE_EN_AMBAS_REFERENCIAS, "ID_SECCION"])
    ids_eval = pd.Index(cross.loc[cross.CATEGORIA.eq("sin_cambio_cartografico_referencia"), "ID_SECCION"])
    if len(ids_train) != 654 or len(ids_eval) != 788:
        raise ValueError("Universo distinto del benchmark anterior")
    fuentes = preparar_fuentes(set(ids_train) | set(ids_eval))
    previo18, previo21 = d18.loc[ids_train], d21.loc[ids_eval]
    observado21, observado24 = pct(d21.loc[ids_train]), pct(d24.loc[ids_eval])
    reporte = {
        "muestra": "Querétaro; resultados por sección comparable, no agregados por estado",
        "entrenamiento_secciones": len(ids_train),
        "evaluacion_secciones": len(ids_eval),
        "cobertura_lista_nominal_pct": float(
            100 * d24.loc[ids_eval, "LISTA_NOMINAL"].sum() / d24.LISTA_NOMINAL.sum()),
        "metodo": "HistGradientBoostingRegressor por partido; mismos parámetros y holdout en las tres corridas",
        "modelos": {},
        "limites": ["Ensayo retrospectivo 2024, no pronóstico de 2027.",
                    "Los campos ECEG crudos incluyen conteos y tasas; algunos son redundantes.",
                    "CPV seccional no describe votantes individuales ni el área propia de casillas E.",
                    "Atribución de coaliciones fraccionaria y analítica, no cómputo legal."],
    }
    filas = []
    for nombre, fuente in fuentes.items():
        train_x = tabla_features(previo18, fuente)
        eval_x = tabla_features(previo21, fuente)
        estimado = train_predict(train_x, observado21, eval_x)
        m = metrics(estimado, observado24)
        reporte["modelos"][nombre] = {
            "n_variables_cpv": len(fuente.columns) - 1,
            "variables_cpv": [c for c in fuente if c != "ID_SECCION"],
            **m,
        }
        for i, seccion in enumerate(ids_eval):
            for j, partido in enumerate(m["por_partido"]):
                filas.append({"ID_SECCION": seccion, "PARTIDO": partido,
                              "MODELO": nombre, "CUOTA_PREDICHA_PCT": float(estimado[i, j]),
                              "CUOTA_OBSERVADA_PCT": float(observado24[i, j])})
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(filas).to_parquet(PREDICCIONES, index=False)
    return reporte


if __name__ == "__main__":
    resultado = run()
    print(json.dumps({k: {"variables": v["n_variables_cpv"],
                           "mae_cuota_macro_pp": v["mae_cuota_macro_pp"],
                           "mae_margen_macro_pp": v["mae_margen_macro_pp"],
                           "lideres_detectados_morena": v["por_partido"]["MORENA"]["lideres_detectados"]}
                      for k, v in resultado["modelos"].items()}, ensure_ascii=False, indent=2))
