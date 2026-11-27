-- PROPUESTA, NO APLICADA. Elimina el RPC v1 y cierra lectura directa.
-- Reversión: restaurar guardar_horarios desde 20261127_encuesta_horarios_v2.sql;
-- cualquier política o grant retirado debe recrearse desde un respaldo revisado.
-- Revisar políticas existentes antes de aplicar: este cambio puede afectar otros clientes.
alter table public.crm_disponibilidad enable row level security;
alter table public.inscripciones enable row level security;
revoke all on public.crm_disponibilidad from public, anon, authenticated;
revoke all on public.inscripciones from public, anon, authenticated;

do $policy$
declare p record;
begin
  for p in select schemaname, tablename, policyname from pg_policies
    where schemaname = 'public' and tablename in ('crm_disponibilidad', 'inscripciones')
  loop
    execute format('drop policy %I on %I.%I', p.policyname, p.schemaname, p.tablename);
  end loop;
end;
$policy$;

revoke all on function public.guardar_horarios(uuid,text[],text) from public, anon, authenticated;
drop function if exists public.guardar_horarios(uuid,text[],text);
-- ver_horarios(uuid) ya es SECURITY DEFINER, search_path='', y solo devuelve:
-- curso, opciones, sin_bloques, comentario, respondio_at. Sus estatus son los
-- mismos que guardar_horarios_v2: interesado, contactado, inscrito y pagado.
