"""Los perfiles usan CPV seccional y la cercanía se mide sin depender del ML."""

import pandas as pd
import pytest

from electoral.cpv import ETIQUETAS
from electoral.perfilamiento_cpv import agrupar_cpv, resumir_partido


def test_agrupar_cpv_excluye_seccion_sin_tasas_y_no_usa_votos():
    ids = pd.Index([f"22-{n:04d}" for n in range(1, 7)])
    cpv = pd.DataFrame({"ID_SECCION": ids[::-1]})
    for variable in ETIQUETAS:
        cpv[variable] = [None, 70.0, 65.0, 60.0, 20.0, 10.0]
    asignacion, reporte = agrupar_cpv(cpv, ids, n_perfiles=2)
    assert len(asignacion) == 5
    assert "22-0006" not in asignacion.ID_SECCION.tolist()
    assert reporte["secciones_sin_tasas_cpv"] == 1
    assert reporte["min_tasas_requeridas"] == 12
    assert sum(v["secciones"] for v in reporte["perfiles"].values()) == 5


def test_perfil_exige_doce_tasas():
    ids = pd.Index([f"22-{n:04d}" for n in range(1, 6)])
    cpv = pd.DataFrame({"ID_SECCION": ids})
    for i, variable in enumerate(ETIQUETAS):
        cpv[variable] = [float(j * 10 + i) for j in range(5)]
    cpv.loc[0, list(ETIQUETAS)[1:]] = None
    asignacion, reporte = agrupar_cpv(cpv, ids, n_perfiles=2)
    assert "22-0001" not in asignacion.ID_SECCION.tolist()
    assert reporte["secciones_excluidas_por_cpv_incompleto"] == 1


def test_derrota_cercana_incluye_menos_cinco_y_excluye_empate():
    perfil = pd.DataFrame({"ID_SECCION": ["22-0001", "22-0002", "22-0003", "22-0004"],
                           "PERFIL_CPV": [1, 1, 2, 2]})
    pred = pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0002", "22-0003", "22-0004"],
        "PARTIDO": ["PAN"] * 4, "MODELO": ["hist_gradient_boosting_cpv"] * 4,
        "CUOTA_OBSERVADA_PCT": [40.0, 20.0, 55.0, 40.0],
        "MARGEN_OBSERVADO_PP": [-5.0, -12.0, 6.0, 0.0],
        "MARGEN_PREDICHO_PP": [2.0, 4.0, 5.0, 3.0],
    })
    cand = pd.DataFrame({"ID_SECCION": perfil.ID_SECCION, "PARTIDO": ["PAN"] * 4,
                         "MARGEN_CANDIDATURA_PP": [3.0, -15.0, 10.0, 0.0]})
    summary, detail = resumir_partido(perfil, pred, "PAN", cand)
    assert detail.DERROTA_CERCANA.tolist() == [True, False, False, False]
    assert detail.CERCANA_Y_ML_PREDIJO_LIDERAZGO.tolist() == [True, False, False, False]
    assert summary.derrotas_cercanas.sum() == 1
    assert summary.candidatura_lidero.sum() == 1
    with pytest.raises(ValueError, match="Faltan predicciones"):
        resumir_partido(perfil, pred.iloc[:2], "PAN")
