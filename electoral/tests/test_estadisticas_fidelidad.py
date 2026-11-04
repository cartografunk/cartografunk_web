import numpy as np
import pandas as pd
import pytest

from electoral.estadisticas_fidelidad import (
    correlaciones_pares,
    distribucion_rango,
    icc_consistencia,
    icc_por_partido,
)


def _largo(matriz, partido="PAN", elecciones=("pres", "dip", "sen")):
    filas = []
    for i, fila in enumerate(matriz):
        for e, v in zip(elecciones, fila):
            filas.append({"ID_SECCION": f"01-{i:04d}", "partido": partido, "eleccion": e, "pct": v})
    return pd.DataFrame(filas)


def test_icc_perfecto_cuando_las_elecciones_son_iguales():
    base = np.linspace(5, 60, 50)
    X = np.column_stack([base, base, base])
    icc1, icc3 = icc_consistencia(X)
    assert icc1 == pytest.approx(1.0)
    assert icc3 == pytest.approx(1.0)


def test_icc3_ignora_nivel_pero_icc1_lo_penaliza():
    base = np.linspace(5, 60, 50)
    X = np.column_stack([base, base + 10, base + 20])
    icc1, icc3 = icc_consistencia(X)
    assert icc3 == pytest.approx(1.0)
    assert icc1 < icc3


def test_icc_cercano_a_cero_con_ruido_independiente():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(5000, 3))
    icc1, icc3 = icc_consistencia(X)
    assert abs(icc1) < 0.05 and abs(icc3) < 0.05


def test_icc_requiere_dimensiones_minimas():
    with pytest.raises(ValueError):
        icc_consistencia(np.array([[1.0, 2.0]]))


def test_icc_por_partido_y_n():
    base = np.linspace(5, 60, 20)
    largo = pd.concat([
        _largo(np.column_stack([base, base, base]), "PAN"),
        _largo(np.column_stack([base, base[::-1], base]), "PRI"),
    ])
    r = icc_por_partido(largo).set_index("partido")
    assert r.loc["PAN", "n"] == 20
    assert r.loc["PAN", "icc3_consistencia"] == pytest.approx(1.0)
    assert r.loc["PRI", "icc3_consistencia"] < 0.5


def test_correlaciones_tres_pares_y_valores_conocidos():
    base = np.linspace(1, 20, 30)
    largo = _largo(np.column_stack([base, 2 * base + 1, -base]))
    r = correlaciones_pares(largo)
    assert len(r) == 3
    por_par = r.set_index("par")
    assert por_par.loc["dip vs pres", "pearson"] == pytest.approx(1.0)
    assert por_par.loc["pres vs sen", "spearman"] == pytest.approx(-1.0)


def test_distribucion_rango_percentiles_y_agrupacion():
    estab = pd.DataFrame({
        "partido": ["PAN"] * 5 + ["PRI"] * 5,
        "ID_ESTADO": [1, 1, 1, 2, 2] * 2,
        "rango_pp": [0.0, 1.0, 2.0, 3.0, 4.0] * 2,
        "piso_pct": [10.0, 20.0, 30.0, 40.0, 50.0] * 2,
    })
    r = distribucion_rango(estab).set_index("partido")
    assert r.loc["PAN", "n_secciones"] == 5
    assert r.loc["PAN", "rango_pp_p50"] == pytest.approx(2.0)
    assert r.loc["PAN", "piso_pct_p90"] == pytest.approx(46.0)
    por_estado = distribucion_rango(estab, por=["ID_ESTADO"])
    assert len(por_estado) == 4
