"""La ficha ubica la sección y no inventa coordenadas de casilla."""

import geopandas as gpd
from shapely.geometry import box
from streamlit.testing.v1 import AppTest

from electoral.diagnostico_casillas_tab import _cargar_geometria_seccion


def test_poligono_seccional_se_lee_por_clave(tmp_path):
    archivo = tmp_path / "secciones.parquet"
    gpd.GeoDataFrame({"ID_SECCION": ["22-0001", "22-0002"]},
                     geometry=[box(-100.5, 20.5, -100.4, 20.6),
                               box(-100.6, 20.6, -100.5, 20.7)], crs=4326).to_parquet(archivo)
    salida = _cargar_geometria_seccion(archivo, "22-0001")
    assert salida is not None
    geojson, limites = salida
    assert len(geojson["features"]) == 1
    assert geojson["features"][0]["properties"]["ID_SECCION"] == "22-0001"
    assert limites == (-100.5, 20.5, -100.4, 20.6)
    assert _cargar_geometria_seccion(archivo, "22-9999") is None


def test_ficha_muestra_poligono_y_otras_casillas_sin_punto(tmp_path):
    archivo = tmp_path / "secciones.parquet"
    gpd.GeoDataFrame({"ID_SECCION": ["22-0001"]},
                     geometry=[box(-100.5, 20.5, -100.4, 20.6)], crs=4326).to_parquet(archivo)
    script = (
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "import electoral.diagnostico_casillas_tab as tab\n"
        f"tab.GEOMETRIA_PARQUET = Path({str(archivo)!r})\n"
        "base = pd.DataFrame({'ID_SECCION':['22-0001','22-0001'], "
        "'CASILLA_ETIQUETA':['B1','C1'], 'LOCALIDAD_INSTALACION':['CENTRO','CENTRO'], "
        "'VOTOS_PARTIDO':[120.,110.], 'VOTOS_RIVAL':[100.,105.], "
        "'MARGEN_PP':[5.,1.], 'CLASE':['ganada_ajustada','ganada_ajustada'], "
        "'PERFIL_CPV':[1,1], 'RASGOS_CPV_SECCION':['Más Internet','Más Internet'], "
        "'TIPO_REVISION':['Defender ventaja cercana']*2, "
        "'MOTIVO_REVISION':['Ventaja cercana']*2})\n"
        "tab._mostrar_ficha_casilla(base.iloc[0], base)\n"
    )
    at = AppTest.from_string(script).run(timeout=180)
    assert not at.exception
    assert any("Sección 22-0001 · casilla B1" in x.value for x in at.subheader)
    assert any("no se coloca un punto aproximado" in x.value for x in at.caption)
    assert at.dataframe[0].value.Casilla.tolist() == ["B1", "C1"]
