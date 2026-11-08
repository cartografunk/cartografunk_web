"""Las marcas de coalición se cuentan una vez para la candidatura activa."""

import pandas as pd

from electoral.candidaturas_ieeq import margenes_candidatura
from electoral.reparto_ieeq import COMBINACIONES, INDEPENDIENTES, PROPIOS


def test_coalicion_se_suma_a_candidatura_sin_repartir():
    opciones = {col: 0 for col in (*PROPIOS[2024], *COMBINACIONES[2024], *INDEPENDIENTES[2024])}
    opciones.update(PAN=4, PRI=3, PRD=2, MORENA=5, PVEM=1, PT=1, **{"PAN-PRI": 2})
    bruto = pd.DataFrame([{"ID_SECCION": "22-0001", **opciones,
                           "TOTAL_VOTOS": 18, "NULOS": 0, "NO_REGISTRADAS": 0}])
    distritos = pd.DataFrame({"ID_SECCION": ["22-0001"], "ID_DISTRITO_LOCAL": [1]})
    candidatos = {1: [{"id_participante": i} for i in (22, 18, 4, 8)]}
    out = margenes_candidatura(bruto, distritos, candidatos).set_index("PARTIDO")
    assert out.loc["PAN", "VOTOS_CANDIDATURA"] == 11
    assert out.loc["PRI", "VOTOS_CANDIDATURA"] == 11
    assert out.loc["MORENA", "VOTOS_CANDIDATURA"] == 7
    assert round(out.loc["PAN", "MARGEN_CANDIDATURA_PP"], 2) == 22.22
