-- PROPUESTA, NO APLICADA. Cierra la sobrescritura anónima en el registro público.
-- Antes: con el email de alguien ya registrado, un anónimo cambiaba su nombre/whatsapp
-- (usuarios) y sus respuestas (inscripciones), aun si ya estaba pagado.
-- Ahora: usuarios existentes no se tocan; las respuestas solo se reemplazan mientras
-- la inscripción siga en 'interesado'. Si el dato cambió de verdad, lo corrige el equipo.
-- Reversión: restaurar la función desde 20261124_agentes_ia_tesis.sql.
create or replace function public.registrar_inscripcion_agentes_ia(
  p_email text,
  p_nombre text,
  p_edad integer,
  p_residencia text,
  p_whatsapp text,
  p_instagram text,
  p_solicita_beca boolean,
  p_aporte_mxn integer,
  p_propuesta_intercambio text
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_usuario_id uuid;
  v_inscripcion_id uuid;
  v_curso_id constant uuid := 'a77e51c2-441a-4bac-9a25-922aa99ab323';
begin
  if p_email is null or length(trim(p_email)) > 254 or trim(p_email) !~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
    or p_nombre is null or length(trim(p_nombre)) not between 1 and 120
    or p_edad is null or p_edad not between 1 and 120
    or p_residencia is null or length(trim(p_residencia)) not between 1 and 160
    or p_whatsapp is null or length(trim(p_whatsapp)) not between 1 and 30
    or (p_instagram is not null and length(trim(p_instagram)) > 120)
    or p_solicita_beca is null
    or (p_solicita_beca and (p_aporte_mxn is null or p_aporte_mxn not between 1 and 1499
        or p_propuesta_intercambio is null or length(trim(p_propuesta_intercambio)) not between 1 and 1500))
    or (not p_solicita_beca and (p_aporte_mxn is not null or p_propuesta_intercambio is not null))
  then
    raise exception 'Datos de inscripción inválidos';
  end if;

  insert into public.usuarios (email, nombre, instagram, whatsapp)
  values (lower(trim(p_email)), trim(p_nombre), nullif(trim(p_instagram), ''), trim(p_whatsapp))
  on conflict (email) do nothing
  returning id into v_usuario_id;

  if v_usuario_id is null then
    select id into v_usuario_id from public.usuarios where email = lower(trim(p_email));
  end if;

  insert into public.inscripciones (usuario_id, curso_id, estatus, respuestas)
  values (
    v_usuario_id,
    v_curso_id,
    'interesado',
    jsonb_build_object(
      'edad', p_edad,
      'residencia', trim(p_residencia),
      'solicita_beca', p_solicita_beca,
      'aporte_mxn', p_aporte_mxn,
      'propuesta_intercambio', case when p_solicita_beca then trim(p_propuesta_intercambio) else null end
    )
  )
  on conflict (usuario_id, curso_id) do update
    set respuestas = excluded.respuestas
    where public.inscripciones.estatus = 'interesado'
  returning id into v_inscripcion_id;

  -- Si el conflicto no actualizó (estatus distinto de 'interesado'), RETURNING no devuelve fila.
  if v_inscripcion_id is null then
    select id into v_inscripcion_id
    from public.inscripciones
    where usuario_id = v_usuario_id and curso_id = v_curso_id;
  end if;

  return v_inscripcion_id;
end;
$function$;

revoke all on function public.registrar_inscripcion_agentes_ia(text, text, integer, text, text, text, boolean, integer, text) from public;
grant execute on function public.registrar_inscripcion_agentes_ia(text, text, integer, text, text, text, boolean, integer, text) to anon, authenticated;
