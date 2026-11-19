# stage machine: probe → teach → Verify → practice · ผ่านตาม skill

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/stage-machine` |
| Checklist item | stage machine: probe → teach → Verify ด้วยโจทย์แบบเดียวกัน → practice (TM-03, TM-04, AM-08, AM-09) · ผ่านตาม skill (TM-16, SM-12) |
| Status | in progress · 2026-11-19 |

## Plan

มีแล้ว: ai-orchestration §2.2.4 (ตาราง stage + เงื่อนไข Done + Park + การสอนตาม error type) · §2.2.10 · §2.5.4 (เลือก skill + difficulty) · `config/learning.yaml` `done.*`, `park.*`, `bkt.*` · `app/domain/bkt.py` (`level`, `target_difficulty`, `mastery_eff`) · `app/domain/planner.py` (#166) · DB มีคอลัมน์ครบแล้วใน `0001` (`topic_progress.stage`, `skill_coverage`, `fail_streak` · `problems.purpose`, `skill_id` · `tutor_sessions.stage`)

ไม่อยู่ในงานนี้: ต่อเข้าห้องติว (PR ถัดไปหลัง 23 พ.ย. · ห้ามแตะห้องที่ใช้อัดวิดีโอ) · Park ฝั่งกลับเข้า queue และ push prerequisite (TM-19 · S6) · source ของโจทย์ (ข้อสอบเก่า / สร้างใหม่) · intent "ยังไม่เคยเรียน" (รับเป็น input)

- [x] 1. 🤖 `/spec-feature` → `specs/features/tutor/stage-machine.md` (TM-03, TM-04, AM-08, AM-09, TM-16, SM-12): pure function `next_step(state, event, cfg) -> Step` (stage ถัดไป + directive + skill + difficulty + purpose) · คำถามให้ Jam ตัดสินใน §10 (hint ladder ของ demo กับ Teach ตาม AM-07 · Park อยู่ในงานนี้แค่ไหน · ค่า difficulty ของ Probe/Practice/Verify ต้องเพิ่มใน config ไหม) → 🙋 Jam review spec
- [x] 2. 🤖 (ถ้า §10 ต้องเพิ่มค่าใน `config/learning.yaml` · ไฟล์กลาง) เพิ่มค่า + ป้ายที่มา + `learning-model.md` + settings class → 🙋 Jam ok + บอกกลุ่มก่อน merge
- [ ] 3. 🤖 `/spec-to-tests` (unit · table-driven · ไม่มี magic number) → 🙋 Jam review test
- [ ] 4. 🤖 `/implement-feature` จน green · ruff · pytest ทั้งชุด

## Definition of done

- code ตัดสิน stage ของหัวข้อ: Probe ก่อนสอน (ข้าม Teach เมื่อถูก · TM-03) · Teach ↔ Practice ทีละหัวข้อ (TM-04) · Verify ด้วยโจทย์ skill เดิม (AM-08) · Teach ครั้งที่สองใช้มุมใหม่ (AM-09) · Done ตาม skill + ระดับเป้า + mastery (TM-16, SM-12)
- test จาก AC ผ่าน · test เดิมผ่าน · ruff, pytest, CI เขียว

## Decisions

- 2026-11-19 · Jam เลือกข้อ 1 ของ `/work-start Jam` · ทำแบบ planner: domain + test ก่อน ต่อเข้าห้องหลัง 23 พ.ย.
- 2026-11-19 · spec §10: (ก) ทำตาม AM-07 ที่เขียนไว้ (hint ladder อยู่แค่เดโม่) · เข้า Park เท่านั้น · config `stages:` (probe 2, practice เริ่ม 2, verify ลด 0) · user ใหม่ → introduce + Practice · ครอบคลุมหมดแล้ว → skill ที่ถูกน้อยสุด · Start หัวข้อที่ Park → Probe ใหม่

## Next step

ข้อ 2 รอ Jam ok (config `stages:` v1.8 + learning-model v1.8 + `StagesConfig`) · ok แล้ว commit แล้วทำข้อ 3 `/spec-to-tests` → `tests/unit/test_stage_machine.py`

## Waiting on

- ก่อน merge: Jam โพสต์กลุ่มเรื่องแก้ `config/learning.yaml` (ไฟล์กลาง · ส่วนใหม่ `stages:`)

## Notes for next time

- อย่าแตะห้องติวที่ใช้อัดวิดีโอก่อน 23 พ.ย.
- PR #167 (docs: ส่งไฟล์ทางสำรองฉาก 3) รอ Jam ok เพื่อ merge
