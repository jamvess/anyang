-- Real uploads of course files (specs/features/exam-prep/materials-db.md §2.2, §5 · api.md v1.21).
-- One private bucket `materials` for every file a user sends: materials now, room photos and
-- voice later (/sessions/{id}/uploads). Objects live at {tenant_id}/{exam_prep_id}/{material_id}
-- (uuids only, no extension); the user's file name is display text in materials.file_name.

-- materials: the type the API checked when it gave the upload URL, and when the browser said
-- the upload finished. Both null on rows made before this migration.
alter table public.materials add column content_type text;  -- the set of types lives in code
alter table public.materials add column uploaded_at timestamptz;  -- null: URL given, not announced

-- RLS of materials (tenant_rows) already covers the new columns.

-- The bucket. The size limit is the hard cap, config/ai.yaml guards.max_material_mb x 1,048,576;
-- the API checks the tighter cap per type (max_image_mb for images) at /uploaded. The types are
-- MATERIAL_CONTENT_TYPES plus UPLOAD_CONTENT_TYPES in code. SQL cannot read yaml or Python, so
-- tests/unit/test_materials_storage_rules.py checks that these values match.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('materials', 'materials', false, 52428800, array[
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/heic',
  'audio/webm',
  'audio/ogg',
  'audio/mp4'
])
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

-- Storage policies (SA-06): a signed-in user reaches only objects under their tenant's folder.
-- No update policy: a signed upload never overwrites. No policy for anon. Ingestion reads with
-- the service role, which bypasses RLS, at the storage_path that code wrote.
create policy materials_tenant_select on storage.objects
  for select to authenticated
  using (bucket_id = 'materials'
         and (storage.foldername(name))[1] = public.current_tenant_id()::text);

create policy materials_tenant_insert on storage.objects
  for insert to authenticated
  with check (bucket_id = 'materials'
              and (storage.foldername(name))[1] = public.current_tenant_id()::text);

create policy materials_tenant_delete on storage.objects
  for delete to authenticated
  using (bucket_id = 'materials'
         and (storage.foldername(name))[1] = public.current_tenant_id()::text);
