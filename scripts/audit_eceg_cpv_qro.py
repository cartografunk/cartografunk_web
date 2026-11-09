"""Audita el ECEG completo en las secciones CPV comparables de Querétaro.

Salida local: data/electoral/ieeq_local/auditoria_variables_eceg_2020.csv.
No usa votos para seleccionar indicadores.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from pathlib import Path

import pandas as pd

from electoral.cpv import ETIQUETAS, VARIABLES


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/electoral"
FUENTE = DATA / "eceg_2020_seccion.parquet"
DIAGNOSTICO = DATA / "ieeq_local/diagnostico_casillas_cpv_2024.parquet"
SALIDA = DATA / "ieeq_local/auditoria_variables_eceg_2020.csv"

# Pares con denominador interpretable; su inclusión en el modelo requiere revisión.
CANDIDATOS = {
    "PCON_DISC": ("Discapacidad", "POBTOT"),
    "PNACOE": ("Nació en otra entidad", "POBTOT"),
    "P15SEC_CO": ("Secundaria completa (15+)", "P_15YMAS"),
    "PEA_F": ("Participación económica de mujeres (12+)", "P_12YMAS_F"),
    "PEA_M": ("Participación económica de hombres (12+)", "P_12YMAS_M"),
    "PDER_IMSS": ("Afiliación al IMSS", "POBTOT"),
    "VPH_1CUART": ("Viviendas de un cuarto", "VIVPAR_HAB"),
    "VPH_PC": ("Viviendas con computadora", "VIVPAR_HAB"),
    "VPH_CEL": ("Viviendas con celular", "VIVPAR_HAB"),
    "VPH_MOTO": ("Viviendas con motocicleta", "VIVPAR_HAB"),
    "VPH_BICI": ("Viviendas con bicicleta", "VIVPAR_HAB"),
    "VPH_S_ELEC": ("Viviendas sin electricidad", "VIVPAR_HAB"),
}


def correlacion_pares(a: pd.Series, b: pd.Series) -> float:
    """Pearson por pares válidos sin la rutina nativa que falla en este entorno."""
    pares = [(float(x), float(y)) for x, y in zip(a, b) if pd.notna(x) and pd.notna(y)]
    if len(pares) < 3:
        return float("nan")
    mx = math.fsum(x for x, _ in pares) / len(pares)
    my = math.fsum(y for _, y in pares) / len(pares)
    cov = math.fsum((x-mx) * (y-my) for x, y in pares)
    va = math.fsum((x-mx)**2 for x, _ in pares)
    vb = math.fsum((y-my)**2 for _, y in pares)
    return cov / math.sqrt(va * vb) if va > 0 and vb > 0 else float("nan")


def auditar(fuente: pd.DataFrame, claves: set[str], diccionario: pd.DataFrame) -> pd.DataFrame:
    muestra = fuente.loc[fuente.ID_SECCION.isin(claves)].copy()
    if len(muestra) != len(claves) or muestra.ID_SECCION.duplicated().any():
        raise ValueError("Las claves comparables no empatan uno a uno con ECEG")
    descriptores = diccionario.set_index("Mnemónico")
    filas = []
    for columna in fuente.columns:
        if columna in {"ID_ENTIDAD", "ID_SECCION"}:
            continue
        meta = descriptores.loc[columna] if columna in descriptores.index else None
        valores = pd.to_numeric(muestra[columna], errors="coerce")
        fila = {
            "columna": columna,
            "tema": str(meta["Tema"]) if meta is not None else "Sin descriptor",
            "indicador": str(meta["Indicador"]) if meta is not None else "",
            "insumo_de_15": columna in {c for _, _, num, den in VARIABLES for c in (num, den)},
            "secciones_con_dato": int(valores.notna().sum()),
            "cobertura_pct": round(100 * valores.notna().mean(), 2),
            "valores_distintos": int(valores.nunique()),
            "candidato": columna in CANDIDATOS,
            "tasa_valida_pct": "",
            "mediana_tasa_pct": "",
            "max_correlacion_15": "",
            "rasgo_mas_parecido": "",
        }
        if columna in CANDIDATOS:
            denominador = pd.to_numeric(muestra[CANDIDATOS[columna][1]], errors="coerce")
            tasa = (100 * valores / denominador.where(denominador.gt(0)))
            tasa = tasa.where(tasa.between(0, 100))
            fila["tasa_valida_pct"] = round(100 * tasa.notna().mean(), 2)
            fila["mediana_tasa_pct"] = round(float(tasa.median()), 2) if tasa.notna().any() else ""
        filas.append(fila)
    return pd.DataFrame(filas)


def main() -> None:
    zip_path = Path.home() / "Downloads/eceg_2020_csv.zip"
    with zipfile.ZipFile(zip_path) as archivo:
        contenido = archivo.read(
            "diccionario_de_datos/Descriptor_indicadores_ECEG_Seccion_2020.csv.csv")
    diccionario = pd.read_csv(io.BytesIO(contenido), encoding="latin1")
    fuente = pd.read_parquet(FUENTE)
    diagnostico = pd.read_parquet(DIAGNOSTICO, columns=["ID_SECCION", "CPV_COMPARABLE"])
    claves = set(diagnostico.loc[diagnostico.CPV_COMPARABLE, "ID_SECCION"])
    informe = auditar(fuente, claves, diccionario)
    compactas = pd.read_parquet(DATA / "cpv_2020_seccion.parquet")
    compactas = compactas.loc[compactas.ID_SECCION.isin(claves)].set_index("ID_SECCION")
    muestra = fuente.loc[fuente.ID_SECCION.isin(claves)].set_index("ID_SECCION")
    for columna, (_, den) in CANDIDATOS.items():
        tasa = 100 * pd.to_numeric(muestra[columna], errors="coerce") / pd.to_numeric(
            muestra[den], errors="coerce").replace(0, float("nan"))
        tasa = tasa.where(tasa.between(0, 100)).reindex(compactas.index)
        correlaciones = pd.Series({nombre: abs(correlacion_pares(compactas[nombre], tasa))
                                   for nombre in ETIQUETAS}).dropna()
        if not correlaciones.empty:
            principal = correlaciones.idxmax()
            informe.loc[informe.columna.eq(columna), "max_correlacion_15"] = round(
                float(correlaciones[principal]), 3)
            informe.loc[informe.columna.eq(columna), "rasgo_mas_parecido"] = ETIQUETAS[principal]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    informe.to_csv(SALIDA, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    print(f"Secciones comparables: {len(claves)}; indicadores auditados: {len(informe)}")
    print(informe.loc[informe.candidato, ["columna", "tema", "tasa_valida_pct",
                                          "mediana_tasa_pct", "max_correlacion_15",
                                          "rasgo_mas_parecido"]]
          .to_string(index=False))
    print(f"Salida: {SALIDA}")


if __name__ == "__main__":
    main()
