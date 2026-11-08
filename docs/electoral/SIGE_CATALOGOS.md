# Inventario de los 14 catálogos del SIGE

Revisión de la [página oficial de catálogos del INE](https://cartografia.ine.mx/sige8/productosCartograficos/catalogos) el 2026-11-07. **Los 14 productos muestran corte enero de 2026** y la página advierte que cada descarga corresponde al último corte disponible, no a la fecha de consulta. La interfaz examinada no ofrece un selector de corte histórico. Se revisaron las fichas públicas, no el contenido completo de cada descarga. `CIGB` y `CPC` son PDF y no se abrieron; para leerlos habría que convertirlos antes a Markdown conforme a `CLAUDE.md`.

| Producto | Campos o contenido anunciado | Formatos | Valor para el proyecto |
| --- | --- | --- | --- |
| EDMSLM | Entidad, distrito federal, municipio, sección, localidad, manzana y estatus de manzana | MDB, TXT | **Clave:** relación manzana/localidad electoral→sección del corte 2026; [auditoría local](EDMSLM_CATALOGO.md) |
| CDEL | Entidad y distrito local | XLS, MDB, TXT | Sólo catálogo de claves de distrito local |
| CDEF | Entidad y distrito federal | XLS, MDB, TXT | Sólo catálogo de claves de distrito federal |
| CDEFCD | Distrito federal y localidad de su cabecera | XLS, MDB, TXT | Ubica cabeceras distritales; no residencia electoral |
| CM | Entidad, municipio y nombre | XLS, MDB, TXT | Normaliza nombres municipales |
| CMDEF | Municipio y distrito federal | XLS, MDB, TXT | Referencia de distritación federal del corte |
| CSEDEF | Sección, tipo urbano/rural/mixto, municipio y distrito federal | XLS, MDB, TXT | Audita claves seccionales y distrito federal 2026 |
| CSDEL | Sección, municipio, distrito federal y **distrito local** | XLS, TXT | **Útil para elección local**; no aplicar a 2024 sin cotejar el corte |
| CLOC | Municipio, localidad, nombre y tipo urbano/rural | XLS, MDB, TXT | Coincide en campos con el Excel de localidades aportado por el usuario; no trae sección |
| CLS | Localidad **con sección**, municipio y tipo | XLS, MDB, TXT | Resumen localidad→sección; EDMSLM agrega manzanas |
| CMZA | Entidad, distrito federal, municipio, sección, localidad, manzana y estatus | MDB, TXT | Subconjunto de campos de EDMSLM; útil para contrastar sus manzanas |
| CIGB | Mapas y cuadros agregados del marco geoelectoral | PDF | Contexto y conteos, sin cruce por casilla |
| CCOL | Colonia, tipo, CP, sección, municipio y distrito | XLS, MDB | Referencia colonia→sección; [auditoría de llaves](CCOL_COLONIAS.md) |
| CPC | Guía de productos cartográficos públicos | PDF | Índice de productos, no tabla de personas o casillas |

La ficha **CCOL** dice expresamente que la colonia es un rasgo *auxiliar* para ubicar domicilios y que el INE **no define oficialmente sus límites**. Por tanto, sus nombres y CP ayudan a buscar candidatos, pero no convierten una colonia en un polígono censal oficial ni identifican la casilla E de cada domicilio.

**Conclusión medida:** ninguna de estas 14 fichas anuncia un campo de casilla o una relación `manzana/localidad de residencia → E1/E2`. EDMSLM y CMZA dan la pieza territorial hasta **sección de enero de 2026**. El caso Viñedos muestra que unir esa sección sin correspondencia temporal a votos 2024 daría un cruce incorrecto. **NO VERIFICADO:** existencia de un corte 2024 descargable por otra vía, la equivalencia final de manzanas electorales 2026 con manzanas CPV 2020 y la conformación territorial por E de 2024.

**Siguiente uso concreto:** conseguir el catálogo EDMSLM/CMZA del corte aplicable a la jornada 2024 o una correspondencia oficial por manzana/localidad entre cortes; mientras tanto, comparar la lista de claves, no reasignar votos ni CPV. Para el diagnóstico actual conservar `B+C+E` por sección 2024 y el ECEG sólo en secciones de perímetro comparable; `S` permanece aparte.
