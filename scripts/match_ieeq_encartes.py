"""Busca secciones 2024 nuevas en encartes 2021/2024 por sede y localidad.

Los PDF se convierten primero a Markdown. Esta comparación no traslada votos ni
personas; genera candidatos de correspondencia seccional con evidencia trazable.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/electoral/fuentes_ieeq"
OUTPUT = ROOT / "data/electoral/ieeq_local"
ENCARTES = {2021: SOURCE / "encarte_qro_2021_jl.md", 2024: SOURCE / "encarte_qro_2024_3005.md"}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.upper())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("�", "")
    return " ".join(re.findall(r"[A-Z0-9]+", texto))


def parse_encarte(path: Path, anio: int) -> pd.DataFrame:
    texto = path.read_text(encoding="utf-8")
    pdf = path.with_suffix(".pdf")
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if f"SHA-256: `{digest}`" not in texto:
        raise ValueError(f"Markdown no corresponde al PDF: {path}")
    claves = list(re.finditer(r"Secci.n:\s*(\d+)\s+([A-Z]\d+(?:C\d+)?)", texto))
    municipios = list(re.finditer(r"Municipio:\s*(\d+)\)\s*([^\n]+)", texto))
    localidades = list(re.finditer(r"Localidad:\s*(\d+)\)\s*([^\n]+)", texto))
    mpos = [m.start() for m in municipios]
    lpos = [m.start() for m in localidades]
    paginas = list(re.finditer(r"## P.gina (\d+)", texto))
    ppos = [m.start() for m in paginas]
    filas = []
    for i, clave in enumerate(claves):
        mi = bisect.bisect_left(mpos, clave.start()) - 1
        li = bisect.bisect_left(lpos, clave.start()) - 1
        pi = bisect.bisect_left(ppos, clave.start()) - 1
        if min(mi, li, pi) < 0:
            raise ValueError(f"Contexto ausente para sección {clave.group(1)}")
        despues = texto[clave.end():claves[i + 1].start() if i + 1 < len(claves) else len(texto)]
        ubicacion = re.search(r"Ubicaci.n:\s*(.*?)(?=\s+Presidenta/e:|$)", despues, re.S)
        domicilio = ""
        if ubicacion:
            domicilio = ubicacion.group(1).split("Distrito Federal:")[0]
            domicilio = re.sub(r"## P.gina \d+|P.gina \d+|Ubica tu casilla", " ", domicilio)
            domicilio = " ".join(domicilio.split())
        filas.append({
            "ANIO": anio,
            "ID_SECCION": f"22-{int(clave.group(1)):04d}",
            "CASILLA": clave.group(2),
            "MUNICIPIO_INE": int(municipios[mi].group(1)),
            "LOCALIDAD_INE": int(localidades[li].group(1)),
            "LOCALIDAD_NOMBRE": localidades[li].group(2).strip(),
            "DOMICILIO": domicilio,
            "DOMICILIO_NORMALIZADO": normalizar(domicilio),
            "PAGINA": int(paginas[pi].group(1)),
        })
    resultado = pd.DataFrame(filas)
    if resultado.duplicated(["ID_SECCION", "CASILLA"]).any():
        duplicadas = resultado.loc[resultado.duplicated(["ID_SECCION", "CASILLA"], keep=False),
                                   ["ID_SECCION", "CASILLA", "MUNICIPIO_INE", "LOCALIDAD_INE", "PAGINA"]]
        raise ValueError(f"Casilla duplicada en encarte {anio}: {duplicadas.head(10).to_dict('records')}")
    return resultado


def build(output: Path = OUTPUT) -> dict:
    enc21, enc24 = (parse_encarte(ENCARTES[y], y) for y in (2021, 2024))
    if len(enc21) != 2853 or len(enc24) != 3138:
        raise ValueError(f"Conteo de encartes inesperado: {len(enc21)}, {len(enc24)}")
    eceg = pd.read_parquet(ROOT / "data/electoral/eceg_2020_seccion.parquet", columns=["ID_SECCION"])
    cross = pd.read_parquet(output / "crosswalk_qro_2018_2021_2024_referencias.parquet")
    nuevos = cross.loc[
        cross.CATEGORIA.ne("sin_cambio_cartografico_referencia")
        & ~cross.ID_SECCION.isin(eceg.ID_SECCION), "ID_SECCION"
    ]
    if len(nuevos) != 81:
        raise ValueError(f"Esperadas 81 secciones sin clave ECEG, hay {len(nuevos)}")
    links = pd.read_parquet(output / "crosswalk_eceg_2021_a_2024.parquet")
    geometria = defaultdict(dict)
    for row in links.itertuples():
        geometria[row.DESTINO][row.ORIGEN] = float(row.FRACCION_DESTINO)
    antiguas = enc21.groupby("ID_SECCION")
    nuevas = enc24.groupby("ID_SECCION")
    indice_localidad: dict[tuple[int, int], set[str]] = defaultdict(set)
    for row in enc21.itertuples():
        indice_localidad[(row.MUNICIPIO_INE, row.LOCALIDAD_INE)].add(row.ID_SECCION)
    filas = []
    for destino in nuevos:
        if destino not in nuevas.groups:
            filas.append({"DESTINO_2024": destino, "ORIGEN_2021": "", "EVIDENCIA": "sin_encarte_2024"})
            continue
        d = nuevas.get_group(destino)
        locales = set(zip(d.MUNICIPIO_INE, d.LOCALIDAD_INE))
        candidates = set().union(*(indice_localidad.get(k, set()) for k in locales))
        # El polígono añade candidatos cuando el domicilio cambió de escuela
        # o la localidad del encarte fue reclasificada entre años.
        candidates |= set(geometria.get(destino, {})) & set(antiguas.groups)
        for origen in sorted(candidates):
            a = antiguas.get_group(origen)
            same_local = bool(locales & set(zip(a.MUNICIPIO_INE, a.LOCALIDAD_INE)))
            dom_d = {x for x in d.DOMICILIO_NORMALIZADO if x}
            dom_a = {x for x in a.DOMICILIO_NORMALIZADO if x}
            exacto = bool(dom_d & dom_a)
            parecido = max((SequenceMatcher(None, x, y).ratio() for x in dom_d for y in dom_a), default=0.0)
            fraccion = geometria.get(destino, {}).get(origen, 0.0)
            if exacto:
                evidencia = "domicilio_exacto"
            elif same_local:
                evidencia = "misma_localidad"
            elif fraccion > 0:
                evidencia = "solo_geometria"
            else:
                continue
            filas.append({
                "DESTINO_2024": destino, "ORIGEN_2021": origen,
                "EVIDENCIA": evidencia, "DOMICILIO_SIMILITUD": round(parecido, 3),
                "MISMA_LOCALIDAD": same_local, "FRACCION_DESTINO_GEOMETRIA": round(fraccion, 6),
                "LOCALIDADES_DESTINO": ",".join(sorted(d.LOCALIDAD_NOMBRE.unique())),
                "LOCALIDADES_ORIGEN": ",".join(sorted(a.LOCALIDAD_NOMBRE.unique())),
                "PAGINAS_ENCARTE_2024": ",".join(map(str, sorted(d.PAGINA.unique()))),
                "PAGINAS_ENCARTE_2021": ",".join(map(str, sorted(a.PAGINA.unique()))),
            })
    pares = pd.DataFrame(filas)
    output.mkdir(parents=True, exist_ok=True)
    pares.to_csv(output / "encarte_2021_2024_81_candidatos.csv", index=False, encoding="utf-8-sig")
    enlaces = pares.loc[pares.FRACCION_DESTINO_GEOMETRIA.gt(0)].copy()
    enlaces["CLASE_EVIDENCIA"] = enlaces.apply(
        lambda r: "domicilio_y_geometria" if r.EVIDENCIA == "domicilio_exacto"
        else "localidad_y_geometria" if r.MISMA_LOCALIDAD else "solo_geometria", axis=1)
    enlaces = enlaces.sort_values(["DESTINO_2024", "FRACCION_DESTINO_GEOMETRIA"], ascending=[True, False])
    enlaces.to_csv(output / "encarte_2021_2024_81_enlaces.csv", index=False, encoding="utf-8-sig")
    enc21.drop(columns=["DOMICILIO"]).to_parquet(output / "encarte_qro_2021_claves.parquet", index=False)
    enc24.drop(columns=["DOMICILIO"]).to_parquet(output / "encarte_qro_2024_claves.parquet", index=False)
    resumen = {
        "fuentes": {str(y): {"url": ENCARTES[y].read_text(encoding="utf-8").split("- Fuente: ")[1].splitlines()[0],
                              "sha256_pdf": hashlib.sha256(ENCARTES[y].with_suffix(".pdf").read_bytes()).hexdigest(),
                              "casillas": len(enc)} for y, enc in ((2021, enc21), (2024, enc24))},
        "secciones_2024_sin_clave_eceg": len(nuevos),
        "secciones_con_algun_candidato": int(pares.DESTINO_2024.nunique()),
        "pares_por_evidencia": pares.EVIDENCIA.value_counts().to_dict(),
        "enlaces_con_superposicion": len(enlaces),
        "destinos_con_domicilio_exacto_y_geometria": int(enlaces.loc[enlaces.CLASE_EVIDENCIA.eq("domicilio_y_geometria"), "DESTINO_2024"].nunique()),
        "destinos_con_localidad_y_geometria": int(enlaces.loc[enlaces.MISMA_LOCALIDAD, "DESTINO_2024"].nunique()),
        "destinos_solo_geometria": sorted(set(nuevos) - set(enlaces.loc[enlaces.MISMA_LOCALIDAD, "DESTINO_2024"])),
        "destinos_con_varios_origenes_geometricos": int(enlaces.groupby("DESTINO_2024").size().gt(1).sum()),
        "destinos_con_origen_dominante_95pct": int(enlaces.groupby("DESTINO_2024").FRACCION_DESTINO_GEOMETRIA.max().ge(.95).sum()),
        "nota": "Domicilio y localidad proponen correspondencias; no identifican residencia ni traslado de votantes."
    }
    (output / "encarte_2021_2024_81_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return resumen


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False))
