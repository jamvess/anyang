# materials + Storage จริง (demo ขั้น 3)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/materials-storage` |
| Checklist item | ⭐ demo ขั้น 3: `POST /exam-preps/{id}/materials` + `POST /materials/{id}/uploaded` + `POST /exam-preps/{id}/materials/confirm` จริง · signed upload URL · bucket + storage policy (migration ใหม่ + isolation test) (CM-03, CM-07) |
| Status | in progress · 2026-11-16 |

## Plan

- [ ] 1. 🤖 `/spec-feature` → `specs/features/exam-prep/materials-db.md` (CM-03, CM-06, CM-07, SA-06) · มี token แล้ว 4 endpoint ใช้ DB + Storage จริง: `POST /exam-preps/{id}/materials` (แถว `materials` + signed upload URL จาก JWT ของผู้ใช้) · `POST /materials/{id}/uploaded` (เช็คว่ามีไฟล์จริงใน Storage + ขนาดจริง → เรียก `classify_material` เบื้องหลัง) · `GET /exam-preps/{id}/materials` (หน้า S10 poll) · `POST /materials/confirm` (`kind`, `kind_confirmed`, `status = confirmed` → `get_ingestion_runner().start()`) · ไม่มี token ยังได้ stub เหมือนเดิม · `retry` และ `DELETE` ยังเป็น stub (หลัง demo) · ใส่ข้อเสนอเพื่อปิดคำถามที่ยังเปิดของ api.md v1.10 ข้อ 2, 5, 6
- [ ] 2. 🙋 Junior review spec + ตัดสินคำถามที่ยังเปิด (§10) · api.md เป็นไฟล์กลาง: ถ้า ok ให้แก้ใน PR นี้แล้วบอกกลุ่ม
- [ ] 3. 🤖 `/spec-to-tests` · unit (repo + storage ปลอม · ทางมี/ไม่มี token · 404 ของ tenant อื่น · 409 · 422) + integration บน `anyang-dev` (อัปโหลดผ่าน signed URL ได้จริง · user B อ่าน/เขียน/ขอ URL ใน prefix ของ A ไม่ได้ · แถว `materials` แยก tenant) · test เริ่มต้นด้วย requirement ID
- [ ] 4. 🙋 Junior review test (อ่านตาราง AC → test ที่ Claude สรุป)
- [ ] 5. 🤖 `supabase/migrations/0008_materials_storage.sql`: bucket `materials` แบบ private · `file_size_limit` = `guards.max_material_mb` · `allowed_mime_types` ตาม api.md · policy บน `storage.objects` (insert/select/update/delete) เฉพาะเมื่อโฟลเดอร์แรกของ path = `current_tenant_id()` · แล้ว `/implement-feature`: `app/db/materials.py` (JWT ของผู้ใช้) + ตัวขอ signed URL + router + งานเบื้องหลัง classify จนทุก test ผ่าน
- [ ] 6. 🙋 Junior review SQL ของ `0008` แล้วรัน `npx supabase db push` ขึ้น `anyang-dev` (ข้อความบอกกลุ่มเรื่อง migration + RLS · Claude ร่างให้)
- [ ] 7. 🤖 รัน integration บน `anyang-dev` + ลองครบ flow ในเครื่องกับ Gemini บน Vertex: สร้าง prep → ขอ URL → `PUT` PDF จาก `evals/topics/mth10101/raw/` → `/uploaded` → `kind` ขึ้น → confirm → `GET /ingestion` จนหัวข้อ + ดาวขึ้น → `GET /scope` · ใช้บัญชีทดสอบของตัวเอง (ไม่ใช่บัญชี demo · กติกา D2 (ก))
- [ ] 8. 🙋 บอกกลุ่ม (migration `0008`, api.md) + บอก May ว่าหน้าอัปโหลดต่อ API จริงได้แล้ว → `/work-done`

## Definition of done

- มี token: `POST /exam-preps/{id}/materials` สร้างแถว `materials` (`status = uploaded`, `storage_path = {tenant_id}/{exam_prep_id}/{material_id}`) และคืน signed upload URL ที่ `PUT` ไฟล์เข้า bucket `materials` ได้จริง
- `POST /materials/{id}/uploaded` → `202` แล้ว classify เบื้องหลังจน `kind` ขึ้นใน `GET /exam-preps/{id}/materials` (CM-06, CM-07)
- `POST /exam-preps/{id}/materials/confirm` → `202 {queued}` แล้ว ingestion ของ Jam สร้าง `topics` + ดาวของ prep นั้น
- bucket + storage policy อยู่ใน migration `0008` · isolation test พิสูจน์ว่า tenant อื่นอ่าน เขียน หรือขอ URL ใน prefix ของเราไม่ได้ (SA-06)
- ไม่มี token + `AUTH_REQUIRED=false` ยังได้ stub (`X-Stub`) เหมือนเดิม · test สัญญาเดิมยังผ่าน
- CI ผ่าน · `0008` ขึ้น `anyang-dev` แล้ว · เสร็จภายใน พฤ. 19 พ.ย. (ทุกขั้นต่อกันได้ในเครื่องเดียว)

## Decisions

- 2026-11-16 · ขอบเขต: 4 endpoint (รวม `GET /materials` เพราะหน้า S10 ต้อง poll) · `retry` และ `DELETE` ยังเป็น stub จนหลัง demo · เป้า: เสร็จ 19 พ.ย. เพื่อวิดีโอ 23 พ.ย. (Junior)
- 2026-11-16 · reset DB password ของ `anyang-dev` แล้ว + ปิด "Allow new users to sign up" ใน Dashboard แล้ว (Junior) · `.env` อัปเดตแล้ว · ติ๊กข้อ "reset database password" ใน checklist ใน PR นี้ · advisor update เลื่อนออกไป

## Next step

ข้อ 1: รัน `/spec-feature` สร้าง `specs/features/exam-prep/materials-db.md` จาก api.md "สร้างการเตรียมสอบและใส่ไฟล์" (v1.10 · v1.13), `ingestion.md` §2.1 + §9, `data-model.md` (Storage path) และ `create-exam-prep.md` (รูปแบบมี/ไม่มี token)

## Waiting on

ไม่มี

## Notes for next time

- ingestion ของ Jam อ่านไฟล์ด้วย service role จาก bucket `materials` (`MATERIALS_BUCKET` ใน `app/services/ingestion.py`) ที่ `materials.storage_path` · ชื่อ bucket และ path ต้องตรงกันนี้
- ปิด sign-up แล้ว: integration test สร้าง user ด้วย admin API (service role) อยู่แล้ว จึงไม่กระทบ · ถ้าต้องการบัญชีทดสอบใหม่ให้สร้างใน Dashboard
- `materials` RLS เป็นแบบทั้ง tenant (`tenant_rows`) ไม่ใช่ต่อ user · tenant เป็นแบบ personal (1 คน) จึงเท่ากัน
