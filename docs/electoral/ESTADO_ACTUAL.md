# Estado actual del módulo electoral

## Ensayo ML con CPV y reporte de errata, 2026-11-07

Se ejecutó un [modelo de árboles con las 15 tasas CPV](BENCHMARK_ML_CPV_QRO_2024.md): entrenamiento 2018→2021 en 654 secciones estables y evaluación 2024 en 788 secciones, 73.66 % de la lista nominal. Su MAE medio de cuota fue **5.90 pp**, frente a **5.38 pp** de Ridge sin CPV; detectó 75 de 436 liderazgos observados de MORENA por punto estimado y generó 393 falsos liderazgos de PAN. La app muestra el ensayo por partido y sección cuando los archivos locales existen. **NO VERIFICADO:** confianza futura ni causalidad del CPV; el árbol no se presenta como pronóstico fiable. El [posible error de rango `0529`](ERRATA_ANEXO_IEEQ_2026.md) quedó descrito con texto listo para remitir al IEEQ; la corrección sigue por confirmar.

## Diagnóstico de campaña por casilla, 2026-11-07

Se añadió una pestaña aislada «Dónde actuar · casillas» para el piloto IEEQ Querétaro. Por partido y registro B/C/E muestra margen frente al mayor de otros seis partidos atribuidos, votos para liderar, abstención, apoyo mínimo federal 2024 cuando está disponible, costo supuesto opcional y una acción como hipótesis. El perfil principal resume 3–5 asociaciones de las 15 variables ECEG por clase de casilla; cada sección cuenta una sola vez por clase. **CPV 2020 vs votos 2024; asociación, no causa.** [Datos, cobertura y límites](DATOS.md#diagnóstico-local-ieeq-2024-por-registro-de-casilla).

**Medido:** 2 323/3 081 registros B/C/E, 788/953 secciones y 73.66 % de lista nominal tienen cruce CPV con geometría comparable. Los 758 registros restantes, en 165 secciones, mantienen diagnóstico electoral sin perfil CPV. Para MORENA, el contraste victoria sólida vs derrota lejana muestra mayor proporción de personas de 60+ y educación posbásica en las secciones de derrota lejana; es una comparación descriptiva, no una explicación individual de voto. 105 pruebas electorales pasaron y la vista aislada abrió con AppTest sin excepciones.

Las 77 claves aparentes repetidas ya quedaron aclaradas: eran contiguas de casillas extraordinarias E cuyo número faltaba en el CSV, pero estaba en el JSON IEEQ. Se recuperaron las 218 etiquetas E sin eliminar filas ni modificar votos. El encarte empata con las 3 081 B/C/E y aporta su localidad de **instalación**, incluida la de las 218 E; [método](DATOS.md#diagnóstico-local-ieeq-2024-por-registro-de-casilla).

Las **218 E** ya tienen lista nominal individual en el IEEQ (**108 227 electores registrados en total**); las 218 cifras coinciden con la tabla federal de casillas de Presidencia 2024 del INE. Esta lista nominal no es el CPV ni describe edad, educación o vivienda de quienes votan en la E. El perfil sociodemográfico propio de la E sigue pendiente de su conformación por manzanas/localidades de residencia.

**NO VERIFICADO:** área de atención y CPV propio de extraordinarias; legalidad del reparto fraccionario como voto oficialmente atribuido al partido; estabilidad de las asociaciones entre años y entidades; capacidad real de movilizar abstencionistas; efecto y costo real de las acciones. El apoyo mínimo federal 2024 no mide fidelidad individual ni histórica.

La [pregunta central del producto](PREGUNTAS_ESTRATEGICAS.md) queda formulada como **«¿dónde vale la pena concentrar esfuerzos de campaña?»**. Primero se identifican asociaciones entre CPV y resultados por casilla; después se cruzan con rentabilidad, abstención, apoyo mínimo observado, costo supuesto y cobertura para proponer acciones como hipótesis. La implementación actual aún no mide el efecto causal de esas acciones.

## Benchmark exploratorio por partido, 2026-11-07

Se ejecutó la [primera prueba retrospectiva por partido](BENCHMARK_PARTIDOS_QRO_2024.md) en 788 de 953 secciones comparables ECEG→2024 (73.66 % de lista nominal). Las combinaciones IEEQ se atribuyen por fracciones iguales a los partidos marcados, sin redondeo seccional. Ridge obtuvo MAE medio de cuota de 5.38 puntos porcentuales frente a 5.95 de persistencia 2021, pero no detectó ninguna de las 436 secciones donde MORENA lideró entre siete partidos comparables. **No hay pronóstico de liderazgo confiable ni validación prospectiva.** El código, protocolos sellados, cobertura y abstenciones están documentados en ese informe. La etapa 6 anterior conserva su resultado histórico de NO-GO de tres fechas; la corrida actual es una decisión exploratoria posterior del propietario.

La app añade una pestaña aislada «Forecasting · diagnóstico» que presenta el ensayo retrospectivo por partido y sección, incluido el resultado observado y los intervalos. Para MORENA/Ridge en el archivo completo: 0 secciones con lectura «lidera», 201 «no lidera», 587 indeterminadas y 165 sin modelo por cambio territorial. El bloque se oculta sin los archivos locales. No se presenta como probabilidad de victoria ni se atribuye causalidad al CPV. [Método y límites](IEEQ_LOCAL_ETAPAS_4_7.md#etapa-7--diagnóstico-y-demo).

Por instrucción posterior del propietario, se [reagruparon las secciones relacionadas de 2021 y 2024](AGRUPACION_SECCIONES_QRO_2021_2024.md): **891 + 953 secciones forman 834 grupos**, de los cuales 801 son uno a uno y 33 reúnen divisiones/fusiones. Cada año conserva 100 % de su lista nominal y sus votos al sumar; no se reparte el voto viejo entre secciones nuevas. El benchmark por grupo incluye toda la lista nominal 2024, pero **no produce una predicción individual para las 152 secciones actuales de los 33 grupos reconfigurados**. Ridge detecta 106 de 462 grupos con liderazgo observado de MORENA con su estimación puntual, y marca falsamente liderazgo de PAN en 391 grupos: aún no hay forecast confiable. La pestaña muestra esta comparación histórica como bloque separado cuando existen los datos locales.

El [cruce de encartes 2021 y 2024](CRUCE_ENCARTES_QRO_2021_2024.md) encontró candidatos de origen para las 81 secciones 2024 sin clave ECEG: ocho con mismo domicilio de casilla, 69 adicionales con misma localidad y superposición territorial, y cuatro sólo con vínculo geométrico. El listado de 92 enlaces queda local para revisión sección por sección. No se redistribuyeron votos ni población por esa pista.

La auditoría separada de clave, distrito local y domicilio encontró **19 claves 2021 desaparecidas, 81 nuevas y 872 conservadas**. Entre las conservadas, **532 cambiaron de distrito local**; entre las nuevas, **20** tienen el mismo distrito local que su origen territorial dominante. **419** claves conservadas no tienen un domicilio textual idéntico entre encartes, lo que por sí solo no confirma cambio físico de sede. La causa de cada cambio y la reasignación de votantes siguen **NO VERIFICADAS**. [Detalle y método](CRUCE_ENCARTES_QRO_2021_2024.md#clave-distrito-y-domicilio-auditoría-separada).

## Piloto local Querétaro: etapas 1–3

Se descargaron y normalizaron los resultados IEEQ de diputaciones locales MR 2018, 2021 y 2024. Las salidas locales por casilla, sección B+C+E y casillas especiales, los hashes de 20 archivos fuente y los cotejos están descritos en [IEEQ_LOCAL_ETAPAS_1_3.md](IEEQ_LOCAL_ETAPAS_1_3.md). Hay 860, 891 y 953 secciones B+C+E respectivamente. El cotejo seccional no deja diferencias sin explicar; las casillas S se conservan aparte como voto fuera de la sección de residencia. Se versionaron los Parquet pequeños de casillas especiales MR 2018/2021/2024 y el domicilio de instalación de las 57 S de 2024 extraído del encarte IEEQ; faltan coordenadas verificadas. El [crosswalk geométrico y las puertas de etapas 4–7](IEEQ_LOCAL_ETAPAS_4_7.md) ya están medidos para Querétaro: 788/953 secciones 2024 casi idénticas al marco ECEG de enero de 2021; 654/953 también casi idénticas a la referencia 2019 en el paso anterior. La cadena cubre 55.47 % de la lista nominal 2024, debajo del umbral de 70 % registrado junto con el resultado, **sin preregistro independiente: NO-GO para ML de tres elecciones**. La app ya incluye una pestaña de diagnóstico local por sección. La geometría exacta de 2018 y el voto de diferencia distrital 2018 siguen **NO VERIFICADOS**. [Fuentes de reseccionamiento](RESECCIONAMIENTO_FUENTES.md).

## Auditoría de colonias del 2026-11-06

Se obtuvo el CCOL nacional 2022 del INE y se comparó con `ColoniasINE2020a.parquet`. Aunque 100 668 polígonos comparten `(ENTIDAD, ID)` con el catálogo, sólo 4 630 coinciden también en nombre, municipio y CP: **el ID no es una llave segura entre cortes**. En las 95 007 colonias con un único candidato por atributos, 104 704 de 111 524 pares colonia–sección del piloto espacial (93,885 %) aparecen también en el CCOL 2022. La procedencia y el corte exacto de los polígonos, así como la causa de los 6 820 pares discordantes, siguen **NO VERIFICADOS**. La app conserva el ECEG a nivel sección; [auditoría y fuentes](CCOL_COLONIAS.md).

## Revisión de catálogos SIGE del 2026-11-07

Se revisaron los [14 catálogos SIGE](SIGE_CATALOGOS.md), todos con corte enero de 2026. EDMSLM aportado por el usuario vincula localidad/manzana electoral con sección de ese corte, pero **no con casilla E**. En el encarte 2024, la E de Fraccionamiento Viñedos está en `22-0553`; el EDMSLM 2026 asigna esa localidad a `22-0999`, `22-1002`, `22-1003` y `22-1004` y no contiene `22-0553`. No se han reasignado votos ni CPV con ese catálogo; la correspondencia final 2024→2026 sigue **NO VERIFICADA**. [Auditoría EDMSLM](EDMSLM_CATALOGO.md).

El EDMSLM de enero de 2026 ya se convirtió a Parquet local para Querétaro: 59 157 manzanas electorales, 1 090 secciones; 935 de las 953 claves de resultados IEEQ 2024 coinciden y 18 faltan. El [anexo oficial IEEQ](EDMSLM_CATALOGO.md) explica las 18: seis secciones originaron 60 nuevas en el programa 2023–2024 y otras 12 originaron 95 en 2024–2025. `0553 → 0995–1006` queda **verificado a nivel de sección padre→hijas**; un plano anterior a la elección muestra `0553` y el paquete cartográfico IEEQ actualizado el 28 de junio de 2024 muestra las nuevas claves. **NO VERIFICADO:** equivalencia precisa por manzana ni residencia asignada a cada casilla E. [Tabla CSV, fechas, fuentes y hashes](EDMSLM_CATALOGO.md).

## Adición del 2026-11-06

Se integró el CPV 2020 del ECEG INEGI-INE por `ID_SECCION` en un Parquet local con 15 tasas. La coincidencia exacta de claves con cada Parquet seccional 2024 es de 67 736 secciones (96,030–96,074 %) y cubre 94,501–94,719 % de su lista nominal; detalle en [DATOS.md](DATOS.md). «¿Por qué?» ahora muestra el perfil CPV por clase de **sección**: ganada sólida, pérdida competitiva y pérdida lejana en la vista electoral; Bastión, Base fuerte y Resto en apoyo mínimo por partido. Cada variable tiene medias y diferencias estandarizadas; correlación y regresión se dejan en «Avanzado». El estado solo filtra la muestra. El INE resecciona y puede alterar incluso secciones que conservan su clave: en Querétaro ya se midió la superposición ECEG→2024; para el resto del país la equivalencia geométrica sigue **NO VERIFICADA**, y la composición de personas no se infiere de polígonos.

Los tres CSV completos del ZIP ECEG se guardaron además como Parquet y tablas materializadas en `data/electoral/eceg_2020.duckdb`: 32 entidades, 300 distritos federales y 68 806 secciones. La suma `POBTOT` coincide entre niveles (126 014 024). Las 15 tasas usadas por la app se verificaron contra el Parquet seccional completo sin discrepancias. Los archivos generados son locales, no versionados; [DATOS.md](DATOS.md#tablas-completas-de-entidad-distrito-y-sección) documenta rutas, llaves y límites de uso. La app sigue operando a nivel sección; las tablas agregadas sirven para consulta y auditoría.

El primer modelo de `explicacion.py` usaba `margen_pct` como objetivo y eliminaba sus nulos. Como `margen_pct` solo existe cuando la candidatura ganó, **sí filtraba de hecho el análisis a victorias**. El objetivo electoral actual es `ventaja_firmada = margen_pct` en victoria, `-faltante_pct` en derrota y `0` en empate. `faltante_pct` y `alcanzable_por_abstencion` se analizan únicamente en derrotas; `rescatable_vs_abst` no entra como variable. El modelo de apoyo mínimo usa `piso_pct` del partido seleccionado.

La auditoría de secciones sin CPV por estado y clase está en [CPV_SIN_CRUCE.md](CPV_SIN_CRUCE.md) y su CSV de detalle. Validación de esta revisión: **75 pruebas aprobadas**, 2 advertencias de GDAL. AppTest con `timeout=180` abrió «Mapa y secciones» y «Apoyo mínimo», además de Diputaciones y Senadurías: los bloques «¿Por qué?» aparecieron sin excepciones. La vista se inspeccionó en navegador a 1252 px y 390 px: la tabla se desplaza dentro de su marco en móvil, sin desbordamiento horizontal de la página. La portada ya describe el CPV como disponible cuando existe el archivo local. La cifra histórica de 67 pruebas del apartado inferior corresponde al estado previo a la integración CPV.

El histórico oficial del INE registra primeros movimientos 2021–2023 para las **2 768 secciones territoriales** de 2024 sin clave ECEG. Esto acota la falta de cobertura por clave; la equivalencia de los polígonos de las **67 736 claves coincidentes sigue NO VERIFICADA**. El paquete local `deploy_streamlit/` contiene `explorador.py`, no `electoral/app_simple.py`; no hay un despliegue electoral configurado en ese paquete para revisar visualmente.

Actualizado: 2026-11-04. Fuente principal: código y pruebas de esta rama. Las cifras de inventario históricas conservan sus fuentes en [DATOS.md](DATOS.md) y [PENDIENTES.md](PENDIENTES.md).

## Rama y aplicaciones

| Elemento | Estado comprobado |
| --- | --- |
| Rama de trabajo | `demo-tres-elecciones`, derivada de `demo-11am` (`31464db`) y publicada como `origin/demo-tres-elecciones`. |
| Respaldos locales | `respaldo-antes-noche` apunta a `ab5b4ea`; `demo-11am`, `demo-11am-b` y `demo-11am-c` conservan sus commits originales. No se publicaron esas etiquetas. |
| App vigente para el demo | `electoral/app_simple.py`: selector de Presidencia, Diputaciones MR y Senadurías MR de 2024; candidatura activa, mapa, clases, aportes de partidos de coalición, priorización y apoyo mínimo. |
| App anterior | `electoral/demo_app.py`: demo de Presidencia 2024. |
| Archivos de datos | `data/electoral/*.parquet`, generados localmente y no versionados; los ZIP de origen se indican en `electoral/config.py`. |

Los cambios funcionales de `demo-11am-b` (controles técnicos en «Avanzado») y `demo-11am-c` (costo inicial vacío, persistencia por sesión, tabla legible, Querétaro por omisión) se integraron en la app vigente. El ámbito de apoyo mínimo permanece visible, según la corrección posterior a `demo-11am-b`. Las ramas y etiquetas de respaldo no se borraron.

## Cálculos que muestra la app

- El resultado, la clase, el margen, el faltante y los votos para ganar pertenecen a la **candidatura** seleccionada. En Diputaciones y Senadurías, las candidaturas activas varían por distrito; una sección sin la candidatura elegida queda sin clase para ella. Véanse `electoral/analisis_demo.py`, `electoral/candidaturas.py` y `electoral/rentabilidad.py`.
- El selector de partidos aparece junto al de candidatura cuando se elige una coalición. Los votos atribuidos y porcentajes por sección y estado usan `repartir_coalicion(..., variante="A_propios")`. Es un reparto **experimental**; la regla oficial sigue NO VERIFICADA.
- «Apoyo mínimo observado 2024» compara las tres boletas del mismo año. Sus clases son una propuesta provisional; no mide personas ni continuidad entre años. Véanse `electoral/fidelidad.py` y `electoral/estadisticas_fidelidad.py`.
- El simulador espera un costo ingresado por el usuario antes de calcular. Conserva costos y descartes por sesión y los rotula como «supuesto del usuario» en el Excel.
- El CPV 2020 se incorporó por sección mediante ECEG. La equivalencia territorial exacta del seccionado ECEG con 2024 sigue NO VERIFICADA.

## Validación de esta integración

Ejecutado desde `C:\cartografunk_web` con `D:\Conda\envs\cartografunk\python.exe`:

```powershell
$env:PATH='D:\Conda\envs\cartografunk\Library\bin;'+$env:PATH
D:\Conda\envs\cartografunk\python.exe -B -m pytest electoral/tests -q
```

Resultado: **67 aprobadas, 0 omitidas**, 2 advertencias de GDAL. AppTest con `timeout=180`: **0 excepciones** en Presidencia/PVEM-PT-MORENA/estado 14, Diputaciones MR/PAN-PRI-PRD/estado 9 y Senadurías MR/MC/estado 14; tiempos medidos 32.03 s, 9.98 s y 10.47 s, respectivamente. El aspecto en navegador y el arranque del servidor: **NO VERIFICADO**.

## Acceso entre cuentas

Esta documentación se comparte mediante `origin/demo-tres-elecciones`. No existe un `.mcp.json` en el repositorio. Los Parquet locales y las rutas `D:\` no se comparten por Git; su acceso desde otras cuentas o máquinas es **NO VERIFICADO**. No se ha implementado un servidor MCP para esos datos.
