# Archivos de data/electoral

## Resultados locales IEEQ 2018, 2021 y 2024

Los archivos originales de diputaciones locales MR de Querétaro se guardan en `data/electoral/fuentes_ieeq/` con un manifiesto de URLs, fechas UTC y SHA-256. `scripts/build_ieeq_dip_local.py` produce Parquet de casillas, secciones B+C+E y casillas especiales MR en `data/electoral/ieeq_local/`. Sólo se versionan los tres Parquet pequeños de especiales MR y el de domicilios del encarte 2024; los demás quedan locales. Las definiciones, exclusiones, fuentes y cifras del cotejo están en [IEEQ_LOCAL_ETAPAS_1_3.md](IEEQ_LOCAL_ETAPAS_1_3.md). La pestaña «Piloto local IEEQ» de la app lee estas tablas cuando existen y muestra una sección por vez. El cruce geométrico se describe en [IEEQ_LOCAL_ETAPAS_4_7.md](IEEQ_LOCAL_ETAPAS_4_7.md); no se trata como serie comparable para ML.

### Casillas especiales y encarte de ubicación

El producto a consultar para domicilios se llama **Listado de Ubicación e Integración de Mesas Directivas de Casilla (Encarte)**. El [encarte IEEQ de Querétaro 2024, generado el 30-may-2024](https://ieeq.mx/contenido/difusion/2024/Encarte_30052024.pdf), publica sección, tipo/número de casilla y ubicación. El PDF fuente se conserva local con SHA-256 `2bbe1fe5272b4641380b85ac314df05f7c5c59cbd64af57b5112e5b5c13e7645` y no se versiona porque incluye nombres de funcionarios. Antes de extraer, se convirtió con [`pdf_to_md.py`](../../scripts/pdf_to_md.py) y `--preserve-stream-order` porque el encarte tiene columnas. [`extract_ieeq_especiales_encarte_2024.py`](../../scripts/extract_ieeq_especiales_encarte_2024.py) lee ese Markdown y extrae sólo los domicilios S, página y URL de fuente. Sus **57 claves sección+número S** coinciden una a una con los **57 registros MR** del Parquet electoral 2024. El resultado versionado `dip_local_mr_2024_especial_ubicacion.parquet` no contiene nombres ni coordenadas.

También existe un [encarte IEEQ 2018 por distrito federal](https://ieeq.mx/contenido/elecciones/2017_2018/contenido/mesas-directivas/archivos/ENCARTE_03.pdf). **NO VERIFICADO:** un juego completo de encartes 2018 y el encarte oficial de Querétaro 2021, ni los cambios de domicilio posteriores a cada PDF. Los Parquet `dip_local_mr_AAAA_especial_mr.parquet` contienen votos MR y **sección de instalación**, no sección de residencia. Los domicilios 2024 son una entrada para geocodificación futura: hasta validar cada punto contra el domicilio y el polígono de su año, la cobertura de coordenadas verificadas es **0/57**. Un punto de instalación no revela el origen del voto foráneo.

## Ruta alternativa: CPV urbano por manzana, colonia y sección

La búsqueda posterior del Catálogo de Colonias con claves seccionales, sus cortes 2022/2026 y la auditoría que impide unirlo directamente al polígono local se documentan en [CCOL_COLONIAS.md](CCOL_COLONIAS.md). El [catálogo EDMSLM](EDMSLM_CATALOGO.md) aportado por el usuario vincula localidad y manzana electoral con sección de su corte; la prueba de Viñedos demuestra que sus secciones no se pueden asignar directamente al encarte 2024.

El archivo local `H:\Mi unidad\(0) CARTOGRAFUNK BASICS\(4) DATA\00 Marco Geoestadístico\00m.parquet` contiene **geometría de manzanas**, no indicadores CPV. El archivo `H:\Mi unidad\(0) CARTOGRAFUNK BASICS\(4) DATA\11 Colonias INE\ColoniasINE2020a.parquet` contiene polígonos de colonias, sin clave de sección ni indicadores CPV. Los conteos vienen del [CPV 2020 por AGEB y manzana urbana de INEGI](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_01_cpv2020_csv.zip). En el CSV se excluyen filas agregadas `MZA=000` antes de formar la llave de 16 dígitos `ENTIDAD+MUN+LOC+AGEB+MZA` y cruzarla con `CVEGEO` de `00m`.

`scripts/build_cpv_colonia_seccion.py --entidad 01 --zip RUTA.zip` asigna el punto interior de cada manzana a una colonia y una sección 2024. La ruta del ZIP puede omitirse cuando se llama `data/electoral/ageb_mza_urbana_XX_cpv2020_csv.zip`, sustituyendo `XX` por la entidad. Las manzanas con varios polígonos candidatos quedan sin asignar; así cada manzana usada aporta sus conteos una sola vez. Las tasas son cocientes de **sumas de conteos**, nunca promedios de porcentajes. Si un conteo de una tasa está suprimido o falta, la tasa agregada queda nula. Para `pct_menores_18`, el numerador se deriva como `POBTOT - P_18YMAS`; las otras 14 variables siguen las definiciones de la tabla ECEG abajo. Las salidas locales no versionadas por entidad son `cpv_2020_colonia_seccion_XX.parquet`, `cpv_2020_manzana_seccion_XX.parquet` y `cpv_2020_colonia_seccion_XX_cobertura.json`. El primero conserva los **fragmentos colonia–sección**; el segundo suma las mismas manzanas por sección. El identificador `ID_COLONIA_LOCAL` es la fila de la colonia dentro del archivo filtrado por entidad, no una clave oficial persistente. Para Jalisco el ZIP trae una bitácora adicional y el CSV censal usa codificación Latin-1; el lector contempla ambos casos.

**Medido en las 32 entidades:** 2 447 943 geometrías de manzana, 107 027 colonias y 1 611 448 filas censales de manzana urbana. 1 513 215 manzanas censales tienen asignación única a colonia y sección, repartidas en 125 614 pares colonia–sección. Son 96 168 269 de 100 340 409 personas con `POBTOT` numérico en los CSV de manzana urbana (**95,842 % de la población urbana numérica**). Los totales estatales del primer renglón de los 32 CSV suman 126 014 024 personas; la población urbana asignada equivale al **76,316 % de ese total nacional**, sin cubrir la parte rural. De 70 753 secciones de la geometría 2024, 51 109 reciben alguna manzana urbana con colonia. En 22 727 colonias, las manzanas censales asignadas caen en varias secciones; 29 288 manzanas geométricas tienen varias colonias candidatas y 1 680 varias secciones candidatas. La menor cobertura de población urbana numérica asignada es Tabasco (85,347 %), Puebla (89,392 %), Hidalgo (90,278 %) y Chiapas (90,344 %). Los archivos locales de cada entidad y el consolidado `cpv_2020_colonia_seccion_nacional.json` contienen los conteos para reproducir esta auditoría.

| Elección 2024 | Secciones con alguna manzana CPV urbana / total | Cobertura de secciones | Lista nominal en esas secciones / total | Cobertura de lista nominal |
| --- | ---: | ---: | ---: | ---: |
| Presidencia | 51 025 / 70 536 | 72,339 % | 81 352 555 / 98 468 994 | 82,617 % |
| Diputaciones MR | 51 025 / 70 504 | 72,372 % | 81 321 811 / 98 214 289 | 82,800 % |
| Senadurías MR | 51 025 / 70 536 | 72,339 % | 81 321 811 / 98 438 250 | 82,612 % |

Estos porcentajes de secciones y lista nominal sólo indican que **existe alguna manzana CPV urbana** en la sección; no indican que su CPV cubra a todos sus habitantes. No equivalen a los porcentajes del cruce ECEG por llave exacta de la tabla posterior.

**Medido en la entidad 01:** 22 940 geometrías de manzana, 1 135 colonias, 663 secciones 2024 y 15 843 filas censales de manzana urbana. 15 812 manzanas censales cruzaron `CVEGEO` con geometría; 15 683 recibieron colonia, 15 802 sección y 15 673 ambas. Las manzanas asignadas representan 1 192 078 de 1 198 709 personas con `POBTOT` numérico en el CSV urbano (99,447 % de esa población urbana). La salida contiene 1 441 pares colonia–sección, 243 colonias con población censal repartida entre varias secciones y 577 secciones con población de manzanas urbanas asignada. En la geometría completa hubo 27 manzanas con más de una colonia candidata y 2 con más de una sección candidata. Además, 717 de las 1 135 colonias **intersectan** más de una sección; por eso no se puede sumar colonias enteras para obtener secciones sin reasignar población.

**Limitación medida de las tasas:** la supresión de conteos por manzana deja muchas tasas agregadas nulas. Entre las 51 109 secciones con población urbana asignada, `pct_mujeres` está disponible en 26 407 y `pct_analfabeta` sólo en 1 966; la disponibilidad de las 15 tasas se registra en cada JSON local y en el consolidado. Esta ruta no sirve todavía para sustituir el perfil CPV oficial de la app.

**Cruce con las extraordinarias de Querétaro:** de 218 E en 119 secciones, sólo 102 E pertenecen a 34 secciones con alguna manzana urbana CPV asignada. En esas 102, la tasa `pct_60_mas` del agregado urbano por manzana está nula en todas y `pct_internet` sólo está disponible para una E; son tasas **de sección**, no de área E. En cambio, el ECEG oficial seccional con perímetro comparable aporta `pct_60_mas` a 167 E en 110 secciones. Tener las geometrías y el censo por manzana no basta para un perfil E propio: faltan la asignación territorial de cada E y, en muchas manzanas, conteos censales no suprimidos.

**NO VERIFICADO:** equivalencia espacial de los polígonos de colonias INE 2020 con las secciones electorales 2024; CRS original de la geometría seccional local (documentado abajo); validación independiente de los cruces de puntos próximos a límites; comparabilidad de este cálculo urbano con el ECEG seccional oficial. El CSV por manzana urbana omite población rural: 95,842 % **no es cobertura de población nacional ni de lista nominal**. Aunque la ruta corrió en las 32 entidades, su asignación espacial no está validada contra límites oficiales sección 2020/2024. El Parquet oficial ECEG seccional sigue siendo la fuente de la app hasta completar esa auditoría.

## CPV 2020 por sección: ECEG INEGI-INE (integración 2026-11-06)

### Diagnóstico local IEEQ 2024 por registro de casilla

`scripts/build_diagnostico_casillas.py` (`python -B -m scripts.build_diagnostico_casillas`) genera el archivo **local, no versionado** `data/electoral/ieeq_local/diagnostico_casillas_cpv_2024.parquet`. Parte de los registros IEEQ de diputaciones locales MR 2024 B/C/E marcados `INCLUIR_SECCION`, reparte cada marca de coalición en fracciones iguales entre sus partidos y une por `ID_SECCION` el ECEG 2020. Sólo conserva valores CPV en las secciones con geometría prácticamente igual (IoU ≥ 0.995) en el cruce ECEG 2021→2024. La unión nunca usa municipio o colonia. Los registros S de tránsito y A de voto anticipado quedan fuera. Las E reciben el perfil de toda la sección; su área específica de atención no está verificada.

**Medido en Querétaro:** 3 081 registros B/C/E de 953 secciones y 1 899 053 personas en lista nominal. Hay cruce CPV territorialmente comparable en 2 323 registros, 788 secciones y 1 398 846 personas de lista nominal (**73.66 %**). Los otros 758 registros están en 165 secciones modificadas o reconfiguradas; se conservan sus resultados de voto, pero se ocultan sus variables CPV. En dos registros comparables, la mayoría de tasas censales son nulas; Internet está disponible en 2 155 registros y automóvil en 2 259. Cada tasa se evalúa con sus datos no nulos.

El CSV IEEQ 2024 ponía `EXT_CONTIGUA=0` en todas las E: así, **117 filas parecían repetir 40 claves**, lo que se contó como «77 registros adicionales». El JSON del mismo visor contiene las **218 E** y su número de contigua. Un cruce uno a uno por distrito, sección, número E, votos totales, lista nominal y votos PAN/MORENA recuperó las etiquetas E1, E1C1, etc., para las 218 sin faltantes ni ambigüedad. El constructor conserva `EXT_CONTIGUA` original y añade `CONTIGUA_E_JSON` y `CASILLA_ETIQUETA`; esta última coincide con el encarte y es única entre todas las B/C/E de la sección y distrito. **No se borró ninguna fila ni cambió ningún voto**; el cotejo seccional y el total publicado siguen iguales. `FILA_FUENTE` permanece para rastrear la fila CSV.

El [encarte IEEQ 2024](https://ieeq.mx/contenido/difusion/2024/Encarte_30052024.pdf) —convertido antes a Markdown, SHA-256 `2bbe1fe5272b4641380b85ac314df05f7c5c59cbd64af57b5112e5b5c13e7645`— empata por `(ID_SECCION, CASILLA_ETIQUETA)` con los **3 081 registros B/C/E** del diagnóstico, incluidas las **218 E**. Aporta localidad y domicilio de **instalación**; el Parquet diagnóstico guarda `LOCALIDAD_INE_INSTALACION` y `LOCALIDAD_INSTALACION`. Las E están en 119 secciones y 141 combinaciones sección–localidad de instalación. El encarte no enumera en esas entradas las localidades o manzanas **de residencia asignadas** a cada extraordinaria. Por eso no se construye aún un CPV particular de E a partir del domicilio ni se equipara localidad de instalación con su área de atención. El [INE describe](https://centralelectoral.ine.mx/2023/08/10/celebra-ine-oaxaca-quinta-reunion-estatal-de-trabajo-de-cara-al-proceso-electoral-2024/) la conformación de E con manzanas/localidades y listas nominales separadas en sus sistemas de ubicación y cartografía; esa relación detallada de Querétaro 2024 es el insumo por localizar.

**Lista nominal por E ya resuelta:** las 218 extraordinarias tienen `LISTA_NOMINAL` en el CSV de diputaciones locales IEEQ 2024; suman **108 227 electores registrados**. Al cruzarlas por sección, E y contigua con el Parquet de casillas de Presidencia 2024 del [SICEE del INE](https://ine.mx/voto-y-elecciones/resultados-electorales/), las 218 empatan uno a uno y sus 218 listas nominales son iguales. Esa columna mide cuántos electores estaban registrados en cada mesa; **no es el CPV 2020** ni permite calcular por sí sola las 15 tasas sociodemográficas de esa mesa. Para un perfil CPV propio de la E sigue faltando la relación oficial de manzanas/localidades de residencia asignadas a su área de atención, además del cruce censal correspondiente.

El perfil compara 15 variables por clase de **casilla** para cada partido, pero cuenta una sección sólo una vez por clase porque B/C/E comparten CPV seccional. Para MORENA, las 758 filas sin CPV se distribuyen: 288 victorias sólidas, 267 derrotas lejanas, 123 victorias ajustadas, 78 derrotas competitivas y 2 empates. El porcentaje sin CPV por clase es 24.7 %, 29.2 %, 21.4 %, 18.6 % y 28.6 %, respectivamente: hay algo más de falta de CPV en derrotas lejanas que en las otras clases numerosas; **no se concentra exclusivamente en una clase**. La clase depende del margen del partido frente al mayor de otros seis partidos atribuidos, no del ganador oficial de la candidatura coaligada. Umbrales exploratorios: victoria sólida ≥10 pp, derrota competitiva hasta 10 pp de desventaja; las victorias ajustadas y empates se muestran en la tabla, pero no en el contraste principal de tres clases. El reparto fraccionario es una atribución analítica; no sustituye el cómputo legal.

La segunda capa muestra votos para liderar entre partidos, abstención no negativa, apoyo mínimo del **mismo partido en tres boletas federales 2024 de la sección** cuando existe el Parquet local `fidelidad_estado.parquet`, y costo por voto adicional ingresado por el usuario. Son dimensiones separadas. En un registro con `TOTAL_VOTOS > LISTA_NOMINAL` la abstención se deja nula y la acción pasa a revisión; otro registro no tiene votos válidos. `COSTO_HIPOTETICO = VOTOS_PARA_LIDERAR × COSTO_SUPUESTO_POR_VOTO` no estima gasto real, votos captables ni retorno. Las acciones sugeridas por clase son hipótesis para probar. **Asociación, no causa; CPV 2020 vs votos 2024.**

Fuente oficial: [Estadísticas Censales a Escalas Geoelectorales 2020, INEGI](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/geoelectorales/eceg_2020_csv.zip), miembro `conjunto_de_datos/INE_SECCION_2020.csv`; definiciones en `diccionario_de_datos/Descriptor_indicadores_ECEG_Seccion_2020.csv.csv` dentro del mismo ZIP. El [INE](https://central-estatico.ine.mx/2021/08/18/presentan-ine-e-inegi-la-herramienta-estadisticas-censales-a-escalas-geoelectorales-2020/) describe los indicadores a nivel de sección. Se construye con `D:\Conda\envs\cartografunk\python.exe -B scripts/build_eceg_2020.py` y se guarda localmente en `data/electoral/cpv_2020_seccion.parquet` (no versionado). Contiene 68 806 secciones únicas y 15 porcentajes; `ID_SECCION` se forma con entidad de dos dígitos, guion y sección de cuatro (`01-0338`). La unión es exacta por esa llave, sin imputación municipal. Valores no numéricos, denominadores cero y porcentajes fuera de 0–100 se dejan nulos.

### Tablas completas de entidad, distrito y sección

El ZIP `C:\Users\HeyCe\Downloads\eceg_2020_csv.zip` tiene el mismo SHA-256 (`db357fee6f869ec10c7c996e72d4ab6a339d10b20b8043f63ab5a256339708fe`) que el ZIP local ya descargado. `scripts/build_eceg_completo.py` convierte los tres CSV originales a Parquet tipado y crea tablas materializadas e índices únicos en `data/electoral/eceg_2020.duckdb`. Conserva los indicadores originales; quita el espacio final de `NOM_ENT ` y añade llaves nacionales. Los Parquet y DuckDB son locales y no se versionan.

| Nivel | Parquet local | Tabla DuckDB | Filas | Columnas con llaves nuevas | Llave |
| --- | --- | --- | ---: | ---: | --- |
| Entidad | `eceg_2020_entidad.parquet` | `eceg_entidad_2020` | 32 | 223 | `ID_ENTIDAD` (2 dígitos) |
| Distrito federal | `eceg_2020_distrito.parquet` | `eceg_distrito_2020` | 300 | 227 | `ID_DISTRITO` (`01-03`) |
| Sección | `eceg_2020_seccion.parquet` | `eceg_seccion_2020` | 68 806 | 228 | `ID_SECCION` (`01-0338`) |

**Verificado:** `POBTOT` suma 126 014 024 en cada nivel; las llaves son únicas; DuckDB contiene el mismo número de filas que los Parquet. Las 68 806 claves seccionales coinciden exactamente con `cpv_2020_seccion.parquet` y sus 15 tasas derivadas coinciden sin discrepancias numéricas ni de nulos. El archivo `eceg_2020_completo_auditoria.json` guarda estos conteos localmente. La app sigue usando **sólo secciones** y sus 15 tasas; las tablas de entidad y distrito quedan disponibles para consulta y auditoría, sin mostrar resultados agregados por estado o municipio. El distrito ECEG corresponde al marco de enero de 2021, no a la distritación 2024.

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

Estos porcentajes miden coincidencia de **claves**, no equivalencia espacial ni cobertura de la misma población. El INE resecciona: crea secciones y puede mover parte de una sección existente a otra. Por ello, una clave presente en ambos cortes puede conservar su número y cambiar de territorio; las 2 768 claves nuevas son sólo la parte visible del problema en un cruce por ID. La lista nominal es la columna local de cada Parquet 2024. La fecha de corte documental de esa columna sigue NO VERIFICADA. El archivo `data/electoral/cpv_2020_cobertura.json` reproduce el conteo local; no se versiona.

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

# Piloto local IEEQ 2018–2024: geometría y sentencia

La [auditoría de etapas 4–7](IEEQ_LOCAL_ETAPAS_4_7.md) agrega tres fuentes locales sin versionar: el SHP nacional de Pautas con DBF 30-sep-2019 (`860` claves de Querétaro), el SHP seccional ECEG del INE con corte declarado 20-ene-2021 (`891` claves), y el GPKG original 2024 (`953` claves). Las claves electorales B+C+E de 2018, 2021 y 2024 coinciden con las respectivas capas en **860/860, 891/891 y 953/953**. Esta coincidencia de ID es una prueba de cobertura de llaves, no de perímetros iguales. La superposición ECEG→2024 encontró **788/953** polígonos casi idénticos, que cubren **1 398 846/1 899 053** de lista nominal 2024; el encadenamiento con la referencia 2019 encontró **654/953** y **1 053 423/1 899 053**. Los archivos `data/electoral/ieeq_local/crosswalk_*.parquet` registran área y fracción para cada vínculo y no se agregan a Git.

La [sentencia ST-JRC-216/2024](https://www.te.gob.mx/sentenciasHTML/convertir/expediente/ST-JRC-0216-2024-) permite cotejar seis casillas del distrito local 7 y su total MR de **67 452** votos. El alcance del cotejo y sus límites están en el informe enlazado. La fecha jurídica final de otros distritos y la geometría exacta de 2018 siguen **NO VERIFICADAS**.

## Sedes puntuales de casillas 2024

- Fuente de coordenadas: [Casillas INE, Morlan, DataMX](https://datamx.io/es/dataset/casillas-ine), publicación 3-jun-2024, GeoPackage [descarga](https://datamx.io/dataset/985fceef-1d7b-49ed-8098-a5bc182462d2/resource/50f1cc66-c303-4713-adc4-dcd27bd4c3c3/download/casillas.gpkg). El editor declara que extrajo los puntos de Ubica tu Casilla del INE; **es una copia de tercero**, no una descarga oficial de coordenadas del INE. Licencia indicada por DataMX: CC BY.
- Archivo fuente local: `data/electoral/fuentes_ine/casillas_ine_morlan_2024.gpkg`, SHA-256 `9180feeed610779b789fc76bf20ff60d095a4628f5ce029e5a7681c351b139ea`.
- Fuentes de cotejo: encarte IEEQ 30-may-2024 convertido a Markdown, procesado en `data/electoral/ieeq_local/encarte_qro_2024_claves.parquet`, y `data/electoral/secciones_2024_geom.parquet` (MGE 2024).
- Reproducción: `D:\Conda\envs\cartografunk\python.exe -B -m scripts.build_casillas_2024_puntos`. Salidas **locales no versionadas**: `data/electoral/ieeq_local/casillas_2024_puntos.parquet` y `.audit.json`.
- Llave: `(ID_SECCION, CASILLA_ETIQUETA)`; `B` en la fuente de puntos corresponde a `B1` del encarte. No se usan S ni A para el mapa seccional.
- Aceptación visual: coincidencia de llave, domicilio completo normalizado y punto contenido por el polígono de sección. Tres E fuera del polígono se aceptaron por revisión manual del usuario en Google Maps, con coordenadas documentadas en `electoral/revisiones_sedes_2024.csv`; el script exige que la coordenada revisada esté a ≤35 m del punto fuente y no mueve el punto original. El usuario declaró revisadas visualmente las 15 sedes de los 73 registros pendientes; `electoral/revisiones_sedes_usuario_2024.csv` documenta sección, punto fuente, casillas del grupo y dos notas históricas de domicilio. No se recibieron coordenadas nuevas para esas 15 sedes y tampoco se movieron sus puntos. La aplicación distingue los estados de revisión. El punto es una sede de instalación, no una localización residencial ni CPV propio de casilla E.

| Medición Querétaro B/C/E | Registros |
| --- | ---: |
| Encarte y resultados | 3 081 en 953 secciones |
| Punto con misma llave | 2 614 |
| Punto aceptado tras domicilio y polígono | 2 538 |
| Punto E aceptado tras revisión manual documentada | 3 |
| Punto de 15 sedes revisadas visualmente por el usuario | 73 |
| Total con punto mostrado | 2 614 en 854 secciones |
| Sin punto en la copia cartográfica | 467 |
| Punto aún por revisar por domicilio o polígono | 0 |
| Puntos fuera del polígono | 20 |
| Puntos cuyo domicilio difiere del encarte | 56 |

Los puntos exteriores y las diferencias de domicilio pueden solaparse; no se suman. Las coordenadas aportadas para `22-0165 E1`, `22-0237 E1` y `22-0630 E2` quedan a **8.72 m, 19.70 m y 22.56 m** de los respectivos puntos fuente. En `22-0782`, B1 corresponde al domicilio del encarte 2024 **avenida Camino Real 240**, entonces «In Sano», y C1 al **242**, entonces «Marios Pizza»; la vigencia actual de los negocios no se afirma. Esta revisión visual no equivale a inspección física del sitio. **NO VERIFICADO:** exactitud métrica del punto, causas de ausencia o discrepancia, sitio final de instalación frente al corte del encarte y procedencia oficial directa de cada coordenada. El Parquet no se publica con el código; en un despliegue sin ese archivo la ficha muestra únicamente la sección.
