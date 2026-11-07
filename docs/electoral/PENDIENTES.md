# Pendientes activos del producto electoral

Actualizado: 2026-11-07. Los detalles y verificaciones anteriores quedan en [el archivo histórico](PENDIENTES_HISTORICO.md); los resultados medidos están en [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md) y [DATOS.md](DATOS.md).

1. **Forecast útil por partido.** El ensayo de Querétaro aún no detecta liderazgo con fiabilidad. Incorporar CPV como predictor, probar escenarios de cambio y evaluar fuera de tiempo y en otras entidades antes de mostrar confianza prospectiva. La comparación de secciones reconfiguradas funciona por grupo, no por cada sección hija.
2. **Comparabilidad territorial.** En Querétaro, 165 de 953 secciones 2024 no tienen perímetro comparable con ECEG y no reciben CPV en el diagnóstico por casilla. Extender la revisión geométrica a las otras entidades; buscar la correspondencia final de reseccionamientos cuando se necesite resolver secciones hijas.
3. **Datos por casilla.** El JSON IEEQ ya resolvió las 77 claves aparentes repetidas de casillas E: eran contiguas de extraordinaria con número omitido en el CSV. Aún falta el área de atención por manzana/localidad para dar a cada E un CPV propio; hasta entonces usa CPV de sección. Las S siguen separadas porque no identifican residencia.
4. **Partidos y resultados.** Contrastar la atribución fraccionaria de marcas de coalición con la regla y el cómputo legal. Aclarar el voto de diferencia distrital 2018 y la versión jurídica final de resultados 2024. Conservar las advertencias de fuente mientras tanto.
5. **Decisión de campaña.** Probar si las asociaciones CPV se repiten en otras elecciones. Registrar acción, lugar, fecha, costo y resultado posterior para medir efecto y retorno; la sugerencia y el costo actuales son sólo hipótesis. El apoyo mínimo 2024 no es fidelidad individual ni histórica.

**NO VERIFICADO:** área propia de las E, reasignación individual de votantes en reseccionamientos, equivalencia territorial nacional ECEG–2024, reparto legal exacto de coaliciones y eficacia de intervenciones. Ninguno impide mostrar el diagnóstico descriptivo con su cobertura.
