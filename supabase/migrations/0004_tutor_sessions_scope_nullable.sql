-- tutor_sessions.scope_version_id may be null: a session that started before the exam scope was
-- confirmed (the demo path while ingestion and scope/confirm are not real · room-sessions-db.md,
-- data-model.md). Once they are real, the planner attaches exam_preps.active_scope_version_id to
-- every new session (rule for Jam's planner in data-model.md). The foreign key stays.

alter table public.tutor_sessions alter column scope_version_id drop not null;
