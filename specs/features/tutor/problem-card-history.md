# Feature: การ์ดโจทย์อยู่ในประวัติแชท (กลับเข้าห้องแล้วยังตอบต่อได้ · goal อาจารย์ข้อ 4)

| | |
|---|---|
| Area | tutor |
| Requirements | TM-13, TM-06, AM-02 |
| Owner | May (หน้าเว็บ) · Jam (API · §6) |
| Reviewer | May (spec + test หน้าเว็บ) · Jam (สัญญาข้อมูล §6 และ API) |
| Status | approved 2026-11-17 (May ok spec) |
| Related system spec | `room-problems-db.md` §10 ข้อ 3 (ข้อเสนอเดิมของ Jam: `messages` `role = "card"`, `card = {"problem": {...}}`) · `room-answers-db.md` (ข้อต่อไปหลังตรวจ) · api.md `Message` · SSE `problem` (`ProblemEvent`) · `problem-card.md` · `answer-canvas.md` §2 B (canvas ตามการ์ดโจทย์ใบล่าสุด) · `use-cases.md` UC-03 E1 · goal อาจารย์ 17 พ.ย. ข้อ 4 |

## 1. Context

การ์ดโจทย์มาทาง SSE `problem` เท่านั้น ไม่ได้บันทึกใน `messages` · `GET /sessions/{id}` จึงคืนแค่ข้อความ · รีเฟรชหรือกลับเข้าห้อง (`sessions/active` · TM-13) แล้วการ์ดโจทย์หาย และ canvas หายตามเพราะ canvas อยู่ได้เมื่อมีการ์ดโจทย์ (answer-canvas.md §2 B) · ผู้ใช้ไม่เห็นว่าค้างข้อไหน ทั้งที่ API ยังจำโจทย์ค้าง · Jam เลือกทาง (ข) 17 พ.ย.: บันทึกการ์ดโจทย์เป็นข้อความ `role = "card"` ทุกครั้งที่ส่ง event `problem` (Jam ทำ API) · feature นี้คือฝั่งหน้าเว็บ: แสดงการ์ดโจทย์จากประวัติแบบเดียวกับการ์ดที่มาทาง SSE · และกำหนดรูปร่างข้อมูลให้ API (§6)

## 2. Behavior

### 2.1 แยกชนิดการ์ดในประวัติ (หน้าเว็บ)

ข้อความ `role = "card"` จาก `GET /sessions/{id}` (`room.messages`):

1. `card.problem` เป็น object ที่มี `problem_id` (string), `text_latex` (string), `difficulty` (number), `purpose` (string) → **การ์ดโจทย์** (`ProblemCard`) ที่ตำแหน่งของข้อความนั้นในแชท (เรียงตาม `created_at` แบบข้อความอื่น) · เหมือนการ์ดจาก SSE `problem` ทุกอย่าง
2. `card.problem` มีแต่รูปร่างไม่ครบ (ขาด field หรือชนิดผิด) → ไม่แสดงการ์ดนั้น (ข้ามแบบ `chat-room-ui.md` AC-4 ที่ไม่แสดงการ์ดว่าง) · ข้อความอื่นแสดงปกติ · ไม่ crash
3. `card` ที่ไม่มี key `problem` → **การ์ดความคืบหน้า** แบบเดิม (ไม่เปลี่ยน)
4. การแยกทำครั้งเดียวตอนรับ `room` (ข้อความที่สร้างในเบราว์เซอร์ระหว่าง session มาจาก SSE อยู่แล้ว)

### 2.2 canvas และการตอบ

การ์ดโจทย์จากประวัติเป็น "การ์ดโจทย์" ตาม answer-canvas.md ทุกข้อ:

1. canvas อยู่ท้ายแชทเมื่อมีการ์ดโจทย์อย่างน้อย 1 ใบ (§2 B ข้อ 16) · หัวกล่องเป็นโจทย์ของการ์ดใบล่าสุด
2. การ์ดโจทย์ใหม่จาก SSE ที่ `problem_id` ต่างจากใบล่าสุดในประวัติ → canvas เริ่มใหม่ตามกฎเดิม (§2 B ข้อ 18)
3. รูปที่ส่งจาก canvas / 📷 จำ `problem_id` ของการ์ดใบล่าสุด (answer-canvas.md §2 E) รวมการ์ดจากประวัติ

### 2.3 ไม่เปลี่ยน

- การ์ดความคืบหน้าตอนกลับเข้าห้อง: UC-03 E1 บอกว่ากลับเข้าห้องเดิม "ไม่มี progress card ใบใหม่" · API ไม่ต้องบันทึกการ์ดความคืบหน้าใน feature นี้
- ห้องเดโม่ในเครื่อง (`APP_ENV=local` ไม่มี token): ไม่มี DB · ไม่เปลี่ยน
- ไม่มี `card.problem` ในประวัติเลย (API ก่อนงานของ Jam) → ทำงานเหมือนวันนี้ทุกอย่าง · merge หน้าเว็บก่อน API ได้

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `Room.messages[]` ที่มี `role = "card"`, `card = {"problem": ProblemEvent}` | `{"id": "…", "role": "card", "content": null, "card": {"problem": {"problem_id": "9b…", "text_latex": "\\lim_{x\\to 2} \\frac{x^2-4}{x-2}", "difficulty": 2, "purpose": "practice"}}, "created_at": "…"}` |
| Output (UI) | `ProblemCard` ที่ตำแหน่งนั้น + canvas ท้ายแชท | |

## 4. Acceptance criteria

Vitest + Testing Library · `ChatRoom` กับ `room.messages` ที่กำหนด · `TutorRoom` กับ `fetch` ปลอม · ไม่มี AI จริง

- **AC-1 (TM-13)** Given ประวัติมีข้อความ tutor แล้วการ์ด `{problem: P1}` When เปิดห้อง Then เห็นการ์ดโจทย์ของ P1 (หัว "โจทย์" + KaTeX ของ `text_latex`) หลังข้อความ tutor · ไม่มีการ์ดความคืบหน้าจากข้อความนั้น
- **AC-2 (TM-15)** Given ประวัติมีการ์ดความคืบหน้า (card ไม่มี `problem`) Then แสดงการ์ดความคืบหน้าเหมือนเดิม
- **AC-3 (TM-13, TM-06)** Given ประวัติมีการ์ด `{problem: P1}` Then มี canvas "เขียนคำตอบ" ท้ายแชท 1 อัน และหัวกล่องเป็นโจทย์ P1
- **AC-4 (TM-06)** Given ประวัติมีการ์ด P1 แล้ว P2 Then มี canvas 1 อัน หัวกล่องเป็น P2 · การ์ดโจทย์ทั้ง 2 ใบยังอยู่
- **AC-5 (TM-06)** Given ประวัติมีการ์ด P1 When SSE ส่ง `problem` P2 Then หัว canvas เป็น P2
- **AC-6 (AM-02)** Given ประวัติมีการ์ด P1 When ส่งรูปจาก canvas และได้การ์ดยืนยันลายมือ แล้วกด "ถ่ายใหม่" Then กลับไปที่ canvas (ไม่เปิดตัวเลือกไฟล์) เพราะรูปจำ `problem_id` ของ P1 (answer-canvas.md §2 E)
- **AC-7** Given การ์ด `{problem: {problem_id: "p1"}}` (ไม่มี `text_latex`) หรือ `{problem: "x"}` Then ไม่มีการ์ดโจทย์และไม่มี canvas · ข้อความอื่นในประวัติแสดงครบ · ไม่ throw
- **AC-8 (TM-13 · TutorRoom)** Given `sessions/active` → S, `GET /sessions/S` คืนข้อความ tutor + การ์ด `{problem: P1}` When เปิดหน้าห้อง Then เห็นการ์ดโจทย์ P1 และ canvas · ไม่มี request สร้าง session ใหม่

ไม่มี threshold · หน้าเว็บไม่อ่านหรือเขียน DB เอง (RLS ของ `messages` มีอยู่แล้ว · การแยก tenant เป็นของ API) จึงไม่มี AC-tenant ฝั่งเว็บ

## 5. Data changes

ไม่มี migration · ใช้ `messages.role = 'card'` และ `messages.card jsonb` ที่มีอยู่ (`0001`) · ความหมายของ `card` กว้างขึ้น: การ์ดความคืบหน้า **หรือ** `{"problem": …}`

## 6. API / SSE changes (สัญญาให้ Jam · Jam ทำ API ใน PR แยก)

1. ทุกครั้งที่ห้องในทางที่มี token ส่ง SSE `problem` ให้บันทึกข้อความ 1 แถว: `role = "card"`, `content = null`, `card = {"problem": <payload เดียวกับ event `problem` ทุก field>}` · บันทึก**ก่อน**ข้อความ tutor ถัดไป (ลำดับ `created_at` ต้องตรงกับที่ผู้ใช้เห็นใน SSE)
2. ที่ที่ส่ง `problem` ตอนนี้ (Jam ยืนยันรายการ): เปิดห้อง (`room_problems.opening_events`) · ข้อต่อไปหลังตรวจคำตอบพิมพ์ (`room-answers-db.md`) · หลังตรวจรูป / ยืนยันลายมือ (`photo_check`)
3. `GET /sessions/{id}` คืนแถวนี้ใน `messages` ตามปกติ · `Message.card` เป็น object อยู่แล้ว ไม่ต้องเปลี่ยน schema
4. id ของแถวนี้อยู่ใน `done.message_ids` หรือไม่: Jam ตัดสิน (หน้าเว็บไม่ใช้)
5. ห้องเดโม่ในเครื่องที่ไม่มี token: ไม่เปลี่ยน

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `apps/web/tests/chat/ChatRoomProblemHistory.test.tsx` (ใหม่) | unit (Vitest) | AC-1 ถึง AC-7 |
| `apps/web/tests/chat/RoomPageProblemHistory.test.tsx` (ใหม่ · `TutorRoom` + `fetch` ปลอม) | unit | AC-8 |
| test เดิมทั้งหมดผ่าน | unit | §2.3 |
| test ฝั่ง API (Jam · PR แยก) | unit / integration | §6 |
| ลองเส้นจริงหลัง API ของ Jam: เปิดห้อง → การ์ดโจทย์ → รีเฟรช → การ์ด + canvas ยังอยู่ | มือ | ทั้งหมด |

## 9. Out of scope

- บันทึกการ์ดความคืบหน้า, การ์ดยืนยันลายมือ และผลตรวจ (verdict) ในประวัติ · กลับเข้าห้องแล้วเห็นแค่ข้อความ + การ์ดโจทย์
- ตัดสินว่าโจทย์ในการ์ดจบแล้วหรือยัง (`problems.ended_at`) · §10 ข้อ 1
- งาน API (Jam · §6)

## 10. Open questions

1. **(Jam) การ์ดใบล่าสุดเป็นโจทย์ที่จบแล้ว:** ปกติหลังตรวจจะมีโจทย์ข้อต่อไปเสมอ · ถ้าสร้างข้อต่อไปไม่ผ่าน (`room.no_problem`) การ์ดใบล่าสุดในประวัติเป็นโจทย์ที่จบแล้ว แต่ canvas ยังขึ้น (แบบเดียวกับวันนี้ใน SSE) · ข้อเสนอ: ไม่ทำอะไรใน feature นี้ · ถ้าต้องการ API ใส่ `card.problem.ended: true` ภายหลัง
2. **(Jam) `done.message_ids`** รวม id ของการ์ดไหม (§6 ข้อ 4)

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `specs/system/api.md` (ไฟล์กลาง) | `Message.card`: การ์ดความคืบหน้า หรือ `{"problem": ProblemEvent}` · ห้องบันทึกการ์ดโจทย์ทุกครั้งที่ส่ง `problem` | Jam · PR ของ API · บอกกลุ่มก่อน merge |
| `specs/features/tutor/room-problems-db.md` §10 ข้อ 3 | ปิดแล้ว: ทาง (ข) · หน้าเว็บตาม spec นี้ | Jam · PR ของ API (หรือ May ใน PR นี้ถ้า Jam ok) |
