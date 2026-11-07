"""Casos geométricos que evitan declarar estabilidad por mera coincidencia de clave."""

import geopandas as gpd
import pytest
from shapely.geometry import box

from scripts.audit_ieeq_judicial_2024 import audit as audit_judicial
from scripts.build_ieeq_crosswalk import compare


def geo(rows):
    return gpd.GeoDataFrame(
        {"ID_SECCION": [key for key, _ in rows]},
        geometry=[shape for _, shape in rows], crs="EPSG:3857"
    )


def test_misma_clave_con_limite_cambiado_no_es_estable():
    old = geo([("22-0001", box(0, 0, 10, 10))])
    new = geo([("22-0001", box(0, 0, 9, 10))])
    _, states = compare(old, new)
    assert states.iloc[0].CATEGORIA == "modificada_o_renumerada"
    assert states.iloc[0].IOU_MISMA_CLAVE == 0.9


def test_division_y_fusion_se_reconocen_por_area():
    old = geo([("22-0001", box(0, 0, 10, 10))])
    split = geo([("22-0001", box(0, 0, 5, 10)), ("22-0002", box(5, 0, 10, 10))])
    edges, states = compare(old, split)
    assert len(edges) == 2
    assert set(states.CATEGORIA) == {"dividida_o_reconfigurada"}
    _, fused = compare(split, old)
    assert fused.iloc[0].CATEGORIA == "fusionada_o_reconfigurada"


def test_sin_superposicion_es_nueva_y_geometria_identica_estable():
    old = geo([("22-0001", box(0, 0, 1, 1))])
    new = geo([("22-0001", box(0, 0, 1, 1)), ("22-0002", box(2, 0, 3, 1))])
    _, states = compare(old, new)
    assert states.set_index("ID_SECCION").loc["22-0001", "CATEGORIA"] == "sin_cambio_cartografico_referencia"
    assert states.set_index("ID_SECCION").loc["22-0002", "CATEGORIA"] == "nueva_sin_superposicion"


@pytest.mark.skipif(
    not __import__("pathlib").Path("data/electoral/ieeq_local/dip_local_mr_2024_casilla.parquet").exists(),
    reason="datos locales IEEQ no disponibles",
)
def test_sentencia_cuadra_totales_sin_votos_especiales_rp(tmp_path):
    from pathlib import Path

    source = Path("data/electoral/ieeq_local")
    for name in ("dip_local_mr_2024_casilla.parquet", "dip_local_mr_2024_especial_mr.parquet"):
        (tmp_path / name).write_bytes((source / name).read_bytes())
    result = audit_judicial(tmp_path)
    assert result["casillas_corregidas"] == 6
    assert result["votos_en_seis_casillas"] == 1870
    assert result["distrito_7_total"] == 67452
