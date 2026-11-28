-- PROPUESTA, NO APLICADA. La votación de IA se abre al verificar el pago.
-- Los enlaces ya creados siguen siendo válidos cuando se verifica el pago.
create or replace function private.crm_voto_habilitado(p_inscripcion_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $function$
  select coalesce((
    select case
      when i.curso_id <> 'a77e51c2-441a-4bac-9a25-922aa99ab323'::uuid then true
      when i.respuestas->>'solicita_beca' = 'true' then
        i.beca_aprobada
        and coalesce(i.respuestas->>'aporte_mxn', '') ~ '^[1-9][0-9]{0,3}$'
        and (i.respuestas->>'aporte_mxn')::integer between 1 and 1499
        and coalesce((select sum(p.monto_mxn) from public.crm_pagos p
          where p.inscripcion_id = i.id and p.estado = 'verificado'), 0)
          >= (i.respuestas->>'aporte_mxn')::integer
      else coalesce((select sum(p.monto_mxn) from public.crm_pagos p
        where p.inscripcion_id = i.id and p.estado = 'verificado'), 0) >= 450
    end
    from public.inscripciones i where i.id = p_inscripcion_id
  ), false)
$function$;

revoke all on function private.crm_voto_habilitado(uuid) from public, anon, authenticated;

create or replace function public.crm_invitaciones_horario(
  p_curso_id uuid, p_generar boolean default false
)
returns jsonb language plpgsql security definer set search_path = ''
as $function$
declare v_resultado jsonb;
begin
  perform private.crm_exigir_admin();
  if p_curso_id is null or not exists (select 1 from public.cursos where id = p_curso_id) then
    raise exception 'Curso inválido';
  end if;
  if coalesce(p_generar, false) then
    insert into public.crm_disponibilidad(inscripcion_id)
    select i.id from public.inscripciones i
    where i.curso_id = p_curso_id
      and i.estatus in ('interesado','contactado','inscrito','pagado')
      and private.crm_voto_habilitado(i.id)
    on conflict (inscripcion_id) do nothing;
  end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'inscripcion_id', i.id, 'nombre', u.nombre, 'email', u.email,
    'whatsapp', u.whatsapp, 'estatus', i.estatus,
    'precio_completo', i.respuestas->>'solicita_beca' = 'false',
    'pago_habilitado', private.crm_voto_habilitado(i.id),
    'token', case when private.crm_voto_habilitado(i.id) then d.token else null end,
    'opciones', coalesce(to_jsonb(d.opciones), '[]'::jsonb),
    'comentario', d.comentario, 'respondio_at', d.respondio_at
  ) order by i.created_at desc), '[]'::jsonb) into v_resultado
  from public.inscripciones i
  join public.usuarios u on u.id = i.usuario_id
  left join public.crm_disponibilidad d on d.inscripcion_id = i.id
  where i.curso_id = p_curso_id
    and i.estatus in ('interesado','contactado','inscrito','pagado');
  return v_resultado;
end;
$function$;

create or replace function public.ver_horarios(p_token uuid)
returns jsonb language plpgsql security definer set search_path = ''
as $function$
declare v_resultado jsonb;
begin
  select jsonb_build_object(
    'curso', c.nombre, 'opciones', to_jsonb(d.opciones),
    'sin_bloques', d.sin_bloques, 'comentario', d.comentario,
    'respondio_at', d.respondio_at
  ) into v_resultado
  from public.crm_disponibilidad d
  join public.inscripciones i on i.id = d.inscripcion_id
  join public.cursos c on c.id = i.curso_id
  where d.token = p_token
    and i.estatus in ('interesado','contactado','inscrito','pagado')
    and private.crm_voto_habilitado(i.id);
  if v_resultado is null then raise exception 'Enlace inválido o pago pendiente'; end if;
  return v_resultado;
end;
$function$;

create or replace function public.guardar_horarios_v2(
  p_token uuid, p_opciones text[], p_sin_bloques boolean, p_comentario text default null
)
returns void language plpgsql security definer set search_path = ''
as $function$
declare v_opciones text[];
begin
  if now() >= timestamptz '2026-12-07 02:00:00+00' then
    raise exception 'La votación está cerrada';
  end if;
  if p_token is null or p_opciones is null or p_sin_bloques is null
    or cardinality(p_opciones) > 28
    or (p_comentario is not null and length(p_comentario) > 500) then
    raise exception 'Respuesta inválida';
  end if;
  select coalesce(array_agg(distinct opcion), '{}') into v_opciones
  from unnest(p_opciones) as opcion;
  if exists (select 1 from unnest(v_opciones) as opcion
    where opcion is null or opcion !~ '^[1-7]-(09|12|16|19)$')
    or (p_sin_bloques and cardinality(v_opciones) > 0)
    or (not p_sin_bloques and cardinality(v_opciones) = 0
      and nullif(trim(p_comentario), '') is null) then
    raise exception 'Selecciona horarios o explica cuándo puedes';
  end if;
  update public.crm_disponibilidad d
  set opciones = v_opciones, sin_bloques = p_sin_bloques,
      comentario = nullif(trim(p_comentario), ''), respondio_at = now()
  from public.inscripciones i
  where d.token = p_token and i.id = d.inscripcion_id
    and i.estatus in ('interesado','contactado','inscrito','pagado')
    and private.crm_voto_habilitado(i.id);
  if not found then raise exception 'Enlace inválido o pago pendiente'; end if;
end;
$function$;
