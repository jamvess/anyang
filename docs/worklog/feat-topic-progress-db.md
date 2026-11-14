# BKT ลง `topic_progress` + การ์ดเปลี่ยนตาม mastery (demo ขั้น 8)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/topic-progress-db` |
| Checklist item | ⭐ demo ขั้น 8–9: BKT ลง `attempts` / `topic_progress` + การ์ดจาก DB (PM-01–04) · สรุป session ด้วย `session_summary` (PM-05) |
| Status | in progress · 2026-11-14 |

## Plan

งานนี้ทำเฉพาะขั้น 8 (ขั้น 9 สรุป session แยกงาน) · `attempts` บันทึกแล้วตั้งแต่ #132 และการ์ดตอนเปิดห้องอ่าน `topic_progress` อยู่แล้ว (#131) · ที่ขาดคือ **ไม่มีใครเขียน `topic_progress`** · `DbRoomState.record_check` (จุดที่ code ตัดสินว่าโจทย์จบ) ยังไม่ทำ BKT · เดโม่ในเครื่องทำ BKT ใน memory ได้แล้ว (`demo-room.md` §2 D · `domain/bkt.py`) · แผนคือย้าย BKT เดียวกันลง DB

- [x] 1. 🤖 (14 พ.ย. · Jam ok) `/spec-feature` → `specs/features/planner/topic-progress-db.md`: โจทย์จบ (ถูก, เฉลย, ยอมแพ้) → `record_attempt` ของ `domain/bkt.py` กับแถว `topic_progress` ของผู้ใช้ (ไม่มีแถว = `bkt.p_init`) → upsert `mastery`, `attempts_n`, `correct_n`, `d_max`, `level`, `last_seen_at` · `count_only_independent` ตามเดิม · migration `0007`: `topic_progress.d_max` (room-problems-db §10 ข้อ 2) · เปิดห้องใหม่ → การ์ดเห็นระดับและความพร้อมเปลี่ยน (PM-02, PM-03, PM-06) · 🙋 Jam review spec
- [x] 2. 🤖 (14 พ.ย. · Jam ok) `/spec-to-tests` (fake repository + fake provider + SymPy จริง · integration บน Supabase: RLS ของ `topic_progress`) · 🙋 Jam review test
- [x] 3. 🤖 (14 พ.ย. · green 1699 · Jam ok) `/implement-feature` จน green · migration `0007` + `data-model.md`
- [ ] 4. 🤖 รันจริงบน Vertex: เปิดห้อง → ตอบถูก 2 ข้อ → เปิดห้องใหม่ → การ์ด mastery/ระดับ/ความพร้อมขยับ · 🙋 Jam ดูผล
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- โจทย์ที่จบในทางที่มี token เขียน `topic_progress` ของผู้ใช้ด้วย BKT เดียวกับเดโม่ (นับครั้งเดียวต่อโจทย์ · ถูกหลังใบ้ครั้งสุดท้ายไม่นับตาม `count_only_independent`)
- เปิดห้องใหม่ การ์ดแสดงระดับและความพร้อมจาก `topic_progress` ที่เปลี่ยนแล้ว
- ผู้ใช้อื่นไม่เห็นแถวของกัน (SA-06) · test เดิมไม่ต้องแก้

## Decisions

- 2026-11-14 · BKT เฉพาะเมื่อ request นี้ปิดโจทย์สำเร็จ (ปิดไม่ได้ → โจทย์ยังเปิด อาจตอบซ้ำแล้วนับสองครั้ง)
- 2026-11-14 · เพิ่ม `get_topic_progress` / `save_topic_progress` ให้ fake `FakeProblemRepo` ของ test #131 · หัวข้อใน fake ใหม่ใช้ `signal_r = 1.0` (Jam ok · ไม่แตะ assert)
- 2026-11-14 · ทำเฉพาะขั้น 8 · การ์ดตอนเปิดห้องเท่านั้น (fallback ของ demo ขั้น 8 ในตาราง demo) · `GET /exam-preps/{id}/progress` ยังเป็น stub (PM-04 หน้า home หลัง demo)

## Next step

ขั้น 4: รันจริงบน Vertex (เปิดห้อง → ตอบถูก 2 ข้อ → เปิดใหม่ การ์ดขยับ)

## Waiting on

Junior: `db push` ของ `0005`, `0006`, `0007` ขึ้น `anyang-dev` (demo ใช้ `anyang-dev` ตาม D2 · PR #134)

## Notes for next time

- ไม่มี
