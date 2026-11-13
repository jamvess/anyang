-- ingestion_jobs of the whole exam prep (specs/features/scope/ingestion.md §5 · api.md v1.11
-- "รอตัดสิน" item 1): topics and stars are built once per prep, not per file, so their rows have no
-- material_id. Every row now names its exam_prep_id, so the progress of a prep is one query.
-- Proposed by Jam in solo time 2026-11-13 for the demo of 23 Nov; Junior reviews afterwards.

alter table public.ingestion_jobs add column exam_prep_id uuid references public.exam_preps(id) on delete cascade;

update public.ingestion_jobs j
   set exam_prep_id = m.exam_prep_id
  from public.materials m
 where m.id = j.material_id;

alter table public.ingestion_jobs alter column exam_prep_id set not null;
alter table public.ingestion_jobs alter column material_id drop not null;

create index on public.ingestion_jobs (exam_prep_id);

-- RLS is unchanged: the table already has tenant_rows (tenant_id = current_tenant_id()).
