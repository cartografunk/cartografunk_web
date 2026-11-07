# Estado actual del módulo electoral

## Benchmark exploratorio por partido, 2026-11-07

Se ejecutó la [primera prueba retrospectiva por partido](BENCHMARK_PARTIDOS_QRO_2024.md) en 788 de 953 secciones comparables ECEG→2024 (73.66 % de lista nominal). Las combinaciones IEEQ se atribuyen por fracciones iguales a los partidos marcados, sin redondeo seccional. Ridge obtuvo MAE medio de cuota de 5.38 puntos porcentuales frente a 5.95 de persistencia 2021, pero no detectó ninguna de las 436 secciones donde MORENA lideró entre siete partidos comparables. **No hay pronóstico de liderazgo confiable ni validación prospectiva.** El código, protocolos sellados, cobertura y abstenciones están documentados en ese informe. La etapa 6 anterior conserva su resultado histórico de NO-GO de tres fechas; la corrida actual es una decisión exploratoria posterior del propietario.

El [cruce de encartes 2021 y 2024](CRUCE_ENCARTES_QRO_2021_2024.md) encontró candidatos de origen para las 81 secciones 2024 sin clave ECEG: ocho con mismo domicilio de casilla, 69 adicionales con misma localidad y superposición territorial, y cuatro sólo con vínculo geométrico. El listado de 92 enlaces queda local para revisión sección por sección. No se redistribuyeron votos ni población por esa pista.

## Piloto local Querétaro: etapas 1–3

Se descargaron y normalizaron los resultados IEEQ de diputaciones locales MR 2018, 2021 y 2024. Las salidas locales por casilla, sección B+C+E y casillas especiales, los hashes de 20 archivos fuente y los cotejos están descritos en [IEEQ_LOCAL_ETAPAS_1_3.md](IEEQ_LOCAL_ETAPAS_1_3.md). Hay 860, 891 y 953 secciones B+C+E respectivamente. El cotejo seccional no deja diferencias sin explicar; las casillas S se conservan aparte como voto fuera de la sección de residencia. Se versionaron los Parquet pequeños de casillas especiales MR 2018/2021/2024 y el domicilio de instalación de las 57 S de 2024 extraído del encarte IEEQ; faltan coordenadas verificadas. El [crosswalk geométrico y las puertas de etapas 4–7](IEEQ_LOCAL_ETAPAS_4_7.md) ya están medidos para Querétaro: 788/953 secciones 2024 casi idénticas al marco ECEG de enero de 2021; 654/953 también casi idénticas a la referencia 2019 en el paso anterior. La cadena cubre 55.47 % de la lista nominal 2024, debajo del umbral de 70 % registrado junto con el resultado, **sin preregistro independiente: NO-GO para ML de tres elecciones**. La app ya incluye una pestaña de diagnóstico local por sección. La geometría exacta de 2018 y el voto de diferencia distrital 2018 siguen **NO VERIFICADOS**. [Fuentes de reseccionamiento](RESECCIONAMIENTO_FUENTES.md).

## Auditoría de colonias del 2026-11-06

Se obtuvo el CCOL nacional 2022 del INE y se comparó con `ColoniasINE2020a.parquet`. Aunque 100 668 polígonos comparten `(ENTIDAD, ID)` con el catálogo, sólo 4 630 coinciden también en nombre, municipio y CP: **el ID no es una llave segura entre cortes**. En las 95 007 colonias con un único candidato por atributos, 104 704 de 111 524 pares colonia–sección del piloto espacial (93,885 %) aparecen también en el CCOL 2022. La procedencia y el corte exacto de los polígonos, así como la causa de los 6 820 pares discordantes, siguen **NO VERIFICADOS**. La app conserva el ECEG a nivel sección; [auditoría y fuentes](CCOL_COLONIAS.md).

## Adición del 2026-11-06

Se integró el CPV 2020 del ECEG INEGI-INE por `ID_SECCION` en un Parquet local con 15 tasas. La coincidencia exacta de claves con cada Parquet seccional 2024 es de 67 736 secciones (96,030–96,074 %) y cubre 94,501–94,719 % de su lista nominal; detalle en [DATOS.md](DATOS.md). «¿Por qué?» ahora muestra el perfil CPV por clase de **sección**: ganada sólida, pérdida competitiva y pérdida lejana en la vista electoral; Bastión, Base fuerte y Resto en apoyo mínimo por partido. Cada variable tiene medias y diferencias estandarizadas; correlación y regresión se dejan en «Avanzado». El estado solo filtra la muestra. El INE resecciona y puede alterar incluso secciones que conservan su clave: en Querétaro ya se midió la superposición ECEG→2024; para el resto del país la equivalencia geométrica sigue **NO VERIFICADA**, y la composición de personas no se infiere de polígonos.

Los tres CSV completos del ZIP ECEG se guardaron además como Parquet y tablas materializadas en `data/electoral/eceg_2020.duckdb`: 32 entidades, 300 distritos federales y 68 806 secciones. La suma `POBTOT` coincide entre niveles (126 014 024). Las 15 tasas usadas por la app se verificaron contra el Parquet seccional completo sin discrepancias. Los archivos generados son locales, no versionados; [DATOS.md](DATOS.md#tablas-completas-de-entidad-distrito-y-sección) documenta rutas, llaves y límites de uso. La app sigue operando a nivel sección; las tablas agregadas sirven para consulta y auditoría.

El primer modelo de `explicacion.py` usaba `margen_pct` como objetivo y eliminaba sus nulos. Como `margen_pct` solo existe cuando la candidatura ganó, **sí filtraba de hecho el análisis a victorias**. El objetivo electoral actual es `ventaja_firmada = margen_pct` en victoria, `-faltante_pct` en derrota y `0` en empate. `faltante_pct` y `alcanzable_por_abstencion` se analizan únicamente en derrotas; `rescatable_vs_abst` no entra como variable. El modelo de apoyo mínimo usa `piso_pct` del partido seleccionado.

La auditoría de secciones sin CPV por estado y clase está en [CPV_SIN_CRUCE.md](CPV_SIN_CRUCE.md) y su CSV de detalle. Validación de esta revisión: **75 pruebas aprobadas**, 2 advertencias de GDAL. AppTest con `timeout=180` abrió «Mapa y secciones» y «Apoyo mínimo», además de Diputaciones y Senadurías: los bloques «¿Por qué?» aparecieron sin excepciones. La vista se inspeccionó en navegador a 1252 px y 390 px: la tabla se desplaza dentro de su marco en móvil, sin desbordamiento horizontal de la página. La portada ya describe el CPV como disponible cuando existe el archivo local. La cifra histórica de 67 pruebas del apartado inferior corresponde al estado previo a la integración CPV.

El histórico oficial del INE registra primeros movimientos 2021–2023 para las **2 768 secciones territoriales** de 2024 sin clave ECEG. Esto acota la falta de cobertura por clave; la equivalencia de los polígonos de las **67 736 claves coincidentes sigue NO VERIFICADA**. El paquete local `deploy_streamlit/` contiene `explorador.py`, no `electoral/app_simple.py`; no hay un despliegue electoral configurado en ese paquete para revisar visualmente.

Actualizado: 2026-11-04. Fuente principal: código y pruebas de esta rama. Las cifras de inventario históricas conservan sus fuentes en [DATOS.md](DATOS.md) y [PENDIENTES.md](PENDIENTES.md).

## Rama y aplicaciones

| Elemento | Estado comprobado |
| --- | --- |
| Rama de trabajo | `demo-tres-elecciones`, derivada de `demo-11am` (`31464db`) y publicada como `origin/demo-tres-elecciones`. |
| Respaldos locales | `respaldo-antes-noche` apunta a `ab5b4ea`; `demo-11am`, `demo-11am-b` y `demo-11am-c` conservan sus commits originales. No se publicaron esas etiquetas. |
| App vigente para el demo | `electoral/app_simple.py`: selector de Presidencia, Diputaciones MR y Senadurías MR de 2024; candidatura activa, mapa, clases, aportes de partidos de coalición, priorización y apoyo mínimo. |
| App anterior | `electoral/demo_app.py`: demo de Presidencia 2024. |
| Archivos de datos | `data/electoral/*.parquet`, generados localmente y no versionados; los ZIP de origen se indican en `electoral/config.py`. |

Los cambios funcionales de `demo-11am-b` (controles técnicos en «Avanzado») y `demo-11am-c` (costo inicial vacío, persistencia por sesión, tabla legible, Querétaro por omisión) se integraron en la app vigente. El ámbito de apoyo mínimo permanece visible, según la corrección posterior a `demo-11am-b`. Las ramas y etiquetas de respaldo no se borraron.

## Cálculos que muestra la app

- El resultado, la clase, el margen, el faltante y los votos para ganar pertenecen a la **candidatura** seleccionada. En Diputaciones y Senadurías, las candidaturas activas varían por distrito; una sección sin la candidatura elegida queda sin clase para ella. Véanse `electoral/analisis_demo.py`, `electoral/candidaturas.py` y `electoral/rentabilidad.py`.
- El selector de partidos aparece junto al de candidatura cuando se elige una coalición. Los votos atribuidos y porcentajes por sección y estado usan `repartir_coalicion(..., variante="A_propios")`. Es un reparto **experimental**; la regla oficial sigue NO VERIFICADA.
- «Apoyo mínimo observado 2024» compara las tres boletas del mismo año. Sus clases son una propuesta provisional; no mide personas ni continuidad entre años. Véanse `electoral/fidelidad.py` y `electoral/estadisticas_fidelidad.py`.
- El simulador espera un costo ingresado por el usuario antes de calcular. Conserva costos y descartes por sesión y los rotula como «supuesto del usuario» en el Excel.
- El CPV 2020 se incorporó por sección mediante ECEG. La equivalencia territorial exacta del seccionado ECEG con 2024 sigue NO VERIFICADA.

## Validación de esta integración

Ejecutado desde `C:\cartografunk_web` con `D:\Conda\envs\cartografunk\python.exe`:

```powershell
$env:PATH='D:\Conda\envs\cartografunk\Library\bin;'+$env:PATH
D:\Conda\envs\cartografunk\python.exe -B -m pytest electoral/tests -q
```

Resultado: **67 aprobadas, 0 omitidas**, 2 advertencias de GDAL. AppTest con `timeout=180`: **0 excepciones** en Presidencia/PVEM-PT-MORENA/estado 14, Diputaciones MR/PAN-PRI-PRD/estado 9 y Senadurías MR/MC/estado 14; tiempos medidos 32.03 s, 9.98 s y 10.47 s, respectivamente. El aspecto en navegador y el arranque del servidor: **NO VERIFICADO**.

## Acceso entre cuentas

Esta documentación se comparte mediante `origin/demo-tres-elecciones`. No existe un `.mcp.json` en el repositorio. Los Parquet locales y las rutas `D:\` no se comparten por Git; su acceso desde otras cuentas o máquinas es **NO VERIFICADO**. No se ha implementado un servidor MCP para esos datos.
