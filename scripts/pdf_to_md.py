"""Convierte un PDF descargado a Markdown antes de revisar su contenido."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import fitz


def convert(pdf: Path, md: Path, url: str = "", sort: bool = True) -> dict:
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    parts = [f"# {pdf.name}", "", f"- Fuente: {url or 'archivo local'}",
             f"- SHA-256: `{sha}`", f"- Método: texto extraído con PyMuPDF; orden={'lectura' if sort else 'flujo PDF'}", ""]
    empty = []
    with fitz.open(pdf) as document:
        for number, page in enumerate(document, start=1):
            text = page.get_text(sort=sort).strip()
            if not text:
                empty.append(number)
                text = "[SIN TEXTO EXTRAÍBLE: requiere OCR]"
            parts.extend([f"## Página {number}", "", text, ""])
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("\n".join(parts), encoding="utf-8")
    return {"paginas": number, "paginas_sin_texto": empty, "sha256": sha,
            "markdown": str(md)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("md", type=Path)
    parser.add_argument("--url", default="")
    parser.add_argument("--preserve-stream-order", action="store_true")
    args = parser.parse_args()
    print(convert(args.pdf, args.md, args.url, sort=not args.preserve_stream_order))
