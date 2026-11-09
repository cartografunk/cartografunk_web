# Despliegue del MVP electoral

## Actualización visual, 2026-11-09

La rama `electoral-mvp` se actualizó en el commit `eede36f` con una portada
ejecutiva, navegación directa a las cuatro preguntas y un tema azul propio del
paquete. La primera pregunta dibuja las secciones 2024 por la **mediana del
margen partidario de sus casillas**; al seleccionar una sección, la tabla se
filtra y aparecen sus sedes puntuales. La selección de una casilla centra el
mapa y abre la ficha existente. Las secciones sin punto conservan su geometría.
El mapa usa calles de CARTO. Los números de la portada se calculan de los
Parquet incluidos; no proceden de las maquetas de 12ui.

Corrección del 2026-11-09: las **1 024 sedes del filtro aparecen desde que se
abre el mapa**, sobre la capa de secciones. «Sólo secciones» es una vista
opcional. El smoke test comprueba que la capa `sedes` contiene datos en la
vista inicial; una sede puede reunir varias casillas B/C/E.
La simbología vuelve a ser visual: cuadros de color para secciones y círculos
para sedes. Sus muestras de color salen de las mismas constantes que pintan el
mapa; la explicación larga debajo del selector se retiró.

Actualización del 2026-11-09: la simbología usa cinco colores de ColorBrewer
RdYlBu en orden azul → amarillo → rojo para ventaja amplia, ventaja estrecha,
empate, pérdida cercana y pérdida lejana. Las secciones y sedes comparten la
escala; el gris identifica falta de resultado. Los cortes seccionales del mapa
son los mismos 10 pp del diagnóstico por casilla. La pregunta 02 ofrece grupos
de las 15 tasas CPV y muestra las 15 en «Avanzado»; el [inventario completo del
ECEG](CPV_VARIABLES_2020.md) se audita aparte. La pregunta 04 recuperó el mapa
de sedes y secciones: seleccionar una fila centra el mapa y abre la ficha, y
seleccionar un punto abre su casilla inicial.

**Medido:** el paquete aislado contiene 58 archivos cotejados por SHA-256.
Su smoke test recorrió portada, boletas, enlace de la casilla `22-0272 B1` y
las cuatro preguntas sin excepciones. En la URL pública se observaron la
portada con 953 secciones, 3 081 casillas y 2 614 puntos de sede, y la capa
seccional del mapa. En navegador local, clic en polígono filtró la tabla a
`22-0987`; clic en `B1` centró la sede y abrió su ficha.

**NO VERIFICADO:** concurrencia, continuidad del servicio, probabilidad
electoral futura, eficacia de las acciones y precisión de cada sede en campo.
La suite completa de esta máquina se interrumpió en una prueba preexistente de
correlaciones (`test_estadisticas_fidelidad.py`) por un fallo nativo de NumPy
`0xc06d007f`; la prueba aislada de la interfaz y el smoke del paquete pasaron.

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
