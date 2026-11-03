import geopandas as gpd
import pytest
from shapely import get_num_coordinates
from shapely.geometry import MultiPolygon, Polygon

from electoral.geometria import cargar_geometria


@pytest.fixture
def gpkg(tmp_path):
    poligono = MultiPolygon([Polygon([
        (499000, 2200000), (499500, 2200000), (500000, 2200000),
        (500000, 2201000), (499000, 2201000), (499000, 2200000),
    ])])
    origen = gpd.GeoDataFrame({
        "ENTIDAD": [1], "DISTRITO": [2], "DISTRITO_L": [3],
        "MUNICIPIO": [4], "SECCION": [5], "TIPO": [6], "geometry": [poligono],
    }, crs=4326)
    ruta = tmp_path / "secciones.gpkg"
    origen.to_file(ruta, layer="SECCIONES_2024", driver="GPKG")
    return ruta


def test_formato_crs_y_columnas(gpkg):
    resultado = cargar_geometria(gpkg, tolerancia_m=0)
    assert resultado.crs.to_epsg() == 4326
    assert resultado.ID_SECCION.tolist() == ["01-0005"]
    assert resultado.columns.tolist() == [
        "ID_SECCION", "ENTIDAD", "DISTRITO", "DISTRITO_L", "MUNICIPIO", "TIPO", "geometry"
    ]


def test_set_crs_no_altera_coordenadas_y_tolerancia_cero_conserva_vertices(gpkg):
    original = gpd.read_file(gpkg, layer="SECCIONES_2024")
    redefinida = original.set_crs(32614, allow_override=True)
    assert original.geometry.iloc[0].equals_exact(redefinida.geometry.iloc[0], 0)
    resultado = cargar_geometria(gpkg, tolerancia_m=0)
    assert get_num_coordinates(resultado.geometry.iloc[0]) == get_num_coordinates(original.geometry.iloc[0])
    assert resultado.to_crs(32614).geometry.iloc[0].equals_exact(original.geometry.iloc[0], 1e-6)


def test_tolerancia_negativa(gpkg):
    with pytest.raises(ValueError):
        cargar_geometria(gpkg, tolerancia_m=-1)
