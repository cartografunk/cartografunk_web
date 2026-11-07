"""La pestaña de forecasting distingue resultados y datos locales ausentes."""

import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_forecasting_tab_render(tmp_path):
    carpeta = tmp_path / "data/electoral/ieeq_local"
    carpeta.mkdir(parents=True)
    informe = {
        "estado": "calculado", "universo": {"total_secciones": 2,
            "comparable": {"secciones": 1, "cobertura_lista_nominal_pct": 50.0}},
        "resultados": {modelo: {"por_partido": {partido: {
            "intervalo_90_semianchura_pp": 5.0, "mae_pct": 2.0,
            "lideres_observados": 1, "lideres_detectados": 1,
            "cobertura_empirica_intervalo_pct": 80.0,
        } for partido in ("PAN", "PRI", "PRD", "MC", "PVEM", "MORENA", "PT")}}
        for modelo in ("persistencia", "ridge")},
    }
    (carpeta / "benchmark_partidos_2024.json").write_text(json.dumps(informe), encoding="utf-8")
    pd.DataFrame({"ID_SECCION": ["22-0001", "22-0002"],
                  "CATEGORIA": ["sin_cambio_cartografico_referencia", "modificada"]}).to_parquet(
                      carpeta / "crosswalk_qro_2018_2021_2024_referencias.parquet", index=False)
    pd.DataFrame({"ID_SECCION": ["22-0001"], "PARTIDO": ["MORENA"], "MODELO": ["ridge"],
                  "CUOTA_OBSERVADA_PCT": [40.], "CUOTA_PREDICHA_PCT": [38.],
                  "MARGEN_OBSERVADO_PP": [8.], "MARGEN_PREDICHO_PP": [6.]}).to_parquet(
                      carpeta / "benchmark_partidos_2024_seccion.parquet", index=False)
    script = ("from pathlib import Path\n"
              "from electoral.forecasting_tab import mostrar_diagnostico_forecast\n"
              f"mostrar_diagnostico_forecast(22, Path({str(tmp_path)!r}))\n")
    at = AppTest.from_string(script).run(timeout=180)
    assert not at.exception
    assert any("1 sección queda sin modelo" in item.value for item in at.caption)
    assert "Sin modelo: sección modificada" in at.dataframe[0].value["Lectura del ensayo"].tolist()
