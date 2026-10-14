-- Diagnóstico de solo lectura antes de crear el CRM.
-- Ejecutar en el SQL Editor del proyecto. No devuelve registros de contactos.
select jsonb_build_object(
  'columns', (
    select jsonb_agg(to_jsonb(c) order by c.table_name, c.ordinal_position)
    from (
      select table_name, column_name, data_type, udt_name, is_nullable,
             column_default, ordinal_position
      from information_schema.columns
      where table_schema = 'public'
        and table_name in ('usuarios', 'inscripciones', 'cursos', 'pendientes_seguimiento')
    ) c
  ),
  'constraints', (
    select jsonb_agg(jsonb_build_object(
      'table', t.relname, 'name', c.conname,
      'definition', pg_get_constraintdef(c.oid)
    ))
    from pg_constraint c
    join pg_class t on t.oid = c.conrelid
    join pg_namespace n on n.oid = t.relnamespace
    where n.nspname = 'public' and t.relname in ('usuarios', 'inscripciones', 'cursos')
  ),
  'rls', (
    select jsonb_agg(jsonb_build_object('table', c.relname,
      'enabled', c.relrowsecurity, 'forced', c.relforcerowsecurity,
      'options', c.reloptions))
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in ('usuarios', 'inscripciones', 'cursos', 'pendientes_seguimiento')
  ),
  'policies', (
    select jsonb_agg(to_jsonb(p)) from pg_policies p
    where schemaname = 'public'
      and tablename in ('usuarios', 'inscripciones', 'cursos', 'pendientes_seguimiento')
  ),
  'grants', (
    select jsonb_agg(to_jsonb(g)) from (
      select table_name, grantee, privilege_type
      from information_schema.table_privileges
      where table_schema = 'public' and grantee in ('anon', 'authenticated')
        and table_name in ('usuarios', 'inscripciones', 'cursos', 'pendientes_seguimiento')
    ) g
  ),
  'views', (
    select jsonb_agg(to_jsonb(v)) from pg_views v
    where schemaname = 'public' and viewname = 'pendientes_seguimiento'
  ),
  'registration_rpc', (
    select jsonb_agg(jsonb_build_object('signature', p.oid::regprocedure::text,
      'security_definer', p.prosecdef, 'settings', p.proconfig,
      'definition', pg_get_functiondef(p.oid)))
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public' and p.proname = 'registrar_inscripcion'
  )
) as crm_schema_audit;
