"""Piloto CPV urbano 2020 por fragmento colonia-sección, desde manzanas.

Uso: python scripts/build_cpv_colonia_seccion.py --entidad 01 --zip RUTA.zip
Los Parquet de salida son locales; no sustituyen al ECEG seccional oficial.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from electoral.cpv import VARIABLES  # noqa: E402

MGE = Path(r"H:\Mi unidad\(0) CARTOGRAFUNK BASICS\(4) DATA\00 Marco Geoestadístico\00m.parquet")
COLONIAS = Path(r"H:\Mi unidad\(0) CARTOGRAFUNK BASICS\(4) DATA\11 Colonias INE\ColoniasINE2020a.parquet")
SECCIONES = ROOT / "data/electoral/secciones_2024_geom.parquet"
DESTINO = ROOT / "data/electoral"


def _asignar_puntos(manzanas: gpd.GeoDataFrame, destinos: gpd.GeoDataFrame, llave: str) -> tuple[pd.Series, int]:
    """Asigna sólo puntos interiores únicos; los solapamientos quedan sin asignar."""
    puntos = manzanas[["CVEGEO", "geometry"]].copy()
    puntos.geometry = puntos.geometry.representative_point()
    puntos = puntos.to_crs(destinos.crs)
    cruces = gpd.sjoin(puntos, destinos[[llave, "geometry"]], how="left", predicate="within")
    candidatos = cruces.dropna(subset=[llave]).groupby("CVEGEO")[llave].agg(["first", "nunique"])
    ambiguos = int(candidatos["nunique"].gt(1).sum())
    unicos = candidatos.loc[candidatos["nunique"].eq(1), "first"]
    return manzanas.CVEGEO.map(unicos), ambiguos


def _leer_cpv(archivo: Path, entidad: str) -> pd.DataFrame:
    columnas = {"ENTIDAD", "MUN", "LOC", "AGEB", "MZA", "POBTOT"}
    columnas.update(c for _, _, n, d in VARIABLES for c in (n, d) if c != "P_0A17")
    with zipfile.ZipFile(archivo) as z:
        miembros = [n for n in z.namelist() if Path(n).name.startswith("conjunto_de_datos_ageb_") and n.endswith(".csv")]
        if len(miembros) != 1:
            raise ValueError(f"Se esperaba un CSV de datos; hay {len(miembros)}")
        try:
            with z.open(miembros[0]) as csv:
                cpv = pd.read_csv(csv, dtype=str, usecols=lambda c: c in columnas, encoding="utf-8-sig")
        except UnicodeDecodeError:
            with z.open(miembros[0]) as csv:
                cpv = pd.read_csv(csv, dtype=str, usecols=lambda c: c in columnas, encoding="latin1")
    cpv = cpv.loc[(cpv.ENTIDAD == entidad) & (cpv.MZA != "000")].copy()
    cpv["CVEGEO"] = cpv.ENTIDAD + cpv.MUN + cpv.LOC + cpv.AGEB + cpv.MZA
    if cpv.CVEGEO.duplicated().any():
        raise ValueError("CVEGEO duplicada en manzanas CPV")
    return cpv


def _sumar_tasas(cpv: pd.DataFrame, claves: list[str]) -> pd.DataFrame:
    """Suma conteos antes de dividir; si falta un conteo, deja la tasa nula."""
    columnas = {c for _, _, n, d in VARIABLES for c in (n, d) if c != "P_0A17"}
    numericos = cpv[list(columnas)].apply(pd.to_numeric, errors="coerce")
    numericos["P_0A17"] = numericos.POBTOT - numericos.P_18YMAS
    base = pd.concat([cpv[claves].reset_index(drop=True), numericos.reset_index(drop=True)], axis=1)
    grupos = base.groupby(claves, dropna=False, sort=True)
    sumas = grupos[list(numericos)].sum(min_count=1)
    completos = grupos[list(numericos)].count().eq(grupos.size(), axis=0)
    resultado = sumas[["POBTOT"]].rename(columns={"POBTOT": "poblacion_urbana_observada"})
    resultado["manzanas_cpv"] = grupos.size()
    for nombre, _, num, den in VARIABLES:
        tasa = 100 * sumas[num] / sumas[den].where(sumas[den].gt(0))
        valida = completos[num] & completos[den] & tasa.between(0, 100)
        resultado[nombre] = tasa.where(valida)
    return resultado.reset_index()


def construir(entidad: str, archivo: Path) -> dict:
    entidad = entidad.zfill(2)
    manzanas = gpd.read_parquet(MGE, filters=[("CVE_ENT", "=", entidad)])
    colonias = gpd.read_parquet(COLONIAS, filters=[("ENTIDAD", "=", int(entidad))]).reset_index(drop=True)
    secciones = gpd.read_parquet(SECCIONES, filters=[("ENTIDAD", "=", int(entidad))])
    if not manzanas.CVEGEO.is_unique or not secciones.ID_SECCION.is_unique:
        raise ValueError("Geometría con llaves duplicadas")
    colonias["ID_COLONIA_LOCAL"] = colonias.index.map(lambda i: f"{entidad}:{i:06d}")
    colonia, ambiguas_colonia = _asignar_puntos(manzanas, colonias, "ID_COLONIA_LOCAL")
    seccion, ambiguas_seccion = _asignar_puntos(manzanas, secciones, "ID_SECCION")
    mapa = pd.DataFrame({"CVEGEO": manzanas.CVEGEO, "ID_COLONIA_LOCAL": colonia,
                         "ID_SECCION": seccion})
    cpv = _leer_cpv(archivo, entidad)
    total_cpv = len(cpv)
    poblacion_cpv = pd.to_numeric(cpv.POBTOT, errors="coerce").sum()
    cpv = cpv.merge(mapa, on="CVEGEO", how="left", validate="one_to_one", indicator=True)
    validas = cpv.ID_COLONIA_LOCAL.notna() & cpv.ID_SECCION.notna()
    usadas = cpv.loc[validas].copy()
    salida = _sumar_tasas(usadas, ["ID_COLONIA_LOCAL", "ID_SECCION"])
    metadatos = colonias[["ID_COLONIA_LOCAL", "ID", "MUNICIPIO", "NOMBRE"]].rename(columns={"ID": "ID_ORIGEN_COLONIA"})
    salida = salida.merge(metadatos, on="ID_COLONIA_LOCAL", validate="many_to_one")
    if int(salida.manzanas_cpv.sum()) != len(usadas):
        raise AssertionError("La agregación duplicó o perdió manzanas")
    salida.to_parquet(DESTINO / f"cpv_2020_colonia_seccion_{entidad}.parquet", index=False)
    por_seccion = _sumar_tasas(usadas, ["ID_SECCION"])
    if int(por_seccion.manzanas_cpv.sum()) != len(usadas):
        raise AssertionError("La agregación seccional duplicó o perdió manzanas")
    por_seccion.to_parquet(DESTINO / f"cpv_2020_manzana_seccion_{entidad}.parquet", index=False)
    poblacion_usada = pd.to_numeric(usadas.POBTOT, errors="coerce").sum()
    informe = {
        "entidad": entidad, "manzanas_geometricas": len(manzanas), "colonias": len(colonias),
        "secciones_2024": len(secciones), "manzanas_cpv_urbanas": total_cpv,
        "manzanas_cpv_con_geometria": int(cpv._merge.eq("both").sum()),
        "manzanas_cpv_con_colonia": int(cpv.ID_COLONIA_LOCAL.notna().sum()),
        "manzanas_cpv_con_seccion": int(cpv.ID_SECCION.notna().sum()),
        "manzanas_cpv_en_ambas": len(usadas),
        "poblacion_cpv_urbana_numerica": int(poblacion_cpv),
        "poblacion_cpv_en_ambas": int(poblacion_usada),
        "cobertura_poblacion_urbana_pct": round(100 * poblacion_usada / poblacion_cpv, 3),
        "manzanas_geometricas_ambiguas_colonia": ambiguas_colonia,
        "manzanas_geometricas_ambiguas_seccion": ambiguas_seccion,
        "pares_colonia_seccion": len(salida),
        "colonias_en_multiples_secciones": int(salida.groupby("ID_COLONIA_LOCAL").ID_SECCION.nunique().gt(1).sum()),
        "secciones_con_cpv_colonia": int(salida.ID_SECCION.nunique()),
        "tasas_disponibles_pares": {n: int(salida[n].notna().sum()) for n, *_ in VARIABLES},
        "tasas_disponibles_secciones": {n: int(por_seccion[n].notna().sum()) for n, *_ in VARIABLES},
    }
    (DESTINO / f"cpv_2020_colonia_seccion_{entidad}_cobertura.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return informe


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entidad", default="01")
    p.add_argument("--zip", dest="archivo", type=Path)
    args = p.parse_args()
    archivo = args.archivo or DESTINO / f"ageb_mza_urbana_{args.entidad.zfill(2)}_cpv2020_csv.zip"
    print(json.dumps(construir(args.entidad, archivo), ensure_ascii=False, indent=2))
