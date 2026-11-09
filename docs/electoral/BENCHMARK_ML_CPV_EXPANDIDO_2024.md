# Corrida exploratoria de ML con CPV ampliado

**Fecha:** 9-nov-2026. Reproducir con `D:\Conda\envs\cartografunk\python.exe -B -m scripts.benchmark_ieeq_ml_cpv_expandido`. Las salidas locales, sin versionar, son `data/electoral/ieeq_local/benchmark_ml_cpv_expandido_2024.json` y `benchmark_ml_cpv_expandido_2024_seccion.parquet`. La app de presentación incluye sólo el JSON resumido del piloto.

Se entrenó el mismo árbol por partido con 654 secciones de 2018→2021 y se midió en las mismas **788 de 953 secciones** comparables de 2024 (**73.66 % de lista nominal**). Se probaron 15 tasas existentes, 27 tasas al añadir doce candidatas auditadas y 247 entradas: las 27 tasas más 220 campos censales no geográficos del ECEG. Los campos crudos incluyen conteos y duplicaciones; esta tercera corrida prueba amplitud de datos, no un conjunto de variables seleccionado.

| Modelo | Entradas CPV | Error medio de cuota de los siete partidos | Error medio de margen | Liderazgos MORENA detectados / observados |
| --- | ---: | ---: | ---: | ---: |
| Ridge sin CPV, referencia anterior | 0 | 5.37 pp | 11.28 pp | 89 / 436 |
| Árbol CPV inicial | 15 | 5.89 pp | 12.71 pp | 75 / 436 |
| Árbol CPV ampliado | 27 | 5.97 pp | 12.94 pp | 71 / 436 |
| Árbol con todos los campos | 247 | 5.86 pp | 12.54 pp | 81 / 436 |

**Por partido, error medio de cuota (pp):**

| Partido | Ridge sin CPV | 15 tasas | 27 tasas | 247 campos |
| --- | ---: | ---: | ---: | ---: |
| PAN | 10.97 | 12.04 | 12.13 | 11.68 |
| PRI | 6.80 | 7.07 | 7.04 | 6.91 |
| PRD | 0.86 | 0.94 | 0.93 | 0.92 |
| MC | 4.31 | 4.48 | 4.47 | 4.47 |
| PVEM | 3.95 | 4.12 | 4.33 | 4.33 |
| MORENA | 8.06 | 9.74 | 10.05 | 9.95 |
| PT | 2.66 | 2.85 | 2.86 | 2.78 |

**Lectura medida:** añadir las doce tasas no mejoró el error macro. Usar los 247 campos bajó el error del árbol inicial sólo 0.03 pp, pero quedó 0.49 pp por encima de Ridge sin CPV. Para MORENA, el árbol de 247 campos detectó 81 de 436 liderazgos observados, frente a 75 del árbol inicial y 89 de Ridge. Más columnas no resolvieron la pregunta «dónde ganarás».

**NO VERIFICADO:** utilidad prospectiva para 2027, repetición en otros estados, estabilidad con otro corte electoral, efecto causal de cualquier rasgo censal y equivalencia del perfil seccional con el área de una casilla extraordinaria. El reparto de coaliciones continúa siendo una atribución fraccionaria analítica. El resultado describe cuotas partidarias atribuidas, no la victoria legal de una candidatura.
