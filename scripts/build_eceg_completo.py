"""Parquetiza el ECEG 2020 completo y crea tablas locales en DuckDB.

Uso: python scripts/build_eceg_completo.py [eceg_2020_csv.zip]
No reemplaza `cpv_2020_seccion.parquet`, que contiene las 15 tasas de la app.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from electoral.cpv import VARIABLES, preparar_variables  # noqa: E402

DATA = ROOT / "data" / "electoral"
MIEMBROS = {
    "entidad": "conjunto_de_datos/INE_ENTIDAD_2020.CSV",
    "distrito": "conjunto_de_datos/INE_DISTRITO_2020.CSV",
    "seccion": "conjunto_de_datos/INE_SECCION_2020.csv",
}
FILAS_ESPERADAS = {"entidad": 32, "distrito": 300, "seccion": 68806}
TEXTO = {"NOM_ENT", "INDIGENA", "COMPLEJIDA"}


def normalizar(tabla: pd.DataFrame, nivel: str) -> pd.DataFrame:
    """Convierte indicadores a números y añade llaves nacionales estables."""
    if nivel not in MIEMBROS:
        raise ValueError(f"Nivel desconocido: {nivel}")
    tabla = tabla.copy()
    tabla.columns = tabla.columns.str.strip()
    if tabla.columns.duplicated().any():
        raise ValueError("Columnas duplicadas tras quitar espacios")
    tabla = pd.DataFrame({
        columna: (tabla[columna].astype("string").str.strip() if columna in TEXTO
                  else pd.to_numeric(tabla[columna], errors="raise"))
        for columna in tabla.columns
    })
    entidad = "ENT" if nivel == "entidad" else "ENTIDAD"
    if entidad not in tabla:
        raise ValueError(f"Falta llave {entidad}")
    if tabla[entidad].isna().any() or not tabla[entidad].between(1, 32).all():
        raise ValueError("Clave de entidad inválida")
    tabla.insert(0, "ID_ENTIDAD", tabla[entidad].astype(int).astype(str).str.zfill(2))
    llave = "ID_ENTIDAD"
    if nivel == "distrito":
        if tabla.DISTRITO.isna().any() or not tabla.DISTRITO.gt(0).all():
            raise ValueError("Clave de distrito inválida")
        tabla.insert(1, "ID_DISTRITO", tabla.ID_ENTIDAD + "-" + tabla.DISTRITO.astype(int).astype(str).str.zfill(2))
        llave = "ID_DISTRITO"
    elif nivel == "seccion":
        if tabla.SECCION.isna().any() or not tabla.SECCION.gt(0).all():
            raise ValueError("Clave de sección inválida")
        tabla.insert(1, "ID_SECCION", tabla.ID_ENTIDAD + "-" + tabla.SECCION.astype(int).astype(str).str.zfill(4))
        llave = "ID_SECCION"
    if tabla[llave].duplicated().any():
        raise ValueError(f"Llave duplicada: {llave}")
    return tabla


def construir(archivo: Path) -> dict:
    informe = {"origen": str(archivo), "niveles": {}}
    destino_db = DATA / "eceg_2020.duckdb"
    temporal_db = DATA / "eceg_2020_tmp.duckdb"
    temporal_db.unlink(missing_ok=True)
    with zipfile.ZipFile(archivo) as z, duckdb.connect(str(temporal_db)) as con:
        for nivel, miembro in MIEMBROS.items():
            with z.open(miembro) as csv:
                tabla = pd.read_csv(csv, dtype=str, encoding="latin1", low_memory=False)
            tabla = normalizar(tabla, nivel)
            if len(tabla) != FILAS_ESPERADAS[nivel]:
                raise ValueError(f"Filas inesperadas en {nivel}: {len(tabla)}")
            if nivel == "seccion" and (DATA / "cpv_2020_seccion.parquet").exists():
                actual = preparar_variables(tabla)
                previo = pd.read_parquet(DATA / "cpv_2020_seccion.parquet")
                if set(actual.ID_SECCION) != set(previo.ID_SECCION):
                    raise ValueError("Las claves seccionales difieren del CPV de la app")
                cotejo = actual.merge(previo, on="ID_SECCION", validate="one_to_one", suffixes=("_nuevo", "_previo"))
                for variable, *_ in VARIABLES:
                    nuevo, viejo = cotejo[f"{variable}_nuevo"], cotejo[f"{variable}_previo"]
                    if not nuevo.isna().equals(viejo.isna()) or (nuevo - viejo).abs().gt(1e-9).any():
                        raise ValueError(f"La tasa {variable} difiere del CPV de la app")
                informe["tasas_app_verificadas"] = len(VARIABLES)
            parquet = DATA / f"eceg_2020_{nivel}.parquet"
            tabla.to_parquet(parquet, index=False)
            nombre_sql = f"eceg_{nivel}_2020"
            con.execute(f"CREATE TABLE {nombre_sql} AS SELECT * FROM read_parquet(?)", [str(parquet)])
            llave = {"entidad": "ID_ENTIDAD", "distrito": "ID_DISTRITO", "seccion": "ID_SECCION"}[nivel]
            con.execute(f"CREATE UNIQUE INDEX idx_{nombre_sql} ON {nombre_sql} ({llave})")
            if con.execute(f"SELECT count(*) FROM {nombre_sql}").fetchone()[0] != len(tabla):
                raise AssertionError(f"DuckDB no conserva las filas de {nivel}")
            informe["niveles"][nivel] = {
                "filas": len(tabla), "columnas": len(tabla.columns), "llave": llave,
                "parquet": str(parquet), "tabla_duckdb": nombre_sql,
                "poblacion_total": int(tabla.POBTOT.sum()),
            }
        con.execute("CHECKPOINT")
    temporal_db.replace(destino_db)
    (DATA / "eceg_2020_completo_auditoria.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return informe


if __name__ == "__main__":
    origen = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "eceg_2020_csv.zip"
    print(json.dumps(construir(origen), ensure_ascii=False, indent=2))
