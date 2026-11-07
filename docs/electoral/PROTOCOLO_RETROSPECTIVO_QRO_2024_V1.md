# Protocolo v1 · prueba retrospectiva seccional Querétaro 2024

**Fecha de congelación:** 2026-11-07. **Estado:** exploratorio, posterior al conocimiento de la cobertura 2024. No sustituye el NO-GO de tres elecciones de `IEEQ_LOCAL_ETAPAS_4_7.md`, no es preregistro independiente ni acredita capacidad prospectiva.

## Pregunta y unidad

Para cada sección residencial B+C+E de Querétaro, ¿qué candidatura o familia política habría liderado en 2024 con información disponible hasta 2021, y cuán bien cubren los intervalos retrospectivos el resultado observado? El distrito sólo sirve para construir la candidatura conforme al convenio y la boleta de cada año; la **salida es exclusivamente por sección**. Casillas S MR y voto anticipado A quedan fuera.

## Datos congelados

| Archivo local en `data/electoral/ieeq_local/` | SHA-256 |
| --- | --- |
| `dip_local_mr_2018_seccion_bce.parquet` | `3373cbc2da881c513b92c68eca70dc1170180150d652a83623789b3f52c81aa2` |
| `dip_local_mr_2021_seccion_bce.parquet` | `f591c0f91ab15cb3ec7d261091d4037ed71e134877ef68d5f10ad051a48b0b0f` |
| `dip_local_mr_2024_seccion_bce.parquet` | `ab55e028f3523883f7a78906b8e3405c874e3755702d044a2713e929c10408b3` |
| `crosswalk_qro_2018_2021_2024_referencias.parquet` | `08092bd1198c07543aed2a7aff2252ab24b9017fa7cf570f28073c0ad27f1644` |

Universo de evaluación principal: secciones 2024 con `CATEGORIA=sin_cambio_cartografico_referencia` en ECEG enero 2021→2024, misma clave, vínculo único e IoU ≥ 0.995. Ya se conocen **788 de 953 secciones** y **1 398 846 / 1 899 053 = 73.66 % de lista nominal 2024**. La cobertura debe acompañar **cada métrica**, con denominador 953 y 1 899 053; reportar además cobertura condicional dentro de las 788. Las otras 165 secciones quedan en abstención territorial. La cadena 2019→2021→2024 de 654 secciones y 55.47 % de lista nominal es sensibilidad separada, nunca se suma a la muestra principal.

## Condición de entrada: candidatura y resultado

Antes de calcular métricas se fija una tabla de **año × distrito local × candidatura × columnas de voto** a partir de convenios y boletas IEEQ, con URL y hash. En cada distrito-año las columnas propias y de combinación deben formar una partición: ninguna dos veces ni omitida; su suma más nulos y no registrados debe reconstruir `TOTAL_VOTOS` por sección. Cada combinación aporta **un voto a la candidatura**, sin reparto partidario. Si falta la tabla o falla la partición, **no se calcula liderazgo ni margen** y se reporta el fallo. El reparto de fracciones entre partidos, `A_propios` y el piso partidario no son objetivos de esta prueba.

La comparación temporal de candidaturas requiere una tabla explícita de familias por distrito-año; se congela junto con la tabla anterior. No se infiere continuidad de personas ni se considera una familia idéntica a una candidatura. Se informa qué familias carecen de homólogo en 2021 y se abstiene para ellas. `CPV 2020`, variables derivadas de votos 2024 y cambios conocidos después de la jornada no entran en predictores.

Objetivos observados: cuota de votos válidos B+C+E de cada candidatura/familia y **margen firmado frente al mejor rival** en puntos porcentuales. Liderar significa margen > 0; empate = 0 y se informa por separado. El denominador son votos válidos de candidaturas, excluyendo nulos y no registrados. Se verifica numéricamente antes de modelar.

## Baselines y validación temporal

1. **Persistencia:** cuota 2024 predicha = cuota 2021 de la misma familia y sección. Comparador principal, sin ajuste con 2024.
2. **Media histórica:** cuota 2024 predicha = cuota media 2021 de la familia en las secciones elegibles de entrenamiento; comparador ingenuo. Ninguna media usa resultados 2024.
3. **Swing histórico simple:** en secciones de la cadena estable 2019→2021 se calcula el cambio medio 2018→2021 por familia; se suma a la cuota 2021 y se acota a [0, 100]. Es sensibilidad por la cartografía 2018 no certificada y por el distinto tipo de elección.
4. **Techo retrospectivo con oráculo:** cambio agregado 2021→2024 conocido después de la elección; sólo diagnóstico, **nunca** pronóstico ni competidor elegible.

No se ajustan parámetros, familias, filtros ni umbrales con el error 2024. El año 2024 se evalúa una sola vez tras el sello de este documento y de las tablas de candidatura. Sin tabla certificada, se detiene la evaluación en el control de datos. Un modelo bayesiano o de ML queda fuera de v1; requerirá otro protocolo sellado.

## Incertidumbre, abstención y métricas

Para persistencia, el intervalo exploratorio del margen se obtiene con el percentil 90 del error absoluto de margen observado en la transición 2018→2021 de la cadena estable, aplicado simétricamente al margen 2024 predicho. Es un procedimiento congelado pero **no garantiza cobertura** al cambiar de tipo de elección. Si no hay muestra histórica válida para una familia, se abstiene; no se fabrica un intervalo.

Abstención por orden exclusivo: (1) sección territorialmente modificada o sin vínculo 2021; (2) candidatura/familia sin mapa o dato 2021; (3) sin intervalo histórico estimable; (4) intervalo de margen que contiene 0. Se cuentan secciones y lista nominal por causa, dentro de 788 y sobre 953. Un intervalo que cruza el empate significa «sin pronóstico de liderazgo», aunque se puede conservar la cuota estimada como ejercicio exploratorio rotulado.

Métrica principal: MAE de la cuota de votos válidos en **puntos porcentuales**, macro-promediado entre familias con homólogo. Secundarias: MAE del margen firmado, error de cuota ponderado por votos válidos, cobertura empírica del intervalo nominal 90 %, anchura mediana del intervalo, acierto de liderazgo sólo entre secciones sin abstención y curva riesgo–cobertura por umbrales de anchura predefinidos 5, 10, 15 y 20 pp. Todos los resultados llevan `n` de secciones, suma de lista nominal y cobertura sobre el total. No hay p-valores ni afirmaciones de causalidad.

Sensibilidades separadas: excluir las cinco secciones afectadas por las seis filas judiciales de 2024; usar sólo la cadena estable de 654; comparar familias individuales sin reasignar votos de combinaciones a partidos. No cambiar la definición principal tras ver estas sensibilidades.

## Criterio de lectura

Esta prueba no tiene umbral de GO comercial. Se informa error, cobertura, abstención y comparación con persistencia; cualquier ventaja de un método más complejo deberá pasar por un protocolo futuro. La muestra estable puede estar sesgada hacia zonas con menor crecimiento. La versión jurídica exacta de algunos resultados 2024 y el marco 2018 siguen **NO VERIFICADOS**. Ninguna cifra de esta corrida se presenta como probabilidad de ganar en 2027.
