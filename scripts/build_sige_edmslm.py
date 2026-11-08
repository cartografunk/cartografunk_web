"""Parquetiza un corte EDMSLM del SIGE sin mezclarlo con cortes electorales previos.

Ejemplo:
    python scripts/build_sige_edmslm.py --txt RUTA/EDMSLM.txt --corte 2026-01 \
        --entidad 22 --secciones-2024 data/electoral/ieeq_local/dip_local_mr_2024_seccion_bce.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb


EXPECTED = {
    "ENTIDAD", "DISTRITO", "MUNICIPIO", "NOMBRE_MUNICIPIO", "SECCION",
    "TIPO_SECCION", "TIPO_NOMBRE", "LOCALIDAD", "NOMBRE_LOCALIDAD",
    "TIPO_LOCALIDAD", "TIPO_NOMBRE_LOCALIDAD", "MANZANA", "STATUS",
}


def _literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(
    txt: Path,
    corte: str,
    entidad: int,
    output: Path,
    secciones_2024: Path | None = None,
) -> dict:
    if not txt.is_file():
        raise FileNotFoundError(txt)
    if not (len(corte) == 7 and corte[4] == "-" and corte[:4].isdigit() and corte[5:].isdigit()):
        raise ValueError("corte debe tener formato AAAA-MM")
    if not 1 <= entidad <= 32:
        raise ValueError("entidad debe estar entre 01 y 32")

    output.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect()
    source = f"read_csv({_literal(txt)}, delim='|', header=true, all_varchar=true, auto_detect=true)"
    columns = {row[0] for row in conn.execute(f"DESCRIBE SELECT * FROM {source}").fetchall()}
    if columns != EXPECTED:
        raise ValueError(f"Columnas EDMSLM inesperadas: faltan {EXPECTED - columns}; sobran {columns - EXPECTED}")
    entity_code = f"{entidad:02d}"
    temp = output.with_name(output.name + ".tmp.parquet")
    query = f"""
        SELECT *,
            '{corte}' AS CORTE_SIGE,
            lpad(trim(ENTIDAD),2,'0') || '-' || lpad(trim(SECCION),4,'0') AS ID_SECCION_CORTE,
            lpad(trim(ENTIDAD),2,'0') || '-' || lpad(trim(MUNICIPIO),3,'0') || '-'
                || lpad(trim(LOCALIDAD),4,'0') AS ID_LOCALIDAD_INE_CORTE,
            lpad(trim(ENTIDAD),2,'0') || '-' || lpad(trim(MUNICIPIO),3,'0') || '-'
                || lpad(trim(SECCION),4,'0') || '-' || lpad(trim(LOCALIDAD),4,'0') || '-'
                || lpad(trim(MANZANA),4,'0') AS ID_MANZANA_INE_CORTE
        FROM {source}
        WHERE trim(ENTIDAD) = '{entity_code}'
    """
    conn.execute(f"COPY ({query}) TO {_literal(temp)} (FORMAT PARQUET, COMPRESSION ZSTD)")
    temp.replace(output)
    data = f"read_parquet({_literal(output)})"
    rows, sections, localities, keys, disabled = conn.execute(f"""
        SELECT count(*), count(DISTINCT ID_SECCION_CORTE),
               count(DISTINCT ID_LOCALIDAD_INE_CORTE),
               count(DISTINCT ID_MANZANA_INE_CORTE),
               count(*) FILTER (WHERE STATUS='*')
        FROM {data}
    """).fetchone()
    if rows != keys:
        raise ValueError(f"La clave de manzana electoral no es única: {rows} filas, {keys} claves")
    audit: dict = {
        "fuente": str(txt), "sha256_fuente": _sha256(txt), "corte_sige": corte,
        "entidad": entity_code, "parquet": str(output), "filas": rows,
        "secciones": sections, "localidades": localities,
        "manzanas_inhabilitadas": disabled,
        "nota": "La clave de manzana INE incluye sección; no equivale directamente al CVEGEO INEGI. El catálogo no tiene casilla E.",
    }
    if secciones_2024 is not None:
        if not secciones_2024.is_file():
            raise FileNotFoundError(secciones_2024)
        old = f"read_parquet({_literal(secciones_2024)})"
        same, old_count, missing = conn.execute(f"""
            WITH actual AS (SELECT DISTINCT ID_SECCION_CORTE AS id FROM {data}),
                 previo AS (SELECT DISTINCT ID_SECCION AS id FROM {old})
            SELECT count(*) FILTER (WHERE actual.id IS NOT NULL), count(*),
                   list(previo.id ORDER BY previo.id) FILTER (WHERE actual.id IS NULL)
            FROM previo LEFT JOIN actual USING(id)
        """).fetchone()
        audit["comparacion_claves_2024"] = {
            "secciones_2024": old_count, "claves_compartidas": same,
            "claves_2024_ausentes_en_corte": missing or [],
            "advertencia": "Compartir clave no demuestra identidad de perímetro entre cortes.",
        }
    audit_path = output.with_suffix(".audit.json")
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--txt", type=Path, required=True)
    parser.add_argument("--corte", required=True)
    parser.add_argument("--entidad", type=int, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--secciones-2024", type=Path)
    args = parser.parse_args()
    output = args.output or Path(f"data/electoral/edmslm_{args.corte.replace('-', '_')}_{args.entidad:02d}.parquet")
    print(json.dumps(build(args.txt, args.corte, args.entidad, output, args.secciones_2024), ensure_ascii=False, indent=2))
