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
- [x] 5. 🙋 ขั้น 6–9: เข้าห้อง (การ์ด + คำทัก + การ์ดโจทย์) → ตอบผิด 1 ครั้ง (hint) → ตอบถูกพร้อมวิธีทำ ≥2 ขั้น + ส่งรูป 1 ครั้ง → ออกแล้วเปิดใหม่ (การ์ดเปลี่ยน) → จบ session (สรุป) → เปิดใหม่เห็นประวัติ → "ติวรอบใหม่" ได้คำทัก
- [x] 6. 🤖 อ่าน log ขั้น 6–9: นับ `generate_problem` ต่อโจทย์ + เหตุที่ถูกปฏิเสธ
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

### ขั้น 6–8 (session `44a6ce6a…`)

- ✅ ขั้น 6: การ์ด + คำทัก + การ์ดโจทย์ (generate_problem ok · tokens_out 591 · 11.4 s)
- ✅ ขั้น 7 ผิดผ่าน canvas: OCR "a = 71" → การ์ดยืนยัน → "✗ ยังไม่ถูก · บรรทัด 1" + hint ไม่บอกคำตอบ
- ✅ ขั้น 7 ถูก (พิมพ์ `a = sqrt(2/3)`): "✓ ถูก" 13:05 + คำอธิบาย
- ❌ **ไม่มีโจทย์ข้อถัดไป** · `generate_problem` 3 ครั้ง **truncated ทุกครั้ง** ที่ `max_tokens=2000` (tokens_out 1983/1985/1984 · 17.7 + 14.4 + 9.6 = 41.7 s) · input เท่ากันทุกครั้ง (3353) · ไม่ใช่ 429 และไม่ใช่ SymPy ปฏิเสธ · thinking `low` นับรวมใน max_tokens (แบบ #170 ของ classify)
  - spec `room-answers-db.md` §2.2 ข้อ 5: สร้างไม่ได้ → None → **ไม่ส่งอะไรเลย** ผู้ใช้ค้างอยู่กับ canvas ของโจทย์เก่า ("ส่งแล้ว · แก้แล้วส่งใหม่ได้") ไม่มีข้อความ `no_problem` แบบตอนเปิดห้อง → ช่องว่างของ spec (Jam)
  - น่าจะเป็นสาเหตุเดียวกับ "3 รอบ ~23 s" ของ 19 พ.ย. (แก้ข้อสันนิษฐานเดิมใน Decisions: ไม่ใช่ `max_generate_retries` เพราะ SymPy · เป็น retry หลังถูกตัด)
- ⚠️ `check_answer` truncated 1 ครั้ง ที่ `max_tokens=600` (tokens_out 584) → "classifier failed; the answer can be sent again" · ครั้งที่ ok ใช้ 527 · ใกล้เพดาน
- ✅/ℹ️ ขั้น 8 เปิดใหม่: ประวัติแชทกลับมา · การ์ดยังเป็น 0/36, 0%, ลิมิตของฟังก์ชัน "ยังไม่เริ่ม" · **ตาม spec** (`progress-card.md`, TM-15): การ์ดส่งตอนเปิด session และเก็บเป็นข้อความ `card` ในประวัติ · resume แสดงประวัติเดิม ไม่คำนวณใหม่ · การ์ดใหม่มาเมื่อเปิด session ใหม่ (ดูในขั้น 9) · คำตอบถูกหลังคำอธิบายไม่นับ mastery (`bkt.count_only_independent`)

### ขั้น 9

- ✅ "จบการติว" → สรุป (`session_summary` ok · 17.3 s)
- ❌ **เข้าห้องใหม่ ~13:21 → ห้องว่าง** (ไม่มีประวัติ ไม่มีการ์ด ไม่มีคำทัก ไม่มีโจทย์) · รอเกิน 1 นาทีก็ยังว่าง · บั๊กเดียวกับ 17 พ.ย. (ข้อ 2)
  - log: `GET sessions/active` 404 → `OPTIONS POST /exam-preps/{id}/sessions` → **ไม่มีบรรทัด POST** → `GET sessions/active` 200 = `1b325411…` → `GET /sessions/1b325411…` 200 · **ไม่มี AI call ใดๆ หลัง `session_summary`** (ไม่มี `open_session`, `generate_problem`)
  - กลไก: router (`room.py` `_open_and_save`) สร้างแถว `tutor_sessions` ก่อน stream · การ์ด คำทัก โจทย์ และการบันทึกอยู่ใน generator ของ SSE · ไม่มีบรรทัด access log ของ POST = client ตัดก่อน response เริ่ม (sse-starlette ยกเลิก generator เมื่อ client หลุด) → แถว session ค้าง ไม่มีข้อความ → ครั้งถัดไป `sessions/active` คืน session ว่างนี้ → หน้าเว็บ resume แบบไม่มีอะไรแสดง และไม่มีใครเติมคำเปิดให้
  - ชั้นที่เกี่ยว: (1) web `TutorRoom.tsx` abort POST ตอน cleanup ของ effect (May) · ตัวกระตุ้นในเบราว์เซอร์ยังไม่รู้แน่ (ออกจากหน้า / remount ใน dev) · (2) API router สร้างแถวก่อนแล้วปล่อยให้ opening ตายไปกับ connection (Junior · issue #126) · (3) resume ของ session ที่ไม่มีคำเปิดไม่สร้างใหม่ (room opening · Jam · บั๊ก 3 ของ 17 พ.ย.)
  - ทางเลี่ยงวันอัด: หลังจบ ใช้ปุ่ม "ติวรอบใหม่" (ผ่าน 19 พ.ย.) และอย่าออกจากหน้าห้องจนการ์ดโจทย์ขึ้น · ถ้าห้องว่าง Junior ปิด session ว่างใน SQL Editor แล้ว reload ห้อง → session ใหม่

## Decisions

- 2026-11-20 · ไม่รอ #169 (ปุ่มลองใหม่ของ May) สำหรับวิดีโอ · conflict กับ `main` 4 ไฟล์ (ทำ `/materials/{id}/retry` ซ้ำกับ #171) และยังไม่ได้ลองในเบราว์เซอร์ · ซ้อมบน `main` ตามที่เป็น
- 2026-11-20 · `generate_problem` 3 รอบ (~23 วินาที) ยังไม่มีใครแก้ · น่าจะมาจาก `session.max_generate_retries: 2` (SymPy ไม่ผ่านหรือโจทย์ซ้ำ) · Junior เสนอ Jam หลังวิดีโอ: สร้างโจทย์ข้อถัดไปเบื้องหลังระหว่างที่ผู้ใช้ทำข้อปัจจุบัน

## Next step

Junior วาง CSV ของ query `ai_calls` (ข้อความในแชท 20 พ.ย.) → Claude เปิด PR `fix/ai-max-tokens-headroom` แก้ `config/ai.yaml` ทุก purpose ที่ max ≥ ~70% ของเพดาน + timeout · Junior บอก Jam + กลุ่มก่อน merge · merge แล้ว restart API ลองตอบถูกให้ได้โจทย์ข้อถัดไป

## Waiting on

ไม่มี

## Notes for next time

- log ของ API อยู่ `.local/rehearsal-api.log` (gitignored) · บรรทัด JSON ของ logger `app.ai.calls` มี purpose + เวลา ใช้แทนการ query `ai_calls`
- log เป็น UTF-16 (Tee-Object ของ PowerShell 5.1) · อ่านด้วย `iconv -f UTF-16 -t UTF-8 .local/rehearsal-api.log` · บรรทัด `NativeCommandError` ตอนเริ่มเป็นแค่ PowerShell ห่อ stderr ไม่ใช่ error จริง
- PowerShell ตัดบรรทัด log ตามความกว้างจอ · ต่อบรรทัดก่อน parse JSON (record ขึ้นต้นด้วย `{"severity"` หรือ `INFO:`)
