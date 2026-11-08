# Catálogo EDMSLM del SIGE: localidad y manzana por sección

Auditoría local del 2026-11-07 de los archivos aportados por el usuario:

- `C:\Users\HeyCe\Downloads\Catalogodeinformaciongeoelectoral(EDMSLM).txt`: 2 697 642 filas nacionales, delimitadas por `|`. [SIGE](https://cartografia.ine.mx/sige8/productosCartograficos/catalogos) indica **corte enero de 2026**. Campos: `ENTIDAD`, `DISTRITO`, `MUNICIPIO`, `NOMBRE_MUNICIPIO`, `SECCION`, `TIPO_SECCION`, `TIPO_NOMBRE`, `LOCALIDAD`, `NOMBRE_LOCALIDAD`, `TIPO_LOCALIDAD`, `TIPO_NOMBRE_LOCALIDAD`, `MANZANA`, `STATUS`. El sitio define `C` como manzana habilitada y `*` como inhabilitada.
- `C:\Users\HeyCe\Downloads\Catálogo de Localidades.xlsx`: 1 968 localidades de Querétaro con entidad, municipio, localidad, nombre y tipo; no trae sección, manzana ni casilla. El CLOC del SIGE también indica corte enero de 2026.
- El TXT tiene para Querétaro 59 157 filas, 1 090 secciones, 1 968 pares municipio–localidad y 2 735 pares localidad–sección. **Sí da la relación localidad/manzana INE → sección de su propio corte**, incluso para localidades urbanas como `FRACCIONAMIENTO VIÑEDOS` (municipio 14, localidad 173).

## Prueba de cambio de corte: Viñedos

El encarte IEEQ 2024 local (`encarte_qro_2024_claves.parquet`) registra las casillas E instaladas en `FRACCIONAMIENTO VIÑEDOS` como `22-0553`, municipio 14, localidad 173. En el EDMSLM **enero 2026** aportado, esa localidad aparece en las secciones `22-0999`, `22-1002`, `22-1003` y `22-1004`; la sección `22-0553` no aparece en ninguna fila de Querétaro. **La identidad de municipio y localidad no autoriza asignar esas manzanas a la sección electoral 2024**. La correspondencia territorial exacta 0553→secciones posteriores sigue **NO VERIFICADA**.

## Uso correcto y límite

1. Usar EDMSLM como catálogo de referencia para identificar localidades y manzanas electorales y detectar cambios entre cortes. Conservar `ENTIDAD + MUNICIPIO + LOCALIDAD + MANZANA + SECCION`; no unir por nombre solamente.
2. Obtener el corte vigente en la elección 2024 o una correspondencia final de manzanas/localidades entre cortes antes de atribuirle el EDMSLM actual a los votos de esa elección.
3. El TXT **no tiene columna de casilla B/C/E** ni enumera la población de residencia asignada a cada E. El Excel tampoco. Relaciona manzana/localidad con sección de su corte, no con casilla extraordinaria.
4. La clave `MANZANA` electoral no incluye `AGEB`; el `CVEGEO` de manzana censal INEGI sí. La equivalencia entre ambas claves de manzana sigue **NO VERIFICADA** y requiere cotejo cartográfico/catálogo, no concatenación directa.

**Decisión actual:** mantener el ECEG por sección comparable como base de la app. Este catálogo aporta una pieza para investigar reseccionamiento y un piloto por localidad; no se ha usado para reasignar votos ni CPV a casillas E.

La [revisión de los 14 catálogos del SIGE](SIGE_CATALOGOS.md) distingue qué campos agrega cada producto y confirma que ninguno documenta la conformación de casillas E.
