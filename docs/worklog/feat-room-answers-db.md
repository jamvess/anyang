# ห้องติวตอนมี token: ตอบ → ตรวจ → ใบ้ → ข้อต่อไป (demo ขั้น 7)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/room-answers-db` |
| Checklist item | ⭐ demo ขั้น 7: `typed_answer` + ตรวจ + รูป/canvas ในทางที่มี token (TM-06 ส่วนพิมพ์และรูป, AM-01–07) · hint ladder เฉพาะ `APP_ENV=local` ตาม `demo-room.md` §2 K (AM-07 ยังเป็นข้อเดิมจนกว่าทีมตัดสิน) |
| Status | in progress · 2026-11-13 |

## Plan

ห้องที่มี token ตอนนี้ (#131) ให้โจทย์ได้ แต่ตอบแล้วได้แค่แชท · ทางตรวจคำตอบทั้งหมด (พิมพ์, รูป, canvas, ตรวจ, คำอธิบาย, hint ladder, ข้อต่อไป) มีอยู่แล้วในเดโม่ในเครื่อง และเขียนผ่าน interface `RoomState` · แผนคือทำ `RoomState` ที่อ่าน/เขียน DB (`DbRoomState`) แล้วให้ทางที่มี token ใช้ flow เดิมทั้งหมด แทนการเขียนใหม่

- [x] 1. 🤖 (13 พ.ย. · Jam ok) `/spec-feature` → `specs/features/tutor/room-answers-db.md`: `DbRoomState` (โจทย์ค้างจาก `problems` · ladder จาก `attempts` · ข้อต่อไปด้วย generator ของ #131 · บันทึกบทสนทนาลง `messages`: คำพูดเป็น `user`/`tutor`, บรรทัดภายในเช่น `(ผลตรวจ)…` เป็น `system` ที่หน้าเว็บไม่แสดง) · `typed_answer` ในทางที่มี token (ทุก env เมื่อมีโจทย์ค้าง) · รูป/canvas ในทางที่มี token (เฉพาะในเครื่องจนกว่ามี Storage) · บันทึก `attempts` ทุกคำตอบที่ตรวจ (PM-01 · ย้ายจากขั้น 8 เพราะ flow ต้องรู้ว่าโจทย์จบหรือยัง) · migration `0006`: `problems.ended_at` (โจทย์จบ) + `problems.working_steps` (ขั้นที่ส่งแล้วของ `continue`) · BKT ลง `topic_progress` ยังเป็นขั้น 8 · 🙋 Jam review spec
- [x] 2. 🤖 (13 พ.ย. · Jam ok) `/spec-to-tests` (fake repository + fake provider + SymPy จริง · integration บน Supabase) · 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · ไฟล์กลาง (`api.md`) ถามก่อน
- [ ] 4. 🤖 รันจริงบน Vertex ผ่าน API กับ DB ในหน่วยความจำ: เปิดห้อง → ตอบผิด 2 ครั้ง (ladder) → ยอมแพ้ → ข้อต่อไป → ตอบถูก
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- มี token + โจทย์ค้าง: พิมพ์คำตอบ หรือส่งรูป/canvas (ในเครื่อง) แล้วได้ `verdict` + คำอธิบาย + โจทย์เดิม (ใบ้) หรือข้อต่อไป ตาม `demo-room.md` §2 G–K
- ทุกคำตอบที่ตรวจมีแถวใน `attempts` · โจทย์ที่จบมี `ended_at` · เปิดห้องใหม่ไม่ได้โจทย์ที่จบแล้วซ้ำ
- ทางที่ไม่มี token (เดโม่เดิม) ทำงานเหมือนเดิม · test เดิมไม่ต้องแก้

## Decisions

- 2026-11-13 · ใช้ `RoomState` เดิมผ่าน `DbRoomState` แทนการเขียน flow ใหม่ (Jam เลือกงานนี้)

## Next step

ขั้น 1: เขียน spec

## Waiting on

Junior: ดู migration `0006` แล้ว `db push` หลัง merge (demo ในเครื่องใช้ `db reset`)

## Notes for next time

- ไม่มี
