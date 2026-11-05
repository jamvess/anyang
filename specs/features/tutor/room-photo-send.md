# Feature: ห้องติว · ส่งรูปวิธีทำผ่าน API จนถึงผลตรวจ

| | |
|---|---|
| Area | tutor |
| Requirements | TM-06 · TM-21 · AM-01 · AM-02 |
| Owner | Jam (item of May · ช่วง solo 2026-11-05) |
| Reviewer | Jam · May ดูย้อนหลัง (หน้าจอ) · Junior ดูย้อนหลัง (`SendMessageRequest`) |
| Status | approved by Jam 2026-11-05 (OQ 1, 2 ตามข้อเสนอ · OQ 3–5 ให้ May ดูย้อนหลัง) |
| Related system spec | api.md "ห้องติว" (`/uploads`, `/messages`, `/ocr/confirm`, "รอตัดสิน (PR #35)" ข้อ 1, v1.7) · ai-orchestration.md §2.2.5 · `room-http.md` · `ocr-confirm-card.md` · `chat-room-ui.md` · `chat-streaming.md` |

## 1. Context

ห้องติวที่ต่อ API ยังส่งรูปไม่ได้: `TutorRoom` ปิดด้วย `imagesEnabled={false}` เพราะตอนนั้นยังไม่มี `/uploads` · ตอนนี้ stub ของ `/uploads`, `/messages` แบบรูป และ `/ocr/confirm` มีครบแล้ว (api.md v1.7 · PR #102) และการ์ดยืนยันลายมือทำเสร็จแล้ว (`ocr-confirm-card.md`) แต่ยังไม่ได้ต่อกัน · feature นี้ต่อเส้นทางนี้ให้ครบ เพื่อให้ลองส่งรูปจนเห็นผลตรวจได้ก่อนมี Storage จริง

## 2. Behavior

**ส่งรูป (`createHttpTransport`)** เมื่อ `payload.image` มีค่า ทำตามลำดับ โดยส่ง `signal` เดียวกันทุก request:

1. `POST /sessions/{id}/uploads` body `{kind: "image", content_type: image.type, file_name: image.name, size_bytes: image.size}`
2. ส่งไฟล์เข้า `upload_url` ด้วย `PUT` · body คือไฟล์ · header `Content-Type: image.type` · ไม่ส่ง `Authorization` เพราะเป็น signed URL
   - **ยกเว้น** response ของขั้น 1 มี header `X-Stub: true` → ข้ามขั้นนี้ เพราะ URL ของ stub ใช้จริงไม่ได้ (ตัดสินแล้ว · Open question 2)
3. `POST /sessions/{id}/messages` body `{image_path: path}` · ถ้ามีข้อความกำกับ เพิ่ม `text` · ไม่มีข้อความก็ไม่ส่ง key `text`

ขั้นไหนตอบไม่ใช่ 2xx → หยุดทันที ไม่ทำขั้นถัดไป และ throw · ห้องจัดการเหมือนส่งข้อความไม่สำเร็จตาม `chat-streaming.md`: bubble ของผู้ใช้ยังอยู่ · เห็น "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" ข้อความเดียวทุกกรณี (May เลือก · chat-streaming.md) · ช่องพิมพ์กลับมาใช้ได้ · รูปต้องเลือกใหม่ เพราะ Composer ล้างรูปตอนกดส่ง (`chat-room-ui.md` AC-16)

**ข้อความไม่มีรูป:** ทำงานเหมือนเดิมทุกอย่าง ไม่เรียก `/uploads`

**หน้าห้อง (`TutorRoom`)**

- เลิกส่ง `imagesEnabled={false}` · เลือกรูปแล้วแนบได้ตาม `chat-room-ui.md` AC-15 · ตรวจชนิดและขนาดตามเดิม ขีดจำกัดมาจาก `Room.limits` (TM-21)
- ส่ง `confirmOcr={createHttpOcrConfirm(sessionId)}` ให้ `ChatRoom` · ไม่งั้นกด "ถูกแล้ว ตรวจเลย" แล้วจะไม่มีอะไรเกิดขึ้น
- การ์ด ผลตรวจ และ "ถ่ายใหม่" ใช้ของเดิมตาม `ocr-confirm-card.md` และ `verdict-mark.md` · รูปใหม่จาก "ถ่ายใหม่" เดินตามขั้น 1–3 อีกรอบ

**API: ส่งข้อความพร้อมรูปได้** (ตัดสินแล้ว · Jam 2026-10-21 · PR #45 · api.md บอกไว้แล้ว แต่โค้ดยังไม่ได้แก้)

- `SendMessageRequest` รับ `text`, `image_path` หรือทั้งคู่ · ต้องมีอย่างน้อยหนึ่งค่า
- `text` ว่างหรือมีแต่ช่องว่าง → `422` เสมอ แม้มีรูป (Composer ตัดเป็น null ให้แล้ว)
- ยาวเกิน `guards.max_message_chars` → `422 message_too_long` แม้มีรูป
- มี `image_path` → stub ส่ง `ocr_preview` เหมือนรูปอย่างเดียว · `text` เป็นคำบรรยาย ไม่เข้า `extract_answer` และ checker (ยังไม่มีผลใน stub)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (transport) | `SendPayload` = `{text: string \| null, image: File \| null}` | `{text: "ข้อ 2 ครับ", image: File("วิธีทำ.jpg", image/jpeg, 900000)}` |
| Output (request 1) | `UploadRequest` | `{"kind": "image", "content_type": "image/jpeg", "file_name": "วิธีทำ.jpg", "size_bytes": 900000}` |
| Output (request 3) | `SendMessageRequest` | `{"text": "ข้อ 2 ครับ", "image_path": "t/sessions/s1/ab.jpeg"}` |
| Output (ห้อง) | SSE ของ `/messages` | `ocr_preview` → การ์ด · ยืนยันแล้ว `verdict` → `token` → `done` |

## 4. Acceptance criteria

**API: ข้อความพร้อมรูป**

- **AC-1 (TM-06)** Given body `{text: "ไม่แน่ใจบรรทัด 3", image_path: "t/sessions/s1/a.jpg"}` When `POST /sessions/{id}/messages` Then `200` SSE ที่มี `ocr_preview` และจบด้วย `done`
- **AC-2 (TM-06)** Given `{image_path}` อย่างเดียว Then ได้ `ocr_preview` · Given `{text}` อย่างเดียว Then ได้คำตอบจาก gateway เหมือนเดิม (ไม่มี `ocr_preview`)
- **AC-3 (TM-06)** Given `{}` หรือ `{text: null, image_path: null}` Then `422` envelope
- **AC-4 (TM-06)** Given `{text: "   ", image_path}` Then `422` envelope
- **AC-boundary-caption (TM-21)** Given `image_path` และ `text` ยาว `max_message_chars` Then `200` · ยาว `max_message_chars + 1` Then `422 message_too_long` · ค่าอ่านจาก `config/ai.yaml`

**Transport**

- **AC-5 (TM-06)** Given รูป "วิธีทำ.jpg" (`image/jpeg`, 900000 bytes) ไม่มีข้อความ และ `/uploads` ไม่มี `X-Stub` When ส่ง Then fetch ตามลำดับ `POST /uploads` → `PUT upload_url` → `POST /messages` · body ของ `/uploads` ตรงตาม §3 · yield event ของ `/messages` ตามลำดับ
- **AC-6 (TM-06)** Given เดียวกัน Then `PUT` ได้ไฟล์นั้นเป็น body · `Content-Type: image/jpeg` · ไม่มี header `Authorization`
- **AC-7 (TM-06)** Given เดียวกัน Then body ของ `/messages` คือ `{image_path: path}` พอดี ไม่มี key `text`
- **AC-8 (TM-06)** Given รูป และข้อความ "ข้อ 2 ครับ" Then body ของ `/messages` คือ `{text: "ข้อ 2 ครับ", image_path: path}`
- **AC-9 (TM-06)** Given `/uploads` ตอบ header `X-Stub: true` Then ไม่มี `PUT` และ `/messages` ยังถูกเรียกด้วย `path` ที่ได้
- **AC-10 (TM-06)** Given ข้อความไม่มีรูป Then ไม่เรียก `/uploads` และ body เหมือนเดิม (`room-http.md` เดิมผ่านทั้งหมด)
- **AC-11 (TM-21)** Given `/uploads` ตอบ `422` (`unsupported_type` หรือ `file_too_large`) หรือ `429` Then throw · ไม่มี `PUT` และไม่มี `/messages`
- **AC-12 (TM-06)** Given `PUT` ตอบ `403` Then throw · ไม่มี `/messages`
- **AC-13 (TM-06)** Given ส่งรูป Then ทุก request (`/uploads`, `PUT`, `/messages`) ได้ `signal` ตัวเดียวกัน

**หน้าห้องที่ต่อ API**

- **AC-14 (TM-06)** Given ห้องเปิดแล้ว When เลือกรูป Then เห็นชื่อไฟล์และปุ่ม "เอารูปออก" · ไม่เห็น "ตอนนี้ยังส่งรูปไม่ได้" · ยังไม่มี request ใหม่
- **AC-15 (AM-02)** Given แนบรูปแล้ว When กดส่ง Then เห็น bubble ของผู้ใช้ที่มีชื่อไฟล์ แล้วเห็นการ์ด "อ่านได้แบบนี้ ถูกไหม" ทุกบรรทัดของ `ocr_preview` (AM-01: render เป็นสมการ)
- **AC-16 (AM-02)** Given การ์ด When กด "ถูกแล้ว ตรวจเลย" Then `POST /sessions/{id}/ocr/confirm` ได้ `{lines}` ตามลำดับ · เห็นผลตรวจและข้อความของติวเตอร์ · การ์ดล็อก
- **AC-17 (TM-06)** Given `/uploads` ตอบ `422` When กดส่ง Then bubble ของผู้ใช้ยังอยู่ · เห็น "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" · ช่องพิมพ์ใช้ได้ · ไม่มีการ์ด · ไม่มี request ไป `/messages`
- **AC-18 (AM-02)** Given การ์ดที่ยังไม่ยืนยัน When กด "ถ่ายใหม่" แล้วเลือกรูปใหม่และส่ง Then มี `/uploads` และ `/messages` อีกรอบ · เห็นการ์ดใบใหม่ · ใบเก่าล็อก
- **AC-19 (TM-06)** Given เส้นทางทั้งหมดนี้ Then ไม่มีปุ่มตัวเลือกคำตอบในห้อง

**AC-tenant:** ไม่มี · feature นี้ไม่อ่านหรือเขียนฐานข้อมูล (stub) · path ที่ขึ้นต้นด้วย tenant อยู่ใน api.md v1.7 และ test ของ `/uploads` แล้ว

## 5. Data changes

ไม่มี

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /sessions/{id}/messages` | รับ `text` พร้อม `image_path` ได้ · ตรงกับ api.md อยู่แล้ว · โค้ดเดิมปฏิเสธ | ไม่เปลี่ยน |

ไม่เพิ่ม endpoint หรือ event

## 7. AI calls

ไม่มี · รูปยังตอบด้วย stub (`image_reply.sse`, `ocr_confirm.sse`)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `apps/api/tests/unit/test_room_photo_send.py` | unit (API) | AC-1 ถึง AC-4, AC-boundary-caption |
| `apps/web/tests/httpTransport.test.ts` (เพิ่มท้ายไฟล์) | unit | AC-5 ถึง AC-13 |
| `apps/web/tests/chat/RoomPagePhoto.test.tsx` | integration (TutorRoom + fetch ปลอม) | AC-14 ถึง AC-19 |

**test เดิมที่ต้องแก้ (Jam อนุญาตแล้ว 2026-11-05 · Open question 1):**

- `apps/api/tests/unit/test_room_api_contract.py` · `test_apimd_room_send_message_needs_exactly_one_of_text_or_image` · เอาเคสที่ส่งทั้งคู่ออก
- `apps/web/tests/chat/RoomPageHttp.test.tsx` · `TM06 picking a photo does not attach it…` · ลบ เพราะบังคับพฤติกรรมชั่วคราวที่ `room-http.md` ระบุว่าใช้จนกว่าจะมี `/uploads`

## 9. Out of scope

- `/uploads` ตัวจริงที่ต่อ Supabase Storage (bucket + policy · Junior · api.md รอตัดสิน v1.7 ข้อ 2)
- `extract_answer` และ checker จริง · ผลตรวจยังเป็น stub
- ปุ่มไมค์ (`voiceEnabled`) · ทำแยก
- แสดงรูปจริงในแชทเก่า · แสดงแค่ชื่อไฟล์ตาม `chat-room-ui.md` AC-6
- token ใน request · หน้า login ยังไม่มี (May)

## 10. Open questions

1. ~~**แก้ test ที่ review แล้ว 2 ตัว (§8)**~~ **ตัดสินแล้ว** (Jam 2026-11-05): อนุญาตทั้งคู่ · ตัวแรกขัดกับการตัดสิน PR #45 และมี comment ให้แก้พร้อม spec · ตัวที่สองบังคับพฤติกรรมชั่วคราว
2. ~~**`PUT` กับ stub**~~ **ตัดสินแล้ว** (Jam 2026-11-05): เลือก (ข) · `upload_url` ของ stub คือ `https://stub.invalid/...` · (ก) เพิ่ม route `PUT` ปลอมใน API เป็น route สาธารณะบน staging และกระทบ test ที่ walk ทุก route ด้าน auth · (ข) เว็บข้าม `PUT` เมื่อเห็น `X-Stub: true` ซึ่ง CORS เปิดให้อ่านแล้ว · ต้องลบเงื่อนไขนี้ตอนมี Storage จริง และ `PUT` จริงจะยังไม่เคยวิ่งในเบราว์เซอร์จนกว่าจะถึงตอนนั้น
3. **ไฟล์รูปที่ API ไม่รับ:** Composer รับทุก `image/*` แต่ `/uploads` รับแค่ jpeg, png, webp, heic · เช่น `image/gif` จะเห็น "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" ซึ่งไม่บอกสาเหตุ · ข้อเสนอคือยังใช้ข้อความเดียวตามที่ May เลือก แล้วให้ May ตัดสินว่าจะเปลี่ยน `accept` ของ input หรือไม่
4. **รูปหายเมื่อส่งไม่สำเร็จ:** Composer ล้างรูปตอนกดส่ง · ผู้ใช้ต้องเลือกใหม่ · ข้อความก็เป็นแบบนี้อยู่แล้ว · ไม่เปลี่ยนใน feature นี้ · ให้ May ดู
5. **prop `imagesEnabled`:** ไม่มีหน้าไหนส่ง `false` แล้ว แต่ test ของ Composer ยังใช้ · ข้อเสนอคือคงไว้ใน PR นี้ เพื่อไม่แก้ test เพิ่ม

## 11. Spec changes needed

- `room-http.md` §2 "รูป (TM-06)" และ §9: ข้อความเก่าบอกว่ารอ `/uploads` และรอ Jam · แก้ให้ชี้มาที่ spec นี้ (ทำในขั้น 1)
- `api.md`: ไม่ต้องแก้ · แถว `POST /sessions/{id}/messages` ตรงอยู่แล้ว
