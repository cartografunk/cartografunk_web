# Secciones 2024 sin cruce ECEG 2020

Medición local del 2026-11-06. Se comparó `ID_SECCION` con `data/electoral/cpv_2020_seccion.parquet`. Se excluyeron 32 filas de extranjero de Presidencia y 32 de Senadurías; no son secciones territoriales. El [CSV de detalle](cpv_sin_cruce_por_estado_clase.csv) contiene **2 979 filas** por elección, candidatura o partido, estado y clase, con total, faltantes, tasa de falta, proporción de faltantes del estado y razón frente a la tasa estatal. Se reproduce con `scripts/report_cpv_sin_cruce.py`.

## Por estado

En cada elección, las mismas **2 768 secciones territoriales** de 2024 no tienen clave ECEG; el número por estado también es igual en las tres. La tabla cuenta secciones únicas, sin multiplicarlas por candidaturas.

### Origen registrado en el histórico del INE

Se descargó el [Histórico de Secciones del INE, corte diciembre de 2025](https://cartografia.ine.mx/mapoteca/historicos/HISTORICO_SECC_ELECT_PEF_1994-PEF2024_Corte_diciembre2025.accdb) desde el [SIGE](https://cartografia.ine.mx/sige8/estadisticos-Geoelectorales). El archivo registra altas, bajas y movimientos parciales desde 1994; no es una geometría comparable por sí mismo. Las 2 768 claves sin CPV aparecen en él y su campo `PRIMER_MOVIMIENTO` menciona exactamente uno de los años 2021, 2022 o 2023. Se extrajo con `scripts/export_historico_ine.ps1` y se auditó con `scripts/audit_eceg_historico.py`; la [tabla por estado y año](cpv_sin_cruce_origen.csv) conserva los conteos y la lista nominal de Presidencia 2024.

| Año mencionado en `PRIMER_MOVIMIENTO` | Secciones sin CPV | Lista nominal 2024 |
| ---: | ---: | ---: |
| 2021 | 947 | 1 727 533 |
| 2022 | 1 370 | 2 768 364 |
| 2023 | 451 | 694 709 |
| **Total** | **2 768** | **5 190 606** |

La [metodología de ECEG](https://gaia.inegi.org.mx/mdm6/docs/geoelectorales/Metodolog%C3%ADa_de_Estad%C3%ADsticas_Censales_a_escalas_Geoelectorales.pdf) indica que usó el marco seccional del INE de enero de 2021. Estos movimientos registrados son coherentes con la ausencia de las claves en ECEG. El año es una etiqueta textual del primer movimiento, **no una fecha exacta de entrada en vigor**. El histórico incluso llena `Distrito_PEF2021` para algunas secciones cuya descripción dice «nueva por reseccionamiento 2022»; por ello no se usa esa columna como prueba de existencia en 2021. Tampoco puede deducirse de este archivo que todas las claves coincidentes conserven límites idénticos.

| Estado | Sin CPV | Estado | Sin CPV | Estado | Sin CPV | Estado | Sin CPV |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 01 | 52 | 09 | 64 | 17 | 47 | 25 | 88 |
| 02 | 110 | 10 | 22 | 18 | 39 | 26 | 58 |
| 03 | 48 | 11 | 99 | 19 | 135 | 27 | 52 |
| 04 | 18 | 12 | 43 | 20 | 91 | 28 | 104 |
| 05 | 101 | 13 | 82 | 21 | 206 | 29 | 29 |
| 06 | 28 | 14 | 227 | 22 | 81 | 30 | 92 |
| 07 | 228 | 15 | 284 | 23 | 55 | 31 | 59 |
| 08 | 64 | 16 | 59 | 24 | 61 | 32 | 42 |

## Por clase

Las clases dependen de candidatura y elección. Por ello, las cifras siguientes cuentan **sección × candidatura**, y en apoyo mínimo **sección × partido**. Una misma sección puede aparecer varias veces; no se deben sumar para obtener secciones únicas.

| Ámbito | Clase | Sin CPV / total | Tasa sin CPV |
| --- | --- | ---: | ---: |
| Presidencia, candidaturas | Ganada sólida | 2 438 / 59 138 | 4,12 % |
| Presidencia, candidaturas | Pérdida competitiva | 102 / 3 604 | 2,83 % |
| Presidencia, candidaturas | Pérdida lejana | 5 200 / 129 286 | 4,02 % |
| Diputaciones, candidaturas | Ganada sólida | 2 175 / 52 709 | 4,13 % |
| Diputaciones, candidaturas | Pérdida competitiva | 195 / 6 075 | 3,21 % |
| Diputaciones, candidaturas | Pérdida lejana | 5 754 / 142 806 | 4,03 % |
| Senadurías, candidaturas | Ganada sólida | 2 041 / 50 394 | 4,05 % |
| Senadurías, candidaturas | Pérdida competitiva | 249 / 7 106 | 3,50 % |
| Senadurías, candidaturas | Pérdida lejana | 7 143 / 176 028 | 4,06 % |
| Apoyo mínimo, partidos | Bastión | 919 / 24 417 | 3,76 % |
| Apoyo mínimo, partidos | Base fuerte | 3 876 / 98 812 | 3,92 % |
| Apoyo mínimo, partidos | Resto | 14 539 / 369 193 | 3,94 % |

**Concentración:** no se observa una clase con una tasa de falta claramente mayor en el agregado. En apoyo mínimo, Resto reúne 75,20 % de las faltas y 74,97 % de las observaciones, proporciones casi iguales. En Presidencia, pérdida lejana reúne 62,62 % de faltas y 61,12 % de observaciones. En Diputaciones y Senadurías la categoría `sin_clase` incluye candidaturas inactivas o filas sin resultado y concentra muchas observaciones, pero su proporción de faltas también es cercana a su tamaño. El CSV permite revisar variaciones por estado y candidatura; este resumen no establece equivalencia territorial de las claves entre 2020/2021 y 2024.
