# Presentación del dashboard electoral · Querétaro 2024

## Arranque local

Desde `C:\cartografunk_web`:

```powershell
$env:PATH='D:\Conda\envs\cartografunk\Library\bin;'+$env:PATH
D:\Conda\envs\cartografunk\python.exe -B -m streamlit run electoral/dashboard_app.py --server.port 8502
```

Abrir `http://127.0.0.1:8502`. Requiere los Parquet locales del piloto, incluidos votos IEEQ, cruce CPV, sedes puntuales y benchmark; el código se versiona, esos datos no. Si faltan sedes, el mapa lo indica y la tabla sigue mostrando resultados por casilla.

## Recorrido breve

1. **¿Dónde vas a ganar?** Cambiar de partido y alternar «Todas», «Cercanas» y «Fortalezas». El mapa agrupa casillas que comparten sede; al elegir una fila o punto se abre la ficha con sección y domicilio de instalación. Aclarar que son **resultados observados en 2024**, no una victoria futura predicha.
2. **¿Por qué?** Comparar «Pérdida cercana» con «Pérdida lejana» y luego «Victoria sólida». Enseñar las cinco diferencias CPV, sus promedios y tres frases de lectura. Decir **CPV 2020 vs votos 2024; asociación, no causa**.
3. **¿Con qué grado de confiabilidad?** Mostrar error medio de persistencia y Ridge para el partido elegido, 788/953 secciones comparables y 73.66 % de lista nominal cubierta. Decir que es **prueba retrospectiva**, sin probabilidad prospectiva calibrada.
4. **¿Dónde enfocar esfuerzo?** Filtrar motivo, buscar sección o casilla, abrir ficha y, si interesa, introducir costo y presupuesto supuestos. La lista propone **casos para revisión de campo**; no mide votos captables ni retorno.

El desglose técnico queda en «Cómo llegamos a esta respuesta» y «Fuentes y límites del diagnóstico». Para una demostración fluida, mantener Querétaro y abrir primero la entrada directa. El piloto no muestra resultados agregados por estado ni municipio.
