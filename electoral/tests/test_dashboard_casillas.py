"""Una sede compartida no debe contarse como varias ubicaciones en el mapa."""

import pandas as pd

from electoral.dashboard_casillas import preparar_sedes


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
