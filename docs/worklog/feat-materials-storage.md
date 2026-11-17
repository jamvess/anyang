# materials + Storage จริง (demo ขั้น 3)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/materials-storage` |
| Checklist item | ⭐ demo ขั้น 3: `POST /exam-preps/{id}/materials` + `POST /materials/{id}/uploaded` + `POST /exam-preps/{id}/materials/confirm` จริง · signed upload URL · bucket + storage policy (migration ใหม่ + isolation test) (CM-03, CM-07) |
| Status | in progress · 2026-11-17 |

## Plan

- [x] 1. 🤖 `/spec-feature` → `specs/features/exam-prep/materials-db.md` (CM-03, CM-06, CM-07, SA-06) · มี token แล้ว 4 endpoint ใช้ DB + Storage จริง: `POST /exam-preps/{id}/materials` (แถว `materials` + signed upload URL จาก JWT ของผู้ใช้) · `POST /materials/{id}/uploaded` (เช็คว่ามีไฟล์จริงใน Storage + ขนาดจริง → เรียก `classify_material` เบื้องหลัง) · `GET /exam-preps/{id}/materials` (หน้า S10 poll) · `POST /materials/confirm` (`kind`, `kind_confirmed`, `status = confirmed` → `get_ingestion_runner().start()`) · ไม่มี token ยังได้ stub เหมือนเดิม · `retry` และ `DELETE` ยังเป็น stub (หลัง demo) · ใส่ข้อเสนอเพื่อปิดคำถามที่ยังเปิดของ api.md v1.10 ข้อ 2, 5, 6
- [x] 2. 🙋 Junior review spec + ตัดสินคำถามที่ยังเปิด (§10) · api.md เป็นไฟล์กลาง: ถ้า ok ให้แก้ใน PR นี้แล้วบอกกลุ่ม
- [x] 3. 🤖 `/spec-to-tests` · unit (repo + storage ปลอม · ทางมี/ไม่มี token · 404 ของ tenant อื่น · 409 · 422) + integration บน `anyang-dev` (อัปโหลดผ่าน signed URL ได้จริง · user B อ่าน/เขียน/ขอ URL ใน prefix ของ A ไม่ได้ · แถว `materials` แยก tenant) · test เริ่มต้นด้วย requirement ID
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
- 2026-11-16 · ตรวจโค้ดของ Jam ก่อนเขียน spec (Junior ขอ): bucket `materials` (`MATERIALS_BUCKET`) และ path `{tenant_id}/{exam_prep_id}/{material_id}` ไม่มีนามสกุล ตรงกับที่ ingestion อ่านจาก `storage_path` · ใช้ชื่อเดิมของ Jam · bucket เดียว private ใช้ร่วมกับรูป/เสียงของห้องติว · เพดาน `guards.max_material_mb` / `max_image_mb` · bucket 50 MB เป็นเพดานแข็ง · path ใช้ uuid ล้วน ชื่อไฟล์ใช้แสดงผลอย่างเดียว
- 2026-11-16 · reset DB password ของ `anyang-dev` แล้ว + ปิด "Allow new users to sign up" ใน Dashboard แล้ว (Junior) · `.env` อัปเดตแล้ว · ติ๊กข้อ "reset database password" ใน checklist ใน PR นี้ · advisor update เลื่อนออกไป

- 2026-11-17 · review spec (Junior): §2.2, §9, §11 ok · §10 ข้อ 2–7 ตามข้อเสนอ · ข้อ 1 ถาม Jam · แก้ api.md เป็น v1.21 ใน PR นี้ (บอกกลุ่มก่อน merge) · **เพิ่ม:** `user_note` เข้า prompt สกัดหัวข้อ ต้องอยู่ใน data block แบบ `<document>` เท่านั้น ไม่ใช่คำสั่ง (§2.4 ข้อ 9 · AC-27) · spec approved
- 2026-11-17 · ตรวจ prompt แล้ว: A1 v1 ใส่ note ใน `<note>`, A6 v2 ใน `<document name="user_notes">` อยู่แล้ว · A5 ไม่รับ note · gateway กันการปิด block ให้ (`prompt_data.as_data`) · เจอเรื่องใหม่ §10 ข้อ 8 (note หลายบรรทัดปลอมบรรทัดของไฟล์อื่นใน A6) ส่งให้ Jam

## Next step

ข้อ 4: Junior review test (ตาราง AC → test ใน PR description / ข้อความ session 2026-11-17) · ไฟล์: `tests/unit/test_materials_db_api.py`, `tests/unit/test_materials_storage_rules.py`, `tests/integration/test_materials_storage_db.py` · ok แล้วไปข้อ 5 (`0008` + `/implement-feature`)

## Waiting on

- Jam: spec §10 ข้อ 1 (`_image_type` อ่านนามสกุลจากชื่อไฟล์ · WEBP/HEIC/PPTX/DOCX ล้มตอน classify) · ข้อ 8 (note หลายบรรทัดใน A6) · ตรวจ prompt A1/A6 ตาม §2.4 ข้อ 9 · รับทราบข้อ 5 · ส่งข้อความแล้ว 2026-11-17 · ไม่ขวางวิดีโอที่ใช้ PDF

## Notes for next time

- test ที่ต้องการ interface ใหม่ (เขียนไว้ใน docstring ของ `test_materials_db_api.py`): `app.db.materials` (repo) · `app.services.material_storage` (Storage adapter) · `IngestionRunner.classify(material_id)` (เพิ่มในไฟล์ของ Jam · บอก Jam) · `get_ingestion_runner` เป็น dependency ของ router
- AC-27 (`test_CM04_user_note_*`) ผ่านอยู่แล้วเพราะ prompt A1 v1 / A6 v2 ถูกต้อง · เป็น test กันถอยหลัง ไม่ใช่ test แดง
- รัน `uv run pytest tests/unit` ในเครื่อง Junior: test เดิมราว 350 ตัวล้ม (401 และ "unit tests must not reach the network" ไปที่ host ของ `anyang-dev`) ทั้งที่ไม่ได้แก้ code ใน app · น่าจะมาจากค่าใน `.env` ในเครื่อง · ยังไม่ได้ตรวจ (ห้ามอ่าน `.env`) · ดู CI ของ PR นี้เทียบ

- ingestion ของ Jam อ่านไฟล์ด้วย service role จาก bucket `materials` (`MATERIALS_BUCKET` ใน `app/services/ingestion.py`) ที่ `materials.storage_path` · ชื่อ bucket และ path ต้องตรงกันนี้
- ปิด sign-up แล้ว: integration test สร้าง user ด้วย admin API (service role) อยู่แล้ว จึงไม่กระทบ · ถ้าต้องการบัญชีทดสอบใหม่ให้สร้างใน Dashboard
- `materials` RLS เป็นแบบทั้ง tenant (`tenant_rows`) ไม่ใช่ต่อ user · tenant เป็นแบบ personal (1 คน) จึงเท่ากัน
