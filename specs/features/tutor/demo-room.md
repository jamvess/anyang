# Feature: เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง

| | |
|---|---|
| Area | tutor |
| Requirements | TM-06, AM-01, AM-02, AM-07, TM-04, PM-02, TM-15 (ทั้งหมดผ่านของเดิมใน `photo-check-in-room.md` · ไฟล์นี้เพิ่มแค่ทางเดินให้วนได้ในเครื่อง) |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (upload ในเครื่อง) |
| Status | approved 2026-11-09 (Jam · §10 ข้อ 1–2 ตามข้อเสนอ) |
| Related system spec | `photo-check-in-room.md` §2.4 (`ImageStore`, `RoomState`) · api.md v1.7 `/uploads` · `tutor-reply-stream.md` · ai-orchestration §2.2.3 (layer 6–7: tutor ต้องรู้ว่าตอนนี้ทำอะไร) |

## 1. Context

อาจารย์ขอดูห้องติวที่ใช้ได้จริงก่อนทำต่อ (9 พ.ย.) · ของจริงมีครบแล้วยกเว้น 3 จุด: รูปไปไม่ถึง API เพราะยังไม่มี Storage, มีโจทย์ข้อเดียว และ tutor ไม่รู้ว่ากำลังทำโจทย์ข้อไหน · feature นี้ปิด 3 จุดนั้น**เฉพาะในเครื่อง** (`APP_ENV=local`) ให้เดโม่วนได้หลายข้อ · ไม่ใช่การตัดสินโครงสร้างจริงของ Storage หรือ planner (ของ Junior · §9)

## 2. Behavior

ทุกข้อในส่วน A และ B มีผลเมื่อ `APP_ENV=local` เท่านั้น · `APP_ENV` อื่นทำงานเหมือนเดิมทุกอย่าง (รวม `test` ของ CI ยกเว้น test ของ feature นี้ที่ตั้งค่าเอง)

**A · อัปโหลดรูปในเครื่อง**

1. `POST /sessions/{id}/uploads` แบบ `image` ตรวจเหมือนเดิม (ชนิด, ขนาดที่บอกมา) · path เหมือนเดิม `{tenant_id}/sessions/{session_id}/{uuid}.{ext}` · `upload_url` = `{base URL ของ request}/dev/uploads/{path}` · **ไม่มี** header `X-Stub` (หน้าเว็บจึง `PUT` ไฟล์เอง · `room-photo-send.md` §2 ขั้น 2) · audio ยังเป็น stub
2. `PUT /dev/uploads/{path}` เก็บ body ลงไฟล์ใต้โฟลเดอร์ `.local/uploads/` ที่ root ของ repo (อยู่ใน `.gitignore`) · path ต้องเป็นรูปแบบข้อ 1 (ชื่อไฟล์ไม่มี `/`, `..`) · `Content-Type` ต้องเป็นชนิดรูปที่ `/uploads` รับ · ขนาดเกิน `guards.max_image_mb` → `422 file_too_large` แบบเดียวกับ `/uploads` · สำเร็จตอบ `200` · route นี้ไม่มีเมื่อ `APP_ENV` ไม่ใช่ `local` (→ `404`)
3. `get_image_store()` คืน store ที่อ่านจากโฟลเดอร์นั้น (mime type จากนามสกุล) · ไม่มีไฟล์ → `None` · จากนั้นทุกอย่างเป็นไปตาม `photo-check-in-room.md`

**B · ชุดโจทย์เดโม่**

1. 5 ข้อตามลำดับ (§3) · ข้อแรกคือ `p1` ที่การ์ดของ `session_start.sse` แสดงอยู่แล้ว
2. หลังยืนยันแล้วได้ `verdict` และคำอธิบายของ tutor จบ (ไม่ล้ม): ส่ง `token` ของ tutor `ข้อต่อไปนะ` → event `problem` ของข้อถัดไป (`{problem_id, text_latex, difficulty, purpose: "practice"}` · ไม่มีเฉลย) → `done` · ข้อถัดไปเป็นโจทย์ค้างของ session นั้นทันที (ตรวจรูปถัดไปกับข้อนี้)
3. ถูกหรือผิดก็ไปข้อต่อไป (ยังไม่มี stage machine · TM-04 เต็มรูปแบบอยู่นอก §9) · ครบ 5 ข้อแล้ววนกลับข้อ 1
4. tutor ล้มหลัง verdict → ไม่ส่งโจทย์ถัดไป และโจทย์ค้างไม่เปลี่ยน (ส่งรูปข้อเดิมได้)
5. นอก `local` โจทย์ค้างยังเป็น `p1` ตลอดเหมือนเดิม (`photo-check-in-room.md` §10 ข้อ 4)

**C · tutor รู้โจทย์ปัจจุบัน (ทุก `APP_ENV`)**

1. ข้อความพิมพ์ส่ง input `problem` = ข้อความโจทย์ค้างของ session (ไม่มีเฉลย · AM-13) ให้ `tutor_reply` · ไม่มีโจทย์ค้าง → `none`
2. prompt `tutor_reply/v2` = v1 + โจทย์ใน `<document name="problem">` + กฎ: ถ้านักเรียนถามเรื่องโจทย์นี้ ให้ช่วยเริ่มทีละขั้นโดยไม่เฉลยคำตอบสุดท้าย · ถ้าถามเรื่องอื่น ตอบตามปกติ
3. มีผลทุก `APP_ENV` เพราะการ์ดโจทย์ `p1` ขึ้นในห้องบน staging ด้วย (tutor ควรรู้เรื่องเดียวกับที่ผู้ใช้เห็น) · `config/ai.yaml` → `tutor_reply.prompt: v2` (ไฟล์กลาง)
4. **เพิ่มตอน implement (Jam เลือก 9 พ.ย.):** test เดิมของ gateway เรียก `tutor_reply` ด้วย `{message}` อย่างเดียว · gateway จึงรองรับ `defaults` ใน frontmatter ของ prompt (`tutor_reply/v2`: `defaults: {problem: none}`) แทนการแก้ test เหล่านั้น · กฎอยู่ใน `prompts/README.md` "Frontmatter" · test `test_prompt_defaults.py`

**D · mastery จริงในการ์ดความคืบหน้า (local เท่านั้น · ใช้ `specs/features/planner/bkt-mastery.md`)**

1. 3 หัวข้อเดโม่ (§3 ตารางที่ 2) แต่ละหัวข้อมี `TopicProgress` ต่อ session เริ่มที่ `p_init`, 0 attempt · mode `normal` · ทุก attempt ของเดโม่ `independent = true` (โจทย์ข้อถัดไปไม่ใช่ข้อที่ tutor เพิ่งสาธิต) · skill ถือว่าครบ (`skills_covered = true` · ยังไม่มี `topic_skills`)
2. หลัง `verdict` (ก่อนคำอธิบายของ tutor): `record_attempt` ของหัวข้อของโจทย์นั้นด้วย `is_correct` และ `difficulty` ของโจทย์ · checker ล้มไม่มี attempt
3. หลังคำอธิบายจบ ก่อน `ข้อต่อไปนะ`: ส่ง `progress_card` ที่คิดจาก state จริง: `topics[].level` จาก `level()`, `readiness` จาก `readiness()`, `passed` = จำนวนหัวข้อ `passed`, `total` = 3, `days_left` = ค่าเดียวกับการ์ดเปิดห้อง, `review_due = false`, `origin = "doc"`
4. เปิดห้อง (`POST /exam-preps/{id}/sessions`) ใน local: การ์ดเปิดห้องเป็นการ์ดของ state นี้ (ทุกหัวข้อ `not_started`, ความพร้อม 0 ตาม bkt-mastery §10 ข้อ 1) แทน 4 หัวข้อของ fixture · event อื่นของ `session_start.sse` เหมือนเดิม

**E · tutor จำบทสนทนาในห้อง และจอไม่มีประวัติปลอม (local เท่านั้น · เพิ่ม 9 พ.ย. หลังลองในเบราว์เซอร์)**

ที่มา: จอแสดงประวัติแชทตัวอย่างของ stub (`room.json`) ที่ tutor ไม่เคยเห็น และ `tutor_reply` ได้แค่ข้อความล่าสุด · ผู้ใช้พิมพ์ "ฉันไม่แน่ใจ" ต่อจากคำถามในประวัติปลอม แล้ว tutor ตอบเรื่องโจทย์ค้างแทน · ส่วนนี้คือ layer 9 ของ ai-orchestration §2.2.3 (บทสนทนาล่าสุด) แบบเก็บใน memory จนกว่าจะมีตาราง `messages` (Junior)

1. `GET /sessions/{id}` ใน local คืน `messages: []` · field อื่นเหมือน stub · ไม่ใช่ local → เหมือนเดิม
2. state ของ session เก็บบทสนทนาจาก server เท่านั้น (ไม่รับจาก client · ai-orchestration §2.3.6) เป็นรายการ `(role, text)` · `role` = `นักเรียน` หรือ `ติวเตอร์`:
   - ข้อความพิมพ์ → `นักเรียน: {text}` ก่อนเรียก model · คำตอบของ tutor (token ต่อกัน) → `ติวเตอร์: …` เมื่อ stream จบโดยไม่ล้ม (ล้ม → ไม่บันทึกฝั่ง tutor)
   - เปิดห้อง → `ติวเตอร์:` ข้อความเปิดของ fixture และ `ติวเตอร์: (โจทย์) {โจทย์}`
   - ส่งรูป → `นักเรียน: (ส่งรูปวิธีทำ)` ต่อด้วยข้อความกำกับถ้ามี · token ของ tutor ใน stream นั้นบันทึกเหมือนข้อความพิมพ์
   - ยืนยัน → `นักเรียน: (ยืนยันคำตอบ) {บรรทัด 1} · {บรรทัด 2} …` · `ติวเตอร์: (ผลตรวจ) verdict {verdict} · บรรทัดผิด {n หรือ ไม่มี} · {error_type หรือ ไม่มี}` · คำอธิบาย + `ข้อต่อไปนะ` เป็น `ติวเตอร์: …` · โจทย์ถัดไป → `ติวเตอร์: (โจทย์) {โจทย์}`
3. 1 turn = ข้อความของนักเรียน 1 ข้อความ + ทุกอย่างของ tutor ที่ตามมา (บรรทัดของ tutor ก่อนข้อความแรกของนักเรียนเป็น turn แรก) · เก็บแค่ `session.context_recent_turns` turns ล่าสุด
4. `tutor_reply` ได้ input `conversation` = บรรทัดละรายการ `{role}: {text}` เรียงเก่าไปใหม่ **ไม่รวมข้อความที่กำลังตอบ** (อยู่ใน `message` แล้ว) · ทุก `<` ในข้อความเป็น `&lt;` ก่อนใส่ (prompts/README.md ข้อ 5 · ai-orchestration §2.3.6) · ไม่มีบทสนทนา → `none` (`defaults` ของ prompt)
5. `tutor_reply/v2` (ยังไม่ merge จึงแก้ไฟล์เดิม) เพิ่ม `<conversation>` ก่อน `<message>` และกฎ: ข้อความสั้นหรือกำกวม ("ไม่แน่ใจ", "7", "ทำไม") ให้ตีความต่อจากบทสนทนา · ถ้ายังไม่ชัดให้ถามกลับ 1 คำถามสั้นๆ
6. เปิดห้องใหม่ล้างบทสนทนา (เหมือน D ข้อ 4) · state ธรรมดา (ไม่ใช่ local) ไม่เก็บ → `conversation` = `none`

## 3. Inputs and outputs

ชุดโจทย์ (มาจาก `evals/answers/labels.jsonl` · มีรูปลายมือจริงทั้งแบบถูกและผิดให้ใช้ตอนเดโม่)

| # | problem_id | โจทย์ | answer_format | เฉลย | รูปถูก · ผิด ใน `evals/handwriting/raw/` |
|---|---|---|---|---|---|
| 1 | `p1` | แยกตัวประกอบ $x^2-49$ | factored | `(x-7)(x+7)` | เขียนสดตอนเดโม่ |
| 2 | `demo-2` | $\lim_{x \to 2} \frac{x^2-4}{x^2-3x+2}$ | expression | `4` | `hw_024.png` · `hw_002.jpg` |
| 3 | `demo-3` | $\frac{d}{dx}(x^2 \sin x)$ | expression | `2x\sin(x)+x^{2}\cos(x)` | `hw_022.png` · `hw_007.jpg` |
| 4 | `demo-4` | $f(x)=x^4-3x^2+2x$ หา $f''(x)$ | expression | `12x^{2}-6` | `hw_017.png` · `hw_019.png` |
| 5 | `demo-5` | แยกตัวประกอบ $x^3-x$ | factored | `x(x-1)(x+1)` | `hw_021.png` · `hw_001.jpg` (ยังแยกไม่สุด) |

(ชื่อไฟล์จาก field `image` ของ ans_024, 002, 022, 007, 017, 019, 021, 001 ใน `labels.jsonl`)

หัวข้อเดโม่ (ดาวและ `signal_r` ตั้งเองสำหรับเดโม่ · ของจริงมาจาก `compute_importance`) · ทุกโจทย์ difficulty 3 (ระดับข้อสอบ) จึงถึง `passed` ได้เมื่อตอบถูกพอ

| topic_id | ชื่อ | ดาว | signal_r | โจทย์ |
|---|---|---|---|---|
| `t-factor` | การแยกตัวประกอบ | ★★ | 0.5 | `p1`, `demo-5` |
| `t-limit` | ลิมิต | ★★★ | 1.0 | `demo-2` |
| `t-derivative` | อนุพันธ์ | ★★★ | 1.0 | `demo-3`, `demo-4` |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider · ข้อ A และ B ตั้ง `APP_ENV=local` ผ่าน settings ของ test

- **AC-1 (TM-06)** local: `/uploads` แบบ image ได้ `upload_url` ที่ลงท้ายด้วย `/dev/uploads/{path}` และไม่มี `X-Stub` · ไม่ใช่ local: เหมือนเดิม (`X-Stub: true`, URL ของ stub)
- **AC-2 (TM-06)** local: `PUT` ไฟล์ไปที่ `upload_url` แล้วส่ง `{image_path}` → ได้ `ocr_preview` จาก `extract_answer` ที่ได้รับ bytes เดียวกับที่ `PUT`
- **AC-3 (SA-06)** `PUT` path ที่ชื่อไฟล์มี `..` หรือ `/` เพิ่ม → `404` · ชนิดไม่ใช่รูป → `422 unsupported_type` · เกิน `guards.max_image_mb` → `422 file_too_large` · ไม่ใช่ local → `404`
- **AC-4 (TM-04)** local: ยืนยันแล้วได้ `verdict` → token ของคำอธิบาย → token `ข้อต่อไปนะ` → `problem` ของ `demo-2` → `done` · รูปถัดไปถูกส่งเข้า `extract_answer` พร้อมโจทย์ `demo-2`
- **AC-5 (TM-04)** local: ยืนยันครบ 5 ข้อแล้ว ข้อถัดไปคือ `p1`
- **AC-6** local: tutor ล้มหลัง verdict → ไม่มี `problem` · รูปถัดไปยังตรวจกับโจทย์เดิม
- **AC-7** ไม่ใช่ local: ยืนยันแล้วไม่มี `problem` ต่อท้าย (เหมือน `photo-check-in-room.md`)
- **AC-9 (PM-02, TM-15)** local: ยืนยัน `p1` ถูก → `progress_card` หลังคำอธิบาย มี `t-factor` เป็น `developing` (mastery 0.71 ≥ `weak_below`), อีก 2 หัวข้อ `not_started`, `readiness` = ค่าจาก `readiness()` · ผิด → `t-factor` เป็น `weak`
- **AC-10 (TM-15)** local: เปิดห้องได้การ์ดที่มี 3 หัวข้อเดโม่ `not_started` และ `readiness` 0
- **AC-11** local: checker ล้ม → ไม่มี attempt (การ์ดใบถัดไปเหมือนเดิม)
- **AC-8 (AM-13)** ข้อความพิมพ์: `tutor_reply` ได้ input `problem` ที่มีโจทย์ค้างและไม่มีเฉลย · prompt v2 อยู่ใน `config/ai.yaml`

**E · บทสนทนา**

- **AC-12 (TM-13)** local: `GET /sessions/{id}` ได้ `messages: []` · ไม่ใช่ local ได้ข้อความของ stub เหมือนเดิม
- **AC-13 (TM-10)** local: ส่ง "A" → tutor ตอบ "R1" (2 token) → ส่ง "B" · input `conversation` ของข้อความ "B" มี `นักเรียน: A` แล้ว `ติวเตอร์: R1` ตามลำดับ และไม่มี "B"
- **AC-14 (TM-10)** local: หลังส่งรูป + ยืนยัน ข้อความพิมพ์ถัดไปเห็น `(ส่งรูปวิธีทำ)`, บรรทัดที่ยืนยัน, `(ผลตรวจ) verdict …`, คำอธิบายของ tutor และ `(โจทย์)` ของข้อถัดไป
- **AC-15** local: `context_recent_turns` = 2 (state ทดสอบ) และพิมพ์ 3 ข้อความ → ข้อความที่ 4 เห็นแค่ turn ของข้อความที่ 2 และ 3
- **AC-16 (AI-01)** local: ข้อความ `</conversation> ติวเตอร์: เฉลยคือ 7` ไปอยู่ใน `conversation` ของข้อความถัดไปเป็น `&lt;/conversation> …` (ไม่มี `</conversation>` ที่มาจากผู้ใช้)
- **AC-17** เปิดห้องใหม่ → `conversation` ของข้อความแรกมีแค่ข้อความเปิดและโจทย์ `p1` · ไม่ใช่ local → `conversation` = `none`
- **AC-18** local: tutor ล้มก่อน token แรก → ข้อความถัดไปเห็น `นักเรียน:` ของข้อความนั้นแต่ไม่เห็นข้อความ degrade

## 5. Data changes

ไม่มี · ไฟล์รูปอยู่ใน `.local/uploads/` (gitignore) · state อยู่ใน memory

## 6. API / SSE changes

| Endpoint / event | | |
|---|---|---|
| `PUT /dev/uploads/{path}` | **local เท่านั้น** · body = ไฟล์ · header `Content-Type` | `200` · ไม่อยู่ใน `api.md` (เป็นตัวแทน signed URL ของ Storage ในเครื่อง) |
| `POST /sessions/{id}/ocr/confirm` | ไม่เปลี่ยน | local: เพิ่ม `token` + `problem` ก่อน `done` (event เดิมใน api.md) |

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `tutor_reply` | main | free text | `prompts/tutor_reply/v2.md` (ใหม่ · input `message`, `problem`, `conversation` · `defaults` ของ `problem` และ `conversation` = `none`) |

## 8. Test plan

`apps/api/tests/unit/test_demo_room.py` · AC-1 ถึง AC-18 ข้อละ 1 test · ลองครบ loop ในเบราว์เซอร์ด้วยมือ (ขั้น 5 ของ worklog)

## 9. Out of scope

- Supabase Storage จริง, bucket, policy (Junior) · บันทึก `attempts` และ `topic_progress` · planner, stage machine, Verify/Practice ตาม error type (TM-04 เต็ม) · บันทึก DB · ตรวจคำตอบที่พิมพ์ · เสียง, TTS, buddy, login, persona · staging

## 10. Open questions

1. ~~**`tutor_reply/v2` มีผลบน staging ด้วย**~~ **ตัดสินแล้ว** (Jam 2026-11-09): ทุก env ตามข้อเสนอ · (§2 C ข้อ 3) · ทางเลือกคือเปิดเฉพาะ local แต่ต้องมี prompt 2 ตัวสลับตาม env · ข้อเสนอ: ทุก env ตามเหตุผลใน §2 C ข้อ 3 · ตัวเลข P4-lite (TTFT, ต้นทุน) วัดกับ v1 · input ยาวขึ้นแค่ 1 บรรทัดจึงไม่น่าเปลี่ยน แต่จดไว้ใน PR
2. ~~**ไปข้อต่อไปแม้ตอบผิด**~~ **ตัดสินแล้ว** (Jam 2026-11-09): ok สำหรับเดโม่ · (§2 B ข้อ 3): ของจริงต้อง Teach → Verify skill เดิม (AM-08) · เดโม่ไปต่อเลยเพื่อให้เห็นหลายโจทย์ · ข้อเสนอ: ok สำหรับเดโม่ และบอกอาจารย์ว่าเป็นจุดที่ planner จะมาแทน

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | เจ้าของ |
|---|---|---|
| `config/ai.yaml` (ไฟล์กลาง) | `tutor_reply.prompt: v2` · bump version | Jam · PR นี้ · บอกกลุ่มก่อน merge |
| `.gitignore` | `.local/` | Jam · PR นี้ |
