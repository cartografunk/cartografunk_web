"""Genera perfiles de secciones CPV 2020 y los cruza con votos 2024."""

from __future__ import annotations

import json

import pandas as pd
import numpy as np
import sklearn
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from electoral.cpv import ETIQUETAS
from electoral.perfilamiento_cpv import agrupar_cpv
from scripts.benchmark_ieeq_ml_cpv import CPV, DATA


def run() -> dict:
    cross = pd.read_parquet(DATA / "crosswalk_qro_2018_2021_2024_referencias.parquet")
    ids = pd.Index(cross.loc[cross.CATEGORIA.eq("sin_cambio_cartografico_referencia"), "ID_SECCION"])
    cpv = pd.read_parquet(CPV)
    asignacion, reporte = agrupar_cpv(cpv, ids)
    tasas = cpv.set_index("ID_SECCION").loc[asignacion.ID_SECCION, list(ETIQUETAS)]
    x = np.clip(StandardScaler().fit_transform(
        SimpleImputer(strategy="median").fit_transform(tasas)), -3, 3)
    labels = {k: KMeans(n_clusters=k, n_init=20, random_state=0).fit_predict(x)
              for k in range(4, 8)}
    seeds = [KMeans(n_clusters=4, n_init=20, random_state=s).fit_predict(x)
             for s in (1, 2)]
    reporte["estabilidad"] = {
        "silhouette_k_4_a_7": {str(k): float(silhouette_score(x, lab))
                                 for k, lab in labels.items()},
        "ari_k4_semilla_0_vs_1": float(adjusted_rand_score(labels[4], seeds[0])),
        "ari_k4_semilla_0_vs_2": float(adjusted_rand_score(labels[4], seeds[1])),
        "sklearn_version": sklearn.__version__,
    }
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
