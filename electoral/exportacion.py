"""Exportación local del diagnóstico de Presidencia 2024 a Excel."""

from io import BytesIO

import pandas as pd

from electoral.clasificacion import CLASES, Umbrales
from electoral.config import NOTAS_CALIDAD_DEMO, REGLAS_METODOLOGIA_DEMO


def _secciones(resultados: pd.DataFrame) -> pd.DataFrame:
    d = resultados.loc[resultados["estado"].eq("con_resultado")].copy()
    columnas = {
        "ID_SECCION": "Sección", "MUNICIPIO": "Municipio", "clase": "Clase",
        "margen_votos": "Margen (votos)", "faltante_votos": "Faltante (votos)",
        "margen_pct": "Margen (%)", "faltante_pct": "Faltante (%)",
        "votos_para_ganar": "Votos para ganar", "abstencion": "Abstención",
        "participacion_pct": "Participación (%)",
    }
    return d[list(columnas)].rename(columns=columnas)


def _priorizacion(tabla: pd.DataFrame, presupuesto: float) -> pd.DataFrame:
    columnas = {
        "ID_SECCION": "Sección", "MUNICIPIO": "Municipio",
        "ID_DISTRITO_FEDERAL": "Distrito federal",
        "votos_para_ganar": "Votos para ganar", "abstencion": "Abstención",
        "costo_por_voto": "Costo por voto (pesos)",
        "costo_estimado": "Costo estimado (pesos)",
        "descartar": "Descartar", "seleccionada": "Dentro del presupuesto",
    }
    d = tabla[list(columnas)].rename(columns=columnas).copy()
    d["Presupuesto (pesos)"] = presupuesto
    return d


def _distritos(tabla: pd.DataFrame) -> pd.DataFrame:
    columnas = {
        "ID_DISTRITO_FEDERAL": "Distrito federal", "n_secciones": "Secciones",
        "n_con_resultado": "Con resultado", "n_sin_resultado": "Sin resultado",
        "resultado": "Resultado", "clase": "Clase",
        "margen_votos": "Margen (votos)", "faltante_votos": "Faltante (votos)",
        "margen_pct": "Margen (%)", "faltante_pct": "Faltante (%)",
        "votos_para_ganar": "Votos para ganar",
    }
    return tabla[list(columnas)].rename(columns=columnas).copy()


def construir_excel(resultados: pd.DataFrame, parametros: dict) -> bytes:
    """Construye el libro sin modificar tablas de entrada ni escribir archivos."""
    umbrales: Umbrales = parametros.get("umbrales", Umbrales())
    conteos = resultados.loc[resultados["estado"].eq("con_resultado"), "clase"].value_counts()
    resumen = pd.DataFrame([
        ("Candidatura", parametros["candidatura"]),
        ("Estado", parametros["estado"]),
        ("Fecha", parametros["fecha"]),
        ("Competitiva (puntos)", umbrales.competitiva_pp),
        ("Lejana (puntos)", umbrales.lejana_pp),
        ("Sólida (puntos)", umbrales.solida_pp),
        ("Alcanzable (votos)", umbrales.votos_alcanzables),
        *[(clase, int(conteos.get(clase, 0))) for clase in CLASES],
        ("Nota", "Diagnóstico sobre Presidencia 2024; no es un pronóstico."),
    ], columns=["Concepto", "Valor"])
    metodologia = pd.DataFrame({"Regla": REGLAS_METODOLOGIA_DEMO})
    secciones = _secciones(resultados)
    distritos = _distritos(parametros["distritos"])
    calidad = pd.DataFrame({"Nota de calidad": NOTAS_CALIDAD_DEMO})

    hojas = {"Resumen": resumen, "Metodología": metodologia, "Secciones": secciones}
    if "priorizacion" in parametros:
        hojas["Priorización"] = _priorizacion(
            parametros["priorizacion"], float(parametros["presupuesto"])
        )
    hojas["Distritos"] = distritos
    hojas["Calidad"] = calidad

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as escritor:
        negrita = escritor.book.add_format({"bold": True})
        porcentaje = escritor.book.add_format({"num_format": '0.0"%"'})
        for nombre, tabla in hojas.items():
            tabla.to_excel(escritor, sheet_name=nombre, index=False)
            hoja = escritor.sheets[nombre]
            hoja.freeze_panes(1, 0)
            hoja.set_row(0, None, negrita)
            for indice, columna in enumerate(tabla.columns):
                ancho = min(65, max(16, len(columna) + 3))
                if columna.endswith("(%)"):
                    hoja.set_column(indice, indice, ancho, porcentaje)
                else:
                    hoja.set_column(indice, indice, ancho)
    return buffer.getvalue()
