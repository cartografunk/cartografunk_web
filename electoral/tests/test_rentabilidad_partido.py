import pandas as pd

from electoral.candidaturas import resolver_candidatura
from electoral.rentabilidad_partido import rentabilidad_partido


def test_candidatura_variable_y_rivales_ausentes():
    df = pd.DataFrame({
        "estado": ["con_resultado", "con_resultado", "con_resultado"],
        "cand_PVEM_PT_MORENA": [10.0, 10.0, float("nan")],
        "cand_PT": [float("nan"), float("nan"), 2.0],
        "cand_MORENA": [float("nan"), float("nan"), 8.0],
        "cand_MC": [5.0, 5.0, 5.0],
        "NUM_VOTOS_VALIDOS": [15, 15, 15],
        "TOTAL_VOTOS": [15, 15, 15],
        "LISTA_NOMINAL": [20, 20, 20],
    })
    original = df.copy(deep=True)
    assert resolver_candidatura(df, "PT").tolist() == ["cand_PVEM_PT_MORENA", "cand_PVEM_PT_MORENA", "cand_PT"]
    r = rentabilidad_partido(df, "PT")
    assert r["resultado"].tolist() == ["ganada", "ganada", "perdida"]
    assert r.loc[2, "faltante_votos"] == 6
    pd.testing.assert_frame_equal(df, original)


def test_partido_no_compitio():
    df = pd.DataFrame({
        "estado": ["con_resultado"], "cand_MC": [5.0],
        "cand_PAN": [3.0], "NUM_VOTOS_VALIDOS": [8],
        "TOTAL_VOTOS": [8], "LISTA_NOMINAL": [10],
    })
    r = rentabilidad_partido(df, "MORENA")
    assert pd.isna(r.loc[0, "resultado"])
    assert pd.isna(r.loc[0, "clase"])
    assert r.loc[0, "estado"] == "con_resultado"
