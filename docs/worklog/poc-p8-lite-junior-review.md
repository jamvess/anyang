# P8-lite · Junior review test ของ `compute_importance` ย้อนหลัง

| | |
|---|---|
| Owner | Junior |
| Branch | `poc/p8-lite-junior-review` |
| Checklist item | P8-lite ร่วมกับทีม (review test ของ `compute_importance`) |
| Status | paused · 2026-11-22 · Junior ทำต่อหลัง advisor update 23 พ.ย. |

## Plan

- [ ] 1. 🤖 ทำตาราง AC → test เป็นภาษาไทย (`specs/features/scope/compute-importance.md` ↔ `apps/api/tests/unit/test_stars.py`) · บอกจุดที่ May กับ `/code-review` ยังไม่ได้ดู · เขียนคำถามให้ Junior ตอบไม่เกิน 3 ข้อ · Claude ห้ามแก้ test (Jam review แล้ว)
- [ ] 2. 🙋 Junior review: จดเวลาเริ่มจากนาฬิกาจริง → เปิด `apps/api/tests/unit/test_stars.py` ใน VS Code → อ่านตารางของ Claude คู่กับโค้ด test → ตอบคำถาม → จดเวลาจบ · บอก Claude ด้วยว่าอ่านโค้ด test เอง หรืออ่านแค่ตาราง (§4 แยกสองแบบนี้ไว้)
- [ ] 3. 🤖 จดผลใน `poc/P8-lite/metrics.md`: แถวของ Junior ใน §4 · ถ้าเจอ test ผิด เปราะ หรือมีช่องโหว่ ให้เพิ่มในตารางที่ 2 ของ §3 · แถว "เวลาที่คนใช้รวม" ใน §6
- [ ] 4. 🤖 tick ข้อ P8-lite ของ Junior ใน `docs/team/sprint-checklists.md` พร้อมบรรทัดวันที่ + PR
- [ ] 5. 🙋 `/work-done` · Claude ถามก่อน merge

## Definition of done

- Junior review test ของ `compute_importance` แล้ว (ตามข้อ checklist)
- เวลาที่ใช้มาจากนาฬิกาจริง จดใน `poc/P8-lite/metrics.md` §4 · ไม่ได้ประมาณ
- สิ่งที่เจอจดใน §3 · ไม่แก้ test ที่ review แล้ว (ถ้าต้องเพิ่มหรือแก้ test ให้เสนอ Jam ทำใน PR ใหม่)

## Decisions

- 2026-11-22 · ทำหลัง demo ตามแผน 13 พ.ย. แต่เริ่มก่อนอัดวิดีโอได้ เพราะไม่แตะโค้ดหรือ staging
- 2026-11-22 · report P8-lite และตัวเลขสำหรับ Self-Assessment เป็นข้อของ Jam ไม่ทำใน branch นี้

## Done today (2026-11-22)

- เปิด branch + worklog + draft PR #175 · เขียนแผน 5 ข้อแล้ว · ยังไม่ได้ทำข้อไหน และ Junior ยังไม่ได้ ok แผน

## Next step

ถาม Junior ว่าแผน 5 ข้อด้านบนโอเคไหม · ถ้า ok ให้ทำข้อ 1: อ่าน `specs/features/scope/compute-importance.md` (AC ทั้งหมด + §10) กับ `apps/api/tests/unit/test_stars.py` แล้วทำตาราง AC → test เป็นภาษาไทย (แบบเดียวกับที่ทำให้ May 11 พ.ย.) · บอกจุดที่ `poc/P8-lite/metrics.md` §3 ยังไม่มี · ตั้งคำถามไม่เกิน 3 ข้อ · ห้ามแก้ test

## Waiting on

ไม่มี

## Notes for next time

- PR #113 merge แล้ว (8 พ.ย.) · review นี้เป็นแบบย้อนหลัง เหมือนที่ May ทำ 11 พ.ย.
- อย่าเริ่มจับเวลาจนกว่า Junior จะบอกเวลาเริ่มเอง (ข้อ 2) · เวลาที่ Claude ทำตารางในข้อ 1 จดเป็นแถวของ Claude แยกจากเวลาของคน
- เลื่อนออกไปเพราะ 23 พ.ย. มีอัดวิดีโอ demo + advisor update · ข้อ checklist นี้มีป้ายว่า "หลัง demo" อยู่แล้ว
