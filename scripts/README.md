# Pipeline local de grupos, mensajes y Google Calendar

**Estado:** propuesta. Las migraciones de esta entrega no están aplicadas y no se ejecutó ningún script contra producción. La primera corrida real corresponde a una persona del equipo. `out/` y `fixtures/private/` están ignorados por Git. No copies allí datos reales si compartes el directorio fuera del equipo.

## Orden de trabajo

1. Revisar las cinco migraciones propuestas, **no aplicadas**, de `supabase/migrations/`: `20261127_endurecimiento.sql`, `20261127_pipeline_campos.sql`, `20261127_sesiones.sql`, `20261127150000_registro_no_sobrescribe.sql` y `20261127150100_crm_pago_confirmacion.sql`. Esta última es autocontenida y puede ir antes o después de `pipeline_campos`, pero el equipo debe elegir un orden deliberado: varias migraciones del 20261127 comparten el prefijo de ocho dígitos. Revisar también el impacto de permisos/políticas antes de aplicar. `inscripciones` no tiene su `CREATE TABLE` base en este repo, así que la verificación final de RLS y grants debe hacerse en Supabase por una persona autorizada. No ejecutar la migración de endurecimiento sin revisar si otro cliente depende de esas políticas.
2. Actualizar qué inscripciones están `inscrito` o `pagado` y marcar pago comprobado o beca aprobada mediante `crm_marcar_pago_beca`; registrar la confirmación manual por persona mediante `crm_confirmar_grupo`. El panel `/crm` aún no tiene interfaz para estas dos funciones. Aceptar el precio **no equivale** a pagar. Los campos de pago/beca se proponen en `20261127_pipeline_campos.sql` y, de forma autocontenida, en `20261127150100_crm_pago_confirmacion.sql`.
3. Ejecutar el agrupador con votos reales solo cuando el equipo decida hacerlo. Revisar `out/propuesta-grupos.json` y `out/propuesta-grupos.txt`. El criterio es **menos días distintos, luego menos grupos**, siempre que alcance la cobertura objetivo. Si no se alcanza, muestra la máxima cobertura posible. `--cupo` es opcional; sin él no hay límite por grupo.
4. Revisar con cada persona la propuesta por WhatsApp. El script de mensajes solo crea texto y enlaces; nunca envía mensajes. Los archivos con teléfonos y textos van a `out/`.
5. Preparar a mano un `grupos-confirmados.json` con bloque, **tres fechas explícitas** y IDs revisados. No se infieren fechas. Usa un identificador de grupo único por edición del curso para evitar choques con eventos anteriores. `confirmado: false` crea el título con **Pendiente**. Cámbialo a `true` solo tras confirmación manual por el equipo; una nueva corrida quita esa marca. La respuesta RSVP de Meet no se usa como métrica ni como confirmación.
6. Ejecutar invitaciones solo para inscripciones con `pago_comprobado` o `beca_aprobada`. Google Calendar envía correo y un Meet propio por sesión únicamente con `--apply`. El equipo debe revisar la vista previa y los destinatarios antes de usar esa bandera.

Revisión estática de seguridad: la migración original de `crm_disponibilidad` habilita RLS y revoca permisos directos; la v1 `guardar_horarios(uuid,text[],text)` **sí existe** como wrapper público en `20261127_encuesta_horarios_v2.sql`, por eso la propuesta la elimina. `ver_horarios` en ese mismo archivo devuelve solo `curso`, `opciones`, `sin_bloques`, `comentario` y `respondio_at`, usa `security definer` con `search_path=''` y filtra los mismos cuatro estatus que `guardar_horarios_v2`. El estado efectivo de RLS, grants y políticas de `inscripciones` en producción **no se verificó** por la regla de no ejecutar contra producción.

## Formato de datos

`--input` lee un JSON local con `inscripciones[]`. Cada fila requiere `id`, `estatus` y `disponibilidad: {opciones, sin_bloques, respondio_at}` para grupos. Mensajes añaden `nombre`, `whatsapp`, `respuestas.solicita_beca`; invitaciones requieren `email`, `pago_comprobado` o `beca_aprobada`. Consulta `fixtures/pipeline.json` para un ejemplo sin contactos. No commitear archivos con contactos.

Para leer Supabase se usa `--supabase --apply`, `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en variables de entorno. La llave nunca se imprime. El lector selecciona las columnas de la migración propuesta; fallará hasta que una persona la aplique. No usar la llave de servicio en el navegador ni en el repo.

## Comandos de vista previa

Desde la raíz del repositorio:

```powershell
node --test scripts/pipeline/pipeline.test.mjs
node scripts/grupos/index.mjs --input fixtures/pipeline.json
node scripts/mensajes/index.mjs --input fixtures/pipeline.json --tipo primer-contacto --plazo "fecha revisada por el equipo"
node scripts/invitaciones/index.mjs --input fixtures/pipeline.json --confirmados fixtures/grupos-confirmados.json
```

Grupos admite `--max-grupos` (1 a 5; por defecto 4), `--cupo` (por defecto ilimitado), `--cobertura-objetivo` (0 a 1; por defecto 0.85) y `--incluir-contactados`. Por defecto solo toma `inscrito` y `pagado`. La tabla Pareto muestra la mayor cobertura con **hasta** 1, 2, …, 7 días. Los votos después del 29 de noviembre de 2026 a las 20:00 CDMX se marcan como tardíos.

Mensajes admite `--tipo primer-contacto|beca|grupo|sesion|recordatorio-24h|recordatorio-1h`. Para textos de grupo o sesión se requiere un archivo `--confirmados` con `inscripciones[]` y las variables de la plantilla. `--apply` genera archivos locales en `out/`; no envía WhatsApp. Con `--supabase --apply` también guarda la variante A/B en la nueva columna. Después de enviar y recibir respuesta, el equipo puede registrar las fechas con `node scripts/mensajes/registrar.mjs --input <archivo-registro.json> --apply`; sin la bandera solo muestra un conteo. El JSON lleva `registros[]` con `id` y una o ambas fechas ISO (`primer_mensaje_at`, `primera_respuesta_at`). El reporte semanal cuenta ambas por variante, sin pruebas estadísticas. Si hay quejas, o una variante responde menos tras 10 envíos por brazo, se detiene el experimento para revisión.

## Preparar Google Calendar (Gmail personal)

1. En Google Cloud crear un proyecto y habilitar la API de Google Calendar. Crear consentimiento OAuth y un cliente de tipo **aplicación de escritorio**. Si Google Cloud solicita tarjeta, detenerse y consultar al responsable. Usar la cuenta organizadora al autorizar.
2. Guardar el JSON del cliente y el token **fuera del repositorio**. Definir `GOOGLE_OAUTH_CLIENT_FILE` y `GOOGLE_OAUTH_TOKEN_FILE` como rutas absolutas, y ejecutar `node scripts/invitaciones/auth.mjs`. El script imprime un enlace, escucha solo en `127.0.0.1` y guarda el token en la ruta indicada.
3. Revisar un archivo privado de personas y `grupos-confirmados.json`. Ejecutar `node scripts/invitaciones/index.mjs --input <archivo-privado> --confirmados <grupos-confirmados.json>` sin bandera para ver solo cantidades. Tras revisar, añadir `--apply`. Este último paso requiere también la llave de servicio de Supabase y la tabla `sesiones` aplicada por el equipo.

El evento usa `conferenceDataVersion=1`, `conferenceData.createRequest` distinto por sesión y `sendUpdates=all`; Google enviará correos de invitación. El ID determinista permite reintentar sin duplicar. El título **Pendiente** solo cambia mediante `confirmado: true` en el archivo revisado por el equipo. No se interpretan respuestas RSVP.

Documentación oficial: [OAuth de escritorio](https://developers.google.com/identity/protocols/oauth2/native-app), [crear eventos y Meet](https://developers.google.com/workspace/calendar/api/guides/create-events), [Events: insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert).
