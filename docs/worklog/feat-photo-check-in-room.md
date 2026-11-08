# ต่อ P1 + P2 เข้าห้องแชท: ส่งรูปแล้วได้ verdict

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/photo-check-in-room` |
| Checklist item | (ถ้ามีเวลา) ต่อ P1 + P2 เข้าหน้าแชท: ส่งรูปแล้วได้ verdict |
| Status | in progress · 2026-11-08 |

เส้นทาง: `POST /sessions/{id}/messages` มี `image_path` → `extract_answer` (P1 · tier vision) → SSE `ocr_preview` · `POST /sessions/{id}/ocr/confirm` → `check_answer` service (P2 · SymPy + LLM + merge rules) → SSE `verdict` → `token` → `done` · ตอนนี้ทั้งสองจุดเป็น stub (`room-photo-send.md` §9)

## Plan

- [x] 1. 🤖 `/spec-feature` → `specs/features/check/photo-check-in-room.md` (AM-xx, TM-06 · หา ID ที่ถูกตอนเขียน) · อ่าน P1.md, P2.md, ai-orchestration §2.4, api.md v1.7 (`ocr_preview`, `verdict`, `/ocr/confirm`), `room-photo-send.md`, `ocr-confirm-card.md`, `verdict-mark.md` · ทุกเรื่องโครงสร้าง backend (อ่านรูปจาก Storage, เก็บ OCR ที่รอยืนยันและโจทย์ปัจจุบันไว้ที่ไหน) เขียนเป็นข้อเสนอใน §10 ให้ Junior ตัดสินย้อนหลัง
- [x] 2. 🙋 Jam review spec · ตัดสินเรื่อง AI (prompt, model, threshold) · ข้อเสนอ backend เลือกแบบชั่วคราวได้ แล้วรอ Junior
- [x] 3. 🤖 `/spec-to-tests` (fake provider · ไม่ใช้ network)
- [x] 4. 🙋 Jam review test
- [x] 5. 🤖 `/implement-feature`
- [ ] 6. 🙋 smoke ในเครื่องกับ Vertex จริง (ADC ของ Jam): ส่งรูปจาก `evals/` แล้วเห็น `ocr_preview` → ยืนยัน → `verdict` · ขั้นตอนแบบคลิกต่อคลิกจะเขียนให้ตอนถึงขั้นนี้
- [ ] 7. 🤖 `/work-done` + ข้อความกลุ่มถึง Junior

## Definition of done

- ส่งรูปคำตอบในห้องแล้วได้ `ocr_preview` จาก `extract_answer` จริง (ไม่ใช่ stub) และหลังยืนยันได้ `verdict` จาก checker ของ P2 · test ผ่านด้วย fake provider ใน CI
- ส่วนที่ยังรอ Junior เขียนไว้ใน spec §10 และ Waiting on

## Decisions

- 2026-11-08 · spec approved (Jam): §10 ข้อ 1 (ข) purpose ใหม่ `explain_check` + ส่งเฉลย · ข้อ 2 (ข) classifier ล้ม → ลองยืนยันใหม่ ไม่แก้ contract · ข้อ 3–8 ใช้ข้อเสนอ รอ Junior ดูย้อนหลัง · ต้องแก้ `config/ai.yaml` (ไฟล์กลาง) ตอน implement → บอกกลุ่มก่อน merge
- 2026-11-08 · solo time: Jam ทำข้อของ Junior · โครงสร้าง backend ใน spec เป็นข้อเสนอ ให้ Junior ตัดสินย้อนหลัง (`roles.md` "ตัดสินใจเรื่อง")

## Next step

ขั้น 6 (🙋 Jam): smoke กับ Vertex จริงในเครื่อง ตามขั้นตอนที่ Claude เขียนให้ (สคริปต์อยู่ใน scratchpad ไม่ commit) · ก่อน `/work-done` ต้องแก้ `room-photo-send.md` §9 และ ai-orchestration §2.10 ตาม spec §11

## Waiting on

- Junior: `/uploads` จริงที่ต่อ Supabase Storage (bucket + policy · api.md v1.7 รอตัดสินข้อ 2) และวิธีที่ API อ่านรูปกลับมา
- Junior: บันทึก `messages` / `attempts` และที่เก็บ OCR ที่รอยืนยัน (ยังไม่มี session จริงใน DB)
- Junior: env ของ `api-staging` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AUTH_REQUIRED`, runtime SA) ถ้าจะโชว์บน staging

## Notes for next time

- เริ่ม 16:47 (8 พ.ย.)
- `/spec-to-tests` 16:55–17:09 · test ที่ไม่มี AC ตรง: `test_AM02_problem_stays_pending_after_check` (§10 ข้อ 4) · spec ไม่มี AC ของ "ส่งรูปตอนไม่มีโจทย์ค้าง" (§2.1 ข้อ 2) จึงยังไม่มี test
- `/implement-feature` 17:10–17:18 · red → green 2 รอบ: (1) 28 test ใหม่เขียวในรอบแรก (2) guard เดิม 2 ตัวแดง: `photo_check.py` import `Image` จาก `app.ai.providers` (AI-01) → เปลี่ยนเป็น import จาก gateway · prompt ใหม่ต้องลงทะเบียนใน `OUTSIDE_BY_PROMPT` ของ `test_prompt_data_blocks.py` (เพิ่ม 1 แถว · test เดิมออกแบบให้เพิ่มแบบนี้)
- โค้ดที่ไม่มี test: `_no_pending_problem` (spec ไม่มี AC · §10 ข้อ 4) และการกัน `..` กับ `/` ในชื่อไฟล์ของ `_own_upload`
- spec draft: SymPy ของจริงตรวจตัวอย่าง AC-11 (`x^2 - 49`, `= (x-7)(x+7)` → ถูกทุกบรรทัด) และ AC-12 (`= (x-7)(x-7)` → บรรทัด 2 ผิด) ได้ตามที่เขียน
