# ติวเตอร์เรียกชื่อผู้ใช้แทน "คุณ" และผู้ใช้ตั้งชื่อเองได้ (เป้าข้อ 2 ของ advisor)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/tutor-calls-by-name` |
| Checklist item | ยังไม่มีใน `docs/team/sprint-checklists.md` · เป้าข้อ 2 ของ advisor ("ติวเตอร์เรียกชื่อผู้ใช้แทน 'คุณ' และผู้ใช้ตั้งชื่อได้") · ใกล้กับ S5 "API ของบัญชี + persona บน DB … โปรไฟล์ (UM-08, UM-09)" · เพิ่มเข้าเช็คลิสต์ใน `/work-done` |
| Status | in progress · 2026-11-28 |

## สิ่งที่มีอยู่แล้ว (สำรวจ 28 พ.ย.)

- `profiles.nickname text` (null ได้) มีตั้งแต่ `0001_init.sql` · RLS `owner_rows` (tenant + `auth.uid()`) · trigger `handle_new_user` คัดลอก `raw_user_meta_data.name` มาตรงๆ (บัญชี email + password ของ demo ได้ null · ชื่อจาก Google อาจไม่ผ่าน whitelist · api.md รอตัดสิน v1.12 ข้อ 8)
- ทางที่อ่านชื่ออยู่แล้ว: `app/db/room.py` → `ProfileFacts.nickname` → `domain/room.py` (`user_name` หรือ "คุณ") → หัวห้อง `Room.user_name` + คำทัก template `hello_named` "สวัสดี {user_name}!" (`config/messages.yaml` · ไม่เรียก AI)
- **prompt ทุกตัวยังไม่ได้รับชื่อ:** `tutor_reply/v2` (problem, conversation, message) · `explain_check/v3` · `session_summary/v1` · `open_session/v2` · ai-orchestration §2.7 ข้อ 5 บอกไว้แล้วว่าตอนนี้ยังไม่มี prompt ไหนใช้ nickname
- `GET /me/profile`, `PUT /me/profile` มีแล้วแต่**เป็น stub** (`routers/persona.py` · `X-Stub`) · `PUT` ต้องส่งทุก field (`education_level`, `explain_language`, `auto_read` ซึ่งยังไม่มีคอลัมน์) · `nickname` ใช้ `PersonaText` (whitelist ไทย/อังกฤษ/ตัวเลข/ช่องว่าง · ไม่เกิน `guards.max_persona_text_chars` = 20 · นับ code point)
- test สัญญาของ `PUT /me/profile` มีแล้วใน `tests/unit/test_persona_api_contract.py` (review แล้ว ห้ามแก้)
- ยังไม่มี isolation test ของ `profiles` ใน `test_rls_isolation.py`

## Plan

- [ ] 1. 🤖 `/spec-feature UM-08 UM-09` → `specs/features/platform/display-name.md` (ข้อเสนอ api.md อยู่ใน §10)
- [ ] 2. 🙋 Junior review spec + ตัดสินคำถามใน §10 + ok ให้แก้ `specs/system/api.md` (shared · บอกกลุ่ม)
- [ ] 3. 🤖 `/spec-to-tests` → unit (validation, PATCH/GET, stub เมื่อไม่มี token) + integration บน DB จริง (บันทึก, อ่านกลับ, หัวห้องและคำทักใช้ชื่อใหม่, RLS: A แก้/อ่านชื่อ B ไม่ได้)
- [ ] 4. 🙋 Junior review test
- [ ] 5. 🤖 `/implement-feature` · `app/db/profile.py` (repository ผ่าน JWT ผู้ใช้) · `GET`/`PATCH /me/display-name` ตาม spec · ฟังก์ชัน `prompt_user_name()` ใน `domain/` (ตรวจ whitelist ซ้ำตอนประกอบ prompt · ไม่ผ่าน → None) ให้ Jam ใช้ · api.md + `apps/web/lib/api-schema.ts`
- [ ] 6. 🤖 handoff: รายการให้ Jam (prompt) และ May (หน้าตั้งค่า) ใน PR description + ข้อความกลุ่ม
- [ ] 7. 🙋 ลองกับ `anyang-dev`: login demo → PATCH ชื่อ → เปิดห้องติวใหม่ → หัวห้องและคำทักเป็นชื่อใหม่ (ไม่มี migration · ไม่ต้อง `db push`)

## Definition of done

- ผู้ใช้ที่มี token อ่านและตั้งชื่อที่ให้ติวเตอร์เรียกได้ · ค่าที่ไม่ผ่านกฎได้ `422 validation_error` · ลบชื่อแล้วกลับเป็น "คุณ"
- หัวห้องและคำทักของ session ใหม่ใช้ชื่อที่ตั้ง (TM-13 AC-11 เดิมยังผ่าน)
- isolation test ของ `profiles` ผ่าน (SA-06)
- api.md อัปเดต · CI ผ่าน · `/code-review` แล้ว
- PR บอกชัดว่า Jam ต้องแก้ prompt อะไร และ May ต้องทำอะไรในหน้าตั้งค่า

## Decisions

- 2026-11-28 · ภาษาที่ใช้อธิบาย (`explain_language`) ไม่อยู่ใน scope · Junior สั่ง
- 2026-11-28 · ทำใน worktree `../anyang-name` เพราะ working tree หลักกำลังรัน P9-lite

## Next step

รอ Junior ok แผน · แล้ว `/spec-feature UM-08 UM-09` ใน `../anyang-name`

## Waiting on

- Jam: prompt version ใหม่ที่รับชื่อ (หลัง PR นี้)
- May: ช่องชื่อในหน้าตั้งค่า (หลัง PR นี้)

## Notes for next time

- worktree: `C:\Users\Junior\projects\anyang-name` · ลบด้วย `git worktree remove ../anyang-name` หลัง merge
