-- La prioridad comercial aplica solo a personas que aceptaron explícitamente
-- el precio completo; los registros históricos sin respuesta no se clasifican.
create or replace function public.crm_prioridad_precio(
  p_curso_id uuid default null,
  p_estatus text default null,
  p_busqueda text default null,
  p_desde date default null,
  p_hasta date default null,
  p_limit integer default 50,
  p_offset integer default 0
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_resultado jsonb;
begin
  perform private.crm_exigir_admin();
  if p_limit is null or p_limit not between 1 and 100 or p_offset is null or p_offset < 0 then
    raise exception 'Paginación inválida';
  end if;

  with filtradas as materialized (
    select i.id, i.created_at, i.estatus, i.ultimo_contacto, i.proximo_contacto_at,
      i.respuestas, i.curso_id, c.nombre as curso, u.nombre, u.email, u.whatsapp, u.instagram
    from public.inscripciones i
    join public.usuarios u on u.id = i.usuario_id
    join public.cursos c on c.id = i.curso_id
    where i.respuestas->>'solicita_beca' = 'false'
      and i.estatus in ('interesado','contactado','inscrito')
      and (p_curso_id is null or i.curso_id = p_curso_id)
      and (p_estatus is null or i.estatus = p_estatus)
      and (p_busqueda is null or trim(p_busqueda) = '' or
        u.nombre ilike '%' || trim(p_busqueda) || '%' or
        u.email ilike '%' || trim(p_busqueda) || '%')
      and (p_desde is null or (i.created_at at time zone 'America/Mexico_City')::date >= p_desde)
      and (p_hasta is null or (i.created_at at time zone 'America/Mexico_City')::date <= p_hasta)
  ), pagina as (
    select * from filtradas
    order by
      case when proximo_contacto_at < now() then 0
           when ultimo_contacto is null then 1 else 2 end,
      proximo_contacto_at asc nulls last,
      created_at desc
    limit p_limit offset p_offset
  )
  select jsonb_build_object(
    'total', (select count(*) from filtradas),
    'filas', (select coalesce(jsonb_agg(to_jsonb(pagina)), '[]'::jsonb) from pagina)
  ) into v_resultado;
  return v_resultado;
end;
$function$;

revoke all on function public.crm_prioridad_precio(uuid,text,text,date,date,integer,integer) from public, anon;
grant execute on function public.crm_prioridad_precio(uuid,text,text,date,date,integer,integer) to authenticated;
