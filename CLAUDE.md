# Cartografunk electoral

Lee [docs/electoral/ESTADO_ACTUAL.md](docs/electoral/ESTADO_ACTUAL.md) antes de cambiar el módulo electoral. Las definiciones y fuentes están en [METODOLOGIA.md](docs/electoral/METODOLOGIA.md), [DATOS.md](docs/electoral/DATOS.md) y [PENDIENTES.md](docs/electoral/PENDIENTES.md).

- Rama de trabajo electoral: `demo-tres-elecciones`. Las etiquetas `demo-11am`, `demo-11am-b`, `demo-11am-c` y `respaldo-antes-noche` son respaldos; no las muevas.
- App actual: `electoral/app_simple.py`. `electoral/demo_app.py` es un demo anterior de Presidencia.
- Conserva las columnas originales y las reglas de cálculo verificadas por las pruebas. El reparto `A_propios` es experimental, no una regla oficial confirmada.
- Los Parquet en `data/electoral/` y los ZIP de origen son datos locales; comprueba su disponibilidad antes de ejecutar la app. No los agregues a commits.
- Prueba con `D:\Conda\envs\cartografunk\python.exe -B -m pytest electoral/tests -q` y, al cambiar la interfaz, con `streamlit.testing.v1.AppTest` usando `timeout=180`.
- Reporta por separado lo medido y lo NO VERIFICADO. No presentes el apoyo mínimo de 2024 como seguimiento de personas ni como fidelidad histórica.
