# หน้าตรวจขอบเขตอ่าน/ยืนยันบน DB (demo ขั้น 5)

| | |
|---|---|
| Owner | Jam (item of Junior · Junior ให้ตัดสินใจไปก่อน แล้วมาเช็คทีหลัง · 14 พ.ย.) |
| Branch | `feat/scope-db` |
| Checklist item | ⭐ demo ขั้น 5: `GET /exam-preps/{id}/scope` อ่าน DB · `POST /scope/confirm` เขียน `scope_versions` + `active_scope_version_id` (SM-09) |
| Status | in progress · 2026-11-14 |

## Plan

`GET /exam-preps/{id}/scope`, `POST /exam-preps/{id}/scope/confirm` และ `GET /topics/{id}/sources` ยังเป็น stub · หัวข้อ, ดาว, เหตุผล, ช่วงหน้า และข้อสอบเก่าอยู่ใน DB แล้วจาก ingestion (#130) · api.md v1.6 เขียนรูปร่างและข้อเสนอไว้แล้ว (รอตัดสินข้อ 1–5 ของ Junior) · แผนคือทำตามข้อเสนอนั้นในทางที่มี token · หน้า scope ของ May (S12) ต่อ API จริงได้

- [x] 1. 🤖 (14 พ.ย. · Jam ok) `/spec-feature` → `specs/features/scope/scope-db.md`: มี token → `GET /scope` อ่าน `topics` (รวมที่ตัดออก · `stars` 0), `source_label` จาก `topic_sources` + `materials.file_name`, `unmapped_questions`, `status` จาก `active_scope_version_id` · ดาวยังไม่ครบ → `409 scope_not_ready` · `POST /scope/confirm` → `409` 3 แบบ · สร้าง `scope_versions` (version ถัดไป · `snapshot` ของหัวข้อ) → ตั้ง `active_scope_version_id` → หัวข้อ `draft` เป็น `confirmed` · ยืนยันพร้อมกัน 2 ครั้ง → `409` (unique ของ version) · `GET /topics/{id}/sources` อ่านหน้าใน `material_pages` + ข้อสอบของหัวข้อ · ไม่มี token → stub เดิม · 🙋 Jam review spec
- [ ] 2. 🤖 `/spec-to-tests` (fake repository · integration: RLS + ยืนยันแล้วห้องติวใช้ scope version) · 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · ไฟล์กลาง (`specs/system/api.md`) ถามก่อน
- [ ] 4. 🤖 รันกับข้อมูลจริงของ MTH10101 (ingestion ในเครื่อง → `GET /scope` → confirm → เปิดห้อง) · 🙋 Jam ดูผล
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- มี token: หน้า scope ได้หัวข้อจริง (ดาว, เหตุผล, ที่มา, ข้อสอบที่ map ไม่ได้) · กดยืนยันแล้วได้ `scope_versions` แถวใหม่ + `active_scope_version_id` + หัวข้อ `confirmed` · ยืนยันซ้ำ → `409 scope_already_confirmed`
- ดาวยังไม่ครบ → `409 scope_not_ready` · ไม่มีหัวข้อเหลือ → `409 scope_empty` · prep ของคนอื่น → `404`
- ไม่มี token → stub เดิม · test เดิมไม่ต้องแก้

## Decisions

- 2026-11-14 · รวม `GET /topics/{id}/sources` ใน PR นี้ (Jam ok)
- 2026-11-14 · Junior ให้ Jam ตัดสินใจเรื่อง DB ของ scope ไปก่อน (ตามข้อเสนอ api.md v1.6) แล้วมาเช็คทีหลัง

## Next step

ขั้น 2: เขียน test (red) จาก AC-1 ถึง AC-12 + AC-tenant

## Waiting on

- Junior: ดูย้อนหลัง + ยืนยันข้อรอตัดสิน api.md v1.6 · `db push` ของ `0007` ขึ้น `anyang-dev` (จาก #135)
- May: หน้า scope (S12) ต่อ API จริง (demo ขั้น 5 ฝั่งเว็บ)

## Notes for next time

- ไม่มี
