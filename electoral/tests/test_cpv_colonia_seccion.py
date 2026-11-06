"""Garantías de no duplicación y suma de conteos en el piloto espacial."""

import geopandas as gpd
import pandas as pd
from shapely.geometry import box
import zipfile

from electoral.cpv import VARIABLES
from scripts.build_cpv_colonia_seccion import _asignar_puntos, _leer_cpv, _sumar_tasas


def test_solapamiento_no_duplica_manzana():
    manzanas = gpd.GeoDataFrame(
        {"CVEGEO": ["1", "2"]}, geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)], crs=4326
    )
    colonias = gpd.GeoDataFrame(
        {"ID_COLONIA_LOCAL": ["A", "B"]},
        geometry=[box(-1, -1, 1.5, 2), box(0, -1, 4, 2)], crs=4326,
    )
    asignadas, ambiguas = _asignar_puntos(manzanas, colonias, "ID_COLONIA_LOCAL")
    assert ambiguas == 1
    assert pd.isna(asignadas.iloc[0])
    assert asignadas.iloc[1] == "B"


def test_tasas_suman_conteos_y_no_promedian_porcentajes():
    columnas = {c for _, _, n, d in VARIABLES for c in (n, d) if c != "P_0A17"}
    cpv = pd.DataFrame({c: [0, 0] for c in columnas})
    cpv["ID_SECCION"] = ["01-0001", "01-0001"]
    cpv["POBTOT"] = [10, 90]
    cpv["POBFEM"] = [10, 0]
    cpv["P_18YMAS"] = [5, 80]
    cpv["VIVPAR_HAB"] = [1, 9]
    salida = _sumar_tasas(cpv, ["ID_SECCION"])
    assert salida.loc[0, "pct_mujeres"] == 10
    assert salida.loc[0, "pct_menores_18"] == 15
    assert salida.loc[0, "manzanas_cpv"] == 2
    cpv["POBFEM"] = cpv["POBFEM"].astype(object)
    cpv.loc[1, "POBFEM"] = "*"
    assert pd.isna(_sumar_tasas(cpv, ["ID_SECCION"]).loc[0, "pct_mujeres"])


def test_zip_con_bitacora_y_latin1(tmp_path):
    archivo = tmp_path / "cpv.zip"
    columnas = {c for _, _, n, d in VARIABLES for c in (n, d) if c != "P_0A17"}
    fila = {c: "0" for c in columnas}
    fila.update(ENTIDAD="14", MUN="001", LOC="0001", AGEB="0017", MZA="001", NOM_LOC="Mérida")
    contenido = pd.DataFrame([fila]).to_csv(index=False).encode("latin1")
    with zipfile.ZipFile(archivo, "w") as z:
        z.writestr("conjunto_de_datos/bitacora_cambios_ageb_urbana_14.csv", "cambio\n1\n")
        z.writestr("conjunto_de_datos/conjunto_de_datos_ageb_urbana_14_cpv2020.csv", contenido)
    cpv = _leer_cpv(archivo, "14")
    assert cpv.CVEGEO.tolist() == ["1400100010017001"]
