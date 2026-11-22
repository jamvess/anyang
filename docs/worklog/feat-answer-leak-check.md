# answer-leak check แบบ deterministic (AM-13)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/answer-leak-check` |
| Checklist item | answer-leak check แบบ deterministic ใน gateway (AM-13) |
| Status | in progress · 2026-11-22 |

## Plan

มีแล้ว: ai-orchestration §2.9 "Answer-leak check" (tutor reply มี `reference_answer` ของโจทย์ค้าง → generate ใหม่ · ตรวจด้วย string match และ SymPy) · `config/ai.yaml` `guards.answer_leak_check: true` (ยังไม่มี code อ่าน) · prompt ไม่ได้รับเฉลยอยู่แล้ว (`tutor_reply/v2` รับแค่ข้อความโจทย์ · demo-room §2 C · hint ladder ส่ง `none` แทนเฉลย · §2 K ข้อ 7) · `app/domain/room.py` มีตัว normalize LaTeX (`_plain`, `_math_of`) · `app/math/sympy_service.py` มี `SympyWorkerPool.run(fn, ...)` ที่รัน function ใน subprocess พร้อม timeout

ไม่อยู่ในงานนี้: ต่อเข้า gateway / ห้องติว (หลัง 23 พ.ย. · ห้ามแตะห้องที่ใช้อัดวิดีโอ) · วิธีรับมือกับ stream ที่ส่ง token ไปแล้ว (คำถามใน spec §10 สำหรับ PR ต่อ)

- [ ] 1. 🤖 `/spec-feature` → `specs/features/ai/answer-leak-check.md` (AM-13): ตัวตรวจ `leaks(reply, reference_answer, answer_format) -> bool` · ขั้นที่ 1 string match ใน `app/domain/` (pure) · ขั้นที่ 2 SymPy รันใน worker pool (`app/math/`) · คำถามให้ Jam ตัดสินใน §10 (อะไรนับว่า "หลุด" ต่อ `answer_format` · เลี่ยง false positive จากตัวโจทย์เอง · purpose ไหนต้องตรวจ · stream แล้วจะ generate ใหม่ยังไง · พบแล้วทำอะไร) → 🙋 Jam review spec
- [ ] 2. 🤖 (ถ้า §10 ต้องเพิ่มค่าใน `config/ai.yaml` · ไฟล์กลาง) → 🙋 Jam ok + บอกกลุ่มก่อน merge
- [ ] 3. 🤖 `/spec-to-tests` (unit · table-driven จากตัวอย่างโจทย์จริงของ demo · ไม่มี AI จริง) → 🙋 Jam review test
- [ ] 4. 🤖 `/implement-feature` จน green · ruff · pytest ทั้งชุด

## Definition of done

- code ตัดสินได้แบบ deterministic ว่าข้อความของ tutor มีเฉลยของโจทย์ที่ยังรอคำตอบหรือไม่ (AM-13) ทั้งแบบตัวอักษรตรงกันและแบบ SymPy เท่ากัน โดยไม่นับตัวโจทย์เอง
- test จาก AC ผ่าน · test เดิมผ่าน · ruff, pytest, CI เขียว

## Decisions

- 2026-11-22 · Jam เลือกข้อ 1 ของ `/work-start Jam` · ทำแบบ planner / stage machine: domain + test ก่อน ต่อเข้า gateway หลัง 23 พ.ย.

## Next step

ข้อ 1: ร่าง `specs/features/ai/answer-leak-check.md` จาก ai-orchestration §2.9 · demo-room §2 C, K · `room.py` (`_plain`) · `sympy_service.py`

## Waiting on

ไม่มี

## Notes for next time

- อย่าแตะห้องติวที่ใช้อัดวิดีโอก่อน 23 พ.ย.
- อ่านผล test ก่อนแล้วค่อย commit (อย่าต่อ `&&` หลัง grep ผล)
