# Metodología implementada

Esta página describe las operaciones del código actual. Los nombres en mayúsculas son columnas de los CSV; `cand_*`, `rep_*` y `frac_*` son columnas calculadas.

## Candidaturas y llaves

[`CANDIDATURAS` en `config.py`](../../electoral/config.py) define para Presidencia 2024:

| Columna calculada | Suma de columnas de origen |
| --- | --- |
| `cand_PAN_PRI_PRD` | `PAN + PRI + PRD + PAN_PRI_PRD + PAN_PRI + PAN_PRD + PRI_PRD` |
| `cand_PVEM_PT_MORENA` | `PVEM + PT + MORENA + PVEM_PT_MORENA + PVEM_PT + PVEM_MORENA + PT_MORENA` |
| `cand_MC` | `MC` |

[`cargar_sec()`](../../electoral/datos.py) conserva las columnas del CSV y usa `sum(axis=1, min_count=1)` para crear esas candidaturas. En Diputaciones MR y Senadurías MR, [`actividad_distrital()` y `candidaturas_por_distrito()`](../../electoral/candidaturas.py) leen `_DISCAND.csv` por `(ID_ESTADO, ID_DISTRITO_FEDERAL)`: una coalición activa suma sus partidos individuales y todas sus combinaciones; si no está activa, cada integrante compite con su columna individual. `MC` y `CAND_IND*` usan su propia columna. `cand_*` es `NaN` donde la candidatura no está activa. [`resolver_candidatura()`](../../electoral/candidaturas.py) devuelve la columna activa que contiene al partido; [`rentabilidad_partido()`](../../electoral/rentabilidad_partido.py) evalúa esa candidatura, no reparte sus votos entre partidos.

[`cargar_sec()`](../../electoral/datos.py) construye `ID_SECCION = str(ID_ESTADO).zfill(2) + '-' + str(SECCION).zfill(4)`. [`cargar_casillas()`](../../electoral/casillas.py) usa el mismo `ID_SECCION` y crea `ID_CASILLA_LEGIBLE = ID_SECCION + '-' + TIPO_CASILLA + '-' + ID_CASILLA + '-' + EXT_CONTIGUA + '-' + ACTA_CASILLA-MEC`. La llave que comprueba es `(ID_ESTADO, SECCION, TIPO_CASILLA, ID_CASILLA, EXT_CONTIGUA, ACTA_CASILLA-MEC)`; excluye `TRIBUNAL == 'ANULADA'` tras comprobar su unicidad.

Estado en [`datos.py`](../../electoral/datos.py) y [`casillas.py`](../../electoral/casillas.py), en ese orden: `extranjero` si `SECCION == 0`; `sin_resultado` si `NUM_VOTOS_VALIDOS` es nulo o cero; `con_resultado` en otro caso. Solo `con_resultado` entra al ranking por fila.

## Ranking, distancias y abstención

[`rentabilidad(df, candidaturas, evaluar)`](../../electoral/rentabilidad.py) toma `primero` y `segundo` como el mayor y segundo mayor voto entre las candidaturas; los `NaN` se sustituyen por `-inf` únicamente para ordenar. Si el voto propio iguala a `primero` y supera a `segundo`, `resultado = ganada`; si iguala a ambos, `empate`; en los demás casos, `perdida`. [`rentabilidad_partido()`](../../electoral/rentabilidad_partido.py) quita del conjunto de rivales la columna que está evaluando en esa fila y deja métricas vacías si ese partido no compitió.

| Métrica | Fórmula y dominio |
| --- | --- |
| `margen_votos` | `propio - segundo`, solo `ganada`. |
| `faltante_votos` | `primero - propio`, solo `perdida` o `empate`; en empate es 0. |
| `margen_pct` | `100 × margen_votos / NUM_VOTOS_VALIDOS`; `NaN` si el denominador es 0. |
| `faltante_pct` | `100 × faltante_votos / NUM_VOTOS_VALIDOS`; `NaN` si el denominador es 0. |
| `votos_para_ganar` | `faltante_votos + 1`; `NaN` para ganadas. |
| `abstencion` | `LISTA_NOMINAL - votos_en_lista` si existe esa columna; de otro modo, `LISTA_NOMINAL - TOTAL_VOTOS`. |
| `votos_sobre_lista` | `abstencion < 0`. |
| `participacion_pct` | `100 × votos_en_lista / LISTA_NOMINAL`, o `TOTAL_VOTOS` en lugar de `votos_en_lista` si esta no existe; `NaN` si `LISTA_NOMINAL == 0`. |
| `rescatable_vs_abst` | `votos_para_ganar / abstencion`, solo si `abstencion > 0`. |

Para secciones, [`cargar_sec()`](../../electoral/datos.py) suma `TOTAL_VOTOS` de las filas `_CAS.csv` con `TIPO_CASILLA == 'S'` y `TRIBUNAL != 'ANULADA'` por `(ID_ESTADO, SECCION)`. Produce `votos_casillas_s`, `n_casillas_s` y, solo en `con_resultado`, `votos_en_lista = TOTAL_VOTOS - votos_casillas_s`. En [`cargar_casillas()`](../../electoral/casillas.py), `votos_en_lista = TOTAL_VOTOS` salvo en casillas `S`, donde es `NaN`; así, `abstencion` y `participacion_pct` de esas casillas resultan `NaN` al llamar a `rentabilidad()`.

## Clasificación

[`Umbrales` y `clasificar()`](../../electoral/clasificacion.py) usan por defecto `solida_pp = 15.0`, `competitiva_pp = 5.0`, `lejana_pp = 15.0`, `votos_alcanzables = 100`. Los cuatro valores deben ser positivos y `competitiva_pp <= lejana_pp`.

| `clase` | Condición en `con_resultado` |
| --- | --- |
| `ganada_solida` | `ganada` y `margen_pct >= solida_pp`. |
| `ganada_ajustada` | `ganada` y `margen_pct < solida_pp`. |
| `empate` | `resultado == 'empate'` y `faltante_pct` calculable. |
| `perdida_competitiva` | `perdida` y `faltante_pct < competitiva_pp`. |
| `perdida_intermedia` | `perdida` y `competitiva_pp <= faltante_pct < lejana_pp`. |
| `perdida_lejana` | `perdida` y `faltante_pct >= lejana_pp`. |

La categoría es ordenada en el orden de la tabla. Queda vacía fuera de `con_resultado` o si falta el porcentaje aplicable. `alcanzable_por_abstencion = (rescatable_vs_abst <= 1)` solo en pérdida/empate, con abstención positiva, `votos_sobre_lista == False` y cociente calculable; en otro caso es nulo. `alcanzable_en_votos = (votos_para_ganar <= votos_alcanzables)` solo en pérdida/empate con faltante calculable.

## Agregación

[`agregar()`](../../electoral/agregacion.py) admite `pais`, `distrito`, `municipio` y `estado`. Distrito usa `(ID_ESTADO, ID_DISTRITO_FEDERAL)`; municipio usa `(ID_ESTADO, ID_MUNICIPIO, MUNICIPIO)` del CSV; estado usa `ID_ESTADO`. País incluye las filas `extranjero` en las sumas. Los demás niveles excluyen `extranjero`. Cuenta secciones `con_resultado` y `sin_resultado` por clave; suma votos y lista nominal de `con_resultado`, más `extranjero` cuando el nivel es `pais`. Suma votos por candidatura y recalcula el ranking agregado llamando a `rentabilidad()` y `clasificar()`, o a `rentabilidad_partido()` cuando se pasa `partido`. También cuenta las clases de sección, los votos para ganar de `perdida_competitiva` y los casos `votos_sobre_lista`.

## Repartos experimentales por partido

[`repartir_distrito()`](../../electoral/reparto_distrito.py) agrupa `_SEC` por `(ID_ESTADO, ID_DISTRITO_FEDERAL)`, incluyendo el distrito 0 extranjero y las filas sin resultado tal como vienen en `_SEC`. Parte de los votos propios `PAN`, `PRI`, `PRD`, `PVEM`, `PT`, `MORENA`; `MC` queda en `rep_MC = MC`.

- `A_propios`: para cada columna combinada, divide sus votos enteros entre los partidos nombrados (`cociente, residuo = divmod(votos, número de integrantes)`). Suma el cociente a cada integrante y todo el residuo al de mayor columna individual propia en el distrito.
- `B_propios`: suma las cuatro columnas combinadas de cada coalición y divide el total entre sus tres integrantes. El residuo va al de más votos propios en el distrito.
- En empate de votos propios, `np.argmax` selecciona al primero en el orden `PAN, PRI, PRD` o `PVEM, PT, MORENA` definido en [`reparto.py`](../../electoral/reparto.py). Las columnas `suma_original_*` registran el total previo al reparto.

[`repartir_coalicion()`](../../electoral/reparto.py) aplica las variantes A/B por fila `con_resultado`, con el voto propio de esa fila como criterio del residuo. [`repartir_fraccionario()`](../../electoral/reparto_fraccionario.py) calcula por fila `con_resultado` `frac_partido = voto_propio + Σ(votos_de_combinación / número_de_integrantes)` para las combinaciones que incluyen al partido, sin residuo ni redondeo. **Ninguna variante está verificada como regla oficial**, según los docstrings de esas funciones.

## Geometría

[`cargar_geometria()`](../../electoral/geometria.py) lee la capa `SECCIONES_2024`, reemplaza el CRS declarado por EPSG:32614, simplifica en metros con `preserve_topology=True` y tolerancia predeterminada de 25 m, luego reproyecta a EPSG:4326. El uso de EPSG:32614 es una **hipótesis de trabajo**, según [`cartografunk_ine_crs.json`](<C:/Users/HeyCe/AppData/Local/Temp/cartografunk_ine_crs.json>) y el código; no se presenta como confirmación del CRS de origen.
