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
    if not any("3,081" in x.value for x in app.metric):
        raise AssertionError("La portada no mostró el inventario medido")
    app.segmented_control[0].set_value("Boletas y apoyo mínimo").run()
    if app.exception or not any("22-0269" in x.label for x in app.button):
        raise AssertionError("No se mostró la lista de casillas")
    casilla = next((x for x in app.button if "22-0272 · B1" in x.label), None)
    if casilla is None:
        raise AssertionError("No se encontró 22-0272 B1 en la lista")
    casilla.click().run()
    if app.exception or app.session_state["boletas_casilla_seleccionada"] != ("22-0272", "B1"):
        raise AssertionError("La casilla no se enlazó con el mapa")
    if not any("Sede marcada y mapa centrado" in x.value for x in app.info):
        raise AssertionError("La ficha no confirmó el zoom a la sede")

    resultados = {}
    app.segmented_control[0].set_value("Cuatro preguntas").run()
    for pregunta in PREGUNTAS:
        app.segmented_control[1].set_value(pregunta).run()
        if app.exception:
            raise AssertionError(f"Error en {pregunta}: {app.exception[0].message}")
        if "Partido a explorar" not in [x.label for x in app.selectbox]:
            raise AssertionError(f"Falta el piloto en {pregunta}")
        if pregunta == PREGUNTAS[0]:
            capa = next(x for x in app.segmented_control if x.label == "Vista del mapa")
            mapa = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
            sedes = next(x for x in mapa["layers"] if x.get("id") == "sedes")
            if capa.value != "Sedes de casillas" or not sedes["data"]:
                raise AssertionError("Las sedes de casillas no aparecen al abrir el mapa")
            if not any("leyenda-mapa" in x.proto.body and "leyenda-sede" in x.proto.body
                       for x in app.get("html")):
                raise AssertionError("Falta la simbología visual de secciones y sedes")
            if not any("Ventaja amplia ≥10 pp" in x.proto.body and "Pérdida cercana ≤10 pp" in x.proto.body
                       for x in app.get("html")):
                raise AssertionError("La leyenda no usa las clases comunes de 10 pp")
        if pregunta == PREGUNTAS[1] and not any("15 rasgos" in x.value for x in app.caption):
            raise AssertionError("El perfil no aclara que compara los 15 rasgos CPV")
        if pregunta == PREGUNTAS[2] and not any("247 campos" in x.value for x in app.caption):
            raise AssertionError("No aparece la nueva comparación de ML con CPV ampliado")
        if pregunta == PREGUNTAS[3]:
            mapas = app.get("deck_gl_json_chart")
            if not mapas or not json.loads(mapas[0].proto.json)["layers"]:
                raise AssertionError("Falta el mapa interactivo de esfuerzo")
        resultados[pregunta] = {"tablas": len(app.dataframe), "graficas": len(app.get("vega_lite_chart"))}
    return {"archivos_verificados": len(manifiesto["archivos"]),
            "casilla_enlazada": "22-0272 B1", "preguntas": resultados}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paquete", type=Path)
    print(json.dumps(comprobar(parser.parse_args().paquete), ensure_ascii=False, indent=2))
