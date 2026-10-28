# Feature: ห้องติว · การ์ดโจทย์

| | |
|---|---|
| Area | tutor |
| Requirements | TM-04, TM-08, TM-14, TM-06 · AM-11 (โจทย์ที่ส่งมาไม่มีเฉลย) |
| Owner | May |
| Reviewer | Junior |
| Status | approved by May 2026-10-21 (owner) · รอ Junior review ใน PR (OQ 2) |
| Related system spec | api.md "SSE events" (`problem`), Conventions (`problem.text_latex` เป็น LaTeX ล้วน) · ai-orchestration.md §2.2.4 (ที่มาของโจทย์), §2.2.8 ("การ์ดโจทย์ render KaTeX") · wireframe S15 · `progress-card.md` (การ์ดตัดการรวม bubble) |

## 1. Context

เมื่อ directive ต้องการโจทย์ใหม่ backend สร้างโจทย์พร้อมเฉลยที่ verify แล้ว เก็บลง `problems` แล้วส่ง event `problem` (ไม่มีเฉลย) ให้หน้าเว็บ (ai-orchestration §2.2.4) · ตอนนี้หน้าเว็บข้าม event นี้ (chat-streaming AC-7) · ตอนเปิดห้อง stub ส่ง `progress_card` → `token` "สวัสดี" → `problem` → `done` จึงไม่เห็นโจทย์ข้อแรก · feature นี้แสดงโจทย์เป็นการ์ดตาม api.md §2.2.8

## 2. Behavior

**ข้อมูล:** `{problem_id, text_latex, difficulty, purpose}` (api.md) · `text_latex` เป็น LaTeX ล้วนไม่มี `$` (api.md Conventions)

**หน้าตา** (May ตัดสิน 2026-10-21: มีแค่โจทย์)

- การ์ดมีหัวสั้นๆ "โจทย์" และสมการจาก `text_latex` render ด้วย `Tex` แบบ block (`display`) · ไม่ผ่าน `MessageText` เพราะไม่มีตัวคั่น
- **ไม่แสดง** `difficulty` และ `purpose` · ติวเตอร์บอกเองในข้อความ (เช่น "ลองข้อนี้ดูก่อน")
- ไม่มีปุ่มใดๆ ในการ์ด · ไม่มีปุ่มตัวเลือกคำตอบ (TM-06) · ไม่มีตัวจับเวลา (TM-14)
- `role="region"` และ `aria-label="โจทย์"` (ไม่ใช้ `group` เพื่อไม่ชนกับการ์ดความคืบหน้าที่ test ของ `progress-card.md` นับด้วย `role="group"`) · ใส่ `data-problem-id` เท่ากับ `problem_id`
- `text_latex` ว่าง → ไม่แสดงการ์ด

**แสดงตรงไหน**

- event `problem` ระหว่าง stream (ตอนเปิดห้องและตอนตอบ) → เพิ่มการ์ดต่อท้าย ณ ตำแหน่งที่ event มา · ไม่ใช่ bubble (ไม่มี `data-role`) · ข้อความติวเตอร์ที่ตามมาเป็น bubble ใหม่ (ตัดการรวมแบบเดียวกับ `progress-card.md` AC-9)
- **ประวัติ (`GET /sessions/{id}`):** `Message.role` ใน api.md ไม่มีประเภทโจทย์ จึงไม่มีการ์ดโจทย์ในแชทเก่า (Open question 2)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | SSE `problem` | `{"problem_id": "p1", "text_latex": "x^2 - 49", "difficulty": 1, "purpose": "probe"}` |
| Output | การ์ดโจทย์ในรายการข้อความ | "โจทย์" + $$x^2-49$$ |

## 4. Acceptance criteria

- **AC-1 (TM08)** Given event `problem` ที่ `text_latex = "x^2 - 49"` When แสดงการ์ด Then มีการ์ด `role="region"` ชื่อ "โจทย์" ที่มี KaTeX แบบ block 1 ชิ้นซึ่ง source คือ `x^2 - 49` และ `data-problem-id="p1"`
- **AC-2 (TM04)** Given การ์ดโจทย์ Then ไม่มีข้อความ `difficulty` หรือ `purpose` (ไม่มีตัวเลข 1 ในหัวการ์ด, ไม่มีคำว่า "probe")
- **AC-3 (TM06)** Given การ์ดโจทย์ Then ไม่มีปุ่มในการ์ด
- **AC-4 (TM04)** Given `text_latex = ""` Then ไม่มีการ์ด
- **AC-5 (TM04)** Given stream เปิดห้อง `room_session_start.txt` (`progress_card` → `token tutor "สวัสดี"` → `problem` → `done`) Then ลำดับคือ การ์ดความคืบหน้า, bubble ติวเตอร์ "สวัสดี", การ์ดโจทย์
- **AC-6 (TM04)** Given stream ตอบ `token tutor "ถูก ข้อต่อไป"` → `problem` → `token tutor "ลองดูนะ"` → `done` Then ลำดับคือ bubble user, bubble ติวเตอร์ "ถูก ข้อต่อไป", การ์ดโจทย์, bubble ติวเตอร์ "ลองดูนะ" (การ์ดตัดการรวม)
- **AC-7 (TM04)** Given `problem` ที่ `text_latex` ผิด syntax (เช่น `\frac{1`) Then การ์ดยังแสดง (KaTeX `throwOnError: false` แสดง source สีแดงตาม `Tex` เดิม) ไม่พังทั้งห้อง
- **AC-8** test เดิมผ่าน · chat-streaming AC-7 (ข้าม `problem`, `verdict`, event ที่ไม่รู้จักโดย bubble ไม่แตก) **ต้องตัดบรรทัด `problem` ออก** แบบเดียวกับที่ทำกับ `progress_card` ใน `progress-card.md` (ต้องให้ May อนุมัติ เพราะเป็น test ที่ review แล้ว)

**AC-boundary:** ไม่มี threshold · **AC-tenant (SA-06):** ไม่เกี่ยว

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ใช้ `problem` ที่มีอยู่ (api.md)

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/ProblemCard.test.tsx` (ใหม่) | unit (component) | AC-1 ถึง AC-4, AC-7 |
| `tests/chat/ChatRoomStream.test.tsx` (เพิ่ม test) | integration | AC-5, AC-6 |
| test เดิม | — | AC-8 |

## 9. Out of scope

- ส่งคำตอบผูกกับ `problem_id` (backend รู้ว่าโจทย์ไหนค้างอยู่แล้ว)
- การ์ดผลตรวจ `verdict` (feature แยก)
- โจทย์ในประวัติ (Open question 2)

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-21)

1. ไม่แสดง `difficulty` และ `purpose` (AC-2)

ให้ Junior ตอบ (reviewer)

2. **โจทย์ในประวัติ:** `Message.role` ไม่มีประเภทโจทย์ · กลับเข้าห้อง (UC-03 E1 "โจทย์ที่ค้างยังรอคำตอบ") จะเห็นโจทย์ได้จากไหน · ทางเลือก: (ก) บันทึกโจทย์เป็น message role ใหม่ `problem` พร้อม `problem` object แบบเดียวกับ `card` (ข) tutor เขียนโจทย์ซ้ำในข้อความ (ค) `Room` ส่ง `pending_problem` มาแยก

## 11. Spec changes needed

- **api.md** (ไฟล์ร่วม) ตาม Open question 2
- **chat-streaming.md** AC-7: `problem` ไม่ถูกข้ามแล้ว
