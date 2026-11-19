-- 0009 · materials.storage_path cannot point outside its own prep
-- (specs/features/exam-prep/materials-db.md §2.2 items 7, 9 · AC-29, AC-30, AC-32 · SA-06)
--
-- Found in the self-review of #140. The tenant_rows policy of materials checks only tenant_id,
-- so a user could write any storage_path through PostgREST (anon key + JWT). Ingestion then
-- reads that path with the service role, which skips the storage policies of 0008. A user could
-- also file a row under another tenant's prep, because a foreign key ignores RLS (wider audit:
-- issue #148).
--
-- Only the authenticated role is checked. The service role (ingestion, seed, tests) and
-- migrations are not.

create or replace function public.materials_path_guard()
returns trigger
language plpgsql
security invoker  -- the caller's rights: RLS of exam_preps hides other tenants' preps
set search_path = ''
as $$
begin
  if current_user = 'authenticated' then
    if tg_op = 'INSERT' then
      if new.storage_path is distinct from
           new.tenant_id::text || '/' || new.exam_prep_id::text || '/' || new.id::text then
        raise exception 'materials.storage_path must be {tenant_id}/{exam_prep_id}/{id}'
          using errcode = '42501';
      end if;
      if not exists (
        select 1 from public.exam_preps p
        where p.id = new.exam_prep_id and p.tenant_id = new.tenant_id
      ) then
        raise exception 'materials.exam_prep_id is not an exam prep of this tenant'
          using errcode = '42501';
      end if;
    elsif new.storage_path is distinct from old.storage_path
       or new.tenant_id is distinct from old.tenant_id
       or new.exam_prep_id is distinct from old.exam_prep_id then
      raise exception 'materials.storage_path, tenant_id and exam_prep_id cannot change'
        using errcode = '42501';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists materials_path_guard on public.materials;
create trigger materials_path_guard
  before insert or update on public.materials
  for each row execute function public.materials_path_guard();

-- Rows from before 0008, and rows from seed_scope_demo.py, have no uploaded_at, so GET
-- /materials hid them and confirm answered unknown_material (§2.2 item 9). A row past
-- 'uploaded' was certainly uploaded. A row still 'uploaded' may be a ticket that was never
-- announced, so it stays null.
update public.materials set uploaded_at = created_at
where uploaded_at is null and status <> 'uploaded';
