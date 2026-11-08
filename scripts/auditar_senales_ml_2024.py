"""Contrasta derrota partidaria cercana, persistencia y margen de candidatura."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from electoral.candidaturas_ieeq import margenes_candidatura
from electoral.reparto_ieeq import PARTIDOS_COMUNES
from scripts.benchmark_ieeq_ml_cpv import DATA


ROOT = Path(__file__).resolve().parents[1]
FUENTES = ROOT / "data/electoral/fuentes_ieeq"


def comparar_senales_partidarias(pred: pd.DataFrame) -> list[dict]:
    """Compara señales puntuales con la regla transparente de persistir 2021."""
    filas = []
    for partido in PARTIDOS_COMUNES:
        p = pred.loc[pred.PARTIDO.eq(partido)]
        margen = p.pivot(index="ID_SECCION", columns="MODELO", values="MARGEN_PREDICHO_PP")
        observado = p.loc[p.MODELO.eq("persistencia"),
                          ["ID_SECCION", "MARGEN_OBSERVADO_PP"]].set_index("ID_SECCION")
        if margen.index.has_duplicates or observado.index.has_duplicates or set(margen.index) != set(observado.index):
            raise ValueError(f"Predicciones incompletas o duplicadas para {partido}")
        margen = margen.reindex(observado.index)
        if margen[["persistencia", "hist_gradient_boosting_cpv"]].isna().any().any():
            raise ValueError(f"Faltan señales de persistencia o ML para {partido}")
        close = observado.MARGEN_OBSERVADO_PP.lt(0) & observado.MARGEN_OBSERVADO_PP.ge(-5)
        ml = margen.hist_gradient_boosting_cpv.gt(0)
        persiste = margen.persistencia.gt(0)
        filas.append({"partido": partido, "secciones_evaluadas": len(observado),
                      "derrotas_partidarias_a_5_pp_o_menos": int(close.sum()),
                      "de_ellas_ml_predijo_liderazgo_puntual": int((close & ml).sum()),
                      "de_ellas_persistencia_predijo_liderazgo_puntual": int((close & persiste).sum()),
                      "de_ellas_ambos": int((close & ml & persiste).sum()),
                      "de_ellas_solo_ml": int((close & ml & ~persiste).sum())})
    return filas


def run(partido: str = "PAN") -> dict:
    casillas = pd.read_parquet(DATA / "dip_local_mr_2024_casilla.parquet")
    incluidas = casillas.loc[casillas.TIPO_NORMALIZADO.isin(("B", "C", "E"))
                            & casillas.INCLUIR_SECCION.eq(True)]
    distritos = incluidas[["ID_SECCION", "ID_DISTRITO_LOCAL"]].drop_duplicates()
    if distritos.ID_SECCION.duplicated().any():
        raise ValueError("Una sección aparece en varios distritos locales")
    fuentes = {d: json.loads((FUENTES / f"2024_json_d{d}.json").read_text(encoding="utf-8"))["candidatos"]
               for d in range(1, 16)}
    bruto = pd.read_parquet(DATA / "dip_local_mr_2024_seccion_bce.parquet")
    candidaturas = margenes_candidatura(bruto, distritos, fuentes)
    destino = DATA / "margen_candidatura_ieeq_2024_seccion.parquet"
    candidaturas.to_parquet(destino, index=False)

    pred = pd.read_parquet(DATA / "benchmark_ml_cpv_2024_seccion.parquet")
    (DATA / "auditoria_senales_partidos_2024.json").write_text(
        json.dumps(comparar_senales_partidarias(pred), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    party = pred.loc[pred.PARTIDO.eq(partido)]
    model = party.pivot(index="ID_SECCION", columns="MODELO", values="MARGEN_PREDICHO_PP")
    observed = party.loc[party.MODELO.eq("hist_gradient_boosting_cpv"),
                         ["ID_SECCION", "MARGEN_OBSERVADO_PP"]].set_index("ID_SECCION")
    base = observed.join(model).join(
        candidaturas.loc[candidaturas.PARTIDO.eq(partido),
                          ["ID_SECCION", "MARGEN_CANDIDATURA_PP"]].set_index("ID_SECCION"),
        validate="one_to_one",
    )
    close = base.MARGEN_OBSERVADO_PP.lt(0) & base.MARGEN_OBSERVADO_PP.ge(-5)
    ml = base.hist_gradient_boosting_cpv.gt(0)
    persist = base.persistencia.gt(0)
    candidate_wins = base.MARGEN_CANDIDATURA_PP.gt(0)
    report = {
        "partido": partido, "secciones_evaluadas": len(base),
        "derrotas_partido_a_5_pp_o_menos": int(close.sum()),
        "de_ellas_ml_esperaba_liderazgo": int((close & ml).sum()),
        "de_ellas_persistencia_esperaba_liderazgo": int((close & persist).sum()),
        "de_ellas_ambos": int((close & ml & persist).sum()),
        "de_ellas_solo_ml": int((close & ml & ~persist).sum()),
        "de_ellas_candidatura_local_lidero": int((close & candidate_wins).sum()),
        "de_ellas_candidatura_local_empato": int((close & base.MARGEN_CANDIDATURA_PP.eq(0)).sum()),
        "de_ellas_candidatura_local_perdio": int((close & base.MARGEN_CANDIDATURA_PP.lt(0)).sum()),
        "de_ellas_candidatura_perdio_a_5_pp_o_menos": int((
            close & base.MARGEN_CANDIDATURA_PP.lt(0)
            & base.MARGEN_CANDIDATURA_PP.ge(-5)).sum()),
        "entre_ml_cercanas_candidatura_local_lidero": int((close & ml & candidate_wins).sum()),
        "nota": "Liderazgo de partido usa siete cuotas fraccionarias; candidatura local usa opciones de voto IEEQ por distrito. No son la misma elección analítica.",
    }
    (DATA / "auditoria_senales_ml_2024.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
