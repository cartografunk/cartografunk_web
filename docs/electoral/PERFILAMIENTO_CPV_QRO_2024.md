# Perfilamiento CPV por sección · Querétaro 2024

**Unidad:** sección; Querétaro sólo filtra la muestra. Los cuatro grupos se formaron exclusivamente con 15 tasas CPV 2020 del ECEG INEGI–INE. Después se cruzaron con los resultados IEEQ 2024. Los votos no intervienen en K-means. Se exige un mínimo de 12 de 15 tasas presentes; 787 de 788 secciones comparables cumplen. La sección restante no tiene ninguna tasa. Los nulos parciales se imputan con la mediana, las tasas se estandarizan y los extremos se limitan a ±3. Semilla 0, 20 inicializaciones; scikit-learn 1.9.0. [Código](../../electoral/perfilamiento_cpv.py).

| Perfil | Secciones | Rasgos CPV respecto de la muestra | PAN lideró entre siete partidos | PAN quedó a ≤5 pp del primero entre partidos | De esos casos, la candidatura local ya lideró |
| --- | ---: | --- | ---: | ---: | ---: |
| 1 | 264 | Más Internet y población económicamente activa; menos analfabetismo | 77 | 31 | 4 |
| 2 | 221 | Menos educación posbásica, más menores de 18, menos Internet | 51 | 21 | 11 |
| 3 | 185 | Más personas de 60+, menos menores de 18, más educación posbásica | 142 | 12 | 4 |
| 4 | 117 | Más analfabetismo y viviendas sin drenaje; menos Internet | 44 | 12 | 8 |

La separación entre grupos es modesta: silhouette de **0.183** para k=4, frente a 0.167, 0.179 y 0.154 para k=5, 6 y 7. Para k=4, la concordancia ARI de la semilla 0 con las semillas 1 y 2 fue **0.986** y **0.985**. Elegimos k=4 por estabilidad descriptiva; no son categorías naturales comprobadas ni tipos de votantes. El JSON local guarda k, semilla, versión y estas métricas.

**Auditoría de la antigua lista de 74.** En las 788 secciones evaluadas, el PAN quedó a ≤5 pp del primero entre **siete partidos con reparto fraccionario en 76**. El ML esperaba liderazgo en 74 y la simple persistencia de 2021 en 65; los 65 casos de persistencia están dentro de los 74. El filtro ML añade nueve casos y omite dos. Esta lista describe errores de pronóstico y derrotas partidarias cercanas; **no mide oportunidades de victoria**.

Al sumar las marcas IEEQ por candidatura local MR según las opciones de cada distrito, de esas 76 secciones la candidatura del PAN **ya lideró en 27**, empató en una y perdió en 48; sólo **17** tuvieron derrota de candidatura a ≤5 pp. Entre las 74 señaladas por ML, 26 ya tenían candidatura ganadora. El margen de partido y el de candidatura responden a preguntas distintas porque los votos de coalición se reparten entre partidos en el primero. [Auditoría reproducible](../../scripts/auditar_senales_ml_2024.py). La app ordena las 76 por perfil y sección, sin insinuar que la menor distancia sea más fácil de revertir.

La salida principal es un perfil censal descriptivo. Cuando se muestran resultados del modelo en ese perfil, se leen como **dónde falla el modelo**; las mismas 15 tasas CPV ya entraron al ML, por lo que el cruce no es validación independiente. Las cifras por perfil son medias simples por sección. **CPV 2020 vs votos 2024; asociación, no causa.** Hipótesis de reversión para una elección intermedia futura: **sin prueba**.

Los archivos locales `data/electoral/ieeq_local/perfilamiento_cpv_2024.json`, `perfilamiento_cpv_2024_seccion.parquet`, `margen_candidatura_ieeq_2024_seccion.parquet` y `auditoria_senales_ml_2024.json` no se versionan. Las 165 secciones con geometría modificada no entran en este análisis. El perfil de una sección no describe la edad, educación o preferencia de individuos, colonias o casillas extraordinarias.

**NO VERIFICADO:** que las derrotas cercanas sean reversibles, que los abstencionistas apoyarían al PAN, estabilidad de perfiles en otras elecciones o entidades, efecto causal del CPV, probabilidad futura de victoria y rendimiento de campaña. Rentabilidad y apoyo mínimo se evalúan por separado.
