# Inventario de variables CPV por sección

Auditoría local del 9-nov-2026. El archivo completo `data/electoral/eceg_2020_seccion.parquet`, ya preparado para el explorador a partir de `eceg_2020_csv.zip`, contiene **68 806 secciones y 228 columnas**: 226 columnas del CSV oficial y dos llaves normalizadas. Su diccionario clasifica los 226 campos en población, educación, vivienda, economía, salud, migración, discapacidad y otros temas. El Parquet compacto que usa el diagnóstico electoral conserva sólo `ID_SECCION` y **15 tasas elegidas inicialmente**.

`python -B -m scripts.audit_eceg_cpv_qro` reproduce el inventario para las **788 secciones de Querétaro con CPV comparable** y deja, sin versionar, `data/electoral/ieeq_local/auditoria_variables_eceg_2020.csv`. Reporta cobertura, variación y, para doce tasas candidatas con denominador explícito, cobertura de tasa válida y máxima correlación absoluta con cualquiera de las 15 tasas actuales. La correlación sirve para detectar redundancia; no mide relación con el voto ni causalidad.

| Grupo y tasa candidata | Cobertura en 788 secciones | Mayor correlación con las 15 actuales | Decisión inicial |
| --- | ---: | ---: | --- |
| Discapacidad / población total | 99.87 % | 0.373 | Priorizar para contraste |
| Bicicleta / viviendas habitadas | 99.87 % | 0.255 | Priorizar para contraste |
| Motocicleta / viviendas habitadas | 99.87 % | 0.448 | Priorizar para contraste |
| Viviendas de un cuarto / viviendas habitadas | 99.87 % | 0.543 | Priorizar para contraste |
| PEA masculina / hombres de 12+ | 99.87 % | 0.625 | Revisar junto con PEA total |
| Sin electricidad / viviendas habitadas | 99.87 % | 0.659 | Revisar distribución: mediana 0.14 % |
| Afiliación IMSS / población total | 99.87 % | 0.810 | Revisar redundancia y definición |
| Secundaria completa / personas de 15+ | 99.87 % | 0.852 | Revisar redundancia |
| Nació en otra entidad / población total | 99.87 % | 0.909 | Evitar duplicar señal sin examen |
| PEA femenina / mujeres de 12+ | 99.87 % | 0.942 | Evitar duplicar señal sin examen |
| Computadora / viviendas habitadas | 98.48 % | 0.977 | Redundante con rasgos actuales |
| Celular / viviendas habitadas | 75.25 % | 0.786 | Cobertura menor; no priorizar |

La pregunta 02 del dashboard agrupa las 15 tasas actuales para explorar temas y muestra las cinco diferencias mayores del grupo elegido; el detalle de las 15 está en «Avanzado». El resultado varía por partido porque la clase de cada casilla se recalcula para ese partido. **Pregunta 02 es un contraste descriptivo.** El ensayo de ML con CPV usó las 15 tasas compactas, no los 226 campos; se resume en la pregunta 03. Estas doce candidatas aún no entran al ML ni deben interpretarse como factores causales. Antes de añadir cada grupo al perfil, contrastar su definición en el diccionario ECEG, su distribución, redundancia y cobertura por partido y clase. CPV 2020 vs votos 2024 · asociación, no causa.
