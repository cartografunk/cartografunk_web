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
