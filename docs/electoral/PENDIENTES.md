# Límites de verificación y decisiones registradas

## Piloto local IEEQ, tras etapas 1–3

El procesamiento y cotejo de diputaciones locales MR 2018, 2021 y 2024 se documenta en [IEEQ_LOCAL_ETAPAS_1_3.md](IEEQ_LOCAL_ETAPAS_1_3.md). El [informe de etapas 4–7](IEEQ_LOCAL_ETAPAS_4_7.md) mide la superposición ECEG→2024 y declara NO-GO para ML de tres elecciones. **NO VERIFICADO:** causa del voto de diferencia entre tabla distrital y seccional del IEEQ en 2018; marco exacto de la jornada 2018; versión jurídica final de los otros catorce distritos 2024; estatus de recuento de 2021/2024 cuando el archivo no lo especifica. En el distrito 7, seis casillas y el total 67 452 sí cuadran con ST-JRC-216/2024. El voto en casillas especiales indica sufragio fuera de la sección de residencia, pero los archivos no identifican su sección de origen.

El benchmark posterior a la puerta territorial ya se muestra en una pestaña diagnóstica, pero sigue pendiente un modelo que detecte liderazgo del partido con cobertura y calibración suficientes para uso prospectivo. Para MORENA/Ridge detectó 0 de 436 liderazgos observados; el intervalo nominal 90 % cubrió menos del 90 % de los márgenes observados. El CPV aún no entra como predictor, por lo que las asociaciones del bloque «¿Por qué?» no explican el forecast. Se requieren escenarios de cambio agregado y una evaluación fuera de tiempo adicional antes de ofrecer un grado de confiabilidad; los 165 casos territoriales modificados permanecen como abstenciones.

La [reagrupación 2021→2024](AGRUPACION_SECCIONES_QRO_2021_2024.md) ya permite comparar **834 grupos con el total de votos de ambos años**, sin tabla oficial para repartir votos entre secciones hijas. El benchmark anterior de **sección individual** sigue absteniéndose en 165 secciones; los 33 grupos reconfigurados no se desagregan en pronósticos para cada una de sus 152 secciones 2024. Pendiente: evaluar la calidad geométrica de cada grupo y obtener relaciones oficiales sólo para mejorar resolución seccional, no para impedir la comparación agrupada.

Para ubicar casillas especiales, [el encarte IEEQ 2024](https://ieeq.mx/contenido/difusion/2024/Encarte_30052024.pdf) enlaza domicilio a las 57 S MR mediante sección+número de casilla. **Pendiente:** geocodificar y revisar manualmente cada punto contra el domicilio y la sección de instalación; localizar encartes completos 2018 y 2021 y los cambios posteriores al corte publicado. Para reconstruir reseccionamiento, obtener la **tabla final INE de sección origen→secciones resultantes** y, si está disponible, el desglose por manzana/localidad, de cada programa aplicable antes de las jornadas 2021 y 2024; no usar claves temporales de escenarios como definitivas. [Fuentes y hallazgos](RESECCIONAMIENTO_FUENTES.md).

Esta lista recoge los `NO VERIFICADO` y `NO ENCONTRADO` de los reportes temporales disponibles y de la inspección de código y datos de Prompt 6. Las rutas de `%TEMP%` se refieren a `C:\Users\HeyCe\AppData\Local\Temp` en esta sesión.

## NO VERIFICADO

El CCOL del INE sí contiene secciones y distritos, pero el corte 2022 no enlaza de forma segura por `(ENTIDAD, ID)` con `ColoniasINE2020a.parquet`: sólo 4 630 de 100 668 IDs compartidos coinciden también en nombre, municipio y CP. Faltan el CCOL del corte compatible, la procedencia geométrica exacta del Parquet de colonias y una validación de las coincidencias compuestas. [Auditoría y fuentes](CCOL_COLONIAS.md).

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
| En Prompt 6 no se encontró entonces la etiqueta local `demo-11am`; **esta observación histórica ya no describe el repositorio actual**. | `%TEMP%\cola3_reporte.md`; estado actualizado en [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md). |
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

## Pendientes del demo actual

La integración ECEG 2020 del 2026-11-06 cruza 67 736 secciones por `ID_SECCION` con cada una de las tres elecciones 2024. **NO VERIFICADO:** que la misma clave represente límites idénticos entre el seccionado ECEG 2020/2021 y el de 2024. Las asociaciones de `electoral/explicacion.py` son descriptivas entre secciones y no sustentan causalidad ni inferencias sobre votantes individuales.
El [histórico de secciones del INE](CPV_SIN_CRUCE.md#origen-registrado-en-el-histórico-del-ine) registra altas, bajas y movimientos parciales. Permite rastrear las 2 768 claves territoriales sin CPV a primeros movimientos etiquetados 2021–2023, pero **NO VERIFICA** que las 67 736 claves coincidentes representen la misma población. En Querétaro, la correspondencia espacial ECEG enero 2021→2024 ya separa 788 polígonos casi idénticos de 165 modificados/reconfigurados. La app local deja sin perfil CPV a los modificados; el bloque federal «¿Por qué?» aún requiere aplicar este control en las otras 31 entidades. No trasladar porcentajes de una sección de origen a sus hijas por simple copia.
En la app revisada, «¿Por qué?» de apoyo mínimo usa `piso_pct` del **partido** mostrado en esa pestaña. La función auxiliar `piso_candidatura()` permanece disponible, pero no alimenta esa vista.

| Punto | Evidencia y estado |
| --- | --- |
| La regla oficial de reparto de coaliciones por partido sigue **NO VERIFICADO**. La app vigente muestra `A_propios` por sección como estimación de aportes de partidos, sin cambiar el resultado de la candidatura. | [`app_simple.py`](../../electoral/app_simple.py), [`analisis_demo.py`](../../electoral/analisis_demo.py), [`reparto.py`](../../electoral/reparto.py). |
| Las clases `Bastión` y `Base fuerte` de apoyo mínimo son propuestas provisionales; su relación con una fidelidad individual o histórica sigue **NO VERIFICADO**. | [`analizar_fidelidad()`](../../electoral/fidelidad.py) y [METODOLOGIA.md](METODOLOGIA.md), sección «Apoyo mínimo observado 2024». |
| Fidelidad entre años y comparación de casillas de las tres boletas: **NO VERIFICADO** en el demo. Los archivos usados por la app son secciones de 2024 y casillas de Presidencia 2024. | [`config.py`](../../electoral/config.py) y [DATOS.md](DATOS.md). |
| La unión municipal CPV sigue **NO VERIFICADA** y no se utiliza. El nuevo cruce ECEG es por sección; su equivalencia espacial 2020/2021–2024 sigue **NO VERIFICADA**. | `%TEMP%\cartografunk_mza_20261103_claves_por_seccion.csv` registra discrepancias K1–K3; [DATOS.md](DATOS.md) mide el nuevo cruce por clave. |
| Las 19 secciones de Presidencia 2024 que siguen con votos sobre lista tras descontar casillas `S` no tienen explicación documental **NO VERIFICADO**. | `%TEMP%\electoral_reporte_cola6.md` y [`config.py`](../../electoral/config.py). |
| La meta de carga inicial menor de 10 s no se cumplió: AppTest midió 27.92 s tras precalcular los dos ámbitos. El aspecto en navegador y el arranque del servidor siguen **NO VERIFICADO**. | `%TEMP%\electoral_reporte_demo.md`, paso 2. |
