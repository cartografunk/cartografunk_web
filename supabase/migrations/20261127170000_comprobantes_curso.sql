-- PROPUESTA, NO APLICADA. Anticipos y comprobantes privados del curso de IA.
-- Reversión: respaldar comprobantes y actividad; eliminar funciones, tablas y
-- bucket (incluidos sus objetos) después de resolver los pagos abiertos.
alter table public.inscripciones
  add column if not exists pago_comprobado boolean not null default false;

create table public.crm_enlaces_pago (
  inscripcion_id uuid primary key references public.inscripciones(id) on delete cascade,
  token uuid not null unique default gen_random_uuid(),
  creado_at timestamptz not null default now()
);
alter table public.crm_enlaces_pago enable row level security;
revoke all on public.crm_enlaces_pago from public, anon, authenticated;

create table public.crm_pagos (
  id uuid primary key default gen_random_uuid(),
  inscripcion_id uuid not null references public.inscripciones(id) on delete cascade,
  monto_mxn integer not null check (monto_mxn between 1 and 1500),
  estado text not null default 'pendiente' check (estado in ('pendiente','verificado','rechazado')),
  comprobante_path text not null unique,
  referencia text,
  recibido_at timestamptz not null default now(),
  revisado_at timestamptz,
  revisado_por uuid references auth.users(id),
  nota_revision text,
  constraint crm_pagos_nota_revision check (nota_revision is null or length(nota_revision) <= 1500)
);
create index crm_pagos_inscripcion_idx on public.crm_pagos(inscripcion_id, recibido_at desc);
alter table public.crm_pagos enable row level security;
revoke all on public.crm_pagos from public, anon, authenticated;

insert into storage.buckets (id, name, public)
values ('comprobantes-cursos', 'comprobantes-cursos', false)
on conflict (id) do nothing;

create or replace function public.crm_enlace_pago(p_inscripcion_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $function$
declare v_token uuid;
begin
  perform private.crm_exigir_admin();
  if not exists (
    select 1 from public.inscripciones i
    where i.id = p_inscripcion_id
      and i.curso_id = 'a77e51c2-441a-4bac-9a25-922aa99ab323'::uuid
      and i.respuestas->>'solicita_beca' = 'false'
      and i.estatus in ('interesado','contactado','inscrito','pagado')
  ) then raise exception 'Inscripción no disponible'; end if;
  insert into public.crm_enlaces_pago(inscripcion_id) values (p_inscripcion_id)
    on conflict (inscripcion_id) do nothing;
  select token into v_token from public.crm_enlaces_pago
    where inscripcion_id = p_inscripcion_id;
  return v_token;
end;
$function$;

create or replace function public.crm_pagos_detalle(p_inscripcion_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare v_result jsonb;
begin
  perform private.crm_exigir_admin();
  select jsonb_build_object(
    'costo_mxn', c.costo_mxn,
    'verificado_mxn', coalesce((select sum(p.monto_mxn) from public.crm_pagos p
      where p.inscripcion_id = i.id and p.estado = 'verificado'), 0),
    'pagos', coalesce((select jsonb_agg(jsonb_build_object(
      'id', p.id, 'monto_mxn', p.monto_mxn, 'estado', p.estado,
      'recibido_at', p.recibido_at, 'referencia', p.referencia,
      'nota_revision', p.nota_revision
    ) order by p.recibido_at desc) from public.crm_pagos p
      where p.inscripcion_id = i.id), '[]'::jsonb)
  ) into v_result
  from public.inscripciones i join public.cursos c on c.id = i.curso_id
  where i.id = p_inscripcion_id;
  if v_result is null then raise exception 'Inscripción no encontrada'; end if;
  return v_result;
end;
$function$;

create or replace function public.crm_revisar_pago(
  p_pago_id uuid, p_aprobar boolean, p_nota text
)
returns void
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_pago public.crm_pagos%rowtype;
  v_estatus text;
  v_total integer;
  v_costo integer;
begin
  perform private.crm_exigir_admin();
  if p_aprobar is null or p_nota is null or length(trim(p_nota)) not between 1 and 1500 then
    raise exception 'Revisión inválida';
  end if;
  select * into v_pago from public.crm_pagos where id = p_pago_id for update;
  if not found or v_pago.estado <> 'pendiente' then raise exception 'Pago no disponible'; end if;
  select i.estatus, c.costo_mxn into v_estatus, v_costo
    from public.inscripciones i join public.cursos c on c.id = i.curso_id
    where i.id = v_pago.inscripcion_id for update of i;
  update public.crm_pagos set estado = case when p_aprobar then 'verificado' else 'rechazado' end,
    revisado_at = now(), revisado_por = auth.uid(), nota_revision = trim(p_nota)
    where id = p_pago_id;
  select coalesce(sum(monto_mxn), 0) into v_total from public.crm_pagos
    where inscripcion_id = v_pago.inscripcion_id and estado = 'verificado';
  if v_total > v_costo then raise exception 'El total verificado excede el costo del curso'; end if;
  update public.inscripciones set
    pago_comprobado = v_total >= 450,
    estatus = case
      when v_total >= v_costo and estatus in ('interesado','contactado','inscrito') then 'pagado'
      when v_total >= 450 and estatus in ('interesado','contactado') then 'inscrito'
      else estatus end
    where id = v_pago.inscripcion_id;
  insert into public.crm_actividades
    (inscripcion_id, actor_id, tipo, nota, estatus_anterior, estatus_nuevo)
  values (v_pago.inscripcion_id, auth.uid(), 'nota',
    (case when p_aprobar then 'Pago verificado: $' else 'Comprobante rechazado: $' end)
      || v_pago.monto_mxn || ' MXN. ' || trim(p_nota),
    v_estatus, (select estatus from public.inscripciones where id = v_pago.inscripcion_id));
end;
$function$;

revoke all on function public.crm_enlace_pago(uuid) from public, anon;
revoke all on function public.crm_pagos_detalle(uuid) from public, anon;
revoke all on function public.crm_revisar_pago(uuid,boolean,text) from public, anon;
grant execute on function public.crm_enlace_pago(uuid) to authenticated;
grant execute on function public.crm_pagos_detalle(uuid) to authenticated;
grant execute on function public.crm_revisar_pago(uuid,boolean,text) to authenticated;
