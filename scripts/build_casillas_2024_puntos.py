"""Cruza sedes puntuales 2024 con el encarte IEEQ por sección y casilla.

El punto indica dónde se instaló la mesa, no el domicilio de sus electores.
El GeoPackage procede de una copia de Ubica tu Casilla publicada por Morlan.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from pyproj import Geod

from electoral.config import GEOMETRIA_PARQUET
from scripts.match_ieeq_encartes import normalizar


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/electoral/fuentes_ine/casillas_ine_morlan_2024.gpkg"
ENCARTE = ROOT / "data/electoral/ieeq_local/encarte_qro_2024_claves.parquet"
OUTPUT = ROOT / "data/electoral/ieeq_local/casillas_2024_puntos.parquet"
AUDIT = ROOT / "data/electoral/ieeq_local/casillas_2024_puntos.audit.json"
REVISIONES = ROOT / "electoral/revisiones_sedes_2024.csv"
SOURCE_URL = ("https://datamx.io/dataset/985fceef-1d7b-49ed-8098-a5bc182462d2/"
              "resource/50f1cc66-c303-4713-adc4-dcd27bd4c3c3/download/casillas.gpkg")


def cruzar_puntos(encarte: pd.DataFrame, puntos: gpd.GeoDataFrame,
                  secciones: gpd.GeoDataFrame,
                  revisiones: pd.DataFrame | None = None) -> pd.DataFrame:
    """Coteja clave y domicilio; acepta polígono o revisión visual documentada."""
    if puntos.crs is None or secciones.crs is None:
        raise ValueError("CRS ausente")
    puntos = puntos.to_crs(4326).copy()
    secciones = secciones.to_crs(4326)
    puntos["ID_SECCION"] = "22-" + puntos.seccion.astype(int).astype(str).str.zfill(4)
    puntos["CASILLA"] = puntos.name.replace({"B": "B1"})
    if puntos.duplicated(["ID_SECCION", "CASILLA"]).any():
        raise ValueError("Puntos duplicados por sección y casilla")
    if secciones.ID_SECCION.duplicated().any():
        raise ValueError("Polígonos duplicados por sección")
    base = encarte.loc[encarte.CASILLA.str[0].isin(list("BCE")),
                       ["ID_SECCION", "CASILLA", "DOMICILIO_NORMALIZADO"]].copy()
    if base.duplicated(["ID_SECCION", "CASILLA"]).any():
        raise ValueError("Encarte duplicado por sección y casilla")
    cols = ["ID_SECCION", "CASILLA", "ubicacion", "domicilio", "referencia", "geometry"]
    joined = base.merge(puntos[cols], on=["ID_SECCION", "CASILLA"], how="left", validate="one_to_one")
    joined = joined.merge(secciones[["ID_SECCION", "geometry"]].rename(columns={"geometry": "polygon"}),
                          on="ID_SECCION", how="left", validate="many_to_one")
    has_point = joined.geometry.notna()
    joined["DOMICILIO_COINCIDE"] = False
    joined["DENTRO_SECCION"] = False
    for idx in joined.index[has_point]:
        row = joined.loc[idx]
        fuente = normalizar(" ".join(str(row[c]) for c in ("ubicacion", "domicilio", "referencia")))
        joined.at[idx, "DOMICILIO_COINCIDE"] = bool(fuente and fuente == row.DOMICILIO_NORMALIZADO)
        if row.polygon is not None:
            joined.at[idx, "DENTRO_SECCION"] = bool(shapely.covers(row.polygon, row.geometry))
    joined["CALIDAD"] = "sin_punto_fuente"
    joined.loc[has_point, "CALIDAD"] = "revisar_domicilio_o_poligono"
    valid = has_point & joined.DOMICILIO_COINCIDE & joined.DENTRO_SECCION
    joined.loc[valid, "CALIDAD"] = "clave_domicilio_y_poligono"
    joined["DISTANCIA_REVISION_M"] = float("nan")
    joined["URL_REVISION"] = ""
    if revisiones is not None and len(revisiones):
        if revisiones.duplicated(["ID_SECCION", "CASILLA_ETIQUETA"]).any():
            raise ValueError("Revisión manual duplicada")
        geod = Geod(ellps="WGS84")
        for row in revisiones.itertuples():
            match = joined.ID_SECCION.eq(row.ID_SECCION) & joined.CASILLA.eq(row.CASILLA_ETIQUETA)
            if int(match.sum()) != 1:
                raise ValueError(f"Revisión sin casilla única: {row.ID_SECCION} {row.CASILLA_ETIQUETA}")
            idx = joined.index[match][0]
            punto = joined.at[idx, "geometry"]
            if not row.CASILLA_ETIQUETA.startswith("E") or punto is None:
                raise ValueError("La revisión documentada debe corresponder a una E con punto")
            if not joined.at[idx, "DOMICILIO_COINCIDE"] or joined.at[idx, "DENTRO_SECCION"]:
                raise ValueError("La revisión no corresponde a un punto exterior con domicilio coincidente")
            metros = geod.inv(punto.x, punto.y, row.LONGITUD_REVISION, row.LATITUD_REVISION)[2]
            if metros > 35:
                raise ValueError(f"Coordenada revisada demasiado lejos del punto fuente: {metros:.1f} m")
            joined.at[idx, "DISTANCIA_REVISION_M"] = round(metros, 2)
            joined.at[idx, "URL_REVISION"] = row.URL_REVISION if pd.notna(row.URL_REVISION) else ""
            joined.at[idx, "CALIDAD"] = "domicilio_y_revision_manual"
    joined["LONGITUD"] = joined.geometry.map(lambda p: p.x if p is not None else float("nan"))
    joined["LATITUD"] = joined.geometry.map(lambda p: p.y if p is not None else float("nan"))
    return joined.rename(columns={"CASILLA": "CASILLA_ETIQUETA", "ubicacion": "SEDE",
                                  "domicilio": "DOMICILIO_FUENTE"})[
        ["ID_SECCION", "CASILLA_ETIQUETA", "LONGITUD", "LATITUD", "SEDE",
         "DOMICILIO_FUENTE", "CALIDAD", "DOMICILIO_COINCIDE", "DENTRO_SECCION",
         "DISTANCIA_REVISION_M", "URL_REVISION"]]


def build(source: Path = SOURCE, encarte_path: Path = ENCARTE,
          geometry_path: Path = GEOMETRIA_PARQUET, output: Path = OUTPUT) -> dict:
    puntos = gpd.read_file(source, where="entidad = 22")
    encarte = pd.read_parquet(encarte_path)
    secciones = gpd.read_parquet(geometry_path, columns=["ID_SECCION", "geometry"])
    revisiones = pd.read_csv(REVISIONES)
    result = cruzar_puntos(encarte, puntos, secciones, revisiones)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, index=False)
    audit = {
        "fuente_url": SOURCE_URL,
        "fuente_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "fuente_publicada": "2024-06-03",
        "fuente_tipo": "copia de Ubica tu Casilla 2024 publicada por tercero; no descarga oficial INE",
        "encarte_casillas_bce": len(result),
        "puntos_por_clave": int(result.LONGITUD.notna().sum()),
        "puntos_aceptados": int(result.CALIDAD.isin(("clave_domicilio_y_poligono", "domicilio_y_revision_manual")).sum()),
        "secciones_con_punto_aceptado": int(result.loc[result.CALIDAD.isin(("clave_domicilio_y_poligono", "domicilio_y_revision_manual")), "ID_SECCION"].nunique()),
        "puntos_revision_manual": int(result.CALIDAD.eq("domicilio_y_revision_manual").sum()),
        "distancia_revision_m": result.loc[result.CALIDAD.eq("domicilio_y_revision_manual"),
                                           ["ID_SECCION", "CASILLA_ETIQUETA", "DISTANCIA_REVISION_M"]].to_dict("records"),
        "calidad": result.CALIDAD.value_counts().to_dict(),
        "puntos_fuera_seccion": int((result.LONGITUD.notna() & ~result.DENTRO_SECCION).sum()),
        "puntos_con_domicilio_distinto": int((result.LONGITUD.notna() & ~result.DOMICILIO_COINCIDE).sum()),
        "nota": "Los puntos representan sedes de instalación; no residencia ni área de atención de E."
    }
    output.with_suffix(".audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
