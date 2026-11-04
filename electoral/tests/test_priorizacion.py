import pandas as pd

from electoral.priorizacion import (
    calcular_costos, cubrir_meta, meta_distrital, preparar_priorizacion, presupuestar,
)


def _secciones():
    return pd.DataFrame({
        "ID_SECCION": ["14-0001", "14-0002", "14-0003", "14-0004"],
        "MUNICIPIO": ["A", "A", "B", "B"],
        "ID_DISTRITO_FEDERAL": [2, 2, 2, 3],
        "resultado": ["perdida", "empate", "perdida", "ganada"],
        "abstencion": [100, 20, -1, 50],
        "votos_sobre_lista": [False, False, True, False],
        "votos_para_ganar": [5, 1, 10, None],
    })


def test_costos_presupuesto_y_descartadas():
    entrada = _secciones()
    original = entrada.copy(deep=True)
    tabla = preparar_priorizacion(entrada, 10)
    assert tabla.ID_SECCION.tolist() == ["14-0001", "14-0002"]
    tabla.loc[0, "costo_por_voto"] = 20
    tabla.loc[1, "descartar"] = True
    calculada = calcular_costos(tabla)
    assert calculada.loc[0, "costo_estimado"] == 5 * 20
    salida, gastado = presupuestar(calculada, 100)
    assert gastado == 100
    assert gastado <= 100
    assert not salida.loc[1, "seleccionada"]
    assert salida.loc[1, "descartar"]
    pd.testing.assert_frame_equal(entrada, original)


def test_meta_agregada_y_capacidad():
    distritos = pd.DataFrame({"ID_DISTRITO_FEDERAL": [2], "faltante_votos": [119]})
    meta = meta_distrital(distritos, 2)
    assert meta == 120
    tabla = preparar_priorizacion(_secciones(), 10)
    assert cubrir_meta(tabla, 2, meta) == (2, 120)
    tabla.loc[1, "descartar"] = True
    assert cubrir_meta(tabla, 2, meta) == (None, 100)
