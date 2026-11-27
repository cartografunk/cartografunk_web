-- Objetivo público: 29 nov 2026, 20:00 CDMX. Cierre real: 6 dic, 20:00 CDMX.
create or replace function public.guardar_horarios_v2(
  p_token uuid,
  p_opciones text[],
  p_sin_bloques boolean,
  p_comentario text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_opciones text[];
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
  set opciones = v_opciones,
      sin_bloques = p_sin_bloques,
      comentario = nullif(trim(p_comentario), ''),
      respondio_at = now()
  from public.inscripciones i
  where d.token = p_token and i.id = d.inscripcion_id
    and i.estatus in ('interesado','contactado','inscrito','pagado');
  if not found then raise exception 'Enlace inválido o vencido'; end if;
end;
$function$;
