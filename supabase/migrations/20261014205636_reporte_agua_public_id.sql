-- Identificador aleatorio para el mapa. El folio permanece solo en el esquema privado.
-- El folio previo ya usaba UUID aleatorio; se amplía sin fecha visible.
alter table reporte_agua.reportes alter column folio set default (
  'AGUA-' || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 20))
);

alter table reporte_agua.reportes
  add column if not exists public_id uuid default gen_random_uuid();
update reporte_agua.reportes set public_id = gen_random_uuid() where public_id is null;
alter table reporte_agua.reportes alter column public_id set not null;
create unique index if not exists reportes_public_id_uidx
  on reporte_agua.reportes (public_id);

alter table public.reportes_agua_publicos
  add column if not exists public_id uuid;

do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'reportes_agua_publicos'
      and column_name = 'reporte_id'
  ) then
    execute '
      update public.reportes_agua_publicos as p
      set public_id = r.public_id
      from reporte_agua.reportes as r
      where p.reporte_id = r.id and p.public_id is null';
  end if;
end;
$$;

alter table public.reportes_agua_publicos alter column public_id set not null;
alter table public.reportes_agua_publicos
  drop constraint if exists reportes_agua_publicos_pkey;
alter table public.reportes_agua_publicos
  add constraint reportes_agua_publicos_pkey primary key (public_id);
alter table public.reportes_agua_publicos
  drop column if exists folio,
  drop column if exists reporte_id;
alter table public.reportes_agua_publicos
  drop constraint if exists reportes_agua_publicos_public_id_fkey;
alter table public.reportes_agua_publicos
  add constraint reportes_agua_publicos_public_id_fkey
  foreign key (public_id) references reporte_agua.reportes(public_id)
  on delete cascade;

create or replace function reporte_agua.sincronizar_reporte_publico()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'UPDATE' then
    if old.public_id is distinct from new.public_id then
      delete from public.reportes_agua_publicos where public_id = old.public_id;
    end if;
  end if;

  if new.estado_moderacion = 'publicado' then
    insert into public.reportes_agua_publicos (
      public_id, geom_publica, categoria_codigo, categoria_nombre,
      nota, fecha_observacion, created_at
    )
    select new.public_id, new.geom_publica, c.codigo, c.nombre,
           new.nota, new.fecha_observacion, new.created_at
    from reporte_agua.categorias as c
    where c.id = new.categoria_id
    on conflict (public_id) do update set
      geom_publica = excluded.geom_publica,
      categoria_codigo = excluded.categoria_codigo,
      categoria_nombre = excluded.categoria_nombre,
      nota = excluded.nota,
      fecha_observacion = excluded.fecha_observacion,
      created_at = excluded.created_at;
  else
    delete from public.reportes_agua_publicos where public_id = new.public_id;
  end if;
  return null;
end;
$$;

drop function if exists public.ruta_foto_reporte_agua(text);
create or replace function public.ruta_foto_reporte_agua(p_public_id uuid)
returns text
language sql
security definer
set search_path = ''
as $$
  select r.foto_ruta
  from reporte_agua.reportes as r
  where r.public_id = p_public_id and r.estado_moderacion = 'publicado'
  limit 1;
$$;

revoke all on function public.ruta_foto_reporte_agua(uuid)
  from public, anon, authenticated;
grant execute on function public.ruta_foto_reporte_agua(uuid) to service_role;

notify pgrst, 'reload schema';
