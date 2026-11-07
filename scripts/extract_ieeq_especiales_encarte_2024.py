"""Extrae domicilios de casillas S del encarte IEEQ 2024, sin nombres de funcionarios.

Fuente: https://ieeq.mx/contenido/difusion/2024/Encarte_30052024.pdf
No geocodifica: un domicilio publicado no equivale a una coordenada verificada.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/electoral/fuentes_ieeq/encarte_qro_2024_3005.pdf"
SPECIALS = ROOT / "data/electoral/ieeq_local/dip_local_mr_2024_especial_mr.parquet"
OUTPUT = ROOT / "data/electoral/ieeq_local/dip_local_mr_2024_especial_ubicacion.parquet"
SOURCE_URL = "https://ieeq.mx/contenido/difusion/2024/Encarte_30052024.pdf"


def parse(pdf: Path = SOURCE) -> pd.DataFrame:
    records = []
    markdown = pdf.with_suffix(".md")
    if not markdown.exists():
        raise FileNotFoundError(f"Primero convierte el PDF a Markdown: {markdown}")
    source_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    content = markdown.read_text(encoding="utf-8")
    if f"SHA-256: `{source_hash}`" not in content:
        raise ValueError("El Markdown no corresponde al PDF actual")
    for page in re.split(r"(?=## Página \d+)", content):
        header = re.match(r"## Página (\d+)", page)
        if not header:
            continue
        page_no = int(header.group(1))
        # Cada bloque empieza con el distrito federal; se conservan sólo
        # sección, S y domicilio, nunca los nombres de la mesa directiva.
        for block in re.split(r"(?= Distrito Federal:)", page):
            key = re.search(r"Secci.n:\s*(\d+)\s+S(\d+)\b", block)
            if not key:
                continue
            place = re.search(r"Ubicaci.n:\s*(.*?)\s+Presidenta/e:", block, re.S)
            if not place:
                raise ValueError(f"Domicilio ausente en página {page_no}: {key.group(0)}")
            records.append({
                "ANIO": 2024,
                "ID_SECCION_INSTALACION": f"22-{int(key.group(1)):04d}",
                "NUMERO_CASILLA": int(key.group(2)),
                "DOMICILIO_ENCARTE": " ".join(place.group(1).split()),
                "PAGINA_ENCARTE": page_no,
                "FUENTE_URL": SOURCE_URL,
            })
    result = pd.DataFrame(records)
    if result.duplicated(["ID_SECCION_INSTALACION", "NUMERO_CASILLA"]).any():
        raise ValueError("Claves S duplicadas en el encarte")
    return result


def build(pdf: Path = SOURCE, specials: Path = SPECIALS, output: Path = OUTPUT) -> dict:
    location = parse(pdf)
    votes = pd.read_parquet(specials)
    key = ["ID_SECCION_INSTALACION", "NUMERO_CASILLA"]
    matched = votes[key].merge(location, on=key, how="outer", indicator=True, validate="one_to_one")
    if not matched._merge.eq("both").all():
        raise ValueError(matched.loc[matched._merge.ne("both"), key + ["_merge"]].to_string(index=False))
    output.parent.mkdir(parents=True, exist_ok=True)
    location.sort_values(key).to_parquet(output, index=False)
    return {"registros_encarte": len(location), "registros_votos_mr": len(votes),
            "claves_coincidentes": len(matched),
            "sha256_pdf": hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "coordenadas_verificadas": 0}


if __name__ == "__main__":
    print(build())
