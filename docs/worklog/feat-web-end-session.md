# ปุ่มจบการติว + สรุปในแชท (หน้าเว็บ · demo ขั้น 9)

| | |
|---|---|
| Owner | May |
| Branch | `feat/web-end-session` |
| Checklist item | ⭐ demo ขั้น 9 ส่วนหน้าเว็บ (goal อาจารย์ข้อ 4: บันทึกการเรียน ปิดแล้วกลับมาเรียนต่อได้) |
| Status | in progress · 2026-11-17 |

## Plan

Spec: `specs/features/tutor/session-end-ui.md` · API ทำแล้ว (#136 · `session-end-db.md`)

- [x] 1. 🤖 `/spec-feature` → 🙋 May ok spec (17 พ.ย.)
- [x] 2. 🤖 `/spec-to-tests` (`ChatRoomSessionEnd.test.tsx`, `RoomPageSessionEnd.test.tsx`, fixture `session_end.txt`) → 🙋 May review test · May ok test 17 พ.ย. (17 red · AC-12 ผ่านตั้งแต่ต้นเพราะยังไม่มีปุ่ม)
- [x] 3. 🤖 `/implement-feature` จน test ผ่าน + `pnpm lint && pnpm typecheck` · 17 พ.ย. 423/423 ผ่าน · 4 รอบ red → green · lint ไม่มี warning ใหม่ · typecheck ผ่าน
- [ ] 4. 🙋 May ลองในเบราว์เซอร์ (ห้อง → ตอบ → จบ → สรุป → ติวรอบใหม่)
- [ ] 5. 🤖 `/work-done`

## Definition of done

- AC-1 ถึง AC-16 มี test และผ่าน · test เดิมของ `tests/chat/` ผ่านโดยไม่แก้
- May ลองเส้นจริงในเบราว์เซอร์แล้ว

## Decisions

- 2026-11-17 · May: ปุ่มบนหัวห้อง (ไม่ใช่พิมพ์ "พอแล้ว" · ยังไม่มี `route_intent`) · ไม่ถามยืนยัน · สรุปเป็น bubble ของ tutor · หลังจบล็อกช่องพิมพ์ + ลิงก์ "กลับหน้าหลัก" / "ติวรอบใหม่" · "ติวรอบใหม่" เป็นลิงก์
- 2026-11-17 · May (ตอน implement): หลังจบซ่อน canvas (เดิม AC-4 ให้อยู่แต่ส่งไม่ได้ · ขัดกับ AC-1 สรุปต้องอยู่ท้ายสุด) · แก้ AC-4 ใน spec + test
- 2026-11-17 · May (ตอน implement): เพิ่ม "จบการติว" ในรายการปุ่มของ test Jam `RoomPagePhoto.test.tsx` "no answer choice buttons in the whole room" (ไม่ใช่ตัวเลือกคำตอบ · TM-06) · บอก Jam
- 2026-11-17 · แก้ `session-end-db.md` §9 (spec ของ Jam) ให้ชี้มาที่ spec นี้ · บอก Jam

## Next step

ขั้น 4: May ลองหน้าตาในห้องเดโม่ (ไม่มี token · `/end` เป็น stub) · เส้นจริงบน DB (login → ตอบ → จบ → ติวรอบใหม่ → การ์ดเปลี่ยน) ลองตอนต่อทุกขั้น 19 พ.ย. หรือขอ Jam (ต้องมี prep ที่ยืนยัน scope แล้ว · `seed_scope_demo.py` ใช้ไฟล์บนเครื่อง Jam)

## Waiting on

- ไม่มี

## Notes for next time

- ปุ่มจบขึ้นเฉพาะเมื่อ `ChatRoom` ได้ `endSession` · test เดิมที่นับปุ่ม (ChatRoomVoice AC-17, Composer) จึงไม่ต้องแก้
