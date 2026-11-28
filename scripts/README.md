# Pipeline local de grupos, mensajes y Google Calendar

**Estado:** propuesta. Las migraciones de esta entrega no están aplicadas y no se ejecutó ningún script contra producción. La primera corrida real corresponde a una persona del equipo. `out/` y `fixtures/private/` están ignorados por Git. No copies allí datos reales si compartes el directorio fuera del equipo.

## Orden de trabajo

1. Revisar las siete migraciones propuestas, **no aplicadas**, de `supabase/migrations/`: `20261127_endurecimiento.sql`, `20261127_pipeline_campos.sql`, `20261127_sesiones.sql`, `20261127150000_registro_no_sobrescribe.sql`, `20261127150100_crm_pago_confirmacion.sql`, `20261127170000_comprobantes_curso.sql` y `20261127180000_votacion_tras_pago.sql`. `crm_pago_confirmacion` es autocontenida y puede ir antes o después de `pipeline_campos`, pero el equipo debe elegir un orden deliberado: varias migraciones del 20261127 comparten el prefijo de ocho dígitos. `comprobantes_curso` requiere las funciones CRM previas y debe revisarse junto con la configuración de Storage. Revisar también el impacto de permisos/políticas antes de aplicar. `inscripciones` no tiene su `CREATE TABLE` base en este repo, así que la verificación final de RLS y grants debe hacerse en Supabase por una persona autorizada. No ejecutar la migración de endurecimiento sin revisar si otro cliente depende de esas políticas.
2. Actualizar qué inscripciones están `inscrito` o `pagado`. Los anticipos del curso de IA se registran mediante `20261127170000_comprobantes_curso.sql`: cada persona sube su comprobante en `/pago` con enlace individual, y el equipo verifica la transferencia desde `/crm`. Para precio completo, un total **verificado de al menos $450** aparta el lugar. Para una beca aprobada, se verifica el monto positivo que propuso la persona antes de abrir la votación. El saldo del precio completo debe cubrirse antes de la última sesión; los acuerdos de pago se documentan en las notas de seguimiento. La aprobación de beca usa `crm_marcar_pago_beca` desde el panel; la confirmación manual de grupo sigue usando `crm_confirmar_grupo`. Aceptar el precio **no equivale** a pagar.
3. Ejecutar el agrupador con votos reales solo cuando el equipo decida hacerlo. Revisar `out/propuesta-grupos.json` y `out/propuesta-grupos.txt`. El criterio es **menos días distintos, luego menos grupos**, siempre que alcance la cobertura objetivo. Si no se alcanza, muestra la máxima cobertura posible. `--cupo` es opcional; sin él no hay límite por grupo.
4. Revisar con cada persona la propuesta por WhatsApp. El script de mensajes solo crea texto y enlaces; nunca envía mensajes. Los archivos con teléfonos y textos van a `out/`.
5. Preparar a mano un `grupos-confirmados.json` con bloque, **tres fechas explícitas** y IDs revisados. No se infieren fechas. Usa un identificador de grupo único por edición del curso para evitar choques con eventos anteriores. `confirmado: false` crea el título con **Pendiente**. Cámbialo a `true` solo tras confirmación manual por el equipo; una nueva corrida quita esa marca. La respuesta RSVP de Meet no se usa como métrica ni como confirmación.
6. Ejecutar invitaciones solo para inscripciones con `pago_comprobado` respaldado por transferencias verificadas. Google Calendar envía correo y un Meet propio por sesión únicamente con `--apply`. El equipo debe revisar la vista previa y los destinatarios antes de usar esa bandera.

Revisión estática de seguridad: la migración original de `crm_disponibilidad` habilita RLS y revoca permisos directos; la v1 `guardar_horarios(uuid,text[],text)` **sí existe** como wrapper público en `20261127_encuesta_horarios_v2.sql`, por eso la propuesta la elimina. `ver_horarios` en ese mismo archivo devuelve solo `curso`, `opciones`, `sin_bloques`, `comentario` y `respondio_at`, usa `security definer` con `search_path=''` y filtra los mismos cuatro estatus que `guardar_horarios_v2`. El estado efectivo de RLS, grants y políticas de `inscripciones` en producción **no se verificó** por la regla de no ejecutar contra producción.

## Formato de datos

`--input` lee un JSON local con `inscripciones[]`. Cada fila requiere `id`, `estatus` y `disponibilidad: {opciones, sin_bloques, respondio_at}` para grupos. Mensajes añaden `nombre`, `whatsapp`, `respuestas.solicita_beca`; invitaciones requieren `email` y `pago_comprobado`. Consulta `fixtures/pipeline.json` para un ejemplo sin contactos. No commitear archivos con contactos.

Para leer Supabase se usa `--supabase --apply`, `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en variables de entorno. La llave nunca se imprime. El lector selecciona las columnas de la migración propuesta; fallará hasta que una persona la aplique. No usar la llave de servicio en el navegador ni en el repo.

### Anticipo y comprobante

`20261127170000_comprobantes_curso.sql`, la función Edge `comprobante-curso` y la página `/pago` son propuestas **no desplegadas**. El bucket es privado. El formulario acepta JPG, PNG o PDF de hasta 5 MB, conserva el archivo y monto como **pendientes** y no aparta el lugar automáticamente. El equipo compara la transferencia con el comprobante y registra una nota al aprobar o rechazar; la acción queda en `crm_actividades`. Para el curso de $1,500, el anticipo cubierto empieza en $450 y el saldo mostrado se calcula solo con pagos verificados. Para una beca aprobada de $1 a $1,499, el costo y saldo del enlace privado son el monto propuesto. La aprobación no equivale a pago: primero se verifica el comprobante. El CRM solo prepara enlaces para precio completo o becas aprobadas.

Configurar `CARTOFUNK_TRANSFER_ACCOUNT` como secreto de la función Edge y como variable local cuando se generen mensajes desde `scripts/mensajes`. No escribir el número de transferencia en Git. La primera plantilla necesita `{{enlace_pago}}` por persona, que se obtiene con el botón **Copiar mensaje de anticipo** del CRM tras desplegar la migración y la función. Hasta entonces, ese botón y el formulario no están disponibles en producción. El enlace lleva un token aleatorio en el fragmento `#` y debe enviarse solo a la persona correspondiente. Antes de desplegar, revisar las políticas existentes de Storage y probar el flujo completo en un entorno de prueba.

## Comandos de vista previa

Desde la raíz del repositorio:

```powershell
node --test scripts/pipeline/pipeline.test.mjs
node scripts/grupos/index.mjs --input fixtures/pipeline.json
node scripts/mensajes/index.mjs --input fixtures/pipeline.json --tipo primer-contacto --plazo "fecha revisada por el equipo"
node scripts/invitaciones/index.mjs --input fixtures/pipeline.json --confirmados fixtures/grupos-confirmados.json
```

Grupos admite `--max-grupos` (1 a 5; por defecto 4), `--cupo` (por defecto ilimitado), `--cobertura-objetivo` (0 a 1; por defecto 0.85) y `--incluir-contactados`. Por defecto solo toma `inscrito` y `pagado`. La tabla Pareto muestra la mayor cobertura con **hasta** 1, 2, …, 7 días. Los votos después del 29 de noviembre de 2026 a las 20:00 CDMX se marcan como tardíos.

Mensajes admite `--tipo primer-contacto|beca|beca-aprobada|votacion|grupo|sesion|recordatorio-24h|recordatorio-1h`. La votación solo se prepara para pagos verificados; la beca aprobada requiere aporte positivo. Para textos de grupo o sesión se requiere un archivo `--confirmados` con `inscripciones[]` y las variables de la plantilla. `--apply` genera archivos locales en `out/`; no envía WhatsApp. Con `--supabase --apply` también guarda la variante A/B en la nueva columna. Después de enviar y recibir respuesta, el equipo puede registrar las fechas con `node scripts/mensajes/registrar.mjs --input <archivo-registro.json> --apply`; sin la bandera solo muestra un conteo. El JSON lleva `registros[]` con `id` y una o ambas fechas ISO (`primer_mensaje_at`, `primera_respuesta_at`). El reporte semanal cuenta ambas por variante, sin pruebas estadísticas. Si hay quejas, o una variante responde menos tras 10 envíos por brazo, se detiene el experimento para revisión.

## Preparar Google Calendar (Gmail personal)

1. En Google Cloud crear un proyecto y habilitar la API de Google Calendar. Crear consentimiento OAuth y un cliente de tipo **aplicación de escritorio**. Si Google Cloud solicita tarjeta, detenerse y consultar al responsable. Usar la cuenta organizadora al autorizar.
2. Guardar el JSON del cliente y el token **fuera del repositorio**. Definir `GOOGLE_OAUTH_CLIENT_FILE` y `GOOGLE_OAUTH_TOKEN_FILE` como rutas absolutas, y ejecutar `node scripts/invitaciones/auth.mjs`. El script imprime un enlace, escucha solo en `127.0.0.1` y guarda el token en la ruta indicada.
3. Revisar un archivo privado de personas y `grupos-confirmados.json`. Ejecutar `node scripts/invitaciones/index.mjs --input <archivo-privado> --confirmados <grupos-confirmados.json>` sin bandera para ver solo cantidades. Tras revisar, añadir `--apply`. Este último paso requiere también la llave de servicio de Supabase y la tabla `sesiones` aplicada por el equipo.

El evento usa `conferenceDataVersion=1`, `conferenceData.createRequest` distinto por sesión y `sendUpdates=all`; Google enviará correos de invitación. El ID determinista permite reintentar sin duplicar. El título **Pendiente** solo cambia mediante `confirmado: true` en el archivo revisado por el equipo. No se interpretan respuestas RSVP.

Documentación oficial: [OAuth de escritorio](https://developers.google.com/identity/protocols/oauth2/native-app), [crear eventos y Meet](https://developers.google.com/workspace/calendar/api/guides/create-events), [Events: insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert).
