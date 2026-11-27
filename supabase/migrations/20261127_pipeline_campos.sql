-- PROPUESTA, NO APLICADA. Campos de confirmación y medición de mensajes.
-- Reversión: drop column de los cinco campos añadidos, previa exportación de
-- cualquier dato capturado en ellos.
alter table public.inscripciones
  add column if not exists pago_comprobado boolean not null default false,
  add column if not exists beca_aprobada boolean not null default false,
  add column if not exists mensaje_variante text,
  add column if not exists primer_mensaje_at timestamptz,
  add column if not exists primera_respuesta_at timestamptz;

alter table public.inscripciones
  add constraint inscripciones_mensaje_variante_check
  check (mensaje_variante is null or mensaje_variante in ('A', 'B'));
