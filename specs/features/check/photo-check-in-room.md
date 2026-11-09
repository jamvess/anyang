# Feature: ส่งรูปคำตอบในห้องแล้วได้ผลตรวจจริง (P1 + P2 เข้าห้องแชท)

| | |
|---|---|
| Area | checker |
| Requirements | TM-06, AM-01, AM-02, AM-03, AM-04, AM-05, AM-06, AM-07, TM-21, SA-06 |
| Owner | Jam (item of Junior · ช่วง solo 2026-11-08) |
| Reviewer | Jam (AI) · Junior (โครงสร้าง backend ย้อนหลัง · §10) |
| Status | implemented 2026-11-08 (PR #114 · บน staging ยังเป็น stub จนกว่าจะมี Storage · §2.4) · approved 2026-11-08 (Jam · §10 ข้อ 1–2 ตัดสินแล้ว · ข้อ 3–8 ใช้ข้อเสนอไปก่อน รอ Junior ดูย้อนหลัง) |
| Related system spec | ai-orchestration.md §2.2.3 (layer 6, 8), §2.2.4 (การสอนตาม error type), §2.2.5 (รูป), §2.4 (checker), §2.10 (degrade) · api.md "ห้องติว" (`POST /sessions/{id}/messages`, v1.7 `/uploads` + `/ocr/confirm`, SSE `ocr_preview` + `verdict`) · `config/learning.yaml` → `ocr.always_confirm`, `checker.*` · `config/ai.yaml` → `extract_answer`, `check_answer`, `guards.max_image_mb` · use-cases.md UC-04 · P1.md · P2.md · features: `check-answer-classifier.md`, `merge-rules.md`, `sympy-service.md`, `ocr-confirm-card.md`, `verdict-mark.md`, `room-photo-send.md`, `tutor-reply-stream.md` |

## 1. Context

หน้าเว็บส่งรูปวิธีทำได้แล้วและแสดงการ์ดยืนยันลายมือกับแถบผลตรวจได้ (`room-photo-send.md`, `ocr-confirm-card.md`, `verdict-mark.md`) แต่ API ยังตอบด้วย stub: `ocr_preview` กับ `verdict` เป็นค่าตายตัว · ส่วน AI ที่ต้องใช้มีครบแล้วจาก PoC: `extract_answer/v1` อ่านลายมือ (P1 · 95.2% ของบรรทัด) และ `app/services/checker.py` ตรวจคำตอบ (P2 · verdict 100%) · feature นี้ต่อสองอย่างนี้เข้า endpoint ของห้องตาม UC-04 ขั้น 1–6 · ส่วนที่ต้องใช้ Storage และ DB จริงยังไม่มี (ของ Junior · §9, §10) จึงเข้าผ่าน interface ที่สลับเป็นของจริงทีหลังได้

## 2. Behavior

### 2.1 ส่งรูป · `POST /sessions/{id}/messages` ที่มี `image_path`

ทำตามลำดับ · ข้อความกำกับ (`text`) ไม่เข้า `extract_answer` และ checker (api.md ตัดสินแล้ว · PR #45) · validation เดิมของ endpoint (body, `message_too_long`, rate limit) ทำก่อนเหมือนเดิม

1. **path ต้องเป็นของ session นี้:** `image_path` ต้องขึ้นต้นด้วย `{tenant_id}/sessions/{session_id}/` (รูปแบบ path ใน api.md v1.7 · `tenant_id` จาก token) · ไม่ใช่ → `404 not_found` ก่อนเริ่ม SSE (SA-06 · §10 ข้อ 3)
2. **ต้องมีโจทย์ค้าง:** อ่านโจทย์ที่ค้างของ session จาก `RoomState` (§2.4) · ไม่มี → §10 ข้อ 4 (UC-04 E9)
3. **อ่านรูป** ผ่าน `ImageStore` (§2.4) → `Image(data, mime_type)` · ไม่พบไฟล์ → `404 not_found` ก่อนเริ่ม SSE · ขนาดจริงเกิน `guards.max_image_mb` (1 MB = 1,048,576 bytes) → `422 file_too_large` ก่อนเริ่ม SSE (api.md v1.7 ข้อ 1: browser บอกขนาดเอง ต้องตรวจซ้ำตอนใช้ไฟล์ · TM-21)
4. **เริ่ม SSE:** ส่ง `token` ของ tutor ข้อความ `ขอดูก่อนนะ` ทันทีก่อนเรียก model (ข้อความเดียวกับ stub · ให้ผู้ใช้เห็นว่าระบบรับรูปแล้ว · ai-orchestration §2.10 TTFT)
5. **อ่านลายมือ:** `ai.call("extract_answer", {image, problem_text}, ExtractAnswerResult)` · `problem_text` = ข้อความโจทย์ที่ค้าง
6. **ผล:**
   - `lines` ไม่ว่าง → บันทึก **preview ที่รอยืนยัน** ของ session ลง `RoomState` แทนใบเดิม (api.md "preview ที่ค้าง": ส่งรูปใหม่ → preview ใหม่แทนใบเดิม) · ส่ง `ocr_preview` `{lines: [{latex, confidence}]}` ตามลำดับที่ model คืน → `token` `เช็คให้หน่อยว่าอ่านถูกไหม` → `done` (AM-01, AM-02 · ยืนยันทุกครั้งตาม `ocr.always_confirm` · ไม่ดู `confidence`)
   - `lines` ว่าง (รูปอ่านไม่ได้หรือไม่ใช่คำตอบ · UC-04 E1) → ไม่มี `ocr_preview` · ส่ง `token` `รูปนี้อ่านไม่ออก ลองถ่ายใหม่ให้ชัดขึ้นอีกนิดนะ` → `done` · preview ใบเดิม (ถ้ามี) → §10 ข้อ 6
   - model ล้มหลัง retry ของ gateway (`AIProviderError`) หรือตอบไม่ตรง schema (`AISchemaError`) → ส่ง `token` `ระบบช้า ลองส่งอีกทีนะ` (ข้อความ degrade เดียวกับ `tutor-reply-stream.md`) → `done` · preview ใบเดิมไม่เปลี่ยน
   - error อื่น (bug) → `error` `internal_error` แบบเดียวกับ `tutor-reply-stream.md`

### 2.2 ยืนยัน · `POST /sessions/{id}/ocr/confirm`

1. ไม่มี preview ที่รอยืนยันของ session นี้ใน `RoomState` → `409 no_pending_ocr` (api.md v1.7)
2. จำนวน `lines` ไม่เท่ากับ preview → `422 ocr_lines_mismatch` · บรรทัดว่างหรือมีแต่ช่องว่าง → `422` (validation ของ body เดิม)
3. **log บรรทัดที่แก้ (AM-03):** เทียบทีละบรรทัดกับ `preview.lines[i].latex` · เขียน log JSON 1 แถวต่อการยืนยันที่ได้ `verdict` (ข้อ 5 · logger `app.ocr.confirm` · field: `session_id`, `line_count`, `edited_lines` = เลขบรรทัดที่ต่าง เริ่มที่ 1) · ไม่ log ตัวคำตอบ · ตารางเก็บถาวร → §10 ข้อ 7
4. **ตรวจ:** `check_answer(problem, lines)` ของ `app/services/checker.py` ด้วยโจทย์ที่ผูกกับ preview นั้น (ไม่ใช่โจทย์ค้างปัจจุบัน ถ้าเปลี่ยนไปแล้ว) · ใช้บรรทัดที่ผู้ใช้ส่งมา ไม่ใช่ของ preview (AM-04, AM-05, AM-06)
5. **สำเร็จ:** ลบ preview ออกจาก `RoomState` (ยืนยันได้ครั้งเดียว) · ส่ง `verdict` `{verdict, first_wrong_line, error_type}` จาก `CheckResult` ก่อน token แรกของ tutor (ai-orchestration §2.4.5) · ชุดค่าตาม `merge-rules.md` §2 อยู่แล้ว
6. **คำอธิบายของ tutor หลัง verdict** (AM-07 · ai-orchestration §2.2.4 "การสอนตาม error type") → `gateway.stream("explain_check", input)` → ทุก chunk เป็น `token` ของ tutor → `done` (§10 ข้อ 1 ตัดสินแล้ว) · input ทุกค่าเป็น string อยู่ใน data block ของ gateway:
   - `problem` = ข้อความโจทย์ · `reference_answer` = เฉลย (ส่งเสมอ เพราะต้องบอกค่าที่ถูกและสาธิตวิธี · โจทย์ข้อนี้ผู้ใช้ตอบแล้ว จึงไม่ขัด AM-13) · `solution_steps` = ขั้นตอนในชีท บรรทัดละขั้น (ว่าง → ข้อความเดียวกับ `check_answer`)
   - `answer_lines` = บรรทัดที่ยืนยัน ขึ้นต้นด้วยเลขบรรทัด (`1. …`) แบบเดียวกับ `check_answer`
   - `check_result` = `verdict`, `first_wrong_line`, `error_type`, `evidence`, `method` ของ `CheckResult` บรรทัดละ field (`name: value` · null เขียน `none`)
   - prompt `prompts/explain_check/v1.md` บอกวิธีพูดตาม verdict และ error type ตาม §2.2.4 และ UC-04 ขั้น 5–6, A4–A8: `correct` ชมสั้นๆ (`method: other` → บอกวิธีในชีทด้วย) · ผิด → ชี้บรรทัด `first_wrong_line` แล้วอธิบายวิธีแก้ทันที ไม่ให้ hint แล้วให้ลองเอง ไม่ถาม "งงตรงไหน" · `no_answer` → ทำขั้นแรกให้ดู · กติกาสมการแบบเดียวกับ `tutor_reply/v1` · ไม่ส่งโจทย์ข้อถัดไป (ยังไม่มี planner · §9)
7. **checker ล้ม:**
   - classifier ล้ม (`AIProviderError` / `AISchemaError` ออกมาจาก `check_answer` · check-answer-classifier §10 ข้อ 2) → ไม่มี `verdict` · ส่ง `token` `ระบบช้า ลองส่งอีกทีนะ` → `done` · preview ยังอยู่ ผู้ใช้กดยืนยันใหม่ได้ · ไม่เขียน log ข้อ 3 (เขียนเมื่อได้ verdict เท่านั้น จึงไม่ซ้ำตอนยืนยันใหม่) · (§10 ข้อ 2 ตัดสินแล้ว · ชั่วคราวแทน UC-04 E4)
   - อื่นๆ (bug) → `error` `internal_error` · preview ยังอยู่ ผู้ใช้กดยืนยันใหม่ได้
8. tutor ล้มหลัง verdict ส่งแล้ว → ทำแบบเดียวกับ `tutor-reply-stream.md` (ยังไม่มี token → `ระบบช้า ลองส่งอีกทีนะ` · มี token แล้ว → `error` `ai_unavailable`) · verdict ที่ส่งไปแล้วไม่ถูกยกเลิก (UC-04 E5)

### 2.3 ข้อความที่พิมพ์ระหว่าง preview ค้าง

เป็นข้อความปกติตาม `tutor-reply-stream.md` และ preview ยังรอยืนยัน (api.md v1.7 ข้อ 3) · feature นี้ไม่เปลี่ยน flow ข้อความพิมพ์

### 2.4 Interface ที่สลับเป็นของจริงทีหลัง (ข้อเสนอ · Junior ตัดสิน · §10 ข้อ 5)

ทั้งสองเป็น FastAPI dependency เหมือน `get_gateway` เพื่อให้ test ใส่ของปลอมได้

- **`ImageStore.read(path) -> Image | None`** · `None` = ไม่พบไฟล์ · ของจริงอ่านจาก Supabase Storage ด้วย JWT ของผู้ใช้ (RLS ของ storage · CLAUDE.md "Database") เมื่อ Junior สร้าง bucket + policy และ `/uploads` จริง · **จนกว่าจะมี** ค่าเริ่มต้นคือ "ยังไม่มี Storage" ซึ่งทำให้ข้อความรูปตอบด้วย stub เดิม (`image_reply.sse` + `X-Stub`) และ `/ocr/confirm` ตอบด้วย stub เดิม (`ocr_confirm.sse`) · หน้าเว็บบน staging จึงไม่เปลี่ยน
- **`RoomState`** เก็บต่อ session: โจทย์ที่ค้าง (`CheckProblem` + `problem_id`) และ preview ที่รอยืนยัน (`lines` + `problem_id`) · ค่าเริ่มต้นเก็บใน memory ของ process (แบบเดียวกับ rate limiter · `gateway-guards.md` §2.1) · โจทย์ค้างเริ่มต้นของทุก session คือโจทย์ `p1` ของ `session_start.sse` พร้อมเฉลยฝั่ง server (§3) จนกว่าจะมีตาราง `problems` จริง · ของจริงอ่านเขียน `problems` / `messages` / `attempts` (Junior)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (ส่งรูป) | `SendMessageRequest` `{text?, image_path}` | `{"image_path": "<tenant>/sessions/s1/ab.jpeg"}` |
| Input (โจทย์ค้าง) | `CheckProblem` (text, reference_answer, answer_format, solution_steps) + `problem_id` | `p1`: text `แยกตัวประกอบ $x^2 - 49$` · reference `(x-7)(x+7)` · format `factored` · steps `[]` (เฉลยของ stub · ไม่ส่งให้ client) |
| AI call 1 | `extract_answer` → `ExtractAnswerResult` `{lines: [{latex, confidence}], notes}` | `{"lines": [{"latex": "x^2 - 49", "confidence": 0.97}, {"latex": "= (x-7)(x+7)", "confidence": 0.95}], "notes": ""}` |
| Output (ส่งรูป) | SSE `token` → `ocr_preview` → `token` → `done` | `ocr_preview` `{"lines": [{"latex": "x^2 - 49", "confidence": 0.97}, …]}` |
| Input (ยืนยัน) | `OcrConfirmRequest` `{lines: string[]}` | `{"lines": ["x^2 - 49", "= (x-7)(x+7)"]}` |
| AI call 2 | `check_answer` service → `CheckResult` | `verdict: correct` |
| Output (ยืนยัน) | SSE `verdict` → `token`… → `done` | `{"verdict": "correct", "first_wrong_line": null, "error_type": null}` |
| Log (AM-03) | JSON 1 แถว logger `app.ocr.confirm` | `{"session_id": "s1", "line_count": 2, "edited_lines": [2]}` |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider (`AI_PROVIDER=fake` · กำหนดผลของ `extract_answer` / `check_answer` / tutor ใน test), `ImageStore` และ `RoomState` ปลอม · SymPy ใช้ของจริง (`sympy_service` ใน unit test เดิมก็รันจริง) · ขีดจำกัดอ่านจาก config

**ส่งรูป**

- **AC-1 (TM-06, AM-01, AM-02)** Given โจทย์ค้าง `p1` และรูปที่ `extract_answer` คืน 2 บรรทัด When ส่ง `{image_path}` ของ session นี้ Then SSE คือ `token` "ขอดูก่อนนะ" → `ocr_preview` ที่มี 2 บรรทัดตามลำดับพร้อม `confidence` เดิม → `token` "เช็คให้หน่อยว่าอ่านถูกไหม" → `done` · ไม่มี `X-Stub`
- **AC-2 (AM-02)** Given `extract_answer` คืน `confidence` 1.0 ทุกบรรทัด When ส่งรูป Then ยังได้ `ocr_preview` และไม่มี `verdict` ใน stream นี้ (ยืนยันทุกครั้ง ไม่ข้ามไปตรวจ)
- **AC-3 (TM-06)** Given ข้อความกำกับ `"ข้อ 2 ครับ"` When ส่ง `{text, image_path}` Then input ของ `extract_answer` มีแค่ `image` และ `problem_text` (ไม่มีข้อความกำกับ)
- **AC-4 (AM-01)** When ส่งรูป Then `extract_answer` ได้ `problem_text` = ข้อความของโจทย์ค้าง และรูปที่ `ImageStore` คืน (bytes และ mime type เดิม)
- **AC-5 (UC-04 E1)** Given `extract_answer` คืน `lines: []` Then SSE คือ `token` "ขอดูก่อนนะ" → `token` "รูปนี้อ่านไม่ออก ลองถ่ายใหม่ให้ชัดขึ้นอีกนิดนะ" → `done` · ไม่มี `ocr_preview`
- **AC-6 (api.md v1.7)** Given preview ใบแรกรอยืนยัน When ส่งรูปใหม่ที่อ่านได้ 3 บรรทัด Then `/ocr/confirm` ด้วย 2 บรรทัด → `422 ocr_lines_mismatch` และด้วย 3 บรรทัด → ตรวจได้ (ใบใหม่แทนใบเดิม)
- **AC-7 (ai-orchestration §2.10)** Given `extract_answer` ล้มด้วย `AIProviderError` หรือ `AISchemaError` Then SSE คือ `token` "ขอดูก่อนนะ" → `token` "ระบบช้า ลองส่งอีกทีนะ" → `done` · preview ใบเดิม (ถ้ามี) ยังยืนยันได้
- **AC-8 (SA-06)** Given `image_path` ขึ้นต้นด้วย tenant อื่น หรือ session อื่นของ tenant เดียวกัน When ส่ง Then `404 not_found` ก่อนเริ่ม SSE และไม่เรียก `ImageStore` หรือ `extract_answer`
- **AC-9 (api.md v1.7)** Given `ImageStore` ไม่พบไฟล์ Then `404 not_found` และไม่เรียก `extract_answer`
- **AC-boundary (TM-21)** Given ไฟล์จริงขนาด `guards.max_image_mb × 1,048,576` bytes − 1, = และ + 1 Then −1 และ = → ได้ `ocr_preview` · +1 → `422 file_too_large` ก่อนเริ่ม SSE และไม่เรียก `extract_answer` (ขีดเดียวกับ `/uploads` ที่รับ `size_bytes` เท่ากับเพดานพอดี)
- **AC-10** Given ยังไม่มี Storage (ค่าเริ่มต้นของ `ImageStore`) When ส่งรูป Then ได้ stream ของ stub เดิม (`image_reply.sse`) พร้อม `X-Stub: true` และไม่เรียก model · `/ocr/confirm` ได้ `ocr_confirm.sse` เดิม (test เดิมของ stub ยังผ่าน)

**ยืนยัน**

- **AC-11 (AM-04)** Given preview ของ `p1` When ยืนยัน `["x^2 - 49", "= (x-7)(x+7)"]` Then `verdict` `{verdict: "correct", first_wrong_line: null, error_type: null}` มาก่อน `token` แรก แล้ว `done`
- **AC-12 (AM-05, AM-06)** Given preview ของ `p1` และ classifier ปลอมคืน `error_type: sign` When ยืนยัน `["x^2 - 49", "= (x-7)(x-7)"]` Then `verdict` `{verdict: "incorrect", first_wrong_line: 2, error_type: "sign"}` (บรรทัดผิดมาจาก SymPy)
- **AC-13 (AM-04)** When ยืนยันบรรทัดที่ผู้ใช้แก้แล้ว (ต่างจาก preview) Then checker ได้บรรทัดที่ผู้ใช้ส่งมา ไม่ใช่ของ preview
- **AC-14 (AM-03)** Given preview 3 บรรทัด When ยืนยันโดยแก้บรรทัด 2 Then log `app.ocr.confirm` 1 แถว `{session_id, line_count: 3, edited_lines: [2]}` · ไม่แก้เลย → `edited_lines: []` · ไม่มีข้อความคำตอบใน log
- **AC-15 (api.md v1.7)** Given ยืนยันสำเร็จแล้ว When ยืนยันซ้ำ Then `409 no_pending_ocr`
- **AC-16 (api.md v1.7)** Given ไม่เคยส่งรูปใน session นี้ หรือ preview เป็นของ session อื่น When ยืนยัน Then `409 no_pending_ocr`
- **AC-17** Given checker ล้มด้วย error ที่ไม่ใช่ของ AI (bug) Then SSE `error` `internal_error` ไม่มี `verdict` · preview ยังอยู่ (ยืนยันใหม่ได้)
- **AC-18 (AM-07)** Given verdict เป็น `incorrect` บรรทัด 2 `sign` When ยืนยัน Then gateway ได้ `stream("explain_check", …)` ที่มี `problem`, `reference_answer`, `solution_steps`, `answer_lines` (บรรทัดที่ยืนยัน มีเลขบรรทัด) และ `check_result` ที่มี `verdict: incorrect`, `first_wrong_line: 2`, `error_type: sign`, `evidence`, `method` · chunk ของ stream เป็น `token` ของ tutor ตามลำดับ และมาหลัง `verdict`
- **AC-18b (AM-07)** Given verdict เป็น `correct` When ยืนยัน Then `check_result` มี `first_wrong_line: none` และ `error_type: none` · ยังเรียก `explain_check` (ชมสั้นๆ)
- **AC-18c (AI-01)** `prompts/explain_check/v1.md` มี front matter `purpose: explain_check`, `version: 1` และ input ครบ 5 ตัว · `config/ai.yaml` มี `explain_check` ที่ `stream: true` และ tier main (test โหลด prompt ผ่าน gateway จริงกับ fake provider)
- **AC-19 (UC-04 E5)** Given tutor ล้มก่อน token แรก Then หลัง `verdict` ได้ `token` "ระบบช้า ลองส่งอีกทีนะ" → `done` · ล้มหลังมี token แล้ว → `error` `ai_unavailable`
- **AC-E4 (UC-04 E4 · ชั่วคราว)** Given classifier ล้มด้วย `AIProviderError` หรือ `AISchemaError` Then SSE คือ `token` "ระบบช้า ลองส่งอีกทีนะ" → `done` · ไม่มี `verdict` · ไม่เรียก `explain_check` · ไม่มี log `app.ocr.confirm` · ยืนยันซ้ำด้วยบรรทัดเดิมแล้ว classifier ทำงาน → ได้ `verdict` (preview ยังอยู่)

## 5. Data changes

ไม่มีใน PR นี้ · `RoomState` อยู่ใน memory · ของจริงต้องใช้ตารางเดิมใน `0001_init.sql`: `problems` (โจทย์ + เฉลย), `messages` (`input_mode: 'image'`, `attachment_path`, `attachment_name`), `attempts` (ผลตรวจ) · preview ที่รอยืนยันและ log AM-03 ยังไม่มีที่เก็บใน data model → §10 ข้อ 5, 7

## 6. API / SSE changes

ไม่มี endpoint หรือ event ใหม่ · ใช้ contract เดิมของ api.md v1.7 (ยังเป็นข้อเสนอรอ Junior) · พฤติกรรมที่เพิ่ม:

| Endpoint | เพิ่ม |
|---|---|
| `POST /sessions/{id}/messages` (มี `image_path`) | `404 not_found` เมื่อ path ไม่ใช่ของ session นี้หรือไม่พบไฟล์ · `422 file_too_large` เมื่อไฟล์จริงเกิน · ทั้งสองเป็น error ที่ api.md มีอยู่แล้วแต่ยังไม่ได้เขียนไว้ที่ endpoint นี้ (§11) |
| `POST /sessions/{id}/ocr/confirm` | ไม่เปลี่ยน contract |

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `extract_answer` | vision | `ExtractAnswerResult` (`app/models/scope_ai.py`) | `prompts/extract_answer/v1.md` (ไม่แก้) |
| `check_answer` (ใน `check_answer` service) | ตาม `ai.yaml` | `CheckAnswerResult` | `prompts/check_answer/v2.md` (ไม่แก้) |
| `explain_check` (ใหม่ · `stream: true`) | main (เท่ากับ `tutor_reply` · ค่า temperature, max_tokens, timeout_s, thinking เดียวกับ `tutor_reply` ใน `config/ai.yaml`) | free text (stream) | `prompts/explain_check/v1.md` (ใหม่) |

ทุก call ผ่าน gateway (AI-01) · log `ai_calls` ด้วย `ai_call_context` แบบเดียวกับ `tutor-reply-stream.md` เมื่อมี token

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `test_TM06_photo_streams_real_ocr_preview` | unit (TestClient + fake) | AC-1, AC-4 |
| `test_AM02_photo_always_asks_to_confirm` | unit | AC-2 |
| `test_TM06_caption_does_not_reach_extract_answer` | unit | AC-3 |
| `test_AM01_unreadable_photo_asks_for_a_new_one` | unit | AC-5 |
| `test_AM02_new_photo_replaces_pending_preview` | unit | AC-6 |
| `test_AM01_extract_answer_failure_degrades` (parametrize provider / schema error) | unit | AC-7 |
| `test_SA06_image_path_of_another_session_is_not_found` (parametrize tenant / session) | unit | AC-8 |
| `test_TM06_missing_image_is_not_found` | unit | AC-9 |
| `test_TM21_image_size_boundary` (parametrize −1, =, +1) | unit | AC-boundary |
| `test_TM06_photo_stays_stub_without_storage` | unit | AC-10 |
| `test_AM04_confirmed_answer_gets_verdict_before_tutor` | unit | AC-11 |
| `test_AM05_wrong_line_and_error_type_in_verdict` | unit | AC-12 |
| `test_AM04_checker_uses_confirmed_lines` | unit | AC-13 |
| `test_AM03_confirm_logs_edited_lines` | unit | AC-14 |
| `test_AM02_confirm_twice_has_no_pending_ocr` | unit | AC-15 |
| `test_AM02_confirm_without_preview_has_no_pending_ocr` | unit | AC-16 |
| `test_AM04_checker_bug_keeps_preview` | unit | AC-17 |
| `test_AM07_explain_check_gets_check_result` (parametrize incorrect / correct) | unit | AC-18, AC-18b |
| `test_AM07_explain_check_prompt_and_route` | unit | AC-18c |
| `test_AM07_tutor_failure_after_verdict` | unit | AC-19 |
| `test_AM06_classifier_failure_keeps_preview` | unit | AC-E4 |

ไฟล์: `apps/api/tests/unit/test_photo_check_in_room.py` · smoke กับ Vertex จริงในเครื่อง (ขั้น 6 ของ worklog) ไม่อยู่ใน CI

## 9. Out of scope

- `/uploads` จริง, bucket, storage policy และ `ImageStore` ตัวที่อ่าน Supabase Storage (Junior · api.md v1.7 รอตัดสินข้อ 2)
- บันทึก `messages`, `problems`, `attempts`, `checker_disagreements` และ mastery (Junior · ยังไม่มี session จริงใน DB · `tutor-reply-stream.md` §10 ข้อ 1)
- intent router, `normalize_math` (คำตอบที่พิมพ์ · UC-04 A2), dispute (AM-12), answer-leak check (AM-13), stage machine และโจทย์ถัดไป (AM-08)
- `extract_answer/v2` (P1 §4 · term 2)
- หน้าเว็บ (ใช้ของเดิมได้เลย · `room-photo-send.md`)

## 10. Open questions

1. ~~**tutor พูดอะไรหลัง verdict**~~ **ตัดสินแล้ว** (Jam 2026-11-08): เลือก (ข) purpose ใหม่ `explain_check` และส่งเฉลยให้ model · เหตุผล: demo S4 ต้องโชว์การอธิบายทันที (AM-07) · ไม่กระทบ `tutor_reply` ที่ P4-lite วัดไว้ · ยังไม่มี golden set ของ prompt นี้ ใช้ smoke กับ Vertex (ขั้น 6 ของ worklog) ไปก่อน · รายละเอียด §2.2 ข้อ 6 · ทางเลือกเดิม: `tutor_reply/v1` รับแค่ `message` และสั่งให้ "guide to the next step instead of giving the final answer" ซึ่งขัดกับ AM-07 (อธิบายวิธีแก้ทันที) · ทางเลือก:
   - (ก) **`tutor_reply/v2`** เพิ่ม input `checker_result` (layer 8 · §2.2.3) และกฎการสอนตาม error type (§2.2.4) · ข้อความพิมพ์ส่ง `checker_result` = `none` · ต้องรัน eval ของ tutor (ยังไม่มี golden set ของ tutor_reply)
   - (ข) **purpose ใหม่ `explain_check`** (stream · prompt v1 แยก) · ไม่กระทบข้อความพิมพ์ · ต้องเพิ่มใน `config/ai.yaml` (ไฟล์กลาง) และรายชื่อ purpose ใน ai-orchestration §2.10
   - (ค) **ข้อความ template ตาม verdict ไปก่อน** (ไม่เรียก model) เช่น `ถูกต้อง` / `บรรทัด {n} ผิด` · ไม่ผ่าน AM-07 แต่ไม่ต้องแก้ prompt ใน PR นี้
   - ข้อเสนอ: (ข) เพราะเป็น directive แบบแคบที่ test ได้ และไม่เปลี่ยนพฤติกรรมของแชทที่ P4-lite วัดไว้ · input: โจทย์, บรรทัดที่ยืนยัน, `CheckResult` (verdict, first_wrong_line, error_type, evidence, method) · ไม่ส่งเฉลยถ้า verdict ไม่ใช่ `correct`? → ต้องตัดสินด้วย (AM-07 ต้องสาธิตวิธีแก้ จึงน่าจะต้องเห็นเฉลย · AM-13 ห้ามเฉลย*โจทย์ที่ยังรอคำตอบ* ซึ่งข้อนี้ตอบแล้ว)
2. ~~**classifier ล้ม (UC-04 E4)**~~ **ตัดสินแล้ว** (Jam 2026-11-08): เลือก (ข) ไม่แก้ contract · ทางเลือกเดิม: use case บอกให้ใช้ผล SymPy อย่างเดียวไม่มี error type แต่ `verdict` ของ api.md บังคับว่า `incorrect` ต้องมีทั้ง `first_wrong_line` และ `error_type` (merge-rules §2) และ `check_answer` service ส่ง error ออกมาโดยไม่เดา error type · ทางเลือก: (ก) SymPy ตัดสินได้ → `verdict` ที่มี `error_type: null` (ต้องแก้ api.md + `VerdictEvent` + verdict-mark ของ May) · (ข) ส่ง `ระบบช้า ลองส่งอีกทีนะ` แล้วเก็บ preview ไว้ให้ยืนยันใหม่ (ไม่มี verdict) · ข้อเสนอ: (ข) ใน PR นี้ เพราะไม่ต้องแก้ contract และ P2 ล้มน้อย · E4 แบบเต็มทำตอนแก้ api.md รอบถัดไป
3. **(Junior) `image_path` ของ session อื่น:** api.md เขียน `404 not_found` ไว้ที่ `audio_path` ของ `/transcribe` แต่ไม่ได้เขียนที่ `image_path` · ข้อเสนอ: ใช้กฎเดียวกัน (AC-8)
4. **(Jam · Junior) ส่งรูปตอนไม่มีโจทย์ค้าง (UC-04 E9):** ควรให้ intent router ตัดสิน แต่ยังไม่มี · ทางเลือก: (ก) ส่งเป็นข้อความปกติเข้า tutor โดยใช้ข้อความกำกับ (ไม่มีข้อความกำกับ → ข้อความว่าง) · (ข) `token` template "ตอนนี้ยังไม่มีโจทย์ที่รอคำตอบ ส่งคำถามเป็นข้อความได้เลยนะ" · ข้อเสนอ: (ข) เพราะ tutor อ่านรูปไม่ได้อยู่ดี · ใน PR นี้ทุก session มีโจทย์ค้างเริ่มต้นคือ `p1` (§2.4) จึงเกิดหลัง `p1` ถูกตรวจแล้วเท่านั้น → ข้อเสนอเพิ่ม: หลังตรวจ `p1` ยังค้างอยู่ (ไม่มีโจทย์ถัดไปจนกว่าจะมี planner) เพื่อให้ demo ส่งซ้ำได้
5. **(Junior) โครงสร้าง backend ใน §2.4:** `ImageStore` และ `RoomState` เป็น dependency ใน `app/services/` (ชื่อไฟล์เสนอ `app/services/photo_check.py`, `app/services/room_state.py`) · ค่าเริ่มต้น "ยังไม่มี Storage" ทำให้ staging ยังเป็น stub · preview ที่รอยืนยันควรเก็บที่ไหนเมื่อมี DB: (ก) `messages` แถวของ tutor ที่มี payload ของ `ocr_preview` (ต้องเพิ่มคอลัมน์) (ข) ตารางใหม่ `ocr_previews` · RoomState ใน memory ใช้ไม่ได้เมื่อ Cloud Run มีหลาย instance (เหมือน rate limiter)
6. **รูปอ่านไม่ได้ขณะมี preview ค้าง:** api.md บอกแค่ "ส่งรูปใหม่ → preview ใหม่แทนใบเดิม" · ข้อเสนอ: preview ใบเดิมยังยืนยันได้ (หน้าเว็บล็อกการ์ดเดิมเฉพาะเมื่อได้ `ocr_preview` ใบใหม่ · ocr-confirm-card AC ข้อ 58)
7. **(Junior) ที่เก็บ log AM-03:** data model ไม่มีตารางของการแก้ลายมือ · ข้อเสนอ: log JSON ไป Cloud Logging ใน PR นี้ (แบบ `ai-calls-log.md`) · ตารางจริงตอนบันทึก `messages`
8. **เฉลยของโจทย์ stub `p1`:** `session_start.sse` มีแค่ `x^2 - 49` · ข้อเสนอ: ข้อความ `แยกตัวประกอบ $x^2 - 49$` · `factored` · `(x-7)(x+7)` · เก็บฝั่ง server ไม่ส่ง client (เฉลยห้ามออกไปก่อนตอบ · `problem` event ไม่มีเฉลย)

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | เจ้าของ · เมื่อไหร่ |
|---|---|---|
| `specs/system/api.md` (ไฟล์กลาง) | `POST /sessions/{id}/messages`: `404 not_found` เมื่อ `image_path` ไม่ใช่ของ session หรือไม่พบไฟล์ · `422 file_too_large` เมื่อไฟล์จริงเกิน (§6 · §10 ข้อ 3) | Jam เสนอ · Junior ตัดสิน · ถามก่อนแก้ |
| `config/ai.yaml` (ไฟล์กลาง) | เพิ่ม `explain_check` (§7) · bump `version` | เสร็จแล้ว (PR #114 · `ai.yaml` 1.12) · บอกกลุ่มก่อน merge |
| `specs/system/ai-orchestration.md` §2.10 ตาราง tier + ตาราง purpose (T-rows) | เพิ่ม `explain_check` (tier main · หลัง verdict ใน 2.2) | เสร็จแล้ว (PR #114 · v1.7) |
| `room-photo-send.md` §9 | "`extract_answer` และ checker จริง · ผลตรวจยังเป็น stub" → ชี้มาที่ spec นี้ | เสร็จแล้ว (PR #114) |
| `docs/design/use-cases.md` UC-04 E4 | หมายเหตุว่าตอนนี้ classifier ล้มแล้วให้ยืนยันใหม่ (§10 ข้อ 2 ข) เป็นแบบชั่วคราว | May · ย้อนหลัง |
