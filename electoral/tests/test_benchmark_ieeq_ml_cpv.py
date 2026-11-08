"""El ensayo ML une CPV por clave y mide liderazgo con ambos signos."""

import numpy as np
import pandas as pd
import pytest

from scripts.benchmark_ieeq_ml_cpv import P, metrics, tabla_features


def _previous():
    values = {f"pct_{party}": [10.0, 20.0] for party in P}
    return pd.DataFrame({**values, "participacion": [0.5, 0.6],
                         "LISTA_NOMINAL": [100, 200]}, index=["22-0002", "22-0001"])


def test_cpv_alineado_por_seccion_y_nulos_conservados():
    cpv = pd.DataFrame({"ID_SECCION": ["22-0001", "22-0002"],
                        "pct_mujeres": [55.0, np.nan]})
    out = tabla_features(_previous(), cpv)
    assert np.isnan(out.loc["22-0002", "pct_mujeres"])
    assert out.loc["22-0001", "pct_mujeres"] == 55.0
    assert out.loc["22-0002", "prev_pct_PAN"] == 10.0


def test_falta_de_clave_y_duplicados_se_rechazan():
    cpv = pd.DataFrame({"ID_SECCION": ["22-0001"], "pct_mujeres": [55.0]})
    with pytest.raises(ValueError, match="Falta clave"):
        tabla_features(_previous(), cpv)
    with pytest.raises(ValueError, match="duplicado"):
        tabla_features(_previous(), pd.concat([cpv, cpv], ignore_index=True))


def test_metricas_cuentan_lideres_y_falsos_lideres():
    actual = np.zeros((2, len(P)))
    estimated = np.zeros_like(actual)
    actual[0, P.index("PAN")] = 60
    actual[1, P.index("MORENA")] = 60
    estimated[0, P.index("PAN")] = 50
    estimated[1, P.index("PAN")] = 50
    result = metrics(estimated, actual)["por_partido"]
    assert result["PAN"]["lideres_detectados"] == 1
    assert result["PAN"]["falsos_lideres"] == 1
    assert result["MORENA"]["lideres_observados"] == 1
    assert result["MORENA"]["lideres_detectados"] == 0
