import pandas as pd
import pytest

from electoral.reparto import COALICIONES, repartir_coalicion


def _fila(**cambios):
    fila = {
        "estado": "con_resultado",
        **{partido: 0 for grupo in COALICIONES.values() for partido in grupo["partidos"]},
        **{combo: 0 for grupo in COALICIONES.values() for combo in grupo["combinaciones"]},
    }
    fila.update(cambios)
    return fila


@pytest.mark.parametrize("variante", ["A_propios", "B_propios"])
def test_conservacion_por_fila_y_coalicion(variante):
    df = pd.DataFrame([
        _fila(PAN=10, PRI=6, PRD=2, PAN_PRI_PRD=5, PAN_PRI=3, PRI_PRD=1,
              PVEM=4, PT=2, MORENA=8, PVEM_PT_MORENA=7, PT_MORENA=3),
        _fila(PAN=0, PRI=0, PRD=0, PAN_PRI=1, PVEM=0, PT=0, MORENA=0, PT_MORENA=1),
    ])
    reparto = repartir_coalicion(df, variante)
    for grupo in COALICIONES.values():
        partidos = list(grupo["partidos"])
        combinaciones = list(grupo["combinaciones"])
        esperado = df[partidos + combinaciones].sum(axis=1)
        medido = reparto[[f"rep_{partido}" for partido in partidos]].sum(axis=1)
        pd.testing.assert_series_equal(medido, esperado, check_names=False, check_dtype=False)


def test_residuo_y_empate_usan_votos_propios_y_orden_fijo():
    df = pd.DataFrame([
        _fila(PAN=10, PRI=6, PAN_PRI=5),
        _fila(PAN=7, PRI=7, PAN_PRI=1, PVEM=3, PT=3, PVEM_PT=1),
    ])
    reparto = repartir_coalicion(df)
    assert reparto.loc[0, ["rep_PAN", "rep_PRI"]].tolist() == [13, 8]
    assert reparto.loc[1, ["rep_PAN", "rep_PRI"]].tolist() == [8, 7]
    assert reparto.loc[1, ["rep_PVEM", "rep_PT", "rep_MORENA"]].tolist() == [4, 3, 0]


def test_b_propios_junta_combinaciones_antes_de_repartir():
    df = pd.DataFrame([_fila(PAN=10, PRI=1, PRD=0, PAN_PRI=1, PRI_PRD=1)])
    a = repartir_coalicion(df, "A_propios")
    b = repartir_coalicion(df, "B_propios")
    assert a.loc[0, ["rep_PAN", "rep_PRI", "rep_PRD"]].tolist() == [11, 2, 0]
    assert b.loc[0, ["rep_PAN", "rep_PRI", "rep_PRD"]].tolist() == [12, 1, 0]


def test_no_muta_y_deja_nan_fuera_de_con_resultado():
    df = pd.DataFrame([
        _fila(PAN_PRI=1),
        _fila(estado="sin_resultado", PAN_PRI=2),
        _fila(estado="extranjero", PT_MORENA=3),
    ])
    original = df.copy(deep=True)
    reparto = repartir_coalicion(df)
    pd.testing.assert_frame_equal(df, original)
    assert reparto.loc[1:, [f"rep_{p}" for g in COALICIONES.values() for p in g["partidos"]]].isna().all().all()


def test_variante_desconocida():
    with pytest.raises(ValueError):
        repartir_coalicion(pd.DataFrame(), "C")
