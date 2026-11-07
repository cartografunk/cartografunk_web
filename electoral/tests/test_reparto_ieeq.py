"""Controles del reparto analítico y del universo del benchmark local."""

import pandas as pd
import pytest

from electoral.reparto_ieeq import COMBINACIONES, INDEPENDIENTES, PROPIOS, atribuir_partidos
from scripts.benchmark_ieeq_partidos import margen


def _fila_2024() -> pd.DataFrame:
    fila = {col: 0 for col in (*PROPIOS[2024], *COMBINACIONES[2024], *INDEPENDIENTES[2024])}
    fila.update(ID_SECCION="22-0001", PAN=7, PRI=2, **{"PAN-PRI": 3},
                NO_REGISTRADAS=1, NULOS=2, TOTAL_VOTOS=15, LISTA_NOMINAL=20)
    return pd.DataFrame([fila])


def test_reparto_conserva_tres_votos_y_no_inventa_redondeo_seccional():
    resultado = atribuir_partidos(_fila_2024(), 2024).iloc[0]
    assert resultado.PAN == 8.5
    assert resultado.PRI == 3.5
    assert resultado.VOTOS_VALIDOS == 12
    assert resultado.TOTAL_VOTOS == 15


def test_reparto_rechaza_total_inconsistente():
    fila = _fila_2024()
    fila.loc[0, "TOTAL_VOTOS"] = 16
    with pytest.raises(ValueError, match="no cuadran"):
        atribuir_partidos(fila, 2024)


def test_margen_firmado_compara_cada_partido_con_su_mejor_rival():
    import numpy as np

    resultado = margen(np.array([[40.0, 35.0, 25.0]]))
    assert resultado.tolist() == [[5.0, -5.0, -15.0]]
