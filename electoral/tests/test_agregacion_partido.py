import pandas as pd

from electoral.agregacion import agregar
from electoral.rentabilidad_partido import rentabilidad_partido


def test_pais_incluye_extranjero_y_partido_se_resuelve():
    d = pd.DataFrame({
        "ID_ESTADO": [1, 1, 1], "ID_DISTRITO_FEDERAL": [1, 1, 0],
        "estado": ["con_resultado", "sin_resultado", "extranjero"],
        "cand_PAN_PRI_PRD": [5.0, 0.0, 2.0],
        "cand_PVEM_PT_MORENA": [10.0, 0.0, 3.0],
        "cand_MC": [2.0, 0.0, 1.0],
        "NUM_VOTOS_VALIDOS": [17, 0, 6],
        "TOTAL_VOTOS": [17, 0, 6],
        "LISTA_NOMINAL": [20, 10, 10],
    })
    original = d.copy(deep=True)
    r = rentabilidad_partido(d, "MORENA")
    a = agregar(r, "pais", ["cand_PAN_PRI_PRD", "cand_PVEM_PT_MORENA", "cand_MC"],
                "cand_PVEM_PT_MORENA", partido="MORENA")
    assert len(a) == 1
    assert a.loc[0, "cand_PVEM_PT_MORENA"] == 13
    assert a.loc[0, "n_secciones"] == 3
    assert a.loc[0, "n_con_resultado"] == 1
    assert a.loc[0, "n_sin_resultado"] == 1
    assert a.loc[0, "resultado"] == "ganada"
    pd.testing.assert_frame_equal(d, original)


def test_agregado_partido_respeta_candidaturas_ausentes():
    d = pd.DataFrame({
        "ID_ESTADO": [1, 1], "ID_DISTRITO_FEDERAL": [1, 1],
        "estado": ["con_resultado", "con_resultado"],
        "cand_PAN_PRI_PRD": [float("nan"), float("nan")],
        "cand_PAN": [4.0, 6.0], "cand_MC": [3.0, 4.0],
        "NUM_VOTOS_VALIDOS": [7, 10], "TOTAL_VOTOS": [7, 10],
        "LISTA_NOMINAL": [10, 10],
    })
    r = rentabilidad_partido(d, "PAN")
    a = agregar(r, "distrito", ["cand_PAN_PRI_PRD", "cand_PAN", "cand_MC"],
                "cand_PAN", partido="PAN")
    assert pd.isna(a.loc[0, "cand_PAN_PRI_PRD"])
    assert a.loc[0, "resultado"] == "ganada"
