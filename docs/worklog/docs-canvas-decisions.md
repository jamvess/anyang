# May ตัดสินหน้าตา canvas ย้อนหลัง (answer-canvas.md §10)

| | |
|---|---|
| Owner | May |
| Branch | `docs/canvas-decisions` |
| Checklist item | ไม่มีใน checklist · ค้างจาก `specs/features/tutor/answer-canvas.md` §10 (Jam ทำดีไซน์ชั่วคราว 9 พ.ย. · PR #117) |
| Status | in progress · 2026-11-11 |

## Plan

- [x] 1. 🤖 สรุปพฤติกรรมตอนนี้ของ 4 เรื่องใน §10 เป็นภาษาไทย + วิธีเปิดห้องเดโม่ในเครื่องด้วย AI จำลอง (ไม่ต้องใช้สิทธิ์ Vertex) · 2026-11-11 ลองแล้ว: `APP_ENV=local AI_PROVIDER=fake` เปิดห้องได้ (การ์ด + ข้อความทักสำรอง + โจทย์) · ส่งคำตอบกับ AI จำลองจะไม่ได้ผลตรวจจริง แต่พอลอง canvas
- [x] 2. 🙋 May ลองใช้ canvas ในห้องเดโม่ (เขียน, ยางลบ, ย้อนกลับ, ล้าง, ใส่รูป, ส่ง, คุยต่อ, ไปข้อถัดไป)
- [x] 3. 🙋 May ตัดสิน 4 เรื่อง (Claude ถามเป็นตัวเลือก) · 2026-11-12 ทั้ง 4 ข้อเลือกตามของเดิม
- [x] 4. 🤖 บันทึกคำตัดสินใน `answer-canvas.md` §10 · ถ้ามีข้อที่ต่างจากของตอนนี้ → แก้ §2 + เขียน test ใหม่ (`/spec-to-tests`, May review) + implement ใน PR นี้ ถ้าเล็ก หรือแยก PR ถ้าใหญ่ · 2026-11-12 ไม่มีข้อไหนเปลี่ยน behavior → แก้แค่ §10 และ Status

## Definition of done

- §10 ของ `answer-canvas.md` ปิดครบ 4 ข้อด้วยคำตัดสินของ May
- ถ้าเปลี่ยน behavior: spec §2, test และโค้ดตรงกัน · CI เขียว

## Decisions

- 2026-11-11 · ใช้ type `docs` ไว้ก่อน · ถ้ามีโค้ดเปลี่ยนจะบอกใน PR
- 2026-11-12 · May ลอง canvas ในห้องเดโม่ (AI จำลอง) แล้วเลือกตามของเดิมครบ 4 ข้อ: ท้ายแชท · 320 px + เครื่องมือชุดเดิม · ภาพยังอยู่หลังส่ง · ข้อเก่าหาย

## Next step

ทุกขั้นเสร็จแล้ว · May พิมพ์ `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- `answer-canvas.md` Owner คือ Jam แต่หน้าจอเป็นของ May (roles.md "ตัดสินใจเรื่อง")
