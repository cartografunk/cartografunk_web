"""Los perfiles usan CPV seccional y las oportunidades exigen derrota cercana."""

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
    assert sum(v["secciones"] for v in reporte["perfiles"].values()) == 5


def test_revisar_oportunidad_requiere_falso_liderazgo_y_derrota_cercana():
    perfil = pd.DataFrame({"ID_SECCION": ["22-0001", "22-0002", "22-0003"],
                           "PERFIL_CPV": [1, 1, 2]})
    pred = pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0002", "22-0003"],
        "PARTIDO": ["PAN"] * 3, "MODELO": ["hist_gradient_boosting_cpv"] * 3,
        "CUOTA_OBSERVADA_PCT": [40.0, 20.0, 55.0],
        "MARGEN_OBSERVADO_PP": [-3.0, -12.0, 6.0],
        "MARGEN_PREDICHO_PP": [2.0, 4.0, 5.0],
    })
    summary, detail = resumir_partido(perfil, pred, "PAN")
    assert detail.REVISAR_OPORTUNIDAD.tolist() == [True, False, False]
    assert summary.revisar_oportunidad.sum() == 1
    with pytest.raises(ValueError, match="Faltan predicciones"):
        resumir_partido(perfil, pred.iloc[:2], "PAN")
