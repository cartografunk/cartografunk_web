import pandas as pd
import pytest

from electoral.fidelidad import analizar_fidelidad
from electoral.reparto import COALICIONES


def _elecciones(especificaciones):
    base = {
        "estado": "con_resultado", "ID_ESTADO": 1, "LISTA_NOMINAL": 200,
        **{p: 0 for g in COALICIONES.values() for p in g["partidos"]},
        **{c: 0 for g in COALICIONES.values() for c in g["combinaciones"]},
        "MC": 0,
    }
    salida = {}
    for eleccion in ("presidencia", "diputaciones", "senadurias"):
        filas = []
        for i, cambios in enumerate(especificaciones[eleccion]):
            fila = {**base, "ID_SECCION": f"{cambios.get('ID_ESTADO', 1):02d}-{i:04d}", **cambios}
            fila["NUM_VOTOS_VALIDOS"] = sum(
                fila[c] for c in ("PAN", "PRI", "PRD", "PVEM", "PT", "MORENA", "MC", "PAN_PRI_PRD", "PVEM_PT_MORENA")
            )
            filas.append(fila)
        salida[eleccion] = pd.DataFrame(filas)
    return salida


def _mismos(filas):
    return _elecciones({n: filas for n in ("presidencia", "diputaciones", "senadurias")})


def test_empate_no_es_primera_en_todas():
    d = _mismos([{"PAN": 50, "MC": 50, "cand_PAN": 50, "cand_MC": 50}])
    r = analizar_fidelidad(d, pct_bastion=50)
    pan = r.loc[r.partido.eq("PAN")].iloc[0]
    assert not pan.primera_en_todas
    assert pan.clase == "Base fuerte"


def test_bastion_por_estado_frente_a_nacional():
    filas = [
        {"ID_ESTADO": 1, "PAN": 60, "MC": 40, "cand_PAN": 60, "cand_MC": 40},
        {"ID_ESTADO": 2, "PAN": 80, "MC": 20, "cand_PAN": 80, "cand_MC": 20},
    ]
    d = _mismos(filas)
    estatal = analizar_fidelidad(d).set_index(["ID_SECCION", "partido"])
    assert estatal.loc[("01-0000", "PAN"), "clase"] == "Bastión"
    nacional = analizar_fidelidad(d, ambito="nacional").set_index(["ID_SECCION", "partido"])
    assert nacional.loc[("01-0000", "PAN"), "clase"] == "Resto"


def test_tukey_detecta_outlier():
    estables = [{"PAN": 60, "MC": 40, "cand_PAN": 60, "cand_MC": 40} for _ in range(8)]
    d = _mismos(estables)
    d["senadurias"].loc[7, ["PAN", "MC", "cand_PAN", "cand_MC"]] = [10, 90, 10, 90]
    r = analizar_fidelidad(d)
    pan = r.loc[r.partido.eq("PAN")].set_index("ID_SECCION")
    assert pan.loc["01-0007", "volatil"]
    assert pan.loc["01-0007", "umbral_rango_pp"] == 0
    assert not pan.loc["01-0000", "volatil"]


def test_filtro_lista_nominal_en_cualquier_eleccion():
    d = _mismos([{"PAN": 60, "MC": 40, "cand_PAN": 60, "cand_MC": 40},
                 {"PAN": 70, "MC": 30, "cand_PAN": 70, "cand_MC": 30}])
    d["diputaciones"].loc[1, "LISTA_NOMINAL"] = 99
    r = analizar_fidelidad(d)
    assert set(r.ID_SECCION) == {"01-0000"}


def test_coalicion_distinta():
    d = _mismos([{"PAN": 60, "MC": 40, "cand_PAN": 60, "cand_MC": 40}])
    d["presidencia"].loc[0, "cand_PAN_PRI_PRD"] = 60
    d["presidencia"] = d["presidencia"].drop(columns="cand_PAN")
    r = analizar_fidelidad(d).set_index("partido")
    assert r.loc["PAN", "coalicion_distinta"]
    assert not r.loc["MC", "coalicion_distinta"]


def test_ambito_invalido_y_entrada_intacta():
    d = _mismos([{"PAN": 60, "MC": 40, "cand_PAN": 60, "cand_MC": 40}])
    originales = {n: x.copy(deep=True) for n, x in d.items()}
    with pytest.raises(ValueError, match="ambito"):
        analizar_fidelidad(d, ambito="municipio")
    analizar_fidelidad(d)
    for n in d:
        pd.testing.assert_frame_equal(d[n], originales[n])
