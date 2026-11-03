from zipfile import ZipFile

import pandas as pd
import pytest

from electoral.casillas import LLAVE_CASILLA, cargar_casillas
from electoral.clasificacion import clasificar
from electoral.config import CANDIDATURAS
from electoral.rentabilidad import rentabilidad


@pytest.fixture
def casillas_zip(tmp_path):
    votos = {columna: 0 for grupo in CANDIDATURAS.values() for columna in grupo}
    filas = []
    for seccion, tipo, acta, tribunal, validos, nominal, propios in (
        (821, "B", "B", "", 10, 20, {"PAN": 6, "MORENA": 4}),
        (821, "B", "B2", "", 10, 20, {"PAN": 4, "MORENA": 6}),
        (821, "S", "S01", "", 5, 0, {"MORENA": 5}),
        (0, "MEC", "VMRE01", "", 3, 0, {"MC": 3}),
        (821, "C", "C01", "ANULADA", 2, 20, {"PAN": 2}),
    ):
        filas.append({
            "ID_ESTADO": 14, "SECCION": seccion, "TIPO_CASILLA": tipo,
            "ID_CASILLA": 1, "EXT_CONTIGUA": 0, "ACTA_CASILLA-MEC": acta,
            "TRIBUNAL": tribunal, "NUM_VOTOS_VALIDOS": validos,
            "TOTAL_VOTOS": validos, "LISTA_NOMINAL": nominal,
            **{**votos, **propios},
        })
    ruta = tmp_path / "presidencia.zip"
    with ZipFile(ruta, "w") as archivo:
        archivo.writestr("2024_SEE_PRE_NAL_CAS.csv", pd.DataFrame(filas).to_csv(index=False).encode("cp1252"))
    return ruta


def test_carga_llave_estados_y_anuladas(casillas_zip):
    d = cargar_casillas(casillas_zip)
    assert len(d) == 4
    assert d.attrs["n_anuladas"] == 1
    assert d[list(LLAVE_CASILLA)].duplicated().sum() == 0
    assert d["ID_CASILLA_LEGIBLE"].is_unique
    assert d.loc[d["ACTA_CASILLA-MEC"].eq("B"), "ID_CASILLA_LEGIBLE"].iloc[0] == "14-0821-B-1-0-B"
    assert d["estado"].value_counts().to_dict() == {"con_resultado": 3, "extranjero": 1}
    assert d.loc[d["TIPO_CASILLA"].eq("S"), "votos_en_lista"].isna().all()
    assert d.loc[d["TIPO_CASILLA"].eq("S"), "cand_PVEM_PT_MORENA"].iloc[0] == 5


def test_rentabilidad_y_clase_sin_abstencion_en_s(casillas_zip):
    d = cargar_casillas(casillas_zip)
    candidaturas = [f"cand_{nombre}" for nombre in CANDIDATURAS]
    r = clasificar(rentabilidad(d, candidaturas, "cand_PVEM_PT_MORENA"))
    especial = r.loc[r["TIPO_CASILLA"].eq("S")].iloc[0]
    assert especial["resultado"] == "ganada"
    assert pd.isna(especial["abstencion"])
    assert pd.isna(especial["participacion_pct"])
    assert pd.isna(r.loc[r["estado"].eq("extranjero"), "clase"].iloc[0])


def test_llave_duplicada_rechazada(casillas_zip, tmp_path):
    with ZipFile(casillas_zip) as archivo:
        d = pd.read_csv(archivo.open("2024_SEE_PRE_NAL_CAS.csv"))
    d = pd.concat([d, d.iloc[[0]]], ignore_index=True)
    ruta = tmp_path / "duplicada.zip"
    with ZipFile(ruta, "w") as archivo:
        archivo.writestr("2024_SEE_PRE_NAL_CAS.csv", d.to_csv(index=False).encode("cp1252"))
    with pytest.raises(ValueError, match="duplicada"):
        cargar_casillas(ruta)
