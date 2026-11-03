# Límites de verificación y decisiones registradas

Esta lista recoge los `NO VERIFICADO` y `NO ENCONTRADO` de los reportes temporales disponibles y de la inspección de código y datos de Prompt 6. Las rutas de `%TEMP%` se refieren a `C:\Users\HeyCe\AppData\Local\Temp` en esta sesión.

## NO VERIFICADO

| Punto | Fuente y alcance de la revisión |
| --- | --- |
| Regla oficial para repartir votos de combinaciones entre partidos y equivalencia legal de una candidatura con un partido. | `%TEMP%\cola3_reporte.md`, sección `NO VERIFICADO`; docstrings de [`reparto.py`](../../electoral/reparto.py), [`reparto_distrito.py`](../../electoral/reparto_distrito.py) y [`reparto_fraccionario.py`](../../electoral/reparto_fraccionario.py). |
| Correspondencia o continuidad territorial fuera de las llaves comparadas. | `%TEMP%\cola3_reporte.md`, sección `NO VERIFICADO`. |
| CRS original correcto del GPKG y causa de las discordancias espaciales. | `%TEMP%\cartografunk_ine_crs.json` mide candidatos; [`geometria.py`](../../electoral/geometria.py) aplica EPSG:32614 con `allow_override=True`. Es hipótesis de trabajo. |
| Significado de los valores `TIPO=2` y `TIPO=4` del MGE. | `%TEMP%\cartografunk_ine_three_sections.json`, campos `selector`; allí se señalan expresamente como `NO VERIFICADO`. |
| Fecha de corte de `LISTA_NOMINAL` en los cinco Parquet. | Inventario de esquemas en [DATOS.md](DATOS.md) y `%TEMP%\cartografunk_ine_sec_schema.md`; no se verificó una fecha documental en esos archivos. |
| Significado documental de `EXT_CONTIGUA` y de los códigos de `ACTA_CASILLA-MEC`. | [`casillas.py`](../../electoral/casillas.py) usa los campos para la llave; `%TEMP%\cartografunk_ine_inventario.md` los inventaría sin documentar su significado. |
| Comando exacto empleado originalmente para crear cada Parquet electoral y ejecución de la app en este turno. | Búsqueda de los cinco nombres de Parquet fuera de `data/` y [`README.md`](README.md): referencias en [`config.py`](../../electoral/config.py), pero no se halló un script constructor de esos archivos. El encabezado de [`demo_app.py`](../../electoral/demo_app.py) da el comando de arranque; no se ejecutó en Prompt 6. |

## NO ENCONTRADO

| Punto | Fuente |
| --- | --- |
| Etiqueta local `demo-11am`; ya existía la rama `electoral-extension`, que se usó. | `%TEMP%\cola3_reporte.md`, primera línea de contenido; comprobación de `git tag -l demo-11am` y `git branch --show-current` en Prompt 6. |
| Una fila del distrito de coalición parcial donde `PT` sea individual y `MORENA` conserve `cand_PVEM_PT_MORENA`. | `%TEMP%\cola3_reporte.md`, sección B: reporta ejemplos separados `01-0338` y `02-0370` y marca el caso combinado `NO ENCONTRADO`. |

## Decisiones implementadas y evidencia

| Decisión en código | Evidencia localizada |
| --- | --- |
| Unidad de ranking: candidatura activa. En Presidencia se suman partidos individuales y combinaciones de cada coalición; en Diputaciones y Senadurías `_DISCAND.csv` determina la actividad por distrito. | [`config.py`](../../electoral/config.py), [`datos.py`](../../electoral/datos.py), [`candidaturas.py`](../../electoral/candidaturas.py); `%TEMP%\cola3_reporte.md` registra 46 distritos de coalición parcial en Diputaciones y 108 en Senadurías, y coincidencia con `_DISPP.csv` salvo 9 distritos de Diputaciones. |
| `ID_SECCION` usa estado de dos dígitos y sección de cuatro. `SECCION=0` se clasifica `extranjero`. | [`datos.py`](../../electoral/datos.py), [`casillas.py`](../../electoral/casillas.py); `%TEMP%\electoral_reporte_cola6.md` consigna llaves únicas y los conteos de estado de los Parquet. |
| `sin_resultado` se define con `NUM_VOTOS_VALIDOS` nulo o cero; solo `con_resultado` recibe ranking. | [`datos.py`](../../electoral/datos.py), [`casillas.py`](../../electoral/casillas.py), [`rentabilidad.py`](../../electoral/rentabilidad.py); `%TEMP%\electoral_reporte_cola6.md` consigna los conteos actuales. |
| Para secciones, restar votos de casillas `S` no anuladas de `TOTAL_VOTOS` al calcular `votos_en_lista`; en casillas `S`, abstención y participación quedan sin dato. | [`datos.py`](../../electoral/datos.py), [`casillas.py`](../../electoral/casillas.py), [`rentabilidad.py`](../../electoral/rentabilidad.py); `%TEMP%\electoral_reporte_cola6.md` registra en Presidencia 728/19 secciones con `votos_sobre_lista` antes/después. |
| Mantener sin ajuste la bandera de discrepancia SEC/DISPP de Diputaciones. | [`datos.py`](../../electoral/datos.py) enumera nueve claves; `%TEMP%\cola3_reporte.md` mide 9 distritos, 19 comparaciones y diferencia máxima absoluta de 176 votos. |
| Clasificar con 15 pp para ganada sólida, 5 pp para pérdida competitiva, 15 pp para pérdida lejana y 100 votos para el indicador en votos. | [`clasificacion.py`](../../electoral/clasificacion.py), `Umbrales` y `clasificar()`. |
| Mantener los repartos por partido como experimentales. | Docstrings de [`reparto.py`](../../electoral/reparto.py), [`reparto_distrito.py`](../../electoral/reparto_distrito.py), [`reparto_fraccionario.py`](../../electoral/reparto_fraccionario.py); `%TEMP%\cartografunk_coalition_split.json` registra desviación absoluta 312 para `A_own` distrital frente a las cifras de referencia que contiene ese mismo reporte. |
| Interpretar la geometría del GPKG como EPSG:32614, simplificar a 25 m y escribir GeoParquet EPSG:4326. | [`geometria.py`](../../electoral/geometria.py), [`config.py`](../../electoral/config.py); `%TEMP%\cartografunk_ine_crs.json` registra 70 643/70 753 centroides dentro de su entidad con EPSG:32614; `%TEMP%\cartografunk_ine_geometry_quality.json` registra 249 polígonos sin fila de Presidencia. |

Estas decisiones describen el comportamiento actual y las mediciones citadas; ninguna de las hipótesis marcadas `NO VERIFICADO` se eleva a conclusión documental.
