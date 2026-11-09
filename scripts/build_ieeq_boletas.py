"""Unifica resultados por sección conservando año, cargo y opción de voto.

Los Parquet resultantes son locales. Una opción (partido o combinación de
coalición) sigue siendo una columna distinta: este módulo no reasigna votos a
candidaturas ni mezcla boletas de cargos diferentes.
"""

from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FUENTES = ROOT / "data/electoral/fuentes_ieeq"
SALIDA = ROOT / "data/electoral/ieeq_local"
ADMIN = {
    "ID_ESTADO", "NOMBRE_ESTADO", "ESTADO", "ID_DISTRITO_LOCAL",
    "CABECERA_DISTRITAL_LOCAL", "ID_DISTRITO_FEDERAL", "CABECERA_DISTRITAL_FEDERAL",
    "ID_MUNICIPIO", "MUNICIPIO", "SECCION", "ID_SECCION", "TIPO_CASILLA",
    "ID_CASILLA", "EXT_CONTIGUA", "CASILLA", "UBICACION_CASILLA",
    "NUM_VOTOS_VALIDOS", "NUM_VOTOS_CAN_NREG", "NO_REGISTRADAS", "NULOS",
    "NUM_VOTOS_NULOS", "TOTAL_VOTOS", "LISTA_NOMINAL", "ESTATUS_ACTA",
    "TRIBUNAL", "OBSERVACIONES", "RUTA_ACTA", "CASILLAS",
    "ACTAS_CASILLA-MEC", "CIRCUNSCRIPCION", "estado", "votos_casillas_s",
    "n_casillas_s", "votos_en_lista",
}


def _xlsx(archivo: str, hoja: str, *, zip_2018: bool = False) -> pd.DataFrame:
    if zip_2018:
        with ZipFile(FUENTES / "2018_tablas_resultados.zip") as z:
            return pd.read_excel(BytesIO(z.read(archivo)), sheet_name=hoja)
    return pd.read_excel(FUENTES / archivo, sheet_name=hoja, header=1)


def _csv_2024() -> pd.DataFrame:
    with ZipFile(FUENTES / "2024_resultados_qro.zip") as z:
        nombre = next(n for n in z.namelist() if n.endswith("QRO_AYUN_RESULTADOS_2024.csv"))
        return pd.read_csv(z.open(nombre), low_memory=False, encoding="latin-1")


def normalizar_boleta(df: pd.DataFrame, anio: int, cargo: str, fuente: str,
                      *, casillas: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve totales seccionales y votos por opción sin perder la boleta."""
    d = df.copy()
    d.columns = d.columns.astype(str).str.strip()
    if casillas:
        d = d.loc[d.TIPO_CASILLA.astype(str).str.upper().str.strip().isin(("B", "C", "E"))].copy()
    d["SECCION"] = pd.to_numeric(d.SECCION, errors="coerce")
    d["ID_MUNICIPIO"] = pd.to_numeric(d.ID_MUNICIPIO, errors="coerce")
    d = d.loc[d.SECCION.gt(0) & d.ID_MUNICIPIO.gt(0)].copy()
    d["ID_SECCION"] = "22-" + d.SECCION.astype(int).astype(str).str.zfill(4)
    opciones = [c for c in d if c not in ADMIN and not c.startswith(("cand_", "Unnamed:"))
                and pd.to_numeric(d[c], errors="coerce").notna().any()]
    if not opciones:
        raise ValueError(f"{fuente}: no hay columnas de opciones de voto")
    for c in [*opciones, "TOTAL_VOTOS", "LISTA_NOMINAL"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    grupos = ["ID_SECCION", "ID_MUNICIPIO"]
    agregados = d.groupby(grupos, as_index=False)[[*opciones, "TOTAL_VOTOS", "LISTA_NOMINAL"]].sum()
    if agregados.ID_SECCION.duplicated().any():
        raise ValueError(f"{fuente}: sección con más de un municipio")
    base = agregados[grupos + ["TOTAL_VOTOS", "LISTA_NOMINAL"]].copy()
    base.insert(0, "ANIO", anio)
    base.insert(1, "CARGO", cargo)
    base["FUENTE"] = fuente
    votos = agregados.melt(id_vars=grupos, value_vars=opciones,
                           var_name="OPCION", value_name="VOTOS")
    votos.insert(0, "ANIO", anio)
    votos.insert(1, "CARGO", cargo)
    votos["FUENTE"] = fuente
    return base, votos


def construir() -> dict:
    ayu_2024 = _csv_2024()
    entradas = [
        (_xlsx("2018_SEE_AYUN_QRO_CAS.xlsx", 0, zip_2018=True), 2018,
         "ayuntamiento", "IEEQ 2018 tablas de resultados"),
        (_xlsx("2021_ayuntamientos.xlsx", "Casilla"), 2021,
         "ayuntamiento", "IEEQ 2021 Ayuntamiento.xlsx"),
        (_xlsx("2021_gubernatura.xlsx", "Casilla"), 2021,
         "gubernatura", "IEEQ 2021 Gubernatura.xlsx"),
        (ayu_2024, 2024, "ayuntamiento", "IEEQ 2024 resultados ayuntamientos"),
        (pd.read_parquet(ROOT / "data/electoral/senadurias_2024_seccion.parquet")
         .query("ID_ESTADO == 22 and SECCION > 0"), 2024,
         "senado", "INE 2024 senadurías por sección"),
    ]
    boletas, votos = [], []
    for df, anio, cargo, fuente in entradas:
        b, v = normalizar_boleta(df, anio, cargo, fuente,
                                 casillas=cargo != "senado")
        boletas.append(b)
        votos.append(v)
    b = pd.concat(boletas, ignore_index=True)
    v = pd.concat(votos, ignore_index=True)
    cruce = pd.read_parquet(SALIDA / "crosswalk_qro_2018_2021_2024_referencias.parquet",
                            columns=["ID_SECCION", "CATEGORIA", "ESTABLE_EN_AMBAS_REFERENCIAS"])
    b = b.merge(cruce, on="ID_SECCION", how="left", validate="many_to_one")
    b["CPV_COMPARABLE_2024"] = b.ANIO.eq(2024) & b.CATEGORIA.eq(
        "sin_cambio_cartografico_referencia")
    cpv = pd.read_parquet(ROOT / "data/electoral/cpv_2020_seccion.parquet")
    b = b.merge(cpv, on="ID_SECCION", how="left", validate="many_to_one")
    rasgos = [c for c in cpv if c != "ID_SECCION"]
    b.loc[~b.CPV_COMPARABLE_2024, rasgos] = pd.NA
    if b.duplicated(["ANIO", "CARGO", "ID_SECCION"]).any() or v.duplicated(
        ["ANIO", "CARGO", "ID_SECCION", "OPCION"]
    ).any():
        raise ValueError("Llaves repetidas en panel de boletas")
    SALIDA.mkdir(parents=True, exist_ok=True)
    b.to_parquet(SALIDA / "boletas_qro_2018_2024_seccion.parquet", index=False)
    v.to_parquet(SALIDA / "votos_opcion_qro_2018_2024_seccion.parquet", index=False)
    cas = ayu_2024.loc[ayu_2024.TIPO_CASILLA.isin(("B", "C", "E"))].copy()
    cas["SECCION"] = pd.to_numeric(cas.SECCION, errors="coerce")
    cas["ID_SECCION"] = "22-" + cas.SECCION.astype(int).astype(str).str.zfill(4)
    llaves = ["ID_SECCION", "TIPO_CASILLA", "ID_CASILLA"]
    cas["ORDEN_CASILLA"] = cas.groupby(llaves).cumcount()
    referencia = pd.read_parquet(SALIDA / "dip_local_mr_2024_casilla.parquet")
    referencia = referencia.loc[referencia.TIPO_NORMALIZADO.isin(("B", "C", "E"))].copy()
    referencia["ORDEN_CASILLA"] = referencia.groupby(
        ["ID_SECCION", "TIPO_NORMALIZADO", "ID_CASILLA"]).cumcount()
    cas = cas.merge(referencia[["ID_SECCION", "TIPO_NORMALIZADO", "ID_CASILLA",
                               "ORDEN_CASILLA", "LISTA_NOMINAL", "CASILLA_ETIQUETA"]],
                    left_on=[*llaves, "ORDEN_CASILLA"],
                    right_on=["ID_SECCION", "TIPO_NORMALIZADO", "ID_CASILLA", "ORDEN_CASILLA"],
                    how="left", validate="one_to_one", suffixes=("", "_DIP"))
    if len(cas) != len(referencia) or cas.CASILLA_ETIQUETA.isna().any() or not (
        cas.LISTA_NOMINAL.eq(cas.LISTA_NOMINAL_DIP)
    ).all():
        raise ValueError("Las casillas de Ayuntamiento 2024 no cuadran con la referencia IEEQ")
    cas = cas.drop(columns=["TIPO_NORMALIZADO", "LISTA_NOMINAL_DIP"])
    cas.to_parquet(SALIDA / "ayuntamiento_2024_casilla.parquet", index=False)
    casillas_todas = []
    for df, anio, cargo, _ in entradas[:4]:
        if anio == 2024:
            filas = cas.copy()
        else:
            filas = df.loc[df.TIPO_CASILLA.astype(str).str.upper().isin(("B", "C", "E"))].copy()
            filas["ID_SECCION"] = "22-" + pd.to_numeric(
                filas.SECCION, errors="raise").astype(int).astype(str).str.zfill(4)
            filas["CASILLA_ETIQUETA"] = filas.CASILLA.astype(str).str.upper().map(
                lambda s: "B1" if s == "B" else re.sub(
                    r"^(C|E\d+C)0+(\d+)$", r"\1\2", s))
        filas["ANIO"] = anio
        filas["CARGO"] = cargo
        filas["ID_MUNICIPIO"] = pd.to_numeric(filas.ID_MUNICIPIO, errors="raise").astype(int)
        filas["FILA_FUENTE"] = range(1, len(filas) + 1)
        casillas_todas.append(filas)
    casillas = pd.concat(casillas_todas, ignore_index=True)
    if casillas.duplicated(["ANIO", "CARGO", "ID_SECCION", "CASILLA_ETIQUETA"]).any():
        raise ValueError("Casilla histórica duplicada tras normalizar etiqueta")
    meta = ["ANIO", "CARGO", "ID_SECCION", "ID_MUNICIPIO", "CASILLA_ETIQUETA",
            "TIPO_CASILLA", "FILA_FUENTE"]
    opciones_casilla = [c for c in v.OPCION.unique() if c in casillas.columns]
    casillas = casillas[meta + ["TOTAL_VOTOS", "LISTA_NOMINAL"] + opciones_casilla].copy()
    for c in ["TOTAL_VOTOS", "LISTA_NOMINAL", *opciones_casilla]:
        casillas[c] = pd.to_numeric(casillas[c], errors="coerce")
    casillas.to_parquet(SALIDA / "boletas_qro_2018_2024_casilla.parquet", index=False)
    resumen = {f"{anio}_{cargo}": {"secciones": len(g),
                                   "lista_nominal": int(g.LISTA_NOMINAL.sum()),
                                   "cpv_comparable_2024": int(g.CPV_COMPARABLE_2024.sum())}
               for (anio, cargo), g in b.groupby(["ANIO", "CARGO"])}
    resumen["ayuntamiento_2024_casillas"] = {"casillas_bce": len(cas),
                                              "casillas_con_etiqueta_cotejada": int(cas.CASILLA_ETIQUETA.notna().sum())}
    resumen["casillas_locales_por_boleta"] = {
        f"{anio}_{cargo}": len(g) for (anio, cargo), g in
        casillas.groupby(["ANIO", "CARGO"])}
    (SALIDA / "boletas_qro_2018_2024_auditoria.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


if __name__ == "__main__":
    print(json.dumps(construir(), ensure_ascii=False, indent=2))
