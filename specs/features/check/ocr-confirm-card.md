# Feature: ห้องติว · การ์ดยืนยันคำตอบลายมือ

| | |
|---|---|
| Area | checker (หน้าเว็บ) |
| Requirements | AM-02 · AM-01 (แสดงผลที่อ่านได้เป็นสมการ) · AM-03 (ส่งบรรทัดที่แก้ให้ backend log) · TM-08 · TM-06 |
| Owner | May |
| Reviewer | Junior (api.md · Open questions 5–7) |
| Status | approved by May 2026-10-28 (owner · OQ 1–4, 7) · รอ Junior ตอบ OQ 5, 6, 8 (api.md) |
| Related system spec | api.md "ห้องติว" (`POST /sessions/{id}/ocr/confirm`), "SSE events" (`ocr_preview`) · ai-orchestration.md §2.2.5, §2.2.10 ข้อ 5 · `config/learning.yaml` → `ocr.always_confirm` · use-cases.md UC-04 ขั้น 2–3, A1, E1, E2 · wireframe S21, S35 · `chat-streaming.md` §2 · `chat-room-ui.md` §2 (ปุ่มในห้อง) · `problem-card.md` (รูปแบบการ์ดใน stream) |

## 1. Context

เมื่อผู้ใช้ส่งรูปวิธีทำ backend อ่านลายมือด้วย `extract_answer` ได้ LaTeX ทีละบรรทัด แล้วส่ง event `ocr_preview` · ระบบต้องให้ผู้ใช้ยืนยันทุกครั้งก่อนตรวจ เพราะ PoC P1 พบว่า confidence ของ model แยกบรรทัดที่อ่านผิดไม่ได้ (AM-02 · `ocr.always_confirm`) · ตอนนี้หน้าเว็บข้าม `ocr_preview` (chat-streaming.md §2) feature นี้แสดงการ์ด "อ่านได้แบบนี้ ถูกไหม" ให้ผู้ใช้แก้บรรทัดที่อ่านผิด แล้วกดยืนยันเพื่อเรียก `POST /sessions/{id}/ocr/confirm` ซึ่ง stream ผลตรวจกับคำตอบของติวเตอร์ต่อ (UC-04 ขั้น 2–5)

## 2. Behavior

**ข้อมูล:** `ocr_preview` = `{lines: [{latex, confidence}]}` (api.md) · `latex` เป็น LaTeX ล้วนไม่มี `$` แบบเดียวกับ `problem.text_latex` (ต้องยืนยัน · Open question 6)

**แสดงเมื่อไหร่**

- event `ocr_preview` ระหว่าง stream ของ `POST /sessions/{id}/messages` → เพิ่มการ์ดต่อท้าย ณ ตำแหน่งที่ event มา · ไม่ใช่ bubble (ไม่มี `data-role`) · token ที่ตามมาเริ่ม bubble ใหม่ (แบบเดียวกับ `problem-card.md` AC-6)
- แสดง**ทุกครั้ง** ไม่ว่า `confidence` จะเท่าไร · หน้าเว็บไม่อ่าน `confidence` เลย (ไม่แสดง ไม่ไฮไลต์ ไม่ใช้ตัดสิน · UC-04 ตัดสินแล้ว 2026-10-21)
- `lines` ว่าง → ไม่มีการ์ด (backend ส่งรูปที่อ่านไม่ได้เป็น `token` ของติวเตอร์ ไม่ใช่ `ocr_preview` · UC-04 E1 · ถ้า `lines` ว่างมาถึงก็ไม่มีอะไรให้ยืนยัน)
- รูปอ่านไม่ได้ (E1): ไม่มี `ocr_preview` → ไม่มีการ์ด · ห้องแสดง token ของติวเตอร์ตามปกติ (ไม่ต้องทำอะไรเพิ่ม)

**หน้าตา (ตาม wireframe S21)**

- `role="region"` ชื่อ (`aria-label`) "อ่านได้แบบนี้ ถูกไหม" · หัวการ์ดเป็นข้อความคงที่ "ขอเช็คก่อนว่าอ่านถูกมั้ย ที่เขียนมาคือ" อยู่ใน `strings.ts` ไม่ได้มาจาก LLM (architecture rule 1)
- ทุกบรรทัดเรียงตามลำดับใน `lines` · มีเลขบรรทัด 1…n · สมการ render ด้วย `Tex` (ไม่ผ่าน `MessageText`) · ปุ่ม "✎ แก้" ท้ายบรรทัด (`aria-label` "แก้บรรทัด {n}")
- ใต้รายการ: ปุ่ม "ถูกแล้ว ตรวจเลย" และ "ถ่ายใหม่"
- `latex` ผิด syntax → การ์ดยังแสดง (`Tex` ใช้ `throwOnError: false` แสดง source สีแดง) ผู้ใช้กดแก้บรรทัดนั้นได้

**แก้บรรทัด (AM-03)**

- กด "✎ แก้" บรรทัด n → บรรทัดนั้นเปลี่ยนเป็นช่องพิมพ์ (`aria-label` "บรรทัด {n}") ที่มีค่าเดิมเป็น `latex` ของบรรทัดนั้น · ใต้ช่องมี preview สมการที่อัปเดตทุกครั้งที่พิมพ์ · มีปุ่ม "บันทึก" และ "ยกเลิก" · Enter = บันทึก, Esc = ยกเลิก
- บันทึก → บรรทัดแสดงค่าใหม่เป็นสมการ และมีป้ายเล็ก "แก้แล้ว" · ยกเลิก → กลับเป็นค่าก่อนกดแก้
- แก้ได้ทีละบรรทัด (กด "✎ แก้" บรรทัดอื่นขณะแก้อยู่ = บันทึกบรรทัดเดิมก่อน ถ้าช่องว่างล้วนให้ยกเลิกแทน · ตัดสินแล้ว OQ 2)
- ช่องที่เหลือแต่ช่องว่าง → ปุ่ม "บันทึก" กดไม่ได้ · ลบหรือเพิ่มบรรทัดไม่ได้ (ตัดสินแล้ว OQ 3)
- ระหว่างแก้อยู่ ปุ่ม "ถูกแล้ว ตรวจเลย" กดไม่ได้ (กันส่งค่าที่ยังไม่บันทึก)

**ยืนยัน**

- กด "ถูกแล้ว ตรวจเลย" → เรียก `confirmOcr(lines)` ของ transport โดย `lines` คือ LaTeX ทุกบรรทัดเรียงตามลำดับ บรรทัดที่แก้ใช้ค่าที่บันทึก (A1: ไม่แก้เลย = ส่งค่าเดิมทุกบรรทัด) · ไม่ส่ง `confidence`
- เล่น stream ที่ได้กลับด้วย `play` เดิม (chat-streaming.md §2) · ไม่มี bubble ของผู้ใช้เพิ่ม
- ระหว่าง stream: ปุ่มทั้งหมดในการ์ดกดไม่ได้ และช่องพิมพ์ของห้องปิดเหมือนตอนรอคำตอบปกติ
- stream จบด้วย `done` → การ์ด**ล็อก**: ไม่มีปุ่มเหลือ แสดงบรรทัดที่ยืนยันแล้ว (รวมป้าย "แก้แล้ว") และข้อความเล็ก "ยืนยันแล้ว" (ตัดสินแล้ว OQ 1)
- stream ล้ม (`error` หรือเน็ตหลุดก่อน `done`) → การ์ด**ไม่ล็อก** บรรทัดที่แก้ยังอยู่ · แสดง "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" แบบเดิม (chat-streaming.md) · กดยืนยันซ้ำได้
- event `verdict` ใน stream ยืนยันยังไม่แสดง (feature แยก · Out of scope) · token ของติวเตอร์แสดงเป็น bubble ตามปกติ

**ถ่ายใหม่**

- กด "ถ่ายใหม่" → การ์ดล็อกแบบไม่มีปุ่ม พร้อมข้อความเล็ก "ส่งรูปใหม่ได้เลย" · เปิดหน้าต่างเลือกรูปของปุ่มแนบรูปใน Composer ทันที (ตัดสินแล้ว OQ 4) · ไม่เรียก `confirmOcr`
- รูปใหม่ส่งผ่าน `POST /sessions/{id}/messages` ตามปกติ · backend ต้องรู้ว่า preview เดิมถูกทิ้ง (Open question 5)

**การ์ดที่ยังไม่ยืนยันมีได้ใบเดียว**

- ขณะที่มีการ์ดรอยืนยัน ช่องพิมพ์ของห้องยังใช้ได้ (ตัดสินแล้ว OQ 7) · ถ้าได้ `ocr_preview` ใบใหม่ การ์ดเก่าที่ยังไม่ยืนยันล็อกพร้อมข้อความ "ส่งรูปใหม่ได้เลย" (เหมือนกด "ถ่ายใหม่")

**ประวัติ (`GET /sessions/{id}`):** `Message.role` ใน api.md ไม่มีประเภทการ์ดยืนยัน จึงไม่มีการ์ดในแชทเก่า · กลับเข้าห้องระหว่างรอยืนยันจะไม่เห็นการ์ด (Open question 8)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | SSE `ocr_preview` | `{"lines": [{"latex": "x^2 - 5x + 6", "confidence": 0.97}, {"latex": "= (x - 2)(x + 3)", "confidence": 0.91}, {"latex": "= x^2 + x - 6", "confidence": 0.95}]}` |
| Output (การ์ด) | การ์ดในรายการข้อความ | "ขอเช็คก่อนว่าอ่านถูกมั้ย ที่เขียนมาคือ" · 1 $x^2-5x+6$ ✎ · 2 … · [ถูกแล้ว ตรวจเลย] [ถ่ายใหม่] |
| Output (transport) | `confirmOcr(lines: string[], signal) → AsyncIterable<SSEEvent>` | `["x^2 - 5x + 6", "= (x - 2)(x - 3)", "= x^2 - 5x + 6"]` (แก้บรรทัด 2, 3) |
| Output (HTTP) | `POST /sessions/{id}/ocr/confirm` body ตาม Open question 5 | ข้อเสนอ: `{"lines": ["…", "…"]}` |

## 4. Acceptance criteria

ใช้ fake transport ทุกข้อ ไม่ใช้ AI จริง · fixture `OCR3` = 3 บรรทัดในตาราง §3

**แสดงการ์ด**

- **AC-1 (AM02)** Given stream ส่ง `ocr_preview` OCR3 → `done` When แสดง Then มีการ์ด `role="region"` ชื่อ "อ่านได้แบบนี้ ถูกไหม" ที่มี 3 บรรทัด เลข 1, 2, 3 · KaTeX source ของแต่ละบรรทัดตรงกับ `latex` ตามลำดับ · มีปุ่ม "แก้บรรทัด 1"…"แก้บรรทัด 3", "ถูกแล้ว ตรวจเลย", "ถ่ายใหม่" · การ์ดไม่มี `data-role`
- **AC-2 (AM02)** Given `ocr_preview` ที่ทุกบรรทัด `confidence = 1` Then การ์ดแสดง (ยืนยันทุกครั้ง · ไม่มีการข้าม)
- **AC-3 (AM02)** Given `ocr_preview` ที่ `confidence` เป็น 0, 0.5, 1 Then ข้อความในการ์ดไม่มีตัวเลข confidence และทุกบรรทัดมี class/attribute เหมือนกัน (ไม่ไฮไลต์)
- **AC-4 (AM02)** Given `ocr_preview` ที่ `lines = []` Then ไม่มีการ์ด
- **AC-5 (AM02 · E1)** Given stream `token tutor "รูปนี้อ่านไม่ออกเลย ถ่ายใหม่ให้หน่อย"` → `done` (ไม่มี `ocr_preview`) Then มี bubble ติวเตอร์ และไม่มีการ์ด
- **AC-6 (TM08)** Given บรรทัดที่ `latex = "\\frac{1"` Then การ์ดยังแสดงครบ และปุ่ม "แก้บรรทัด" ของบรรทัดนั้นกดได้
- **AC-7 (AM02)** Given stream `token tutor "ขอดูก่อนนะ"` → `ocr_preview` → `token tutor "เช็คให้หน่อย"` → `done` Then ลำดับคือ bubble user (รูป), bubble ติวเตอร์ "ขอดูก่อนนะ", การ์ด, bubble ติวเตอร์ "เช็คให้หน่อย" (การ์ดตัดการรวม)

**แก้บรรทัด**

- **AC-8 (AM03)** Given การ์ด OCR3 When กด "แก้บรรทัด 2" Then มีช่องพิมพ์ชื่อ "บรรทัด 2" ค่า `= (x - 2)(x + 3)` และ preview มี KaTeX source เดียวกัน · When พิมพ์เปลี่ยนเป็น `= (x - 2)(x - 3)` Then preview เปลี่ยนตาม
- **AC-9 (AM03)** Given แก้บรรทัด 2 แล้ว When กด "บันทึก" (หรือกด Enter) Then ไม่มีช่องพิมพ์ · บรรทัด 2 แสดง KaTeX `= (x - 2)(x - 3)` และป้าย "แก้แล้ว" · บรรทัด 1, 3 ไม่มีป้าย
- **AC-10 (AM03)** Given แก้บรรทัด 2 แล้ว When กด "ยกเลิก" (หรือกด Esc) Then บรรทัด 2 กลับเป็น `= (x - 2)(x + 3)` ไม่มีป้าย
- **AC-11 (AM03)** Given ช่องพิมพ์บรรทัด 2 เป็น `""` หรือ `"   "` Then ปุ่ม "บันทึก" กดไม่ได้ และ Enter ไม่บันทึก
- **AC-12 (AM02)** Given กำลังแก้บรรทัดใดอยู่ Then ปุ่ม "ถูกแล้ว ตรวจเลย" กดไม่ได้

**ยืนยัน**

- **AC-13 (AM02 · A1)** Given การ์ด OCR3 ไม่แก้อะไร When กด "ถูกแล้ว ตรวจเลย" Then `confirmOcr` ถูกเรียก 1 ครั้งด้วย `["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"]` · ไม่มี bubble user เพิ่ม
- **AC-14 (AM03)** Given แก้บรรทัด 2 เป็น `= (x - 2)(x - 3)` และบรรทัด 3 เป็น `= x^2 - 5x + 6` แล้วบันทึก When กดยืนยัน Then `confirmOcr` ได้ `["x^2 - 5x + 6", "= (x - 2)(x - 3)", "= x^2 - 5x + 6"]`
- **AC-15 (AM02)** Given `confirmOcr` stream `token tutor "บรรทัดสองยังไม่ถูกนะ"` → `done` When กดยืนยัน Then มี bubble ติวเตอร์ข้อความนั้นต่อจากการ์ด · การ์ดไม่มีปุ่มเหลือ และมีข้อความ "ยืนยันแล้ว" · บรรทัดยังแสดงค่าที่ยืนยัน (รวมป้าย "แก้แล้ว")
- **AC-16 (AM02)** Given `confirmOcr` stream ยังไม่จบ Then ปุ่ม "ถูกแล้ว ตรวจเลย", "ถ่ายใหม่", "แก้บรรทัด n" กดไม่ได้ และกดยืนยันซ้ำไม่เรียก `confirmOcr` ครั้งที่สอง
- **AC-17 (AM02)** Given `confirmOcr` stream ส่ง `error` (หรือ throw) ก่อน `done` Then มี alert "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" · การ์ดยังมีปุ่ม · บรรทัดที่แก้ยังอยู่ · กดยืนยันอีกครั้งเรียก `confirmOcr` ด้วยค่าเดิม
- **AC-18 (AM02)** Given `confirmOcr` stream มี `verdict` คั่นระหว่าง token Then bubble ติวเตอร์ไม่แตก และไม่มีข้อความ verdict (feature แยก)

**ถ่ายใหม่ และการ์ดหลายใบ**

- **AC-19 (AM02)** Given การ์ด OCR3 When กด "ถ่ายใหม่" Then `confirmOcr` ไม่ถูกเรียก · การ์ดไม่มีปุ่มเหลือ และมีข้อความ "ส่งรูปใหม่ได้เลย" · หน้าต่างเลือกไฟล์ของ Composer ถูกเปิด (`input[type=file]` ถูก `click()`)
- **AC-20 (AM02)** Given การ์ดใบแรกยังไม่ยืนยัน When stream ใหม่ส่ง `ocr_preview` อีกใบ Then การ์ดใบแรกไม่มีปุ่มและมี "ส่งรูปใหม่ได้เลย" · การ์ดใบใหม่มีปุ่มครบ

**HTTP และของเดิม**

- **AC-21 (AM02)** Given HTTP transport ของ session `s1` When เรียก `confirmOcr(["a", "b"])` Then POST ไป `{API}/sessions/s1/ocr/confirm` ด้วย body ตาม Open question 5 (ข้อเสนอ `{"lines": ["a", "b"]}`) และ yield SSE ที่ได้กลับ
- **AC-22 (TM06)** Given การ์ดยืนยัน Then ไม่มีปุ่มตัวเลือกคำตอบ · ปุ่มในการ์ดมีแค่ "แก้บรรทัด n", "บันทึก", "ยกเลิก", "ถูกแล้ว ตรวจเลย", "ถ่ายใหม่"
- **AC-23** test เดิมผ่านทั้งหมด (chat-streaming AC-7 ไม่มี `ocr_preview` ใน test จึงไม่ต้องแก้ test ที่ review แล้ว)

**AC-boundary:** หน้าเว็บไม่ใช้ threshold (`ocr.always_confirm` เป็นค่าฝั่ง backend · confidence ไม่ถูกอ่าน) · ขอบของ confidence ทดสอบใน AC-2, AC-3 (0, 0.5, 1) · ขอบของจำนวนบรรทัด: 0 (AC-4), 1 และ 3 บรรทัด · **AC-tenant (SA-06):** หน้าเว็บไม่อ่านหรือเขียน DB เอง · backend ตรวจว่า session เป็นของ user ใน `ocr/confirm` (ไม่อยู่ใน feature นี้)

## 5. Data changes

ไม่มีในหน้าเว็บ · backend log บรรทัดที่แก้เพื่อวัด OCR accuracy (AM-03 · ai-orchestration §2.11) อยู่ฝั่ง Junior และต้องมีที่เก็บ (Open question 5)

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `ocr_preview` (มีแล้ว) | — | `{lines: [{latex, confidence}]}` · ยังไม่มีใน OpenAPI → ต้องเพิ่ม schema `OcrPreviewEvent` แล้ว `pnpm gen:api` |
| `POST /sessions/{id}/ocr/confirm` (มีแค่ชื่อใน api.md) | **ยังไม่กำหนด** · ข้อเสนอ `{lines: string[]}` | SSE แบบเดียวกับ `POST /sessions/{id}/messages`: `verdict` → `token`… → `done` · ยังไม่มี stub |
| ทาง "ถ่ายใหม่" | **ยังไม่กำหนด** (Open question 5) | — |

## 7. AI calls

ไม่มีในหน้าเว็บ (`extract_answer` และ checker อยู่ฝั่ง backend)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/OcrConfirmCard.test.tsx` (ใหม่) | unit (component) | AC-1 ถึง AC-6, AC-8 ถึง AC-12, AC-22 |
| `tests/chat/ChatRoomOcr.test.tsx` (ใหม่) | integration (ChatRoom + fake transport) | AC-7, AC-13 ถึง AC-20 |
| `tests/httpTransport.test.ts` (เพิ่ม test) | unit | AC-21 |
| test เดิม | — | AC-23 |

## 9. Out of scope

- แสดงผลตรวจ `verdict` (✓/✗, บรรทัดแรกที่ผิด · AM-05 · S22) · feature แยก
- อัปโหลดรูปจริงผ่าน `POST /sessions/{id}/uploads` (รอ Junior · `room-http.md`)
- แย้งผลตรวจ / อ่านผิดหลังตรวจ (UC-04 A10, E2) · พิมพ์ในแชทตามปกติ ไม่มีปุ่มใหม่
- ข้อความกำกับที่ส่งมากับรูป (A11 · ตัดสินแล้วใน api.md ข้อ 1 ไม่เกี่ยวกับการ์ด)
- การ์ดในประวัติ (Open question 8)

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-28)

1. **การ์ดหลังยืนยัน:** ล็อกไว้ แสดงบรรทัดที่ยืนยัน + "ยืนยันแล้ว" เพื่อย้อนดูได้ว่าส่งอะไรไปตรวจ (AC-15)
2. **แก้หลายบรรทัด:** ทีละบรรทัด · กดแก้บรรทัดอื่นขณะแก้อยู่ = บันทึกบรรทัดเดิมก่อน (ถ้าช่องว่างล้วน = ยกเลิกบรรทัดเดิม)
3. **บรรทัดที่อ่านเกินหรือขาด:** แก้ได้อย่างเดียว ตาม wireframe ที่มีแค่ "✎ แก้" · ลบหรือเพิ่มบรรทัดไม่ได้ ช่องว่างล้วนบันทึกไม่ได้ (AC-11) · ถ้าอ่านผิดมากให้กด "ถ่ายใหม่"
4. **"ถ่ายใหม่":** ล็อกการ์ด + เปิดหน้าต่างเลือกรูปทันที (AC-19)
7. **พิมพ์ในแชทขณะการ์ดรอยืนยัน:** พิมพ์ได้ตามปกติ การ์ดค้างไว้ ไม่บังคับ flow · ข้อความที่พิมพ์ถือเป็นอะไรฝั่ง backend อยู่ในข้อ 5

ให้ Junior ตอบ (api.md · ไฟล์ร่วม)

5. **`ocr/confirm` และ "ถ่ายใหม่":** body ข้อเสนอ `{lines: string[]}` (ส่งทุกบรรทัดตามลำดับ backend เทียบกับ preview เองเพื่อ log AM-03) · ทางยกเลิก preview: (ก) `POST /sessions/{id}/ocr/discard` (ข) รูปใหม่หรือข้อความใหม่ทับ preview เดิมเอง ไม่ต้องมี endpoint (ค) `ocr/confirm` รับ `{action: "retake"}` · ข้อความที่พิมพ์ขณะ preview ค้าง (May เลือกให้พิมพ์ได้ · ข้อ 7) backend ถือเป็นอะไร: คำตอบแทนรูป, คำถามปกติที่ preview ยังค้าง, หรือทิ้ง preview · log บรรทัดที่แก้เก็บที่ไหน (`messages.extracted_text` ของข้อความรูป หรือตารางใหม่) · ต้องเพิ่ม `OcrPreviewEvent` และ `OcrConfirmRequest` ใน OpenAPI และ stub
6. **รูปแบบ `latex`:** LaTeX ล้วนไม่มี `$` เหมือน `problem.text_latex` ใช่ไหม (เพิ่มใน api.md Conventions)
8. **การ์ดในประวัติ:** กลับเข้าห้องระหว่างรอยืนยัน (UC-03 E1) จะเห็นการ์ดได้จากไหน · แนวเดียวกับ problem-card OQ 2 (#69)

## 11. Spec changes needed

- **api.md** (ไฟล์ร่วม · Junior): Open questions 5, 6, 8
- **chat-room-ui.md** §2 "ปุ่มที่กดได้ในห้องมีแค่: แนบรูป, ส่ง, เอารูปที่แนบออก, ลิงก์ออกจากห้อง" → เพิ่มปุ่มในการ์ดยืนยัน (ไม่ใช่ปุ่มตัวเลือกคำตอบ · TM-06 ยังเป็นจริง)
- **chat-streaming.md** §2 ตาราง event: `ocr_preview` ไม่ถูกข้ามแล้ว (แสดงตาม `ocr-confirm-card.md`)
