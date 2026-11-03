import pandas as pd
import pytest

from electoral.reparto import COALICIONES
from electoral.reparto_distrito import repartir_distrito
from electoral.reparto_fraccionario import repartir_fraccionario


def _fila(**cambios):
    fila = {
        "ID_ESTADO": 1,
        "ID_DISTRITO_FEDERAL": 1,
        "SECCION": 1,
        "estado": "con_resultado",
        "MC": 0,
        **{partido: 0 for grupo in COALICIONES.values() for partido in grupo["partidos"]},
        **{combo: 0 for grupo in COALICIONES.values() for combo in grupo["combinaciones"]},
    }
    fila.update(cambios)
    return fila


@pytest.mark.parametrize("variante", ["A_propios", "B_propios"])
def test_distrito_conserva_votos_y_no_muta(variante):
    df = pd.DataFrame([
        _fila(PAN=1, PRI=5, PAN_PRI=1, PVEM=3, PT=2, PVEM_PT_MORENA=3),
        _fila(SECCION=2, PAN=10, PAN_PRI=2, PT_MORENA=2, MC=4),
        _fila(ID_DISTRITO_FEDERAL=0, SECCION=0, estado="extranjero", PAN=3, PRI=3, PAN_PRI=1),
    ])
    original = df.copy(deep=True)
    repartido = repartir_distrito(df, variante)
    pd.testing.assert_frame_equal(df, original)
    assert len(repartido) == 2
    for grupo in COALICIONES:
        partes = COALICIONES[grupo]["partidos"]
        assert repartido[[f"rep_{p}" for p in partes]].sum(axis=1).eq(
            repartido[f"suma_original_{grupo}"]
        ).all()
    distrito = repartido.loc[repartido.ID_DISTRITO_FEDERAL.eq(1)].iloc[0]
    assert distrito.rep_MC == 4
    if variante == "A_propios":
        assert (distrito.rep_PAN, distrito.rep_PRI) == (13, 6)
    extranjero = repartido.loc[repartido.ID_DISTRITO_FEDERAL.eq(0)].iloc[0]
    assert (extranjero.rep_PAN, extranjero.rep_PRI) == (4, 3)


def test_fraccionario_conserva_y_deja_extranjero_vacio():
    df = pd.DataFrame([
        _fila(PAN=5, PRI=2, PAN_PRI_PRD=3, PAN_PRI=2, PVEM=1, PVEM_PT_MORENA=3),
        _fila(ID_DISTRITO_FEDERAL=0, SECCION=0, estado="extranjero", PAN_PRI=1),
        _fila(SECCION=2, estado="sin_resultado", PT_MORENA=2),
    ])
    original = df.copy(deep=True)
    repartido = repartir_fraccionario(df)
    pd.testing.assert_frame_equal(df, original)
    assert all(pd.api.types.is_float_dtype(repartido[f"frac_{p}"]) for g in COALICIONES.values() for p in g["partidos"])
    for grupo in COALICIONES.values():
        partes = list(grupo["partidos"])
        columnas = partes + list(grupo["combinaciones"])
        assert repartido.loc[0, [f"frac_{p}" for p in partes]].sum() == df.loc[0, columnas].sum()
    assert repartido.loc[1:, [f"frac_{p}" for g in COALICIONES.values() for p in g["partidos"]]].isna().all().all()
    assert repartido.loc[0, "frac_PAN"] == 7


def test_variante_distrital_desconocida():
    with pytest.raises(ValueError):
        repartir_distrito(pd.DataFrame(), "C")
