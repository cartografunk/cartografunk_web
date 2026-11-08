import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, box

from scripts.build_casillas_2024_puntos import cruzar_puntos
from scripts.match_ieeq_encartes import normalizar


def test_cruce_acepta_solo_clave_domicilio_y_geometria():
    texto = "ESCUELA PRIMARIA CALLE UNO CERCA DEL PARQUE"
    encarte = pd.DataFrame({
        "ID_SECCION": ["22-0001"] * 4,
        "CASILLA": ["B1", "C1", "E1", "S1"],
        "DOMICILIO_NORMALIZADO": [normalizar(texto), normalizar(texto), "OTRA SEDE", normalizar(texto)],
    })
    puntos = gpd.GeoDataFrame({
        "seccion": [1, 1, 1], "name": ["B", "C1", "E1"],
        "ubicacion": ["ESCUELA PRIMARIA"] * 3,
        "domicilio": ["CALLE UNO"] * 3,
        "referencia": ["CERCA DEL PARQUE"] * 3,
    }, geometry=[Point(-100.45, 20.55), Point(-100.7, 20.55), Point(-100.45, 20.55)], crs=4326)
    secciones = gpd.GeoDataFrame({"ID_SECCION": ["22-0001"]},
                                 geometry=[box(-100.5, 20.5, -100.4, 20.6)], crs=4326)
    result = cruzar_puntos(encarte, puntos, secciones).set_index("CASILLA_ETIQUETA")
    assert len(result) == 3  # Especial S queda fuera del piloto por sección.
    assert result.loc["B1", "CALIDAD"] == "clave_domicilio_y_poligono"
    assert result.loc["C1", "CALIDAD"] == "revisar_domicilio_o_poligono"
    assert result.loc["E1", "CALIDAD"] == "revisar_domicilio_o_poligono"


def test_revision_manual_acepta_e_fuera_si_coordenada_concuerda():
    texto = "ESCUELA CALLE UNO"
    encarte = pd.DataFrame({"ID_SECCION": ["22-0001"], "CASILLA": ["E1"],
                            "DOMICILIO_NORMALIZADO": [texto]})
    puntos = gpd.GeoDataFrame({"seccion": [1], "name": ["E1"],
                               "ubicacion": ["ESCUELA"], "domicilio": ["CALLE UNO"],
                               "referencia": [""]}, geometry=[Point(-100.5001, 20.55)], crs=4326)
    secciones = gpd.GeoDataFrame({"ID_SECCION": ["22-0001"]},
                                 geometry=[box(-100.5, 20.5, -100.4, 20.6)], crs=4326)
    revisiones = pd.DataFrame({"ID_SECCION": ["22-0001"], "CASILLA_ETIQUETA": ["E1"],
                               "LONGITUD_REVISION": [-100.50009], "LATITUD_REVISION": [20.55],
                               "URL_REVISION": ["https://maps.app.goo.gl/ejemplo"]})
    result = cruzar_puntos(encarte, puntos, secciones, revisiones).iloc[0]
    assert result.CALIDAD == "domicilio_y_revision_manual"
    assert result.DISTANCIA_REVISION_M < 2
    assert not result.DENTRO_SECCION


def test_revision_visual_de_sede_aplica_a_b_y_c_sin_cambiar_punto():
    encarte = pd.DataFrame({"ID_SECCION": ["22-0001"] * 2,
                            "CASILLA": ["B1", "C1"],
                            "DOMICILIO_NORMALIZADO": ["DOMICILIO ENCARTE"] * 2})
    puntos = gpd.GeoDataFrame({"seccion": [1, 1], "name": ["B", "C1"],
                               "ubicacion": ["RESTAURANTE"] * 2,
                               "domicilio": ["CALLE UNO"] * 2,
                               "referencia": [""] * 2},
                              geometry=[Point(-100.45, 20.55)] * 2, crs=4326)
    secciones = gpd.GeoDataFrame({"ID_SECCION": ["22-0001"]},
                                 geometry=[box(-100.5, 20.5, -100.4, 20.6)], crs=4326)
    revision = pd.DataFrame({"GRUPO_SEDE": ["SEDE-01"], "ID_SECCION": ["22-0001"],
                             "LATITUD_FUENTE": [20.55], "LONGITUD_FUENTE": [-100.45],
                             "CASILLAS_DEL_GRUPO": ["B1, C1"],
                             "NOTA": ["Domicilio del encarte 2024"]})
    result = cruzar_puntos(encarte, puntos, secciones, revisiones_sitios=revision)
    assert result.CALIDAD.eq("sede_revisada_visual_usuario").all()
    assert result.LONGITUD.eq(-100.45).all()
    assert result.NOTA_REVISION.eq("Domicilio del encarte 2024").all()
