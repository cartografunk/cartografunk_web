-- Panel privado de inscripciones. La historia de actividades comienza con este cambio;
-- los estados anteriores se conservan sin inventar eventos pasados.
create schema if not exists private;

create table if not exists private.crm_admin_emails (
  email text primary key,
  created_at timestamptz not null default now(),
  constraint crm_admin_email_lowercase check (email = lower(email))
);

revoke all on schema private from public, anon, authenticated;
revoke all on table private.crm_admin_emails from public, anon, authenticated;

insert into private.crm_admin_emails (email)
values ('cartografunk@gmail.com')
on conflict (email) do nothing;

alter table public.inscripciones
  add column if not exists proximo_contacto_at timestamptz;

create index if not exists inscripciones_crm_pendientes_idx
  on public.inscripciones (proximo_contacto_at, estatus)
  where estatus in ('interesado', 'contactado', 'inscrito', 'pagado');

create table if not exists public.crm_actividades (
  id uuid primary key default gen_random_uuid(),
  inscripcion_id uuid not null references public.inscripciones(id) on delete cascade,
  actor_id uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  tipo text not null check (tipo in ('nota', 'whatsapp', 'correo', 'llamada')),
  nota text not null check (length(trim(nota)) between 1 and 2000),
  estatus_anterior text not null,
  estatus_nuevo text not null,
  proximo_contacto_at timestamptz
);

create index if not exists crm_actividades_inscripcion_fecha_idx
  on public.crm_actividades (inscripcion_id, created_at desc);

alter table public.crm_actividades enable row level security;
revoke all on table public.crm_actividades from public, anon, authenticated;

create or replace function private.crm_exigir_admin()
returns void
language plpgsql
security definer
set search_path = ''
as $function$
begin
  if auth.uid() is null or not exists (
    select 1
    from auth.users u
    join private.crm_admin_emails a on a.email = lower(u.email)
    where u.id = auth.uid() and u.email_confirmed_at is not null
  ) then
    raise exception 'Acceso no autorizado' using errcode = '42501';
  end if;
end;
$function$;

revoke all on function private.crm_exigir_admin() from public, anon, authenticated;

create or replace function public.crm_resumen(
  p_curso_id uuid default null,
  p_desde date default null,
  p_hasta date default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_resumen jsonb;
  v_cursos jsonb;
  v_tendencia jsonb;
begin
  perform private.crm_exigir_admin();
  if p_desde is not null and p_hasta is not null and p_desde > p_hasta then
    raise exception 'Rango de fechas inválido';
  end if;

  select jsonb_build_object(
    'total', count(*),
    'interesado', count(*) filter (where estatus = 'interesado'),
    'contactado', count(*) filter (where estatus = 'contactado'),
    'inscrito', count(*) filter (where estatus = 'inscrito'),
    'pagado', count(*) filter (where estatus = 'pagado'),
    'completado', count(*) filter (where estatus = 'completado'),
    'perdido', count(*) filter (where estatus = 'perdido'),
    'sin_primer_contacto', count(*) filter (where estatus = 'interesado' and ultimo_contacto is null),
    'vencidos', count(*) filter (where estatus in ('interesado','contactado','inscrito','pagado') and proximo_contacto_at < now()),
    'sin_programar', count(*) filter (where estatus in ('interesado','contactado','inscrito','pagado') and proximo_contacto_at is null),
    'becas', count(*) filter (where respuestas->>'solicita_beca' = 'true')
  ) into v_resumen
  from public.inscripciones
  where (p_curso_id is null or curso_id = p_curso_id)
    and (p_desde is null or (created_at at time zone 'America/Mexico_City')::date >= p_desde)
    and (p_hasta is null or (created_at at time zone 'America/Mexico_City')::date <= p_hasta);

  select coalesce(jsonb_agg(jsonb_build_object(
    'id', id, 'nombre', nombre, 'costo_mxn', costo_mxn, 'sesiones', sesiones
  ) order by nombre), '[]'::jsonb) into v_cursos
  from public.cursos where activo is true;

  select coalesce(jsonb_agg(jsonb_build_object('dia', dia, 'total', total) order by dia), '[]'::jsonb)
  into v_tendencia
  from (
    select (created_at at time zone 'America/Mexico_City')::date as dia, count(*) as total
    from public.inscripciones
    where created_at >= now() - interval '30 days'
      and (p_curso_id is null or curso_id = p_curso_id)
    group by (created_at at time zone 'America/Mexico_City')::date
  ) t;

  return jsonb_build_object('resumen', v_resumen, 'cursos', v_cursos, 'tendencia_30d', v_tendencia);
end;
$function$;

create or replace function public.crm_listar_inscripciones(
  p_curso_id uuid default null,
  p_estatus text default null,
  p_busqueda text default null,
  p_cola text default null,
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
  if p_cola is not null and p_cola not in ('sin_contacto','vencidos','sin_programar','pendientes') then
    raise exception 'Cola inválida';
  end if;

  with filtradas as materialized (
    select i.id, i.created_at, i.estatus, i.ultimo_contacto, i.proximo_contacto_at,
      i.respuestas, i.curso_id, c.nombre as curso, u.nombre, u.email, u.whatsapp, u.instagram
    from public.inscripciones i
    join public.usuarios u on u.id = i.usuario_id
    join public.cursos c on c.id = i.curso_id
    where (p_curso_id is null or i.curso_id = p_curso_id)
      and (p_estatus is null or i.estatus = p_estatus)
      and (p_desde is null or (i.created_at at time zone 'America/Mexico_City')::date >= p_desde)
      and (p_hasta is null or (i.created_at at time zone 'America/Mexico_City')::date <= p_hasta)
      and (p_busqueda is null or trim(p_busqueda) = '' or
        u.nombre ilike '%' || trim(p_busqueda) || '%' or
        u.email ilike '%' || trim(p_busqueda) || '%')
      and (p_cola is null
        or (p_cola = 'sin_contacto' and i.estatus = 'interesado' and i.ultimo_contacto is null)
        or (p_cola = 'vencidos' and i.estatus in ('interesado','contactado','inscrito','pagado') and i.proximo_contacto_at < now())
        or (p_cola = 'sin_programar' and i.estatus in ('interesado','contactado','inscrito','pagado') and i.proximo_contacto_at is null)
        or (p_cola = 'pendientes' and i.estatus in ('interesado','contactado','inscrito','pagado') and
            (i.proximo_contacto_at is null or i.proximo_contacto_at <= now())))
  ), pagina as (
    select * from filtradas
    order by
      case when proximo_contacto_at < now() then 0
           when proximo_contacto_at is null and estatus in ('interesado','contactado','inscrito','pagado') then 1
           else 2 end,
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

create or replace function public.crm_historial(p_inscripcion_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_resultado jsonb;
begin
  perform private.crm_exigir_admin();
  select coalesce(jsonb_agg(to_jsonb(a) order by a.created_at desc), '[]'::jsonb)
  into v_resultado
  from (select id, created_at, tipo, nota, estatus_anterior, estatus_nuevo,
        proximo_contacto_at from public.crm_actividades
        where inscripcion_id = p_inscripcion_id
        order by created_at desc limit 100) a;
  return v_resultado;
end;
$function$;

create or replace function public.crm_guardar_seguimiento(
  p_inscripcion_id uuid,
  p_estatus text,
  p_tipo text,
  p_nota text,
  p_proximo_contacto_at timestamptz
)
returns void
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_estatus_anterior text;
  v_proximo timestamptz;
begin
  perform private.crm_exigir_admin();
  if p_estatus is null or p_estatus not in ('interesado','contactado','inscrito','pagado','completado','perdido')
    or p_tipo is null or p_tipo not in ('nota','whatsapp','correo','llamada')
    or p_nota is null or length(trim(p_nota)) not between 1 and 2000 then
    raise exception 'Datos de seguimiento inválidos';
  end if;

  select estatus into v_estatus_anterior
  from public.inscripciones where id = p_inscripcion_id for update;
  if not found then raise exception 'Inscripción no encontrada'; end if;

  v_proximo := case when p_estatus in ('completado','perdido') then null else p_proximo_contacto_at end;

  update public.inscripciones
  set estatus = p_estatus,
      proximo_contacto_at = v_proximo,
      ultimo_contacto = case when p_tipo in ('whatsapp','correo','llamada')
        then (now() at time zone 'America/Mexico_City')::date else ultimo_contacto end,
      notas_seguimiento = trim(p_nota)
  where id = p_inscripcion_id;

  insert into public.crm_actividades (
    inscripcion_id, actor_id, tipo, nota, estatus_anterior, estatus_nuevo, proximo_contacto_at
  ) values (
    p_inscripcion_id, auth.uid(), p_tipo, trim(p_nota), v_estatus_anterior, p_estatus, v_proximo
  );
end;
$function$;

revoke all on function public.crm_resumen(uuid,date,date) from public, anon;
revoke all on function public.crm_listar_inscripciones(uuid,text,text,text,date,date,integer,integer) from public, anon;
revoke all on function public.crm_historial(uuid) from public, anon;
revoke all on function public.crm_guardar_seguimiento(uuid,text,text,text,timestamptz) from public, anon;
grant execute on function public.crm_resumen(uuid,date,date) to authenticated;
grant execute on function public.crm_listar_inscripciones(uuid,text,text,text,date,date,integer,integer) to authenticated;
grant execute on function public.crm_historial(uuid) to authenticated;
grant execute on function public.crm_guardar_seguimiento(uuid,text,text,text,timestamptz) to authenticated;
