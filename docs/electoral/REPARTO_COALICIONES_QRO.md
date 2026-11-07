# Reparto de votos de coaliciones y candidaturas comunes en Querétaro

## Fuentes descargadas y convertidas a Markdown

Se convirtió cada PDF con `scripts/pdf_to_md.py` antes de leerlo. Los PDF y las transcripciones Markdown son insumos locales sin commit en `data/electoral/fuentes_ieeq/`.

| Elección | Fuente | Markdown local | Regla revisada |
| --- | --- | --- | --- |
| 2021 | [Ley electoral 2020, compilación IEEQ a marzo de 2023](https://ieeq.mx/contenido/normatividad/leyes/_LEEQ-23MAR2023.pdf) | `ley_qro_2020_consolidada_2023.md` | Art. 144: una boleta válida cuenta una vez para la candidatura común; el reparto por partido sigue la regla general de coaliciones. La compilación es posterior a la elección y debe cotejarse con el texto vigente en 2021. |
| 2024 | [Ley electoral, compilación IEEQ marzo de 2024](https://ieeq.mx/contenido/normatividad/leyes/LEEQ-MAR2024.pdf) | `ley_qro_mar2024.md` | Art. 144: misma regla de candidatura común. |
| 2021 | [Lineamientos de cómputo IEEQ 2020–2021](https://ieeq.mx/contenido/convocatorias/archivos/AnxCG0804211100E-4.pdf) | `lineamientos_computo_ieeq_2021.md` | Arts. 161–163: reparto igualitario de las combinaciones; fracción para partido de mayor votación; empate por antigüedad de registro según orden de boleta; total posterior por candidatura. |
| 2024 | [Lineamientos de cómputo IEEQ 2023–2024](https://ieeq.mx/contenido/normatividad/lineamientos/Lineamientos%20para%20el%20desarrollo%20de%20las%20sesiones%20especiales%20de%20c%C3%B3mputos%20PEL%202023-2024.pdf) | `lineamientos_computo_ieeq_2024.md` | Arts. 164–166: misma regla; el sistema informático IEEQ hace el reparto. |
| 2018 | [Acuerdo IEEQ del 30 de agosto de 2017](https://ieeq.mx/contenido/cg/acuerdos/a_30_Ago_2017_6.pdf) | `lineamientos_computo_ieeq_2018_acuerdo.md` | Sus nueve páginas no tienen texto extraíble. Requiere OCR y cotejo visual; además falta el anexo operativo. |

Para 2018, la [transcripción institucional del TEPJF de la ley electoral de 2017](https://www.te.gob.mx/legislacion/media/files/abbe27ead60b791.htm) contiene en el **art. 142** la regla de un voto por boleta válida para la candidatura común y remite el reparto de partidos a las reglas generales de coaliciones. Es una fuente secundaria que debe cotejarse con la publicación oficial de 2017. El servidor del periódico oficial devolvió un error de certificado al intentar descargarla; no se omitió la validación TLS.

## Medido en los Parquet IEEQ

Los tres Parquet de casilla conservan columnas separadas para marcas de un partido y combinaciones de partidos. Se contaron **22 150** votos en columnas de combinación en 2018, **1 558** en 2021 y **45 563** en 2024. Estos son conteos de columnas, no totales por candidatura ni reparto por partido. Las columnas 2018 incluyen coaliciones y candidaturas comunes. Según el [IEEQ, en 2021 no se registraron coaliciones](https://ieeq.mx/comunicacion/boletines/2540): las combinaciones de ese año corresponden a candidaturas comunes.

## Alcance de la verificación

Para el liderazgo de una candidatura, cada marca individual de sus partidos y cada combinación que la postula aporta un voto; no se necesita repartir los votos entre partidos. El mapa de candidatura y columnas debe construirse por distrito y año, sin usar el distrito como salida del producto. El reparto por partido se usa para otro total, incluido el de representación proporcional. El redondeo de fracciones no debe hacerse por sección. `A_propios` sigue siendo experimental porque asigna sobrantes por sección.

**NO VERIFICADO:** texto operativo de los lineamientos 2018; versión exacta de la ley vigente en la jornada 2021; mapa candidatura-columna por distrito y año; reproducción exacta de los totales partidarios IEEQ por distrito para 2018, 2021 y 2024; asignación seccional del sobrante; tratamiento de votos nulos por marcas incompatibles. No se eleva el piso de partido a resultado oficial hasta cerrar estas pruebas.
