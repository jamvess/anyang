# Hint ladder: ทำทีละขั้นก่อนเฉลย ในเดโม่ห้องติว

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/hint-ladder` |
| Checklist item | เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง ให้อาจารย์ดูก่อนทำต่อ (อาจารย์ขอ 9 พ.ย. · เพิ่มเอง) · ส่วน "hint ladder ทำทีละขั้นก่อนเฉลย" |
| Status | in progress · 2026-11-12 |

## Plan

ออกแบบตกลงแล้ว 9 พ.ย. ("all ok"): A ขั้นที่ถูกแต่ยังไม่จบ · B ผิดแล้วไล่ hint 2 ระดับก่อนเฉลย · C จับว่ายอมแพ้ · D ผลต่อ BKT · E `explain_check/v3` รับ directive · ทำเฉพาะห้องเดโม่ในเครื่อง (`APP_ENV=local`) ส่วนอื่นยังเฉลยทันทีตาม AM-07 จนกว่าทีมตกลง

- [x] 1. 🤖 (12 พ.ย. · Jam ok) Spec `specs/features/tutor/demo-room.md` §2 K + AC + §7 AI calls + §11 ข้อเสนอแก้ AM-07, AM-10, PM-01 (ไม่แก้ `requirements.md` เอง) · 🙋 Jam review spec
- [x] 2. 🤖 (12 พ.ย. · ร่างแล้ว รอ Jam ส่งในกลุ่ม) ร่างข้อความเสนอทีมเรื่อง AM-07 · 🙋 Jam ส่งในกลุ่ม
- [x] 3. 🤖 (12 พ.ย. · Jam ok · แก้ test เดิม 4 ตัวตามที่ ok) Test (red) จาก AC: domain ตัดสิน directive + "ยังไม่จบ" + นโยบาย BKT · service: hint นับต่อโจทย์, give_up, ไม่มี verdict ตอนทำต่อ · prompt v3 / typed_answer v2 · 🙋 Jam review test
- [x] 4. 🤖 (12 พ.ย. · green · Jam ok ไฟล์กลาง) Implement จน green · ไฟล์กลาง `config/learning.yaml` (`tutoring.max_hints_before_solution: 2` [C]) และ `config/ai.yaml` (prompt version) ถาม Jam ก่อนแก้
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

ขั้น 5: Jam ลองในเบราว์เซอร์กับ Vertex ตามรายการในขั้น 5 (วิธีเปิด `demo-room.md` §12) แล้วเล่าผลหรือส่งภาพหน้าจอ

## Waiting on

ทีม (Junior, May): ตอบข้อเสนอแก้ AM-07 ในกลุ่ม · ไม่บล็อกงานเดโม่ (local เท่านั้น) แต่ต้องได้คำตอบก่อนเปิดบน staging

## Notes for next time

- `explain_check/v3` และ `typed_answer/v2` ยังไม่มี golden set (เหมือน v2 / v1) · เช็คด้วยการลองในเบราว์เซอร์เท่านั้น
- `test_prompt_data_blocks.py`: เพิ่ม `explain_check/v3`, `typed_answer/v2` ใน `OUTSIDE_BY_PROMPT` (ตั้งใจให้ prompt ใหม่ fail จนกว่าจะประกาศ · ทุก input อยู่ใน block)
- `typed_answer/v1` merge แล้วใน #115 จึงต้อง bump เป็น v2 (ตอนออกแบบคิดว่ายังแก้ v1 ได้)
