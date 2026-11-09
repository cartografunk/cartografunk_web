"""Comprueba el paquete aislado que se publicará en Streamlit Cloud."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


PREGUNTAS = (
    "1 · Dónde ganar", "2 · Por qué", "3 · Confianza", "4 · Esfuerzo",
)


def comprobar(paquete: Path) -> dict:
    paquete = paquete.resolve()
    manifiesto = json.loads((paquete / "manifest.json").read_text(encoding="utf-8"))
    for nombre, esperado in manifiesto["archivos"].items():
        archivo = paquete / nombre
        if archivo.stat().st_size != esperado["bytes"]:
            raise AssertionError(f"Tamaño diferente: {nombre}")
        if hashlib.sha256(archivo.read_bytes()).hexdigest() != esperado["sha256"]:
            raise AssertionError(f"SHA-256 diferente: {nombre}")
    if (paquete / "data/electoral/cpv_2020_seccion.parquet").exists():
        raise AssertionError("El paquete no debe incluir el CPV nacional")

    sys.path.insert(0, str(paquete))
    import electoral
    if Path(electoral.__file__).resolve().parents[1] != paquete:
        raise AssertionError("La prueba no está importando el paquete aislado")
    app = AppTest.from_file(str(paquete / "electoral/dashboard_app.py"),
                            default_timeout=180).run()
    if app.exception:
        raise AssertionError(f"Error en portada: {app.exception[0].message}")
    if not app.button or "22-0269" not in app.button[0].label:
        raise AssertionError("No se mostró la lista de casillas")
    app.button[4].click().run()
    if app.exception or app.session_state["boletas_casilla_seleccionada"] != ("22-0272", "B1"):
        raise AssertionError("La casilla no se enlazó con el mapa")
    if not any("Sede marcada y mapa centrado" in x.value for x in app.info):
        raise AssertionError("La ficha no confirmó el zoom a la sede")

    resultados = {}
    for pregunta in PREGUNTAS:
        app.session_state["dashboard_preguntas"] = pregunta
        app.run()
        if app.exception:
            raise AssertionError(f"Error en {pregunta}: {app.exception[0].message}")
        if "Partido a explorar" not in [x.label for x in app.selectbox]:
            raise AssertionError(f"Falta el piloto en {pregunta}")
        resultados[pregunta] = {"tablas": len(app.dataframe), "graficas": len(app.get("vega_lite_chart"))}
    return {"archivos_verificados": len(manifiesto["archivos"]),
            "casilla_enlazada": "22-0272 B1", "preguntas": resultados}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paquete", type=Path)
    print(json.dumps(comprobar(parser.parse_args().paquete), ensure_ascii=False, indent=2))
