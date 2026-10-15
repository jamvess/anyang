# เลือกวิชา pilot สำหรับ P3 + เก็บชีทและข้อสอบเก่า

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/p3-pilot-subject` |
| Checklist item | ⭐ เลือกวิชาคณิต 1 วิชาสำหรับ P3 และหาชีท + ข้อสอบเก่า 2 ชุด |
| Status | in progress · 2026-10-15 |

## Plan

- [x] 1. 🤖 สร้าง branch, worklog และ Draft PR
- [ ] 2. 🤖 เขียน `evals/topics/README.md`: เกณฑ์เลือกวิชา, โครงโฟลเดอร์, กติกาไฟล์ลิขสิทธิ์ (ไฟล์จริงอยู่ใน `raw/` ซึ่ง gitignored + Drive ทีม) และ template `sources.md`
- [ ] 3. 🙋 เลือกวิชาตามเกณฑ์ แล้วบอกชื่อวิชา + เหตุผลสั้นๆ
- [ ] 4. 🙋 หาไฟล์ชีท + ข้อสอบเก่า 2 ชุด → อัปโหลดเข้า Drive ทีม และวางไว้ที่ `evals/topics/<subject>/raw/`
- [ ] 5. 🤖 ตรวจไฟล์ (จำนวนหน้า, เป็น text หรือสแกน, มีเลขข้อชัดไหม) แล้วกรอก `evals/topics/<subject>/sources.md`
- [ ] 6. 🤖 ติ๊ก checklist และร่างข้อความบอก May ว่าไฟล์พร้อม label แล้ว

## Definition of done

- เลือกวิชาคณิต 1 วิชาแล้ว และจดเหตุผลไว้
- มีชีท + ข้อสอบเก่า 2 ชุดใน Drive ทีม และใน `raw/` บนเครื่อง
- `evals/topics/<subject>/sources.md` ระบุทุกไฟล์ (ประเภท, ปี/ภาค, อาจารย์, จำนวนหน้า, text/สแกน, ลิงก์ Drive)
- ไม่มีไฟล์ PDF จริงขึ้น git

## Decisions

- 2026-10-15 · ไฟล์ชีทและข้อสอบจริงไม่ขึ้น git (ลิขสิทธิ์ของอาจารย์ + repo อาจเปิด public) · เก็บใน Drive ทีม และ `evals/**/raw/` ซึ่ง gitignored อยู่แล้ว

## Next step

เขียน `evals/topics/README.md` ตามขั้นที่ 2

## Waiting on

ไม่มี

## Notes for next time

- P3 spec อยู่ที่ `specs/poc/README.md` หัวข้อ P3 · May ต้องใช้ไฟล์เหล่านี้ label ให้เสร็จก่อน ศ. 23 ต.ค.
