-- Votación privada por enlace. El token va en el fragmento de la URL y no en
-- la petición de la página; solo se envía al RPC de Supabase.
create table if not exists public.crm_disponibilidad (
  inscripcion_id uuid primary key references public.inscripciones(id) on delete cascade,
  token uuid not null unique default gen_random_uuid(),
  opciones text[] not null default '{}',
  comentario text,
  respondio_at timestamptz,
  created_at timestamptz not null default now(),
  constraint crm_disponibilidad_comentario check (comentario is null or length(comentario) <= 500)
);

alter table public.crm_disponibilidad enable row level security;
revoke all on table public.crm_disponibilidad from public, anon, authenticated;

create or replace function public.crm_invitaciones_horario(
  p_curso_id uuid,
  p_generar boolean default false
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
  if p_curso_id is null or not exists (select 1 from public.cursos where id = p_curso_id) then
    raise exception 'Curso inválido';
  end if;

  if coalesce(p_generar, false) then
    insert into public.crm_disponibilidad (inscripcion_id)
    select id from public.inscripciones
    where curso_id = p_curso_id and estatus in ('interesado','contactado','inscrito','pagado')
    on conflict (inscripcion_id) do nothing;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'inscripcion_id', i.id,
    'nombre', u.nombre,
    'email', u.email,
    'whatsapp', u.whatsapp,
    'estatus', i.estatus,
    'precio_completo', i.respuestas->>'solicita_beca' = 'false',
    'token', d.token,
    'opciones', coalesce(to_jsonb(d.opciones), '[]'::jsonb),
    'comentario', d.comentario,
    'respondio_at', d.respondio_at
  ) order by i.created_at desc), '[]'::jsonb) into v_resultado
  from public.inscripciones i
  join public.usuarios u on u.id = i.usuario_id
  left join public.crm_disponibilidad d on d.inscripcion_id = i.id
  where i.curso_id = p_curso_id and i.estatus in ('interesado','contactado','inscrito','pagado');

  return v_resultado;
end;
$function$;

create or replace function public.ver_horarios(p_token uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_resultado jsonb;
begin
  select jsonb_build_object(
    'curso', c.nombre,
    'opciones', to_jsonb(d.opciones),
    'comentario', d.comentario,
    'respondio_at', d.respondio_at
  ) into v_resultado
  from public.crm_disponibilidad d
  join public.inscripciones i on i.id = d.inscripcion_id
  join public.cursos c on c.id = i.curso_id
  where d.token = p_token and i.estatus in ('interesado','contactado','inscrito','pagado');

  if v_resultado is null then raise exception 'Enlace inválido o vencido'; end if;
  return v_resultado;
end;
$function$;

create or replace function public.guardar_horarios(
  p_token uuid,
  p_opciones text[],
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
  if p_token is null or p_opciones is null or cardinality(p_opciones) > 28
    or (p_comentario is not null and length(p_comentario) > 500) then
    raise exception 'Respuesta inválida';
  end if;

  select coalesce(array_agg(distinct opcion), '{}') into v_opciones
  from unnest(p_opciones) as opcion;

  if exists (select 1 from unnest(v_opciones) as opcion
    where opcion is null or opcion !~ '^[1-7]-(09|12|16|19)$')
    or (cardinality(v_opciones) = 0 and nullif(trim(p_comentario), '') is null) then
    raise exception 'Selecciona horarios o explica cuándo puedes';
  end if;

  update public.crm_disponibilidad d
  set opciones = v_opciones,
      comentario = nullif(trim(p_comentario), ''),
      respondio_at = now()
  from public.inscripciones i
  where d.token = p_token and i.id = d.inscripcion_id
    and i.estatus in ('interesado','contactado','inscrito','pagado');
  if not found then raise exception 'Enlace inválido o vencido'; end if;
end;
$function$;

revoke all on function public.crm_invitaciones_horario(uuid,boolean) from public, anon;
grant execute on function public.crm_invitaciones_horario(uuid,boolean) to authenticated;
revoke all on function public.ver_horarios(uuid) from public;
revoke all on function public.guardar_horarios(uuid,text[],text) from public;
grant execute on function public.ver_horarios(uuid) to anon, authenticated;
grant execute on function public.guardar_horarios(uuid,text[],text) to anon, authenticated;
