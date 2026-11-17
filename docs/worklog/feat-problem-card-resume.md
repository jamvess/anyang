# การ์ดโจทย์ไม่หายเมื่อกลับเข้าห้อง (goal อาจารย์ข้อ 4)

| | |
|---|---|
| Owner | May |
| Branch | `feat/problem-card-resume` |
| Checklist item | (ยังไม่มีใน checklist · goal อาจารย์ 17 พ.ย. ข้อ 4 "บันทึกการเรียนลงฐานข้อมูล ปิดแล้วกลับมาเรียนต่อได้" · `room-problems-db.md` §10 ข้อ 3 (May)) · จะเพิ่มข้อ ⭐ ใน May S4 ตอน `/work-done` |
| Status | in progress · 2026-11-17 |

## Plan

ปัญหา: `GET /sessions/{id}` คืนแค่ข้อความ · การ์ดโจทย์ (และการ์ดความคืบหน้า) มาทาง SSE เท่านั้น ไม่ได้บันทึก · รีเฟรชหรือกลับเข้าห้อง (`sessions/active`) แล้วการ์ดโจทย์หาย → ไม่มี canvas และไม่เห็นว่าค้างโจทย์ข้อไหน (API ยังจำโจทย์ค้างได้ · พิมพ์ตอบยังตรวจได้)

- [ ] 1. 🙋 May ส่งข้อความถาม Jam (+ Junior) เลือกทาง: (ก) `GET /sessions/{id}` ส่ง `open_problem` (โจทย์ค้างจากตาราง `problems`) แล้วหน้าเว็บแสดงการ์ดท้ายแชท · (ข) บันทึกการ์ดโจทย์เป็น `messages` `role = card` ทุกที่ที่ส่ง event `problem` · และใครทำส่วน API
- [ ] 2. 🤖 `/spec-feature` ตามทางที่เลือก → 🙋 May ok spec (api.md เป็นไฟล์กลาง · บอกกลุ่มก่อน merge)
- [ ] 3. 🤖 `/spec-to-tests` (API + หน้าเว็บ) → 🙋 May review test
- [ ] 4. 🤖 `/implement-feature` จน test ผ่าน (api: ruff + pytest · web: lint + typecheck + test) · `pnpm gen:api`
- [ ] 5. 🙋 ลองเส้นจริง: เปิดห้อง → ได้การ์ดโจทย์ → รีเฟรช → การ์ดโจทย์ + canvas ยังอยู่ (ต้องมี prep ที่มีหัวข้อ · บัญชี May หรือ Jam ลองให้)
- [ ] 6. 🤖 `/work-done` (ไฟล์กลาง api.md → ข้อความกลุ่มก่อน merge)

## Definition of done

- รีเฟรช / กลับเข้าห้องที่มีโจทย์ค้าง → เห็นการ์ดโจทย์ข้อนั้นและ canvas ตอบได้ (TM-13)
- test ผ่านทั้ง api และ web · api.md อัปเดต · ลองเส้นจริงแล้ว

## Decisions

- 2026-11-17 · May เลือกทำเพราะเป็นส่วน "กลับมาเรียนต่อได้" ของ goal 4 ที่ยังขาด (ปุ่มจบเสร็จแล้ว #143)

## Next step

May ส่งข้อความถาม Jam (ขั้น 1) แล้วบอกคำตอบ

## Waiting on

- Jam (+ Junior): เลือกทาง (ก) / (ข) และใครทำส่วน API

## Notes for next time

- การ์ดความคืบหน้าก็ไม่ได้บันทึกเหมือนกัน แต่ UC-03 E1 บอกว่ากลับเข้าห้องเดิม "ไม่มี progress card ใบใหม่" จึงไม่ใช่ปัญหา
