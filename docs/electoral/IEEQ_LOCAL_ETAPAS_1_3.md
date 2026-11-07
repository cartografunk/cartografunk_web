# IEEQ Querétaro: diputaciones locales MR, etapas 1–3

El piloto usa únicamente **diputaciones locales de mayoría relativa** de 2018, 2021 y 2024. La unidad de salida electoral es la **sección de cada año**. El estado es sólo filtro de muestra; estos datos no se han incorporado a la app ni forman una serie territorial comparable entre años.

## 1. Adquisición y procedencia

Se descargaron los archivos del [histórico de resultados del IEEQ](https://ieeq.mx/elecciones/historico) y del [visor de resultados de 2024](https://ieeq.mx/contenido/elecciones/2023_2024/resultados/). `data/electoral/fuentes_ieeq/manifiesto_descargas.json` guarda URL, fecha UTC de descarga, bytes y SHA-256 de **20 archivos**. El constructor vuelve a comprobar todos los hashes antes de procesar. Los originales son locales y no se versionan.

| Año | Archivo usado | Detalle | SHA-256 del archivo principal |
| --- | --- | --- | --- |
| 2018 | `2018_tablas_resultados.zip`, miembros `2018_SEE_DIP_LOC_MR_QRO_CAS.xlsx`, `_SEC.xlsx` y `_DIS.xlsx` | Casilla, sección y distrito | `e64c98d54f5d6de42cc0e2cc95038a6a9c7106e5749bbad9cc53f0c7d594284e` |
| 2021 | `2021_diputaciones_mr.xlsx`, pestañas `Casilla`, `Sección`, `Distrito` | Casilla, sección y distrito | `34e19a6bfe11ed1e032496e4f4143c6e0b4f2f93fba77c928aac98cbee3b5ca9` |
| 2024 | `2024_resultados_qro.zip`, miembro `QRO_DIP_LOC_RESULTADOS_2024.csv`; `2024_json_dip_gral.json` y `2024_json_d1.json`…`d15.json` | CSV de casillas y JSON del visor con secciones/casillas de MR | `68afbe1b0214b0f5b1b2fa069a98c8d40a11f8185fbf0a87d668e05e99e88120` |

También se descargó `2018_casillas_diputaciones_locales.xlsx`, pero **no** se usa como tabla de votos: su primera hoja contiene metadatos de candidaturas ganadoras. El ZIP de tablas es la fuente reproducible del cómputo de 2018. El CSV de 2024 se lee en Latin-1; contiene 27 filas no electorales después de 3 214 registros, que se omiten mediante `ID_ESTADO=22`. El JSON del visor declara corte «15 junio 2024, 13:05», pero seis filas CSV tienen la anotación posterior `MODIFICADA ST-JRC-216/2024 Y ACUMULADOS`. La fecha y versión jurídica exactas de ese conjunto siguen **NO VERIFICADAS**.

## 2. Normalización de casillas

Ejecutar `D:\Conda\envs\cartografunk\python.exe -B scripts/build_ieeq_dip_local.py`. Cada Parquet `data/electoral/ieeq_local/dip_local_mr_AAAA_casilla.parquet` conserva las columnas originales y añade `ANIO`, `FILA_FUENTE`, `SECCION_NORMALIZADA`, `ID_SECCION`, tipo, estatus de recuento documentado, anulación y motivo de exclusión. B, C y E válidas entran al perfil de sección; las S quedan aparte. El voto anticipado A de 2024 queda aparte porque la sección de instalación no demuestra residencia. Los votos de siete casillas anuladas por tribunal en 2018 (2 437) se excluyen; su lista nominal sigue contando en la sección.

En 2018 se etiquetan 827 filas como `Grupo de recuento`. En 2021 el archivo consigna `Acta casilla` para todas las filas, lo que **no demuestra ausencia de recuentos**. En 2024 el CSV no ofrece una columna equivalente de estatus. Las etiquetas B/C/E/S/A no enlazan casillas ni territorios entre años.

El CSV 2024 identifica la casilla C03, distrito local 10, 433 votos, como sección **0861**. `JSON_D10.json` del mismo portal la ubica en **0584**; `JSON_D3.json` no la incluye en 0861. La fila original conserva `SECCION=861`; `SECCION_NORMALIZADA=584` y `CORRECCION_SECCION` documentan el ajuste. Sin él, aparecen diferencias de +433 y −433 entre CSV y visor.

Las casillas especiales son un indicador de **voto fuera de la sección de residencia**, según el [material del IEEQ para 2024](https://ieeq.mx/contenido/convocatorias/archivos/AnxCG2812231000O-23.pdf). El derecho a votar MR o RP depende del domicilio y la ubicación de la casilla. Los archivos no dicen la sección de residencia de cada votante: no permiten medir migración, origen ni flujo entre secciones. `dip_local_mr_AAAA_especial_mr.parquet` conserva la sección **de instalación** y los votos MR por casilla S; en 2024 los 57 registros MR se toman del JSON, porque el CSV incluye además 57 registros S de RP con las mismas claves de casilla.

## 3. Agregación y cotejo

`dip_local_mr_AAAA_seccion_bce.parquet` suma partidos, combinaciones y votos B+C+E válidos por `ID_SECCION` **dentro del año**. La lista nominal suma todas las B+C+E, incluso las anuladas. `dip_local_mr_AAAA_cotejo_seccion.csv` muestra sección a sección el total publicado, el residencial B+C+E, los votos S en el lugar de instalación y cualquier diferencia sin explicar. `auditoria_etapas_1_3.json` guarda los totales reproducibles.

| Año | Secciones B+C+E | Votos B+C+E | Votos MR en S | Votos publicados | Cotejo |
| --- | ---: | ---: | ---: | ---: | --- |
| 2018 | 860 | 991 433 | 2 780 en 44 S | 994 213 en tabla seccional | El total y todas las columnas de votos y lista nominal cuadran al sumar S y excluir 7 anuladas. |
| 2021 | 891 | 894 003 | 4 221 en 23 S | 898 224 en tabla seccional | El total y todas las columnas de votos y lista nominal cuadran al sumar S. |
| 2024 | 953 | 1 165 996 | 6 785 en 57 S MR | 1 172 859 en portada del visor | Cuadra B+C+E + 78 de voto anticipado + S MR. El CSV tiene además 5 288 votos S RP, que no se suman a MR. |

La tabla seccional del visor 2024 suma **1 166 048**, 52 más que B+C+E: incluye dos S MR de la sección de instalación `22-0727`. Las otras S MR no se asignan a las secciones publicadas del mismo modo. Por eso se usa B+C+E para el perfil residencial, y S se conserva aparte. Tras la corrección 0584/0861, no quedan diferencias seccionales sin explicar en los tres años.

**NO VERIFICADO / puerta de la etapa 3:** la tabla distrital 2018 suma **994 214**, un voto válido más que la suma de sus tablas seccionales/casillas válidas (**994 213**); ocurre en el distrito local 1. No se corrigió artificialmente. La versión jurídica exacta de 2024 y su concordancia con resoluciones posteriores también requieren cotejo documental antes de declarar los tres cortes plenamente definitivos para ML. Esto no bloquea el diagnóstico descriptivo por sección dentro de cada año. La correspondencia territorial 2018–2021–2024 y el cruce ECEG pertenecen a la etapa 4; **NO VERIFICADOS** aquí.

Pruebas: `D:\Conda\envs\cartografunk\python.exe -B -m pytest electoral/tests/test_ieeq_local.py -q` comprueba la anulación, la lista nominal, la corrección con fuente y el cotejo integral local.
