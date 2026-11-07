"""Audita por separado clave seccional, distrito local y domicilio de casilla.

La superposición mide superficie, no traslado de electores ni equivalencia de votos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/electoral/ieeq_local"


def distrito_por_seccion(path: Path) -> pd.Series:
    rows = pd.read_parquet(path, columns=["ID_SECCION", "ID_DISTRITO_LOCAL", "TIPO_NORMALIZADO"])
    rows = rows.loc[rows.TIPO_NORMALIZADO.isin(["B", "C", "E"])]
    counts = rows.groupby("ID_SECCION").ID_DISTRITO_LOCAL.nunique()
    if counts.gt(1).any():
        raise ValueError(f"Secciones con varios distritos locales: {counts[counts.gt(1)].index.tolist()}")
    return rows.groupby("ID_SECCION").ID_DISTRITO_LOCAL.first()


def domicilios_por_seccion(path: Path) -> dict[str, set[str]]:
    rows = pd.read_parquet(path, columns=["ID_SECCION", "DOMICILIO_NORMALIZADO"])
    return {key: {value for value in group.DOMICILIO_NORMALIZADO if value}
            for key, group in rows.groupby("ID_SECCION")}


def auditar(data: Path = DATA) -> dict:
    d21 = distrito_por_seccion(data / "dip_local_mr_2021_casilla.parquet")
    d24 = distrito_por_seccion(data / "dip_local_mr_2024_casilla.parquet")
    a21 = domicilios_por_seccion(data / "encarte_qro_2021_claves.parquet")
    a24 = domicilios_por_seccion(data / "encarte_qro_2024_claves.parquet")
    links = pd.read_parquet(data / "crosswalk_eceg_2021_a_2024.parquet")
    previas, actuales = set(d21.index), set(d24.index)
    compartidas, desaparecidas, nuevas = previas & actuales, previas - actuales, actuales - previas
    if set(links.ORIGEN) != previas or set(links.DESTINO) != actuales:
        raise ValueError("El crosswalk no cubre las secciones de ambos años")
    if set(a21) != previas or set(a24) != actuales:
        raise ValueError("Los encartes no cubren las secciones de ambos años")

    # La mayor fracción del polígono destino sólo elige un referente de área.
    dominant = links.sort_values(["DESTINO", "FRACCION_DESTINO", "ORIGEN"],
                                 ascending=[True, False, True]).drop_duplicates("DESTINO")
    origin = dominant.set_index("DESTINO")
    n_origins = links.groupby("DESTINO").size()
    records = []
    for destino in sorted(actuales):
        antecedente = destino if destino in compartidas else origin.at[destino, "ORIGEN"]
        same_address = bool(a21[antecedente] & a24[destino])
        records.append({
            "ID_SECCION_2024": destino,
            "ID_SECCION_2021_REFERENCIA": antecedente,
            "CLAVE_CONSERVADA": destino in compartidas,
            "ORIGEN_DESAPARECIO": antecedente in desaparecidas,
            "DISTRITO_LOCAL_2021_REFERENCIA": int(d21[antecedente]),
            "DISTRITO_LOCAL_2024": int(d24[destino]),
            "DISTRITO_LOCAL_CAMBIO": int(d21[antecedente]) != int(d24[destino]),
            "ALGUN_DOMICILIO_TEXTUAL_EXACTO": same_address,
            "DOMICILIOS_2021_EXTRAIDOS": len(a21[antecedente]),
            "DOMICILIOS_2024_EXTRAIDOS": len(a24[destino]),
            "NUM_ORIGENES_GEOMETRICOS": int(n_origins[destino]),
            "FRACCION_AREA_DESTINO_REFERENCIA": float(origin.at[destino, "FRACCION_DESTINO"]),
        })
    frame = pd.DataFrame(records)
    frame.to_csv(data / "auditoria_clave_distrito_domicilio_2021_2024.csv",
                 index=False, encoding="utf-8-sig")
    shared = frame.loc[frame.CLAVE_CONSERVADA]
    born = frame.loc[~frame.CLAVE_CONSERVADA]
    dead_to_new = links.loc[links.ORIGEN.isin(desaparecidas) & links.DESTINO.isin(nuevas)]
    shared_to_new = links.loc[links.ORIGEN.isin(compartidas) & links.DESTINO.isin(nuevas)]
    dead_to_shared = links.loc[links.ORIGEN.isin(desaparecidas) & links.DESTINO.isin(compartidas)]
    result = {
        "secciones_2021": len(previas), "secciones_2024": len(actuales),
        "claves_conservadas": len(compartidas),
        "claves_desaparecidas_2021": sorted(desaparecidas),
        "claves_nuevas_2024": len(nuevas),
        "conservadas_cambio_distrito_local": int(shared.DISTRITO_LOCAL_CAMBIO.sum()),
        "conservadas_algun_domicilio_textual_exacto": int(shared.ALGUN_DOMICILIO_TEXTUAL_EXACTO.sum()),
        "conservadas_sin_domicilio_textual_exacto": int((~shared.ALGUN_DOMICILIO_TEXTUAL_EXACTO).sum()),
        "nuevas_referencia_area_cambio_distrito_local": int(born.DISTRITO_LOCAL_CAMBIO.sum()),
        "nuevas_referencia_area_mismo_distrito_local": int((~born.DISTRITO_LOCAL_CAMBIO).sum()),
        "nuevas_referencia_area_origen_desaparecido": int(born.ORIGEN_DESAPARECIO.sum()),
        "nuevas_referencia_area_domicilio_textual_exacto": int(born.ALGUN_DOMICILIO_TEXTUAL_EXACTO.sum()),
        "nuevas_con_varios_origenes_geometricos": int(born.NUM_ORIGENES_GEOMETRICOS.gt(1).sum()),
        "enlaces_desaparecida_a_nueva": len(dead_to_new),
        "enlaces_conservada_a_nueva": len(shared_to_new),
        "enlaces_desaparecida_a_conservada": len(dead_to_shared),
        "nota": "Distrito local, clave y texto del domicilio son hechos distintos. Domicilio no idéntico no prueba traslado físico; área no reparte electores.",
    }
    (data / "auditoria_clave_distrito_domicilio_2021_2024.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(auditar(), indent=2, ensure_ascii=False))
