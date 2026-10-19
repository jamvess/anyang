# Use case UC สมัคร และ UC upload → scope (D7)

| | |
|---|---|
| Owner | May |
| Branch | `docs/use-cases-signup-scope` |
| Checklist item | Use case UC สมัคร และ UC upload → scope (D7) |
| Status | in progress · 2026-10-19 |

## Plan

ไฟล์ที่ได้: `docs/design/use-cases.md` (ทั้ง 4 UC จะอยู่ไฟล์นี้ · PR นี้ทำ UC-01 และ UC-02 ส่วน UC ติว และ UC ส่งคำตอบทำใน S4)
รูปแบบต่อ UC: actor, เป้าหมาย, requirement, หน้าจอ, เงื่อนไขก่อนเริ่ม, main flow, alternative flows, exception flows, ผลลัพธ์, คำถามเปิด · ทุกขั้นอ้างหน้าจอ (S01–S27) และ requirement ID · ไม่เดาพฤติกรรมที่ spec ไม่มี (ใส่เป็นคำถามเปิด)

- [x] 1. 🤖 ร่างโครงไฟล์ + UC-01 สมัครสมาชิกและตั้งค่าเริ่มต้น (S01–S07 · UM-01–UM-08) · 2026-10-19 main 9 ขั้น, A 4, E 6, คำถามเปิด 7
- [x] 2. 🙋 May review UC-01 (Claude สรุปในแชท + ถามเรื่องที่ต้องตัดสินเป็นตัวเลือก) · 2026-10-19 May ตัดสิน 4 ข้อ
- [ ] 3. 🤖 ร่าง UC-02 สร้างการเตรียมสอบ อัปโหลด และยืนยันขอบเขต (S07–S14 · CM-01–CM-07, SM-01–SM-12 · ai-orchestration §2.3)
- [ ] 4. 🙋 May review UC-02
- [ ] 5. 🤖 ตรวจความสอดคล้อง: ทุก requirement ID และหน้าจอที่อ้างมีจริง, ทุก requirement Must ที่ Screen อยู่ใน S01–S14 ถูกใช้ใน UC ใด UC หนึ่ง

## Definition of done

- `docs/design/use-cases.md` มี UC-01 และ UC-02 ครบ main flow, alternative flows, exception flows
- ทุกขั้นอ้างหน้าจอและ requirement ID ที่มีจริง · May approve · Junior review PR

## Decisions

- 2026-10-19 · ใช้ type `docs` · เป็นเอกสาร design (D7)
- 2026-10-19 · UC-01 May ตัดสิน: ยืนยันอีเมล (Google ไม่ต้อง) · อีเมลซ้ำบอกตรงๆ + ปุ่มเข้าสู่ระบบ · ปิดกลางคันกลับหน้าที่ค้าง · แปลง persona ไม่ได้ให้ลองใหม่หรือใช้ preset · เรื่องเทคนิค 3 ข้อ (รหัสผ่าน, enum ภาษา, ความยาวคำบรรยาย) ฝาก Junior
- 2026-10-19 · วางไฟล์ที่ `docs/design/` ข้าง wireframe · use case เล่า flow ของผู้ใช้ ไม่ใช่ spec ระดับ 1–3

## Next step

Claude ทำขั้น 3: ร่าง UC-02

## Waiting on

ไม่มี

## Notes for next time

- งานเฉลย LaTeX (P1) พร้อมเริ่มแล้ว: รูปอยู่ใน Drive · `labels.jsonl` แบบโครง 30 แถวอยู่ใน PR #11 ของ Jam
