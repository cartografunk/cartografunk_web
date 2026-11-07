"""Normaliza los resultados locales de diputaciones MR del IEEQ, 2018–2024.

Ejecutar con el Python del entorno cartografunk. Los datos originales y las
salidas quedan en data/electoral/ y no deben agregarse a Git.
"""

from __future__ import annotations

import io
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "electoral" / "fuentes_ieeq"
OUTPUT = ROOT / "data" / "electoral" / "ieeq_local"
VOTE_TAIL = ("NUM_VOTOS_VALIDOS", "NUM_VOTOS_CAN_NREG", "NUM_VOTOS_NULOS", "TOTAL_VOTOS")


def _read_sources(source: Path) -> dict[int, tuple[pd.DataFrame, pd.DataFrame]]:
    manifest = json.loads((source / "manifiesto_descargas.json").read_text(encoding="utf-8"))
    for item in manifest:
        p = source / item["archivo"]
        if hashlib.sha256(p.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"SHA-256 distinto al manifiesto: {p.name}")
    with ZipFile(source / "2018_tablas_resultados.zip") as z:
        cas18 = pd.read_excel(io.BytesIO(z.read("2018_SEE_DIP_LOC_MR_QRO_CAS.xlsx")))
        sec18 = pd.read_excel(io.BytesIO(z.read("2018_SEE_DIP_LOC_MR_QRO_SEC.xlsx")))
    book = pd.ExcelFile(source / "2021_diputaciones_mr.xlsx")
    cas21 = pd.read_excel(book, sheet_name="Casilla", header=1)
    sec21 = pd.read_excel(book, sheet_name=2, header=1)
    with ZipFile(source / "2024_resultados_qro.zip") as z:
        member = next(n for n in z.namelist() if n.endswith("QRO_DIP_LOC_RESULTADOS_2024.csv"))
        cas24 = pd.read_csv(io.BytesIO(z.read(member)), encoding="latin-1")
    refs = []
    for district in range(1, 16):
        raw = json.loads((source / f"2024_json_d{district}.json").read_bytes())
        for section in raw["secciones"]:
            if not str(section["clave_seccion"]).isdigit():
                # El visor añade "Voto Anticipado" como sección ficticia.
                continue
            refs.append({
                "ID_ESTADO": 22,
                "SECCION": int(section["clave_seccion"]),
                "TOTAL_VOTOS": int(section["resumen"]["votos_totales"]),
            })
    sec24 = pd.DataFrame(refs)
    return {2018: (cas18, sec18), 2021: (cas21, sec21), 2024: (cas24, sec24)}


def normalize_casillas(year: int, raw: pd.DataFrame) -> pd.DataFrame:
    """Conserva columnas originales y marca exclusiones territoriales y legales."""
    df = raw.loc[pd.to_numeric(raw["ID_ESTADO"], errors="coerce").eq(22)].copy()
    df.insert(0, "FILA_FUENTE", df.index + (2 if year == 2024 else 3 if year == 2021 else 2))
    df.insert(0, "ANIO", year)
    for col in ("ID_ESTADO", "ID_DISTRITO_LOCAL", "SECCION", "ID_CASILLA", "EXT_CONTIGUA"):
        df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")
    df["SECCION_NORMALIZADA"] = df["SECCION"]
    df["CORRECCION_SECCION"] = ""
    if year == 2024:
        # CSV: distrito 10, C03, 433 votos figura en 0861. JSON_D10 del
        # mismo portal la incluye en 0584; JSON_D3 no la incluye en 0861.
        wrong = (
            df["ID_DISTRITO_LOCAL"].eq(10) & df["SECCION"].eq(861)
            & df["TIPO_CASILLA"].eq("C") & df["ID_CASILLA"].eq(3)
            & pd.to_numeric(df["TOTAL_VOTOS"]).eq(433)
        )
        if int(wrong.sum()) != 1:
            raise ValueError("No se pudo corroborar la corrección 2024 C03 0861→0584")
        df.loc[wrong, "SECCION_NORMALIZADA"] = 584
        df.loc[wrong, "CORRECCION_SECCION"] = "JSON_D10.json: sección 0584; CSV original 0861"
    df["ID_SECCION"] = df["ID_ESTADO"].map("{:02d}".format) + "-" + df["SECCION_NORMALIZADA"].map("{:04d}".format)
    df["TIPO_NORMALIZADO"] = df["TIPO_CASILLA"].astype(str).str.upper().str.strip()
    if not df["TIPO_NORMALIZADO"].isin(["B", "C", "E", "S", "A"]).all():
        raise ValueError(f"{year}: tipo de casilla desconocido")
    annulled = df["TRIBUNAL"].eq("Anulada") if "TRIBUNAL" in df else pd.Series(False, index=df.index)
    df["ANULADA_TRIBUNAL"] = annulled.fillna(False).astype(bool)
    df["RECUENTO_DOCUMENTADO"] = (
        df["ESTATUS_ACTA"].eq("Grupo de recuento").fillna(False)
        if "ESTATUS_ACTA" in df else False
    )
    reason = pd.Series("", index=df.index, dtype="string")
    reason.loc[df["TIPO_NORMALIZADO"].eq("S")] = "especial_sin_residencia_seccional"
    reason.loc[df["TIPO_NORMALIZADO"].eq("A")] = "voto_anticipado_sin_residencia_seccional"
    reason.loc[annulled] = "anulada_tribunal"
    df["MOTIVO_EXCLUSION_SECCION"] = reason
    df["INCLUIR_SECCION"] = reason.eq("")
    # El CSV 2024 repite 57 casillas S por MR y RP. No se escoge una copia
    # mediante su orden; el total MR de S se toma del JSON oficial del visor.
    return df


def special_mr(year: int, cas: pd.DataFrame, source: Path) -> pd.DataFrame:
    """Casillas S de MR, asociadas al lugar de instalación, no a residencia."""
    if year != 2024:
        s = cas.loc[cas["TIPO_NORMALIZADO"].eq("S") & ~cas["ANULADA_TRIBUNAL"]]
        return pd.DataFrame({
            "ANIO": year, "ID_DISTRITO_LOCAL": s["ID_DISTRITO_LOCAL"],
            "ID_SECCION_INSTALACION": s["ID_SECCION"],
            "NUMERO_CASILLA": s["ID_CASILLA"],
            "VOTOS_MR": pd.to_numeric(s["TOTAL_VOTOS"]).astype(int),
            "FUENTE_ESPECIAL": "tabla IEEQ de casillas MR",
        }).reset_index(drop=True)
    rows = []
    for district in range(1, 16):
        raw = json.loads((source / f"2024_json_d{district}.json").read_bytes())
        for section in raw["secciones"]:
            for c in section["casillas"]:
                if c["clave_tipo_casilla"] != "S":
                    continue
                rows.append({
                    "ANIO": year, "ID_DISTRITO_LOCAL": district,
                    "ID_SECCION_INSTALACION": f"22-{int(section['clave_seccion']):04d}",
                    "NUMERO_CASILLA": int(c["no_casilla"]),
                    "VOTOS_MR": int(c["voto_total_calc"]),
                    "FUENTE_ESPECIAL": f"JSON_D{district}.json (MR)",
                })
    return pd.DataFrame(rows)


def vote_columns(year: int, df: pd.DataFrame) -> list[str]:
    columns = list(df.columns)
    start = "UBICACION_CASILLA" if year == 2024 else "CASILLA"
    end = "NO_REGISTRADAS" if year == 2024 else "NUM_VOTOS_VALIDOS"
    votes = columns[columns.index(start) + 1 : columns.index(end)]
    votes += ["NO_REGISTRADAS", "NULOS", "TOTAL_VOTOS"] if year == 2024 else list(VOTE_TAIL)
    return votes


def aggregate_sections(df: pd.DataFrame, year: int) -> pd.DataFrame:
    eligible = df.loc[df["INCLUIR_SECCION"]].copy()
    vote_cols = vote_columns(year, eligible)
    for col in vote_cols:
        eligible[col] = pd.to_numeric(eligible[col], errors="raise").fillna(0).astype("int64")
    result = eligible.groupby("ID_SECCION", as_index=False)[vote_cols].sum()
    # Una anulación elimina los votos, pero no a los electores de la lista.
    all_bce = df.loc[df["TIPO_NORMALIZADO"].isin(["B", "C", "E"])].copy()
    all_bce["LISTA_NOMINAL"] = pd.to_numeric(all_bce["LISTA_NOMINAL"], errors="raise").fillna(0).astype("int64")
    nominal = all_bce.groupby("ID_SECCION")["LISTA_NOMINAL"].sum()
    counts = eligible.groupby("ID_SECCION").size().rename("CASILLAS_BCE_VALIDAS")
    result = result.join(nominal, on="ID_SECCION").join(counts, on="ID_SECCION")
    result = result.join(all_bce.groupby("ID_SECCION").size().rename("CASILLAS_BCE_TOTALES"), on="ID_SECCION")
    result.insert(0, "ANIO", year)
    return result


def reconcile(year: int, cas: pd.DataFrame, sec: pd.DataFrame, official: pd.DataFrame, specials: pd.DataFrame, source: Path) -> tuple[dict, pd.DataFrame]:
    ref = official.copy()
    ref["ID_ESTADO"] = pd.to_numeric(ref["ID_ESTADO"], errors="raise").astype(int)
    ref["SECCION"] = pd.to_numeric(ref["SECCION"], errors="raise").astype(int)
    ref["ID_SECCION"] = ref["ID_ESTADO"].map("{:02d}".format) + "-" + ref["SECCION"].map("{:04d}".format)
    ref["TOTAL_VOTOS"] = pd.to_numeric(ref["TOTAL_VOTOS"], errors="raise").astype(int)
    # El visor 2024 publica algunas secciones más de una vez por distrito;
    # el cotejo se hace al nivel solicitado: sección estatal.
    ref = ref.groupby("ID_SECCION", as_index=False)["TOTAL_VOTOS"].sum()
    comp = sec[["ID_SECCION", "TOTAL_VOTOS"]].merge(ref, on="ID_SECCION", how="outer", suffixes=("_BCE", "_PUBLICADO"), indicator=True)
    comp["DIF_PUBLICADO_MENOS_BCE"] = comp["TOTAL_VOTOS_PUBLICADO"].fillna(0) - comp["TOTAL_VOTOS_BCE"].fillna(0)
    by_special = specials.groupby("ID_SECCION_INSTALACION")["VOTOS_MR"].sum()
    comp["VOTOS_ESPECIALES_MR_EN_SECCION_INSTALACION"] = comp["ID_SECCION"].map(by_special).fillna(0).astype(int)
    comp["DIF_SIN_EXPLICAR"] = comp.apply(
        lambda r: 0 if r["DIF_PUBLICADO_MENOS_BCE"] in (0, r["VOTOS_ESPECIALES_MR_EN_SECCION_INSTALACION"])
        else r["DIF_PUBLICADO_MENOS_BCE"], axis=1
    )
    comp.insert(0, "ANIO", year)
    valid = cas.loc[~cas["ANULADA_TRIBUNAL"]]
    special = valid.loc[valid["TIPO_NORMALIZADO"].eq("S")]
    advance = valid.loc[valid["TIPO_NORMALIZADO"].eq("A")]
    ref_sum = int(ref["TOTAL_VOTOS"].sum())
    result = {
        "anio": year,
        "filas_casilla": len(cas),
        "casillas_bce": int(cas["INCLUIR_SECCION"].sum()),
        "secciones_bce": len(sec),
        "secciones_publicadas": len(ref),
        "filas_anuladas": int(cas["ANULADA_TRIBUNAL"].sum()),
        "votos_anulados": int(pd.to_numeric(cas.loc[cas["ANULADA_TRIBUNAL"], "TOTAL_VOTOS"]).sum()),
        "filas_especiales": len(special),
        "votos_especiales_csv": int(pd.to_numeric(special["TOTAL_VOTOS"]).sum()),
        "filas_anticipadas": len(advance),
        "votos_anticipados": int(pd.to_numeric(advance["TOTAL_VOTOS"]).sum()),
        "votos_bce": int(sec["TOTAL_VOTOS"].sum()),
        "votos_secciones_publicadas": ref_sum,
        "secciones_con_diferencia": int(comp["DIF_PUBLICADO_MENOS_BCE"].ne(0).sum()),
        "secciones_solo_publicadas": int(comp["_merge"].eq("right_only").sum()),
        "secciones_solo_bce": int(comp["_merge"].eq("left_only").sum()),
        "diferencia_publicado_menos_bce": int(comp["DIF_PUBLICADO_MENOS_BCE"].sum()),
        "secciones_con_diferencia_sin_explicar": int(comp["DIF_SIN_EXPLICAR"].ne(0).sum()),
        "casillas_especiales_mr": len(specials),
        "votos_especiales_mr": int(specials["VOTOS_MR"].sum()),
        "filas_con_seccion_corregida": int(cas["CORRECCION_SECCION"].ne("").sum()),
    }
    # En 2018 y 2021 la tabla seccional publicada suma las S de su lugar de
    # instalación. Comparamos todas las columnas de voto, no solo el total.
    if year in (2018, 2021):
        columns = vote_columns(year, cas) + ["LISTA_NOMINAL"]
        grouped = cas.loc[~cas["ANULADA_TRIBUNAL"]].groupby("ID_SECCION")[vote_columns(year, cas)].sum().fillna(0)
        grouped["LISTA_NOMINAL"] = sec.set_index("ID_SECCION")["LISTA_NOMINAL"]
        official_cols = official.copy()
        official_cols["ID_SECCION"] = official_cols["ID_ESTADO"].map("{:02d}".format) + "-" + official_cols["SECCION"].map("{:04d}".format)
        target = official_cols.set_index("ID_SECCION")[columns].fillna(0)
        result["celdas_voto_nominal_distintas_de_tabla_seccional"] = int(grouped.sub(target).fillna(0).ne(0).sum().sum())
        if year == 2018:
            with ZipFile(source / "2018_tablas_resultados.zip") as z:
                district = pd.read_excel(io.BytesIO(z.read("2018_SEE_DIP_LOC_MR_QRO_DIS.xlsx")))
        else:
            district = pd.read_excel(source / "2021_diputaciones_mr.xlsx", sheet_name="Distrito", header=1)
        result["votos_tabla_distrital"] = int(district["TOTAL_VOTOS"].sum())
        result["diferencia_distrito_menos_seccion"] = result["votos_tabla_distrital"] - ref_sum
    if year == 2024:
        general = json.loads((source / "2024_json_dip_gral.json").read_bytes())
        result["votos_mr_portal"] = int(general["resumen"]["votos_totales"])
        result["votos_especiales_mr_portal"] = int(general["participacion_ba_es"]["votos_mr"])
        result["votos_especiales_rp_portal"] = int(general["participacion_ba_es"]["votos_rp"])
        result["votos_bce_mas_anticipado_y_especiales_mr"] = result["votos_bce"] + result["votos_anticipados"] + result["votos_especiales_mr_portal"]
    return result, comp


def build(source: Path = SOURCE, output: Path = OUTPUT) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    for year, (raw, official) in _read_sources(source).items():
        cas = normalize_casillas(year, raw)
        sec = aggregate_sections(cas, year)
        specials = special_mr(year, cas, source)
        report, comp = reconcile(year, cas, sec, official, specials, source)
        cas.to_parquet(output / f"dip_local_mr_{year}_casilla.parquet", index=False)
        sec.to_parquet(output / f"dip_local_mr_{year}_seccion_bce.parquet", index=False)
        specials.to_parquet(output / f"dip_local_mr_{year}_especial_mr.parquet", index=False)
        comp.to_csv(output / f"dip_local_mr_{year}_cotejo_seccion.csv", index=False, encoding="utf-8-sig")
        reports.append(report)
    audit = {"eleccion": "diputaciones_locales_mr_queretaro", "regla_seccion": "B+C+E, sin actas anuladas; S y A aparte", "anios": reports}
    (output / "auditoria_etapas_1_3.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
