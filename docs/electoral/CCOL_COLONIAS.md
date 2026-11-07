# Catálogo de Colonias del INE: auditoría de llaves

Investigación local del 2026-11-06. El [Catálogo de Colonias (CCOL) del INE](https://cartografia.ine.mx/sige8/productosCartograficos/catalogos) sí contiene entidad, distrito, municipio, sección, nombre y CP. La capa `ColoniasINE2020a.parquet` contiene **polígonos de colonia**, pero no distrito ni sección. El [manual de digitalización del INE](https://transparencia.ine.mx/obligaciones/rsc/documentos/Articulo74/Formato3a/MANUALDIGITALIZACIONCARTOGRAFICAGEOMEDIAPROFV40.pdf) describe esos atributos de la capa de colonia y advierte que sus límites sólo coinciden parcialmente con los de distrito y sección. El catálogo relaciona una colonia con **varias** secciones; no se debe asignar una colonia completa a una única sección.

## Fuentes examinadas

- Polígonos: `H:\Mi unidad\(0) CARTOGRAFUNK BASICS\(4) DATA\11 Colonias INE\ColoniasINE2020a.parquet`, 107 027 filas. Su original local `D:\(5) WORK\CONJUNTOS DE DATOS\ColoniasINE\ColoniasINE2020.shp` tiene las mismas columnas sin sección ni distrito. El XML local registra cambios de atributos en febrero y marzo de 2024, pero **no documenta el corte de la geometría**.
- CCOL nacional: [respuesta oficial del INE de 2023](https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/152095/ine-ct-r-0175-2023.pdf), que enlaza el [MDB público](https://1drv.ms/u/s!AtO0oFXXb9dEgY-FBCFL9tc0-PKabQQ?e=zXmuke). La ruta de descarga indica **corte 14 de diciembre de 2022**. Se guardó localmente en `data/electoral/ccol_ine_2022_nacional.mdb`, se exportó con `scripts/export_ccol_access.ps1` y se auditó con `scripts/audit_ccol_colonias.py`. El Parquet y el JSON de auditoría locales no se versionan.
- CCOL actual: el [endpoint del SIGE8](https://cartografia.ine.mx/sige8/api/catalogos?producto=CCol) ofrece corte **19 de enero de 2026**. Su XLS «nacional» descargado tiene 16 383 filas de sólo cinco entidades, por lo que no se trató como catálogo nacional completo.

## Medido

| Revisión | Resultado |
| --- | ---: |
| Filas CCOL 2022 | 188 279 |
| Colonias CCOL distintas por `(ENTIDAD, ID)` | 112 067 |
| Polígonos locales (`ColoniasINE2020a`) | 107 027 |
| IDs compartidos por entidad | 100 668 |
| IDs compartidos cuyo nombre también coincide | 4 859 |
| IDs compartidos cuyos nombre, municipio y CP coinciden | 4 630 |
| Polígonos con algún candidato por `(entidad, municipio, nombre normalizado, CP)` | 101 515 |
| Polígonos con **un** candidato por esa llave compuesta | 95 007 |
| Polígonos con **varios** candidatos | 6 508 |
| Polígonos sin candidato | 5 512 |
| Colonias del CCOL en varias secciones | 35 140 |
| Pares colonia–sección del piloto espacial 2024 comparables por llave textual única | 111 524 |
| Pares comparables también listados en CCOL 2022 | 104 704 (93,885 %) |
| Población urbana observada en los pares comparables | 85 329 325 |
| Población urbana en los pares también listados | 81 268 041 (95,240 %) |

Por tanto, **`(ENTIDAD, ID)` no es una llave de unión válida entre los cortes**: los números se reutilizaron o reordenaron. Como comprobación puntual, el ID 1 de Aguascalientes es `LOS TEPETATES` en el polígono y el CCOL 2022, pero `MISION DE SAN JERONIMO` en el CCOL 2026. La coincidencia de nombre, municipio y CP ofrece candidatos, no prueba identidad geométrica ni continuidad de sección. El JSON local `data/electoral/ccol_ine_2022_auditoria.json` reproduce los conteos.

La comparación de pares usa las 32 entidades del piloto espacial, pero **sólo** las 95 007 colonias con un candidato único por entidad, municipio, nombre normalizado y CP. Cuenta cada par colonia–sección observado en el piloto una vez. La proporción de población suma la población urbana observada en esos pares; no es cobertura de toda la población censal ni prueba de que el CCOL 2022 y el piloto 2024 compartan límites. Los 6 820 pares no listados pueden reflejar cambios de corte, errores de asignación o diferencias de catálogo; la causa está sin verificar.

## NO VERIFICADO y decisión

- Corte y procedencia geométrica exactos de `ColoniasINE2020a.parquet`.
- Equivalencia de los límites de colonia y sección entre los polígonos locales, el CCOL 2022, el ECEG 2020/2021 y los votos 2024.
- Que una coincidencia textual compuesta represente la misma colonia en ambos cortes; los 6 508 casos ambiguos requieren resolver identidad o geometría.
- Catálogo CCOL nacional del mismo corte que el polígono y/o del proceso electoral 2024.

**Decisión:** el CCOL 2022 queda como fuente de contraste y no reemplaza el cruce espacial del piloto ni el ECEG seccional usado por la app. El siguiente paso es obtener el CCOL del corte apropiado y medir la concordancia por claves y geometría antes de modificar la asignación de manzanas.
