# Persona จาก free text: prompt `persona_extract` + `persona_preview` และ `POST /personas/extract` จริง

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/persona-extract` |
| Checklist item | prompt ของ persona (`persona_extract`, `persona_preview`) และ scope edit ผ่านแชท (UM-05, SM-06) |
| Status | in progress · 2026-11-22 |

## Plan

- [x] 1. 🤖 `/spec-feature` UM-05, UM-07 → `specs/features/ai/persona-extract.md` (prompt 2 ตัว · schema ของ output · ค่าที่คำบรรยายไม่ได้พูดถึง · กฎ whitelist · fallback E5 · eval) พร้อมคำถามใน §10
- [x] 2. 🙋 Jam ตัดสิน §10 และ approve spec
- [ ] 3. 🤖 `/spec-to-tests`: service ด้วย fake provider · router (token → จริง · ไม่มี token → stub เดิม) · test contract เดิมต้องผ่าน · red
- [ ] 4. 🙋 Jam review test
- [ ] 5. 🤖 `/implement-feature`: `prompts/persona_extract/v1.md`, `prompts/persona_preview/v1.md` · model ของ output · `app/services/persona.py` · `app/routers/persona.py` (ไฟล์ใน `apps/api/` · CODEOWNERS = Junior · stub endpoint เดิม Jam เขียนเอง PR #107)
- [ ] 6. 🤖 golden set `evals/persona/` (คำบรรยายปกติ · คำขอที่ทำไม่ได้ · injection) + รันบน Vertex จริง
- [ ] 7. 🙋 Jam อ่านประโยคตัวอย่างและผล eval แล้วตัดสินว่าผ่าน
- [ ] 8. 🤖 docs: `ai-orchestration.md` §2.7 / §2.10 (fallback ของ `persona_extract` ที่ use-cases.md บอกว่ายังไม่มี) · checklist sub-bullet

## Definition of done

- `POST /personas/extract` ที่มี token เรียก `persona_extract` แล้ว `persona_preview` ผ่าน gateway และคืน `{params, refused, sample}` ตาม api.md v1.12
- params ผ่าน model เดิม (`TutorParams` / `BuddyParams`) ทุกครั้ง · ค่าที่ AI ให้ผิดไม่หลุดออกไป
- คำบรรยายอยู่ใน data block และไม่เข้า `persona_preview` · eval injection ผ่าน
- AI ล่ม → `503 persona_unavailable` (UC-01 E5)
- ไม่มี token + `AUTH_REQUIRED=false` ยังได้ stub เดิม · `test_persona_api_contract.py` ผ่าน
- ผล eval บน Vertex แนบใน PR · CI เขียว
- ส่วน scope edit ผ่านแชท (SM-06) ของ checklist ข้อเดียวกันเป็น PR ถัดไป (ข้อยังไม่ติ๊ก)

## Decisions

- 2026-11-22 · แยก persona ออกจาก scope edit ผ่านแชท · ข้อ checklist ใหญ่ (L) และ persona ไม่แตะห้องติวที่ใช้อัดวิดีโอ
- 2026-11-22 · spec §10 ข้อ 1–5 ตามข้อเสนอ (Jam) · ข้อ 1 ก ต้องแก้ api.md (shared) ใน PR นี้ และบอกกลุ่มก่อน merge

## Next step

ขั้น 3: `/spec-to-tests` ของ `specs/features/ai/persona-extract.md`

## Waiting on

ไม่มี

## Notes for next time

- ตาราง `tutor_profiles` / `buddy_profiles` และ `PUT /me/*-profile` จริงเป็นของ Junior (S5) · PR นี้ไม่เขียน DB
