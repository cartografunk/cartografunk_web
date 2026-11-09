"""Prepara una copia mínima del dashboard electoral para un despliegue aislado.

No copia el CPV nacional ni los ZIP de origen. Los Parquet que sí incluye son
derivados del piloto Querétaro 2024 y deben publicarse sólo en el repositorio
de despliegue que el propietario elija.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
LOCALES = (
    "boletas_qro_2018_2024_seccion.parquet",
    "votos_opcion_qro_2018_2024_seccion.parquet",
    "boletas_qro_2018_2024_casilla.parquet",
    "ayuntamiento_2024_casilla.parquet",
    "casillas_2024_puntos.parquet",
    "diagnostico_casillas_cpv_2024.parquet",
    "perfilamiento_cpv_2024_seccion.parquet",
    "perfilamiento_cpv_2024.json",
    "benchmark_partidos_2024.json",
    "benchmark_ml_cpv_2024.json",
    "benchmark_ml_cpv_expandido_2024.json",
    "dip_local_mr_2024_seccion_bce.parquet",
)


def _copiar(origen: Path, destino: Path) -> None:
    if not origen.is_file():
        raise FileNotFoundError(origen)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)


def preparar(destino: Path) -> dict:
    destino = destino.resolve()
    if destino.exists():
        raise FileExistsError(f"El destino ya existe: {destino}")
    destino.mkdir(parents=True)
    (destino / "electoral").mkdir()
    for origen in (ROOT / "electoral").glob("*.py"):
        _copiar(origen, destino / "electoral" / origen.name)
    local = Path("data/electoral/ieeq_local")
    for nombre in LOCALES:
        _copiar(ROOT / local / nombre, destino / local / nombre)

    nacionales = Path("data/electoral")
    for nombre in ("presidencia_2024_seccion.parquet",
                   "diputaciones_2024_seccion.parquet",
                   "fidelidad_estado.parquet"):
        origen = ROOT / nacionales / nombre
        tabla = pd.read_parquet(origen, filters=[("ID_ESTADO", "==", 22)])
        if tabla.empty:
            raise ValueError(f"Sin filas de Querétaro: {origen}")
        salida = destino / nacionales / nombre
        salida.parent.mkdir(parents=True, exist_ok=True)
        tabla.to_parquet(salida, index=False)

    geometria = gpd.read_parquet(ROOT / nacionales / "secciones_2024_geom.parquet",
                                  filters=[("ENTIDAD", "==", 22)])
    if len(geometria) != 953:
        raise ValueError(f"Geometría Querétaro: se esperaban 953 secciones, hay {len(geometria)}")
    geometria.to_parquet(destino / nacionales / "secciones_2024_geom.parquet", index=False)

    (destino / "requirements.txt").write_text(
        "streamlit==1.66.1\npandas==2.2.3\nnumpy==2.1.1\n"
        "pyarrow==24.0.0\ngeopandas==1.1.4\nshapely==2.1.2\n"
        "pydeck==0.9.3\naltair==6.3.0\n", encoding="utf-8")
    tema = destino / ".streamlit/config.toml"
    tema.parent.mkdir(parents=True, exist_ok=True)
    tema.write_text(
        '[theme]\nbase = "dark"\nprimaryColor = "#26baff"\n'
        'backgroundColor = "#031b2c"\nsecondaryBackgroundColor = "#062b45"\n'
        'textColor = "#eaf5ff"\nlinkColor = "#61d5ff"\n'
        'borderColor = "#115076"\n'
        'font = "Noto Sans"\nheadingFont = "Noto Sans"\n',
        encoding="utf-8")
    (destino / ".python-version").write_text("3.12\n", encoding="utf-8")
    (destino / "README.md").write_text(
        "# Cartografunk · MVP electoral Querétaro\n\n"
        "Entrada: `electoral/dashboard_app.py`. App de presentación con boletas "
        "locales y un piloto retrospectivo de diputaciones 2024. Los datos son "
        "copias derivadas para Querétaro de fuentes INE/IEEQ; no incluye el "
        "Parquet nacional CPV ni ZIP de origen.\n\n"
        "El CPV 2020 se usa sólo donde la geometría seccional es comparable. "
        "Las asociaciones no prueban causalidad ni constituyen pronósticos "
        "prospectivos. El reparto de coaliciones es analítico y experimental. "
        "Los puntos son sedes de instalación 2024, no domicilios de votantes.\n\n"
        "`manifest.json` registra el SHA-256 y tamaño de cada archivo incluido.\n",
        encoding="utf-8")
    (destino / ".gitignore").write_text("__pycache__/\n*.pyc\n.streamlit/secrets.toml\n",
                                          encoding="utf-8")
    archivos = {}
    for archivo in sorted(destino.rglob("*")):
        if archivo.is_file() and archivo.name != "manifest.json":
            datos = archivo.read_bytes()
            archivos[archivo.relative_to(destino).as_posix()] = {
                "bytes": len(datos), "sha256": hashlib.sha256(datos).hexdigest(),
            }
    manifest = {"fuente": "demo-tres-elecciones", "entrada": "electoral/dashboard_app.py",
                "geometria_secciones": len(geometria), "archivos": archivos}
    (destino / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destino", type=Path)
    args = parser.parse_args()
    resultado = preparar(args.destino)
    print(json.dumps({"destino": str(args.destino.resolve()),
                      "archivos": len(resultado["archivos"]),
                      "bytes": sum(a["bytes"] for a in resultado["archivos"].values())},
                     ensure_ascii=False))
