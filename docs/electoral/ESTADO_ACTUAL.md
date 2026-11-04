# Estado actual del módulo electoral

Actualizado: 2026-11-04. Fuente principal: código y pruebas de esta rama. Las cifras de inventario históricas conservan sus fuentes en [DATOS.md](DATOS.md) y [PENDIENTES.md](PENDIENTES.md).

## Rama y aplicaciones

| Elemento | Estado comprobado |
| --- | --- |
| Rama de trabajo | `demo-tres-elecciones`, derivada de `demo-11am` (`31464db`) y publicada como `origin/demo-tres-elecciones`. |
| Respaldos locales | `respaldo-antes-noche` apunta a `ab5b4ea`; `demo-11am`, `demo-11am-b` y `demo-11am-c` conservan sus commits originales. No se publicaron esas etiquetas. |
| App vigente para el demo | `electoral/app_simple.py`: selector de Presidencia, Diputaciones MR y Senadurías MR de 2024; candidatura activa, mapa, clases, aportes de partidos de coalición, priorización y apoyo mínimo. |
| App anterior | `electoral/demo_app.py`: demo de Presidencia 2024. |
| Archivos de datos | `data/electoral/*.parquet`, generados localmente y no versionados; los ZIP de origen se indican en `electoral/config.py`. |

Los cambios funcionales de `demo-11am-b` (controles técnicos en «Avanzado») y `demo-11am-c` (costo inicial vacío, persistencia por sesión, tabla legible, Querétaro por omisión) se integraron en la app vigente. El ámbito de apoyo mínimo permanece visible, según la corrección posterior a `demo-11am-b`. Las ramas y etiquetas de respaldo no se borraron.

## Cálculos que muestra la app

- El resultado, la clase, el margen, el faltante y los votos para ganar pertenecen a la **candidatura** seleccionada. En Diputaciones y Senadurías, las candidaturas activas varían por distrito; una sección sin la candidatura elegida queda sin clase para ella. Véanse `electoral/analisis_demo.py`, `electoral/candidaturas.py` y `electoral/rentabilidad.py`.
- El selector de partidos aparece junto al de candidatura cuando se elige una coalición. Los votos atribuidos y porcentajes por sección y estado usan `repartir_coalicion(..., variante="A_propios")`. Es un reparto **experimental**; la regla oficial sigue NO VERIFICADA.
- «Apoyo mínimo observado 2024» compara las tres boletas del mismo año. Sus clases son una propuesta provisional; no mide personas ni continuidad entre años. Véanse `electoral/fidelidad.py` y `electoral/estadisticas_fidelidad.py`.
- El simulador espera un costo ingresado por el usuario antes de calcular. Conserva costos y descartes por sesión y los rotula como «supuesto del usuario» en el Excel.
- El Censo de Población y Vivienda no está integrado en esta app. La equivalencia territorial INE–INEGI sigue NO VERIFICADA.

## Validación de esta integración

Ejecutado desde `C:\cartografunk_web` con `D:\Conda\envs\cartografunk\python.exe`:

```powershell
$env:PATH='D:\Conda\envs\cartografunk\Library\bin;'+$env:PATH
D:\Conda\envs\cartografunk\python.exe -B -m pytest electoral/tests -q
```

Resultado: **67 aprobadas, 0 omitidas**, 2 advertencias de GDAL. AppTest con `timeout=180`: **0 excepciones** en Presidencia/PVEM-PT-MORENA/estado 14, Diputaciones MR/PAN-PRI-PRD/estado 9 y Senadurías MR/MC/estado 14; tiempos medidos 32.03 s, 9.98 s y 10.47 s, respectivamente. El aspecto en navegador y el arranque del servidor: **NO VERIFICADO**.

## Acceso entre cuentas

Esta documentación se comparte mediante `origin/demo-tres-elecciones`. No existe un `.mcp.json` en el repositorio. Los Parquet locales y las rutas `D:\` no se comparten por Git; su acceso desde otras cuentas o máquinas es **NO VERIFICADO**. No se ha implementado un servidor MCP para esos datos.
