import pandas as pd

from electoral.boletas_tab import apoyo_minimo_directo, resumen_marcas_casilla, zoom_seccion
from electoral.reparto_ieeq import COMBINACIONES, INDEPENDIENTES, PROPIOS
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


def test_resumen_marcas_muestra_votos_rival_y_diferencia_sin_imputar_coalicion():
    opciones = [*PROPIOS[2024], *COMBINACIONES[2024], *INDEPENDIENTES[2024]]
    datos = {opcion: [0, 0, 0] for opcion in opciones}
    datos.update({"PAN": [40, 25, 10], "MORENA": [30, 50, 10],
                  "PAN-PRI": [20, 0, 0]})
    salida = resumen_marcas_casilla(pd.DataFrame(datos), "PAN")
    assert salida.VOTOS_OPCION.tolist() == [40, 25, 10]
    assert salida.RIVAL.tolist() == ["MORENA", "MORENA", "MORENA"]
    assert salida.VOTOS_RIVAL.tolist() == [30, 50, 10]
    assert salida.DIFERENCIA_VOTOS.tolist() == [10, -25, 0]
    assert salida.DIFERENCIA_PP.tolist() == [11.1, -33.3, 0.0]
    assert salida.LECTURA_RESULTADO.tolist() == [
        "Ventaja de 10 votos (11.1 pp)",
        "Desventaja de 25 votos (33.3 pp)",
        "Empate en marcas",
    ]


def test_zoom_seccion_encuadra_secciones_urbanas_y_rurales():
    assert 15 < zoom_seccion((-100.451, 20.640, -100.444, 20.646)) < 16
    assert 9 < zoom_seccion((-100.6, 20.5, -100.4, 20.7)) < 13
