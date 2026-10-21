# Wireframe หน้าเพิ่มไฟล์ทีหลัง (UC-02 A9 · D6)

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-add-files` |
| Checklist item | ไม่มีข้อตรงใน checklist · ส่วนที่เหลือของ "ต้องเพิ่มใน wireframe" UC-02 (หน้าเพิ่มไฟล์ทีหลัง A9) |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 branch + worklog + draft PR
- [ ] 2. 🙋 May เลือกทางเข้า (เพิ่มไฟล์จากตรงไหน) · spec ยังไม่กำหนด
- [ ] 3. 🤖 เพิ่ม 2 หน้าท้ายบทที่ 6: เพิ่มไฟล์ (เฉพาะไฟล์ใหม่ · CM-05) และยืนยันขอบเขตใหม่ที่แสดงเฉพาะส่วนที่เปลี่ยน (SM-08, ai-orchestration §2.3.6) · screenshot ตรวจ
- [ ] 4. 🙋 May review
- [ ] 5. 🤖 `use-cases.md` UC-02 ทำเครื่องหมาย A9 เสร็จ

## Definition of done

- หน้าเพิ่มไฟล์ทีหลังตาม UC-02 A9 อยู่ใน wireframe · script ไม่มี error · May approve

## Decisions

## Next step

ขั้น 2: ถาม May เรื่องทางเข้า

## Waiting on

ไม่มี

## Notes for next time

- บทที่ 6 อยู่ท้าย array `steps` ใน `docs/design/wireframe.html` · เพิ่มชื่อใน `LABELS` และแก้จำนวนหน้าใน kicker
- screenshot: แทน `go(0);` ด้วย `go(N-1);` ในสำเนาใน scratchpad แล้วใช้ Chrome `--headless=new --screenshot`
