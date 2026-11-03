import pandas as pd

from electoral.candidaturas import actividad_distrital, candidaturas_por_distrito


def _discand():
    return pd.DataFrame({
        "ID_ESTADO": [1, 1], "ID_DISTRITO_FEDERAL": [1, 2],
        "ACTAS_CASILLA-MEC": [1, 1],
        "PAN": ["", "1"], "PRI": ["", "1"], "PRD": ["", "1"],
        "PVEM": ["", ""], "PT": ["", ""], "MC": ["1", "1"],
        "MORENA": ["", ""],
        "PAN_PRI_PRD": ["1", ""], "PVEM_PT_MORENA": ["1", "1"],
        "NUM_VOTOS_VALIDOS": [10, 10],
    })


def test_coalicion_activa_y_partidos_solos_sin_mutar():
    sec = pd.DataFrame({
        "ID_ESTADO": [1, 1], "ID_DISTRITO_FEDERAL": [1, 2],
        "PAN": [3, 4], "PRI": [2, 2], "PRD": [1, 1],
        "PAN_PRI_PRD": [1, 0], "PAN_PRI": [2, 0], "PAN_PRD": [0, 0], "PRI_PRD": [0, 0],
        "PVEM": [1, 1], "PT": [2, 2], "MORENA": [3, 3],
        "PVEM_PT_MORENA": [1, 1], "PVEM_PT": [0, 0],
        "PVEM_MORENA": [0, 0], "PT_MORENA": [2, 2], "MC": [4, 4],
    })
    original = sec.copy(deep=True)
    result = candidaturas_por_distrito(sec, _discand())
    pd.testing.assert_frame_equal(sec, original)
    assert result.loc[0, "cand_PAN_PRI_PRD"] == 9
    assert pd.isna(result.loc[0, "cand_PAN"])
    assert result.loc[1, "cand_PAN"] == 4
    assert pd.isna(result.loc[1, "cand_PAN_PRI_PRD"])
    assert result.loc[1, "cand_PVEM_PT_MORENA"] == 9
    assert pd.isna(result.loc[1, "cand_PT"])
    assert actividad_distrital(_discand())[(1, 2)] == (
        "PAN", "PRI", "PRD", "MC", "PVEM_PT_MORENA"
    )
