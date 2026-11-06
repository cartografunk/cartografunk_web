# Archivos de data/electoral

## CPV 2020 por sección: ECEG INEGI-INE (integración 2026-11-06)

Fuente oficial: [Estadísticas Censales a Escalas Geoelectorales 2020, INEGI](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/geoelectorales/eceg_2020_csv.zip), miembro `conjunto_de_datos/INE_SECCION_2020.csv`; definiciones en `diccionario_de_datos/Descriptor_indicadores_ECEG_Seccion_2020.csv.csv` dentro del mismo ZIP. El [INE](https://central-estatico.ine.mx/2021/08/18/presentan-ine-e-inegi-la-herramienta-estadisticas-censales-a-escalas-geoelectorales-2020/) describe los indicadores a nivel de sección. Se construye con `D:\Conda\envs\cartografunk\python.exe -B scripts/build_eceg_2020.py` y se guarda localmente en `data/electoral/cpv_2020_seccion.parquet` (no versionado). Contiene 68 806 secciones únicas y 15 porcentajes; `ID_SECCION` se forma con entidad de dos dígitos, guion y sección de cuatro (`01-0338`). La unión es exacta por esa llave, sin imputación municipal. Valores no numéricos, denominadores cero y porcentajes fuera de 0–100 se dejan nulos.

| Variable | Numerador / denominador ECEG | Lectura |
| --- | --- | --- |
| `pct_mujeres` | `POBFEM / POBTOT` | Mujeres en la población |
| `pct_menores_18` | `P_0A17 / POBTOT` | Menores de 18 años |
| `pct_60_mas` | `P_60YMAS / POBTOT` | Personas de 60 años o más |
| `pct_18_24` | `P_18A24 / POBTOT` | Personas de 18 a 24 años |
| `pct_lengua_indigena` | `P3YM_HLI / P_3YMAS` | Personas de 3+ que hablan lengua indígena |
| `pct_afromexicana` | `POB_AFRO / POBTOT` | Personas que se consideran afromexicanas |
| `pct_analfabeta` | `P15YM_AN / P_15YMAS` | Personas de 15+ analfabetas |
| `pct_posbasica` | `P18YM_PB / P_18YMAS` | Personas de 18+ con educación posbásica |
| `pct_pea` | `PEA / P_12YMAS` | Personas de 12+ económicamente activas |
| `pct_sin_salud` | `PSINDER / POBTOT` | Personas sin afiliación a servicios de salud |
| `pct_piso_tierra` | `VPH_PISOTI / VIVPAR_HAB` | Viviendas habitadas con piso de tierra |
| `pct_sin_agua` | `VPH_AGUAFV / VIVPAR_HAB` | Viviendas habitadas sin agua entubada en su ámbito |
| `pct_sin_drenaje` | `VPH_NODREN / VIVPAR_HAB` | Viviendas habitadas sin drenaje |
| `pct_internet` | `VPH_INTER / VIVPAR_HAB` | Viviendas habitadas con Internet |
| `pct_automovil` | `VPH_AUTOM / VIVPAR_HAB` | Viviendas habitadas con automóvil o camioneta |

La cobertura por llave exacta frente a 2024 es:

| Elección | Secciones cruzadas / total | Cobertura secciones | Lista nominal cruzada / total | Cobertura lista nominal |
| --- | ---: | ---: | ---: | ---: |
| Presidencia | 67 736 / 70 536 | 96,030 % | 93 054 427 / 98 468 994 | 94,501 % |
| Diputaciones MR | 67 736 / 70 504 | 96,074 % | 93 027 586 / 98 214 289 | 94,719 % |
| Senadurías MR | 67 736 / 70 536 | 96,030 % | 93 027 586 / 98 438 250 | 94,503 % |

Estos porcentajes miden coincidencia de **claves**, no equivalencia espacial entre la cartografía ECEG 2020/2021 y la electoral 2024. La lista nominal es la columna local de cada Parquet 2024. La fecha de corte documental de esa columna sigue NO VERIFICADA. El archivo `data/electoral/cpv_2020_cobertura.json` reproduce el conteo local; no se versiona.

La auditoría del [histórico oficial de secciones](CPV_SIN_CRUCE.md#origen-registrado-en-el-histórico-del-ine) identifica los primeros movimientos 2021–2023 de las 2 768 claves territoriales de 2024 sin CPV. Para 188 claves coincidentes, el número `MUNICIPIO` del ECEG difiere de `ID_MUNICIPIO` en el Parquet de Presidencia; no se interpreta como cambio territorial, porque el descriptor ECEG define su municipio conforme al Marco Geoestadístico y el Parquet electoral usa la clave INE. Para 13 105 claves coincidentes difiere el distrito federal, compatible con la nueva distritación, sin demostrar cambio de límites seccionales.

Inventario leído el 2026-11-03 con pyarrow.parquet.ParquetFile, sin cargar geometría para obtener el esquema. Los tipos de la tabla son tipos Arrow del Parquet; geometry es WKB binario en el GeoParquet.

Fuentes de las métricas: `C:\Users\HeyCe\AppData\Local\Temp\electoral_reporte_cola6.md` (lectura de los Parquet), `C:\Users\HeyCe\AppData\Local\Temp\cartografunk_ine_geometry_quality.json` (cruce MGE/resultados), `C:\Users\HeyCe\AppData\Local\Temp\cartografunk_ine_crs.json` (pruebas de CRS), `C:\Users\HeyCe\AppData\Local\Temp\cola3_reporte.md` (comparaciones SEC/DISPP).

## presidencia_2024_seccion.parquet

- Ruta: `C:\cartografunk_web\data\electoral\presidencia_2024_seccion.parquet`.
- Filas: 70536; columnas: 38; tamaño: 2773752 bytes; modificación local: 2026-11-02T16:09:41.
- Llave: ID_SECCION; construido de ID_ESTADO(2) + SECCION(4); único en el Parquet.
- Origen ZIP: `D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\PRESIDENCIA_2024.zip`.
- Miembros de origen: `PRESIDENCIA_2024/CSV/2024_SEE_PRE_NAL_SEC.csv`; `PRESIDENCIA_2024/CSV/2024_SEE_PRE_NAL_CAS.csv`.

| Columna | dtype Arrow |
| --- | --- |
| `CIRCUNSCRIPCION` | `int64` |
| `ID_ESTADO` | `int64` |
| `NOMBRE_ESTADO` | `string` |
| `ID_DISTRITO_FEDERAL` | `int64` |
| `CABECERA_DISTRITAL_FEDERAL` | `string` |
| `ID_MUNICIPIO` | `int64` |
| `MUNICIPIO` | `string` |
| `SECCION` | `int64` |
| `CASILLAS` | `double` |
| `ACTAS_CASILLA-MEC` | `int64` |
| `PAN` | `int64` |
| `PRI` | `int64` |
| `PRD` | `int64` |
| `PVEM` | `int64` |
| `PT` | `int64` |
| `MC` | `int64` |
| `MORENA` | `int64` |
| `PAN_PRI_PRD` | `int64` |
| `PAN_PRI` | `int64` |
| `PAN_PRD` | `int64` |
| `PRI_PRD` | `int64` |
| `PVEM_PT_MORENA` | `int64` |
| `PVEM_PT` | `int64` |
| `PVEM_MORENA` | `int64` |
| `PT_MORENA` | `int64` |
| `NUM_VOTOS_VALIDOS` | `int64` |
| `NUM_VOTOS_CAN_NREG` | `int64` |
| `NUM_VOTOS_NULOS` | `int64` |
| `TOTAL_VOTOS` | `int64` |
| `LISTA_NOMINAL` | `int64` |
| `ID_SECCION` | `string` |
| `estado` | `string` |
| `cand_PAN_PRI_PRD` | `int64` |
| `cand_PVEM_PT_MORENA` | `int64` |
| `cand_MC` | `int64` |
| `votos_casillas_s` | `int64` |
| `n_casillas_s` | `int64` |
| `votos_en_lista` | `double` |

## diputaciones_2024_seccion.parquet

- Ruta: `C:\cartografunk_web\data\electoral\diputaciones_2024_seccion.parquet`.
- Filas: 70504; columnas: 49; tamaño: 2193050 bytes; modificación local: 2026-11-03T15:15:07.
- Llave: ID_SECCION; construido de ID_ESTADO(2) + SECCION(4); único en el Parquet.
- Origen ZIP: `D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\DIPUTACIONES_FED_MR_2024.zip`.
- Miembros de origen: `DIPUTACIONES_FED_MR_2024/CSV/2024_SEE_DIP_FED_MR_NAL_SEC.csv`; `DIPUTACIONES_FED_MR_2024/CSV/2024_SEE_DIP_FED_MR_NAL_DISCAND.csv`; `DIPUTACIONES_FED_MR_2024/CSV/2024_SEE_DIP_FED_MR_NAL_CAS.csv`.

| Columna | dtype Arrow |
| --- | --- |
| `CIRCUNSCRIPCION` | `int64` |
| `ID_ESTADO` | `int64` |
| `NOMBRE_ESTADO` | `string` |
| `ID_DISTRITO_FEDERAL` | `int64` |
| `CABECERA_DISTRITAL_FEDERAL` | `string` |
| `ID_MUNICIPIO` | `int64` |
| `MUNICIPIO` | `string` |
| `SECCION` | `int64` |
| `CASILLAS` | `int64` |
| `ACTAS_CASILLA-MEC` | `int64` |
| `PAN` | `double` |
| `PRI` | `double` |
| `PRD` | `double` |
| `PVEM` | `double` |
| `PT` | `double` |
| `MC` | `double` |
| `MORENA` | `double` |
| `PAN_PRI_PRD` | `double` |
| `PAN_PRI` | `double` |
| `PAN_PRD` | `double` |
| `PRI_PRD` | `double` |
| `PVEM_PT_MORENA` | `double` |
| `PVEM_PT` | `double` |
| `PVEM_MORENA` | `double` |
| `PT_MORENA` | `double` |
| `CAND_IND1` | `double` |
| `CAND_IND2` | `double` |
| `NUM_VOTOS_VALIDOS` | `double` |
| `NUM_VOTOS_CAN_NREG` | `double` |
| `NUM_VOTOS_NULOS` | `double` |
| `TOTAL_VOTOS` | `double` |
| `LISTA_NOMINAL` | `int64` |
| `ID_SECCION` | `string` |
| `estado` | `string` |
| `cand_PAN` | `double` |
| `cand_PRI` | `double` |
| `cand_PRD` | `double` |
| `cand_PVEM` | `double` |
| `cand_PT` | `double` |
| `cand_MC` | `double` |
| `cand_MORENA` | `double` |
| `cand_PAN_PRI_PRD` | `double` |
| `cand_PVEM_PT_MORENA` | `double` |
| `cand_CAND_IND1` | `double` |
| `cand_CAND_IND2` | `double` |
| `discrepancia_sec_dispp` | `bool` |
| `votos_casillas_s` | `int64` |
| `n_casillas_s` | `int64` |
| `votos_en_lista` | `double` |

## senadurias_2024_seccion.parquet

- Ruta: `C:\cartografunk_web\data\electoral\senadurias_2024_seccion.parquet`.
- Filas: 70536; columnas: 44; tamaño: 2200356 bytes; modificación local: 2026-11-03T15:15:18.
- Llave: ID_SECCION; construido de ID_ESTADO(2) + SECCION(4); único en el Parquet.
- Origen ZIP: `D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\SENADURÍAS_MR_2024.zip`.
- Miembros de origen: `SENADURÍAS_MR_2024/CSV/2024_SEE_SEN_FED_MR_NAL_SEC.csv`; `SENADURÍAS_MR_2024/CSV/2024_SEE_SEN_FED_MR_NAL_DISCAND.csv`; `SENADURÍAS_MR_2024/CSV/2024_SEE_SEN_FED_MR_NAL_CAS.csv`.

| Columna | dtype Arrow |
| --- | --- |
| `CIRCUNSCRIPCION` | `int64` |
| `ID_ESTADO` | `int64` |
| `NOMBRE_ESTADO` | `string` |
| `ID_DISTRITO_FEDERAL` | `int64` |
| `CABECERA_DISTRITAL_FEDERAL` | `string` |
| `ID_MUNICIPIO` | `int64` |
| `MUNICIPIO` | `string` |
| `SECCION` | `int64` |
| `CASILLAS` | `double` |
| `ACTAS_CASILLA-MEC` | `int64` |
| `PAN` | `double` |
| `PRI` | `double` |
| `PRD` | `double` |
| `PVEM` | `double` |
| `PT` | `double` |
| `MC` | `double` |
| `MORENA` | `double` |
| `PAN_PRI_PRD` | `double` |
| `PAN_PRI` | `double` |
| `PAN_PRD` | `double` |
| `PRI_PRD` | `double` |
| `PVEM_PT_MORENA` | `double` |
| `PVEM_PT` | `double` |
| `PVEM_MORENA` | `double` |
| `PT_MORENA` | `double` |
| `NUM_VOTOS_VALIDOS` | `double` |
| `NUM_VOTOS_CAN_NREG` | `double` |
| `NUM_VOTOS_NULOS` | `double` |
| `TOTAL_VOTOS` | `double` |
| `LISTA_NOMINAL` | `int64` |
| `ID_SECCION` | `string` |
| `estado` | `string` |
| `cand_PAN` | `double` |
| `cand_PRI` | `double` |
| `cand_PRD` | `double` |
| `cand_PVEM` | `double` |
| `cand_PT` | `double` |
| `cand_MC` | `double` |
| `cand_MORENA` | `double` |
| `cand_PAN_PRI_PRD` | `double` |
| `cand_PVEM_PT_MORENA` | `double` |
| `votos_casillas_s` | `int64` |
| `n_casillas_s` | `int64` |
| `votos_en_lista` | `double` |

## presidencia_2024_casilla.parquet

- Ruta: `C:\cartografunk_web\data\electoral\presidencia_2024_casilla.parquet`.
- Filas: 170766; columnas: 44; tamaño: 8851713 bytes; modificación local: 2026-11-03T15:39:09.
- Llave: ID_CASILLA_LEGIBLE; incluye ID_SECCION, TIPO_CASILLA, ID_CASILLA, EXT_CONTIGUA y ACTA_CASILLA-MEC; único en el Parquet.
- Origen ZIP: `D:\(5) WORK\CONJUNTOS DE DATOS\INE_SICEE\FEDERALES_2024\PRESIDENCIA_2024.zip`.
- Miembros de origen: `PRESIDENCIA_2024/CSV/2024_SEE_PRE_NAL_CAS.csv`.

| Columna | dtype Arrow |
| --- | --- |
| `CIRCUNSCRIPCION` | `int64` |
| `ID_ESTADO` | `int64` |
| `NOMBRE_ESTADO` | `string` |
| `ID_DISTRITO_FEDERAL` | `int64` |
| `CABECERA_DISTRITAL_FEDERAL` | `string` |
| `ID_MUNICIPIO` | `int64` |
| `MUNICIPIO` | `string` |
| `SECCION` | `int64` |
| `TIPO_CASILLA` | `string` |
| `ID_CASILLA` | `int64` |
| `EXT_CONTIGUA` | `int64` |
| `ACTA_CASILLA-MEC` | `string` |
| `URNA_ELECTRONICA` | `int64` |
| `PAN` | `int64` |
| `PRI` | `int64` |
| `PRD` | `int64` |
| `PVEM` | `int64` |
| `PT` | `int64` |
| `MC` | `int64` |
| `MORENA` | `int64` |
| `PAN_PRI_PRD` | `int64` |
| `PAN_PRI` | `int64` |
| `PAN_PRD` | `int64` |
| `PRI_PRD` | `int64` |
| `PVEM_PT_MORENA` | `int64` |
| `PVEM_PT` | `int64` |
| `PVEM_MORENA` | `int64` |
| `PT_MORENA` | `int64` |
| `NUM_VOTOS_VALIDOS` | `int64` |
| `NUM_VOTOS_CAN_NREG` | `int64` |
| `NUM_VOTOS_NULOS` | `int64` |
| `TOTAL_VOTOS` | `int64` |
| `LISTA_NOMINAL` | `int64` |
| `ESTATUS_ACTA` | `string` |
| `TRIBUNAL` | `double` |
| `RUTA_ACTA` | `string` |
| `OBSERVACIONES` | `string` |
| `ID_SECCION` | `string` |
| `ID_CASILLA_LEGIBLE` | `string` |
| `estado` | `string` |
| `cand_PAN_PRI_PRD` | `int64` |
| `cand_PVEM_PT_MORENA` | `int64` |
| `cand_MC` | `int64` |
| `votos_en_lista` | `double` |

## secciones_2024_geom.parquet

- Ruta: `C:\cartografunk_web\data\electoral\secciones_2024_geom.parquet`.
- Filas: 70753; columnas: 7; tamaño: 45781861 bytes; modificación local: 2026-11-02T16:20:45.
- Llave: ID_SECCION; construido de ENTIDAD(2) + SECCION(4); único en el GeoParquet.
- Origen ZIP: `D:\(5) WORK\CONJUNTOS DE DATOS\INE MGE\MGE 2024-20240515T221823Z-001.zip`.
- Miembros de origen: `MGE 2024/SECCIONES_2024.gpkg; capa SECCIONES_2024`.

- Metadatos GeoParquet: geometry WKB; CRS {'authority': 'EPSG', 'code': 4326}; bounds [-118.3651143522829, 14.533081346032763, -86.71250889096409, 32.722021240808644]. El código usa EPSG:32614 como hipótesis al interpretar el GPKG, simplifica a 25 m y escribe EPSG:4326. Fuentes: `electoral/geometria.py`, `C:\Users\HeyCe\AppData\Local\Temp\cartografunk_ine_crs.json`.

| Columna | dtype Arrow |
| --- | --- |
| `ID_SECCION` | `string` |
| `ENTIDAD` | `int64` |
| `DISTRITO` | `int64` |
| `DISTRITO_L` | `int64` |
| `MUNICIPIO` | `int64` |
| `TIPO` | `int64` |
| `geometry` | `binary` |

## Calidad y cruces

| Archivo | Medición | Fuente |
| --- | --- | --- |
| presidencia_2024_seccion.parquet | estado: 70 448 con_resultado, 56 sin_resultado, 32 extranjero; votos_sobre_lista antes/después de votos_en_lista: 728/19 entre con_resultado. | `C:\Users\HeyCe\AppData\Local\Temp\electoral_reporte_cola6.md` |
| diputaciones_2024_seccion.parquet | estado: 70 417 con_resultado, 87 sin_resultado, 0 extranjero; votos_sobre_lista antes/después: 123/123. | `C:\Users\HeyCe\AppData\Local\Temp\electoral_reporte_cola6.md` |
| senadurias_2024_seccion.parquet | estado: 70 391 con_resultado, 113 sin_resultado, 32 extranjero; votos_sobre_lista antes/después: 339/339. | `C:\Users\HeyCe\AppData\Local\Temp\electoral_reporte_cola6.md` |
| presidencia_2024_casilla.parquet | estado: 170 356 con_resultado, 259 sin_resultado, 151 extranjero; ID_CASILLA_LEGIBLE único. | `C:\Users\HeyCe\AppData\Local\Temp\electoral_reporte_cola6.md` |
| secciones_2024_geom.parquet | 70 753 polígonos; 249 sin fila de resultados de Presidencia; 32 filas de Presidencia sin polígono. | `C:\Users\HeyCe\AppData\Local\Temp\cartografunk_ine_geometry_quality.json` |

El reporte de geometría consigna que el GPKG declara EPSG:4326; `electoral/geometria.py` aplica `set_crs(32614, allow_override=True)`. En `C:\Users\HeyCe\AppData\Local\Temp\cartografunk_ine_crs.json`, EPSG:32614 ubicó 70 643 de 70 753 centroides dentro del polígono de su entidad. Esa medición no confirma el CRS de origen.

En `C:\Users\HeyCe\AppData\Local\Temp\cola3_reporte.md` constan 9 distritos de Diputaciones con diferencias SEC/DISPP (19 comparaciones, máximo absoluto 176 votos) y 0 en Senadurías. El mismo reporte documenta que la configuración de coaliciones de Senadurías fue constante dentro de 32 estados examinados.

NO VERIFICADO: fecha de corte de lista nominal y confirmación documental del CRS original en los archivos/reporte aquí citados.

