-- อ่านยัง? · initial data model (v1.1)
-- Source: specs/system/data-model.md and ai-orchestration.md §3.2
-- Rules: every table has tenant_id; RLS is enabled on every table; thresholds live in config/, not here.

create extension if not exists vector;

-- =====================================================================
-- Tenancy helpers
-- =====================================================================

-- tenant_id is injected into the JWT by custom_access_token_hook (below).
create or replace function public.current_tenant_id()
returns uuid
language sql stable
as $$
  select nullif(auth.jwt() ->> 'tenant_id', '')::uuid
$$;

-- =====================================================================
-- Tenancy & users (ai-orchestration §3.4)
-- =====================================================================

create table public.tenants (
  id              uuid primary key default gen_random_uuid(),
  type            text not null default 'personal' check (type in ('personal', 'organization')),
  name            text not null,
  plan            text not null default 'free',
  quota_tokens_day integer,
  status          text not null default 'active' check (status in ('active', 'suspended')),
  created_at      timestamptz not null default now()
);

create table public.org_units (            -- schema ready for organizations; no UI in v1
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  parent_id  uuid references public.org_units(id) on delete cascade,
  name       text not null,
  created_at timestamptz not null default now()
);

create table public.memberships (
  user_id     uuid not null references auth.users(id) on delete cascade,
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  org_unit_id uuid references public.org_units(id) on delete set null,
  role        text not null default 'owner' check (role in ('owner', 'student', 'teacher', 'admin')),
  created_at  timestamptz not null default now(),
  primary key (user_id, tenant_id)
);

create table public.profiles (
  user_id          uuid primary key references auth.users(id) on delete cascade,
  tenant_id        uuid not null references public.tenants(id) on delete cascade,
  nickname         text,
  education_level  text,
  explain_language text not null default 'th',
  created_at       timestamptz not null default now()
);

create table public.tutor_profiles (       -- flow 2.7
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  description_raw text,                     -- never sent to the LLM as a prompt
  params          jsonb not null,           -- enum-only persona params
  version         integer not null default 1,
  created_at      timestamptz not null default now()
);

create table public.buddy_profiles (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  enabled         boolean not null default true,
  description_raw text,
  params          jsonb not null,
  version         integer not null default 1,
  created_at      timestamptz not null default now()
);

-- =====================================================================
-- Exam prep, materials, ingestion (flow 2.3)
-- =====================================================================

create table public.exam_preps (
  id                       uuid primary key default gen_random_uuid(),
  tenant_id                uuid not null references public.tenants(id) on delete cascade,
  user_id                  uuid not null references auth.users(id) on delete cascade,
  title                    text not null,
  subject                  text,
  exam_date                date not null,
  daily_minutes            integer,          -- optional (S08); planner falls back to observed time
  status                   text not null default 'active' check (status in ('active', 'archived')),
  active_scope_version_id  uuid,             -- fk added after scope_versions
  created_at               timestamptz not null default now()
);

create table public.materials (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references public.tenants(id) on delete cascade,
  exam_prep_id     uuid not null references public.exam_preps(id) on delete cascade,
  storage_path     text not null,            -- {tenant_id}/{exam_prep_id}/{material_id}
  file_name        text not null,
  kind             text check (kind in ('sheet', 'slides', 'past_exam', 'notes', 'other')),
  kind_confidence  numeric,
  kind_confirmed   boolean not null default false,
  user_note        text,
  relevance_weight numeric not null default 1.0,   -- stars.weight_* from config
  status           text not null default 'uploaded'
                   check (status in ('uploaded', 'classified', 'confirmed', 'ingesting', 'ready', 'failed')),
  error            text,
  created_at       timestamptz not null default now()
);

create table public.material_pages (
  id             uuid primary key default gen_random_uuid(),
  tenant_id      uuid not null references public.tenants(id) on delete cascade,
  material_id    uuid not null references public.materials(id) on delete cascade,
  page_no        integer not null,
  text           text not null,
  extract_method text not null check (extract_method in ('text_layer', 'vision', 'document_ai')),
  unique (material_id, page_no)
);

create table public.chunks (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references public.tenants(id) on delete cascade,
  material_id  uuid not null references public.materials(id) on delete cascade,
  page_from    integer not null,
  page_to      integer not null,
  text         text not null,                -- always kept next to the vector (AI-08)
  content_hash text not null,
  embedding    vector(768),                  -- dimension fixed after the embedding spike (PoC P3)
  created_at   timestamptz not null default now()
);

create table public.ingestion_jobs (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  material_id uuid not null references public.materials(id) on delete cascade,
  stage       text not null check (stage in ('classify', 'extract', 'chunk', 'embed', 'split_exam', 'topics', 'stars')),
  progress    numeric not null default 0,
  status      text not null default 'queued' check (status in ('queued', 'running', 'done', 'failed')),
  error       text,
  updated_at  timestamptz not null default now()
);

-- =====================================================================
-- Scope (flow 2.3)
-- =====================================================================

create table public.topics (
  id                uuid primary key default gen_random_uuid(),
  tenant_id         uuid not null references public.tenants(id) on delete cascade,
  exam_prep_id      uuid not null references public.exam_preps(id) on delete cascade,
  name              text not null,
  order_index       integer not null,
  prereq_ids        uuid[] not null default '{}',
  importance        smallint check (importance between 0 and 3),
  importance_reason text,
  importance_source text not null default 'computed' check (importance_source in ('computed', 'user')),
  signal_r          numeric,                 -- share of past exams containing the topic
  origin            text not null default 'doc' check (origin in ('doc', 'user')),
  status            text not null default 'draft' check (status in ('draft', 'confirmed', 'excluded')),
  created_at        timestamptz not null default now()
);

create table public.topic_skills (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  topic_id        uuid not null references public.topics(id) on delete cascade,
  name            text not null,
  exam_freq       integer not null default 0,
  common_mistakes jsonb not null default '[]',
  excluded        boolean not null default false
);

create table public.past_exam_questions (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references public.tenants(id) on delete cascade,
  material_id      uuid not null references public.materials(id) on delete cascade,
  q_no             text not null,
  page_no          integer,
  text             text not null,
  topic_id         uuid references public.topics(id) on delete set null,
  skill_id         uuid references public.topic_skills(id) on delete set null,
  trap             text,
  reference_answer text,
  used_in_session  boolean not null default false
);

create table public.topic_chunks (
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  topic_id  uuid not null references public.topics(id) on delete cascade,
  chunk_id  uuid not null references public.chunks(id) on delete cascade,
  score     numeric not null,
  primary key (topic_id, chunk_id)
);

create table public.scope_changes (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  exam_prep_id uuid not null references public.exam_preps(id) on delete cascade,
  topic_id   uuid references public.topics(id) on delete cascade,
  op         text not null check (op in ('set_importance', 'exclude', 'include', 'rename', 'reorder',
                                         'add_topic', 'exclude_skill', 'include_skill')),
  before     jsonb,
  after      jsonb,
  reason     text,
  actor      text not null check (actor in ('user', 'ai', 'system')),
  created_at timestamptz not null default now()
);

create table public.scope_versions (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references public.tenants(id) on delete cascade,
  exam_prep_id uuid not null references public.exam_preps(id) on delete cascade,
  version      integer not null,
  status       text not null default 'draft' check (status in ('draft', 'confirmed')),
  snapshot     jsonb not null,
  confirmed_at timestamptz,
  unique (exam_prep_id, version)
);

alter table public.exam_preps
  add constraint exam_preps_active_scope_fk
  foreign key (active_scope_version_id) references public.scope_versions(id) on delete set null;

-- =====================================================================
-- Tutoring (flows 2.2, 2.4, 2.5, 2.1)
-- =====================================================================

create table public.tutor_sessions (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references public.tenants(id) on delete cascade,
  user_id          uuid not null references auth.users(id) on delete cascade,
  exam_prep_id     uuid not null references public.exam_preps(id) on delete cascade,
  scope_version_id uuid not null references public.scope_versions(id),
  current_topic_id uuid references public.topics(id) on delete set null,
  stage            text check (stage in ('probe', 'teach', 'verify', 'practice', 'done', 'park')),
  mode             text check (mode in ('normal', 'tight', 'triage', 'final')),
  running_summary  text,
  summary          text,                     -- 2-line end-of-session summary
  buddy_muted      boolean not null default false,
  started_at       timestamptz not null default now(),
  ended_at         timestamptz,
  end_reason       text check (end_reason in ('user', 'time_budget', 'plan_done', 'idle'))
);

create table public.messages (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  session_id      uuid not null references public.tutor_sessions(id) on delete cascade,
  role            text not null check (role in ('user', 'tutor', 'buddy', 'card', 'system')),
  content         text,
  card            jsonb,                     -- progress card snapshot when role = 'card'
  input_mode      text check (input_mode in ('text', 'voice', 'image')),
  attachment_path text,
  extracted_text  text,
  intent          text,
  created_at      timestamptz not null default now()
);

create table public.problems (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references public.tenants(id) on delete cascade,
  session_id       uuid not null references public.tutor_sessions(id) on delete cascade,
  topic_id         uuid not null references public.topics(id) on delete cascade,
  skill_id         uuid references public.topic_skills(id) on delete set null,
  source           text not null check (source in ('generated', 'past_exam', 'doc')),
  source_ref       uuid,
  text             text not null,
  reference_answer text not null,
  solution_steps   jsonb not null default '[]',
  answer_format    text not null check (answer_format in ('expression', 'factored', 'equation',
                                                          'solution_set', 'numeric', 'short_text', 'sql')),
  verified         boolean not null default false,
  difficulty       smallint not null check (difficulty between 1 and 3),
  purpose          text not null check (purpose in ('probe', 'verify', 'practice', 'review')),
  created_at       timestamptz not null default now()
);

create table public.attempts (
  id                   uuid primary key default gen_random_uuid(),
  tenant_id            uuid not null references public.tenants(id) on delete cascade,
  user_id              uuid not null references auth.users(id) on delete cascade,
  problem_id           uuid not null references public.problems(id) on delete cascade,
  topic_id             uuid not null references public.topics(id) on delete cascade,
  skill_id             uuid references public.topic_skills(id) on delete set null,
  answer_text          text,
  verdict              text not null check (verdict in ('correct', 'correct_with_flaw', 'incomplete', 'incorrect')),
  is_correct           boolean not null,      -- what mastery uses (correct_with_flaw → false)
  final_answer_correct boolean,
  error_type           text check (error_type in ('calculation', 'sign', 'wrong_method', 'concept',
                                                  'prerequisite', 'no_answer')),
  first_wrong_line     integer,
  evidence             text,
  method               text check (method in ('doc', 'other')),
  decided_by           text not null check (decided_by in ('sympy', 'llm')),
  confidence           numeric,
  independent          boolean not null default true,
  overridden           boolean not null default false,
  seconds_to_answer    integer,
  created_at           timestamptz not null default now()
);

create table public.topic_progress (
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  exam_prep_id    uuid not null references public.exam_preps(id) on delete cascade,
  topic_id        uuid not null references public.topics(id) on delete cascade,
  mastery         numeric not null,           -- initialised from config bkt.p_init by the app
  level           text not null default 'not_started'
                  check (level in ('not_started', 'weak', 'developing', 'passed')),
  stage           text,
  skill_coverage  jsonb not null default '{}',  -- {skill_id: independent_correct_count}
  attempts_n      integer not null default 0,
  correct_n       integer not null default 0,
  error_counts    jsonb not null default '{}',
  fail_streak     integer not null default 0,
  review_step     integer not null default 0,
  next_review_at  date,
  parked_reason   text,
  parked_at       timestamptz,
  last_seen_at    timestamptz,
  primary key (user_id, topic_id)
);

create table public.user_stats (
  user_id                 uuid primary key references auth.users(id) on delete cascade,
  tenant_id               uuid not null references public.tenants(id) on delete cascade,
  avg_minutes_per_problem numeric,
  avg_session_minutes     numeric,
  updated_at              timestamptz not null default now()
);

create table public.planner_decisions (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  session_id  uuid not null references public.tutor_sessions(id) on delete cascade,
  mode        text not null,
  decision    jsonb not null,
  reason_code text not null,
  inputs      jsonb not null,
  created_at  timestamptz not null default now()
);

create table public.buddy_events (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  session_id uuid not null references public.tutor_sessions(id) on delete cascade,
  topic_id   uuid references public.topics(id) on delete set null,
  role       text not null check (role in ('encourage', 'teach_back', 'ask_trap', 'wrong_demo', 'off_topic')),
  trigger    text not null,
  seed       jsonb,
  message_id uuid references public.messages(id) on delete set null,
  created_at timestamptz not null default now()
);

create table public.checker_disagreements (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  attempt_id  uuid not null references public.attempts(id) on delete cascade,
  sympy_result jsonb not null,
  llm_result   jsonb not null,
  created_at  timestamptz not null default now()
);

-- =====================================================================
-- Observability (flow 2.11)
-- =====================================================================

create table public.ai_calls (
  id             uuid primary key default gen_random_uuid(),
  tenant_id      uuid not null references public.tenants(id) on delete cascade,
  user_id        uuid references auth.users(id) on delete set null,
  session_id     uuid references public.tutor_sessions(id) on delete set null,
  request_id     text,
  purpose        text not null,
  provider       text not null,
  model          text not null,
  prompt_version text,
  tokens_in      integer,
  tokens_out     integer,
  cached_tokens  integer,
  latency_ms     integer,
  cost_usd       numeric,
  status         text not null check (status in ('ok', 'schema_retry', 'fallback', 'degraded', 'error')),
  fallback_used  boolean not null default false,
  created_at     timestamptz not null default now()
);

-- =====================================================================
-- Indexes
-- =====================================================================

create index on public.memberships (tenant_id);
create index on public.exam_preps (tenant_id, user_id);
create index on public.materials (exam_prep_id);
create index on public.chunks (material_id);
create index chunks_embedding_hnsw on public.chunks using hnsw (embedding vector_cosine_ops);
create index on public.topics (exam_prep_id, order_index);
create index on public.topic_skills (topic_id);
create index on public.past_exam_questions (topic_id);
create index on public.tutor_sessions (exam_prep_id, started_at desc);
create index on public.messages (session_id, created_at);
create index on public.problems (session_id);
create index on public.attempts (user_id, topic_id, created_at);
create index on public.topic_progress (exam_prep_id, next_review_at);
create index on public.ai_calls (tenant_id, created_at);

-- =====================================================================
-- Row Level Security (SA-06)
-- Policy pattern: row is visible only inside the caller's tenant;
-- user-private tables also require user_id = auth.uid().
-- Background jobs use the service role (bypasses RLS) and must set tenant_id explicitly.
-- =====================================================================

alter table public.tenants               enable row level security;
alter table public.org_units             enable row level security;
alter table public.memberships           enable row level security;
alter table public.profiles              enable row level security;
alter table public.tutor_profiles        enable row level security;
alter table public.buddy_profiles        enable row level security;
alter table public.exam_preps            enable row level security;
alter table public.materials             enable row level security;
alter table public.material_pages        enable row level security;
alter table public.chunks                enable row level security;
alter table public.ingestion_jobs        enable row level security;
alter table public.topics                enable row level security;
alter table public.topic_skills          enable row level security;
alter table public.past_exam_questions   enable row level security;
alter table public.topic_chunks          enable row level security;
alter table public.scope_changes         enable row level security;
alter table public.scope_versions        enable row level security;
alter table public.tutor_sessions        enable row level security;
alter table public.messages              enable row level security;
alter table public.problems              enable row level security;
alter table public.attempts              enable row level security;
alter table public.topic_progress        enable row level security;
alter table public.user_stats            enable row level security;
alter table public.planner_decisions     enable row level security;
alter table public.buddy_events          enable row level security;
alter table public.checker_disagreements enable row level security;
alter table public.ai_calls              enable row level security;

create policy tenant_read on public.tenants
  for select using (id = public.current_tenant_id());

create policy tenant_rows on public.memberships
  for select using (tenant_id = public.current_tenant_id() and user_id = auth.uid());

-- tenant-scoped tables (shared within a tenant)
create policy tenant_rows on public.org_units           for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.materials           for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.material_pages      for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.chunks              for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.ingestion_jobs      for select using (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.topics              for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.topic_skills        for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.past_exam_questions for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.topic_chunks        for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.scope_changes       for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.scope_versions      for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.problems            for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.messages            for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.planner_decisions   for select using (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.buddy_events        for select using (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.checker_disagreements for select using (tenant_id = public.current_tenant_id());
create policy tenant_rows on public.ai_calls            for select using (tenant_id = public.current_tenant_id());

-- user-private tables (tenant + owner)
create policy owner_rows on public.profiles       for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.tutor_profiles for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.buddy_profiles for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.exam_preps     for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.tutor_sessions for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.attempts       for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.topic_progress for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());
create policy owner_rows on public.user_stats     for all using (tenant_id = public.current_tenant_id() and user_id = auth.uid()) with check (tenant_id = public.current_tenant_id() and user_id = auth.uid());

-- =====================================================================
-- Signup: create a personal tenant, membership and profile
-- =====================================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
  new_tenant uuid;
begin
  insert into public.tenants (type, name)
  values ('personal', coalesce(new.raw_user_meta_data ->> 'name', new.email))
  returning id into new_tenant;

  insert into public.memberships (user_id, tenant_id, role) values (new.id, new_tenant, 'owner');
  insert into public.profiles (user_id, tenant_id, nickname)
  values (new.id, new_tenant, new.raw_user_meta_data ->> 'name');
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- =====================================================================
-- JWT custom claim: tenant_id
-- Enable in Supabase Dashboard → Authentication → Hooks → Custom Access Token
-- (local: [auth.hook.custom_access_token] in supabase/config.toml)
-- =====================================================================

create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql stable
as $$
declare
  claims jsonb;
  tid    uuid;
begin
  select m.tenant_id into tid
  from public.memberships m
  where m.user_id = (event ->> 'user_id')::uuid
  order by m.created_at
  limit 1;

  claims := event -> 'claims';
  if tid is not null then
    claims := jsonb_set(claims, '{tenant_id}', to_jsonb(tid::text));
  end if;
  return jsonb_set(event, '{claims}', claims);
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook from authenticated, anon, public;
grant select on public.memberships to supabase_auth_admin;

create policy auth_admin_reads_memberships on public.memberships
  as permissive for select to supabase_auth_admin using (true);
