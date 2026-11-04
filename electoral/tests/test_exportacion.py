import json
import subprocess
import sys

import pandas as pd

from electoral.exportacion import construir_excel


def test_excel_hojas_cuentas_formato_y_descartadas():
    resultados = pd.DataFrame({
        "estado": ["con_resultado", "con_resultado", "sin_resultado"],
        "ID_SECCION": ["14-0001", "14-0002", "14-0003"],
        "MUNICIPIO": ["A", "B", "C"],
        "clase": ["ganada_solida", "perdida_competitiva", None],
        "margen_votos": [5, None, None], "faltante_votos": [None, 3, None],
        "margen_pct": [10.0, None, None], "faltante_pct": [None, 3.0, None],
        "votos_para_ganar": [None, 4, None], "abstencion": [20, 30, None],
        "participacion_pct": [80.0, 70.0, None],
    })
    distritos = pd.DataFrame({
        "ID_DISTRITO_FEDERAL": [2], "n_secciones": [3],
        "n_con_resultado": [2], "n_sin_resultado": [1],
        "resultado": ["perdida"], "clase": ["perdida_competitiva"],
        "margen_votos": [None], "faltante_votos": [3],
        "margen_pct": [None], "faltante_pct": [3.0], "votos_para_ganar": [4],
    })
    prioridad = pd.DataFrame({
        "ID_SECCION": ["14-0002"], "MUNICIPIO": ["B"],
        "ID_DISTRITO_FEDERAL": [2], "votos_para_ganar": [4],
        "abstencion": [30], "costo_por_voto": [10], "costo_estimado": [40],
        "descartar": [True], "seleccionada": [False],
    })
    copia = resultados.copy(deep=True)
    raw = construir_excel(resultados, {
        "candidatura": "PVEM-PT-MORENA", "estado": "14 · Jalisco", "fecha": "2026-11-04",
        "distritos": distritos, "priorizacion": prioridad, "presupuesto": 100,
    })
    verificador = """
import json,sys
from io import BytesIO
from openpyxl import load_workbook
libro=load_workbook(BytesIO(sys.stdin.buffer.read()),data_only=True)
resumen={a:b for a,b in list(libro['Resumen'].values)[1:]}
print(json.dumps({
    'hojas':libro.sheetnames,
    'secciones':libro['Secciones'].max_row-1,
    'competitivas':resumen['Derrota competitiva'],
    'clases_visibles':[libro['Secciones']['C2'].value,libro['Secciones']['C3'].value],
    'distrito_visible':[libro['Distritos']['E2'].value,libro['Distritos']['F2'].value],
    'priorizacion':libro['Priorización'].max_row-1,
    'descartada':True in list(libro['Priorización'].values)[1],
    'congelada':libro['Secciones'].freeze_panes=='A2',
    'negrita':all(c.font.bold for c in libro['Secciones'][1]),
    'porcentaje':any(c.number_format=='0.0"%"' for c in libro['Secciones'][2]),
    'externos':len(libro._external_links),
    'supuesto':resumen['Costos y descartes']=='supuesto del usuario',
    'columnas_supuestos':sum('supuesto del usuario' in str(c.value) for c in libro['Priorización'][1]),
}))
"""
    proceso = subprocess.run(
        [sys.executable, "-B", "-c", verificador], input=raw, capture_output=True, check=True
    )
    medido = json.loads(proceso.stdout)
    assert medido["hojas"] == [
        "Resumen", "Metodología", "Secciones", "Priorización", "Distritos", "Calidad"
    ]
    assert medido == {
        "hojas": ["Resumen", "Metodología", "Secciones", "Priorización", "Distritos", "Calidad"],
        "secciones": 2, "competitivas": 1, "priorizacion": 1,
        "clases_visibles": ["Victoria sólida", "Derrota competitiva"],
        "distrito_visible": ["Derrota", "Derrota competitiva"],
        "descartada": True, "congelada": True, "negrita": True,
        "porcentaje": True, "externos": 0,
        "supuesto": True, "columnas_supuestos": 3,
    }
    pd.testing.assert_frame_equal(resultados, copia)
