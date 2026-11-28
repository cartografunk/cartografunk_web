-- El panel distingue un borrador abierto de un contacto registrado por el operador.
create or replace function public.crm_contacto_estados(p_inscripcion_ids uuid[])
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_resultado jsonb;
begin
  perform private.crm_exigir_admin();
  if p_inscripcion_ids is null or cardinality(p_inscripcion_ids) > 100 then
    raise exception 'Lista de inscripciones inválida';
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'inscripcion_id', i.id,
    'whatsapp_at', c.whatsapp_at,
    'correo_at', c.correo_at
  )), '[]'::jsonb)
  into v_resultado
  from public.inscripciones i
  left join lateral (
    select max(a.created_at) filter (where a.tipo = 'whatsapp') as whatsapp_at,
      max(a.created_at) filter (where a.tipo = 'correo') as correo_at
    from public.crm_actividades a
    where a.inscripcion_id = i.id
  ) c on true
  where i.id = any(p_inscripcion_ids);

  return v_resultado;
end;
$function$;

revoke all on function public.crm_contacto_estados(uuid[]) from public, anon;
grant execute on function public.crm_contacto_estados(uuid[]) to authenticated;
