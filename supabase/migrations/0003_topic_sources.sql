-- Schema items from P3 (data-model.md "ผลการตัดสิน 2026-10-28" items 1 and 3).

-- topic_sources: page ranges of each topic. One topic can have several ranges and span files,
-- e.g. t02 -> sheet-01:2-26, sheet-03:1-1, sheet-03:1-2 (A6 merge_topics `sources` in P3).
-- Used to build topic_chunks (step 5d) and to show sources on the scope page (SM-04, api.md v1.6).
-- Pages are PDF page numbers counted from 1, the same as material_pages.page_no.
create table public.topic_sources (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  topic_id    uuid not null references public.topics(id) on delete cascade,
  material_id uuid not null references public.materials(id) on delete cascade,
  page_from   integer not null,
  page_to     integer not null,
  check (page_from >= 1 and page_to >= page_from)
);

create index on public.topic_sources (topic_id);
create index on public.topic_sources (material_id);

alter table public.topic_sources enable row level security;

create policy tenant_rows on public.topic_sources for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id());

-- past_exam_questions.map_note: the A7 map_questions `note` for every question, mapped or not
-- (data-model.md item 3; the scope page shows it as "AI: ..." · scope-review.md AC-8, AC-14).
alter table public.past_exam_questions add column map_note text;
