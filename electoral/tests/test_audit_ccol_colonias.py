import pandas as pd

from scripts.audit_ccol_colonias import auditar, comparar_con_espacial, nombre_normalizado


def test_normalizacion_de_nombre():
    assert nombre_normalizado(" Peñitas, Las ") == "PENITASLAS"


def test_id_compartido_no_implica_misma_colonia():
    poligonos = pd.DataFrame([
        {"ENTIDAD": 1, "ID": 1, "MUNICIPIO": 2, "NOMBRE": "Guadalupe", "CP": 20714, "CONTROL": 10},
        {"ENTIDAD": 1, "ID": 2, "MUNICIPIO": 2, "NOMBRE": "Centro", "CP": 20710, "CONTROL": 11},
    ])
    catalogo = pd.DataFrame([
        {"ENTIDAD": 1, "ID": 1, "MUNICIPIO": 2, "NOMBRE": "Otra", "CP": 20714, "CONTROL": 30, "SECCION": 338},
        {"ENTIDAD": 1, "ID": 3, "MUNICIPIO": 2, "NOMBRE": "Guadalupe", "CP": 20714, "CONTROL": 31, "SECCION": 338},
        {"ENTIDAD": 1, "ID": 3, "MUNICIPIO": 2, "NOMBRE": "Guadalupe", "CP": 20714, "CONTROL": 31, "SECCION": 339},
    ])
    informe = auditar(catalogo, poligonos)
    assert informe["id_compartido"] == 1
    assert informe["id_y_nombre_iguales"] == 0
    assert informe["compuesto_candidato_unico"] == 1
    assert informe["colonias_ccol_en_varias_secciones"] == 1
    espacial = pd.DataFrame([
        {"ENTIDAD": 1, "ID_poligono": 1, "ID_SECCION": "01-0338", "poblacion_urbana_observada": 20},
        {"ENTIDAD": 1, "ID_poligono": 2, "ID_SECCION": "01-0338", "poblacion_urbana_observada": 10},
    ])
    comparacion = comparar_con_espacial(catalogo, poligonos, espacial)
    assert comparacion["pares_espaciales_comparados"] == 1
    assert comparacion["pares_espaciales_listados_en_ccol_2022"] == 1
