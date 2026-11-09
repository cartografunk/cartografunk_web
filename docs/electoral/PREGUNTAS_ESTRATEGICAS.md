# Preguntas del producto electoral

## Las cuatro preguntas de la presentación

1. **¿Dónde vas a ganar?** El resultado 2024 identifica ventajas y pérdidas observadas por casilla. El ensayo ML aún no permite afirmar ganadores futuros con confianza.
2. **¿Por qué?** El CPV 2020 describe rasgos asociados a las clases electorales en secciones comparables; **asociación, no causa**.
3. **¿Con qué grado de confiabilidad?** Se reportan error retrospectivo, cobertura territorial y casos indeterminados. Todavía no hay probabilidad de victoria prospectiva calibrada.
4. **¿Dónde vale la pena enfocar esfuerzos de campaña?** Se cruzan distancia en votos, abstención, apoyo mínimo, cobertura y costo supuesto para generar una lista de revisión, no un retorno garantizado.

El dashboard presenta una respuesta breve, cómo se obtuvo y un control para explorar cada pregunta. Los apartados siguientes desglosan las preguntas técnicas que alimentan esas cuatro respuestas.

**Pregunta central:** ¿Dónde vale la pena concentrar esfuerzos de campaña para un partido o candidatura, y qué tipo de esfuerzo tiene sentido en cada lugar?

La unidad de votos del diagnóstico local será la **casilla**; la sección agrupa las casillas y aporta el perfil CPV 2020 disponible. Querétaro es el filtro de la muestra, no una salida por estado. Las casillas especiales (S), que atienden electores en tránsito, se analizan aparte de las B/C/E residenciales. Si una extraordinaria (E) tiene asignación verificada de manzanas o localidades, podrá recibir un perfil CPV de su área de atención; su domicilio de instalación no es esa asignación.

## Primera capa: entender el patrón

1. ¿Dónde observamos apoyo alto, pérdida competitiva, crecimiento o volatilidad por **partido y casilla**?
2. ¿Qué variables CPV —edad, sexo, escolaridad, actividad económica y vivienda, entre otras— se asocian con esos resultados? ¿En qué dirección y con qué cobertura?
3. ¿La relación se mantiene al comparar años y lugares, o sólo describe una elección? Las B/C de una sección comparten CPV seccional, por lo que la validación debe mantener juntas sus casillas. El estado puede ayudar a separar patrones locales de un cambio electoral más amplio.

Estas preguntas describen **asociación, no causa**. El CPV cuenta residentes, no identifica cómo votó cada grupo. La importancia de una variable en un modelo no equivale a la eficacia de una intervención dirigida a ese grupo.

## Segunda capa: decidir dónde actuar

4. **¿Dónde vale la pena enfocar esfuerzo de campaña?** Para cada lugar, cruzar el diagnóstico anterior con: distancia en votos para ganar o conservar ventaja, abstención observada, apoyo mínimo observado, cambio entre elecciones, cobertura de datos, incertidumbre y costo supuesto por el usuario. Mostrar las dimensiones por separado antes de cualquier índice combinado.
5. ¿Qué nivel de esfuerzo probar? Una zona de apoyo alto y ventaja amplia puede ameritar presencia ligera; una pérdida cercana con electorado disponible puede ameritar trabajo intensivo; una pérdida lejana y costosa puede quedar para observación. Son **hipótesis de estrategia**, no efectos medidos de una visita, fotografía o inversión.
6. ¿Qué cambió después de intervenir? Registrar acción, fecha, lugar, costo y resultado posterior para estimar gradualmente qué tácticas producen votos adicionales. Sin esa comparación, los votos para ganar y el costo supuesto describen una oportunidad, no un retorno causal de campaña.

La rentabilidad ya calcula margen, faltante, votos para ganar y abstención. El **apoyo mínimo observado 2024** es el menor porcentaje del partido entre tres boletas federales del mismo año; no demuestra fidelidad individual ni histórica. Ambos entran como contexto de decisión después del diagnóstico CPV, sin aumentar artificialmente la importancia estadística de variables que provienen del mismo resultado electoral.

## Salida esperada

Por casilla o grupo territorial comparable: partido, resultado observado, 3–5 asociaciones CPV principales con dirección y cobertura, distancia electoral, apoyo mínimo cuando corresponda, costo supuesto y una acción sugerida como hipótesis. Los casos con geometría o datos insuficientes se señalan claramente. Las recomendaciones se revisan con resultados de campo antes de atribuirles eficacia.
