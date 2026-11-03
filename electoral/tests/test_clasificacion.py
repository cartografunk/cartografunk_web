from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from electoral.clasificacion import CLASES, Umbrales, clasificar


@pytest.fixture
def secciones():
    return pd.DataFrame({
        "estado": ["con_resultado"] * 8 + ["extranjero"],
        "resultado": [
            "ganada", "ganada", "empate", "perdida", "perdida", "perdida", "ganada", "perdida", "perdida"
        ],
        "margen_pct": [15.0, 14.9, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        "faltante_pct": [np.nan, np.nan, 0.0, 4.9, 5.0, 15.0, np.nan, np.nan, 1.0],
        "abstencion": [10, 10, 10, 10, 10, 10, 10, 10, 10],
        "votos_sobre_lista": [False] * 9,
        "rescatable_vs_abst": [np.nan, np.nan, 0.1, 1.0, 1.1, 2.0, np.nan, 0.2, 0.1],
        "votos_para_ganar": [np.nan, np.nan, 1, 100, 101, 150, np.nan, 2, 1],
    })


def test_una_fila_por_clase_y_fronteras(secciones):
    r = clasificar(secciones)
    assert r.loc[:5, "clase"].tolist() == list(CLASES)
    assert r["clase"].cat.ordered
    assert r["clase"].cat.categories.tolist() == list(CLASES)
    assert r.loc[3, "alcanzable_por_abstencion"]
    assert not r.loc[4, "alcanzable_por_abstencion"]
    assert r.loc[3, "alcanzable_en_votos"]
    assert not r.loc[4, "alcanzable_en_votos"]
    assert r.loc[[6, 7, 8], "clase"].isna().all()


def test_no_muta_y_no_interpreta_abstencion_invalida(secciones):
    secciones.loc[3, "abstencion"] = 0
    secciones.loc[4, "votos_sobre_lista"] = True
    original = secciones.copy(deep=True)
    r = clasificar(secciones)
    pd.testing.assert_frame_equal(secciones, original)
    assert r.loc[[3, 4, 8], "alcanzable_por_abstencion"].isna().all()
    assert r.loc[8, ["clase", "alcanzable_en_votos"]].isna().all()


@pytest.mark.parametrize("cambios", [
    {"solida_pp": 0}, {"competitiva_pp": -1}, {"lejana_pp": 0},
    {"votos_alcanzables": 0}, {"competitiva_pp": 16, "lejana_pp": 15},
])
def test_umbrales_invalidos(cambios):
    with pytest.raises(ValueError):
        Umbrales(**cambios)


def test_umbrales_inmutables():
    with pytest.raises(FrozenInstanceError):
        Umbrales().solida_pp = 10
