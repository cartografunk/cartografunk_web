-- Histograma de altas por hora local, bajo el mismo acceso privado del CRM.
create or replace function public.crm_horas_inscripcion(
  p_curso_id uuid default null,
  p_desde date default null,
  p_hasta date default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare v_resultado jsonb;
begin
  perform private.crm_exigir_admin();
  if p_desde is not null and p_hasta is not null and p_desde > p_hasta then
    raise exception 'Rango de fechas inválido';
  end if;

  select jsonb_agg(jsonb_build_object(
    'hora', horas.hora,
    'total', coalesce(registros.total, 0)
  ) order by horas.hora) into v_resultado
  from generate_series(0, 23) as horas(hora)
  left join (
    select extract(hour from i.created_at at time zone 'America/Mexico_City')::integer as hora,
      count(*) as total
    from public.inscripciones i
    where (p_curso_id is null or i.curso_id = p_curso_id)
      and (p_desde is null or (i.created_at at time zone 'America/Mexico_City')::date >= p_desde)
      and (p_hasta is null or (i.created_at at time zone 'America/Mexico_City')::date <= p_hasta)
    group by 1
  ) registros on registros.hora = horas.hora;
  return v_resultado;
end;
$function$;

revoke all on function public.crm_horas_inscripcion(uuid,date,date) from public, anon;
grant execute on function public.crm_horas_inscripcion(uuid,date,date) to authenticated;
