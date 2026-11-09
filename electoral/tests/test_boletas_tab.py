import pandas as pd

from electoral.boletas_tab import apoyo_minimo_directo
from scripts.build_ieeq_boletas import normalizar_boleta


def test_normalizar_boleta_conserva_cargo_y_opciones_de_coalicion():
    filas = pd.DataFrame({
        "ID_MUNICIPIO": [14, 14, 14], "SECCION": [782, 782, 782],
        "TIPO_CASILLA": ["B", "C", "S"], "PAN": [10, 15, 100],
        "PAN-PRI": [2, 3, 100], "TOTAL_VOTOS": [15, 20, 200],
        "LISTA_NOMINAL": [30, 30, 300],
    })
    b, v = normalizar_boleta(filas, 2024, "ayuntamiento", "prueba")
    assert len(b) == 1
    assert b.iloc[0].ID_SECCION == "22-0782"
    assert b.iloc[0].TOTAL_VOTOS == 35
    assert v.set_index("OPCION").VOTOS.to_dict() == {"PAN": 25, "PAN-PRI": 5}


def test_apoyo_minimo_directo_no_imputa_coalicion():
    b = pd.DataFrame({"ANIO": [2024, 2024], "CARGO": ["ayuntamiento", "senado"],
                      "ID_SECCION": ["22-0782"] * 2, "ID_MUNICIPIO": [14] * 2})
    v = pd.DataFrame({"ANIO": [2024] * 5,
                      "CARGO": ["ayuntamiento"] * 3 + ["senado"] * 2,
                      "ID_SECCION": ["22-0782"] * 5, "ID_MUNICIPIO": [14] * 5,
                      "OPCION": ["PAN", "PAN-PRI", "MORENA", "PAN", "MORENA"],
                      "VOTOS": [20, 10, 70, 30, 70]})
    piso = apoyo_minimo_directo(b, v, "PAN", 14).iloc[0]
    assert piso.PCT_AYUNTAMIENTO == 20
    assert piso.PCT_SENADO == 30
    assert piso.APOYO_MINIMO_DIRECTO_PCT == 20


def test_apoyo_minimo_usa_todas_las_boletas_sin_sumarlas():
    b = pd.DataFrame({"ANIO": [2024, 2024], "CARGO": ["ayuntamiento", "senado"],
                      "ID_SECCION": ["22-0782"] * 2, "ID_MUNICIPIO": [14] * 2})
    v = pd.DataFrame({"ANIO": [2024] * 4,
                      "CARGO": ["ayuntamiento", "ayuntamiento", "senado", "senado"],
                      "ID_SECCION": ["22-0782"] * 4, "ID_MUNICIPIO": [14] * 4,
                      "OPCION": ["PAN", "MORENA", "PAN", "MORENA"],
                      "VOTOS": [40, 60, 30, 70]})
    extras = pd.DataFrame({"CARGO": ["presidencia", "dip_federal", "dip_local"],
                           "ID_SECCION": ["22-0782"] * 3,
                           "VOTOS_VALIDOS": [100] * 3, "VOTOS": [25, 55, 45]})
    piso = apoyo_minimo_directo(b, v, "PAN", 14, extras).iloc[0]
    assert piso.APOYO_MINIMO_DIRECTO_PCT == 25
    assert piso.PCT_DIP_FEDERAL == 55
