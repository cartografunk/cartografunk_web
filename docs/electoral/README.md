# Módulo electoral

`electoral/` lee resultados de Presidencia, Diputaciones MR y Senadurías MR de 2024, construye candidaturas, calcula rentabilidad y clasifica secciones. La app vigente es [`app_simple.py`](../../electoral/app_simple.py), con mapa de secciones para las tres elecciones. El estado actual y las validaciones recientes están en [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md). Las rutas de los ZIP y de cuatro Parquet están en [`electoral/config.py`](../../electoral/config.py); la ruta del Parquet de casillas aparece en el comando de generación más abajo. Las reglas implementadas se describen en [METODOLOGIA.md](METODOLOGIA.md); el inventario de archivos está en [DATOS.md](DATOS.md).

## Estructura comprobada

| Archivo | Contenido |
| --- | --- |
| [`config.py`](../../electoral/config.py) | ZIP de 2024, rutas de Parquet, candidaturas y tolerancia de geometría. |
| [`datos.py`](../../electoral/datos.py) | Lectura de `_SEC.csv` y agregado de casillas `S` desde `_CAS.csv`. |
| [`candidaturas.py`](../../electoral/candidaturas.py) | Candidaturas activas por distrito según `_DISCAND.csv` y resolución por partido. |
| [`casillas.py`](../../electoral/casillas.py) | Lectura de casillas de Presidencia y llave legible. |
| [`rentabilidad.py`](../../electoral/rentabilidad.py), [`rentabilidad_partido.py`](../../electoral/rentabilidad_partido.py) | Ranking y métricas por candidatura activa. |
| [`clasificacion.py`](../../electoral/clasificacion.py), [`agregacion.py`](../../electoral/agregacion.py) | Clases y sumas territoriales. |
| [`reparto.py`](../../electoral/reparto.py), [`reparto_distrito.py`](../../electoral/reparto_distrito.py), [`reparto_fraccionario.py`](../../electoral/reparto_fraccionario.py) | Repartos experimentales de votos combinados. |
| [`geometria.py`](../../electoral/geometria.py) | Lectura, simplificación y reproyección de la capa de secciones. |
| [`app_simple.py`](../../electoral/app_simple.py) | App Streamlit actual de tres elecciones de 2024. |
| [`analisis_demo.py`](../../electoral/analisis_demo.py) | Prepara clases por candidatura activa y aportes de partidos estimados. |
| [`demo_app.py`](../../electoral/demo_app.py) | Demo anterior de Presidencia 2024. |
| [`tests/`](../../electoral/tests/) | Pruebas con pytest. |

## Entorno y ejecución

Comandos PowerShell desde `C:\cartografunk_web`:

```powershell
& 'D:\Conda\envs\cartografunk\python.exe' -B -m pytest electoral/tests -q -p no:cacheprovider
& 'D:\Conda\envs\cartografunk\python.exe' -B -m streamlit run electoral/app_simple.py
```

La suite de esta integración dio 67 pruebas aprobadas y 0 omitidas. AppTest terminó sin excepciones en tres combinaciones de elección, candidatura y estado; véase [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md). **El arranque del servidor y el aspecto en navegador son NO VERIFICADO**.

El código importa `pandas`, `numpy`, `geopandas`, `streamlit` y `pydeck`; el inventario de esquemas usa `pyarrow` y las pruebas usan `pytest`. Versiones comprobadas en `D:\Conda\envs\cartografunk\python.exe` mediante `importlib.metadata.version`: pandas 2.2.3, numpy 2.1.1, geopandas 1.1.4, shapely 2.1.2, streamlit 1.66.1, pydeck 0.9.3, pyarrow 24.0.0 y pytest 9.1.1. Los requisitos existentes en [`deploy_streamlit/requirements.txt`](../../deploy_streamlit/requirements.txt) y [`requirements-explorador.txt`](../../requirements-explorador.txt) se leyeron; ninguno declara pytest.

## Orden y comandos para generar los Parquet

Los cuatro resultados de votos se pueden generar sin depender unos de otros. El demo lee el Parquet de Presidencia por sección y el GeoParquet. Los comandos siguientes llaman a las funciones actuales y escriben en las rutas actuales; **en Prompt 6 se comprobaron las importaciones, rutas y miembros ZIP mediante lecturas, pero no se ejecutaron las escrituras ni se verificó que estos fueran los comandos históricos exactos**.

1. Secciones de las tres elecciones:

```powershell
@'
from electoral.config import (PRESIDENCIA_ZIP, DIPUTACIONES_ZIP, SENADURIAS_ZIP,
    PRESIDENCIA_PARQUET, DIPUTACIONES_PARQUET, SENADURIAS_PARQUET)
from electoral.datos import cargar_sec
for origen, eleccion, salida in (
    (PRESIDENCIA_ZIP, 'presidencia', PRESIDENCIA_PARQUET),
    (DIPUTACIONES_ZIP, 'diputaciones', DIPUTACIONES_PARQUET),
    (SENADURIAS_ZIP, 'senadurias', SENADURIAS_PARQUET),
):
    cargar_sec(origen, eleccion).to_parquet(salida, index=False)
'@ | & 'D:\Conda\envs\cartografunk\python.exe' -B -
```

2. Casillas de Presidencia:

```powershell
@'
from electoral.config import PRESIDENCIA_ZIP
from electoral.casillas import cargar_casillas
cargar_casillas(PRESIDENCIA_ZIP).to_parquet(
    'data/electoral/presidencia_2024_casilla.parquet', index=False)
'@ | & 'D:\Conda\envs\cartografunk\python.exe' -B -
```

3. Geometría: el ZIP MGE contiene `MGE 2024/SECCIONES_2024.gpkg`, capa `SECCIONES_2024`. La extracción temporal y la escritura serían:

```powershell
@'
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from shutil import copyfileobj
from electoral.config import MGE_ZIP, GEOMETRIA_PARQUET, GEOMETRIA_TOLERANCIA_M
from electoral.geometria import cargar_geometria
with TemporaryDirectory() as temporal:
    gpkg = Path(temporal) / 'SECCIONES_2024.gpkg'
    with ZipFile(MGE_ZIP) as archivo, archivo.open('MGE 2024/SECCIONES_2024.gpkg') as fuente, gpkg.open('wb') as destino:
        copyfileobj(fuente, destino)
    cargar_geometria(gpkg, GEOMETRIA_TOLERANCIA_M).to_parquet(GEOMETRIA_PARQUET, index=False)
'@ | & 'D:\Conda\envs\cartografunk\python.exe' -B -
```

No se encontraron scripts de construcción de estos cinco Parquet dentro de `electoral/`; los comandos reproducen las llamadas expuestas por los módulos. Los agregados de `agregacion.py` no se guardan como Parquet en ese módulo.
