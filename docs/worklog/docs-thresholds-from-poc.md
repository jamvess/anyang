# ปรับ threshold ใน AI flow specs และ learning-model ตามผล P1 P2 P3

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/thresholds-from-poc` |
| Checklist item | อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2) |
| Status | paused · 2026-10-31 |

## Plan

- [ ] 1. 🤖 ทำรายการทุกค่าที่ผูกกับ PoC: ทุก key ใน `config/learning.yaml` ที่ป้ายพูดถึง P1/P2/P3 หรือรอ PoC · ตาราง calibration ใน `learning-model.md` §9 · ตัวเลขใน `ai-orchestration.md` (flow 2.3 ingest, 2.4 checker, 2.10 routing, latency/ต้นทุน) · เทียบกับตัวเลขใน `specs/poc/reports/P1.md`, `P2.md`, `P3.md` · ทำเป็นตาราง: ค่า · ตอนนี้ · PoC วัดได้อะไร · ข้อเสนอ (คง / เปลี่ยน / ยังรอ + ป้ายที่มา)
- [ ] 2. 🙋 Jam ตัดสินทีละแถวในตาราง (ตอบเป็นเลขแถว หรือ "ok ทุกแถว")
- [ ] 3. 🤖 แก้ตามที่ตัดสิน: `learning-model.md` (ตารางค่าและ §9), `ai-orchestration.md` (เฉพาะ flow ที่ PoC วัด) · ไม่เปลี่ยนหลักการ
- [ ] 4. 🤖 แก้ `config/learning.yaml` (ค่าหรือป้ายที่มา) ถ้ามีแถวที่ต้องเปลี่ยน · รัน `uv run pytest` เพราะ test อ่าน config · ไฟล์นี้ Jam + Junior เป็นเจ้าของ (CODEOWNERS)
- [ ] 5. 🙋 Jam บอกแชทกลุ่มก่อน merge (ถ้าแก้ `config/learning.yaml`) · ข้อความจะร่างให้

## Definition of done

- ไม่มีค่าใน `config/learning.yaml`, `learning-model.md`, `ai-orchestration.md` ที่ยังเขียนว่ารอผล P1, P2 หรือ P3 · ค่าที่ PoC วัดไม่ได้ระบุว่าวัดเมื่อไหร่แทน
- ทุกค่าที่เปลี่ยนมีป้าย [A]/[B]/[calc]/[C] และอ้าง report ของ PoC
- `uv run pytest` และ `uv run ruff check .` ผ่าน (ถ้าแตะ config)
- ตรงกับ checklist: "อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2)"

## Decisions

## Next step

ขั้น 1 (🤖): ทำรายการค่าที่ผูกกับ PoC แล้วเสนอเป็นตาราง

## Waiting on

ไม่มี

## Notes for next time

- 28 ต.ค. PR #73 ทำ learning-model v1.2 จากการทบทวน design (ไม่ได้มาจากผล PoC) · งานนี้คือส่วนที่เหลือ: ปรับตามผล PoC
- ค่าที่ทำไปแล้วในงานอื่น: `ocr.always_confirm` (P1 · PR #45) · `stars.*` ป้าย P3 (PR #60) · `stars.no_past_exam_method` (PR #89) · `grounding_chunks` ป้าย P3b
