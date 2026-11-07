"""Agrupa secciones 2021 y 2024 conectadas, sin repartir votos antiguos.

Las tablas de entrada ya contienen la suma B+C+E de cada sección. Si una
sección se divide o fusiona, se suman todos sus antecedentes y destinos en
un mismo grupo de comparación. Cada voto de ambos años se cuenta una vez.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from electoral.reparto_ieeq import atribuir_partidos


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/electoral/ieeq_local"


def grupos_relacionados(anteriores: pd.Index, actuales: pd.Index,
                        enlaces: pd.DataFrame) -> pd.DataFrame:
    """Componentes del grafo bipartito origen 2021 ↔ destino 2024."""
    previas, nuevas = set(anteriores), set(actuales)
    if set(enlaces.ORIGEN) != previas or set(enlaces.DESTINO) != nuevas:
        raise ValueError("El cruce no cubre todas las secciones de ambos años")
    parent: dict[tuple[int, str], tuple[int, str]] = {}

    def find(node: tuple[int, str]) -> tuple[int, str]:
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(left: tuple[int, str], right: tuple[int, str]) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)

    for origen, destino in enlaces[["ORIGEN", "DESTINO"]].itertuples(index=False, name=None):
        union((2021, origen), (2024, destino))
    nodes = [(2021, key) for key in sorted(previas)] + [(2024, key) for key in sorted(nuevas)]
    roots = {node: find(node) for node in nodes}
    by_root: dict[tuple[int, str], list[tuple[int, str]]] = {}
    for node, root in roots.items():
        by_root.setdefault(root, []).append(node)
    group_name = {root: min(key for year, key in members if year == 2021)
                  for root, members in by_root.items()}
    frame = pd.DataFrame([{"ANIO": year, "ID_SECCION": key,
                           "ID_GRUPO_2021_2024": group_name[roots[(year, key)]]}
                          for year, key in nodes])
    sizes = frame.groupby(["ID_GRUPO_2021_2024", "ANIO"]).size().unstack(fill_value=0)
    frame["SECCIONES_2021_EN_GRUPO"] = frame.ID_GRUPO_2021_2024.map(sizes[2021])
    frame["SECCIONES_2024_EN_GRUPO"] = frame.ID_GRUPO_2021_2024.map(sizes[2024])
    return frame


def _sumar_votos(secciones: pd.DataFrame, anio: int, mapa: pd.DataFrame) -> pd.DataFrame:
    atribuidos = atribuir_partidos(secciones, anio)
    keys = mapa.loc[mapa.ANIO.eq(anio), ["ID_SECCION", "ID_GRUPO_2021_2024"]]
    unidos = atribuidos.merge(keys, on="ID_SECCION", validate="one_to_one")
    columnas = [c for c in atribuidos.columns if c != "ID_SECCION"]
    agrupado = unidos.groupby("ID_GRUPO_2021_2024", as_index=False)[columnas].sum()
    for column in ("VOTOS_VALIDOS", "TOTAL_VOTOS", "LISTA_NOMINAL"):
        if abs(agrupado[column].sum() - atribuidos[column].sum()) > 1e-7:
            raise ValueError(f"Se perdieron o duplicaron {column} de {anio}")
    return agrupado


def construir(data: Path = DATA) -> dict:
    v21 = pd.read_parquet(data / "dip_local_mr_2021_seccion_bce.parquet")
    v24 = pd.read_parquet(data / "dip_local_mr_2024_seccion_bce.parquet")
    enlaces = pd.read_parquet(data / "crosswalk_eceg_2021_a_2024.parquet")
    if v21.ID_SECCION.duplicated().any() or v24.ID_SECCION.duplicated().any():
        raise ValueError("Sección duplicada en el archivo electoral")
    mapa = grupos_relacionados(v21.ID_SECCION, v24.ID_SECCION, enlaces)
    a21, a24 = (_sumar_votos(v, y, mapa) for v, y in ((v21, 2021), (v24, 2024)))
    tamaños = mapa.drop_duplicates("ID_GRUPO_2021_2024")
    singleton = tamaños.SECCIONES_2021_EN_GRUPO.eq(1) & tamaños.SECCIONES_2024_EN_GRUPO.eq(1)
    data.mkdir(parents=True, exist_ok=True)
    mapa.to_csv(data / "mapa_grupos_secciones_2021_2024.csv", index=False, encoding="utf-8-sig")
    a21.to_parquet(data / "dip_local_mr_2021_agrupado_2021_2024.parquet", index=False)
    a24.to_parquet(data / "dip_local_mr_2024_agrupado_2021_2024.parquet", index=False)
    resumen = {
        "secciones_2021": len(v21), "secciones_2024": len(v24),
        "grupos_comparables": len(tamaños),
        "grupos_uno_a_uno": int(singleton.sum()),
        "grupos_reconfigurados": int((~singleton).sum()),
        "max_secciones_2021_en_grupo": int(tamaños.SECCIONES_2021_EN_GRUPO.max()),
        "max_secciones_2024_en_grupo": int(tamaños.SECCIONES_2024_EN_GRUPO.max()),
        "lista_nominal_2024_agrupada": int(a24.LISTA_NOMINAL.sum()),
        "lista_nominal_2021_agrupada": int(a21.LISTA_NOMINAL.sum()),
        "nota": "Se suman secciones conectadas por superposición. No se dividen votos ni se afirma continuidad individual.",
    }
    (data / "resumen_grupos_secciones_2021_2024.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return resumen


if __name__ == "__main__":
    print(json.dumps(construir(), indent=2, ensure_ascii=False))
