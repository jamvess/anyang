# Team setup guide v2 (own machines, no Docker)

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/team-setup-v2` |
| Checklist item | ไม่มีข้อตรงตัว · รองรับ "ตั้งเครื่องตัวเองตาม `setup.md` Part A" ของทุกคน |
| Status | in progress · 2026-10-14 |

## Plan

- [x] 0. 🤖 เขียน `setup.md` ใหม่ (Part A ตั้งเครื่อง, Part B ทำงานคู่ขนาน) + ติ๊ก `sprint-checklists.md` ตามงานที่เสร็จจริง (commit be64b84)
- [x] 1. 🤖 สร้าง worklog นี้
- [ ] 2. 🤖 ตัด B2–B3 ใน `setup.md` ให้เหลือลิงก์ไป `daily-workflow.md` (เก็บ B1, B4, B5)
- [ ] 3. 🤖 แก้ลิงก์ `setup.md §5` ที่ตาย: ย้ายคำสั่ง cloud เดิมไป `infra/README.md` แล้วแก้ `sprint-checklists.md:27` กับ `infra/README.md:5`
- [ ] 4. 🤖 commit + push + เตรียมลิงก์เปิด PR
- [ ] 5. 🙋 เปิด PR บน GitHub: กดลิงก์ที่ Claude ให้ → **Create pull request** → Reviewers เลือก Junior → บอกในแชทกลุ่ม

## Definition of done

- ไม่มีลิงก์ใน `docs/team/` และ `infra/` ที่ชี้ไปหัวข้อที่ไม่มีอยู่แล้ว
- วิธีทำงานประจำวันมีที่เดียว คือ `daily-workflow.md`
- เปิด PR แล้ว และ Junior เป็น reviewer

## Decisions

- 2026-10-14 · คำสั่งสร้าง cloud resource ย้ายไป `infra/README.md` · เป็นงานของ Junior คนเดียว ไม่ใช่สิ่งที่ทุกคนต้องทำตอนตั้งเครื่อง

## Next step

ตัด B2–B3 ใน `docs/team/setup.md` ให้เหลือย่อหน้าเดียวที่ลิงก์ไป `docs/team/daily-workflow.md`

## Waiting on

ไม่มี

## Notes for next time

- ไฟล์ใน `docs/team/*` เป็นไฟล์กลาง ต้องบอกในแชทกลุ่มก่อนแก้
