# อัปเดต architecture และ data model ตามสิ่งที่สร้างแล้ว (D2, D3)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `docs/architecture-poc-update` |
| Checklist item | อัปเดต architecture และ data model ตามผล PoC (D2, D3) |
| Status | in progress · 2026-11-12 |

## Plan

ช่วง solo · Jam ไม่มีเวลา จึงไม่มีขั้น 🙋 ระหว่างทาง · Junior ดูย้อนหลังได้

- [x] 1. 🤖 (12 พ.ย.) `specs/system/architecture.md` v1.3: ตาราง "สร้างแล้วหรือยัง" ณ 12 พ.ย. เทียบกับโค้ดจริงทีละแถว (P2 ต่อเข้าห้องแล้ว · ห้องติวบน DB #123 · exam prep API #121 · `domain/` ที่มีแล้ว: checker, stars, bkt, hint_ladder · เดโม่ในเครื่อง `APP_ENV=local` · canvas · login / staging ยังรอ #120)
- [x] 2. 🤖 (12 พ.ย.) `specs/system/data-model.md` v1.4: แถว `0004` ในตาราง migration · ERD ครอบคลุมถึง `0004` · หัวข้อ "รอทีม": `attempts` อาจต้องเก็บจำนวน hint (ข้อเสนอแก้ AM-07 · PR #127) · ไม่มี migration ใหม่
- [x] 3. 🤖 (12 พ.ย.) checklist: sub-bullet ใต้ข้อนี้ ("ทำโดย Jam ช่วง solo") · ไม่ติ๊ก ถ้ายังเหลืออัปเดตหลัง P8-lite ตามที่ข้อนี้เขียนไว้ แล้ว `/work-done`

## Definition of done

- ทุกแถวใน "สร้างแล้วหรือยัง" ตรงกับโค้ดบน main วันนี้ และมีที่มา (spec / PR)
- data model มี `0004` และไม่มีข้อความที่ขัดกับ migration จริง
- ไม่แก้ไฟล์กลาง (`api.md`, `requirements.md`, `config/*.yaml`)

## Decisions

- 2026-11-12 · ทำช่วง solo โดย Jam (item ของ Junior) · เป็นเอกสารล้วน ไม่มีโค้ด

## Next step

ทุกขั้นเสร็จ · `/work-done`

## Waiting on

Junior: ดูย้อนหลังหลัง merge

## Notes for next time

- ไม่มี
