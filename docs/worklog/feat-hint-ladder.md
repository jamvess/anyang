# Hint ladder: ทำทีละขั้นก่อนเฉลย ในเดโม่ห้องติว

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/hint-ladder` |
| Checklist item | เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง ให้อาจารย์ดูก่อนทำต่อ (อาจารย์ขอ 9 พ.ย. · เพิ่มเอง) · ส่วน "hint ladder ทำทีละขั้นก่อนเฉลย" |
| Status | in progress · 2026-11-12 |

## Plan

ออกแบบตกลงแล้ว 9 พ.ย. ("all ok"): A ขั้นที่ถูกแต่ยังไม่จบ · B ผิดแล้วไล่ hint 2 ระดับก่อนเฉลย · C จับว่ายอมแพ้ · D ผลต่อ BKT · E `explain_check/v3` รับ directive · ทำเฉพาะห้องเดโม่ในเครื่อง (`APP_ENV=local`) ส่วนอื่นยังเฉลยทันทีตาม AM-07 จนกว่าทีมตกลง

- [x] 1. 🤖 (12 พ.ย. · รอ Jam ok) Spec `specs/features/tutor/demo-room.md` §2 K + AC + §7 AI calls + §11 ข้อเสนอแก้ AM-07, AM-10, PM-01 (ไม่แก้ `requirements.md` เอง) · 🙋 Jam review spec
- [ ] 2. 🤖 ร่างข้อความเสนอทีมเรื่อง AM-07 · 🙋 Jam ส่งในกลุ่ม
- [ ] 3. 🤖 Test (red) จาก AC: domain ตัดสิน directive + "ยังไม่จบ" + นโยบาย BKT · service: hint นับต่อโจทย์, give_up, ไม่มี verdict ตอนทำต่อ · prompt v3 / typed_answer v2 · 🙋 Jam review test
- [ ] 4. 🤖 Implement จน green · ไฟล์กลาง `config/learning.yaml` (`tutoring.max_hints_before_solution: 2` [C]) และ `config/ai.yaml` (prompt version) ถาม Jam ก่อนแก้
- [ ] 5. 🙋 Jam ลองในเบราว์เซอร์กับ Vertex: ข้อ 3 (อนุพันธ์) ส่งขั้นแรก → "ถูกแล้ว ทำต่อ" · ส่งผิด 2 ครั้ง → hint 1, hint 2 · ครั้งที่ 3 → เฉลย · พิมพ์ "ไม่ได้จริงๆ" → เฉลยทันที (วิธีเปิด: spec §12)
- [ ] 6. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- ในห้องเดโม่ในเครื่อง: ขั้นที่ถูกแต่ยังไม่จบได้ "ทำต่อ" ไม่มี ✓/✗ · ผิดได้ hint ระดับ 1, 2 ก่อนเฉลย · ยอมแพ้ได้เฉลยทันที · BKT นับครั้งเดียวต่อโจทย์ตามข้อ D
- ทุก threshold อ่านจาก config · prompt bump version · test ผ่านใน CI
- ข้อเสนอแก้ AM-07 ส่งทีมแล้ว (requirements.md แก้เมื่อทีมตกลง)

## Decisions

- 2026-11-09 · ออกแบบ A–E ตามที่เสนอ และแยกเป็น PR หลัง canvas · Jam "all ok"
- 2026-11-12 · ทำเฉพาะ `APP_ENV=local` · AM-07 ยังเป็น requirement ของทีม จึงไม่เปลี่ยนพฤติกรรมของ staging
- 2026-11-12 · `typed_answer` เพิ่ม field `give_up` (default false) แทน intent 3 ค่า · output ของ v1 และ test เดิมที่ใช้ `is_answer` ยังใช้ได้
- 2026-11-12 · ระหว่างใบ้ `explain_check` ไม่ได้รับเฉลย (AM-13) · code กันไว้ ไม่พึ่ง prompt

## Next step

รอ Jam review `demo-room.md` §2 K, AC-39 ถึง 50, §10 ข้อ 4–5, §11 · ok แล้วทำขั้น 2 (ร่างข้อความเสนอทีมเรื่อง AM-07)

## Waiting on

ไม่มี

## Notes for next time

- `typed_answer/v1` merge แล้วใน #115 จึงต้อง bump เป็น v2 (ตอนออกแบบคิดว่ายังแก้ v1 ได้)
