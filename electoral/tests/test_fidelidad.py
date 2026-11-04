import pandas as pd
import pytest

from electoral.fidelidad import (
    PARTIDOS,
    estabilidad,
    panel,
    porcentaje_por_partido,
    votos_por_partido,
)
from electoral.reparto import COALICIONES


def _df(filas):
    base = {
        "estado": "con_resultado",
        "MC": 0,
        **{p: 0 for g in COALICIONES.values() for p in g["partidos"]},
        **{c: 0 for g in COALICIONES.values() for c in g["combinaciones"]},
    }
    registros = []
    for i, cambios in enumerate(filas):
        r = {**base, "ID_SECCION": f"01-{i:04d}", **cambios}
        if "NUM_VOTOS_VALIDOS" not in cambios:
            r["NUM_VOTOS_VALIDOS"] = sum(
                v for k, v in r.items() if k in PARTIDOS or "_" in k and k.isupper() and k != "ID_SECCION"
            )
        registros.append(r)
    return pd.DataFrame(registros)


def test_reparto_partes_iguales_y_residuo_al_mayor_propio():
    df = _df([{"PAN": 10, "PRI": 6, "PAN_PRI": 5}])
    v = votos_por_partido(df)
    assert v.loc["01-0000", ["PAN", "PRI", "PRD"]].tolist() == [13, 8, 0]


def test_conserva_votos_validos_cuando_no_hay_independientes():
    df = _df([
        {"PAN": 10, "PRI": 6, "PRD": 2, "PAN_PRI_PRD": 5, "PVEM": 4, "PT": 2,
         "MORENA": 8, "PVEM_PT_MORENA": 7, "MC": 3},
    ])
    v = votos_por_partido(df)
    assert v[list(PARTIDOS)].sum(axis=1).iloc[0] == v["VALIDOS"].iloc[0]


def test_porcentaje_suma_100_y_excluye_sin_resultado():
    df = _df([{"PAN": 3, "MORENA": 1}, {"PAN": 1, "estado": "sin_resultado"}])
    p = porcentaje_por_partido(df)
    assert list(p.index) == ["01-0000"]
    assert p.loc["01-0000"].sum() == pytest.approx(100.0)


def test_llave_duplicada_falla():
    df = _df([{"PAN": 1}, {"PAN": 1}])
    df["ID_SECCION"] = "01-0000"
    with pytest.raises(ValueError):
        votos_por_partido(df)


def test_panel_y_estabilidad_piso_y_rango():
    a = _df([{"PAN": 60, "MORENA": 40}, {"PAN": 10, "MORENA": 90}])
    b = _df([{"PAN": 50, "MORENA": 50}, {"PAN": 30, "MORENA": 70}])
    largo = panel({"pres": a, "dip": b})
    assert set(largo["eleccion"]) == {"pres", "dip"}
    e = estabilidad(largo).set_index(["ID_SECCION", "partido"])
    fila = e.loc[("01-0000", "PAN")]
    assert fila["piso_pct"] == pytest.approx(50.0)
    assert fila["rango_pp"] == pytest.approx(10.0)
    assert fila["piso_votos"] == 50
    assert fila["n_elecciones"] == 2
    assert e.loc[("01-0001", "PAN"), "rango_pp"] == pytest.approx(20.0)


def test_panel_solo_secciones_comunes():
    a = _df([{"PAN": 1}, {"PAN": 1}])
    b = _df([{"PAN": 1}])
    largo = panel({"a": a, "b": b})
    assert set(largo["ID_SECCION"]) == {"01-0000"}


def test_panel_requiere_dos_elecciones():
    with pytest.raises(ValueError):
        panel({"a": _df([{"PAN": 1}])})
