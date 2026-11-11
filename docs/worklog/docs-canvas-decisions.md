# May ตัดสินหน้าตา canvas ย้อนหลัง (answer-canvas.md §10)

| | |
|---|---|
| Owner | May |
| Branch | `docs/canvas-decisions` |
| Checklist item | ไม่มีใน checklist · ค้างจาก `specs/features/tutor/answer-canvas.md` §10 (Jam ทำดีไซน์ชั่วคราว 9 พ.ย. · PR #117) |
| Status | in progress · 2026-11-11 |

## Plan

- [ ] 1. 🤖 สรุปพฤติกรรมตอนนี้ของ 4 เรื่องใน §10 เป็นภาษาไทย + วิธีเปิดห้องเดโม่ในเครื่องด้วย AI จำลอง (ไม่ต้องใช้สิทธิ์ Vertex)
- [ ] 2. 🙋 May ลองใช้ canvas ในห้องเดโม่ (เขียน, ยางลบ, ย้อนกลับ, ล้าง, ใส่รูป, ส่ง, คุยต่อ, ไปข้อถัดไป)
- [ ] 3. 🙋 May ตัดสิน 4 เรื่อง (Claude ถามเป็นตัวเลือก)
- [ ] 4. 🤖 บันทึกคำตัดสินใน `answer-canvas.md` §10 · ถ้ามีข้อที่ต่างจากของตอนนี้ → แก้ §2 + เขียน test ใหม่ (`/spec-to-tests`, May review) + implement ใน PR นี้ ถ้าเล็ก หรือแยก PR ถ้าใหญ่

## Definition of done

- §10 ของ `answer-canvas.md` ปิดครบ 4 ข้อด้วยคำตัดสินของ May
- ถ้าเปลี่ยน behavior: spec §2, test และโค้ดตรงกัน · CI เขียว

## Decisions

- 2026-11-11 · ใช้ type `docs` ไว้ก่อน · ถ้ามีโค้ดเปลี่ยนจะบอกใน PR

## Next step

Claude ทำขั้น 1

## Waiting on

ไม่มี

## Notes for next time

- `answer-canvas.md` Owner คือ Jam แต่หน้าจอเป็นของ May (roles.md "ตัดสินใจเรื่อง")
