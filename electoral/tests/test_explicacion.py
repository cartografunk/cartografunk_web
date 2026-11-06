import numpy as np
import pandas as pd
import pytest

from electoral.cpv import ETIQUETAS, VARIABLES, preparar_variables
from electoral.explicacion import explicar, perfil_clases, piso_candidatura, ventaja_firmada


def test_cpv_llave_y_denominador_nulo():
    datos = {col: [10, 0] for _, _, num, den in VARIABLES for col in (num, den)}
    datos.update(ENTIDAD=[1, 2], SECCION=[338, 4], POBTOT=[20, 0], POBFEM=[10, 0])
    salida = preparar_variables(pd.DataFrame(datos))
    assert salida.ID_SECCION.tolist() == ["01-0338", "02-0004"]
    assert salida.pct_mujeres.iloc[0] == 50
    assert pd.isna(salida.pct_mujeres.iloc[1])


def test_piso_requiere_actividad_en_tres_boletas():
    base = pd.DataFrame({"ID_SECCION": ["01-0001", "01-0002"], "ID_ESTADO": [1, 1],
                         "estado": ["con_resultado"] * 2, "NUM_VOTOS_VALIDOS": [100, 100],
                         "cand_X": [40, 30]})
    segunda = base.copy()
    segunda["cand_X"] = [20, np.nan]
    tercera = base.copy()
    tercera["cand_X"] = [50, 50]
    piso = piso_candidatura({"presidencia": base, "diputaciones": segunda, "senadurias": tercera}, "cand_X")
    assert piso.piso_pct.iloc[0] == 20
    assert pd.isna(piso.piso_pct.iloc[1])


def _ejemplo():
    n = 90
    ids = [f"01-{i:04d}" for i in range(1, n + 1)]
    x = np.arange(n, dtype=float)
    resultados = pd.DataFrame({"ID_SECCION": ids, "ID_ESTADO": [1] * n,
        "estado": ["con_resultado"] * n, "cand_X": [1] * n,
        "resultado": ["ganada"] * 30 + ["perdida"] * 59 + ["empate"],
        "clase": ["ganada_solida"] * 30 + ["perdida_competitiva"] * 30 + ["perdida_lejana"] * 29 + ["empate"],
        "margen_pct": list(x[:30]) + [np.nan] * 60,
        "faltante_pct": [np.nan] * 30 + list(x[30:89]) + [0],
        "alcanzable_por_abstencion": [pd.NA] * 30 + [True] * 30 + [False] * 29 + [pd.NA],
        "piso_pct": x,
    })
    censo = pd.DataFrame({"ID_SECCION": ids, **{v: x if v == "pct_internet" else np.full(n, 10.0) for v in ETIQUETAS}})
    return resultados, censo


def test_ventaja_firmada_incluye_victorias_derrotas_y_empates():
    r, _ = _ejemplo()
    d = ventaja_firmada(r)
    assert d.iloc[29] == 29
    assert d.iloc[30] == -30
    assert d.iloc[-1] == 0
    r.loc[0, "estado"] = "sin_resultado"
    assert pd.isna(ventaja_firmada(r).iloc[0])


def test_objetivos_derrota_filtran_y_no_usan_cociente_rescatable():
    r, c = _ejemplo()
    r["rescatable_vs_abst"] = 9999
    ventaja = explicar(r, c, "cand_X", 1, "ventaja_firmada")
    faltante = explicar(r, c, "cand_X", 1, "faltante_pct")
    alcanzable = explicar(r, c, "cand_X", 1, "alcanzable_por_abstencion")
    assert (ventaja["n"], faltante["n"], alcanzable["n"]) == (90, 59, 59)
    assert all(v["variable"] != "rescatable_vs_abst" for v in alcanzable["variables"])
    assert next(v for v in faltante["variables"] if v["variable"] == "pct_internet")["correlacion"] > 0
    assert next(v for v in alcanzable["variables"] if v["variable"] == "pct_internet")["correlacion"] < 0
    assert explicar(r, c, "cand_X", 2, "ventaja_firmada")["n"] == 0


def test_perfil_todas_las_variables_y_diferencia_estandarizada():
    r, c = _ejemplo()
    perfil = perfil_clases(r, c, 1,
        ("ganada_solida", "perdida_competitiva", "perdida_lejana"), "perdida_lejana")
    tabla = perfil["tabla"]
    assert len(tabla) == 15
    internet = tabla.set_index("variable").loc["pct_internet"]
    assert internet["media_ganada_solida"] == 14.5
    assert internet["dif_est_ganada_solida_vs_perdida_lejana"] < 0
    assert perfil["n_por_clase"] == {"ganada_solida": 30, "perdida_competitiva": 30, "perdida_lejana": 29}
    assert any("menor proporción" in frase for frase in perfil["frases"])


def test_perfil_apoyo_minimo_por_clase():
    r, c = _ejemplo()
    r["clase"] = ["Bastión"] * 30 + ["Base fuerte"] * 30 + ["Resto"] * 30
    perfil = perfil_clases(r, c, 1, ("Bastión", "Base fuerte", "Resto"), "Resto")
    assert len(perfil["tabla"]) == 15
    assert perfil["n_por_clase"]["Bastión"] == 30


def test_explicacion_rechaza_duplicados():
    r, c = _ejemplo()
    with pytest.raises(ValueError, match="único"):
        explicar(r, pd.concat([c, c.iloc[[0]]]), "cand_X", 1)
