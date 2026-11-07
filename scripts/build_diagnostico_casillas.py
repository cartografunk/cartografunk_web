"""Genera tabla local IEEQ 2024 + CPV comparable por casilla B/C/E."""

from pathlib import Path

import pandas as pd

from electoral.diagnostico_casillas import cobertura, evaluar_partido, preparar_casillas

ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "data/electoral/ieeq_local"


def main() -> None:
    salida = preparar_casillas(
        pd.read_parquet(CARPETA / "dip_local_mr_2024_casilla.parquet"),
        pd.read_parquet(CARPETA / "crosswalk_qro_2018_2021_2024_referencias.parquet"),
        pd.read_parquet(ROOT / "data/electoral/cpv_2020_seccion.parquet"),
    )
    destino = CARPETA / "diagnostico_casillas_cpv_2024.parquet"
    salida.to_parquet(destino, index=False)
    print(destino)
    print(cobertura(evaluar_partido(salida, "MORENA")))


if __name__ == "__main__":
    main()
