-- PROPUESTA, NO APLICADA. Registro auditable de pago/beca y confirmación por persona.
-- Todo pasa por crm_exigir_admin() y deja fila en crm_actividades.
-- Autocontenida: los campos de pago/beca usan "if not exists", así que no choca con
-- 20261127_pipeline_campos.sql (que además agrega el check de mensaje_variante).
-- Reversión: drop de las dos funciones y de las dos columnas nuevas (confirmado_at,
-- grupo_confirmado), previa exportación de lo capturado.
alter table public.inscripciones
  add column if not exists pago_comprobado boolean not null default false,
  add column if not exists beca_aprobada boolean not null default false,
  add column if not exists grupo_confirmado text,
  add column if not exists confirmado_at timestamptz;

alter table public.inscripciones
  drop constraint if exists inscripciones_grupo_confirmado_check;
alter table public.inscripciones
  add constraint inscripciones_grupo_confirmado_check
  check (grupo_confirmado is null or length(grupo_confirmado) between 1 and 60);

-- Pago comprobado / beca aprobada. NULL = no cambiar ese campo.
-- La nota es obligatoria: referencia de lo que se comprobó (ej. "SPEI 27 nov, ref. ...").
create or replace function public.crm_marcar_pago_beca(
  p_inscripcion_id uuid,
  p_pago_comprobado boolean,
  p_beca_aprobada boolean,
  p_nota text
)
returns void
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_estatus text;
  v_pago boolean;
  v_beca boolean;
begin
  perform private.crm_exigir_admin();
  if p_nota is null or length(trim(p_nota)) not between 1 and 1500
    or (p_pago_comprobado is null and p_beca_aprobada is null) then
    raise exception 'Datos inválidos';
  end if;

  select estatus, pago_comprobado, beca_aprobada into v_estatus, v_pago, v_beca
  from public.inscripciones where id = p_inscripcion_id for update;
  if not found then raise exception 'Inscripción no encontrada'; end if;

  update public.inscripciones
  set pago_comprobado = coalesce(p_pago_comprobado, pago_comprobado),
      beca_aprobada = coalesce(p_beca_aprobada, beca_aprobada)
  where id = p_inscripcion_id;

  insert into public.crm_actividades (
    inscripcion_id, actor_id, tipo, nota, estatus_anterior, estatus_nuevo
  ) values (
    p_inscripcion_id, auth.uid(), 'nota',
    'Pago comprobado: ' || case when coalesce(p_pago_comprobado, v_pago) then 'sí' else 'no' end
      || '; beca aprobada: ' || case when coalesce(p_beca_aprobada, v_beca) then 'sí' else 'no' end
      || '. ' || trim(p_nota),
    v_estatus, v_estatus
  );
end;
$function$;

-- Confirmación por persona, tras hablar con ella. p_grupo = NULL quita la confirmación.
create or replace function public.crm_confirmar_grupo(
  p_inscripcion_id uuid,
  p_grupo text,
  p_nota text
)
returns void
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_estatus text;
begin
  perform private.crm_exigir_admin();
  if (p_grupo is not null and length(trim(p_grupo)) not between 1 and 60)
    or p_nota is null or length(trim(p_nota)) not between 1 and 1500 then
    raise exception 'Datos inválidos';
  end if;

  select estatus into v_estatus
  from public.inscripciones where id = p_inscripcion_id for update;
  if not found then raise exception 'Inscripción no encontrada'; end if;

  update public.inscripciones
  set grupo_confirmado = nullif(trim(p_grupo), ''),
      confirmado_at = case when p_grupo is null then null else now() end
  where id = p_inscripcion_id;

  insert into public.crm_actividades (
    inscripcion_id, actor_id, tipo, nota, estatus_anterior, estatus_nuevo
  ) values (
    p_inscripcion_id, auth.uid(), 'nota',
    case when p_grupo is null then 'Confirmación retirada. ' else 'Confirmó grupo ' || trim(p_grupo) || '. ' end
      || trim(p_nota),
    v_estatus, v_estatus
  );
end;
$function$;

revoke all on function public.crm_marcar_pago_beca(uuid,boolean,boolean,text) from public, anon;
revoke all on function public.crm_confirmar_grupo(uuid,text,text) from public, anon;
grant execute on function public.crm_marcar_pago_beca(uuid,boolean,boolean,text) to authenticated;
grant execute on function public.crm_confirmar_grupo(uuid,text,text) to authenticated;
