# Feature: ห้องติว · ต่อกับ API ผ่าน HTTP (S3 · P4-lite)

| | |
|---|---|
| Area | tutor |
| Requirements | TM-20, TM-13, TM-06, TM-21 · วัดผลภายหลัง: NFR-P1 |
| Owner | May |
| Reviewer | Junior |
| Status | approved by May 2026-10-21 (owner) · รอ Junior review ใน PR (OQ 5–7) |
| Related system spec | api.md v1.3 "Conventions", "ห้องติว", "SSE events", "รอตัดสิน" ข้อ 1–3 · ai-orchestration.md §2.2.2, §2.2.8 · `chat-room-ui.md` · `chat-streaming.md` · `docs/design/use-cases.md` UC-03 E1, E2 |

## 1. Context

ตอนนี้หน้าห้องติว (`/preps/[id]/room`) ใช้ข้อมูลห้องจาก fixture และ fake transport ที่เล่นคำตอบจากไฟล์ PR #38 ของ Junior เพิ่ม stub ของ 4 endpoint ห้องติวที่คืนข้อมูลตาม contract แล้ว (`X-Stub: true`) และ PR #41 generate type ไว้ใน `lib/api-schema.ts` feature นี้ทำให้หน้าห้อง**หา session, โหลดข้อมูลห้อง และส่งข้อความผ่าน HTTP จริง** เมื่อ Junior เปลี่ยน stub เป็น logic จริงใน P4-lite หน้าเว็บไม่ต้องแก้

## 2. Behavior

**ที่อยู่ API**

- base URL อ่านจาก `NEXT_PUBLIC_API_URL` (มีใน `.env.example` แล้ว) · อ่านตอนเรียก ไม่ใช่ตอน load module (แบบเดียวกับ `lib/supabase.ts`) เพื่อให้ `next build` ผ่านโดยไม่มี env

**เปิดห้อง (TM-13 · api.md "รอตัดสิน" ข้อ 2 · UC-03 E1)**

`[id]` ใน URL คือ id ของการเตรียมสอบ (exam prep)

1. เรียก `GET /exam-preps/{id}/sessions/active`
2. ได้ `200 {session_id}` → เรียก `GET /sessions/{session_id}` ได้ `Room` → แสดงห้องด้วยข้อความเดิมทั้งหมด (กลับมาต่อจากจุดเดิม · ไม่มี progress card ใหม่)
3. ได้ `404` ที่ `error.code = "no_active_session"` → เรียก `POST /exam-preps/{id}/sessions` (SSE) · เมื่อได้ event แรก `session {session_id}` → เรียก `GET /sessions/{session_id}` แล้วแสดงห้องทันที · event ที่เหลือของ stream เดิม (`token` ข้อความเปิด, `done` ฯลฯ) ไหลเข้าห้องเหมือนคำตอบปกติ โดยไม่มี bubble user นำหน้า (May ตัดสิน 2026-10-21) · `progress_card` และ `problem` ข้ามไปก่อน (feature แยก · chat-streaming.md AC-7)
   - ChatRoom รับ stream เปิดห้องเป็น prop ที่ไม่บังคับ (`opening?: AsyncIterable<SSEEvent>`) และแสดงด้วยกฎเดียวกับ `chat-streaming.md` ทุกข้อ (สถานะกำลังตอบ, จุดสามจุด, ข้อความแจ้งผิดพลาด, abort เมื่อ unmount)
   - สมมติว่า `GET /sessions/{id}` ที่เรียกระหว่าง stream ยังไม่มีข้อความเปิด (backend บันทึกข้อความ tutor ตอนจบ turn · ai-orchestration §2.2.6) ถ้า backend บันทึกก่อน ข้อความเปิดจะซ้ำ · ให้ Junior ยืนยัน (Open question 5)
4. ระหว่างข้อ 1–3 (ก่อนแสดงห้อง) แสดง "กำลังเปิดห้องติว…" และยังไม่มี composer
5. **โหลดห้องไม่สำเร็จ** (ก่อนแสดงห้อง · May ตัดสิน 2026-10-21):
   - `404` ที่ `error.code` ไม่ใช่ `no_active_session` (เช่น ไม่พบการเตรียมสอบ) → "ไม่พบการเตรียมสอบนี้" + ลิงก์ "กลับหน้าหลัก" (`/`)
   - กรณีอื่น (เน็ตหลุด, HTTP อื่นที่ไม่ใช่ 2xx, stream เปิดห้องจบหรือ `error` ก่อนได้ `session`) → "เปิดห้องติวไม่สำเร็จ" + ปุ่ม "ลองใหม่" (เริ่มข้อ 1 ใหม่) + ลิงก์ "กลับหน้าหลัก"
   - ข้อความแจ้งใช้ `role="alert"` · ไม่แสดง `message` จาก server (เหมือน chat-streaming.md)
   - ถ้า stream เปิดห้องผิดพลาด**หลัง**แสดงห้องแล้ว ใช้ข้อความแจ้งเดียวของ chat-streaming.md ("ส่งไม่สำเร็จ ลองส่งอีกทีนะ")

**ส่งข้อความ (TM-20)**

- HTTP transport เป็น `SendMessage` ตัวใหม่ (type เดิมใน `components/chat/types.ts`) ที่เรียก `postSSE` ใน `lib/sse.ts` ไป `POST /sessions/{session_id}/messages` ด้วย body `{text}` แล้ว yield event ตามที่ได้
- ChatRoom ไม่ต้องแก้: การแสดง token, buddy, done, error, สถานะกำลังตอบ, ข้อความแจ้งผิดพลาด และ scroll เป็นไปตาม `chat-streaming.md` ทุกข้อ
- HTTP ไม่ใช่ 2xx หรือเน็ตหลุด → `postSSE` throw → ChatRoom แสดง "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" (chat-streaming.md AC-14)
- ส่ง `signal` ต่อให้ `fetch` เพื่อให้ออกจากห้องแล้ว request ถูกยกเลิก

**รูป (TM-06)**: ยังส่งไม่ได้ เพราะไม่มี `POST /sessions/{id}/uploads` และ api.md "รอตัดสิน" ข้อ 1 (ส่ง text พร้อมรูป) ยังรอ Jam · ปุ่ม "แนบรูป" ยังอยู่และกดได้ (`chat-room-ui.md` AC-11 ยังผ่าน) แต่เมื่อเลือกไฟล์รูป Composer ไม่แนบ และแสดงใต้ช่องพิมพ์ว่า "ตอนนี้ยังส่งรูปไม่ได้ พิมพ์คำตอบมาก่อนนะ" แบบเดียวกับ "แนบได้เฉพาะรูป" (May ตัดสิน 2026-10-21) · Composer รับ prop ที่ไม่บังคับ `imagesEnabled` (ค่าเริ่มต้น `true` เพื่อให้ test เดิมผ่าน) และหน้าห้องที่ใช้ API ส่ง `false` · ชั่วคราวจนกว่าจะมี `/uploads`

**ลบโหมด demo** (May ตัดสิน 2026-10-21): หน้าห้องใช้ API อย่างเดียว · ลบ `DemoRoom.tsx` และการอ่าน fixture ใน `page.tsx` · ตอน dev ให้เปิด API stub ในเครื่อง (ข้อมูลเดียวกับ fixture) · `lib/fakeTransport.ts` และ fixture ยังเก็บไว้ใช้ใน test

**Type (apps/web/CLAUDE.md: ห้ามเขียน request type เอง)**

- `ChatMessage` = `components["schemas"]["Message"]` (ได้ field `card` เพิ่ม) · `RoomData` = `components["schemas"]["Room"]` (ได้ `session_id` เพิ่ม) · `InputLimits` = `components["schemas"]["Limits"]`
- body ของการส่งข้อความใช้ `components["schemas"]["SendMessageRequest"]`
- ChatRoom สร้างข้อความในเครื่อง (`local-n`) ต้องใส่ `card: null` ให้ครบ type

**ขีดจำกัด (TM-21)**: ใช้ `limits` จาก `Room` ที่ได้จาก API แทน fixture · Composer ไม่ต้องแก้

**Auth**: ยังไม่ส่ง `Authorization` เพราะยังไม่มีหน้า login และ stub ไม่ตรวจ token (Out of scope)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `[id]` ใน URL (uuid ของ exam prep) · `NEXT_PUBLIC_API_URL` | `/preps/7a1e…/room` · `http://localhost:8000` |
| Input (API) | `ActiveSession`, `Room`, SSE events ตาม api.md | `{"session_id":"5f0c2a8e-…"}` |
| Output | หน้าห้องที่แสดง `Room` และ stream คำตอบ · request `POST /sessions/{id}/messages` body `{text}` | `{"text":"(x-7)(x+7)"}` |

## 4. Acceptance criteria

ทุกข้อ mock `fetch` ด้วย response ที่บันทึกไว้ (ไม่เรียก API จริง) · ใช้ fixture `tests/fixtures/room/session-s15.json` และ `tests/fixtures/sse/*.txt`

**เปิดห้อง (TM-13)**

- **AC-1 (TM-13)** Given `GET /exam-preps/P/sessions/active` ตอบ `200 {session_id:"S"}` และ `GET /sessions/S` ตอบ Room ที่มี 3 ข้อความ When เปิด `/preps/P/room` Then เห็นทั้ง 3 ข้อความ, หัวห้องแสดง `prep_name` และ "สอบใน N วัน" ตาม Room และไม่มี request `POST /exam-preps/P/sessions`
- **AC-2 (TM-13)** Given active ตอบ `404 {error:{code:"no_active_session"}}`, `POST /exam-preps/P/sessions` ตอบ SSE ของ `session_start.txt` (`session {session_id:"S"}` → `progress_card` → `token tutor` ข้อความเปิด → `problem` → `done`) และ `GET /sessions/S` ตอบ Room ที่ไม่มีข้อความ When เปิดห้อง Then มี `POST /exam-preps/P/sessions` 1 ครั้ง, `GET /sessions/S` 1 ครั้ง, เห็นหัวห้องตาม Room และมี bubble tutor 1 อันที่มีข้อความเปิด โดยไม่มี bubble user
- **AC-2b (TM-13)** Given stream เปิดห้องหยุดหลัง `session` และยังไม่มี token Then เห็นห้องพร้อมตัวบอกกำลังพิมพ์ และปุ่มส่งกดไม่ได้ · When ได้ token และ `done` Then ตัวบอกหายไปและปุ่มส่งกดได้ (เมื่อพิมพ์ข้อความ)
- **AC-2c (TM-20)** Given ห้องที่เปิดจาก session ใหม่ "S" When ส่ง "ใช่ๆ" Then request ไปที่ `POST /sessions/S/messages`
- **AC-3 (TM-13)** Given request ยังไม่ตอบ When เปิดห้อง Then เห็น "กำลังเปิดห้องติว…" และยังไม่มี composer
- **AC-3b (TM-13)** Given active ตอบ `404 {error:{code:"prep_not_found"}}` When เปิดห้อง Then เห็น `role="alert"` "ไม่พบการเตรียมสอบนี้", ลิงก์ "กลับหน้าหลัก" ไป `/`, ไม่มีปุ่ม "ลองใหม่" และไม่มี `POST /exam-preps/P/sessions`
- **AC-3c (TM-13)** Given active ตอบ `500` When เปิดห้อง Then เห็น "เปิดห้องติวไม่สำเร็จ", ปุ่ม "ลองใหม่" และลิงก์ "กลับหน้าหลัก" · When active ตอบ `200 {session_id:"S"}` ในครั้งถัดไปแล้วกด "ลองใหม่" Then เห็นห้องของ S
- **AC-3d (TM-13)** Given `fetch` reject ตอนเรียก active Then เหมือน AC-3c (เห็น "เปิดห้องติวไม่สำเร็จ")
- **AC-3e (TM-13)** Given `POST /exam-preps/P/sessions` ตอบ `error` ก่อน `session` Then เห็น "เปิดห้องติวไม่สำเร็จ" และไม่มี `GET /sessions/...`
- **AC-3f (TM-20)** Given stream เปิดห้องส่ง `session` และ token บางส่วนแล้วจบโดยไม่มี `done` Then ห้องยังแสดง bubble tutor ที่มี token นั้น และเห็น "ส่งไม่สำเร็จ ลองส่งอีกทีนะ"
- **AC-4 (TM-21)** Given Room ที่ `limits.max_message_chars = 50` When พิมพ์ 51 ตัวอักษร Then ปุ่มส่งกดไม่ได้และเห็น "ข้อความยาวเกิน 50 ตัวอักษร" (ขีดจำกัดมาจาก API ไม่ใช่ fixture)

**ส่งข้อความ (TM-20)**

- **AC-5 (TM-20)** Given ห้องที่โหลดจาก session "S" When ส่ง "(x-7)(x+7)" Then มี request `POST {API_URL}/sessions/S/messages` 1 ครั้ง, header `Content-Type: application/json` และ `Accept: text/event-stream`, body `{"text":"(x-7)(x+7)"}`
- **AC-6 (TM-20)** Given `POST /sessions/S/messages` ตอบ SSE ของ `tutor_reply.txt` When ส่งข้อความ Then เห็น bubble tutor, buddy, tutor ตามลำดับ (แบบเดียวกับ chat-streaming.md AC-4)
- **AC-7 (TM-20)** Given `POST /sessions/S/messages` ตอบ `500` When ส่งข้อความ Then bubble user ยังอยู่ และเห็น "ส่งไม่สำเร็จ ลองส่งอีกทีนะ"
- **AC-8 (TM-20)** Given `fetch` reject (เน็ตหลุด) When ส่งข้อความ Then เหมือน AC-7
- **AC-9 (TM-20)** Given stream ยังไม่จบ (ทั้งคำตอบและ stream เปิดห้อง) When ออกจากห้อง (unmount) Then `signal` ที่ส่งให้ `fetch` ถูก abort

**รูป (TM-06)**

- **AC-12 (TM-06)** Given หน้าห้องที่ใช้ API When เลือกไฟล์รูป "วิธีทำ.jpg" ด้วยปุ่ม "แนบรูป" Then ไม่มีรูปแนบ, เห็น "ตอนนี้ยังส่งรูปไม่ได้ พิมพ์คำตอบมาก่อนนะ" และไม่มี request ไป API
- **AC-13 (TM-06)** Given Composer ที่ไม่ได้ส่ง `imagesEnabled` When แนบรูป Then แนบได้ตามเดิม (test เดิมของ `chat-room-ui.md` ผ่าน)

**HTTP transport (unit)**

- **AC-10 (TM-20)** Given `API_URL = "http://api.test"` When transport ส่ง `{text:"ใช่ๆ", image:null}` ไป session "S" Then เรียก `fetch("http://api.test/sessions/S/messages", …)` และ yield event ตามลำดับใน SSE ที่ได้
- **AC-11 (TM-20)** Given `NEXT_PUBLIC_API_URL` ไม่ได้ตั้ง When `next build` Then build ผ่าน (อ่าน env ตอนเรียก)

**AC-boundary:** ไม่มี threshold ของ learning model · ขีดจำกัดข้อความใช้ AC-4 + test boundary เดิมของ Composer (`chat-room-ui.md` AC-boundary-text)

**AC-tenant (SA-06):** ไม่เกี่ยวโดยตรง · หน้าเว็บไม่อ่าน database เอง การแยก tenant ของ `tutor_sessions` และ `messages` ทดสอบที่ API (RLS)

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี endpoint หรือ event ใหม่ · ใช้ที่มีใน api.md แล้ว: `GET /exam-preps/{id}/sessions/active`, `POST /exam-preps/{id}/sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/messages` และ event `session`, `token`, `buddy`, `done`, `error`

ต้องมีวิธีให้ browser ที่ `localhost:3000` (และ Vercel) เรียก API ที่ `localhost:8000` (และ Cloud Run) ได้ · ตอนนี้ API ไม่มี CORS · ดู Open question 5

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/httpTransport.test.ts` | unit (mock `fetch`) | AC-10, AC-11 |
| `tests/chat/RoomPageHttp.test.tsx` (ไฟล์ใหม่) | integration (mock `fetch`) | AC-1 ถึง AC-9, AC-2b, AC-2c, AC-3b ถึง AC-3f, AC-12 |
| `tests/chat/Composer.test.tsx` (เพิ่ม test) | unit | AC-13 |
| test เดิมของ ChatRoom, Composer, MessageList, fakeTransport | — | ยังต้องผ่านโดยไม่แก้เนื้อ test |

**test เดิมที่ต้องเลิกใช้ (ต้องให้ May อนุมัติ เพราะ review แล้ว):** `RoomPage.test.tsx` describe "Room page (S3, fake transport)" (chat-streaming.md AC-21) render หน้าที่ใช้ fixture + fake transport ซึ่งถูกลบตามที่ May ตัดสิน · แทนด้วย AC-6 ใน `RoomPageHttp.test.tsx` · describe "ChatRoom (S2, fixture data)" ในไฟล์เดียวกันไม่แก้

fixture ใหม่: `tests/fixtures/sse/session_start.txt` (คัดลอกจาก `apps/api/app/stubs/session_start.sse` เพื่อให้ตรงกับ stub)

## 9. Out of scope

- ส่งรูปจริง (`POST /sessions/{id}/uploads` + Storage) · รอ stub และ api.md "รอตัดสิน" ข้อ 1
- Auth header และหน้า login
- แสดง `progress_card`, `problem`, `ocr_preview`, `verdict`, `session_end` (feature แยก)
- `done.message_ids` และ `attachment_name` (api.md v1.3) · API ยังเป็น v1.2 · ทำเมื่อ Junior อัปเดตแล้วรัน `pnpm gen:api`
- `\$` ใน MessageText (api.md v1.3 Conventions) · feature แยก
- วัด TTFT และต้นทุนบน staging (NFR-P1, NFR-P2) · ทำกับ Junior ใน report P4-lite

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-21)

1. ข้อความเปิดของ session ใหม่: แสดงห้องเมื่อได้ `session` แล้วข้อความเปิดไหลเข้าห้อง (AC-2, AC-2b)
2. โหลดห้องไม่สำเร็จ: "เปิดห้องติวไม่สำเร็จ" + "ลองใหม่" + "กลับหน้าหลัก" · ไม่พบการเตรียมสอบ: ข้อความ + "กลับหน้าหลัก" (AC-3b ถึง AC-3e)
3. ปุ่มแนบรูป: กดได้ แต่แจ้งว่ายังส่งรูปไม่ได้ (AC-12)
4. โหมด demo: ลบทิ้ง หน้าห้องใช้ API อย่างเดียว

ให้ Junior ตอบ (reviewer):

5. **ข้อความเปิดซ้ำไหม (AC-2):** `GET /sessions/{id}` ที่เรียกทันทีหลัง event `session` จะยังไม่มีข้อความเปิดใช่ไหม (บันทึกตอนจบ stream)
6. **CORS:** (ก) เพิ่ม CORS ใน FastAPI (`allow_origins` จาก env) หรือ (ข) หน้าเว็บเรียกผ่าน Next.js rewrites (`/api/*` → API) ไม่ต้องแก้ backend · ต้องเช็กว่า rewrite ไม่ buffer SSE · **ระหว่างนี้ test ทั้งหมด mock `fetch` จึงไม่ติด แต่ขั้นลองจริงในเครื่อง (ขั้น 6 ของ worklog) ต้องมีทางใดทางหนึ่ง**
7. **code ของ 404 ไม่พบการเตรียมสอบ:** api.md ยังไม่มีรายการ `error.code` (api.md "รอตัดสิน" ข้อ 3) · spec นี้ถือว่า 404 ทุก code ที่ไม่ใช่ `no_active_session` = ไม่พบ · test ใช้ `prep_not_found` เป็นตัวอย่าง

## 11. Spec changes needed

- **api.md** (ไฟล์ร่วม) Conventions: ระบุวิธีเรียก API จาก browser (CORS หรือ proxy) ตามคำตอบ Open question 6
- **`chat-room-ui.md`** §3: `ChatMessage` / `RoomData` เปลี่ยนเป็น type ที่ generate จาก API (เพิ่ม `card`, `session_id`)
- **`chat-streaming.md`** AC-21 และ §2 "หน้า room ใช้ fake transport": แทนด้วย spec นี้ (หน้า room ใช้ API)
