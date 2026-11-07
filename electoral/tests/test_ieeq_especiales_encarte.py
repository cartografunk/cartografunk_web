"""El encarte enlaza por sección y número S sin copiar nombres de funcionarios."""

import fitz
import pandas as pd

from scripts.extract_ieeq_especiales_encarte_2024 import build
from scripts.pdf_to_md import convert


def test_especiales_encarte_empareja_claves_y_omite_nombres(tmp_path):
    pdf = tmp_path / "encarte.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((40, 40), (
        " Distrito Federal: 1) QRO\n"
        " Distrito Local: 2) QRO\n"
        " Seccion: 48 S1\n"
        " Ubicacion: CENTRAL DE AUTOBUSES, CALLE PRINCIPAL 12\n"
        " Presidenta/e: NOMBRE DE PRUEBA\n"
    ))
    doc.save(pdf)
    doc.close()
    convert(pdf, pdf.with_suffix(".md"))
    specials = tmp_path / "especiales.parquet"
    pd.DataFrame({"ID_SECCION_INSTALACION": ["22-0048"],
                  "NUMERO_CASILLA": [1]}).to_parquet(specials)
    output = tmp_path / "ubicaciones.parquet"
    audit = build(pdf, specials, output)
    row = pd.read_parquet(output).iloc[0]
    assert audit["claves_coincidentes"] == 1
    assert audit["coordenadas_verificadas"] == 0
    assert "CENTRAL DE AUTOBUSES" in row.DOMICILIO_ENCARTE
    assert "NOMBRE DE PRUEBA" not in row.DOMICILIO_ENCARTE
