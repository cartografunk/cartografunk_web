"""El diagnóstico conserva abstenciones y no decide fuera del universo comparable."""

import pandas as pd
import pytest

from electoral.diagnostico_forecast import diagnostico_secciones


def test_intervalo_y_seccion_modificada():
    informe = {"resultados": {"ridge": {"por_partido": {
        "MORENA": {"intervalo_90_semianchura_pp": 5.0}}}}}
    cruce = pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0002", "22-0003", "22-0004"],
        "CATEGORIA": ["sin_cambio_cartografico_referencia"] * 3 + ["dividida_o_reconfigurada"],
    })
    pred = pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0002", "22-0003"],
        "PARTIDO": ["MORENA"] * 3, "MODELO": ["ridge"] * 3,
        "CUOTA_OBSERVADA_PCT": [45., 30., 20.],
        "CUOTA_PREDICHA_PCT": [40., 30., 20.],
        "MARGEN_OBSERVADO_PP": [9., 0., -11.],
        "MARGEN_PREDICHO_PP": [6., 2., -6.],
    })
    out = diagnostico_secciones(informe, pred, cruce, "MORENA", "ridge")
    assert out.LECTURA.tolist() == [
        "Lidera entre siete partidos", "Indeterminado: intervalo cruza empate",
        "No lidera entre siete partidos", "Sin modelo: sección modificada",
    ]
    assert pd.isna(out.loc[3, "CUOTA_PREDICHA_PCT"])
    with pytest.raises(ValueError, match="cobertura"):
        diagnostico_secciones(informe, pred.iloc[:2], cruce, "MORENA", "ridge")
