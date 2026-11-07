"""Una sección hija y varios orígenes se comparan como un solo grupo."""

import pandas as pd
import pytest

from scripts.agrupar_ieeq_2024_a_2021 import grupos_relacionados


def test_grupos_incluyen_division_y_fusion_sin_duplicar_secciones():
    links = pd.DataFrame({"ORIGEN": ["22-0001", "22-0001", "22-0002", "22-0003"],
                          "DESTINO": ["22-0901", "22-0902", "22-0902", "22-0003"]})
    out = grupos_relacionados(pd.Index(["22-0001", "22-0002", "22-0003"]),
                              pd.Index(["22-0901", "22-0902", "22-0003"]), links)
    assert len(out) == 6
    assert out.groupby("ID_GRUPO_2021_2024").ANIO.value_counts().loc["22-0001"].to_dict() == {2021: 2, 2024: 2}
    assert out.groupby("ID_GRUPO_2021_2024").ANIO.value_counts().loc["22-0003"].to_dict() == {2021: 1, 2024: 1}
    assert not out.duplicated(["ANIO", "ID_SECCION"]).any()


def test_falta_de_enlace_no_crea_falsa_comparacion():
    with pytest.raises(ValueError, match="no cubre"):
        grupos_relacionados(pd.Index(["22-0001", "22-0002"]), pd.Index(["22-0901"]),
                            pd.DataFrame({"ORIGEN": ["22-0001"], "DESTINO": ["22-0901"]}))
