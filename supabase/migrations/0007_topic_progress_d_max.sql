-- The hardest difficulty a student has answered right independently, per topic
-- (specs/features/planner/topic-progress-db.md §5 · learning-model.md §4 · room-problems-db.md
-- §10 item 2). mastery_eff caps the mastery of a topic until its target difficulty is solved,
-- so the progress card needs it next to mastery. 0 = none yet.
-- Proposed by Jam in solo time 2026-11-14 for the demo of 23 Nov; Junior reviews afterwards.

alter table public.topic_progress add column d_max smallint not null default 0
  check (d_max between 0 and 3);

-- RLS is unchanged: the table already has owner_rows (tenant and auth.uid()).
