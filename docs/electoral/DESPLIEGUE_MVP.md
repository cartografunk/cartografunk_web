# Despliegue del MVP electoral

**App:** https://cartografunk-electoral.streamlit.app/

**Código y datos derivados:** `cartografunk/cartografunk-streamlit`, rama `electoral-mvp`, commit `0dd9060`.

**Entrada:** `electoral/dashboard_app.py`; Python 3.12; Streamlit 1.66.1. La rama `main` del explorador público permanece independiente.

El paquete se generó desde `demo-tres-elecciones` con:

```powershell
D:\Conda\envs\cartografunk\python.exe -B scripts/package_electoral_mvp.py C:\cartografunk_electoral_mvp_20261108
D:\Conda\envs\cartografunk\python.exe -B scripts/smoke_electoral_mvp.py C:\cartografunk_electoral_mvp_20261108
```

Contiene 56 archivos verificados por SHA-256 (`manifest.json`), 2 680 403 bytes en total. Los Parquet nacionales de resultados y geometría se recortaron a Querétaro. El **Parquet nacional CPV 2020 y los ZIP de origen no se subieron**. El diagnóstico usa el derivado seccional preparado del piloto, que conserva sólo las variables necesarias para la demo. La rama de despliegue es pública: esos datos derivados son accesibles desde GitHub.

**Medido:** 134 pruebas electorales aprobadas. El smoke test del paquete aislado abrió ambas pestañas, enlazó la casilla `22-0272 B1` con su sede y recorrió las cuatro preguntas sin excepciones. En Streamlit Cloud se verificó la misma interacción y que cargan los bloques de CPV, confianza y esfuerzo; el bloque de confianza muestra 788/953 secciones comparables y 73.7 % de lista nominal.

**NO VERIFICADO:** disponibilidad continua del servicio durante la presentación; rendimiento con asistentes simultáneos; precisión física de todas las sedes en campo; causalidad de los perfiles CPV; probabilidad de victoria futura y retorno de campaña. El reparto de coaliciones sigue siendo experimental. La diferencia del flotante de Ayuntamiento 2024 compara marcas de boleta, no candidaturas.
