import geopandas as gpd
from shapely.geometry import box

from electoral.limites import limites_estado


def test_limites_municipales_y_contorno_estatal_seleccionados_por_clave():
    entidades = gpd.GeoDataFrame(
        {"cvegeo": ["14", "22"]},
        geometry=[box(-104, 19, -102, 21), box(-101, 20, -99, 22)],
        crs=4326,
    )
    municipios = gpd.GeoDataFrame(
        {"cvegeo": ["14001", "14002", "22001"]},
        geometry=[box(-104, 19, -103, 21), box(-103, 19, -102, 21), box(-101, 20, -99, 22)],
        crs=4326,
    )
    estatal, municipales, punto, n = limites_estado(entidades, municipios, 14)
    assert n == 2
    assert [f["properties"]["cvegeo"] for f in estatal["features"]] == ["14"]
    assert {f["properties"]["cvegeo"] for f in municipales["features"]} == {"14001", "14002"}
    assert -104 < punto[0] < -102 and 19 < punto[1] < 21
