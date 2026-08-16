-- ============================================================
-- Student Voting System — Supabase schema
-- Run this in: Supabase Dashboard -> SQL Editor -> New query
-- ============================================================

-- Positions (xilalka doorashada)
create table if not exists public.positions (
  id bigint primary key generated always as identity,
  name text not null unique,
  description text
);

-- Candidates (musharraxiinta)
create table if not exists public.candidates (
  id bigint primary key generated always as identity,
  position_id bigint not null references public.positions(id),
  name text not null,
  student_id text,
  manifesto text,
  photo_url text
);

-- Eligible students (liiska ardayda saxda ah ee qasaxda ah)
create table if not exists public.eligible_students (
  id bigint primary key generated always as identity,
  student_id text not null unique,
  name text not null,
  email text
);

-- Students (xisaabaha ardayda ee diiwaangashan)
create table if not exists public.students (
  id bigint primary key generated always as identity,
  student_id text not null unique,
  name text not null,
  email text not null unique,
  password_hash text not null,
  created_at timestamptz not null default now()
);

-- Votes (hal cod oo loogu talagalay hal xil)
create table if not exists public.votes (
  id bigint primary key generated always as identity,
  student_id bigint not null references public.students(id),
  position_id bigint not null references public.positions(id),
  candidate_id bigint not null references public.candidates(id),
  created_at timestamptz not null default now(),
  unique (student_id, position_id)
);

-- Admins (maamulka — admin dashboard)
create table if not exists public.admins (
  id bigint primary key generated always as identity,
  username text not null unique,
  password_hash text not null,
  created_at timestamptz not null default now()
);

-- Elections (maamulka doorashada)
create table if not exists public.elections (
  id bigint primary key generated always as identity,
  title text not null,
  start_at timestamptz,
  end_at timestamptz,
  is_open boolean not null default false,
  created_at timestamptz not null default now()
);

-- ============================================================
-- RLS: demo mode — anon key ayaa si buuxda u isticmaali kara
-- (ma aha nidaam ammaan oo loogu talagalay production!)
-- ============================================================
alter table public.positions enable row level security;
alter table public.candidates enable row level security;
alter table public.eligible_students enable row level security;
alter table public.students enable row level security;
alter table public.votes enable row level security;
alter table public.admins enable row level security;
alter table public.elections enable row level security;

create policy "positions all" on public.positions for all to anon using (true) with check (true);
create policy "candidates all" on public.candidates for all to anon using (true) with check (true);
create policy "eligible all" on public.eligible_students for all to anon using (true) with check (true);
create policy "students all" on public.students for all to anon using (true) with check (true);
create policy "votes all" on public.votes for all to anon using (true) with check (true);
create policy "admins all" on public.admins for all to anon using (true) with check (true);
create policy "elections all" on public.elections for all to anon using (true) with check (true);

-- Create indexes for fast queries
create index if not exists idx_candidates_position on public.candidates(position_id);
create index if not exists idx_votes_position on public.votes(position_id);
create index if not exists idx_votes_student on public.votes(student_id);