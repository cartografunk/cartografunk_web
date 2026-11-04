import pandas as pd

from electoral.analisis_demo import analizar_candidatura, aportes_coalicion


def _secciones():
    base = {
        "ID_ESTADO": [14, 14], "ID_SECCION": ["14-0001", "14-0002"],
        "estado": ["con_resultado", "con_resultado"],
        "NUM_VOTOS_VALIDOS": [30, 20], "TOTAL_VOTOS": [30, 20],
        "LISTA_NOMINAL": [50, 50],
        "PAN": [8, 0], "PRI": [4, 0], "PRD": [2, 0],
        "PAN_PRI_PRD": [3, 0], "PAN_PRI": [1, 0],
        "PAN_PRD": [0, 0], "PRI_PRD": [0, 0],
        "PVEM": [1, 1], "PT": [2, 1], "MORENA": [3, 1],
        "PVEM_PT_MORENA": [2, 0], "PVEM_PT": [0, 0],
        "PVEM_MORENA": [0, 0], "PT_MORENA": [1, 0],
        "cand_PAN_PRI_PRD": [18.0, float("nan")],
        "cand_PAN": [float("nan"), 8.0],
        "cand_PVEM_PT_MORENA": [9.0, 3.0],
        "cand_MC": [3.0, 9.0],
    }
    return pd.DataFrame(base)


def test_candidatura_inactiva_no_es_derrota_y_entrada_intacta():
    entrada = _secciones()
    copia = entrada.copy(deep=True)
    salida = analizar_candidatura(entrada, "cand_PAN_PRI_PRD")
    assert salida.loc[0, "resultado"] == "ganada"
    assert pd.isna(salida.loc[1, "resultado"])
    assert pd.isna(salida.loc[1, "clase"])
    assert salida.loc[1, "estado"] == "con_resultado"
    pd.testing.assert_frame_equal(entrada, copia)


def test_aporte_por_partido_conserva_resultado_de_candidatura():
    analisis = analizar_candidatura(_secciones(), "cand_PAN_PRI_PRD")
    secciones, estado = aportes_coalicion(analisis, "cand_PAN_PRI_PRD", ["PAN", "PRI", "PRD"])
    assert len(secciones) == 1
    assert secciones["resultado"].iloc[0] == "ganada"
    assert secciones[["rep_PAN", "rep_PRI", "rep_PRD"]].sum(axis=1).iloc[0] == 18
    assert estado["Votos atribuidos"].sum() == 18
    assert round(estado["% de la candidatura"].sum(), 6) == 100
    assert secciones["pct_candidatura_PAN"].iloc[0] > secciones["pct_candidatura_PRI"].iloc[0]


def test_seleccion_parcial_solo_muestra_partidos_elegidos():
    analisis = analizar_candidatura(_secciones(), "cand_PAN_PRI_PRD")
    _, estado = aportes_coalicion(analisis, "cand_PAN_PRI_PRD", ["PRI"])
    assert estado["Partido"].tolist() == ["PRI"]
