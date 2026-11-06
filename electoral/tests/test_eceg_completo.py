import pandas as pd
import pytest

from scripts.build_eceg_completo import normalizar


def test_normalizar_crea_llaves_y_tipos():
    entidad = normalizar(pd.DataFrame({"ENT": ["1"], "NOM_ENT ": [" Aguascalientes "], "POBTOT": ["1425607"]}), "entidad")
    distrito = normalizar(pd.DataFrame({"ENTIDAD": ["1"], "DISTRITO": ["3"], "POBTOT": ["482911"]}), "distrito")
    seccion = normalizar(pd.DataFrame({"ENTIDAD": ["1"], "SECCION": ["338"], "POBTOT": ["0"]}), "seccion")
    assert entidad.ID_ENTIDAD.tolist() == ["01"]
    assert entidad.NOM_ENT.tolist() == ["Aguascalientes"]
    assert distrito.ID_DISTRITO.tolist() == ["01-03"]
    assert seccion.ID_SECCION.tolist() == ["01-0338"]
    assert pd.api.types.is_numeric_dtype(seccion.POBTOT)


def test_normalizar_rechaza_llave_seccional_duplicada():
    datos = pd.DataFrame({"ENTIDAD": ["1", "1"], "SECCION": ["338", "338"], "POBTOT": ["1", "2"]})
    with pytest.raises(ValueError, match="duplicada"):
        normalizar(datos, "seccion")
