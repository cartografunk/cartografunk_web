from zipfile import ZipFile

import pandas as pd
import pytest

from electoral.config import CANDIDATURAS, PRESIDENCIA_ZIP
from electoral.datos import cargar_sec


@pytest.fixture(scope="module")
def presidencia():
    if not PRESIDENCIA_ZIP.is_file():
        pytest.skip(f"ZIP no encontrado: {PRESIDENCIA_ZIP}")
    return cargar_sec(PRESIDENCIA_ZIP)


def test_estados_e_id_unico(presidencia):
    assert len(presidencia) == 70_536
    assert presidencia["ID_SECCION"].is_unique
    assert presidencia["estado"].value_counts().to_dict() == {
        "con_resultado": 70_448,
        "sin_resultado": 56,
        "extranjero": 32,
    }
    assert presidencia.loc[presidencia["SECCION"].eq(0), "ID_SECCION"].nunique() == 32
    assert presidencia.loc[presidencia["ID_ESTADO"].eq(1) & presidencia["SECCION"].eq(0), "ID_SECCION"].iloc[0] == "01-0000"


def test_totales_y_columnas_originales(presidencia):
    assert presidencia[[f"cand_{nombre}" for nombre in CANDIDATURAS]].sum().to_dict() == {
        "cand_PAN_PRI_PRD": 16_502_697,
        "cand_PVEM_PT_MORENA": 35_924_519,
        "cand_MC": 6_204_710,
    }
    for nombre, columnas in CANDIDATURAS.items():
        esperado = presidencia[list(columnas)].sum(axis=1, min_count=1)
        pd.testing.assert_series_equal(
            presidencia[f"cand_{nombre}"], esperado, check_names=False
        )
    assert "CIRCUNSCRIPCION" in presidencia.columns
    assert "TOTAL_VOTOS" in presidencia.columns


def test_candidaturas_cuadran_con_votos_validos_con_resultado(presidencia):
    con_resultado = presidencia.loc[presidencia["estado"].eq("con_resultado")]
    suma = con_resultado[[f"cand_{nombre}" for nombre in CANDIDATURAS]].sum(axis=1)
    assert suma.eq(con_resultado["NUM_VOTOS_VALIDOS"]).all()


def test_codificacion_y_estado_con_votos_totales(tmp_path):
    zip_path = tmp_path / "ejemplo.zip"
    columnas = [
        "ID_ESTADO", "SECCION", "NUM_VOTOS_VALIDOS", "TOTAL_VOTOS", "MUNICIPIO",
        *dict.fromkeys(columna for grupo in CANDIDATURAS.values() for columna in grupo),
    ]
    filas = [
        [1, 0, 5, 5, "VOTO EN EL EXTRANJERO", *([0] * (len(columnas) - 5))],
        [1, 1, 0, 12, "ACUÑA", *([0] * (len(columnas) - 5))],
        [1, 2, 7, 7, "ACUÑA", *([1] * (len(columnas) - 5))],
    ]
    origen = pd.DataFrame(filas, columns=columnas)
    with ZipFile(zip_path, "w") as archivo:
        archivo.writestr("2024_SEC.csv", b"\xef\xbb\xbf" + origen.to_csv(index=False).encode("cp1252"))
        cas = pd.DataFrame({
            "ID_ESTADO": [1, 1, 1],
            "SECCION": [1, 2, 2],
            "TIPO_CASILLA": ["S", "S", "S"],
            "TOTAL_VOTOS": [3, 2, 4],
            "TRIBUNAL": [None, None, "ANULADA"],
        })
        archivo.writestr("2024_CAS.csv", b"\xef\xbb\xbf" + cas.to_csv(index=False).encode("cp1252"))

    sec = cargar_sec(zip_path)
    assert sec["ID_SECCION"].tolist() == ["01-0000", "01-0001", "01-0002"]
    assert sec["estado"].tolist() == ["extranjero", "sin_resultado", "con_resultado"]
    pd.testing.assert_frame_equal(sec[columnas], origen)
    assert sec["votos_casillas_s"].tolist() == [0, 3, 2]
    assert sec["n_casillas_s"].tolist() == [0, 1, 1]
    assert pd.isna(sec.loc[0, "votos_en_lista"])
    assert pd.isna(sec.loc[1, "votos_en_lista"])
    assert sec.loc[2, "votos_en_lista"] == 5
