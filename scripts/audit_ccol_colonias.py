"""Audita si un CCOL histórico enlaza con ColoniasINE2020a.parquet.

Uso: python scripts/audit_ccol_colonias.py [ccol_ine_2022_nacional.csv]
Sólo crea artefactos locales de auditoría; no modifica el cruce usado por la app.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/electoral"
POLIGONOS = Path(r"H:\Mi unidad\(0) CARTOGRAFUNK BASICS\(4) DATA\11 Colonias INE\ColoniasINE2020a.parquet")
NUMEROS = ("ID", "ENTIDAD", "MUNICIPIO", "CP", "CONTROL")


def nombre_normalizado(valor: object) -> str:
    if pd.isna(valor):
        return ""
    sin_acentos = unicodedata.normalize("NFKD", str(valor).upper())
    return re.sub(r"[^A-Z0-9]", "", "".join(c for c in sin_acentos if not unicodedata.combining(c)))


def auditar(catalogo: pd.DataFrame, poligonos: pd.DataFrame) -> dict:
    c = catalogo.copy()
    g = poligonos.copy()
    for columna in NUMEROS:
        c[columna] = pd.to_numeric(c[columna], errors="coerce").astype("Int64")
        g[columna] = pd.to_numeric(g[columna], errors="coerce").astype("Int64")
    if g[["ENTIDAD", "ID"]].duplicated().any():
        raise ValueError("Polígonos con (ENTIDAD, ID) duplicado")
    c["NOMBRE_NORM"] = c.NOMBRE.map(nombre_normalizado)
    g["NOMBRE_NORM"] = g.NOMBRE.map(nombre_normalizado)
    por_id = c.merge(g, on=["ENTIDAD", "ID"], how="inner", suffixes=("_ccol", "_poligono"), validate="many_to_one")
    por_id["nombre_igual"] = por_id.NOMBRE_NORM_ccol.eq(por_id.NOMBRE_NORM_poligono)
    por_id["municipio_igual"] = por_id.MUNICIPIO_ccol.eq(por_id.MUNICIPIO_poligono)
    por_id["cp_igual"] = por_id.CP_ccol.eq(por_id.CP_poligono)
    por_id["tres_iguales"] = por_id.nombre_igual & por_id.municipio_igual & por_id.cp_igual
    id_resumen = por_id.groupby(["ENTIDAD", "ID"])[["nombre_igual", "municipio_igual", "cp_igual", "tres_iguales"]].any()

    claves = ["ENTIDAD", "MUNICIPIO", "NOMBRE_NORM", "CP"]
    c_validas = c.loc[c.CP.notna() & c.NOMBRE_NORM.ne(""), claves + ["ID"]].drop_duplicates()
    g_validas = g.loc[g.CP.notna() & g.NOMBRE_NORM.ne(""), claves + ["ID"]]
    candidatos = g_validas.merge(c_validas, on=claves, how="inner", suffixes=("_poligono", "_ccol"))
    conteo = candidatos.groupby(["ENTIDAD", "ID_poligono"]).ID_ccol.nunique()
    secciones_por_colonia = c.groupby(["ENTIDAD", "ID"]).SECCION.nunique()
    return {
        "filas_ccol": len(c), "colonias_ccol_por_entidad_id": int(c[["ENTIDAD", "ID"]].drop_duplicates().shape[0]),
        "filas_poligono": len(g), "id_compartido": len(id_resumen),
        "id_y_nombre_iguales": int(id_resumen.nombre_igual.sum()),
        "id_y_municipio_iguales": int(id_resumen.municipio_igual.sum()),
        "id_y_cp_iguales": int(id_resumen.cp_igual.sum()),
        "id_y_tres_atributos_iguales": int(id_resumen.tres_iguales.sum()),
        "compuesto_entidad_municipio_nombre_cp_con_candidato": len(conteo),
        "compuesto_candidato_unico": int(conteo.eq(1).sum()),
        "compuesto_ambiguo": int(conteo.gt(1).sum()),
        "compuesto_sin_candidato": len(g) - len(conteo),
        "colonias_ccol_en_varias_secciones": int(secciones_por_colonia.gt(1).sum()),
        "max_secciones_por_colonia_ccol": int(secciones_por_colonia.max()),
    }


def comparar_con_espacial(catalogo: pd.DataFrame, poligonos: pd.DataFrame, espacial: pd.DataFrame) -> dict:
    """Contrasta pares 2024 sólo donde la llave textual 2022 es unívoca."""
    c, g = catalogo.copy(), poligonos.copy()
    for columna in NUMEROS:
        c[columna] = pd.to_numeric(c[columna], errors="coerce").astype("Int64")
        g[columna] = pd.to_numeric(g[columna], errors="coerce").astype("Int64")
    c["SECCION"] = pd.to_numeric(c.SECCION, errors="coerce").astype("Int64")
    c["NOMBRE_NORM"] = c.NOMBRE.map(nombre_normalizado)
    g["NOMBRE_NORM"] = g.NOMBRE.map(nombre_normalizado)
    claves = ["ENTIDAD", "MUNICIPIO", "NOMBRE_NORM", "CP"]
    candidatos = g.merge(c[claves + ["ID"]].drop_duplicates(), on=claves, how="inner", suffixes=("_poligono", "_ccol"))
    conteos = candidatos.groupby(["ENTIDAD", "ID_poligono"]).ID_ccol.nunique()
    unicos = conteos[conteos.eq(1)].index
    vinculos = candidatos.set_index(["ENTIDAD", "ID_poligono"]).loc[unicos].reset_index()[
        ["ENTIDAD", "ID_poligono", "ID_ccol"]
    ].drop_duplicates()
    pares_ccol = c[["ENTIDAD", "ID", "SECCION"]].drop_duplicates().rename(columns={"ID": "ID_ccol"})
    pares_ccol["ID_SECCION"] = (
        pares_ccol.ENTIDAD.astype(str).str.zfill(2) + "-" + pares_ccol.SECCION.astype(str).str.zfill(4)
    )
    permitidos = vinculos.merge(pares_ccol, on=["ENTIDAD", "ID_ccol"])[
        ["ENTIDAD", "ID_poligono", "ID_SECCION"]
    ].drop_duplicates()
    observados = espacial.merge(vinculos[["ENTIDAD", "ID_poligono"]].drop_duplicates(),
                                on=["ENTIDAD", "ID_poligono"], how="inner")
    coinciden = observados.merge(permitidos.assign(en_ccol=True),
                                on=["ENTIDAD", "ID_poligono", "ID_SECCION"], how="left")
    ok = coinciden.en_ccol.eq(True)
    total_poblacion = int(coinciden.poblacion_urbana_observada.sum())
    poblacion_coincide = int(coinciden.loc[ok, "poblacion_urbana_observada"].sum())
    return {
        "colonias_con_candidato_textual_unico": len(vinculos),
        "pares_espaciales_comparados": len(coinciden),
        "pares_espaciales_listados_en_ccol_2022": int(ok.sum()),
        "acuerdo_pares_pct": round(100 * ok.mean(), 3) if len(ok) else None,
        "poblacion_urbana_comparada": total_poblacion,
        "poblacion_urbana_en_pares_listados": poblacion_coincide,
        "acuerdo_poblacion_pct": round(100 * poblacion_coincide / total_poblacion, 3) if total_poblacion else None,
    }


def construir(csv: Path) -> dict:
    catalogo = pd.read_csv(csv, dtype=str, encoding="utf-8-sig")
    poligonos = pq.read_table(POLIGONOS, columns=list(NUMEROS) + ["NOMBRE"]).to_pandas()
    informe = auditar(catalogo, poligonos)
    rutas_espaciales = [DATA / f"cpv_2020_colonia_seccion_{e:02d}.parquet" for e in range(1, 33)]
    if all(p.exists() for p in rutas_espaciales):
        espacial = pd.concat([
            pd.read_parquet(p, columns=["ID_ORIGEN_COLONIA", "ID_SECCION", "poblacion_urbana_observada"])
            .assign(ENTIDAD=e)
            for e, p in enumerate(rutas_espaciales, 1)
        ], ignore_index=True).rename(columns={"ID_ORIGEN_COLONIA": "ID_poligono"})
        informe["comparacion_espacial_2024"] = comparar_con_espacial(catalogo, poligonos, espacial)
    for columna in (*NUMEROS, "DISTRITO", "SECCION"):
        catalogo[columna] = pd.to_numeric(catalogo[columna], errors="coerce").astype("Int64")
    catalogo["ID_SECCION_2022"] = (
        catalogo.ENTIDAD.astype(str).str.zfill(2) + "-" + catalogo.SECCION.astype(str).str.zfill(4)
    )
    catalogo.to_parquet(DATA / "ccol_ine_2022_nacional.parquet", index=False)
    (DATA / "ccol_ine_2022_auditoria.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    return informe


if __name__ == "__main__":
    origen = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "ccol_ine_2022_nacional.csv"
    print(json.dumps(construir(origen), ensure_ascii=False, indent=2))
