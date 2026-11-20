# ซ้อม journey 9 ขั้นบน main ก่อนอัดวิดีโอ (20 พ.ย.)

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/journey-rehearsal-1120` |
| Checklist item | ไม่มีข้อเดี่ยวใน checklist · "วันสำคัญ: ศ. 20 พ.ย. ซ้อมเดินครบ + แก้บั๊ก" (⭐ Priority: demo end to end) |
| Status | in progress · 2026-11-20 |

## Plan

- [x] 1. 🤖 สร้าง branch + worklog + draft PR
- [ ] 2. 🙋 เปิด API จาก `main` (VS Code terminal ที่โหลด `.env` · `APP_ENV=local AI_PROVIDER=live AUTH_REQUIRED=true` ชี้ `anyang-dev`): `cd apps/api; uv run fastapi run app/main.py 2>&1 | Tee-Object ..\..\.local\rehearsal-api.log` · เว็บ: `cd apps/web; pnpm dev`
- [ ] 3. 🙋 ขั้น 1–5 ด้วยบัญชีทดสอบ: login → prep "rehearsal 20 Nov" → อัปโหลด 6 ไฟล์ MTH10101 + ยืนยันประเภท → progress → scope (จดเวลา) → ยืนยัน scope → รอ ~1 นาที
- [ ] 4. 🤖 อ่าน `.local/rehearsal-api.log` ขั้น 1–5: 429, error, จำนวน call และเวลาต่อ purpose · จดผ่าน/ไม่ผ่าน
- [ ] 5. 🙋 ขั้น 6–9: เข้าห้อง (การ์ด + คำทัก + การ์ดโจทย์) → ตอบผิด 1 ครั้ง (hint) → ตอบถูกพร้อมวิธีทำ ≥2 ขั้น + ส่งรูป 1 ครั้ง → ออกแล้วเปิดใหม่ (การ์ดเปลี่ยน) → จบ session (สรุป) → เปิดใหม่เห็นประวัติ → "ติวรอบใหม่" ได้คำทัก
- [ ] 6. 🤖 อ่าน log ขั้น 6–9: นับ `generate_problem` ต่อโจทย์ + เหตุที่ถูกปฏิเสธ
- [ ] 7. 🤖 จัดบั๊ก: ของ Junior → PR `fix/…` แยก (ถาม Junior ก่อน merge) · ของ Jam/May → ร่างข้อความ + หลักฐาน · ทางเลี่ยงวันอัดเสนอเพิ่มใน `demo-video.md`
- [ ] 8. 🤖 ร่างข้อความกลุ่ม: ผลซ้อม + สถานะ #169 + เรื่อง `generate_problem` 3 รอบ

## Definition of done

- 9 ขั้นผ่านบน `main` ด้วยบัญชีทดสอบ หรือขั้นที่ไม่ผ่านมีเจ้าของ + ทางเลี่ยงสำหรับวันอัดจดไว้แล้ว
- ส่งผลลงกลุ่มแล้ว

## Decisions

- 2026-11-20 · ไม่รอ #169 (ปุ่มลองใหม่ของ May) สำหรับวิดีโอ · conflict กับ `main` 4 ไฟล์ (ทำ `/materials/{id}/retry` ซ้ำกับ #171) และยังไม่ได้ลองในเบราว์เซอร์ · ซ้อมบน `main` ตามที่เป็น
- 2026-11-20 · `generate_problem` 3 รอบ (~23 วินาที) ยังไม่มีใครแก้ · น่าจะมาจาก `session.max_generate_retries: 2` (SymPy ไม่ผ่านหรือโจทย์ซ้ำ) · Junior เสนอ Jam หลังวิดีโอ: สร้างโจทย์ข้อถัดไปเบื้องหลังระหว่างที่ผู้ใช้ทำข้อปัจจุบัน

## Next step

ขั้น 2 (🙋 Junior): เปิด API + เว็บตามคำสั่งในขั้น 2 แล้วบอก Claude · Claude เช็คว่า `.local/rehearsal-api.log` มีบรรทัด startup

## Waiting on

ไม่มี

## Notes for next time

- log ของ API อยู่ `.local/rehearsal-api.log` (gitignored) · บรรทัด JSON ของ logger `app.ai.calls` มี purpose + เวลา ใช้แทนการ query `ai_calls`
