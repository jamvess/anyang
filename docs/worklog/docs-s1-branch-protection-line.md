# แก้บรรทัด branch protection ใน checklist S1 ตาม review ของ Jam บน PR #17

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/s1-branch-protection-line` |
| Checklist item | ⭐ สร้าง repo, วาง starter files · branch protection ตั้งแล้ว 15 ต.ค. (repo เป็น public, Jam ตั้ง ruleset 25137368: PR + 1 approval + CI 3 job) |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🙋 เลือกข้อความ · เลือกข้อ 1 (ยังติ๊กไว้ แก้แค่ส่วนที่ผิด)
- [x] 2. 🤖 สร้าง branch + worklog + draft PR
- [x] 3. 🤖 แก้บรรทัด S1 ข้อแรกใน `docs/team/sprint-checklists.md` บรรทัดเดียว · ไม่แตะไฟล์อื่น (ไม่แก้ `setup.md`)
- [ ] 4. 🙋 เปิดไฟล์ดูว่าข้อความถูก แล้วตอบ ok
- [ ] 5. 🤖 `/work-done` · PR description ลิงก์ #17 · ขอ review จาก Jam

## Definition of done

- บรรทัด S1 ข้อแรกไม่บอกว่า branch protection ตั้งแล้ว · ตรงกับสถานะจริง 19 ต.ค. (ruleset 25137368 หายไป · ruleset `main` id 25374094 ปิดอยู่)
- diff มีแค่บรรทัดนั้นบรรทัดเดียว
- PR ลิงก์ #17 และขอ review จาก Jam

## Decisions

- 2026-10-19 · ยังติ๊ก `[x]` ไว้ · ส่วน "สร้าง repo, วาง starter files" เสร็จจริง ถ้ายกเลิกติ๊กจะดูเหมือนยังไม่ได้สร้าง repo
- 2026-10-19 · ใช้ข้อความตัวอย่างของ Jam แล้วเพิ่ม ruleset ใหม่ 25374094 ที่ปิดอยู่ · Jam เขียนข้อความไว้เป็นแค่ตัวอย่าง ("เช่น") และหลังจากนั้นมีการสร้าง ruleset ใหม่ (ยังปิดอยู่)
- 2026-10-19 · ไม่แก้ PR description ของ #17 แม้ Jam จะขอไว้ · PR นั้น merge ไปแล้ว และ Junior ให้แก้แค่บรรทัดเดียว

## Next step

ขั้น 4: Junior เปิด `docs/team/sprint-checklists.md` บรรทัด 23 เช็คข้อความ แล้วตอบ ok → commit แล้วรัน `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- งานนี้เป็นงานที่ 2 ของวัน 19 ต.ค. · งานถัดไปคือร่วม review `requirements.md` (D1)
