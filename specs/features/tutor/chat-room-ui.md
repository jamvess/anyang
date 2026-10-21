# Feature: หน้าห้องติว · layout, bubble และ composer (S2)

| | |
|---|---|
| Area | tutor |
| Requirements | TM-06, TM-08 · ใช้ประกอบ: TM-04, TM-05 (ดู Open questions ข้อ 1) |
| Owner | May |
| Reviewer | Junior |
| Status | approved by May 2026-10-19 (owner) · รอ Junior review ใน PR |
| Related system spec | ai-orchestration.md §2.2.5 (input หลายช่องทาง), §2.2.6 (`messages`), §2.9 (limits) · api.md "ห้องติว" และ "SSE events" · `config/ai.yaml` → `guards` · wireframe S15–S26 |

## 1. Context

ห้องติวคือหน้าจอหลักของแอป user คุยกับ tutor และ buddy ในแชทเดียว แล้วตอบด้วยการพิมพ์หรือส่งรูปเท่านั้น ไม่มีปุ่มตัวเลือก (TM-06) feature นี้ทำ**โครงหน้าจอ**ใน S2: layout, bubble ของ 3 ผู้พูด, การแสดงสมการ (TM-08) และ composer สำหรับพิมพ์และแนบรูป โดยใช้**ข้อมูลตัวอย่าง (fixture)** แทน API เพราะ API ห้องติวจะมีใน S3 (P4-lite) ตอนนั้นจะเปลี่ยนจาก fixture เป็น `GET /sessions/{id}/messages` และ `POST /sessions/{id}/messages` (SSE) โดยไม่ต้องแก้ component

## 2. Behavior

**Route:** `app/preps/[id]/room/page.tsx` ใน S2 อ่าน fixture `tests/fixtures/room/session-s15.json` (ข้อความจาก wireframe S15–S17)

**แถบบน (room top)**

- ซ้าย: ชื่อการเตรียมสอบ และ "สอบใน {days_left} วัน" ทั้งสองค่ามาจากข้อมูล (fixture ใน S2, API ใน S3) ไม่คำนวณใน browser
- ขวา: ลิงก์ "ออกจากห้องติว" ไปหน้าหลัก `/`

**รายการข้อความ (MessageList)** เรียงตาม `created_at` จากเก่าไปใหม่

| role | แสดงเป็น |
|---|---|
| `tutor` | bubble ซ้าย, avatar อักษรย่อของชื่อ tutor, สีหลัก (accent) |
| `buddy` | bubble ซ้าย, avatar อักษรย่อของชื่อ buddy, สีเทา ต่างจาก tutor ชัดเจน |
| `user` | bubble ของ user, avatar สีเข้ม |
| `card`, `system` | ยังไม่แสดงใน S2 (progress card อยู่นอกขอบเขต) |

- **อักษรย่อใน avatar** (May เลือกแล้ว ให้ตรง wireframe): ตัดคำนำหน้า `พี่`, `น้อง`, `ครู` และช่องว่างที่ตามมาออกก่อน แล้วข้ามสระหน้า `เ แ โ ใ ไ` เอาตัวอักษรตัวแรกที่เหลือ เช่น พี่ตาล → ต, พี่โจ๊ก → จ, มีน → ม, ครู แอน → อ, Tar → T · avatar ของ user ใช้กฎเดียวกันกับชื่อเล่น (`user_name` จาก `/me/profile`)
- หัว bubble: ชื่อผู้พูด + เวลา `HH:mm` (เวลาท้องถิ่น Asia/Bangkok)
- ข้อความติดกันจากผู้พูดคนเดียวกัน: ไม่แสดงชื่อและ avatar ซ้ำ (เหมือน wireframe)
- ชื่อ tutor และ buddy มาจากข้อมูลห้อง (`tutor_name`, `buddy_name`) ไม่ hard-code
- ข้อความ `user` ที่ `input_mode = image` แสดงเป็นกล่องรูปพร้อมชื่อไฟล์ ("📷 วิธีทำ.jpg") ชื่อไฟล์คือส่วนท้ายของ `attachment_path`

**สมการ (TM-08)** ใน `content` ข้อความ `$…$` เป็นสมการ inline และ `$$…$$` เป็นสมการแบบ block (May เลือกแล้ว · ต้องเพิ่มใน api.md ดูข้อ 11) render ผ่าน `components/math/Tex.tsx` เท่านั้น ข้อความส่วนอื่นแสดงเป็น text ธรรมดา ไม่ render HTML จาก content

**Composer (TM-06)**

- ช่องพิมพ์หลายบรรทัด placeholder "พิมพ์ตอบ..." + ปุ่มแนบรูป 📷 + ปุ่มส่ง ↑
- ห้ามมีปุ่มตัวเลือกคำตอบใดๆ ในห้องติว ปุ่มที่กดได้ในห้องมีแค่: แนบรูป, ส่ง, เอารูปที่แนบออก, ลิงก์ออกจากห้อง
- ปุ่มส่งกดได้เมื่อความยาวข้อความไม่เกิน `max_message_chars` และ (มีข้อความที่ไม่ใช่ช่องว่างล้วน หรือมีรูปแนบ)
- ความยาวเกิน `guards.max_message_chars`: ปุ่มส่งกดไม่ได้ และขึ้นข้อความ "ข้อความยาวเกิน {max} ตัวอักษร"
- Enter = ส่ง · Shift+Enter = ขึ้นบรรทัดใหม่ (May เลือกแล้ว)
- แนบรูป: รับเฉพาะ `image/*` ขนาดไม่เกิน `max_image_mb` (1 MB = 1,048,576 bytes) · ไม่ใช่รูป: ไม่แนบ และขึ้นข้อความ "แนบได้เฉพาะรูป" · ใหญ่เกิน: ไม่แนบ และขึ้นข้อความ "รูปใหญ่เกิน {max} MB"
- เมื่อแนบรูปแล้ว: แสดงชื่อไฟล์ + ปุ่ม "เอารูปออก" · ยังพิมพ์ข้อความกำกับรูปได้ เช่น "ไม่แน่ใจบรรทัด 3" (May เลือกแล้ว · ต้องแก้ api.md ดูข้อ 11)
- กดส่ง: เรียก `onSend({ text, image })` (`text` เป็นข้อความที่ตัดช่องว่างหัวท้ายแล้ว หรือ `null` ถ้าว่าง · `image` เป็น `File` หรือ `null`) แล้วล้างช่องพิมพ์และรูปที่แนบ
- ข้อความ user ที่มีทั้งรูปและข้อความ แสดงกล่องรูปแล้วตามด้วยข้อความในข้อความเดียวกัน
- **ค่าขีดจำกัด** `max_message_chars` และ `max_image_mb` มากับข้อมูลห้องจาก API (May เลือกแล้ว) ค่ามาจาก `config/ai.yaml` → `guards` ฝั่ง backend · ใน S2 อยู่ใน fixture · component ห้าม hard-code
- **S2 เท่านั้น:** หน้า room ต่อ `onSend` เข้ากับ state ในหน้า ให้ข้อความที่ส่งต่อท้ายรายการเป็น bubble ของ user ทันที (ไม่มีคำตอบจาก tutor) · ใน S3 จะเปลี่ยนเป็นเรียก API

**ข้อความทั้งหมดบนหน้าจอ** (ภาษาไทย) อยู่ในไฟล์เดียว `components/chat/strings.ts`

**Accessibility:** ช่องพิมพ์มี label "พิมพ์ตอบ", ปุ่มมี label "แนบรูป", "ส่ง", "เอารูปออก" · ทุกปุ่มกดได้ด้วย keyboard

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (room) | `RoomData { prep_name: string, days_left: number, user_name: string, tutor_name: string, buddy_name: string \| null, limits: { max_message_chars: number, max_image_mb: number }, messages: ChatMessage[] }` | `{prep_name:"Factorization", days_left:5, user_name:"ปาล", tutor_name:"พี่ตาล", buddy_name:"มีน", limits:{max_message_chars:2000, max_image_mb:10}, messages:[…]}` |
| Input (message) | `ChatMessage { id, role: "user"\|"tutor"\|"buddy"\|"card"\|"system", content: string \| null, input_mode: "text"\|"voice"\|"image" \| null, attachment_path: string \| null, created_at: string (ISO) }` · field ตรงกับตาราง `messages` | `{id:"m1", role:"tutor", content:"ลองข้อนี้ $x^2-49$", input_mode:null, created_at:"2026-09-28T13:30:00Z"}` |
| Output (Composer) | `onSend(payload: { text: string \| null, image: File \| null })` (อย่างน้อยหนึ่งค่าไม่เป็น null) | `{text:"(x-7)(x+7)", image:null}` |

## 4. Acceptance criteria

ใช้ค่า `limits` ใน fixture ซึ่งเท่ากับ config ปัจจุบัน: `max_message_chars = 2000`, `max_image_mb = 10` · ทุกข้อ test ด้วย Vitest + Testing Library ไม่ใช้ AI

**Layout และ bubble**

- **AC-1 (TM-04)** Given fixture ที่มีข้อความ tutor, buddy, user When render ห้อง Then เห็นทั้ง 3 bubble ตามลำดับ `created_at` และแต่ละแบบมี role ต่างกันใน DOM (`data-role="tutor" | "buddy" | "user"`)
- **AC-2 (TM-05)** Given ข้อความจาก buddy When render Then หัว bubble แสดงชื่อ `buddy_name` และ avatar ของ buddy ไม่เหมือนของ tutor
- **AC-2b (TM-04)** อักษรย่อใน avatar: พี่ตาล → ต · พี่โจ๊ก → จ · มีน → ม · ครู แอน → อ · Tar → T
- **AC-3 (TM-04)** Given tutor ส่ง 2 ข้อความติดกัน When render Then ชื่อ "พี่ตาล" ปรากฏแค่ครั้งเดียวสำหรับสองข้อความนั้น
- **AC-3b (TM-20 · เพิ่ม 2026-10-21 · PR #59)** ข้อความติดกันของคนเดิมรวมใต้ชื่อเดียวตาม AC-3 **เฉพาะเมื่อห่างจากข้อความก่อนหน้าไม่ถึง `MESSAGE_GROUP_GAP_MIN` (5 นาที · May เลือก · ค่าของ UI ไม่ใช่ learning model)** · ถ้าห่างตั้งแต่ 5 นาทีขึ้นไป ข้อความนั้นแสดงชื่อ avatar และเวลาของตัวเองใหม่ · Given ข้อความ user 20:47 แล้วข้อความ user ถัดไป 11:42 ของอีกวัน When render Then เห็นชื่อ "ปาล" 2 ครั้ง และเวลา 11:42 แสดงอยู่ (เจอตอนลองจริงใน PR #42)
- **AC-3b-boundary (TM-20)** ข้อความ tutor 2 อันติดกัน ห่างกัน 4 นาที 59 วินาที → ชื่อปรากฏ 1 ครั้ง · ห่าง 5 นาทีพอดี → 2 ครั้ง · ห่าง 5 นาที 1 วินาที → 2 ครั้ง
- **AC-4 (TM-04)** Given ข้อความ role `card` หรือ `system` When render Then ไม่มี bubble ของข้อความนั้น · ข้อความ role `card` ที่มี `card` แสดงเป็นการ์ดความคืบหน้า (ไม่ใช่ bubble) ตาม `progress-card.md` (2026-10-21)
- **AC-5 (TM-04)** Given `days_left = 5` และ `prep_name = "Factorization"` When render Then แถบบนแสดง "Factorization" และ "สอบใน 5 วัน" และมีลิงก์ "ออกจากห้องติว" ไป `/`
- **AC-6 (TM-06)** Given ข้อความ user ที่ `input_mode = image` และ `attachment_path = "sessions/s1/วิธีทำ.jpg"` When render Then แสดงกล่องรูปที่มีชื่อ "วิธีทำ.jpg"
- **AC-6b (TM-06 · api.md v1.3)** Given ข้อความ user ที่ `input_mode = image`, `attachment_name = "วิธีทำ.jpg"` และ `attachment_path = "sessions/s1/3f2a9c1e-7b4d-4e8a-9c2f-1d5e6a7b8c90.jpg"` When render Then กล่องรูปแสดง "วิธีทำ.jpg" และไม่แสดง uuid · ชื่อไฟล์มาจาก `attachment_name` ก่อนเสมอ ถ้าเป็น `null` ใช้ส่วนท้ายของ `attachment_path` ตาม AC-6 (เพิ่ม 2026-10-21 · PR #42)
- **AC-6c (TM-06)** Given ข้อความ user ที่ `input_mode = image`, `attachment_name = "วิธีทำ.jpg"` และ `attachment_path = null` (ข้อความในเครื่องก่อนอัปโหลดเสร็จ) When render Then แสดงกล่องรูป "วิธีทำ.jpg" · ChatRoom สร้างข้อความ user ที่มีรูปด้วย `attachment_name` = ชื่อไฟล์ และ `attachment_path = null`

**สมการ (TM-08)**

- **AC-7 (TM-08)** Given content `"ลองข้อนี้ $x^2-49$"` When render Then มี KaTeX inline 1 ชิ้น และข้อความ "ลองข้อนี้" เป็น text ธรรมดา
- **AC-8 (TM-08)** Given content ที่มี `$$a^2-b^2=(a-b)(a+b)$$` When render Then มี KaTeX แบบ block 1 ชิ้น
- **AC-9 (TM-08)** Given content ที่ไม่มี `$` When render Then ไม่มี KaTeX เลย
- **AC-10 (TM-08)** Given content `"<b>x</b>"` When render Then แสดงเป็นตัวอักษร `<b>x</b>` ไม่มี element `<b>`

**Composer (TM-06)**

- **AC-11 (TM-06)** Given ห้องที่ render แล้ว When นับปุ่มทั้งหมด Then มีแค่ "แนบรูป" และ "ส่ง" (ไม่มีปุ่มตัวเลือกคำตอบ)
- **AC-12 (TM-06)** Given ช่องพิมพ์ว่าง หรือมีแค่ช่องว่าง/ขึ้นบรรทัด Then ปุ่มส่งกดไม่ได้
- **AC-13 (TM-06)** Given พิมพ์ "(x-7)(x+7)" When กดปุ่มส่ง Then `onSend` ถูกเรียก 1 ครั้งด้วย `{text:"(x-7)(x+7)", image:null}` และช่องพิมพ์ว่าง
- **AC-14 (TM-06)** Given พิมพ์ข้อความ When กด Enter Then ส่งเหมือนกดปุ่ม · When กด Shift+Enter Then ไม่ส่งและขึ้นบรรทัดใหม่
- **AC-boundary-text (TM-06)** ความยาว 1999 และ 2000 ตัวอักษร → ส่งได้ · 2001 ตัวอักษร → ปุ่มส่งกดไม่ได้และเห็น "ข้อความยาวเกิน 2000 ตัวอักษร"
- **AC-15 (TM-06)** Given เลือกไฟล์รูป "วิธีทำ.jpg" When แนบ Then เห็นชื่อไฟล์และปุ่ม "เอารูปออก" และปุ่มส่งกดได้แม้ช่องพิมพ์ว่าง
- **AC-16 (TM-06)** Given แนบรูปแล้วและช่องพิมพ์ว่าง When กดส่ง Then `onSend` ถูกเรียกด้วย `{text:null, image:File}` และรูปที่แนบหายไป
- **AC-16b (TM-06)** Given แนบรูปแล้วและพิมพ์ "ไม่แน่ใจบรรทัด 3" When กดส่ง Then `onSend` ถูกเรียกด้วย `{text:"ไม่แน่ใจบรรทัด 3", image:File}`
- **AC-17 (TM-06)** Given แนบรูปแล้ว When กด "เอารูปออก" Then รูปหายไป และถ้าช่องพิมพ์ว่าง ปุ่มส่งกดไม่ได้
- **AC-18 (TM-06)** Given เลือกไฟล์ที่ไม่ใช่รูป (เช่น `application/pdf`) Then ไม่แนบ และเห็นข้อความ "แนบได้เฉพาะรูป"
- **AC-boundary-image (TM-06)** ขนาด 10 MB − 1 byte และ 10 MB พอดี (10,485,760 bytes) → แนบได้ · 10 MB + 1 byte → ไม่แนบและเห็น "รูปใหญ่เกิน 10 MB"
- **AC-19 (TM-06)** Given หน้า room (S2) When ส่งข้อความ "ใช่ๆ" Then มี bubble ของ user ข้อความ "ใช่ๆ" ต่อท้ายรายการ

**Accessibility**

- **AC-20 (TM-06)** ช่องพิมพ์หาได้ด้วย label "พิมพ์ตอบ" และปุ่มหาได้ด้วย label "แนบรูป", "ส่ง"

**AC-tenant (SA-06):** ไม่เกี่ยว · feature นี้ไม่อ่านหรือเขียน database ใน S2 (ใช้ fixture) · การแยก tenant ของ `messages` ทดสอบที่ API ใน S3

## 5. Data changes

ไม่มี · ใช้ field ที่มีอยู่แล้วใน `messages` (`role`, `content`, `input_mode`, `attachment_path`, `created_at`)

## 6. API / SSE changes

ไม่มีใน S2 (ใช้ fixture) · S3 จะใช้ endpoint ที่มีอยู่แล้วใน api.md: `GET /sessions/{id}/messages`, `POST /sessions/{id}/uploads`, `POST /sessions/{id}/messages`

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/MessageList.test.tsx` | unit (component) | AC-1 ถึง AC-4, AC-3b, AC-3b-boundary, AC-6, AC-6b, AC-6c |
| `tests/chat/MessageText.test.tsx` | unit | AC-7 ถึง AC-10 |
| `tests/chat/Composer.test.tsx` | unit | AC-11 ถึง AC-18 (รวม AC-16b), AC-boundary-text, AC-boundary-image, AC-20 |
| `tests/chat/RoomPage.test.tsx` | integration (หน้า + fixture) | AC-5, AC-11, AC-19 |

## 9. Out of scope

- ต่อ API และ SSE จริง, การ stream ตัวอักษร (S3 · P4-lite)
- ปุ่มไมค์และข้อความจากเสียง (TM-07), ปุ่มฟังเสียง 🔊 (TM-09)
- progress card (TM-15), การ์ดโจทย์ (`problem` event), กล่องยืนยันลายมือ (`ocr_preview`, AM-02), ผลตรวจ (`verdict`)
- upload รูปขึ้น Storage จริง (`POST /sessions/{id}/uploads`)
- เลื่อนหน้าจอลงล่างอัตโนมัติ, ดูแชทเก่า, ออกจากห้องแล้วกลับมาต่อ (TM-13)
- layout บนมือถือ (ทำเฉพาะจอคอมตาม wireframe)

## 10. Open questions

ตัดสินแล้ว (2026-10-19)

- Enter = ส่ง, Shift+Enter = ขึ้นบรรทัด (May)
- ส่งรูปพร้อมข้อความกำกับได้ (May) · ต้องแก้ api.md
- สมการใช้ `$…$` และ `$$…$$` (May) · ต้องเพิ่มใน api.md และ prompt `tutor_reply`
- ค่าขีดจำกัดมากับข้อมูลห้องจาก API (May) · S2 ใช้ค่าใน fixture
- 1 MB = 1,048,576 bytes (ค่าเริ่มต้น · ต้องตรงกับที่ backend ตรวจ)
- ชื่อไฟล์รูปที่แสดง ใช้ชื่อท้ายของ `attachment_path` ไปก่อน (ไม่เพิ่ม column)

ยังเปิดอยู่ (ให้ reviewer ตอบ)

1. ~~Requirement ID ของ AC เรื่อง layout และ bubble~~ · ตอบแล้ว: requirements v1.2 เพิ่ม **TM-20** (bubble) และ **TM-21** (ขีดจำกัด input) · ตอนทำ P4-lite ให้เปลี่ยนชื่อ test จาก TM04/TM05 เป็น TM20 และ test ขีดจำกัดเป็น TM21 (May ตัดสิน 2026-10-19 · ต้องให้ May review ชื่อใหม่)
2. **เครื่องหมาย `$` ที่ไม่ใช่สมการ** (เช่น ราคา "$5") จะถูกอ่านเป็นสมการ · คณิตระดับนี้แทบไม่เจอ จึงยังไม่จัดการใน S2

## 11. Spec changes needed

ต้องให้เจ้าของอนุมัติก่อน (api.md เป็นไฟล์ร่วม)

- **api.md** "ห้องติว": `POST /sessions/{id}/messages` รับ `{text, image_path}` พร้อมกันได้ (อย่างน้อยหนึ่งค่า) · เดิมรับอย่างใดอย่างหนึ่ง
- **api.md** "ห้องติว": ข้อมูลห้อง (`GET /sessions/{id}/messages` หรือ response ของ `POST /exam-preps/{id}/sessions`) ส่ง `limits: {max_message_chars, max_image_mb}` จาก `config/ai.yaml` → `guards` มาด้วย
- **api.md** "SSE events" + Conventions: สมการใน `token.text` และ `messages.content` เขียนเป็น `$…$` (inline) และ `$$…$$` (block)
- **prompts/tutor_reply** (Jam): ใช้รูปแบบสมการเดียวกัน
