"""Extracción de claves y domicilios sin mezclar casillas extraordinarias."""

import hashlib

from scripts.match_ieeq_encartes import normalizar, parse_encarte


def test_normalizar_domicilio_ignora_acentos_y_puntuacion():
    assert normalizar("Escuela José, Núm. 3") == "ESCUELA JOSE NUM 3"


def test_extraer_2021_distingue_extraordinaria_y_contigua(tmp_path):
    pdf = tmp_path / "encarte.pdf"
    pdf.write_bytes(b"fixture")
    digest = hashlib.sha256(b"fixture").hexdigest()
    md = pdf.with_suffix(".md")
    md.write_text(f"""# encarte.pdf
- SHA-256: `{digest}`
## Página 1
 Distrito Federal: 1) UNO
 Municipio: 10) EL MARQUÉS
 Localidad: 1) CENTRO
 Sección: 195 E1
 Ubicación: ESCUELA NUEVA, CALLE 1
 Presidenta/e: NOMBRE DESCARTADO
 Distrito Federal: 1) UNO
 Municipio: 10) EL MARQUÉS
 Localidad: 1) CENTRO
 Sección: 195 E1C1
 Ubicación: ESCUELA NUEVA, CALLE 1
 Presidenta/e: OTRO NOMBRE DESCARTADO
""", encoding="utf-8")
    filas = parse_encarte(md, 2021)
    assert filas.CASILLA.tolist() == ["E1", "E1C1"]
    assert filas.ID_SECCION.tolist() == ["22-0195", "22-0195"]
    assert filas.LOCALIDAD_INE.tolist() == [1, 1]
    assert "NOMBRE DESCARTADO" not in filas.to_string()
