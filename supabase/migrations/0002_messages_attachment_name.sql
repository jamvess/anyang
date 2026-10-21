-- messages.attachment_name: the original file name the user sees, e.g. "วิธีทำ.jpg" (api.md v1.3 Message).
-- User-supplied and display only. Storage paths stay uuid-based (attachment_path) and never use this value.
-- Max length is config/ai.yaml guards.max_attachment_name_chars, enforced by the API (truncate by grapheme
-- cluster, keep the extension · data-model.md). No CHECK here, so the limit has a single source.

alter table public.messages add column attachment_name text;
