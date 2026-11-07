# ตอบ "รอตัดสิน" ส่วนของ Jam: ข้อความ persona ใน prompt, ประวัติแชทของ A8, ขนาดไฟล์สูงสุด

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/jam-open-decisions` |
| Checklist item | ไม่มีข้อตรง · ปิดข้อเปิดของ api.md v1.10 ข้อ 2, v1.11 ข้อ 4 (ส่วน prompt) และข้อจำกัดที่บันทึกใน PR #107 |
| Status | in progress · 2026-11-07 |

## Plan

- [x] 1. 🤖 วัดข้อมูลจริงและร่างทางเลือกของ 3 เรื่อง ให้ Jam อ่าน (ยังไม่แก้ไฟล์ร่วม)
- [x] 2. 🙋 Jam ตัดสินทั้ง 3 เรื่อง · บอกแชทกลุ่มว่าจะแก้ `api.md` และ `config/ai.yaml` (ไฟล์ร่วม)
- [x] 3. 🤖 เขียนผลลง spec: `ai-orchestration.md` §2.7, §2.3, `prompts/README.md`, `api.md` v1.13
- [ ] 4. 🤖 test ของเพดานขนาดไฟล์ · แดงก่อน
- [ ] 5. 🙋 Jam review test
- [ ] 6. 🤖 `guards.max_material_mb` + เช็คใน `POST /exam-preps/{id}/materials` · test เขียว + ruff
- [ ] 7. 🤖 `api-schema.ts` ถ้าเปลี่ยน

## Definition of done

- 3 เรื่องมีคำตอบเขียนใน spec พร้อมเหตุผล และ "รอตัดสิน" ของ `api.md` ชี้ไปที่คำตอบ
- `POST /exam-preps/{id}/materials` ปฏิเสธไฟล์เกินเพดานด้วยค่าจาก config · test + ruff + CI เขียว
- ไม่แก้ prompt version เดิม · ถ้าไม่มี prompt ที่ต้องแก้ ไม่ต้องรัน eval

## Decisions

- 2026-11-07 · `tutor_reply/v1` ไม่มี placeholder ของ persona เลย (P4-lite ไม่ทำ context layer 2–9) และ `scope_edit` ยังไม่มี prompt · เรื่อง persona และประวัติแชทจึงเป็นกฎใน spec สำหรับ prompt ที่จะเขียน ไม่ใช่การแก้ prompt วันนี้
- 2026-11-07 · Jam ตัดสิน: ค่า persona สี่ช่องอยู่ใน `<persona_data>` + ต้องมี eval case เมื่อสร้าง layer 2 · A8 ได้ประวัติจาก server ไม่รับจาก client · `guards.max_material_mb: 50` ป้าย `[B]` ตามเพดาน Supabase Free (ไฟล์จริงใหญ่สุด 6.2 MB จากวิชาเดียว) · เพดานจำนวนหน้ายังเปิด

## Next step

ขั้น 4: เขียน test เพดานขนาดไฟล์ของ `POST /exam-preps/{id}/materials` ให้แดงก่อน

## Waiting on

- Junior: ที่เก็บประวัติแชท S13 (api.md v1.11 ข้อ 4)

## Notes for next time

- `prompts/README.md` กฎ 5 บอกว่าใช้เฉพาะ params ที่ผ่าน enum แต่ `name`, `self_pronoun`, `call_user`, `nickname` ไม่ใช่ enum · ต้องแก้ให้ตรง
- `ai-orchestration.md` §2.7 ข้อ 5 บอกว่า text ดิบไม่เข้า prompt · ต้องระบุข้อยกเว้นสามช่องนี้และชื่อเล่น
