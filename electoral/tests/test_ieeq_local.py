"""Pruebas de la normalización local IEEQ de diputaciones MR."""

from __future__ import annotations

import pandas as pd
import pytest

from scripts.build_ieeq_dip_local import SOURCE, aggregate_sections, build, normalize_casillas


def test_anulada_pierde_votos_pero_conserva_lista_nominal():
    raw = pd.DataFrame([
        {"ID_ESTADO": 22, "ID_DISTRITO_LOCAL": 1, "SECCION": 10,
         "TIPO_CASILLA": "B", "ID_CASILLA": 1, "EXT_CONTIGUA": 0,
         "CASILLA": "B", "PAN": 60, "NUM_VOTOS_VALIDOS": 60,
         "NUM_VOTOS_CAN_NREG": 0, "NUM_VOTOS_NULOS": 0,
         "TOTAL_VOTOS": 60, "LISTA_NOMINAL": 100, "TRIBUNAL": None},
        {"ID_ESTADO": 22, "ID_DISTRITO_LOCAL": 1, "SECCION": 10,
         "TIPO_CASILLA": "C", "ID_CASILLA": 1, "EXT_CONTIGUA": 0,
         "CASILLA": "C01", "PAN": 55, "NUM_VOTOS_VALIDOS": 55,
         "NUM_VOTOS_CAN_NREG": 0, "NUM_VOTOS_NULOS": 0,
         "TOTAL_VOTOS": 55, "LISTA_NOMINAL": 100, "TRIBUNAL": "Anulada"},
        {"ID_ESTADO": 22, "ID_DISTRITO_LOCAL": 1, "SECCION": 10,
         "TIPO_CASILLA": "S", "ID_CASILLA": 1, "EXT_CONTIGUA": 0,
         "CASILLA": "S01", "PAN": 20, "NUM_VOTOS_VALIDOS": 20,
         "NUM_VOTOS_CAN_NREG": 0, "NUM_VOTOS_NULOS": 0,
         "TOTAL_VOTOS": 20, "LISTA_NOMINAL": 0, "TRIBUNAL": None},
    ])
    cas = normalize_casillas(2018, raw)
    sec = aggregate_sections(cas, 2018)
    assert len(sec) == 1
    assert sec.iloc[0][["ID_SECCION", "PAN", "TOTAL_VOTOS", "LISTA_NOMINAL"]].tolist() == ["22-0010", 60, 60, 200]
    assert cas["MOTIVO_EXCLUSION_SECCION"].tolist() == ["", "anulada_tribunal", "especial_sin_residencia_seccional"]


def test_correccion_2024_conserva_seccion_original():
    raw = pd.DataFrame([{
        "ID_ESTADO": 22, "ID_DISTRITO_LOCAL": 10, "SECCION": 861,
        "TIPO_CASILLA": "C", "ID_CASILLA": 3, "EXT_CONTIGUA": 0,
        "TOTAL_VOTOS": 433, "LISTA_NOMINAL": 600, "OBSERVACIONES": None,
    }])
    cas = normalize_casillas(2024, raw)
    assert cas.loc[0, "SECCION"] == 861
    assert cas.loc[0, "SECCION_NORMALIZADA"] == 584
    assert cas.loc[0, "ID_SECCION"] == "22-0584"
    assert "JSON_D10" in cas.loc[0, "CORRECCION_SECCION"]


@pytest.mark.skipif(not (SOURCE / "2018_tablas_resultados.zip").exists(), reason="fuentes IEEQ locales no disponibles")
def test_cotejo_integral_con_fuentes_locales(tmp_path):
    audit = build(output=tmp_path)
    by_year = {row["anio"]: row for row in audit["anios"]}
    assert [(by_year[y]["secciones_bce"], by_year[y]["secciones_con_diferencia_sin_explicar"]) for y in (2018, 2021, 2024)] == [(860, 0), (891, 0), (953, 0)]
    assert by_year[2018]["celdas_voto_nominal_distintas_de_tabla_seccional"] == 0
    assert by_year[2021]["celdas_voto_nominal_distintas_de_tabla_seccional"] == 0
    assert by_year[2024]["votos_bce_mas_anticipado_y_especiales_mr"] == by_year[2024]["votos_mr_portal"]
    assert by_year[2018]["diferencia_distrito_menos_seccion"] == 1
    assert (by_year[2024]["filas_con_sentencia_posterior"], by_year[2024]["votos_en_filas_con_sentencia_posterior"]) == (6, 1870)
    cotejo = pd.read_csv(tmp_path / "dip_local_mr_2024_cotejo_seccion.csv")
    flagged = cotejo.loc[cotejo["ID_SECCION"].eq("22-0727")].iloc[0]
    assert flagged["INSTALACION_CASILLA_ESPECIAL"]
    assert flagged["DIF_PUBLICADO_MENOS_BCE"] == 52
