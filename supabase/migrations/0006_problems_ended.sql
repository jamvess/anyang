-- When a problem of the room is over, and the working steps sent so far
-- (specs/features/tutor/room-answers-db.md §2.2, §5 · demo-room.md §2 K).
-- ended_at: null while the problem waits for an answer. A wrong answer with a hint has an
-- attempts row but the problem goes on, so "open" can no longer mean "no attempt" (#131).
-- working_steps: the right steps of answers that were not finished yet (`continue`), counted
-- toward the working the final answer needs (§2 K item 3).
-- Proposed by Jam in solo time 2026-11-14 for the demo of 23 Nov; Junior reviews afterwards.

alter table public.problems add column ended_at timestamptz;
alter table public.problems add column working_steps integer not null default 0
  check (working_steps >= 0);

-- The room reads the latest open problem of a session's prep.
create index on public.problems (session_id, created_at desc) where ended_at is null;

-- RLS is unchanged: the table already has tenant_rows (tenant_id = current_tenant_id()).
