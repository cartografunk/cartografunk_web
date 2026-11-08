# Perfilamiento electoral por sección · Querétaro 2024

**Unidad:** sección. Querétaro sólo filtra la muestra. El [ensayo ML](BENCHMARK_ML_CPV_QRO_2024.md) estimó cuotas por partido; este análisis separa **perfiles censales** de **resultados electorales observados** antes de incorporar rentabilidad o apoyo mínimo.

El algoritmo K-means agrupa secciones usando exclusivamente las 15 tasas CPV 2020 del ECEG INEGI–INE. Se imputan nulos parciales con la mediana de la muestra, se estandarizan las tasas y se limitan valores estandarizados extremos a ±3 antes de agrupar. Se fijaron cinco perfiles y semilla 0. **Los votos de 2024 no entran a formar los grupos**; se cruzan después para describir cuotas, liderazgo y derrotas. De las 788 secciones con geometría comparable, **787 tienen al menos una tasa CPV** y reciben perfil; una queda fuera. El código está en [`electoral/perfilamiento_cpv.py`](../../electoral/perfilamiento_cpv.py) y [`scripts/perfilar_ieeq_cpv_2024.py`](../../scripts/perfilar_ieeq_cpv_2024.py).

| Perfil | Secciones | Rasgos CPV más distintos del promedio de muestra | PAN lideró en 2024 | PAN: derrota ≤5 pp + ML esperaba liderazgo |
| --- | ---: | --- | ---: | ---: |
| 1 | 205 | Menos educación posbásica, más menores de 18, menos Internet | 48 | 18 |
| 2 | 187 | Más Internet, menos menores de 18, menos analfabetismo | 62 | 23 |
| 3 | 176 | Más Internet, menos personas de 60+, más educación posbásica | 60 | 21 |
| 4 | 117 | Más analfabetismo, más viviendas sin drenaje, menos Internet | 44 | 11 |
| 5 | 102 | Más personas de 60+, menos menores de 18, más educación posbásica | 100 | 1 |

En las 788 secciones del benchmark, el ML pronosticó liderazgo del PAN en **393 donde no lideró**. Su desventaja observada fue ≤5 puntos en **74**, entre 5 y 10 en **83**, y mayor de 10 en **236**; la mediana fue **12.64 puntos**. Las 74 primeras son una **lista de revisión**, no 74 victorias alcanzables. Una sección de las 393 no tiene perfil CPV por tasas nulas; las 74 cercanas sí aparecen en los cinco perfiles. La app muestra esas secciones y sus perfiles, sin costo ni apoyo mínimo dentro de este bloque.

El perfil 5 describe secciones donde el PAN ya lideró en 100/102 casos; las 74 derrotas cercanas de revisión se concentran en los perfiles 1–4 (73/74). Esta segmentación ayuda a formular hipótesis de mensajes o trabajo territorial para contrastar después; no demuestra que edad, educación o Internet causen el voto. **CPV 2020 vs votos 2024; asociación, no causa.**

Las salidas `data/electoral/ieeq_local/perfilamiento_cpv_2024.json` y `perfilamiento_cpv_2024_seccion.parquet` son locales y no se versionan. Un perfil representa el promedio de una **sección**, no el perfil individual de votantes, de las casillas E o de una colonia. Las 165 secciones territorialmente modificadas carecen de perfil comparable.

**NO VERIFICADO:** que los 74 casos puedan voltearse, que las personas abstencionistas apoyen al partido, estabilidad de perfiles entre elecciones, efecto causal del CPV, probabilidad de victoria o rendimiento de campaña. Rentabilidad y apoyo mínimo se evaluarán como capas separadas después del perfilamiento.
