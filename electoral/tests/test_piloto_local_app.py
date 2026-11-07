"""La demo IEEQ muestra datos por sección y oculta CPV en perímetros cambiados."""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_piloto_local_render_y_perimetro_modificado(tmp_path):
    data = tmp_path / "data/electoral/ieeq_local"
    data.mkdir(parents=True)
    for year in (2018, 2021, 2024):
        pd.DataFrame({
            "ANIO": [year, year], "ID_SECCION": ["22-0001", "22-0002"],
            "PAN": [30, 20], "MORENA": [40, 50], "NULOS": [2, 1],
            "NO_REGISTRADAS": [0, 0], "TOTAL_VOTOS": [72, 71],
            "LISTA_NOMINAL": [100, 100], "CASILLAS_BCE_VALIDAS": [1, 1],
            "CASILLAS_BCE_TOTALES": [1, 1],
        }).to_parquet(data / f"dip_local_mr_{year}_seccion_bce.parquet", index=False)
    pd.DataFrame({
        "ID_SECCION": ["22-0001", "22-0002"],
        "CATEGORIA": ["sin_cambio_cartografico_referencia", "dividida_o_reconfigurada"],
        "IOU_MISMA_CLAVE": [1.0, 0.4],
        "CATEGORIA_2019_A_2021": ["sin_cambio_cartografico_referencia"] * 2,
    }).to_parquet(data / "crosswalk_qro_2018_2021_2024_referencias.parquet", index=False)
    script = (
        "from pathlib import Path\n"
        "from electoral.piloto_local import mostrar_piloto_local\n"
        f"mostrar_piloto_local(22, Path({str(tmp_path)!r}))\n"
    )
    at = AppTest.from_string(script).run(timeout=180)
    assert not at.exception
    assert any("Polígono prácticamente igual" in item.value for item in at.info)
    at.selectbox[1].select("22-0002").run(timeout=180)
    assert not at.exception
    assert any("no se atribuye" in item.value for item in at.warning)
    at.selectbox[0].select(2018).run(timeout=180)
    assert not at.exception
    assert not at.warning
    assert at.dataframe[0].value.iloc[0]["Opción registrada"] == "MORENA"
