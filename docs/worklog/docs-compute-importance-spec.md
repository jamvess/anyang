# Spec `compute_importance` พร้อมใช้ใน P8-lite

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/compute-importance-spec` |
| Checklist item | P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`) |
| Status | in progress · 2026-10-31 |

## Plan

- [ ] 1. 🤖 เทียบร่าง `specs/features/scope/compute-importance.md` (เขียนตั้งแต่ตั้ง repo) กับของที่เปลี่ยนไปแล้ว: ai-orchestration §2.3.5, learning-model §2 + v1.2 (ระดับเป้าตามดาว), `config/learning.yaml` → `stars` (ป้ายที่มาและผล P3), `specs/poc/reports/P3.md`, `poc/P3/stars.py` (สูตรที่ P3 ใช้จริง), `supabase/migrations/0001_init.sql` (`topics`, `materials`), `specs/features/scope/scope-review.md` (หน้าที่แสดงดาว) · สรุปเป็นรายการจุดที่ต้องแก้
- [ ] 2. 🤖 แก้ spec ตามรายการ (ยังเป็น draft): AC ที่ test ได้โดยไม่ใช้ DB, ขอบเขต threshold จาก config (−ε, =, +ε), กรณีขอบของ tercile (หารไม่ลงตัว, จำนวนหน้าเท่ากัน), ข้อเสนอสำหรับคำถามเปิด
- [ ] 3. 🙋 Jam อ่าน spec §2, §4, §10 แล้วตอบคำถามเปิดในแชท
- [ ] 4. 🙋 Jam บอกแชทกลุ่มว่า spec พร้อมสำหรับ P8-lite ใน S4 (ข้อความจะร่างให้) · Junior เป็น reviewer ของ spec · ไม่ต้องรอ approve (`CLAUDE.md` "How we work" 5)
- [ ] 5. 🤖 เตรียมใบเก็บ metrics ของ P8-lite (`poc/P8-lite/metrics.md`): วิธีนับ % โค้ดที่ agent เขียน, รอบ red → green, บั๊กที่ test จับได้ก่อน merge, เวลาที่คนใช้ review · ให้ S4 เก็บแบบเดียวกันทุกคน
- [ ] 6. 🤖 ตั้ง spec เป็น approved · จดการตัดสินใจ · sub-bullet ใน checklist (ยังไม่ติ๊ก เพราะ P8-lite จบเมื่อ implement + merge ใน S4)

## Definition of done

- `compute-importance.md` status approved · ทุก AC test ได้โดยไม่มี DB และ network · ทุก threshold อ่านจาก `config/learning.yaml` → `stars` พร้อม AC ขอบ (−ε, =, +ε)
- ตรงกับ ai-orchestration §2.3.5, learning-model §2 และสูตรที่ P3 พิสูจน์แล้ว (★★★ 10/12) · ถ้าต่างกันระบุใน §11
- ไม่มีคำถามเปิดที่ยังไม่ตัดสิน (หรือระบุชัดว่าเลื่อนไปเมื่อไหร่)
- มีใบเก็บ metrics ของ P8-lite พร้อมใช้ใน S4
- `/spec-to-tests` ใน S4 เริ่มได้ทันทีโดยไม่ต้องถามอะไรเพิ่ม

## Decisions

- 2026-10-31 · งานนี้ทำแค่ส่วน spec ของ P8-lite ก่อนกำหนด · `/spec-to-tests` → ทีม review test → `/implement-feature` ทำร่วมกันใน S4 ตาม `specs/poc/README.md` P8-lite

## Next step

ขั้น 1 (🤖): เทียบร่าง spec กับไฟล์ที่ระบุในแผน แล้วสรุปรายการจุดที่ต้องแก้

## Waiting on

ไม่มี

## Notes for next time

- ร่าง spec มีตั้งแต่ commit แรก (`1346e9b`) · ไม่เคยแก้หลัง P3
