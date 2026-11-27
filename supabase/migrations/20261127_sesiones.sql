-- PROPUESTA, NO APLICADA. Registro privado de eventos Calendar por sesión.
-- Reversión: drop table public.sesiones, después de respaldar IDs y Meet URLs.
create table public.sesiones (
  id uuid primary key default gen_random_uuid(),
  grupo text not null,
  numero_sesion integer not null check (numero_sesion between 1 and 3),
  inicio timestamptz not null,
  fin timestamptz not null check (fin > inicio),
  evento_id text unique,
  meet_url text,
  creada_at timestamptz not null default now(),
  unique (grupo, numero_sesion)
);
alter table public.sesiones enable row level security;
revoke all on public.sesiones from public, anon, authenticated;
