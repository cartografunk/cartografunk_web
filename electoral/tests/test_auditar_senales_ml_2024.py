"""Las señales ML se contrastan con persistencia sobre el mismo universo."""

import pandas as pd

from electoral.reparto_ieeq import PARTIDOS_COMUNES
from scripts.auditar_senales_ml_2024 import comparar_senales_partidarias


def test_comparacion_cuenta_derrotas_cercanas_sin_orden_de_filas():
    filas = []
    for partido in PARTIDOS_COMUNES:
        for sec, observado, persistencia, ml in [
            ("22-0001", -5., 2., 3.), ("22-0002", 0., 2., 3.),
            ("22-0003", -6., 2., -1.),
        ]:
            for modelo, estimado in [("hist_gradient_boosting_cpv", ml),
                                     ("persistencia", persistencia)]:
                filas.append({"ID_SECCION": sec, "PARTIDO": partido, "MODELO": modelo,
                              "MARGEN_OBSERVADO_PP": observado,
                              "MARGEN_PREDICHO_PP": estimado})
    resultado = comparar_senales_partidarias(pd.DataFrame(filas[::-1]))
    assert len(resultado) == len(PARTIDOS_COMUNES)
    assert all(r["derrotas_partidarias_a_5_pp_o_menos"] == 1 for r in resultado)
    assert all(r["de_ellas_ambos"] == 1 for r in resultado)
