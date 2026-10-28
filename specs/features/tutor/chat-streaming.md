# Feature: ห้องติว · stream คำตอบจาก SSE (S3 · P4-lite)

| | |
|---|---|
| Area | tutor |
| Requirements | TM-20, TM-08, TM-06 · เปลี่ยนชื่อ test เดิมเป็น TM-20, TM-21 · วัดผลภายหลัง: NFR-P1 |
| Owner | May |
| Reviewer | Junior |
| Status | approved by May 2026-10-20 (owner) · รอ Junior review ใน PR |
| Related system spec | api.md "Conventions" (Streaming), "ห้องติว", "SSE events" · ai-orchestration.md §2.1.6 (ทั้งฉากใน call เดียว), §2.2.5, §2.2.8 · `chat-room-ui.md` (S2) · PoC P4-lite (`specs/poc/README.md`) |

## 1. Context

ใน S2 ห้องติวส่งข้อความได้แต่ไม่มีใครตอบ feature นี้ทำให้ห้องติว**ส่งข้อความแล้วอ่านคำตอบที่ stream กลับมาเป็น SSE** ผ่าน `lib/sse.ts` ข้อความของ tutor และ buddy ไหลเข้า bubble ทีละส่วน และสมการ render ด้วย KaTeX (TM-08) เป็นฝั่ง web ของ PoC P4-lite

ChatRoom ไม่เรียก `fetch` เอง แต่รับ **transport** เข้ามา (function ที่รับ `SendPayload` แล้วคืน SSE events) branch นี้ใช้ **fake transport** ที่เล่น event จากไฟล์ fixture เพราะ `POST /sessions/{id}/messages` ของ backend ยังไม่มี เมื่อ endpoint มาแล้วจะเพิ่ม HTTP transport โดยไม่ต้องแก้ ChatRoom

## 2. Behavior

**Transport**

```ts
type SendMessage = (payload: SendPayload, signal: AbortSignal) => AsyncIterable<SSEEvent>;
```

- ChatRoom รับ `sendMessage` เป็น prop · `SSEEvent` คือ type เดิมใน `lib/sse.ts`
- `sendMessage` ไม่บังคับ ถ้าไม่ส่งมา ใช้ transport ที่ตอบ `done` ทันที (พฤติกรรมเท่ากับ S2: มีแค่ bubble user ไม่มีคำตอบ) เพื่อให้ test ของ S2 ที่ review แล้วผ่านโดยไม่ต้องแก้
- **Fake transport** (`lib/fakeTransport.ts`): อ่าน SSE text (รูปแบบเดียวกับ `tests/fixtures/sse/*.txt`) ผ่าน `parseSSE` แล้วปล่อยทีละ chunk โดยมีหน่วงเวลาระหว่าง chunk เพื่อให้เห็นการไหลบนหน้าจอ ค่าหน่วงเป็น parameter ของ fake transport (test ใช้ 0) ไม่ใช่ค่าของ learning model
- หน้า room ใช้ fake transport ที่เล่น fixture `tests/fixtures/sse/tutor_reply.txt` ทุกครั้งที่ส่ง ไม่ว่าจะพิมพ์อะไร (ข้อความไม่สัมพันธ์กับคำถาม ยอมรับได้ใน PoC)

**เมื่อกดส่ง**

1. ข้อความ user ต่อท้ายรายการทันที (เหมือน S2)
2. ChatRoom เรียก `sendMessage(payload, signal)` และเข้าสถานะ **กำลังตอบ**:
   - **Composer:** ยังพิมพ์และแนบรูปเป็นร่างไว้ได้ แต่ปุ่มส่งกดไม่ได้และ Enter ไม่ส่ง จนกว่าจะออกจากสถานะกำลังตอบ (May เลือก · backend ประกอบ context ใหม่ทุก turn §2.6 การส่งซ้อนจะได้คำตอบสลับกัน)
   - **ตัวบอกว่ากำลังพิมพ์:** ต่อท้ายรายการด้วย bubble ของ tutor ที่มีจุดสามจุด (•••) และ `aria-label` "กำลังพิมพ์" ใช้หัว bubble ตามกฎเดิม (May เลือก) · หายไปทันทีเมื่อได้ event ที่สร้าง bubble (`token` หรือ `buddy`) หรือเมื่อ stream จบ · ไม่ใช่ `ChatMessage` และไม่นับเป็นข้อความ
3. อ่าน event ตามลำดับ:

| Event | ทำอะไร |
|---|---|
| `token {speaker, text}` | ถ้า bubble ล่าสุดเป็นของ `speaker` เดียวกันและสร้างจาก stream รอบนี้ ให้ต่อ `text` ท้าย content · ถ้าไม่ใช่ ให้สร้าง bubble ใหม่ของ `speaker` นั้น (tutor → buddy → tutor ได้ 3 bubble ตาม §2.1.6) |
| `buddy {text}` | สร้าง bubble buddy ใหม่ 1 อันด้วย `text` ทั้งก้อน (ข้อความ buddy นอกจังหวะ §2.1.7) |
| `done {}` | จบ stream ออกจากสถานะกำลังตอบ |
| `error {code, message}` | จบ stream แสดงข้อความแจ้งผิดพลาดและออกจากสถานะกำลังตอบ · bubble ที่ stream มาแล้วบางส่วนยังอยู่ |
| `progress_card`, `problem`, `ocr_preview`, `verdict`, `session_end`, `scope_patch` และ event ที่ไม่รู้จัก | ไม่แสดงอะไรใน feature นี้ ข้ามไปอ่าน event ถัดไป ห้าม crash · ภายหลังแสดงแล้วตาม feature แยก: `progress_card` (`progress-card.md`), `problem` (`problem-card.md`), `ocr_preview` (`check/ocr-confirm-card.md`), `verdict` (`check/verdict-mark.md`) |

4. ถ้า transport throw (เช่น เน็ตหลุด, HTTP ไม่ใช่ 2xx) หรือ stream จบโดยไม่มี `done`: ทำเหมือนได้ `error`
5. ออกจากหน้า room (unmount) ระหว่าง stream: abort `signal` และไม่ update state อีก

**ข้อความแจ้งผิดพลาด** (May เลือก): "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" ข้อความเดียวทุกกรณี (ทุก `code`, transport throw, จบโดยไม่มี `done`) แสดงเหนือ composer เป็น `role="alert"` · ไม่แสดง `message` จาก server (อาจเป็นภาษาเทคนิค) · หายไปเมื่อกดส่งข้อความถัดไป · ไม่มีปุ่มลองใหม่ user พิมพ์ส่งเอง

**เลื่อนจอตาม stream** (May เลือก): เมื่อมี bubble ใหม่ หรือ content ของ bubble ที่กำลัง stream เปลี่ยน ให้เลื่อนรายการลงล่างสุด **เฉพาะเมื่อ** ก่อนเปลี่ยน user อยู่ใกล้ล่างสุดอยู่แล้ว ถ้า user เลื่อนขึ้นไปอ่านข้อความเก่า ไม่ดึงลง · ตอนกดส่งข้อความเองให้เลื่อนลงล่างสุดเสมอ · ระยะ "ใกล้ล่างสุด" เป็นค่าคงที่ชื่อ `NEAR_BOTTOM_PX` ใน component (ค่าของ UI ไม่ใช่ค่าของ learning model)

**Bubble ที่มาจาก stream**

- เป็น `ChatMessage` ปกติ: `role` = speaker, `input_mode = null`, `attachment_path = null`, `id` เป็น id ในเครื่อง, `created_at` = เวลาในเครื่องตอนได้ token แรกของ bubble นั้น · เมื่อต่อ API จริง ข้อมูลจาก `GET /sessions/{id}/messages` จะเป็นค่าจริงแทน
- กฎ bubble ของ S2 ใช้เหมือนเดิมทั้งหมด (ชื่อ, avatar, ไม่ซ้ำชื่อเมื่อพูดติดกัน, สมการ, ไม่ render HTML)

**สมการระหว่าง stream (TM-08)**

- render ใหม่ทุกครั้งที่ content เปลี่ยน ด้วย `MessageText` ตัวเดิม
- ระหว่าง stream ถ้ามี `$` หรือ `$$` ที่ยังไม่มีตัวปิด ให้**ซ่อน**ตั้งแต่ตัวเปิดนั้นถึงท้าย content (May เลือก) เช่น `"ลอง $x^2"` แสดงแค่ "ลอง " · เมื่อตัวปิดมาถึง สมการแสดงเป็น KaTeX ทั้งก้อน
- กฎซ่อนใช้เฉพาะ bubble ที่ยัง stream อยู่ เมื่อ stream จบ (`done`, `error` หรือจบผิดปกติ) ให้แสดง content ทั้งหมดตามกฎ S2 (`$` ที่ไม่มีคู่แสดงเป็นตัวอักษร) เพื่อไม่ให้ข้อความหาย

**ส่งรูป (TM-06)** composer ส่ง `{text, image}` ให้ transport เหมือนเดิม fake transport ไม่ upload อะไร แค่เล่น fixture · การ upload จริง (`POST /sessions/{id}/uploads` → PUT signed URL → `POST /sessions/{id}/messages` พร้อม `image_path`) อยู่ใน HTTP transport ของ branch ถัดไป

**ข้อความไทยใหม่** อยู่ใน `components/chat/strings.ts`

**Accessibility (NFR-A1):** รายการข้อความเป็น `role="log"` (มี `aria-live="polite"` ในตัว) เพื่อให้ screen reader อ่านข้อความใหม่ · ข้อความแจ้งผิดพลาดใช้ `role="alert"`

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (prop) | `sendMessage: (payload: SendPayload, signal: AbortSignal) => AsyncIterable<SSEEvent>` | fake transport ที่เล่น `tutor_reply.txt` |
| Input (events) | `token {speaker: "tutor" \| "buddy", text}` · `buddy {text}` · `done {}` · `error {code, message}` (api.md "SSE events") | `event: token` / `data: {"speaker":"tutor","text":"ถูกแล้ว "}` |
| Output | bubble ใน MessageList (`ChatMessage` ตาม `chat-room-ui.md` §3) + สถานะกำลังตอบ + ข้อความแจ้งผิดพลาด | bubble tutor "ถูกแล้ว $(x-7)(x+7)$" |

## 4. Acceptance criteria

ทุกข้อใช้ transport ปลอมใน test (async generator ที่ yield event ตามลำดับ หรือ fake transport ที่หน่วง 0) ไม่ใช้ AI และไม่ใช้ network

**การส่งและ stream (TM-20)**

- **AC-1 (TM-20)** Given ห้องที่ render แล้ว When ส่ง "(x-7)(x+7)" Then `sendMessage` ถูกเรียก 1 ครั้งด้วย `{text:"(x-7)(x+7)", image:null}` และ bubble user ต่อท้ายรายการก่อน bubble ของคำตอบ
- **AC-2 (TM-20)** Given transport ส่ง `token tutor "ถูก"`, `token tutor "แล้ว"`, `done` When ส่งข้อความ Then มี bubble tutor ใหม่ **1** อัน content "ถูกแล้ว" และหัว bubble เป็น `tutor_name`
- **AC-3 (TM-20)** Given transport หยุดหลัง `token tutor "ถูก"` (ยังไม่ส่ง event ถัดไป) When ส่งข้อความ Then เห็น bubble tutor "ถูก" ก่อน stream จบ · When transport ส่ง `token tutor "แล้ว"` ต่อ Then bubble เดิมเปลี่ยนเป็น "ถูกแล้ว" (ไม่มี bubble เพิ่ม)
- **AC-4 (TM-20)** Given transport ส่ง token tutor → buddy → tutor แล้ว `done` When ส่ง Then มี bubble ใหม่ 3 อันตามลำดับ tutor, buddy, tutor (`data-role`) และหัว bubble buddy เป็น `buddy_name`
- **AC-5 (TM-20)** Given ข้อความล่าสุดในห้องก่อนส่งเป็นของ tutor When stream ส่ง `token tutor` Then สร้าง bubble ใหม่ ไม่ต่อท้ายข้อความเก่าของ tutor
- **AC-6 (TM-20)** Given transport ส่ง `buddy {text:"เหนื่อยเหมือนกันเลย"}` แล้ว `done` Then มี bubble buddy ใหม่ 1 อัน content "เหนื่อยเหมือนกันเลย"
- **AC-7 (TM-20)** Given transport ส่ง `progress_card`, `problem`, `verdict`, event ชื่อ `unknown_event` คั่นระหว่าง token tutor 2 ตัว แล้ว `done` Then ไม่มี error และมี bubble tutor 1 อันที่รวม token ทั้ง 2 · **แก้ 2026-10-21:** `progress_card` ไม่ถูกข้ามแล้ว แสดงเป็นการ์ดและตัด bubble ตาม `progress-card.md` AC-9 · test นี้ตัด `progress_card` ออก (May อนุมัติ) · `problem` แสดงเป็นการ์ดโจทย์ตาม `problem-card.md` AC-6 · ตัดออกจาก test นี้เช่นกัน (May อนุมัติ 2026-10-21) · `verdict` แสดงเป็นแถบผลตรวจตาม `check/verdict-mark.md` · ตัดออกจาก test นี้เช่นกัน (May อนุมัติ 2026-10-28)
- **AC-8 (TM-20)** Given ส่งข้อความสองรอบ แต่ละรอบ stream `token tutor` Then ได้ bubble tutor 2 อัน แยกกันตามรอบ

**สมการระหว่าง stream (TM-08)**

- **AC-9 (TM-08)** Given token tutor `"ลอง $x^2"` แล้ว `"-49$ ดู"` แล้ว `done` When stream จบ Then bubble มี KaTeX inline 1 ชิ้น (`x^2-49`) และข้อความ "ลอง" กับ "ดู" เป็น text
- **AC-10 (TM-08)** Given transport หยุดหลัง token `"ลอง $x^2"` Then bubble มีข้อความ "ลอง" ไม่มี KaTeX และไม่มีตัวอักษร `$` หรือ `x^2` ใน bubble
- **AC-11 (TM-08)** Given token `"$$a^2-b^2"` แล้ว `"=(a-b)(a+b)$$"` แล้ว `done` Then มี KaTeX แบบ block 1 ชิ้น · และขณะหยุดหลัง token แรก bubble ไม่มีตัวอักษร `$$` หรือ `a^2`
- **AC-11b (TM-08)** Given token `"ราคา $5"` แล้ว `done` When stream จบ Then bubble แสดง "ราคา $5" เป็นตัวอักษร (ไม่ซ่อนหลังจบ stream)

**สถานะกำลังตอบ และข้อผิดพลาด (TM-20)**

- **AC-12 (TM-20)** Given stream ยังไม่จบ When พิมพ์ "ข้อต่อไป" Then ช่องพิมพ์มี "ข้อต่อไป" แต่ปุ่มส่งกดไม่ได้ และกด Enter แล้ว `sendMessage` ไม่ถูกเรียกเพิ่ม · When ได้ `done` Then ปุ่มส่งกดได้ และกดส่ง "ข้อต่อไป" ได้
- **AC-12b (TM-20)** Given stream ยังไม่จบและยังไม่มี token When render Then เห็นตัวบอกกำลังพิมพ์ (หาได้ด้วย label "กำลังพิมพ์") ในตำแหน่งท้ายรายการ · When ได้ `token tutor "ถูก"` Then ตัวบอกหายไปและเห็น bubble tutor "ถูก" · Given stream ได้ `done` โดยไม่มี token Then ตัวบอกหายไป
- **AC-13 (TM-20)** Given transport ส่ง `token tutor "ถูก"` แล้ว `error {code:"ai_unavailable", message:"provider timeout"}` Then bubble tutor "ถูก" ยังอยู่, เห็น `role="alert"` ที่มีข้อความ "ส่งไม่สำเร็จ ลองส่งอีกทีนะ", ไม่เห็นข้อความ "provider timeout" และปุ่มส่งกดได้อีกครั้ง
- **AC-14 (TM-20)** Given transport throw ก่อนได้ event ใดๆ Then bubble user ยังอยู่, เห็นข้อความแจ้งผิดพลาด, ไม่มี bubble tutor ใหม่ และออกจากสถานะกำลังตอบ
- **AC-15 (TM-20)** Given transport ส่ง `token tutor "ถูก"` แล้วจบโดยไม่มี `done` Then ทำเหมือน AC-13
- **AC-16 (TM-20)** Given ข้อความแจ้งผิดพลาดแสดงอยู่ When ส่งข้อความใหม่ Then ข้อความแจ้งผิดพลาดหายไป
- **AC-17 (TM-20)** Given stream ยังไม่จบ When unmount ห้อง Then `signal.aborted === true` และไม่มี warning เรื่อง update state หลัง unmount

**เลื่อนจอตาม stream (TM-20)** ใน test จำลองตำแหน่ง scroll ของรายการ (`scrollTop`, `scrollHeight`, `clientHeight`) เพราะ jsdom ไม่คำนวณ layout

- **AC-scroll-1 (TM-20)** Given รายการอยู่ล่างสุด When ได้ token ใหม่ Then รายการถูกเลื่อนลงล่างสุด
- **AC-scroll-2 (TM-20)** Given user เลื่อนขึ้นไปไกลจากล่างสุดเกิน `NEAR_BOTTOM_PX` When ได้ token ใหม่ Then ตำแหน่ง scroll ไม่เปลี่ยน
- **AC-scroll-boundary (TM-20)** ระยะจากล่างสุด = `NEAR_BOTTOM_PX − 1` และ `= NEAR_BOTTOM_PX` → เลื่อนลง · `NEAR_BOTTOM_PX + 1` → ไม่เลื่อน
- **AC-scroll-3 (TM-20)** Given user เลื่อนขึ้นไปไกลจากล่างสุด When กดส่งข้อความเอง Then รายการถูกเลื่อนลงล่างสุด

**ส่งรูป (TM-06)**

- **AC-18 (TM-06)** Given แนบรูป "วิธีทำ.jpg" และพิมพ์ "ไม่แน่ใจบรรทัด 3" When ส่ง Then `sendMessage` ได้ `{text:"ไม่แน่ใจบรรทัด 3", image:File}` ที่ `image.name === "วิธีทำ.jpg"` และ bubble user แสดงกล่องรูป "วิธีทำ.jpg" พร้อมข้อความ

**Fake transport**

- **AC-19 (TM-20)** Given SSE text ของ `tests/fixtures/sse/tutor_reply.txt` และหน่วง 0 When เรียก fake transport Then ได้ event ตามลำดับในไฟล์ และ event สุดท้ายเป็น `done`
- **AC-20 (TM-20)** Given fake transport When `signal` ถูก abort ระหว่างทาง Then หยุด yield event

**หน้า room**

- **AC-21 (TM-20)** Given หน้า room (ใช้ fake transport ที่หน่วงตามค่า demo · test รอได้สูงสุด 5 วินาที) When ส่ง "ใช่ๆ" Then มี bubble user "ใช่ๆ" ตามด้วย bubble tutor ที่มีข้อความจาก `tutor_reply.txt` (แทน AC-19 ของ `chat-room-ui.md` ที่ไม่มีคำตอบ) · **เลิกใช้ 2026-10-21:** หน้า room ใช้ API แทน fake transport ตาม `room-http.md` (AC-6 แทนข้อนี้ · May อนุมัติ)

**เปลี่ยนชื่อ test เดิม** (ตาม `chat-room-ui.md` §10 ข้อ 1 · ไม่แก้เนื้อ test)

- test ที่ขึ้นต้นด้วย `TM04` และ `TM05` ใน `MessageList.test.tsx` และ `RoomPage.test.tsx` → `TM20`
- test ขีดจำกัดความยาวข้อความและขนาดรูป (AC-boundary-text, AC-boundary-image, AC-18 ของ S2) ใน `Composer.test.tsx` → `TM21`
- test เดิม "a sent message appears at the end as a user bubble" ใน `RoomPage.test.tsx` ยังผ่านได้ (bubble user ยังต่อท้ายทันที) แค่เปลี่ยนชื่อเป็น `TM20`

**AC-tenant (SA-06):** ไม่เกี่ยว · feature นี้ไม่อ่านหรือเขียน database (fake transport) · การแยก tenant ของ `messages` ทดสอบที่ API

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มีการเพิ่ม endpoint หรือ event · ใช้ event ที่มีใน api.md แล้ว: `token`, `buddy`, `done`, `error`

ไฟล์ fixture ใหม่: `tests/fixtures/sse/tutor_reply.txt` (ฉาก tutor → buddy → tutor ที่มีสมการ inline และ block, จบด้วย `done`) · `tests/fixtures/sse/tutor_reply_error.txt` (token บางส่วนแล้ว `error`)

## 7. AI calls

ไม่มี (ฝั่ง backend `tutor_reply` เป็นของ Junior ใน P4-lite)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/ChatRoomStream.test.tsx` | integration (ChatRoom + transport ปลอม) | AC-1 ถึง AC-18 (รวม AC-11b, AC-12b), AC-scroll-* |
| `tests/fakeTransport.test.ts` | unit | AC-19, AC-20 |
| `tests/chat/RoomPage.test.tsx` (เพิ่ม test) | integration (หน้า + fake transport) | AC-21 |
| เปลี่ยนชื่อใน `MessageList`, `Composer`, `RoomPage` test | — | TM-20, TM-21 |

## 9. Out of scope

- HTTP transport จริง (`postSSE` ไป `POST /sessions/{id}/messages`), upload รูปขึ้น Storage, auth header · branch ถัดไปเมื่อ endpoint ของ Junior มา
- วัด TTFT และต้นทุนบน staging (NFR-P1, NFR-P2) · ทำร่วมกับ Junior หลังต่อ API จริง
- โหลดประวัติจาก `GET /sessions/{id}/messages` และสร้าง session (`POST /exam-preps/{id}/sessions`)
- แสดง `progress_card`, `problem`, `ocr_preview`, `verdict`, `session_end` (เป็น feature แยก)
- ปุ่มลองส่งใหม่ (ขัดกับรายการปุ่มที่อนุญาตใน `chat-room-ui.md` · user พิมพ์ส่งใหม่เอง)
- เสียง (TM-07, TM-09)

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-20)

- ระหว่างกำลังตอบ: พิมพ์ร่างได้ แต่ส่งไม่ได้
- ก่อน token แรก: bubble tutor จุดสามจุด
- ผิดพลาด: ข้อความเดียว "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" เหนือ composer ไม่แสดง `message` จาก server
- `$` ที่ยังไม่ปิดระหว่าง stream: ซ่อนไว้จนกว่าจะปิด · แสดงทั้งหมดเมื่อ stream จบ
- เลื่อนจอตาม stream: ทำในงานนี้ เฉพาะเมื่อ user อยู่ใกล้ล่างสุด

ยังเปิดอยู่ ให้ Junior ตอบ (reviewer):

6. **รหัส `error.code` ของ SSE** ที่ backend จะส่งในห้องติวมีอะไรบ้าง · api.md มีแค่รูปแบบ `{code, message}` ไม่มีรายการ code
7. **ข้อความ degrade "ระบบช้า ลองส่งอีกทีนะ"** (§2.10) backend ส่งเป็น `token` ของ tutor แล้วตามด้วย `done` หรือส่งเป็น `error` · ถ้าเป็น `token` หน้าจอจะเห็นเป็น bubble tutor ปกติ

## 11. Spec changes needed

ต้องให้เจ้าของอนุมัติก่อน (api.md เป็นไฟล์ร่วม · ข้อ 1–3 ค้างมาจาก `chat-room-ui.md` §11)

- **api.md** "ห้องติว": `POST /sessions/{id}/messages` รับ `{text, image_path}` พร้อมกันได้ (อย่างน้อยหนึ่งค่า)
- **api.md** "ห้องติว": ข้อมูลห้องส่ง `limits: {max_message_chars, max_image_mb}`
- **api.md** Conventions: สมการใน `token.text` และ `messages.content` เขียนเป็น `$…$` และ `$$…$$`
- **api.md** "SSE events": รายการ `error.code` ของห้องติว (Open question ข้อ 6)
- **api.md** "ห้องติว": response ของ `POST /sessions/{id}/uploads` (field ของ signed URL และ `image_path`) · ต้องใช้ใน HTTP transport branch ถัดไป
