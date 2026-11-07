# Benchmark retrospectivo por partido · Querétaro 2024

**Corrida exploratoria del 2026-11-07.** Protocolos sellados antes de la primera métrica: [v1](PROTOCOLO_RETROSPECTIVO_QRO_2024_V1.md), [v1.1](PROTOCOLO_RETROSPECTIVO_QRO_2024_V1_1.md) y [v1.2, objetivo por partido](PROTOCOLO_RETROSPECTIVO_QRO_2024_V1_2.md), SHA-256 de v1.2 `7c3bbdbdf038e079460fd1152418b0ee465b80654e24caeb8e883c66e9bcef5a`, commit `61212c9`. El cambio a partido fue instrucción del propietario antes de evaluar 2024; los documentos anteriores se preservan. El código de la primera corrida no estaba sellado por separado: el sello cubre el diseño, no una implementación ciega.

## Qué se calculó

Cada partido recibe sus votos de marca individual y una fracción igual de los votos de cada combinación que lo incluye. Las fracciones no se redondean por sección; el sobrante entero oficial corresponde al cómputo distrital y no puede localizarse en una sección. Los votos de candidaturas independientes se mantienen en el denominador válido. Se evaluaron PAN, PRI, PRD, MC, PVEM, MORENA y PT, presentes en las tres elecciones. `QS` y otros partidos de año único se excluyen del modelo, pero permanecen en los votos válidos. «Liderazgo» en este informe significa mayor cuota **entre esos siete partidos**, no victoria de la candidatura de mayoría relativa.

Universo principal: **788/953 secciones (82.69 %)** con geometría ECEG enero 2021→2024 casi idéntica; **1 398 846/1 899 053 de lista nominal (73.66 %)**. Las otras **165 secciones y 500 207 personas en lista nominal** se abstienen por cambio territorial. No hubo faltantes entre los siete partidos en las 788. Una sección de las 788 tuvo como partido de mayor cuota a `QS`, fuera de la serie comparable. La calibración histórica de Ridge usa las **654 secciones** estables también respecto a la referencia 2019; esta referencia no certifica el seccionado de la jornada 2018.

| Método | MAE medio de cuota de los siete partidos, pp | MAE medio de margen, pp | Cobertura base |
| --- | ---: | ---: | --- |
| Persistencia de 2021 | 5.95 | 12.17 | 788/953; 73.66 % de lista nominal |
| Media de 2021 | 6.80 | 14.66 | 788/953; 73.66 % |
| Swing de 2018→2021 | 6.88 | 17.67 | 788/953; 73.66 % |
| Ridge autoregresivo fijo | 5.38 | 11.32 | 788/953; 73.66 % |

La diferencia de MAE entre Ridge y persistencia es descriptiva. **No se declara mejora validada.** En sensibilidad sobre la cadena de 654 secciones, el MAE medio es 5.79 pp para persistencia y 5.24 pp para Ridge. Al excluir las cinco secciones con anotaciones judiciales de 2024, es 5.95 y 5.39 pp, respectivamente.

## Dónde falla la decisión de liderazgo

Los intervalos nominales del 90 % se calibraron con errores 2018→2021 y se evaluaron en 2024. Se emite «lidera» sólo si todo el intervalo del margen queda sobre cero; «no lidera» si queda bajo cero. Si cruza cero, se abstiene. Los siguientes conteos son **dentro de las 788 secciones comparables**; se agregan a las 165 abstenciones territoriales al hablar de la cobertura total.

| Partido | Líder observado entre 7 | Líderes detectados: persistencia / Ridge | Cobertura del intervalo 90 %: persistencia / Ridge | Abstenciones por empate: persistencia / Ridge |
| --- | ---: | ---: | ---: | ---: |
| PAN | 314 | 153 / 137 | 84.1 % / 78.0 % | 616 / 627 |
| MORENA | 436 | 3 / **0** | 73.6 % / **78.4 %** | 528 / 587 |
| PRI | 10 | 1 / 0 | 95.3 % / 96.7 % | 423 / 314 |
| MC | 6 | 0 / 0 | 92.4 % / 88.1 % | 3 / 0 |
| PVEM | 21 | 0 / 0 | 92.4 % / 90.4 % | 35 / 0 |
| PT | 1 | 0 / 0 | 95.2 % / 92.0 % | 2 / 0 |
| PRD | 0 | 0 / 0 | 96.2 % / 92.3 % | 1 / 0 |

Ridge detecta **cero** de las 436 secciones donde MORENA encabezó entre los siete partidos, pese a su menor MAE medio. La cifra de acierto entre «no lidera» emitidos sería engañosa por el predominio de negativos; por eso se reportan líderes detectados y abstenciones. El intervalo no alcanza su cobertura nominal para PAN y MORENA. **Estos modelos no sustentan todavía una respuesta fiable a «dónde ganará mi partido» ni un porcentaje de confianza.**

### Diagnóstico posterior a la prueba

El sesgo medio `observado − predicho` de Ridge en las 788 secciones fue **+6.73 pp para MORENA** y **−9.37 pp para PAN**. Como diagnóstico con **oráculo 2024**, sumar a cada partido su sesgo medio observado reduce el MAE macro de 5.38 a 3.86 pp y recupera 365 de las 436 secciones encabezadas por MORENA. La persistencia ajustada con su propio sesgo 2024 recupera 352. Esto apunta a un cambio agregado de ciclo como parte importante del fallo, pero el ajuste usa el resultado de la prueba y **no es un pronóstico**. Claude sugirió contrastar explícitamente este sesgo antes de diseñar un modelo de escenarios; la interpretación causal o la capacidad futura siguen sin verificarse.

## Archivos y huecos

La corrida se reproduce con `D:\Conda\envs\cartografunk\python.exe -B -m scripts.benchmark_ieeq_partidos`. Los resultados detallados locales, sin commit, son `data/electoral/ieeq_local/benchmark_partidos_2024.json` y `benchmark_partidos_2024_seccion.parquet`. `electoral/reparto_ieeq.py` contiene las columnas de voto propio y combinaciones por año. **94 pruebas electorales aprobadas**, 2 advertencias GDAL.

**NO VERIFICADO:** reparto entero distrital contra totales partidarios oficiales; equivalencia exacta del marco de 2018; versión jurídica final de todas las filas 2024; desempeño prospectivo; calibración fuera de un único cambio de ciclo; apoyo del partido como voto de personas persistentes; victoria legal de la candidatura a partir del liderazgo partidario fraccionario. El protocolo se publicó antes de la métrica, pero se diseñó con conocimiento previo de la cobertura y del resultado general de 2024: no es una prueba ciega ni preregistro externo.
