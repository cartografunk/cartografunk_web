# Presentación del dashboard electoral · Querétaro 2024

## Arranque local

Desde `C:\cartografunk_web`:

```powershell
$env:PATH='D:\Conda\envs\cartografunk\Library\bin;'+$env:PATH
D:\Conda\envs\cartografunk\python.exe -B -m streamlit run electoral/dashboard_app.py --server.port 8502
```

Abrir `http://127.0.0.1:8502`. Requiere los Parquet locales del piloto, incluidos votos IEEQ, cruce CPV, sedes puntuales y benchmark; el código se versiona, esos datos no. Si faltan sedes, el mapa lo indica y la tabla sigue mostrando resultados por casilla.

La primera pestaña, **Boletas y apoyo mínimo**, cubre ayuntamientos 2018/2021/2024, gubernatura 2021 y Senado 2024. Para reconstruir sus Parquet locales: `D:\Conda\envs\cartografunk\python.exe -B scripts/build_ieeq_boletas.py`. Permite elegir cargo, año, municipio cuando corresponde y cualquier opción de voto. **La casilla permanece como unidad principal de voto** para las cuatro boletas locales: Ayuntamiento 2024 muestra tabla y mapa de sedes enlazados (fila → zoom y marca; punto → fila marcada); Ayuntamiento 2018/2021 y Gubernatura 2021 conservan la tabla de casillas sin trasladarles sedes de 2024. Senado 2024 sólo está cargado por sección. En 2024 destaca el mínimo de marca directa al mismo partido entre cinco boletas: Ayuntamiento, Senado, Presidencia y diputaciones federal y local, sección por sección. Las combinaciones de coalición se conservan como opciones distintas. El mínimo no demuestra que votaron las mismas personas independientemente de la candidatura.

La segunda pestaña, **Cuatro preguntas · piloto diputaciones**, conserva el prototipo con diputaciones locales 2024. No debe presentarse como pronóstico específico para la futura gubernatura ni la presidencia municipal. Para la demo de Agustín Dorantes, mostrar Ayuntamiento de Querétaro como contexto del cargo y Senado 2024 como antecedente separado; para Felifer, Gubernatura 2021 como contexto del cargo y Ayuntamiento 2024 como antecedente separado. La plataforma permite explorar las demás candidaturas y municipios; estos nombres son ejemplos de recorrido, no filtros fijos ni atribución de votos futuros.

## Recorrido breve

1. **¿Dónde vas a ganar?** Cambiar de partido y alternar «Todas», «Cercanas» y «Fortalezas». El mapa agrupa casillas que comparten sede; al elegir una fila o punto se abre la ficha con sección y domicilio de instalación. Aclarar que son **resultados observados en 2024**, no una victoria futura predicha.
2. **¿Por qué?** Comparar «Pérdida cercana» con «Pérdida lejana» y luego «Victoria sólida». Enseñar las cinco diferencias CPV, sus promedios y tres frases de lectura. Decir **CPV 2020 vs votos 2024; asociación, no causa**.
3. **¿Con qué grado de confiabilidad?** Mostrar error medio de persistencia y Ridge para el partido elegido, 788/953 secciones comparables y 73.66 % de lista nominal cubierta. Decir que es **prueba retrospectiva**, sin probabilidad prospectiva calibrada.
4. **¿Dónde enfocar esfuerzo?** Filtrar motivo, buscar sección o casilla, abrir ficha y, si interesa, introducir costo y presupuesto supuestos. La lista propone **casos para revisión de campo**; no mide votos captables ni retorno.

El desglose técnico queda en «Cómo llegamos a esta respuesta» y «Fuentes y límites del diagnóstico». Para una demostración fluida, mantener Querétaro y abrir primero la entrada directa. El piloto no muestra resultados agregados por estado ni municipio.
