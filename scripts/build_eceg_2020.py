"""Construye CPV seccional: python scripts/build_eceg_2020.py [zip_oficial]."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from electoral.cpv import preparar_variables  # noqa: E402

SOURCE_URL = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/geoelectorales/eceg_2020_csv.zip"
DATA = ROOT / "data" / "electoral"


def construir(archivo: Path) -> dict:
    with zipfile.ZipFile(archivo) as z:
        miembro = "conjunto_de_datos/INE_SECCION_2020.csv"
        with z.open(miembro) as csv:
            censo = pd.read_csv(csv, low_memory=False, dtype=str)
    variables = preparar_variables(censo)
    destino = DATA / "cpv_2020_seccion.parquet"
    variables.to_parquet(destino, index=False)
    informe = {"fuente": SOURCE_URL, "filas_eceg": len(variables), "columnas": list(variables)}
    claves = set(variables.ID_SECCION)
    for eleccion in ("presidencia", "diputaciones", "senadurias"):
        tabla = pd.read_parquet(DATA / f"{eleccion}_2024_seccion.parquet", columns=["ID_SECCION", "LISTA_NOMINAL"])
        if tabla.ID_SECCION.duplicated().any():
            raise ValueError(f"ID_SECCION duplicado en {eleccion}")
        coincide = tabla.ID_SECCION.isin(claves)
        nominal = pd.to_numeric(tabla.LISTA_NOMINAL, errors="coerce").fillna(0)
        informe[eleccion] = {
            "secciones_2024": len(tabla), "secciones_cruzadas": int(coincide.sum()),
            "cobertura_secciones_pct": round(100 * coincide.mean(), 3),
            "lista_nominal_total": int(nominal.sum()),
            "lista_nominal_cruzada": int(nominal[coincide].sum()),
            "cobertura_lista_nominal_pct": round(100 * nominal[coincide].sum() / nominal.sum(), 3),
        }
    (DATA / "cpv_2020_cobertura.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    return informe


if __name__ == "__main__":
    origen = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "eceg_2020_csv.zip"
    print(json.dumps(construir(origen), ensure_ascii=False, indent=2))
