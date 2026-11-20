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

## Results

### ขั้น 1–5 (ผ่านทั้งหมด · prep `b41af4d9…` · tenant ทดสอบ `f4b39742…`)

- login, สร้าง prep, อัปโหลด 6 ไฟล์ + ยืนยันประเภท, progress → scope **36 หัวข้อ** · หน้าเว็บไม่มี error
- ยืนยันไฟล์ → หน้า scope **5 นาที 55 วินาที** · ยืนยัน scope → เข้าห้องเห็นคำทัก + การ์ดโจทย์ **~21 วินาที** (Junior เข้าห้องทันที ไม่ได้รอ 1 นาที)
- AI calls จาก log (ok ทุกตัว · schema_retries 0): classify_material 6 (รวม 18.9 s) · vision_extract_pages 2 (21.8 s) · split_past_exam 2 (13.8 s) · embed 4 (44.6 s) · extract_topics_local 4 (202.1 s · ตัวที่ช้าสุด 186 s) · merge_topics 1 (54.1 s) · map_questions 2 (39.0 s) · open_session 1 (1.7 s) · generate_problem 1 (11.4 s)
- ⚠️ **429 ที่ผู้ใช้มองไม่เห็น:** `extract_topics_local` โดน 429 ติดกัน 3 ครั้ง (รอ 5 + 15 + 30 s ครบตาราง `[5, 15, 30]` แล้วครั้งที่ 4 ผ่าน) · ถ้าโดนครั้งที่ 4 ingestion จะล้มที่ขั้น "หาหัวข้อ" และบน `main` ยังไม่มีปุ่มลองใหม่ของขั้นรวม (#169) · `generate_problem` ตอนเปิดห้องโดน 429 1 ครั้ง (รอ 5 s แล้วผ่าน) · ไม่ได้รอ 1 นาทีก่อนเข้าห้อง
- 404 ของ `GET /exam-preps/{id}/sessions/active` ตอนเปิดห้องครั้งแรกถูกต้อง (ยังไม่มี session)
- 🐞 (May · เจอแล้ว 19 พ.ย. ยังอยู่) โจทย์ยาวล้นการ์ดด้านขวา

## Decisions

- 2026-11-20 · ไม่รอ #169 (ปุ่มลองใหม่ของ May) สำหรับวิดีโอ · conflict กับ `main` 4 ไฟล์ (ทำ `/materials/{id}/retry` ซ้ำกับ #171) และยังไม่ได้ลองในเบราว์เซอร์ · ซ้อมบน `main` ตามที่เป็น
- 2026-11-20 · `generate_problem` 3 รอบ (~23 วินาที) ยังไม่มีใครแก้ · น่าจะมาจาก `session.max_generate_retries: 2` (SymPy ไม่ผ่านหรือโจทย์ซ้ำ) · Junior เสนอ Jam หลังวิดีโอ: สร้างโจทย์ข้อถัดไปเบื้องหลังระหว่างที่ผู้ใช้ทำข้อปัจจุบัน

## Next step

ขั้น 5 (🙋 Junior): ขั้น 6–9 ในห้องของ prep `b41af4d9…` (ห้องเปิดอยู่แล้ว) แล้วบอก Claude · Claude อ่าน log (ขั้น 6)

## Waiting on

ไม่มี

## Notes for next time

- log ของ API อยู่ `.local/rehearsal-api.log` (gitignored) · บรรทัด JSON ของ logger `app.ai.calls` มี purpose + เวลา ใช้แทนการ query `ai_calls`
- log เป็น UTF-16 (Tee-Object ของ PowerShell 5.1) · อ่านด้วย `iconv -f UTF-16 -t UTF-8 .local/rehearsal-api.log` · บรรทัด `NativeCommandError` ตอนเริ่มเป็นแค่ PowerShell ห่อ stderr ไม่ใช่ error จริง
- PowerShell ตัดบรรทัด log ตามความกว้างจอ · ต่อบรรทัดก่อน parse JSON (record ขึ้นต้นด้วย `{"severity"` หรือ `INFO:`)
