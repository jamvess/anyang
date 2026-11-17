# Feature: ปุ่มจบการติว + สรุปในแชท (หน้าเว็บ · demo ขั้น 9)

| | |
|---|---|
| Area | tutor |
| Requirements | PM-05, TM-13, TM-06, NFR-A1 |
| Owner | May |
| Reviewer | May (spec + test) · Jam ดูย้อนหลัง (เจ้าของ `session-end-db.md`) |
| Status | approved 2026-11-17 (May ok spec · open questions ใช้ข้อเสนอทั้ง 3 ข้อ) |
| Related system spec | api.md v1.19 "`POST /sessions/{id}/end`" + SSE `session_end` · `session-end-db.md` (#136 · API ทำแล้ว · §9 "หน้าเว็บ: ปุ่มจบ + การ์ดสรุป (May)") · `room-http.md` (เปิดห้อง · `sessions/active`) · `chat-streaming.md` (bubble · ข้อความแจ้งผิดพลาด) · `use-cases.md` UC-03 ขั้น 11–12 · wireframe S26 · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 9 · goal อาจารย์ข้อ 4 (17 พ.ย.) |

## 1. Context

API จบ session ได้จริงแล้ว (#136): ปิด session · นับคำตอบ · `session_summary` เขียนสรุป 1–2 บรรทัด · บันทึกเป็นข้อความ tutor · แต่หน้าเว็บไม่มีทางเรียก `POST /sessions/{id}/end` ผู้ใช้จึงจบการติวไม่ได้และไม่เห็นสรุป (PM-05) · feature นี้เพิ่มปุ่ม "จบการติว" บนหัวห้อง แสดงสรุปเป็น bubble ของ tutor แล้วล็อกห้องพร้อมทางไปต่อ (กลับหน้าหลัก / ติวรอบใหม่) · wireframe S26 จบด้วยการพิมพ์ "พอแล้ว" ในแชท ซึ่งต้องมี `route_intent` (ยังไม่มี) จึงใช้ปุ่มไปก่อน (May 17 พ.ย. · §9)

## 2. Behavior

### 2.1 ปุ่ม "จบการติว"

1. หัวห้องมีปุ่ม "จบการติว" (`<button>`) อยู่ก่อนลิงก์ "ออกจากห้องติว" **เฉพาะเมื่อ `ChatRoom` ได้ `endSession`** (แบบเดียวกับไมค์ที่ขึ้นเฉพาะเมื่อมี `transcribe` · voice-input.md) · `TutorRoom` ส่ง `endSession` ของ session ที่เปิดอยู่เสมอ · test เดิมที่นับปุ่มของห้อง (ChatRoomVoice AC-17, Composer) ไม่ส่ง `endSession` จึงไม่เปลี่ยน · **ยกเว้น** `RoomPagePhoto.test.tsx` "no answer choice buttons in the whole room" (Jam · เปิดผ่าน `TutorRoom`) · เพิ่ม "จบการติว" ในรายการปุ่มที่อนุญาต (May 17 พ.ย. ตอน implement · บอก Jam)
2. ปุ่มนี้ไม่ใช่ตัวเลือกคำตอบ (TM-06 ห้ามปุ่ม choice ให้กดตอบ · การจบ session ไม่ใช่คำตอบ)
3. ปุ่มกดไม่ได้ (`disabled`) ขณะห้องกำลังรับคำตอบอยู่ (`busy` เดียวกับ Composer · รวมตอนเปิดห้องที่ stream คำทักอยู่ และตอนยืนยันลายมือ) และหลังจบแล้ว
4. กดแล้วจบทันที ไม่มีกล่องถามยืนยัน (May 17 พ.ย.: ทุกคำตอบบันทึกแล้ว · เริ่มรอบใหม่ได้ทันที)

### 2.2 ระหว่างจบ

1. กด → `endSession(signal)` = `POST /sessions/{id}/end` ไม่มี body (SSE · api.md v1.19) ผ่าน `apiSSE` (แนบ token · 401 → หน้า login แบบเดิม)
2. ระหว่างรอ: ห้องเป็น `busy` (Composer, canvas, ปุ่มจบกดไม่ได้) และแสดงตัวบอกกำลังพิมพ์ (•••) แบบเดิม (chat-streaming.md §2)
3. event `session_end {summary_lines}` → ต่อท้ายแชทด้วย **bubble ของ tutor 1 อัน** เนื้อหา = `summary_lines` ต่อด้วย `\n` (บรรทัดละบรรทัด · bubble รักษาการขึ้นบรรทัดอยู่แล้ว · render ผ่าน `MessageText` จึงรองรับ `$…$` แบบ bubble อื่น) · ตัวบอกกำลังพิมพ์หายเมื่อ bubble ขึ้น (PM-05 "ในรูปแบบ chat message สั้นๆ" · wireframe S26 · May 17 พ.ย.)
4. event `done` → ห้องเข้าสถานะ "จบแล้ว" (§2.3) · `done.message_ids` ไม่ใช้ใน feature นี้
5. event อื่นใน stream นี้ (`token`, `error`, ที่ไม่รู้จัก): `token` และ `error` ทำตามกฎเดิมของ `play()` (chat-streaming.md) · ที่ไม่รู้จักข้าม · API ไม่ส่ง event อื่นใน `/end` (api.md v1.19)

### 2.3 สถานะ "จบแล้ว"

1. Composer ทั้งหมดกดไม่ได้ (ช่องพิมพ์, ส่ง, แนบรูป, ไมค์ถ้ามี) · **canvas ท้ายแชทหายไป** (May 17 พ.ย. ตอน implement: canvas อยู่ท้ายแชทเสมอ · answer-canvas.md §2 B · ถ้ายังอยู่จะอยู่ใต้สรุป ขัดกับ AC-1 · ห้องที่จบแล้วไม่มีอะไรให้เขียน) · การ์ดยืนยันลายมือที่ยังรอ (`pending`) กดยืนยัน / ถ่ายใหม่ / แก้ไม่ได้ · ปุ่ม "จบการติว" กดไม่ได้
2. ใต้แชท (ตำแหน่งเดียวกับข้อความแจ้งผิดพลาด เหนือ Composer) มีบรรทัด `role="status"` "จบการติวรอบนี้แล้ว" พร้อมลิงก์ 2 อัน:
   - "กลับหน้าหลัก" → `/` (ข้อความเดิม `roomStrings.backHome`)
   - "ติวรอบใหม่" → เปิดห้องของ prep เดิมใหม่: `TutorRoom` โหลดใหม่ (`sessions/active` → `404 no_active_session` → `POST /exam-preps/{id}/sessions` → คำทัก + การ์ดความคืบหน้าใหม่ · room-http.md · session-end-db.md §2.5) · เป็นลิงก์ไป URL ของห้องเดิม (`/preps/{id}/room`) ที่กดแล้วโหลดห้องใหม่ในหน้าเดิม
3. ลิงก์ "ออกจากห้องติว" บนหัวห้องยังใช้ได้
4. สถานะนี้อยู่ในหน้าเว็บเท่านั้น · รีเฟรชหน้า = เปิดห้องตามกฎเดิม (session ใหม่ · แชทของ session ที่จบไม่ขึ้น · §9)

### 2.4 จบไม่สำเร็จ

1. HTTP `409` ก่อน SSE (`session_already_ended` · เช่น จบจากอีกแท็บไปแล้ว) → เข้าสถานะ "จบแล้ว" (§2.3) **โดยไม่มี bubble สรุป** (สรุปอยู่ใน session นั้นแล้ว · api.md v1.19)
2. ล้มแบบอื่น (HTTP อื่นที่ไม่ใช่ 2xx ยกเว้น 401, เน็ตหลุด, `error`, stream จบโดยไม่มี `done`) → แสดงข้อความแจ้งผิดพลาดเดิม "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" (`role="alert"` · chat-streaming.md) · ห้องกลับมาใช้ได้ตามเดิม (Composer, ปุ่มจบกดได้) · กดจบซ้ำได้ · ถ้า API ปิด session ไปแล้วแต่ stream ขาด การกดซ้ำได้ 409 → ข้อ 1
3. ถ้าได้ `session_end` แล้วแต่ stream จบโดยไม่มี `done` → bubble สรุปยังอยู่ แต่ทำตามข้อ 2 (session ปิดแล้วฝั่ง API · กดซ้ำได้ 409 → ข้อ 1)
4. ออกจากห้องระหว่างจบ (unmount) → ยกเลิก stream แบบเดียวกับการส่งข้อความ (`abort`)

### 2.5 Accessibility (NFR-A1)

1. ปุ่ม "จบการติว" และลิงก์ทั้ง 2 อันกดด้วย keyboard ได้ · มีชื่อภาษาไทยตามข้อความ
2. bubble สรุปอยู่ใน `role="log"` เดิมจึงถูกอ่านเหมือนข้อความอื่น · บรรทัด "จบการติวรอบนี้แล้ว" เป็น `role="status"`
3. หลังเข้าสถานะ "จบแล้ว" focus ย้ายไปลิงก์ "ติวรอบใหม่" (ปุ่มที่กดอยู่กดไม่ได้แล้ว · focus ไม่หายไปที่ body)

### 2.6 ข้อความ (`components/chat/strings.ts`)

| key | ข้อความ |
|---|---|
| `endSession` | จบการติว |
| `sessionEnded` | จบการติวรอบนี้แล้ว |
| `newSession` | ติวรอบใหม่ |
| `backHome` (มีแล้ว) | กลับหน้าหลัก |
| `sendFailed` (มีแล้ว) | ส่งไม่สำเร็จ ลองส่งอีกทีนะ |

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | กดปุ่ม "จบการติว" | |
| Request | `POST /sessions/{id}/end` ไม่มี body · `Authorization` จาก session (ถ้ามี) | |
| Response | SSE `session_end {summary_lines: string[1..2]}` → `done {message_ids}` · หรือ `409 session_already_ended` ก่อน SSE | `["วันนี้ทำลิมิต 3 ข้อ ถูก 2 ข้อ ตอนนี้อยู่ระดับกำลังดีแล้ว", "ครั้งหน้าลองลิมิตที่มีรากอีกสักข้อ"]` |
| Output (UI) | bubble tutor 1 อัน (บรรทัดต่อด้วย `\n`) · สถานะ "จบแล้ว" | |
| Prop ใหม่ | `ChatRoom.endSession?: (signal: AbortSignal) => AsyncIterable<SSEEvent>` · type `EndSession` ใน `types.ts` | |

## 4. Acceptance criteria

test ใช้ `endSession` ปลอมที่ส่ง event ตามที่กำหนด (component) และ `fetch` ปลอม (`TutorRoom` · แบบ `RoomPagePhoto.test.tsx`) · fixture `tests/fixtures/sse/session_end.txt` · ไม่มี AI จริง

- **AC-1 (PM-05)** Given ห้องที่มี `endSession` และไม่ busy When กด "จบการติว" และได้ `session_end {summary_lines: [L1, L2]}` → `done` Then แชทมี bubble ของ tutor ใหม่ 1 อันท้ายสุด เนื้อหา `L1\nL2` (ข้อความทั้งสองบรรทัดอยู่ใน bubble เดียว)
- **AC-2 (PM-05)** Given `summary_lines` มี 1 บรรทัด When จบ Then bubble มีบรรทัดเดียว
- **AC-3 (TM-13)** Given จบสำเร็จ Then ช่องพิมพ์, ปุ่มส่ง, แนบรูป และปุ่ม "จบการติว" กดไม่ได้ · มี `role="status"` "จบการติวรอบนี้แล้ว" · มีลิงก์ "กลับหน้าหลัก" (`href="/"`) และ "ติวรอบใหม่" · ลิงก์ "ออกจากห้องติว" ยังอยู่
- **AC-4 (TM-13)** Given มีการ์ดโจทย์ค้าง (canvas อยู่ท้ายแชท) When จบสำเร็จ Then ไม่มี canvas (ไม่มีพื้นที่ "เขียนวิธีทำตรงนี้" และปุ่ม "ส่งคำตอบ") · การ์ดโจทย์ยังอยู่ (แก้ 17 พ.ย. ตอน implement · เดิม: canvas อยู่แต่ส่งไม่ได้ · ขัดกับ AC-1)
- **AC-5 (TM-13)** Given การ์ดยืนยันลายมือรออยู่ (`pending`) When จบสำเร็จ Then ปุ่ม "ถูกแล้ว ตรวจเลย", "ถ่ายใหม่" และ "แก้บรรทัด n" ของการ์ดนั้นกดไม่ได้
- **AC-6** Given ห้องกำลัง stream คำตอบอยู่ (busy) Then ปุ่ม "จบการติว" กดไม่ได้ · When stream จบด้วย `done` Then กดได้
- **AC-7** Given กดจบแล้ว stream ยังไม่ส่ง event Then ปุ่มจบ, ช่องพิมพ์, ส่ง กดไม่ได้ และเห็นตัวบอกกำลังพิมพ์ ("กำลังพิมพ์") · When ได้ `session_end` Then ตัวบอกหาย bubble สรุปขึ้น
- **AC-8** Given `endSession` throw error ที่มี `status: 409` ก่อน event แรก When กดจบ Then เข้าสถานะ "จบแล้ว" ตาม AC-3 · ไม่มี bubble ใหม่ · ไม่มี `role="alert"`
- **AC-9** Given `endSession` throw error อื่น (เช่น `status: 503` หรือ error ไม่มี status) When กดจบ Then มี `role="alert"` "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" · ช่องพิมพ์และปุ่ม "จบการติว" กดได้ · ไม่มีบรรทัด "จบการติวรอบนี้แล้ว"
- **AC-10** Given stream ส่ง `error {code, message}` (หรือจบโดยไม่มี `done`) When กดจบ Then เหมือน AC-9
- **AC-11** Given stream ส่ง `session_end` แล้วจบโดยไม่มี `done` Then bubble สรุปอยู่ และเหมือน AC-9 (alert · ห้องใช้ได้)
- **AC-12 (TM-06)** Given `ChatRoom` ไม่มี `endSession` Then ไม่มีปุ่ม "จบการติว" (ปุ่มของห้องเท่าเดิม)
- **AC-13 (NFR-A1)** Given จบสำเร็จ Then `document.activeElement` คือลิงก์ "ติวรอบใหม่"
- **AC-14 (PM-05 · TutorRoom)** Given `fetch` ปลอม: `sessions/active` → session S, `GET /sessions/S` → fixture, `POST /sessions/S/end` → `session_end.txt` When เปิดห้องแล้วกด "จบการติว" Then มี request `POST {API}/sessions/S/end` 1 ครั้ง และเห็น bubble สรุปจาก fixture
- **AC-15 (TM-13 · TutorRoom)** Given AC-14 จบแล้ว และ `sessions/active` ตอบ `404 no_active_session` ครั้งต่อไป, `POST /exam-preps/{id}/sessions` → `room_session_start.txt` (session S2) When กด "ติวรอบใหม่" Then มี request `POST /exam-preps/{id}/sessions` และห้องเปิดเป็น session S2 (ไม่มีบรรทัด "จบการติวรอบนี้แล้ว" · ช่องพิมพ์ใช้ได้)
- **AC-16 (TutorRoom)** Given `POST /sessions/S/end` ตอบ `409 {error: {code: "session_already_ended"}}` When กดจบ Then เหมือน AC-8

ไม่มี threshold (ไม่มี boundary) · ไม่อ่านหรือเขียนข้อมูลเอง (การแยก tenant อยู่ที่ API · `session-end-db.md` AC-tenant) จึงไม่มี AC-tenant ในหน้าเว็บ

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ใช้ `POST /sessions/{id}/end` และ `session_end` ตาม api.md v1.19 (มีใน `lib/api-schema.ts` แล้ว) · หน้าเว็บเพิ่ม `createHttpSessionEnd(sessionId)` ใน `lib/httpTransport.ts` (แบบ `createHttpOcrConfirm`)

## 7. AI calls

ไม่มี (หน้าเว็บ · สรุปมาจาก `session_summary` ของ API)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `apps/web/tests/chat/ChatRoomSessionEnd.test.tsx` (ใหม่ · `ChatRoom` + `endSession` ปลอม) | unit (Vitest) | AC-1 ถึง AC-13 |
| `apps/web/tests/chat/RoomPageSessionEnd.test.tsx` (ใหม่ · `TutorRoom` + `fetch` ปลอม) | unit (Vitest) | AC-14 ถึง AC-16 |
| `apps/web/tests/fixtures/sse/session_end.txt` (ใหม่) | fixture | AC-14, AC-15 |
| test เดิมทั้งหมดของ `tests/chat/` ผ่าน · แก้ 1 บรรทัดใน `RoomPagePhoto.test.tsx` (ปุ่ม "จบการติว" · §2.1 ข้อ 1) | unit | AC-12 |
| ลองในเบราว์เซอร์กับ API ในเครื่อง + `anyang-dev` (login → ห้อง → ตอบ 1 ข้อ → จบ → สรุป → ติวรอบใหม่ → การ์ดเปลี่ยน) | มือ | ทั้งหมด |

## 9. Out of scope

- จบด้วยการพิมพ์ในแชท ("พอแค่นี้" · UC-03 A14 · wireframe S26) · ต้องมี `route_intent` (ai-orchestration) · หลัง demo
- ระบบเสนอให้จบเอง (TM-12 · S5) · จบอัตโนมัติเมื่อไม่ตอบ 15 นาที (UC-03 E2)
- เห็นแชทและสรุปของ session ที่จบแล้วหลังรีเฟรช / ติวรอบใหม่ (ต้องมีรายการ session เก่า · UC-03 E2 ให้สรุปต่อท้ายแชทเก่า) · หลัง demo
- หน้าหลักแสดง "ติวล่าสุด · n นาที" (S27) · หน้ารายการเป็นของ `prep-list-page.md`
- กล่องถามยืนยันก่อนจบ (May 17 พ.ย.: ไม่ถาม)

## 10. Open questions

1. ~~**(May) "ติวรอบใหม่" เป็นลิงก์หรือปุ่ม**~~ **ตัดสินแล้ว (May 17 พ.ย.): ลิงก์** · spec ใช้ลิงก์ (URL ของห้องเดิม) เพราะพาไปหน้าห้องใหม่ และคงจำนวนปุ่มของห้องให้น้อย · ถ้าเป็นปุ่ม test นับปุ่มเดิมไม่กระทบ (ไม่มี `endSession`) · ข้อเสนอ: ลิงก์
2. **(Jam · May รับข้อเสนอ 17 พ.ย.) ห้องเดโม่ในเครื่องที่ไม่มี token (`AUTH_REQUIRED=false`):** `/end` ตอบ stub (`X-Stub` · สรุปเดิมทุกครั้ง · ไม่ปิด session) · กด "ติวรอบใหม่" แล้วได้ session เดิม (`sessions/active`) · ใช้กับวิดีโอที่ login แล้วได้ ไม่กระทบ · ข้อเสนอ: ไม่ทำอะไรเพิ่ม
3. ~~**ข้อความ**~~ **ตัดสินแล้ว (May 17 พ.ย.):** "จบการติว", "จบการติวรอบนี้แล้ว", "ติวรอบใหม่" (§2.6)

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `specs/features/tutor/session-end-db.md` §9 | บรรทัด "หน้าเว็บ: ปุ่มจบ + การ์ดสรุป (May)" ชี้มาที่ spec นี้ (สรุปเป็น bubble ไม่ใช่การ์ด · May 17 พ.ย.) | May · PR นี้ (spec ของ Jam · บอก Jam) |
| `specs/features/tutor/chat-streaming.md` §2 ตาราง event | `session_end` แสดงแล้วตาม `session-end-ui.md` | May · PR นี้ |
| `docs/design/use-cases.md` UC-03 | หมายเหตุ: ขั้น 11 ใน demo ใช้ปุ่ม "จบการติว" จนกว่าจะมี `route_intent` | May · PR นี้ |
