-- RPCs internos para las Edge Functions. El esquema privado sigue sin exponerse.

create table if not exists reporte_agua.limites_ip (
  ip_hash text not null,
  accion text not null,
  ventana_inicio timestamptz not null,
  conteo integer not null,
  primary key (ip_hash, accion),
  constraint limites_ip_hash_valido check (ip_hash ~ '^[0-9a-f]{64}$'),
  constraint limites_ip_accion_valida check (accion in ('enviar', 'geocode')),
  constraint limites_ip_conteo_valido check (conteo > 0)
);

alter table reporte_agua.limites_ip enable row level security;
revoke all on reporte_agua.limites_ip from public, anon, authenticated;
grant all on reporte_agua.limites_ip to service_role;

create or replace function public.consumir_limite_reporte_agua(
  p_ip_hash text, p_accion text, p_limite integer
) returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_aceptado boolean;
begin
  if p_ip_hash !~ '^[0-9a-f]{64}$'
     or p_accion not in ('enviar', 'geocode')
     or p_limite not between 1 and 100 then
    raise exception 'Límite inválido';
  end if;

  insert into reporte_agua.limites_ip as actual (
    ip_hash, accion, ventana_inicio, conteo
  ) values (
    p_ip_hash, p_accion, date_trunc('hour', now()), 1
  )
  on conflict (ip_hash, accion) do update set
    ventana_inicio = case
      when actual.ventana_inicio < excluded.ventana_inicio
        then excluded.ventana_inicio
      else actual.ventana_inicio
    end,
    conteo = case
      when actual.ventana_inicio < excluded.ventana_inicio then 1
      else actual.conteo + 1
    end
  where actual.ventana_inicio < excluded.ventana_inicio
     or actual.conteo < p_limite
  returning true into v_aceptado;

  return coalesce(v_aceptado, false);
end;
$$;

create or replace function public.categorias_reporte_agua()
returns table (id uuid, codigo text, nombre text)
language sql
security definer
set search_path = ''
as $$
  select c.id, c.codigo, c.nombre
  from reporte_agua.categorias as c
  order by c.nombre;
$$;

create or replace function public.crear_reporte_agua(
  p_id uuid,
  p_lng double precision,
  p_lat double precision,
  p_categoria_id uuid,
  p_nota text,
  p_fecha_observacion timestamptz,
  p_calle_texto text,
  p_foto_ruta text,
  p_email text,
  p_telefono text,
  p_consentimiento_contacto_at timestamptz
) returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_folio text;
begin
  if p_id is null or p_lng is null or p_lat is null
     or p_categoria_id is null or p_nota is null
     or p_fecha_observacion is null or p_foto_ruta is null then
    raise exception 'Faltan datos del reporte';
  end if;

  insert into reporte_agua.reportes (
    id, geom_exacta, categoria_id, nota, fecha_observacion,
    calle_texto, foto_ruta
  ) values (
    p_id,
    extensions.ST_SetSRID(extensions.ST_MakePoint(p_lng, p_lat), 4326),
    p_categoria_id, p_nota, p_fecha_observacion,
    nullif(btrim(p_calle_texto), ''), p_foto_ruta
  ) returning folio into v_folio;

  if nullif(btrim(coalesce(p_email, '')), '') is not null
     or nullif(btrim(coalesce(p_telefono, '')), '') is not null then
    if p_consentimiento_contacto_at is null then
      raise exception 'Falta consentimiento de contacto';
    end if;
    insert into reporte_agua.reporte_contacto (
      reporte_id, email, telefono, consentimiento_contacto_at
    ) values (
      p_id, nullif(btrim(p_email), ''), nullif(btrim(p_telefono), ''),
      p_consentimiento_contacto_at
    );
  end if;

  return v_folio;
end;
$$;

create or replace function public.ruta_foto_reporte_agua(p_folio text)
returns text
language sql
security definer
set search_path = ''
as $$
  select r.foto_ruta
  from reporte_agua.reportes as r
  where r.folio = p_folio and r.estado_moderacion = 'publicado'
  limit 1;
$$;

revoke all on function public.consumir_limite_reporte_agua(text, text, integer)
  from public, anon, authenticated;
revoke all on function public.categorias_reporte_agua()
  from public, anon, authenticated;
revoke all on function public.crear_reporte_agua(
  uuid, double precision, double precision, uuid, text, timestamptz,
  text, text, text, text, timestamptz
) from public, anon, authenticated;
revoke all on function public.ruta_foto_reporte_agua(text)
  from public, anon, authenticated;

grant execute on function public.consumir_limite_reporte_agua(text, text, integer)
  to service_role;
grant execute on function public.categorias_reporte_agua() to service_role;
grant execute on function public.crear_reporte_agua(
  uuid, double precision, double precision, uuid, text, timestamptz,
  text, text, text, text, timestamptz
) to service_role;
grant execute on function public.ruta_foto_reporte_agua(text) to service_role;
