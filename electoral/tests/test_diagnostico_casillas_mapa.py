"""La ficha ubica secciones y sólo muestra puntos cotejados."""

import geopandas as gpd
from shapely.geometry import box
from streamlit.testing.v1 import AppTest

from electoral.diagnostico_casillas_tab import _cargar_geometria_seccion, _cargar_punto_casilla


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
        f"tab._mostrar_ficha_casilla(base.iloc[0], base, Path({str(tmp_path / 'ausente.parquet')!r}))\n"
    )
    at = AppTest.from_string(script).run(timeout=180)
    assert not at.exception
    assert any("Sección 22-0001 · casilla B1" in x.value for x in at.subheader)
    assert any("no tiene un punto" in x.value for x in at.caption)
    assert at.dataframe[0].value.Casilla.tolist() == ["B1", "C1"]


def test_cargar_punto_solo_si_paso_cotejo(tmp_path):
    import pandas as pd

    archivo = tmp_path / "puntos.parquet"
    pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0001"], "CASILLA_ETIQUETA": ["B1", "C1"],
        "CALIDAD": ["clave_domicilio_y_poligono", "revisar_domicilio_o_poligono"],
        "LONGITUD": [-100.45, -100.46], "LATITUD": [20.55, 20.56],
        "SEDE": ["Escuela", "Otra"], "DOMICILIO_FUENTE": ["Calle 1", "Calle 2"],
        "URL_REVISION": ["", ""]
    }).to_parquet(archivo)
    assert _cargar_punto_casilla(archivo, "22-0001", "B1")["SEDE"] == "Escuela"
    assert _cargar_punto_casilla(archivo, "22-0001", "C1") is None
    assert _cargar_punto_casilla(archivo, "22-0002", "B1") is None


def test_cargar_punto_con_revision_manual(tmp_path):
    import pandas as pd

    archivo = tmp_path / "puntos.parquet"
    pd.DataFrame({"ID_SECCION": ["22-0001"], "CASILLA_ETIQUETA": ["E1"],
                  "CALIDAD": ["domicilio_y_revision_manual"], "LONGITUD": [-100.5001],
                  "LATITUD": [20.55], "SEDE": ["Escuela"],
                  "DOMICILIO_FUENTE": ["Calle Uno"],
                  "URL_REVISION": ["https://maps.app.goo.gl/ejemplo"]}).to_parquet(archivo)
    punto = _cargar_punto_casilla(archivo, "22-0001", "E1")
    assert punto["CALIDAD"] == "domicilio_y_revision_manual"
    assert punto["URL_REVISION"].endswith("ejemplo")


def test_ficha_muestra_sede_cotejada(tmp_path):
    import pandas as pd

    poligono = tmp_path / "secciones.parquet"
    puntos = tmp_path / "puntos.parquet"
    gpd.GeoDataFrame({"ID_SECCION": ["22-0001"]},
                     geometry=[box(-100.5, 20.5, -100.4, 20.6)], crs=4326).to_parquet(poligono)
    pd.DataFrame({"ID_SECCION": ["22-0001"], "CASILLA_ETIQUETA": ["B1"],
                  "CALIDAD": ["clave_domicilio_y_poligono"], "LONGITUD": [-100.45],
                  "LATITUD": [20.55], "SEDE": ["Escuela Uno"],
                  "DOMICILIO_FUENTE": ["Calle Uno"], "URL_REVISION": [""]}).to_parquet(puntos)
    script = (
        "from pathlib import Path\nimport pandas as pd\n"
        "import electoral.diagnostico_casillas_tab as tab\n"
        f"tab.GEOMETRIA_PARQUET = Path({str(poligono)!r})\n"
        "base = pd.DataFrame({'ID_SECCION':['22-0001'], 'CASILLA_ETIQUETA':['B1'], "
        "'LOCALIDAD_INSTALACION':['CENTRO'], 'VOTOS_PARTIDO':[120.], "
        "'VOTOS_RIVAL':[100.], 'MARGEN_PP':[5.], 'CLASE':['ganada_ajustada'], "
        "'PERFIL_CPV':[None], 'TIPO_REVISION':[''], 'ACCION_HIPOTESIS':['Explorar']})\n"
        f"tab._mostrar_ficha_casilla(base.iloc[0], base, Path({str(puntos)!r}))\n"
    )
    at = AppTest.from_string(script).run(timeout=180)
    assert not at.exception
    assert any("Escuela Uno" in x.value for x in at.markdown)
    assert any("No representa el domicilio" in x.value for x in at.caption)
