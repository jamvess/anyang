# planner เต็ม: เลือกหัวข้อ + เหตุผล + mode

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/planner` |
| Checklist item | planner เต็ม: เลือกหัวข้อ + เหตุผล + mode (TM-01, TM-02, TM-18) · ลำดับ prerequisite (SM-02) |
| Status | in progress · 2026-11-19 |

## Plan

มีแล้ว: spec ระบบ `ai-orchestration.md` §2.5 (mode, queue, reason_code) + `learning-model.md` §6 (สูตร need/available) + ค่าใน `config/learning.yaml` `planner:` ครบ (`tight_ratio`, `triage_ratio`, `triage_days_left`, `final_mode_days_left`, `default_minutes_per_problem`, `default_daily_minutes`, `problems_per_skill: bkt_simulation`) · `bkt.target_difficulty(stars, mode)` รู้จัก mode แล้ว · ห้องติวตอนนี้ใช้ `choose_topic` (กฎง่ายตอน demo · `app/domain/room.py`) และล็อก `MODE = "normal"` (`room_problems.py`)

ไม่อยู่ในงานนี้: spaced review (TM-17 · S6) · Park (TM-19 · S6) · stage machine (TM-03, TM-04 · S5 ข้อถัดไป) · ตาราง `planner_decisions` และการเก็บ mode ครั้งก่อน (Junior · S5 "DB ของ planner")

- [x] 1. 🤖 `/spec-feature` → `specs/features/planner/planner.md` (TM-01, TM-02, TM-18, SM-02):
  - mode: need ÷ available ตาม `learning-model.md` §6 · ขอบทุกตัวจาก config · `problems_per_skill` คำนวณจาก BKT params (วิธีคำนวณเป็นคำถามให้ Jam ตัดสิน)
  - queue: หัวข้อค้างจาก session ก่อน → หัวข้อถัดไปตามลำดับที่ยืนยัน (`order_index` ซึ่ง A6 เรียงตาม prerequisite แล้ว · SM-02) โดยข้ามหัวข้อที่ mode ตัด
  - เหตุผล: `reason_code` + ข้อความสั้นจาก template ของ code (TM-02 · ไม่บอกแผนทั้งหมด)
  - mode เปลี่ยน: บอกครั้งเดียวเมื่อรู้ mode ครั้งก่อน (ที่เก็บ mode เป็นของ Junior → ตอนนี้รับเป็น input)
  - pure domain `app/domain/planner.py` แทน `choose_topic` · ต่อเข้าห้องติวใน PR นี้หรือ PR ถัดไป (คำถามให้ Jam ตัดสิน)
  - → 🙋 Jam ตัดสินเรื่องการออกแบบ + review spec
- [x] 2. 🤖 `/spec-to-tests` (unit · table-driven · ขอบของ ratio จาก config · ไม่มี magic number) → 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · ruff · pytest ทั้งชุด
- [ ] 4. 🤖 + 🙋 (ถ้าต่อเข้าห้องติวใน PR นี้) ลองในเบราว์เซอร์: เปิดห้องแล้วคำทักบอกหัวข้อพร้อมเหตุผล

## Definition of done

- ระบบเลือกหัวข้อถัดไปเองจาก importance, mastery และวันที่เหลือ (TM-01) พร้อมเหตุผลสั้น (TM-02) · เลือก mode normal/tight/triage/final ตาม config (TM-18) · เคารพลำดับ prerequisite (SM-02)
- test จาก AC ผ่าน · test เดิมผ่าน (test ของ `choose_topic` ที่ review แล้ว ถ้าต้องเปลี่ยนต้องถาม Jam) · ruff, pytest, CI เขียว

## Decisions

- 2026-11-19 · Jam เลือกข้อ 1 ของ `/work-start Jam` · ทำ spec ล่วงหน้าระหว่างช่วงอัดวิดีโอ (S5 เริ่ม 30 พ.ย.)

## Next step

ข้อ 2 รอ Jam review test (`test_planner_mode.py` + `test_planner_queue.py` · 27 test แดงทั้งหมด) · ok แล้วทำข้อ 3

## Waiting on

- Junior (S5 "DB ของ planner"): ตาราง `planner_decisions` สำหรับเก็บ mode ครั้งก่อน (การบอก user เมื่อ mode เปลี่ยน)

## Notes for next time

- อย่าแตะห้องติวที่ใช้อัดวิดีโอก่อน 23 พ.ย. (merge หลังส่งวิดีโอ ถ้าต่อเข้าห้องติว)
