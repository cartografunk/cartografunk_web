import pandas as pd
import pytest

from electoral.agregacion import agregar
from electoral.clasificacion import clasificar
from electoral.rentabilidad import rentabilidad


CANDIDATURAS = ["cand_A", "cand_B", "cand_C"]


@pytest.fixture
def secciones():
    base = pd.DataFrame({
        "ID_ESTADO": [1, 1, 2, 1, 1],
        "ID_DISTRITO_FEDERAL": [1, 1, 2, 1, 0],
        "ID_MUNICIPIO": [10, 10, 20, 10, 0],
        "MUNICIPIO": ["UNO", "UNO", "DOS", "UNO", "EXTRANJERO"],
        "estado": ["con_resultado", "con_resultado", "con_resultado", "sin_resultado", "extranjero"],
        "cand_A": [6, 25, 49, 0, 1000],
        "cand_B": [4, 15, 50, 0, 1000],
        "cand_C": [0, 0, 0, 0, 1000],
        "NUM_VOTOS_VALIDOS": [10, 40, 99, 0, 3000],
        "TOTAL_VOTOS": [10, 40, 99, 0, 3000],
        "LISTA_NOMINAL": [20, 50, 90, 100, 3000],
    })
    return clasificar(rentabilidad(base, CANDIDATURAS, "cand_A"))


def test_sumas_y_conteos_no_incluyen_sin_resultado_ni_extranjero(secciones):
    original = secciones.copy(deep=True)
    distritos = agregar(secciones, "distrito", CANDIDATURAS, "cand_A")
    pd.testing.assert_frame_equal(secciones, original)
    assert len(distritos) == 2
    uno = distritos.loc[distritos.ID_ESTADO.eq(1)].iloc[0]
    assert (uno.n_secciones, uno.n_con_resultado, uno.n_sin_resultado) == (3, 2, 1)
    assert (uno.cand_A, uno.cand_B, uno.cand_C) == (31, 19, 0)
    assert (uno.NUM_VOTOS_VALIDOS, uno.LISTA_NOMINAL) == (50, 70)
    assert int(distritos.cand_A.sum()) == 80
    dos = distritos.loc[distritos.ID_ESTADO.eq(2)].iloc[0]
    assert dos.n_perdida_competitiva == 1
    assert dos.votos_para_ganar_perdida_competitiva == 2
    assert dos.n_votos_sobre_lista == 1


def test_ranking_se_recalcula_desde_las_sumas(secciones):
    distrito = agregar(secciones, "distrito", CANDIDATURAS, "cand_A")
    uno = distrito.loc[distrito.ID_ESTADO.eq(1)].iloc[0]
    margenes = secciones.loc[secciones.ID_ESTADO.eq(1) & secciones.estado.eq("con_resultado"), "margen_pct"]
    assert uno.resultado == "ganada"
    assert uno.margen_votos == 12
    assert uno.margen_pct == 24
    assert uno.margen_pct != margenes.mean()


def test_otros_niveles_y_nivel_invalido(secciones):
    municipios = agregar(secciones, "municipio", CANDIDATURAS, "cand_A")
    estados = agregar(secciones, "estado", CANDIDATURAS, "cand_A")
    assert len(municipios) == len(estados) == 2
    assert municipios[["ID_ESTADO", "ID_MUNICIPIO", "MUNICIPIO"]].duplicated().sum() == 0
    with pytest.raises(ValueError):
        agregar(secciones, "casilla", CANDIDATURAS, "cand_A")
