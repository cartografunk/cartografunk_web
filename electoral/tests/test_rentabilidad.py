import pandas as pd
import pytest

from electoral.rentabilidad import rentabilidad


CANDIDATURAS = ["coalicion", "oposicion", "tercera"]


@pytest.fixture
def secciones():
    return pd.DataFrame({
        "estado": ["con_resultado", "con_resultado", "con_resultado", "sin_resultado", "extranjero"],
        "coalicion": [10, 3, 7, 0, 10],
        "oposicion": [5, 9, 7, 0, 5],
        "tercera": [2, 2, 1, 0, 2],
        "NUM_VOTOS_VALIDOS": [20, 20, 20, 0, 20],
        "LISTA_NOMINAL": [25, 19, 20, 0, 25],
        "TOTAL_VOTOS": [15, 15, 20, 0, 15],
    })


def test_ganada_perdida_y_empate(secciones):
    r = rentabilidad(secciones, CANDIDATURAS, "coalicion")
    assert r.loc[:2, "resultado"].tolist() == ["ganada", "perdida", "empate"]
    assert r.loc[0, "margen_votos"] == 5
    assert r.loc[0, "margen_pct"] == 25
    assert pd.isna(r.loc[0, "faltante_votos"])
    assert r.loc[1, "faltante_votos"] == 6
    assert r.loc[1, "faltante_pct"] == 30
    assert r.loc[1, "votos_para_ganar"] == 7
    assert r.loc[1, "abstencion"] == 4
    assert r.loc[1, "rescatable_vs_abst"] == 7 / 4
    assert r.loc[2, "faltante_votos"] == 0
    assert r.loc[2, "votos_para_ganar"] == 1
    assert pd.isna(r.loc[2, "rescatable_vs_abst"])


def test_no_muta_entrada_y_excluye_filas_sin_resultado(secciones):
    original = secciones.copy(deep=True)
    r = rentabilidad(secciones, CANDIDATURAS, "coalicion")
    pd.testing.assert_frame_equal(secciones, original)
    nuevas = r.columns.difference(secciones.columns)
    assert r.loc[3:, nuevas].isna().all().all()


def test_votos_sobre_lista(secciones):
    secciones.loc[1, "LISTA_NOMINAL"] = 14
    r = rentabilidad(secciones, CANDIDATURAS, "coalicion")
    assert r.loc[1, "votos_sobre_lista"]
    assert r.loc[1, "abstencion"] == -1
    assert pd.isna(r.loc[1, "rescatable_vs_abst"])


def test_abstencion_y_participacion_corregidas(secciones):
    secciones["votos_en_lista"] = [12, 12, 20, float("nan"), float("nan")]
    secciones.loc[2, "LISTA_NOMINAL"] = 0
    original = secciones.copy(deep=True)
    r = rentabilidad(secciones, CANDIDATURAS, "coalicion")
    pd.testing.assert_frame_equal(secciones, original)
    assert r.loc[0, "abstencion"] == 13
    assert r.loc[0, "participacion_pct"] == 48
    assert r.loc[1, "abstencion"] == 7
    assert not r.loc[1, "votos_sobre_lista"]
    assert pd.isna(r.loc[2, "participacion_pct"])
    assert r.loc[3:, ["abstencion", "participacion_pct"]].isna().all().all()
