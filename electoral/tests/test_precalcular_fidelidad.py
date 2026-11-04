import pandas as pd

from electoral import precalcular_fidelidad as precalculo


def test_genera_ambos_ambitos_y_conserva_columnas_visibles(tmp_path, monkeypatch):
    llamadas = []

    def analizar(_elecciones, ambito):
        llamadas.append(ambito)
        fila = {col: 1 for col in precalculo.COLUMNAS_PANTALLA}
        fila.update(ID_SECCION="01-0001", partido="PAN", clase="Bastión", ambito=ambito)
        return pd.DataFrame([{**fila, "media_pct": 60.0}])

    monkeypatch.setattr(precalculo, "analizar_fidelidad", analizar)
    monkeypatch.setattr(precalculo, "LIMITE_BYTES", 1)
    salidas = precalculo.generar(tmp_path, {})

    assert llamadas == ["estado", "nacional"]
    for ambito, nombre in precalculo.SALIDAS.items():
        tabla = pd.read_parquet(tmp_path / nombre)
        assert list(tabla.columns) == list(precalculo.COLUMNAS_PANTALLA)
        assert tabla.loc[0, "ambito"] == ambito
        assert salidas[ambito]["filas"] == 1
