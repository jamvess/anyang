# จบ session + สรุปผลการติว (demo ขั้น 9)

| | |
|---|---|
| Owner | Jam (item of Junior: endpoint · ส่วน `session_summary` เป็นของ Jam) |
| Branch | `feat/session-end-db` |
| Checklist item | ⭐ demo ขั้น 9: `POST /sessions/{id}/end` จริง (`ended_at` + สรุป) (TM-13, PM-05) · และส่วน "สรุป session ด้วย `session_summary` (PM-05)" ของ ⭐ demo ขั้น 8–9 (Jam) |
| Status | in progress · 2026-11-14 |

## Plan

`POST /sessions/{id}/end` ยังเป็น stub (สรุปเดิมทุกครั้ง ไม่บันทึกอะไร) · prompt `session_summary` ยังไม่มี (`config/ai.yaml` มีแถวแล้ว) · api.md v1.9 เขียนข้อเสนอไว้แล้ว (รอตัดสินข้อ 1, 6, 7 ของ Junior) · แผนคือทำตามข้อเสนอนั้นในทางที่มี token แล้วให้ Junior ดูย้อนหลัง

- [x] 1. 🤖 (14 พ.ย. · Jam ok) `/spec-feature` → `specs/features/tutor/session-end-db.md`: มี token → 404 / 409 / 503 ก่อน SSE · ตั้ง `ended_at` + `end_reason = 'user'` ด้วยคำสั่งเดียวที่มีเงื่อนไข `ended_at is null` (ชนกัน → 409) · code คิด facts ของ session (โจทย์ที่ทำ, ถูกกี่ข้อ, หัวข้อและระดับตอนนี้จาก `topic_progress`) → `session_summary/v1` (small · 1–2 บรรทัด) → `session_end` → บันทึก `tutor_sessions.summary` + ข้อความ `tutor` ใน `messages` (`done.message_ids`) · AI ล้ม → สรุปจาก template ของ code · ไม่มี token → stub เดิม · กลับมาเปิดห้องได้ session ใหม่ + โจทย์ค้างเดิม (TM-13) · 🙋 Jam review spec
- [x] 2. 🤖 (14 พ.ย. · Jam ok) `/spec-to-tests` (fake repository + fake provider · integration: RLS + 409 ชนกัน) · 🙋 Jam review test
- [x] 3. 🤖 (14 พ.ย. · green 1716 · Jam ok) prompt `prompts/session_summary/v1.md` + implement จน green · ไฟล์กลาง (`config/ai.yaml` ถ้าต้องตั้ง `thinking`, `config/messages.yaml` template สำรอง, `specs/system/api.md`) ถามก่อน
- [ ] 4. 🤖 รันจริงบน Vertex: เปิดห้อง → ตอบ 2 ข้อ → จบ session → สรุป 2 บรรทัด → เปิดห้องใหม่ได้ session ใหม่ · 🙋 Jam ดูผล
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- มี token: กดจบได้สรุป 1–2 บรรทัดจาก facts จริงของ session · `tutor_sessions.ended_at`, `end_reason`, `summary` ถูกบันทึก · สรุปเป็นข้อความในแชท (กลับมาโหลดยังเห็น)
- จบซ้ำหรือจบพร้อมกัน → `409 session_already_ended` · session ของคนอื่น → `404`
- AI ล้ม → ยังได้สรุปจาก template และ session จบ
- ไม่มี token → stub เดิม · test เดิมไม่ต้องแก้

## Decisions

- 2026-11-14 · นับคำตอบของ session จาก `attempts.created_at ≥ started_at` (ไม่เพิ่มคอลัมน์) · ไม่คำนวณ mastery ที่เปลี่ยน (Jam ok spec)
- 2026-11-14 · ไฟล์กลาง: `messages.yaml` 1.1 template สรุปสำรอง · `ai.yaml` 1.21 `session_summary` `thinking: minimal` · `api.md` v1.19 (Jam ok)
- 2026-11-14 · ทำ endpoint ของ Junior ช่วง solo ตามข้อเสนอ api.md v1.9 (SSE, ไม่นับ rate limit, 1–2 บรรทัด, เก็บเป็นข้อความในแชทด้วย) · Junior ดูย้อนหลัง

## Next step

ขั้น 4: รันจริงบน Vertex (เปิดห้อง → ตอบ 2 ข้อ → จบ → สรุป → เปิดใหม่)

## Waiting on

- Junior: ดูย้อนหลังเรื่อง endpoint + การเขียน `tutor_sessions` · `db push` ของ `0005`–`0007` ขึ้น `anyang-dev` (ไม่มี migration ใหม่ในงานนี้ ถ้า spec ไม่ต้องเพิ่มคอลัมน์)

## Notes for next time

- ไม่มี
