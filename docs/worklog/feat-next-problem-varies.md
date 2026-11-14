# ข้อต่อไปไม่ซ้ำข้อที่เพิ่งจบ (`generate_problem/v2`)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/next-problem-varies` |
| Checklist item | ⭐ demo: ข้อต่อไปไม่ซ้ำข้อที่เพิ่งจบ · `generate_problem/v2` รับโจทย์ล่าสุดของหัวข้อ + code ตัดโจทย์ข้อความซ้ำ (นับเป็นรอบที่ไม่ผ่าน) · วัดใหม่บน Vertex (AM-11 · **Jam** · เจอตอนรันจริงของ PR #132 · `room-answers-db.md` §10 ข้อ 4) |
| Status | in progress · 2026-11-14 |

## Plan

รันจริงของ #132 ได้ข้อต่อไปที่ข้อความเหมือนข้อที่เพิ่งจบทุกครั้ง เพราะ `generate_problem/v1` ไม่รู้ว่าเคยให้โจทย์อะไรไปแล้ว (หัวข้อ, ระดับยาก, เนื้อหาเหมือนเดิม → model ตอบแบบเดิม) · แก้ 2 ชั้น: บอก model ว่าเคยให้อะไรไปแล้ว และ code ไม่รับโจทย์ที่ซ้ำ

- [x] 1. 🤖 (14 พ.ย. · Jam ok) `/spec-feature` → แก้ `specs/features/tutor/room-problems-db.md` §2.3 + AC ใหม่: input `previous_problems` (ข้อความของโจทย์ล่าสุดของหัวข้อใน prep นี้ ไม่เกิน N ข้อ · N ใน `config/learning.yaml` ไฟล์กลาง) · code ตัดโจทย์ที่ `text` หรือ `expression` (ตัดช่องว่างแล้ว) ซ้ำกับข้อเหล่านั้น → นับเป็นรอบที่ไม่ผ่าน · repository เพิ่ม `recent_problems(prep_id, topic_id, limit)` · 🙋 Jam review spec
- [x] 2. 🤖 (14 พ.ย. · Jam ok) `/spec-to-tests` (fake provider + fake repository + SymPy จริง) · 🙋 Jam review test
- [ ] 3. 🤖 prompt `generate_problem/v2` (ไม่ทับ v1) + `config/ai.yaml` `prompt: v2` + `config/learning.yaml` ค่า N (ไฟล์กลาง · ถาม Jam ก่อน) + `test_prompt_data_blocks.py` · implement จน green
- [ ] 4. 🤖 วัดใหม่บน Vertex: หัวข้อหลักของ demo (MTH10101) สร้างโจทย์ต่อกัน 3 ข้อต่อหัวข้อ · นับ % ที่ SymPy ยืนยันภายใน 3 รอบ (v1 = 71%) และจำนวนโจทย์ซ้ำ (v1 ซ้ำแทบทุกครั้ง) · 🙋 Jam รับผล
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- ข้อต่อไปของหัวข้อเดิมไม่มี `text` หรือ `expression` ซ้ำกับโจทย์ล่าสุดของหัวข้อใน prep
- `generate_problem/v2` ได้รายการโจทย์ก่อนหน้าใน data block · v1 ยังอยู่
- วัดบน Vertex แล้วสัดส่วนที่ SymPy ยืนยันไม่ต่ำกว่า v1 มาก (Jam รับผล)
- test เดิมไม่ต้องแก้

## Decisions

- 2026-11-14 · prompt v2 + ตัดซ้ำใน code (Jam เลือกทาง 2a ใน PR #132)

## Next step

ขั้น 3: implement (Jam ok ไฟล์กลาง learning.yaml + ai.yaml)

## Waiting on

ไม่มี

## Notes for next time

- รันจริงของ #132 อยู่ใน `room-answers-db.md` §8
