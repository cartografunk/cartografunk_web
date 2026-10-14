-- Reporte ciudadano de agua: datos privados y proyeccion publica.
-- No depende de colonias, calles ni de funciones geograficas existentes.

create extension if not exists postgis with schema extensions;
create schema if not exists reporte_agua;

revoke all on schema reporte_agua from public, anon, authenticated;
grant usage on schema reporte_agua to service_role;

create table if not exists reporte_agua.categorias (
  id uuid primary key default gen_random_uuid(),
  codigo text not null unique,
  nombre text not null,
  constraint categorias_codigo_valido check (codigo ~ '^[a-z_]+$')
);

insert into reporte_agua.categorias (codigo, nombre) values
  ('olor', 'Olor'),
  ('color_anormal', 'Color anormal'),
  ('espuma', 'Espuma'),
  ('descarga_visible', 'Descarga visible'),
  ('residuos', 'Residuos'),
  ('mortandad_fauna', 'Mortandad de fauna'),
  ('otro', 'Otro')
on conflict (codigo) do nothing;

create table if not exists reporte_agua.reportes (
  id uuid primary key default gen_random_uuid(),
  folio text not null unique default (
    'AGUA-' || to_char(now() at time zone 'America/Mexico_City', 'YYYYMMDD') || '-'
    || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 12))
  ),
  geom_exacta extensions.geometry(Point, 4326) not null,
  geom_publica extensions.geometry(Point, 4326) not null,
  colonia_id text,
  calle_texto text,
  categoria_id uuid not null references reporte_agua.categorias(id),
  nota text not null,
  fecha_observacion timestamptz not null,
  estado_moderacion text not null default 'pendiente',
  foto_ruta text not null,
  created_at timestamptz not null default now(),
  constraint reportes_nota_longitud check (char_length(nota) between 1 and 500),
  constraint reportes_calle_longitud check (calle_texto is null or char_length(calle_texto) <= 200),
  constraint reportes_estado_valido check (
    estado_moderacion in ('pendiente', 'publicado', 'rechazado', 'en_revision')
  ),
  constraint reportes_geom_exacta_valida check (
    not extensions.ST_IsEmpty(geom_exacta)
    and extensions.ST_X(geom_exacta) between -180 and 180
    and extensions.ST_Y(geom_exacta) between -90 and 90
  ),
  constraint reportes_foto_ruta_no_vacia check (char_length(btrim(foto_ruta)) > 0)
);

-- No se crea ninguna llave foranea para colonia_id hasta conocer la capa real.
create table if not exists reporte_agua.reporte_contacto (
  reporte_id uuid primary key references reporte_agua.reportes(id) on delete cascade,
  email text,
  telefono text,
  consentimiento_contacto_at timestamptz not null,
  created_at timestamptz not null default now(),
  constraint reporte_contacto_al_menos_un_medio check (
    nullif(btrim(coalesce(email, '')), '') is not null
    or nullif(btrim(coalesce(telefono, '')), '') is not null
  )
);

create index if not exists reportes_geom_exacta_gix
  on reporte_agua.reportes using gist (geom_exacta);
create index if not exists reportes_geom_publica_gix
  on reporte_agua.reportes using gist (geom_publica);
create index if not exists reportes_estado_idx
  on reporte_agua.reportes (estado_moderacion, created_at desc);

-- La cuadricula usa metros en UTM 13N y vuelve a WGS84 para Leaflet.
-- Se recalcula en cada escritura, aun si alguien intenta enviar geom_publica.
create or replace function reporte_agua.calcular_geom_publica()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  new.geom_publica := extensions.ST_Transform(
    extensions.ST_SnapToGrid(
      extensions.ST_Transform(new.geom_exacta, 32613),
      150.0::double precision
    ),
    4326
  );
  return new;
end;
$$;

revoke all on function reporte_agua.calcular_geom_publica() from public, anon, authenticated;
drop trigger if exists reportes_calcular_geom_publica on reporte_agua.reportes;
create trigger reportes_calcular_geom_publica
before insert or update on reporte_agua.reportes
for each row execute function reporte_agua.calcular_geom_publica();

-- Solo esta tabla, sin ubicacion exacta, se consulta desde el navegador.
create table if not exists public.reportes_agua_publicos (
  reporte_id uuid primary key references reporte_agua.reportes(id) on delete cascade,
  folio text not null,
  estado_moderacion text not null default 'publicado',
  geom_publica extensions.geometry(Point, 4326) not null,
  categoria_codigo text not null,
  categoria_nombre text not null,
  nota text not null,
  fecha_observacion timestamptz not null,
  created_at timestamptz not null,
  constraint reportes_agua_publicos_nota_longitud check (char_length(nota) <= 500),
  constraint reportes_agua_publicos_solo_publicados check (estado_moderacion = 'publicado')
);

create index if not exists reportes_agua_publicos_geom_gix
  on public.reportes_agua_publicos using gist (geom_publica);
create index if not exists reportes_agua_publicos_fecha_idx
  on public.reportes_agua_publicos (created_at desc);

-- Publicar, editar o retirar un reporte mantiene sincronizada la proyeccion.
create or replace function reporte_agua.sincronizar_reporte_publico()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.estado_moderacion = 'publicado' then
    insert into public.reportes_agua_publicos (
      reporte_id, folio, geom_publica, categoria_codigo, categoria_nombre,
      nota, fecha_observacion, created_at
    )
    select new.id, new.folio, new.geom_publica, c.codigo, c.nombre,
           new.nota, new.fecha_observacion, new.created_at
    from reporte_agua.categorias as c
    where c.id = new.categoria_id
    on conflict (reporte_id) do update set
      folio = excluded.folio,
      geom_publica = excluded.geom_publica,
      categoria_codigo = excluded.categoria_codigo,
      categoria_nombre = excluded.categoria_nombre,
      nota = excluded.nota,
      fecha_observacion = excluded.fecha_observacion,
      created_at = excluded.created_at;
  else
    delete from public.reportes_agua_publicos where reporte_id = new.id;
  end if;
  return null;
end;
$$;

revoke all on function reporte_agua.sincronizar_reporte_publico() from public, anon, authenticated;
drop trigger if exists reportes_sincronizar_publico on reporte_agua.reportes;
create trigger reportes_sincronizar_publico
after insert or update on reporte_agua.reportes
for each row execute function reporte_agua.sincronizar_reporte_publico();

alter table reporte_agua.categorias enable row level security;
alter table reporte_agua.reportes enable row level security;
alter table reporte_agua.reporte_contacto enable row level security;
alter table public.reportes_agua_publicos enable row level security;

revoke all on reporte_agua.categorias, reporte_agua.reportes,
  reporte_agua.reporte_contacto from public, anon, authenticated;
grant all on reporte_agua.categorias, reporte_agua.reportes,
  reporte_agua.reporte_contacto to service_role;
revoke all on public.reportes_agua_publicos from public, anon, authenticated;
grant select on public.reportes_agua_publicos to anon, authenticated;

-- No hay politicas de lectura o escritura publica sobre las tablas privadas.
-- La proyeccion solo recibe filas publicadas por el trigger anterior.
do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'reportes_agua_publicos'
      and policyname = 'leer_reportes_agua_publicados'
  ) then
    create policy leer_reportes_agua_publicados
      on public.reportes_agua_publicos
      for select to anon, authenticated
      using (estado_moderacion = 'publicado');
  end if;
end;
$$;

-- La Edge Function subira fotos sin EXIF con service_role.
-- No se concede acceso anonimo ni autenticado a este bucket.
insert into storage.buckets (
  id, name, public, file_size_limit, allowed_mime_types
) values (
  'reporte-agua-fotos', 'reporte-agua-fotos', false, 10485760,
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do nothing;

do $$
begin
  if exists (
    select 1 from storage.buckets
    where id = 'reporte-agua-fotos' and public
  ) then
    raise exception 'El bucket reporte-agua-fotos debe ser privado';
  end if;
end;
$$;
