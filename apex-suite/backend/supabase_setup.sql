-- Apex Suite - Supabase setup. Safe to run more than once.
-- Supabase dashboard > SQL Editor > New query > paste all of this > Run.

create table if not exists apex_sessions (
  id          text primary key,
  created_at  timestamptz default now(),
  device      text,
  browser     text,
  screen_size text
);

create table if not exists apex_events (
  id          uuid primary key default gen_random_uuid(),
  session_id  text references apex_sessions(id),
  created_at  timestamptz default now(),
  module      text not null,
  action      text not null,
  job_title   text,
  user_name   text,
  metadata    jsonb default '{}'
);

create index if not exists apex_events_created_idx on apex_events (created_at desc);
create index if not exists apex_events_session_idx on apex_events (session_id);

alter table apex_sessions enable row level security;
alter table apex_events   enable row level security;

drop policy if exists "anon_insert_sessions" on apex_sessions;
drop policy if exists "anon_insert_events"   on apex_events;
drop policy if exists "anon_read_sessions"   on apex_sessions;
drop policy if exists "anon_read_events"     on apex_events;

-- These let the server write and read using the publishable/anon key.
create policy "anon_insert_sessions" on apex_sessions for insert to anon with check (true);
create policy "anon_insert_events"   on apex_events   for insert to anon with check (true);
create policy "anon_read_sessions"   on apex_sessions for select to anon using (true);
create policy "anon_read_events"     on apex_events   for select to anon using (true);

-- ── OPTIONAL HARDENING (recommended once everything works) ──────────────────
-- Put a SECRET key (sb_secret_... or the service_role key) in the server's
-- SUPABASE_SERVICE_KEY. The server then bypasses row-level security, so the four
-- policies above are no longer needed and you can delete them. After that the
-- public/publishable key can read and write NOTHING in these tables:
--
--   drop policy "anon_insert_sessions" on apex_sessions;
--   drop policy "anon_insert_events"   on apex_events;
--   drop policy "anon_read_sessions"   on apex_sessions;
--   drop policy "anon_read_events"     on apex_events;
