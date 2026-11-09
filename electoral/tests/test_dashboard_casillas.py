"""Una sede compartida no debe contarse como varias ubicaciones en el mapa."""

import pandas as pd

from electoral.dashboard_casillas import (
    GRUPOS_CPV,
    COLOR_BASE, COLOR_CERCANA, COLOR_DEFENSA, COLOR_EMPATE, COLOR_FORTALEZA,
    COLOR_SECCION_AMPLIA, COLOR_SECCION_CERCANA, COLOR_SECCION_CORTA,
    COLOR_SECCION_EMPATE,
    COLOR_SECCION_LEJANA, COLOR_SECCION_SIN_DATO, COLOR_SIN_DATO,
    _capa_secciones, preparar_sedes,
)
from electoral.cpv import ETIQUETAS


def test_sede_compartida_conserva_casillas_y_senal_prioritaria():
    casillas = pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0001", "22-0002"],
        "CASILLA_ETIQUETA": ["B1", "C1", "B1"],
        "CLASE": ["ganada_solida", "perdida_competitiva", "ganada_ajustada"],
    })
    puntos = pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0001", "22-0002"],
        "CASILLA_ETIQUETA": ["B1", "C1", "B1"],
        "LATITUD": [20.5, 20.5, 20.6],
        "LONGITUD": [-100.4, -100.4, -100.5],
    })
    sedes = preparar_sedes(casillas, puntos)
    assert len(sedes) == 2
    primera = sedes.set_index("ID_SECCION").loc["22-0001"]
    assert primera.NUM_CASILLAS == 2
    assert primera.CASILLAS == "B1, C1"
    assert primera.SENAL == "Pérdida cercana"


def test_paleta_coincide_entre_sedes_y_secciones_y_reserva_gris_para_sin_dato():
    agrupadas = [variable for grupo in GRUPOS_CPV.values() for variable in grupo]
    assert len(agrupadas) == len(set(agrupadas)) == len(ETIQUETAS) == 15
    assert set(agrupadas) == set(ETIQUETAS)
    assert [COLOR_FORTALEZA[:3], COLOR_DEFENSA[:3], COLOR_EMPATE[:3],
            COLOR_CERCANA[:3], COLOR_BASE[:3]] == [
        [44, 123, 182], [171, 217, 233], [255, 255, 191],
        [253, 174, 97], [215, 25, 28],
    ]
    assert [COLOR_SECCION_AMPLIA[:3], COLOR_SECCION_CORTA[:3],
            COLOR_SECCION_EMPATE[:3], COLOR_SECCION_CERCANA[:3],
            COLOR_SECCION_LEJANA[:3]] == [
        COLOR_FORTALEZA[:3], COLOR_DEFENSA[:3], COLOR_EMPATE[:3],
        COLOR_CERCANA[:3], COLOR_BASE[:3],
    ]
    assert COLOR_SECCION_SIN_DATO[:3] == COLOR_SIN_DATO[:3]
    base = pd.DataFrame({
        "ID_SECCION": [f"22-000{i}" for i in range(1, 7)],
        "MARGEN_PP": [10, 5, 0, -10, -11, float("nan")],
        "CASILLA_ETIQUETA": ["B1"] * 6,
    })
    geometrias = {seccion: {"type": "Point", "coordinates": [-100, 20]}
                  for seccion in base.ID_SECCION}
    colores = [feature["properties"]["COLOR"]
               for feature in _capa_secciones(base, geometrias)["features"]]
    assert colores == [COLOR_SECCION_AMPLIA, COLOR_SECCION_CORTA, COLOR_SECCION_EMPATE,
                       COLOR_SECCION_CERCANA, COLOR_SECCION_LEJANA,
                       COLOR_SECCION_SIN_DATO]
