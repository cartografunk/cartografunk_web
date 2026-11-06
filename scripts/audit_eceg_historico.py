"""Audita el origen de claves 2024 sin CPV usando el histórico oficial del INE.

Requiere el CSV local exportado del ACCDB oficial; véase CPV_SIN_CRUCE.md.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "electoral"
SALIDA = ROOT / "docs" / "electoral" / "cpv_sin_cruce_origen.csv"


def auditar() -> pd.DataFrame:
    historico = pd.read_csv(DATA / "historico_secciones_ine_2025.csv", dtype=str,
                            encoding="utf-8-sig").fillna("")
    historico["ID_SECCION"] = (historico.cve_ent.str.zfill(2) + "-"
                              + historico.seccion.str.zfill(4))
    if historico.ID_SECCION.duplicated().any():
        raise ValueError("Claves duplicadas en el histórico INE")
    cpv = set(pd.read_parquet(DATA / "cpv_2020_seccion.parquet", columns=["ID_SECCION"]).ID_SECCION)
    votos = pd.read_parquet(DATA / "presidencia_2024_seccion.parquet",
                            columns=["ID_SECCION", "ID_ESTADO", "LISTA_NOMINAL", "estado"])
    votos = votos.loc[votos.estado.ne("extranjero") & ~votos.ID_SECCION.isin(cpv)]
    cruce = votos.merge(historico[["ID_SECCION", "PRIMER_MOVIMIENTO"]], on="ID_SECCION",
                        how="left", validate="one_to_one")
    if cruce.PRIMER_MOVIMIENTO.isna().any():
        raise ValueError("Faltan claves 2024 en el histórico INE")
    menciones = cruce.PRIMER_MOVIMIENTO.str.findall(r"2021|2022|2023")
    if not menciones.map(lambda valores: len(set(valores)) == 1).all():
        raise ValueError("Hay movimientos con cero o varios años 2021–2023")
    anos = menciones.str[0]
    cruce["ano_primer_movimiento"] = anos.astype(int)
    salida = cruce.groupby(["ID_ESTADO", "ano_primer_movimiento"], observed=True).agg(
        secciones=("ID_SECCION", "size"), lista_nominal_2024=("LISTA_NOMINAL", "sum")
    ).reset_index()
    salida.to_csv(SALIDA, index=False, encoding="utf-8-sig")
    return salida


if __name__ == "__main__":
    tabla = auditar()
    print(tabla.groupby("ano_primer_movimiento")[["secciones", "lista_nominal_2024"]].sum().to_string())
