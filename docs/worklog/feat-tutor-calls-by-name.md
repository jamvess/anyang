# ติวเตอร์เรียกชื่อผู้ใช้แทน "คุณ" และผู้ใช้ตั้งชื่อเองได้ (เป้าข้อ 2 ของ advisor)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/tutor-calls-by-name` |
| Checklist item | ยังไม่มีใน `docs/team/sprint-checklists.md` · เป้าข้อ 2 ของ advisor ("ติวเตอร์เรียกชื่อผู้ใช้แทน 'คุณ' และผู้ใช้ตั้งชื่อได้") · ใกล้กับ S5 "API ของบัญชี + persona บน DB … โปรไฟล์ (UM-08, UM-09)" · เพิ่มเข้าเช็คลิสต์ใน `/work-done` |
| Status | paused · 2026-11-28 · รอ Junior review test |

## สิ่งที่มีอยู่แล้ว (สำรวจ 28 พ.ย.)

- `profiles.nickname text` (null ได้) มีตั้งแต่ `0001_init.sql` · RLS `owner_rows` (tenant + `auth.uid()`) · trigger `handle_new_user` คัดลอก `raw_user_meta_data.name` มาตรงๆ (บัญชี email + password ของ demo ได้ null · ชื่อจาก Google อาจไม่ผ่าน whitelist · api.md รอตัดสิน v1.12 ข้อ 8)
- ทางที่อ่านชื่ออยู่แล้ว: `app/db/room.py` → `ProfileFacts.nickname` → `domain/room.py` (`user_name` หรือ "คุณ") → หัวห้อง `Room.user_name` + คำทัก template `hello_named` "สวัสดี {user_name}!" (`config/messages.yaml` · ไม่เรียก AI)
- **prompt ทุกตัวยังไม่ได้รับชื่อ:** `tutor_reply/v2` (problem, conversation, message) · `explain_check/v3` · `session_summary/v1` · `open_session/v2` · ai-orchestration §2.7 ข้อ 5 บอกไว้แล้วว่าตอนนี้ยังไม่มี prompt ไหนใช้ nickname
- `GET /me/profile`, `PUT /me/profile` มีแล้วแต่**เป็น stub** (`routers/persona.py` · `X-Stub`) · `PUT` ต้องส่งทุก field (`education_level`, `explain_language`, `auto_read` ซึ่งยังไม่มีคอลัมน์) · `nickname` ใช้ `PersonaText` (whitelist ไทย/อังกฤษ/ตัวเลข/ช่องว่าง · ไม่เกิน `guards.max_persona_text_chars` = 20 · นับ code point)
- test สัญญาของ `PUT /me/profile` มีแล้วใน `tests/unit/test_persona_api_contract.py` (review แล้ว ห้ามแก้)

## Plan

- [x] 1. 🤖 (28 พ.ย.) `/spec-feature UM-08 UM-09` → `specs/features/platform/display-name.md`
- [x] 2. 🙋 (28 พ.ย. · approved) Junior review spec + ตัดสินคำถามใน §10 + ok ให้แก้ `specs/system/api.md` → v1.25 (shared · Junior บอกกลุ่มก่อน merge)
- [x] 3. 🤖 (28 พ.ย. · red) `/spec-to-tests` → unit (กฎของ body, PATCH/GET, stub, token, ไม่มีแถว, DB ล่ม, `prompt_user_name`) + integration บน DB จริง (บันทึก, อ่านกลับ, `setup_step`, หัวห้องและคำทักใช้ชื่อใหม่, ไม่มีแถว, tenant) + RLS ของ `profiles`
- [ ] 4. 🙋 Junior review test
- [ ] 5. 🤖 `/implement-feature` · `app/db/profile.py` (repository ผ่าน JWT ผู้ใช้ · `get()`, `update(changes)`) · `app/domain/profile.py` (`prompt_user_name()` + `setup_step`) · route `PATCH /me/profile` + `GET` ทาง DB ใน `app/routers/persona.py` · `apps/web/lib/api-schema.ts`
- [ ] 6. 🤖 handoff: รายการให้ Jam (prompt · spec §9) และ May (หน้าตั้งค่า · spec §9) ใน PR description + ข้อความกลุ่ม
- [ ] 7. 🙋 ลองกับ `anyang-dev`: login demo → PATCH ชื่อ → เปิดห้องติวใหม่ → หัวห้องและคำทักเป็นชื่อใหม่ (ไม่มี migration · ไม่ต้อง `db push`)

## Definition of done

- ผู้ใช้ที่มี token อ่านและตั้งชื่อที่ให้ติวเตอร์เรียกได้ · ค่าที่ไม่ผ่านกฎได้ `422 validation_error` · ลบชื่อแล้วกลับเป็น "คุณ"
- หัวห้องและคำทักของ session ใหม่ใช้ชื่อที่ตั้ง (TM-13 AC-11 เดิมยังผ่าน)
- isolation test ของ `profiles` ผ่าน (SA-06)
- api.md อัปเดต · CI ผ่าน · `/code-review` แล้ว
- PR บอกชัดว่า Jam ต้องแก้ prompt อะไร และ May ต้องทำอะไรในหน้าตั้งค่า

## Decisions

- 2026-11-28 · ภาษาที่ใช้อธิบาย (`explain_language`) ไม่อยู่ใน scope · Junior สั่ง
- 2026-11-28 · Junior: `PATCH /me/profile` ส่งบาง field (ไม่ใช่ endpoint แยก) เพราะจะเพิ่มภาษาทีหลัง · `nickname` ใช้กฎ persona + ตัดช่องว่าง · ว่าง/null → null → "คุณ" · `GET` คืนชื่อดิบจาก Google แต่ `prompt_user_name()` กรองก่อนเข้า prompt
- 2026-11-28 · Junior: spec §10 ข้อ 1 `{}` → `422` · ข้อ 2 ไม่มีแถว → `404 not_found` ไม่สร้างแถว · ข้อ 3 (`explain_language` นอก enum) นอก scope ปิดพร้อมงานภาษา · `api.md` v1.25 ใน PR นี้
- 2026-11-28 · ทำใน worktree `../anyang-name` เพราะ working tree หลักกำลังรัน P9-lite

## Done today (28 พ.ย.)

- สำรวจของที่มีอยู่ · spec `specs/features/platform/display-name.md` (approved) · `api.md` v1.25
- red test: `apps/api/tests/unit/test_profile_api.py`, `apps/api/tests/unit/test_prompt_user_name.py` (ล้มตอน import เพราะยังไม่มี `app.db.profile`, `app.domain.profile`) · `apps/api/tests/integration/test_profile_db.py` 8 ตัวล้มเพราะ `PATCH` 405 และ `GET` ยังเป็น stub · `test_SA06_profiles_isolated` ท้าย `test_rls_isolation.py` **ผ่านแล้ว** (RLS เดิมกันอยู่แล้ว · เป็นหลักฐาน SA-06)
- test เดิม 2158 passed · ล้ม 1 ตัวตามคาด: `test_api_md_endpoints.py::test_apimd_every_endpoint_in_the_tables_is_in_openapi` (api.md มี `PATCH /me/profile` แล้วแต่ยังไม่มี route · เขียวเองเมื่อ implement)

## Next step

Junior review test 4 ไฟล์ข้างบน (ตาราง AC → test อยู่ใน PR #181 · Claude ห้ามแก้ test หลัง review) · ok แล้วรัน `/implement-feature specs/features/platform/display-name.md` ใน worktree `C:\Users\Junior\projects\anyang-name` ตามข้อ 5

## Waiting on

- Junior: review test (พรุ่งนี้เย็น 29 พ.ย.)
- Jam: prompt version ใหม่ที่รับชื่อ (หลัง PR นี้)
- May: ช่องชื่อในหน้าตั้งค่า (หลัง PR นี้)

## Notes for next time

- worktree: `C:\Users\Junior\projects\anyang-name` · ลบด้วย `git worktree remove ../anyang-name` หลัง merge
- test กฎของ body รวมอยู่ใน `test_profile_api.py` (ไม่แยกไฟล์ตามร่างแรกของ spec) เพราะ import fixture ข้ามไฟล์ติด ruff F811 · ตาราง §8 ของ spec แก้แล้ว
- รัน pytest จาก `apps/api` ด้วย `env -u AI_PROVIDER -u APP_ENV -u AUTH_REQUIRED uv run pytest …` · integration ต้องมี Supabase ใน `.env` (~70 s)
