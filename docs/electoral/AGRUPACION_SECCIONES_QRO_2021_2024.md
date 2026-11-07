# Reagrupación de secciones IEEQ 2021→2024

**Fecha:** 2026-11-07. Unidad de comparación: grupo de secciones relacionadas, formado exclusivamente dentro de Querétaro. No hay resultados por entidad, municipio o distrito.

## Regla simple

Los resultados B+C+E ya están sumados por sección en los Parquet IEEQ de cada año. `scripts/agrupar_ieeq_2024_a_2021.py` toma los enlaces origen 2021 ↔ destino 2024 del crosswalk geométrico y forma grupos conectados. En cada grupo suma **todos** los votos, opciones, votos válidos y lista nominal de 2021 por un lado y los de 2024 por otro. Cada sección entra exactamente una vez en su año. Así, cuando una sección antigua se divide en varias nuevas, se comparan **sumas**, sin repartir el voto antiguo entre hijas. Si varias antiguas desembocan en varias actuales, todas quedan en el mismo grupo.

El [cruce de encartes](CRUCE_ENCARTES_QRO_2021_2024.md) corrobora domicilio o localidad para 77 de las 81 claves nuevas, pero el domicilio de instalación no es la llave del grupo ni identifica residencia. El crosswalk exige al menos 1 % de intersección en origen o destino; contactos menores quedan fuera. Por eso la reagrupación es analítica y requiere revisar los grupos grandes o relaciones oficiales si se pretende una equivalencia cartográfica exacta.

## Medido

| Resultado | Valor |
| --- | ---: |
| Secciones 2021 / 2024 incluidas | 891 / 953 |
| Grupos conectados | 834 |
| Grupos de una sección en cada año | 801 |
| Grupos reconfigurados | 33 |
| Secciones 2021 / 2024 dentro de los 33 grupos | 90 / 152 |
| Lista nominal 2024 en esos 33 grupos | 457 109 de 1 899 053 (24.07 %) |
| Grupo más grande | 11 secciones 2021 o 25 secciones 2024, según el grupo |
| Lista nominal 2024 conservada tras sumar | 1 899 053 de 1 899 053 |
| Lista nominal 2021 conservada tras sumar | 1 736 369 de 1 736 369 |

Los archivos locales, sin commit, son `mapa_grupos_secciones_2021_2024.csv`, `dip_local_mr_2021_agrupado_2021_2024.parquet`, `dip_local_mr_2024_agrupado_2021_2024.parquet` y `resumen_grupos_secciones_2021_2024.json`, en `data/electoral/ieeq_local/`. El identificador del grupo es la menor clave 2021 que contiene; **no** es una clave oficial nueva.

## Benchmark exploratorio sobre los 834 grupos

`scripts/benchmark_ieeq_grupos_2024.py` conserva el entrenamiento previo de 654 secciones en la transición 2018→2021 y evalúa 2024 **después de reagrupar**. No reentrena con votos 2024. El MAE macro de cuota de los siete partidos es **5.91 pp** para persistencia y **5.37 pp** para Ridge. En MORENA, Ridge acierta el liderazgo de **106 de 462 grupos** donde lideró, pero también lo había marcado en **2 grupos donde no lideró**; esta decisión se basa sólo en el punto estimado. En PAN marca falsamente liderazgo en **391 grupos**. El modelo sigue sesgado por el cambio de ciclo y no se convierte en pronóstico fiable por ampliar la cobertura.

Estos conteos **no son comparables directamente** con el benchmark de 788 secciones: aquí la unidad son 834 grupos, 33 de ellos contienen más de una sección en algún año, y no se han recalibrado intervalos para esa escala. La pestaña de forecasting muestra la comparación por grupo como diagnóstico histórico; no asigna una predicción propia a cada sección hija. Las tablas locales son `benchmark_partidos_grupos_2024.json` y `benchmark_partidos_grupos_2024.parquet`.

**NO VERIFICADO:** igualdad exacta de la población entre el perímetro combinado de ambos años, enlaces territoriales inferiores al umbral de 1 %, correspondencia administrativa oficial, localización de electores individuales, calibración de intervalos por grupo y capacidad prospectiva de los modelos.
