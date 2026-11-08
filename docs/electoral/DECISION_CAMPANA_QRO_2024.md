# Lista de revisión de campaña · Querétaro 2024

**Unidad principal:** casilla B/C/E para el diagnóstico observado; sección sólo para el perfil CPV y la comparación histórica del ML. Querétaro es el filtro de la muestra. Se conservan las 3 081 casillas IEEQ 2024 B/C/E, incluso las que no tienen CPV comparable. Las casillas S y el voto anticipado A se tratan aparte.

La pestaña «Dónde actuar · casillas» muestra una lista filtrable y descargable por partido. Entra una casilla si el partido quedó a 10 pp o menos del primero entre siete partidos atribuidos, empató, conservó una ventaja menor de 10 pp, o presenta votos sobre lista nominal que deben revisarse. Las filas se agrupan por **motivo y clave**, sin ordenar por supuesta probabilidad de victoria. Para cada una se ven votos del partido y del rival, distancia para liderar, abstención observada, apoyo mínimo federal 2024 cuando existe, perfil CPV de la sección cuando es comparable y una frase que explica el motivo. El usuario puede introducir costo supuesto por voto adicional y presupuesto por casilla; sólo se compara aritméticamente el costo supuesto con ese presupuesto. En victorias no se calcula costo de defensa.

**Exploración geográfica:** la tabla permite seleccionar una casilla en «Para revisar» o «Todas». Su ficha abre el polígono de la **sección electoral MGE 2024** y muestra todas las casillas B/C/E de esa sección con sus resultados partidarios. La tabla principal deja visibles las columnas de decisión; la ficha muestra motivo, márgenes, rasgos CPV seccionales y localidad de instalación cuando consta en el encarte. El Parquet geométrico local contiene las 953 secciones del piloto y las 3 081 casillas B/C/E se vinculan por clave a una de ellas. **No hay coordenada verificada de la mesa**, por lo que el mapa no coloca marcadores de casilla ni usa el centroide como sustituto.

| Partido | Examinar pérdida cercana | Examinar empate | Defender ventaja cercana | Revisar dato electoral | Total | Con CPV comparable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PAN | 594 | 4 | 400 | 1 | 999 | 789 |
| PRI | 55 | 1 | 15 | 1 | 72 | 66 |
| PRD | 8 | 0 | 0 | 1 | 9 | 9 |
| MC | 43 | 2 | 15 | 1 | 61 | 50 |
| PVEM | 60 | 2 | 35 | 1 | 98 | 86 |
| MORENA | 420 | 7 | 575 | 1 | 1 003 | 800 |
| PT | 2 | 2 | 2 | 1 | 7 | 7 |

Estas cifras son **casillas** y dependen del umbral exploratorio de 10 pp. «Faltante ≤ abstención» sólo constata que hubo suficientes personas sin voto registrado para cubrir numéricamente la distancia; no demuestra que votarían por el partido. El apoyo mínimo federal es de tres boletas de 2024 y no mide fidelidad individual. El perfil CPV describe la sección y se repite en sus casillas; no describe a los votantes de una E. **CPV 2020 vs votos 2024; asociación, no causa.** El reparto fraccionario de coaliciones es analítico, no el cómputo legal confirmado por partido.

## Contraste con señales de 2021 y ML

Sobre las **788 secciones comparables**, se contó cuántas derrotas partidarias a ≤5 pp del primero habrían tenido señal puntual de liderazgo por persistencia de 2021 o por el árbol con CPV. Esta comparación **no interviene en la lista de casillas**: sólo audita si ML aporta una señal distinta de una regla sencilla.

| Partido | Derrotas partidarias ≤5 pp | Persistencia marcó liderazgo | ML marcó liderazgo | Ambos | Sólo ML |
| --- | ---: | ---: | ---: | ---: | ---: |
| PAN | 76 | 65 | 74 | 65 | 9 |
| PRI | 10 | 4 | 0 | 0 | 0 |
| PRD | 0 | 0 | 0 | 0 | 0 |
| MC | 5 | 0 | 0 | 0 | 0 |
| PVEM | 12 | 0 | 0 | 0 | 0 |
| MORENA | 68 | 3 | 3 | 3 | 0 |
| PT | 0 | 0 | 0 | 0 | 0 |

Para PAN, las 65 señales de persistencia están contenidas en las 74 del ML; en MORENA coinciden las tres. Estos conteos son retrospectivos, usan el signo puntual y no el intervalo. Una señal equivocada del modelo no vuelve reversible una derrota. La [auditoría de candidaturas](PERFILAMIENTO_CPV_QRO_2024.md) encontró que 27 de las 76 pérdidas cercanas de PAN entre partidos ya eran victorias de la candidatura local.

**Fuentes y reproducción:** IEEQ 2024 B/C/E normalizadas; ECEG INEGI–INE CPV 2020; apoyo mínimo federal 2024. Reglas en [`electoral/diagnostico_casillas.py`](../../electoral/diagnostico_casillas.py), vista en [`electoral/diagnostico_casillas_tab.py`](../../electoral/diagnostico_casillas_tab.py) y comparación en [`scripts/auditar_senales_ml_2024.py`](../../scripts/auditar_senales_ml_2024.py). Los archivos Parquet y JSON de resultados siguen locales, sin commit.

**NO VERIFICADO:** probabilidad de victoria futura, votos movilizables, costo por voto real, efecto de cada acción, estabilidad de asociaciones CPV fuera de esta elección y atribución legal definitiva de coaliciones. La lista sirve para decidir qué revisar en campo; el retorno exige registrar y comparar intervenciones posteriores.
