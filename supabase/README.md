# Reporte ciudadano de agua

La migración `migrations/20261014194521_reporte_agua_esquema_seguridad.sql`
crea el esquema privado `reporte_agua`, independiente del CRM. `categorias`
contiene las siete opciones del formulario. `reportes` guarda el folio, la
ubicación exacta, la ubicación pública calculada en una cuadrícula de 150 m,
los datos del reporte y su estado de moderación. `colonia_id` es texto nullable
y todavía no tiene llave foránea. `reporte_contacto` guarda el contacto opcional
y la fecha de consentimiento, separado del reporte.

El navegador solo puede leer `public.reportes_agua_publicos`. Un trigger copia
allí los campos seguros de reportes `publicado` y retira la fila si cambia su
estado. Las tablas privadas tienen RLS activado y no conceden acceso a `anon`
ni `authenticated`. Tampoco hay inserción directa desde el navegador; la
Edge Function de la Fase 2 usará `service_role` mediante una RPC restringida
para escribir, sin exponer el esquema privado en la Data API.

Las fotos se guardan en el bucket privado `reporte-agua-fotos`. La Edge Function
`foto-reporte` comprueba el estado antes de entregar una URL firmada por dos
minutos. La migración no depende de `colonias`, `calles` ni
`colonia_de_punto`.

## Envío y configuración

La migración `20261014195803_reporte_agua_envio_limites.sql` agrega el límite
atómico por IP y RPC internas. Solo `service_role` puede ejecutar esas RPC.
`enviar-reporte` recibe el formulario, verifica Turnstile, limita a cinco
envíos por IP y hora, revisa la imagen y guarda foto y reporte. `geocode`
consulta Google desde el servidor, con límite de 30 búsquedas por IP y hora.
El rectángulo provisional del AMG está en
`functions/_shared/reporte-agua.ts`; debe sustituirse por el polígono real.

Configura los secrets de Edge Functions `GOOGLE_MAPS_API_KEY`,
`TURNSTILE_SECRET_KEY` y `RATE_LIMIT_SALT` (valor aleatorio largo). Supabase
proporciona `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`. La site key pública
de Turnstile va en `assets/js/reporte-agua-config.js`. Autoriza los dominios
del sitio y `localhost` en Turnstile para pruebas locales. No publiques los
secrets ni `supabase/.env.secrets`.

## Prueba de punta a punta

1. Abre `/reporte-agua`, marca un pin dentro del área provisional, adjunta
   una foto, elige categoría y fecha, acepta la publicación y completa
   Turnstile. Anota el folio que responde el formulario.
2. Confirma en `reporte_agua.reportes` que el estado es `pendiente` y que no
   aparece en `public.reportes_agua_publicos` ni en el mapa.
3. Desde el editor SQL de Supabase, como administrador, publica el folio:

   ```sql
   update reporte_agua.reportes
   set estado_moderacion = 'publicado'
   where folio = 'PEGA_AQUI_EL_FOLIO';
   ```

4. Recarga el mapa público: debe aparecer un marcador en la ubicación
   aproximada. Ábrelo para comprobar la foto mediante `foto-reporte`.
5. Opcional: cambia el estado a `rechazado` y recarga; debe desaparecer.

La ubicación pública se calcula en PostGIS con una cuadrícula de 150 m en
UTM 13N (EPSG:32613), y vuelve a WGS84 (EPSG:4326) para el mapa. La ubicación
exacta, la referencia de calle y el contacto permanecen privados.
