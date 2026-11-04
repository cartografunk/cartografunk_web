"""Rutas de entrada y definiciones de candidaturas de 2024."""

from pathlib import Path


PRESIDENCIA_ZIP = Path(
    r"D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\PRESIDENCIA_2024.zip"
)
DIPUTACIONES_ZIP = Path(
    r"D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\DIPUTACIONES_FED_MR_2024.zip"
)
SENADURIAS_ZIP = Path(
    r"D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\SENADURÍAS_MR_2024.zip"
)
MGE_ZIP = Path(r"D:\(5) WORK\CONJUNTOS DE DATOS\INE MGE\MGE 2024-20240515T221823Z-001.zip")
GEOMETRIA_TOLERANCIA_M = 25.0
GEOMETRIA_PARQUET = (
    Path(__file__).resolve().parents[1] / "data" / "electoral" / "secciones_2024_geom.parquet"
)
PRESIDENCIA_PARQUET = (
    Path(__file__).resolve().parents[1] / "data" / "electoral" / "presidencia_2024_seccion.parquet"
)
DIPUTACIONES_PARQUET = (
    Path(__file__).resolve().parents[1] / "data" / "electoral" / "diputaciones_2024_seccion.parquet"
)
SENADURIAS_PARQUET = (
    Path(__file__).resolve().parents[1] / "data" / "electoral" / "senadurias_2024_seccion.parquet"
)

CANDIDATURAS = {
    "PAN_PRI_PRD": ("PAN", "PRI", "PRD", "PAN_PRI_PRD", "PAN_PRI", "PAN_PRD", "PRI_PRD"),
    "PVEM_PT_MORENA": (
        "PVEM", "PT", "MORENA", "PVEM_PT_MORENA", "PVEM_PT", "PVEM_MORENA", "PT_MORENA"
    ),
    "MC": ("MC",),
}

NOTAS_CALIDAD_DEMO = (
    "56 secciones sin resultado en Presidencia 2024.",
    "249 polígonos sin fila de resultados; aparecen en gris.",
    "32 filas de voto en el extranjero están fuera del mapa.",
    "19 secciones siguen con más votos en lista que personas en lista nominal; la diferencia no está explicada.",
    "La geometría usa EPSG:32614 como supuesto de trabajo; el CRS original no está confirmado por metadatos.",
    "La Presidencia no se gana por sección ni por distrito: estas escalas sirven para explorar resultados.",
    "CPV no integrado.",
)
