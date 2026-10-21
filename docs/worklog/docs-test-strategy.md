# Test strategy 1 หน้า

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/test-strategy` |
| Checklist item | Test strategy 1 หน้าใน `specs/system/` |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 สำรวจ test ที่มีจริง: จำนวนและชั้นของ test (api unit / integration, web Vitest, PoC, evals), job ใน CI, กติกาตั้งชื่อ, fake / live provider · สรุปเป็นตาราง "มีแล้ว / ยังไม่มี"
- [ ] 2. 🤖 ร่าง `specs/system/test-strategy.md` 1 หน้า: test แต่ละชั้น (อะไร, เครื่องมือ, รันที่ไหน, ใครเขียน, ใคร review), การวัดคุณภาพ AI ด้วย golden set, กฎ SDD/TDD และ traceability, ข้อมูลทดสอบและความเป็นส่วนตัว, ช่องว่างที่ยังไม่มีพร้อมเจ้าของ · อ้างที่มาจาก spec ที่มีอยู่ ไม่คิดกฎใหม่เอง
- [ ] 3. 🙋 Jam ตัดสินเรื่องที่ spec ยังไม่ได้บอก (Claude ให้ตัวเลือกพร้อมคำแนะนำ)
- [ ] 4. 🤖 แก้ตามที่ตัดสิน + เช็คว่าไม่เกิน 1 หน้า

## Definition of done

- `specs/system/test-strategy.md` มีอยู่ ยาวประมาณ 1 หน้า ทุกกฎอ้างที่มา (CLAUDE.md, `apps/*/CLAUDE.md`, `ai-orchestration.md` §2.11, `specs/poc/README.md`, CI)
- เรื่องที่ยังไม่มีคำตอบเขียนเป็น "ช่องว่าง" พร้อมเจ้าของ ไม่แต่งเป็นกฎ
- PR ส่งให้ Junior และ May review (ไฟล์ใน `specs/system/` ไม่มี owner เฉพาะ จึงเป็นไฟล์ร่วม)

## Decisions

- 2026-10-21 · ทำล่วงหน้า (เป็นงาน S4) ระหว่างรอ flash ของ P3 หลัง 14:00 น.
- 2026-10-21 · `specs/system/test-strategy.md` เป็นไฟล์ใหม่ใน `specs/system/` ซึ่ง CODEOWNERS ให้ทั้ง 3 คน → ถือเป็นไฟล์ร่วม · ไม่แก้ `CLAUDE.md` หรือ `architecture.md` ใน PR นี้ (ถ้าจะลิงก์ ต้องถามก่อน)

## Next step

ข้อ 1: สำรวจ test ที่มีจริงใน repo แล้วสรุปเป็นตาราง

## Waiting on

ไม่มี

## Notes for next time

- 
