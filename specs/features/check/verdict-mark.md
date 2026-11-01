# Feature: ห้องติว · ผลตรวจ ✓/✗

| | |
|---|---|
| Area | checker (หน้าเว็บ) |
| Requirements | AM-05 (บอกบรรทัดแรกที่ผิด) · AM-06 (ประเภทความผิด · ไม่แสดง ดู OQ 3) · TM-20 · TM-06 |
| Owner | May |
| Reviewer | Junior (OQ 6) |
| Status | approved by May 2026-10-28 (owner · OQ 1–4) · รอ Junior ตอบ OQ 5, 6 (api.md) |
| Related system spec | api.md "SSE events" (`verdict`) · ai-orchestration.md §2.4.5 ("ส่ง SSE `verdict` ก่อน tutor เริ่มพิมพ์"), §2.2.4 (การสอนตาม error type) · `check/merge-rules.md` §2 (ค่าของ `verdict`, `error_type`, `first_wrong_line`) · use-cases.md UC-04 ขั้น 5, 8, A4, A5, A7, A8 · `check/ocr-confirm-card.md` (stream ของ `ocr/confirm`) · `tutor/chat-streaming.md` AC-7 · wireframe S16, S22 (ยังไม่มีเครื่องหมาย ต้องแก้) |

## 1. Context

เมื่อผู้ใช้ตอบโจทย์ที่ค้าง (พิมพ์ หรือยืนยันลายมือ) backend ตรวจด้วย SymPy + LLM แล้วรวมผลด้วย merge rules ได้ `{verdict, first_wrong_line, error_type}` และส่ง event `verdict` **ก่อน**ติวเตอร์เริ่มพิมพ์ (ai-orchestration §2.4.5) · UC-04 ขั้น 5 "ระบบแสดง ✗ ก่อนที่ติวเตอร์จะเริ่มพิมพ์" · ตอนนี้หน้าเว็บข้าม `verdict` (chat-streaming.md AC-7, ocr-confirm-card.md AC-18) ผู้ใช้จึงรู้ผลจากคำพูดของติวเตอร์เท่านั้น · feature นี้แสดงผลตรวจเป็นแถบสั้นๆ ในแชท ค่าทุกค่ามาจาก API หน้าเว็บไม่ตัดสินเอง (apps/web/CLAUDE.md)

## 2. Behavior

**ข้อมูล:** `verdict` = `{verdict, first_wrong_line, error_type}` (api.md) · ค่าตาม `merge-rules.md`:

- `verdict`: `correct` · `correct_with_flaw` · `incomplete` · `incorrect`
- `first_wrong_line`: integer นับจาก 1 หรือ `null`
- `error_type`: `calculation` · `sign` · `wrong_method` · `concept` · `prerequisite` · `no_answer` หรือ `null` (ชื่อจริงใน API ต้องยืนยัน · OQ 6)

**แสดงที่ไหน**

- event `verdict` ใน stream ใดก็ได้ของห้อง (`POST /sessions/{id}/messages` และ `POST /sessions/{id}/ocr/confirm`) → เพิ่ม**แถบผลตรวจ**ต่อท้าย ณ ตำแหน่งที่ event มา · ไม่ใช่ bubble (ไม่มี `data-role`) · token ที่ตามมาเริ่ม bubble ใหม่ (ตัดการรวมแบบเดียวกับการ์ด · `problem-card.md` AC-6)
- ปกติ `verdict` มาก่อน token แรกของติวเตอร์ จึงอยู่เหนือคำอธิบายของติวเตอร์
- แถบผลตรวจเป็น `role="status"` ชื่อ (`aria-label`) "ผลตรวจ" · ใส่ `data-verdict` เท่ากับค่า `verdict` ที่ได้

**ข้อความ** (ตัดสินแล้ว OQ 1, 2) · ข้อความทั้งหมดอยู่ใน `strings.ts`

| `verdict` | เครื่องหมาย | ข้อความ | เมื่อมี `first_wrong_line = n` |
|---|---|---|---|
| `correct` | ✓ | "ถูก" | (ไม่มี · merge rules ให้ `null` เสมอ) |
| `correct_with_flaw` | ✗ | "คำตอบสุดท้ายถูก แต่มีบรรทัดที่ผิด" | ต่อท้าย " · บรรทัด n" |
| `incomplete` | ✗ | "ค่าถูก แต่ยังไม่อยู่ในรูปที่โจทย์ถาม" | (ไม่มี · merge rules ให้ `null` เสมอ) |
| `incorrect` | ✗ | "ยังไม่ถูก" | ต่อท้าย " · บรรทัด n" |

- `correct_with_flaw` แสดง ✗ เพราะนับเป็นผิดสำหรับ mastery (merge rules ข้อ 4 · UC-04 A5)
- `first_wrong_line` แสดงเป็นตัวเลขจาก API ตรงๆ หน้าเว็บไม่คำนวณ · `null` หรือไม่มี field → ไม่ต่อท้าย
- **ไม่แสดง `error_type`** ติวเตอร์อธิบายเองในคำพูด (ตัดสินแล้ว OQ 3)
- **ไม่มีคำตอบ** (`incorrect` + `error_type = no_answer` · UC-04 A8): ไม่แสดงแถบ เพราะผู้ใช้บอกเองว่าทำไม่ได้ แสดง ✗ ซ้ำจะดูเหมือนตำหนิ ติวเตอร์ทำขั้นแรกให้ดูตามปกติ (ตัดสินแล้ว OQ 4)
- `verdict` ที่ไม่รู้จัก หรือ payload ผิดรูป → ไม่แสดงแถบ และ stream ไปต่อตามปกติ (ห้าม crash · chat-streaming.md §2)
- ไม่มีปุ่มในแถบ (TM-06) · แย้งผลตรวจทำโดยพิมพ์ในแชท (UC-04 A10)

**ประวัติ (`GET /sessions/{id}`):** `Message.role` ใน api.md ไม่มีประเภทผลตรวจ จึงไม่มีแถบในแชทเก่า (OQ 5)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | SSE `verdict` | `{"verdict": "incorrect", "first_wrong_line": 2, "error_type": "sign"}` |
| Output | แถบผลตรวจในรายการข้อความ | "✗ ยังไม่ถูก · บรรทัด 2" |

## 4. Acceptance criteria

ใช้ fake transport ทุกข้อ ไม่ใช้ AI จริง

**ข้อความของแต่ละผล**

- **AC-1 (AM05)** Given `verdict` ตามตาราง Then แถบ `role="status"` ชื่อ "ผลตรวจ" มี `data-verdict` และข้อความตามตาราง (ตารางทดสอบ):

  | payload | ข้อความที่ต้องเห็น |
  |---|---|
  | `correct`, `null`, `null` | "✓ ถูก" |
  | `correct_with_flaw`, `3`, `"sign"` | "✗ คำตอบสุดท้ายถูก แต่มีบรรทัดที่ผิด · บรรทัด 3" |
  | `incomplete`, `null`, `"concept"` | "✗ ค่าถูก แต่ยังไม่อยู่ในรูปที่โจทย์ถาม" |
  | `incorrect`, `2`, `"sign"` | "✗ ยังไม่ถูก · บรรทัด 2" |
  | `incorrect`, `1`, `"calculation"` | "✗ ยังไม่ถูก · บรรทัด 1" |
  | `incorrect`, `null`, `"concept"` | "✗ ยังไม่ถูก" |

- **AC-2 (AM06)** Given `error_type` ใดก็ตามใน 6 ค่า Then ข้อความในแถบไม่มีชื่อ error type (ทั้งภาษาอังกฤษและคำแปล)
- **AC-3 (AM06 · A8)** Given `incorrect` + `error_type = "no_answer"` Then ไม่มีแถบ
- **AC-4 (TM20)** Given `verdict = "maybe"` หรือ payload `{}` Then ไม่มีแถบ และ token ที่ตามมาแสดงเป็น bubble ตามปกติ ไม่มี alert
- **AC-5 (TM06)** Given แถบผลตรวจใดก็ตาม Then ไม่มีปุ่มในแถบ

**ตำแหน่งในแชท**

- **AC-6 (AM05)** Given ส่ง "(x-7)(x+7)" แล้ว stream `verdict correct` → `token tutor "ถูกต้อง"` → `done` Then ลำดับคือ bubble user, แถบผลตรวจ "✓ ถูก", bubble ติวเตอร์ "ถูกต้อง"
- **AC-7 (AM05)** Given stream `token tutor "โอเค "` → `verdict incorrect 2` → `token tutor "บรรทัดสองยังไม่ถูก"` → `done` Then ลำดับคือ bubble user, bubble ติวเตอร์ "โอเค", แถบผลตรวจ, bubble ติวเตอร์ "บรรทัดสองยังไม่ถูก" (แถบตัดการรวม)
- **AC-8 (AM05)** Given การ์ดยืนยันลายมือ (`ocr-confirm-card.md`) When กด "ถูกแล้ว ตรวจเลย" แล้ว stream ยืนยันส่ง `verdict incorrect 2` → `token tutor` → `done` Then ลำดับคือ การ์ด (ยืนยันแล้ว), แถบผลตรวจ "✗ ยังไม่ถูก · บรรทัด 2", bubble ติวเตอร์
- **AC-9 (AM05 · UC-04 ขั้น 8)** Given ตอบสองข้อในสอง stream ได้ `incorrect` แล้ว `correct` Then มีแถบผลตรวจ 2 อันตามลำดับ "✗ …", "✓ ถูก" อันเก่าไม่เปลี่ยน

**ของเดิม**

- **AC-10** test เดิมผ่าน **ยกเว้น 2 ตัวที่ตรวจว่า `verdict` ไม่แสดง** ซึ่งต้องปรับ (ต้องให้ May อนุมัติ เพราะ review แล้ว):
  - chat-streaming AC-7 "skips events this feature does not show…": ตัดบรรทัด `verdict` ออก แบบเดียวกับที่ตัด `progress_card` และ `problem` (event ที่ไม่รู้จักยังอยู่)
  - ocr-confirm-card AC-18 "a verdict inside the confirm reply…": เปลี่ยนเป็นตรวจว่าแถบผลตรวจอยู่ระหว่างการ์ดกับ bubble ติวเตอร์ (= AC-8 ของ spec นี้) หรือตัด `verdict` ออก

**AC-boundary:** ไม่มี threshold · ขอบของ `first_wrong_line`: 1 (บรรทัดแรก), n > 1, `null` (AC-1) · **AC-tenant (SA-06):** ไม่เกี่ยว หน้าเว็บไม่อ่านหรือเขียน DB

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ใช้ `verdict` ที่มีอยู่ (api.md) · ยังไม่มีใน OpenAPI → type เขียนเองชั่วคราวแบบเดียวกับ `OcrPreviewData` จนกว่าจะมี `VerdictEvent` (OQ 6)

## 7. AI calls

ไม่มีในหน้าเว็บ

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/VerdictMark.test.tsx` (ใหม่) | unit (component) | AC-1 ถึง AC-5 |
| `tests/chat/ChatRoomVerdict.test.tsx` (ใหม่) | integration | AC-4, AC-6 ถึง AC-9 |
| test เดิม | — | AC-10 |

## 9. Out of scope

- แสดง `error_type` (ตัดสินแล้ว OQ 3) และ `evidence` (ไม่อยู่ใน SSE)
- ไฮไลต์บรรทัดที่ผิดในการ์ดยืนยันลายมือ (ตัดสินแล้ว OQ 2: ไม่ทำ)
- แย้งผลตรวจ (UC-04 A10) · พิมพ์ในแชทตามปกติ
- ผลตรวจในประวัติ (OQ 5)

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-28)

1. **รูปแบบ:** แถบเล็กบรรทัดเดียวเหนือคำพูดติวเตอร์ เช่น "✗ ยังไม่ถูก · บรรทัด 2"
2. **บรรทัดที่ผิด:** บอกเลขบรรทัดในแถบ (AM-05) · ไม่ไฮไลต์ในการ์ดยืนยันลายมือ
3. **ประเภทความผิด:** ไม่แสดง ติวเตอร์อธิบายเอง (AC-2)
4. **ไม่ได้ตอบ (`no_answer`):** ไม่แสดงแถบ (AC-3)

ให้ Junior ตอบ (api.md · ไฟล์ร่วม)

5. **ผลตรวจในประวัติ:** กลับเข้าห้องแล้วจะเห็นผลตรวจเดิมไหม · แนวเดียวกับโจทย์ในประวัติ (#69) และการ์ดยืนยัน (#77 OQ 8)
6. **ชื่อค่าใน API:** `error_type` ใช้ `wrong_method` และ `no_answer` (snake_case) ตาม `merge-rules.md` ใช่ไหม · ขอ `VerdictEvent` ใน OpenAPI

## 11. Spec changes needed

- **chat-streaming.md** AC-7: `verdict` ไม่ถูกข้ามแล้ว (ตัดออกจาก test · AC-10)
- **ocr-confirm-card.md** AC-18 และ §2 "event `verdict` … ยังไม่แสดง": เปลี่ยนเป็นอ้าง spec นี้
- **wireframe** S16 (ตอบถูก) และ S22 (ตอบผิด): เพิ่มแถบผลตรวจ (May)
- **api.md** (Junior): OQ 5, 6
