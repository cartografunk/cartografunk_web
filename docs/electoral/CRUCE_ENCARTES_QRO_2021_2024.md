# Encartes 2021→2024 para 81 secciones nuevas de Querétaro

Fecha: 2026-11-07. Objetivo: buscar la sección 2021 antecedente de las 81 secciones 2024 que no comparten clave con ECEG 2020. La unidad sigue siendo **sección**. El encarte aporta domicilio de casilla, municipio y localidad de instalación; la superposición de polígonos aporta una segunda pista. No se infiere que las mismas personas hayan votado en ambas casillas.

## Fuentes y extracción

| Año | Encarte oficial | SHA-256 PDF | Casillas extraídas | Claves seccionales cotejadas con votos |
| --- | --- | --- | ---: | ---: |
| 2021 | [IEEQ, encarte generado el 5-jun-2021](https://pel.eleccionesqro.mx/2020-2021/assets/archivos/casillas/ubicacionMesasDirectivasJL.pdf) | `6955cb2ef3e5d735b222d0471fd9f2ec94b6f48b519ae81b5ea105c5b4d4e660` | 2 853 | 891/891 |
| 2024 | [IEEQ, encarte generado el 30-may-2024](https://ieeq.mx/contenido/difusion/2024/Encarte_30052024.pdf) | `2bbe1fe5272b4641380b85ac314df05f7c5c59cbd64af57b5112e5b5c13e7645` | 3 138 | 953/953 |

Ambos PDF se convirtieron a Markdown con `scripts/pdf_to_md.py --preserve-stream-order` antes de leerlos. `scripts/match_ieeq_encartes.py` extrae sólo sección, tipo de casilla, municipio, localidad, domicilio y página; no guarda nombres de funcionarios. El PDF 2021 tiene 26 entradas cuyo domicilio no quedó completo en el texto extraído, aunque sí su sección, casilla y localidad. Sus claves seccionales coinciden por completo con el Parquet de votos 2021; lo mismo ocurre en 2024.

Control adicional del parser: el código de municipio de las **2 853 casillas** extraídas de 2021 coincide con la tabla ECEG de su sección; el de las **3 138 casillas** de 2024 coincide con el marco seccional 2024. No hay sección del encarte asignada a dos municipios en ninguno de los dos años.

## Resultado medido

Para las **81 secciones 2024 sin clave ECEG** se obtuvieron **92 enlaces de polígono** hacia secciones 2021. Cada una tiene al menos un candidato de origen. Los encartes aportan evidencia adicional así:

- **8 secciones**: mismo domicilio normalizado en los dos encartes y superposición territorial.
- **69 adicionales**: mismo municipio y localidad del encarte, más superposición territorial; el domicilio no coincide exactamente. Esto permite investigar cambios de escuela o de redacción sin asumir que el edificio sea el mismo.
- **4 secciones** (`22-0947`, `22-0948`, `22-0959`, `22-0966`): cambió también la localidad consignada; por ahora sólo las conecta la geometría. Son zonas de Santa María Begoña y Zákia, con antecedentes geométricos en `22-0195` y, para algunas, `22-0202`.

**72** destinos tienen un solo origen geométrico y **9** varios. **75** destinos tienen un origen que cubre al menos 95 % de su superficie 2024; esto describe área, no población ni votos. Ejemplo sólido: `22-0969` conserva un domicilio de casilla de `22-0066` y su polígono está totalmente dentro de ese antecedente. Ejemplo mixto: `22-0966` se superpone aproximadamente 60 % con `22-0195` y 40 % con `22-0202`; una sola localidad o escuela no resolvería ese reparto.

La revisión sección por sección está en el CSV local `data/electoral/ieeq_local/encarte_2021_2024_81_enlaces.csv` (92 enlaces, tipo de evidencia, fracción territorial y páginas de ambos encartes). `encarte_2021_2024_81_candidatos.csv` conserva todos los candidatos por localidad para auditoría; las localidades urbanas generan miles de pares ambiguos, por lo que **no** se usan solas como correspondencia final. Los archivos PDF, Markdown, CSV y Parquet derivados son locales y no se versionan.

## Límite práctico

El cruce rescata **candidatos de correspondencia** para las 81 secciones, no transforma automáticamente sus votos 2021 en votos de 2024. Cuando una sección se divide, hay que repartir la población o el padrón anterior entre destinos con una tabla oficial por manzana/localidad o con una aproximación documentada y su incertidumbre. El domicilio de instalación puede cambiar sin que cambie la residencia; por eso el encarte verifica la pista, no el flujo de electores. Los 84 casos que conservaron clave ECEG pero cambiaron geometría siguen como grupo separado.

## Clave, distrito y domicilio: auditoría separada

`scripts/audit_ieeq_cambios_2021_2024.py` cruza las claves de resultados B/C/E, el distrito local de esos resultados, los domicilios normalizados de ambos encartes y el crosswalk geométrico. Deja el detalle local en `auditoria_clave_distrito_domicilio_2021_2024.csv` y el resumen en el JSON homónimo. Para una sección nueva, el origen de referencia es el polígono 2021 que ocupa la mayor fracción de su superficie 2024; esta elección **no** equivale al origen de su padrón o sus votos.

| Cambio 2021→2024 | Medición |
| --- | ---: |
| Secciones 2021 / 2024 | 891 / 953 |
| Claves conservadas / desaparecidas / nuevas | 872 / 19 / 81 |
| Claves conservadas cuyo distrito **local** cambió | 532 de 872 |
| Nuevas cuyo origen territorial dominante cambió de distrito local | 61 de 81 |
| Nuevas cuyo origen territorial dominante quedó en el mismo distrito local | 20 de 81 |
| Claves conservadas con algún domicilio textual idéntico / sin uno idéntico | 453 / 419 |
| Nuevas con domicilio textual idéntico al origen dominante | 8 de 81 |
| Enlaces territoriales desaparecida→nueva / conservada→nueva / desaparecida→conservada | 84 / 8 / 4 |

Las **19 claves desaparecidas** son `22-0066`, `22-0083`, `22-0092`, `22-0116`, `22-0120`, `22-0121`, `22-0147`, `22-0190`, `22-0195`, `22-0214`, `22-0278`, `22-0404`, `22-0491`, `22-0552`, `22-0565`, `22-0585`, `22-0627`, `22-0632` y `22-0685`. Todas las 81 nuevas tienen al menos un vínculo territorial con una de esas 19, aunque una nueva (`22-0910`) tiene como origen dominante una clave que sobrevivió (`22-0898`, 50.16 % de su área). Hay relaciones de uno a varios y de varios a uno.

**Interpretación:** cambiar de distrito local no implica que desaparezca la sección: 532 conservaron su clave. Tampoco todo nacimiento se explica por un cambio de distrito: 20 nuevas quedan en el distrito local de su origen territorial dominante. El encarte documenta el domicilio de instalación de casillas; que dos textos no coincidan **no verifica** una mudanza física, ni permite asignar a las personas del padrón previo. La causa administrativa de cada baja o alta y la distribución oficial por manzana/localidad siguen **NO VERIFICADAS**. La [descripción del SIGE del INE](https://cartografia.ine.mx/sige8/) distingue las modificaciones al marco por reseccionamiento e integración seccional; el [procedimiento de reseccionamiento 2023](https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/151683/cnv-so05-2023-05-11-acuerdo12-anexo1.pdf) describe subdivisión de secciones. El programa 2023–2024 se incorporaría después de la jornada, como se detalla en [fuentes](RESECCIONAMIENTO_FUENTES.md).
