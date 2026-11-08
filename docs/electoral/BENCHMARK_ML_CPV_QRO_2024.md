# Primer ensayo ML con CPV · Querétaro 2024

**Corrida exploratoria del 2026-11-07.** Unidad: sección; Querétaro filtra la muestra. Objetivo: cuota atribuida a cada uno de siete partidos comunes a 2018, 2021 y 2024. El reparto de combinaciones IEEQ es fraccionario, como se documenta en el [benchmark partidario inicial](BENCHMARK_PARTIDOS_QRO_2024.md).

Se entrenó con **654 secciones** estables en la transición 2018→2021 y se evaluó 2021→2024 en **788 de 953 secciones**, que cubren **1 398 846 de 1 899 053 personas de lista nominal (73.66 %)**. Los votos de 2024 sólo se usan al medir el error. Las otras 165 secciones quedan sin salida por cambio territorial; no se reparte el voto de secciones padre entre hijas. Una sección del entrenamiento y una de la evaluación tienen las 15 tasas CPV nulas; el modelo las conserva como faltantes. Las 15 tasas provienen del [ECEG INEGI–INE](DATOS.md#cpv-2020-por-sección-eceg-inegi-ine-integración-2026-11-06).

El modelo nuevo es `HistGradientBoostingRegressor` por partido, con cuotas de los siete partidos en el año anterior, participación, `log1p(lista nominal)` y 15 tasas CPV 2020. Parámetros fijos: 150 iteraciones, 8 hojas, mínimo 30 muestras por hoja, tasa 0.05, regularización L2 10 y semilla 0. No se ajustaron con resultados 2024. Se compara con persistencia y Ridge sin CPV en **las mismas 788 secciones**. El código reproducible está en [`scripts/benchmark_ieeq_ml_cpv.py`](../../scripts/benchmark_ieeq_ml_cpv.py).

| Método | MAE medio cuota, pp | MAE medio margen, pp | MORENA: líderes detectados / observados | MORENA: falsos líderes | PAN: falsos líderes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Persistencia 2021 | 5.95 | 12.17 | 85 / 436 | 11 | 350 |
| Ridge sin CPV | **5.38** | **11.32** | 89 / 436 | 2 | 382 |
| Árbol con CPV | 5.90 | 12.77 | 75 / 436 | 8 | 393 |

Estos liderazgos usan la **estimación puntual** entre siete partidos. En el informe anterior, el «0 de 436» de Ridge correspondía a una decisión mucho más exigente: intervalo completo por encima de cero; no contradice los 89 líderes detectados por su punto estimado aquí. El árbol con CPV **no mejora** el error medio ni la detección de liderazgo sobre Ridge en esta prueba. Su sesgo medio `observado − predicho` para MORENA es **+8.87 pp**, compatible con un cambio de ciclo que el entrenamiento 2018→2021 no anticipó. Para PAN marca falsamente liderazgo en 393 secciones: su lectura de «dónde ganarás» no es fiable.

La pestaña «Forecasting · diagnóstico» muestra el ensayo ML si existen los dos archivos locales `benchmark_ml_cpv_2024.json` y `benchmark_ml_cpv_2024_seccion.parquet`; de otro modo lo oculta. La tabla desagrega por **partido y sección**, sin resultados por estado o municipio. La etiqueta visible dice «CPV 2020 vs votos 2024; asociación, no causa»; método y parámetros quedan en «Avanzado».

**NO VERIFICADO:** desempeño prospectivo, porcentaje de confianza para elecciones futuras, efecto causal de las variables CPV, geografía exacta de 2018 y perfil demográfico propio de casillas E. La selección de esta arquitectura ocurrió después de conocer los resultados generales del benchmark anterior, así que tampoco es una prueba ciega. El CPV de 2020 es posterior a la elección 2018 usada como entrada histórica: esta corrida es una reconstrucción retrospectiva, no una simulación estricta de lo que se sabía en 2018.
