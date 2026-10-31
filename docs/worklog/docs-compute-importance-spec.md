# Spec `compute_importance` พร้อมใช้ใน P8-lite

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/compute-importance-spec` |
| Checklist item | P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`) |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 เทียบร่าง `specs/features/scope/compute-importance.md` (เขียนตั้งแต่ตั้ง repo) กับของที่เปลี่ยนไปแล้ว: ai-orchestration §2.3.5, learning-model §2 + v1.2 (ระดับเป้าตามดาว), `config/learning.yaml` → `stars` (ป้ายที่มาและผล P3), `specs/poc/reports/P3.md`, `poc/P3/stars.py` (สูตรที่ P3 ใช้จริง), `supabase/migrations/0001_init.sql` (`topics`, `materials`), `specs/features/scope/scope-review.md` (หน้าที่แสดงดาว) · สรุปเป็นรายการจุดที่ต้องแก้
- [x] 2. 🤖 แก้ spec ตามรายการ (ยังเป็น draft): AC ที่ test ได้โดยไม่ใช้ DB, ขอบเขต threshold จาก config (−ε, =, +ε), กรณีขอบของ tercile (หารไม่ลงตัว, จำนวนหน้าเท่ากัน), ข้อเสนอสำหรับคำถามเปิด
- [x] 3. 🙋 Jam อ่าน spec §2, §4, §10 แล้วตอบคำถามเปิดในแชท
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

- 2026-10-31 · (ขั้น 3) Jam ok ข้อเสนอทั้ง 5 ข้อใน §10 และผลของ AC-16 (หน้าเท่ากัน → ★★★ ได้มากกว่า 1/3) กับ AC-13 (ผู้ใช้ตั้ง ★★★ เองทำให้ prerequisite ได้ ★★)
- 2026-10-31 · (ขั้น 1) สูตรหลักตรงกันทุกแหล่ง (ai-orchestration §2.3.5, learning-model §2, `learning.yaml`, `poc/P3/stars.py`) และ schema มีคอลัมน์ครบ · เจอ 12 จุด: excluded มาจาก `topics.status`, จำนวนหน้ามาจาก `topic_chunks` → `chunks`, ข้อความเหตุผล 3 แบบ, AC ขอบเดิมใช้ r = 0.599 ที่สร้างจากน้ำหนักจริงไม่ได้, กรณีขอบที่ P3 ทำไว้แต่ spec ไม่ได้เขียน (excluded ยังคำนวณ r และไม่นับเป็น ★★★, r > 0 ชนะเหตุผล prerequisite, หลาย parent ใช้ตัวแรก, น้ำหนักรวม 0), และ 4 ข้อให้ Jam ตัดสิน · Jam ok รายการ
- 2026-10-31 · (ขั้น 2) เขียน spec ใหม่: §2 แบ่ง 3 ขั้น (signal_r → ดาวเมื่อมีข้อสอบ → ดาวเมื่อไม่มีข้อสอบ) · input เพิ่ม `current_importance`, `current_reason` (เก็บค่าที่ผู้ใช้แก้) · AC จาก 13 เป็น 25 ข้อ (AC-1–19 + boundary, config, zero-weight ×2, order, pure) · AC ขอบใช้ r = 0.5 แล้วเลื่อน threshold ±0.001 ใน config fixture · test plan 18 ชื่อใน `tests/unit/test_stars.py` · §10 เป็นข้อเสนอ 5 ข้อ
- 2026-10-31 · งานนี้ทำแค่ส่วน spec ของ P8-lite ก่อนกำหนด · `/spec-to-tests` → ทีม review test → `/implement-feature` ทำร่วมกันใน S4 ตาม `specs/poc/README.md` P8-lite

## Next step

ขั้น 4 (🙋 Jam): ส่งข้อความในแชทกลุ่มตามที่ร่างไว้ในแชท แล้วบอกว่าส่งแล้ว

## Waiting on

ไม่มี

## Notes for next time

- ร่าง spec มีตั้งแต่ commit แรก (`1346e9b`) · ไม่เคยแก้หลัง P3
