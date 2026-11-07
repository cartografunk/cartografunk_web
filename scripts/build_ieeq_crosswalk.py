"""Audita superposición seccional de Querétaro; nunca infiere equivalencia por ID solo.

El ZIP de Pautas 2019 es referencia, no cartografía confirmada del día de 2018.
El SHP ECEG es el marco declarado del 20 de enero de 2021.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/electoral/fuentes_ine"
OUTPUT = ROOT / "data/electoral/ieeq_local"
OLD_ZIPS = {
    "referencia_2019": SOURCE / "ine_seccion_vigencia_2020_2021.zip",
    "eceg_2021_01_20": SOURCE / "eceg_qro_20210120_inner.zip",
}
CURRENT = SOURCE / "SECCIONES_2024_raw.gpkg"
STABLE_IOU = 0.995
LINK_FRACTION = 0.01
MIN_COVERAGE_FOR_ML = 0.70


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_old(path: Path) -> gpd.GeoDataFrame:
    read_path = path
    if path.name == "eceg_qro_20210120_inner.zip":
        read_path = "/vsizip/" + path.resolve().as_posix() + "/22_QUERETARO/Seccion.shp"
    info = pyogrio.read_info(read_path)
    cols = set(info["fields"])
    entity = "ENTIDAD" if "ENTIDAD" in cols else "entidad"
    section = "SECCION" if "SECCION" in cols else "seccion"
    frame = pyogrio.read_dataframe(read_path, where=f"{entity} = 22")
    frame["ID_SECCION"] = "22-" + frame[section].astype(int).astype(str).str.zfill(4)
    frame = frame[["ID_SECCION", "geometry"]].copy()
    if frame.ID_SECCION.duplicated().any():
        raise ValueError(f"Claves duplicadas: {path}")
    return frame


def compare(source: gpd.GeoDataFrame, target: gpd.GeoDataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve vínculos por área y estado de cada sección destino.

    Un borde que sólo toca otra sección no crea vínculo. Una sección se rotula
    estable únicamente con la misma clave y una intersección/unión >= 0.995.
    """
    if source.crs != target.crs:
        target = target.to_crs(source.crs)
    source = source.reset_index(drop=True).copy()
    target = target.reset_index(drop=True).copy()
    source.geometry = source.geometry.make_valid()
    target.geometry = target.geometry.make_valid()
    if source.ID_SECCION.duplicated().any() or target.ID_SECCION.duplicated().any():
        raise ValueError("ID_SECCION duplicado")
    source_area = source.geometry.area.to_numpy()
    target_area = target.geometry.area.to_numpy()
    links = []
    for j, geom in enumerate(target.geometry):
        for i in source.sindex.query(geom, predicate="intersects"):
            area = source.geometry.iloc[i].intersection(geom).area
            if area <= 0 or source_area[i] <= 0 or target_area[j] <= 0:
                continue
            fs, ft = area / source_area[i], area / target_area[j]
            if max(fs, ft) < LINK_FRACTION:
                continue
            links.append({
                "ORIGEN": source.ID_SECCION.iloc[i], "DESTINO": target.ID_SECCION.iloc[j],
                "AREA_INTERSECCION_M2": area, "FRACCION_ORIGEN": fs,
                "FRACCION_DESTINO": ft,
            })
    edges = pd.DataFrame(links, columns=[
        "ORIGEN", "DESTINO", "AREA_INTERSECCION_M2", "FRACCION_ORIGEN", "FRACCION_DESTINO"
    ])
    from_degree = edges.groupby("ORIGEN").size().to_dict()
    to_degree = edges.groupby("DESTINO").size().to_dict()
    by_target = {key: group for key, group in edges.groupby("DESTINO")}
    states = []
    for j, key in enumerate(target.ID_SECCION):
        group = by_target.get(key)
        if group is None:
            category, iou = "nueva_sin_superposicion", 0.0
        else:
            same = group.loc[group.ORIGEN.eq(key)]
            if len(same):
                row = same.iloc[0]
                i = source.index[source.ID_SECCION.eq(key)][0]
                union = source_area[i] + target_area[j] - row.AREA_INTERSECCION_M2
                iou = row.AREA_INTERSECCION_M2 / union if union else 0.0
            else:
                iou = 0.0
            if len(group) == 1 and len(same) == 1 and iou >= STABLE_IOU:
                category = "sin_cambio_cartografico_referencia"
            elif len(group) > 1:
                category = "fusionada_o_reconfigurada"
            elif from_degree[group.iloc[0].ORIGEN] > 1:
                category = "dividida_o_reconfigurada"
            else:
                category = "modificada_o_renumerada"
        states.append({"ID_SECCION": key, "CATEGORIA": category, "IOU_MISMA_CLAVE": iou,
                       "ORIGENES_SUPERPUESTOS": to_degree.get(key, 0)})
    return edges, pd.DataFrame(states)


def build(output: Path = OUTPUT) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    years = {name: load_old(path) for name, path in OLD_ZIPS.items()}
    # El GPKG declara EPSG:4326, pero sus coordenadas están en metros UTM.
    # Se conserva este supuesto explícito y se comprueba su alineación geométrica
    # contra el SHP INE 2021; no se usa el GeoParquet simplificado para la prueba.
    current = pyogrio.read_dataframe(CURRENT, layer="SECCIONES_2024", where="ENTIDAD = 22")
    current = current.set_crs(32614, allow_override=True)
    current["ID_SECCION"] = "22-" + current.SECCION.astype(int).astype(str).str.zfill(4)
    current = current[["ID_SECCION", "geometry"]].copy()
    expected = {
        "referencia_2019": pd.read_parquet(output / "dip_local_mr_2018_seccion_bce.parquet", columns=["ID_SECCION"]),
        "eceg_2021_01_20": pd.read_parquet(output / "dip_local_mr_2021_seccion_bce.parquet", columns=["ID_SECCION"]),
        "2024": pd.read_parquet(output / "dip_local_mr_2024_seccion_bce.parquet", columns=["ID_SECCION"]),
    }
    for label, frame in {**years, "2024": current}.items():
        if set(frame.ID_SECCION) != set(expected[label].ID_SECCION):
            raise ValueError(f"Claves de geometria y votos difieren: {label}")
    cpv = pd.read_parquet(ROOT / "data/electoral/eceg_2020_seccion.parquet", columns=["ID_SECCION"])
    cpv_qro = set(cpv.loc[cpv.ID_SECCION.str.startswith("22-"), "ID_SECCION"])
    if set(years["eceg_2021_01_20"].ID_SECCION) != cpv_qro:
        raise ValueError("El SHP ECEG y la tabla censal de Querétaro no tienen las mismas secciones")
    frames = [years["referencia_2019"], years["eceg_2021_01_20"], current]
    names = ["referencia_2019_a_eceg_2021", "eceg_2021_a_2024"]
    audit = {"fuentes": {}, "comparaciones": [], "umbral_iou": STABLE_IOU,
             "umbral_cobertura_nominal_ml": MIN_COVERAGE_FOR_ML,
             "advertencia": "El SHP ECEG tiene corte declarado 20-ene-2021. El ZIP 2019 no acredita marco exacto de la jornada 2018. CRS original GPKG 2024 es incorrecto."}
    for label, path in OLD_ZIPS.items():
        read_path = path if label != "eceg_2021_01_20" else "/vsizip/" + path.resolve().as_posix() + "/22_QUERETARO/Seccion.shp"
        audit["fuentes"][label] = {"ruta": str(path.relative_to(ROOT)), "sha256": sha256(path),
                                    "dbf_date_last_update": pyogrio.read_info(read_path)["layer_metadata"].get("DBF_DATE_LAST_UPDATE"),
                                    "secciones_qro": len(years[label])}
    audit["fuentes"]["2024"] = {"ruta": str(CURRENT.relative_to(ROOT)), "sha256": sha256(CURRENT),
                                  "secciones_qro": len(current), "crs_original_no_verificado": True,
                                  "crs_trabajo": "EPSG:32614 inferido; GPKG declara EPSG:4326 con coordenadas metricas"}
    states = []
    for name, src, dst in zip(names, frames[:-1], frames[1:]):
        edges, status = compare(src, dst)
        edges.to_parquet(output / f"crosswalk_{name}.parquet", index=False)
        status.to_parquet(output / f"estado_{name}.parquet", index=False)
        status["COMPARACION"] = name
        states.append(status)
        audit["comparaciones"].append({"nombre": name, "origen": len(src), "destino": len(dst),
                                       "vinculos": len(edges), "categorias": status.CATEGORIA.value_counts().to_dict()})
    # El estado del destino 2024 incluye el antecedente 2019 por la misma clave,
    # pero sólo como referencia: nunca reemplaza una cartografía electoral exacta.
    a, b = states
    merged = b.merge(a[["ID_SECCION", "CATEGORIA"]].rename(columns={"CATEGORIA": "CATEGORIA_2019_A_2021"}),
                     on="ID_SECCION", how="left")
    merged["ESTABLE_EN_AMBAS_REFERENCIAS"] = (
        merged.CATEGORIA.eq("sin_cambio_cartografico_referencia")
        & merged.CATEGORIA_2019_A_2021.eq("sin_cambio_cartografico_referencia")
    )
    sec24 = pd.read_parquet(output / "dip_local_mr_2024_seccion_bce.parquet",
                            columns=["ID_SECCION", "LISTA_NOMINAL"])
    merged = merged.merge(sec24, on="ID_SECCION", how="left", validate="one_to_one")
    merged.to_parquet(output / "crosswalk_qro_2018_2021_2024_referencias.parquet", index=False)
    nom = merged.LISTA_NOMINAL.sum()
    stable_nom = merged.loc[merged.ESTABLE_EN_AMBAS_REFERENCIAS, "LISTA_NOMINAL"].sum()
    coverage = float(stable_nom / nom) if nom else None
    audit["cobertura_referencias"] = {"secciones_estables": int(merged.ESTABLE_EN_AMBAS_REFERENCIAS.sum()),
                                      "secciones_2024": len(merged), "lista_nominal_estable": int(stable_nom),
                                      "lista_nominal_total": int(nom),
                                      "fraccion_nominal": coverage,
                                      "cumple_umbral_nominal": bool(coverage is not None and coverage >= MIN_COVERAGE_FOR_ML),
                                      "go_ml": False,
                                      "motivo_no_go": "Cobertura triple inferior al 70 por ciento; falta corte cartografico exacto de la jornada 2018."}
    b2024 = merged.CATEGORIA.eq("sin_cambio_cartografico_referencia")
    audit["cobertura_eceg_2024"] = {
        "secciones_estables": int(b2024.sum()),
        "secciones_total": len(merged),
        "lista_nominal_estable": int(merged.loc[b2024, "LISTA_NOMINAL"].sum()),
        "lista_nominal_total": int(nom),
    }
    stable_2024_iou = merged.loc[b2024, "IOU_MISMA_CLAVE"]
    audit["cobertura_eceg_2024"]["iou_estables"] = {
        "min": float(stable_2024_iou.min()),
        "p01": float(stable_2024_iou.quantile(.01)),
        "mediana": float(stable_2024_iou.median()),
        "p99": float(stable_2024_iou.quantile(.99)),
        "max": float(stable_2024_iou.max()),
    }
    sec21 = pd.read_parquet(output / "dip_local_mr_2021_seccion_bce.parquet",
                            columns=["ID_SECCION", "LISTA_NOMINAL"])
    a_nom = a.merge(sec21, on="ID_SECCION", how="left", validate="one_to_one")
    a_stable = a_nom.CATEGORIA.eq("sin_cambio_cartografico_referencia")
    audit["cobertura_referencia_2019_eceg_2021"] = {
        "secciones_estables": int(a_stable.sum()),
        "secciones_total": len(a_nom),
        "lista_nominal_estable": int(a_nom.loc[a_stable, "LISTA_NOMINAL"].sum()),
        "lista_nominal_total": int(a_nom.LISTA_NOMINAL.sum()),
    }
    audit["cotejo_claves"] = {"2018_votos_con_referencia_2019": len(expected["referencia_2019"]),
                              "2021_votos_con_marco_eceg": len(expected["eceg_2021_01_20"]),
                              "eceg_censo_con_marco": len(cpv_qro),
                              "2024_votos_con_geometria": len(expected["2024"])}
    sample = pd.concat([
        group.sample(n=min(5, len(group)), random_state=20241107)
        for _, group in merged.groupby("CATEGORIA")
    ])
    sample.to_csv(output / "crosswalk_muestra_revision.csv", index=False)
    (output / "auditoria_crosswalk_referencias.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
