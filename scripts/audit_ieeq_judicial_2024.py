"""Coteja las seis filas marcadas y el total del distrito 7 con ST-JRC-216/2024."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/electoral/ieeq_local"
SENTENCIA = "https://www.te.gob.mx/sentenciasHTML/convertir/expediente/ST-JRC-0216-2024-"
EXPECTED = {
    (518, "C", 1, 0): 339,
    (518, "E", 1, 1): 376,
    (536, "C", 4, 0): 316,
    (727, "S", 1, 0): 22,
    (882, "B", 1, 0): 409,
    (885, "C", 1, 0): 408,
}
EXPECTED_DISTRICT_7 = 67452


def audit(folder: Path = OUTPUT) -> dict:
    cas = pd.read_parquet(folder / "dip_local_mr_2024_casilla.parquet")
    special = pd.read_parquet(folder / "dip_local_mr_2024_especial_mr.parquet")
    changed = cas.loc[cas.SENTENCIA_POST_CORTE]
    observed = {
        (int(r.SECCION), r.TIPO_CASILLA, int(r.ID_CASILLA), int(r.EXT_CONTIGUA)): int(r.TOTAL_VOTOS)
        for r in changed.itertuples(index=False)
    }
    if observed != EXPECTED:
        raise ValueError(f"Las seis casillas no cuadran con la sentencia: {observed}")
    district = cas.loc[cas.ID_DISTRITO_LOCAL.eq(7)]
    bce = int(district.loc[district.INCLUIR_SECCION, "TOTAL_VOTOS"].sum())
    special_mr = int(special.loc[special.ID_DISTRITO_LOCAL.eq(7), "VOTOS_MR"].sum())
    advance = int(district.loc[district.TIPO_NORMALIZADO.eq("A"), "TOTAL_VOTOS"].sum())
    if bce + special_mr + advance != EXPECTED_DISTRICT_7:
        raise ValueError("El total MR del distrito 7 no cuadra con la sentencia")
    result = {
        "fuente": SENTENCIA,
        "casillas_corregidas": len(observed),
        "votos_en_seis_casillas": sum(observed.values()),
        "distrito_7_bce": bce,
        "distrito_7_s_mr": special_mr,
        "distrito_7_anticipado": advance,
        "distrito_7_total": bce + special_mr + advance,
        "alcance": "Coinciden seis totales por casilla y total MR distrito 7; no coteja cada columna de partido ni otros distritos.",
    }
    (folder / "auditoria_sentencia_2024.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
