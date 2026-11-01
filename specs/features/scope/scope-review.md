# Feature: หน้าตรวจขอบเขต + ดาว

| | |
|---|---|
| Area | scope (หน้าเว็บ) |
| Requirements | SM-03 (แสดงดาว 1–3 ที่ code คำนวณ) · SM-04 (ที่มา: ชื่อไฟล์ + เลขหน้า + กดดูข้อความต้นฉบับ) · SM-02 (เรียงตามลำดับจาก API) · SM-09 (ยืนยันโดยไม่แก้ · UC-02 A5) |
| Owner | May |
| Reviewer | Junior (OQ 5–8 · api.md) |
| Status | approved by May 2026-10-28 (owner · OQ 1–4) · รอ Junior ตอบ OQ 5–8 (api.md) |
| Related system spec | ai-orchestration.md §2.3.4 (5d code คำนวณดาว), §2.3.5 (สูตรดาว · เหตุผลจาก template), §2.3.6 (`origin = user` ติดป้าย "นอกเอกสาร"), §2.3.8 (API 7, 8, 11) · api.md "Exam prep และ scope" · data-model.md `topics`, `past_exam_questions`, "รอผล" ข้อ 1 (ช่วงหน้า), ข้อ 3 (`map_note`) · use-cases.md UC-02 ขั้น 7–8, A4, A5, E1 · wireframe S12, S38 · `config/learning.yaml` → `stars` (ฝั่ง backend เท่านั้น) |

## 1. Context

หลังอ่านไฟล์เสร็จ (S11) ผู้ใช้ต้องตรวจรายการหัวข้อที่ AI สกัดจากชีทก่อนเริ่มติว (UC-02 ขั้น 7) · หน้านี้ทำให้ผู้ใช้เชื่อระบบ: ทุกหัวข้อบอกว่ามาจากไฟล์ไหนหน้าไหน และกดดูข้อความจากชีทได้ (SM-04 · wireframe S12 "เธอเลยเชื่อ") · ดาวคำนวณโดย code ฝั่ง backend จากความถี่ในข้อสอบเก่า (§2.3.5) หน้าเว็บแสดงอย่างเดียว ไม่คำนวณ (apps/web/CLAUDE.md) · feature นี้ทำหน้า S12 และรายละเอียดของหัวข้อ (S38) · แชทแก้ขอบเขต (S13) และหน้าสรุป (S14) เป็นงานแยก

## 2. Behavior

**ที่อยู่:** `/preps/[id]/scope` · โหลด `GET /exam-preps/{id}/scope` (รูปร่างข้อเสนอใน §3 · OQ 5)

**หัวหน้า**

- "ตรวจขอบเขตก่อนเริ่ม" และบรรทัดรอง "{prep_name} · สอบใน {days_left} วัน · AI เรียงลำดับให้แล้ว" (wireframe S12)

**รายการหัวข้อ** (เรียงตามลำดับที่ API ส่งมา · SM-02 · หน้าเว็บไม่เรียงใหม่ ยกเว้นย้ายหัวข้อ 0 ดาวไปท้าย)

- แต่ละหัวข้อเป็นแถวที่กดได้ (`button` · `aria-expanded`) มี:
  - เลขลำดับ + ชื่อ เช่น "3 · ผลต่างกำลังสอง" · เลขคือ `order` จาก API (OQ 5)
  - ที่มาแบบสั้น + เหตุผล เป็นตัวเล็ก: "{source_label} · {reason}" เช่น "ch3 น.5–6 · ออกทุกชุด" · ทั้งสองเป็นข้อความจาก API (`reason` สร้างจาก template ฝั่ง backend §2.3.5)
  - ดาว 3 ดวง เติมตาม `stars` (แบบเดียวกับการ์ดความคืบหน้า · `aria-label` "{n} ดาว")
  - ป้าย "นอกเอกสาร" เมื่อ `origin = "user"` (§2.3.6)
- **หัวข้อ 0 ดาว** (ตัดออกเพราะ note หรือผู้ใช้ · §2.3.5): แสดง**ท้ายรายการ** (ลำดับระหว่างกันตาม API) เป็นสีจาง มีป้าย "ตัดออก" ดาวว่าง 3 ดวง `aria-label` "0 ดาว" · ยังกดดูรายละเอียดได้ (ตัดสินแล้ว OQ 3 · ผู้ใช้ต้องเห็นว่าอะไรถูกตัด เพราะคนตัดสินคือผู้ใช้ · wireframe S12)
- `stars` นอก 0–3 หรือ `null` → ดาวว่าง 3 ดวง และ `aria-label` "—" (ไม่ crash)

**รายละเอียดหัวข้อ (S38 · UC-02 A4)**

- กดแถว → การ์ดขยาย แล้วโหลด `GET /topics/{id}/sources` (ครั้งแรกเท่านั้น ครั้งต่อไปใช้ของเดิม) · ระหว่างโหลดแสดง "กำลังโหลด…"
- แสดง:
  - **จากชีท:** ทุกข้อความต้นฉบับ (`excerpts`) หัวเป็น "จากชีท · {material_name} หน้า {page}" ตามด้วยข้อความ · ข้อความเป็น**ข้อมูล** แสดงเป็น text ธรรมดา ไม่ render HTML (กัน injection · §2.3.9 ข้อ 5)
  - **ข้อสอบเก่าในหัวข้อนี้ · {n} ข้อ:** แต่ละข้อมี `label` (เช่น "midterm-2566 ข้อ 3") และ `text` · `map_note` ถ้ามีแสดงเป็นตัวเล็ก "AI: {map_note}" (May ตัดสิน #67)
  - ไม่มีข้อสอบในหัวข้อ → "ยังไม่เคยออกในข้อสอบเก่า"
- โหลดไม่สำเร็จ → "โหลดที่มาไม่สำเร็จ" + ปุ่ม "ลองใหม่" ในการ์ด
- กดแถวอีกครั้ง → พับ (wireframe S38 "กดอีกครั้งเพื่อพับ") · เปิดได้หลายหัวข้อพร้อมกัน (ตัดสินแล้ว OQ 2)

**ข้อสอบที่ไม่เข้าหัวข้อไหน** (S38)

- ถ้า `unmapped_questions` ไม่ว่าง → กล่องเส้นประใต้รายการ หัว "ข้อสอบที่ไม่เข้าหัวข้อไหน · {n} ข้อ" แต่ละข้อมี `label`, `text`, "AI: {map_note}" และท้ายกล่อง "ถ้าข้อนี้ควรอยู่ในขอบเขต กด “ขอแก้ก่อน” แล้วบอก AI"
- ว่าง → ไม่มีกล่อง

**ปุ่ม**

- "ยืนยันขอบเขตนี้" (UC-02 A5 · SM-09): เรียก `POST /exam-preps/{id}/scope/confirm` → สำเร็จแล้วไปห้องติว `/preps/{id}/room` · ระหว่างรอปุ่มกดไม่ได้ · ไม่สำเร็จ → "ยืนยันไม่สำเร็จ ลองอีกครั้งนะ" และอยู่หน้าเดิม
- "ขอแก้ก่อน" (ไป S13): S13 ยังไม่มี → แสดงแต่กดไม่ได้ (`disabled`) และมีข้อความเล็ก "แก้ผ่านแชทได้เร็วๆ นี้" (ตัดสินแล้ว OQ 1)
- ข้อความใต้ปุ่ม "กด “ยืนยันขอบเขตนี้” ถ้าโอเคแล้ว หรือ “ขอแก้ก่อน” ถ้าอยากปรับ"

**สถานะของหน้า**

- กำลังโหลด → "กำลังโหลดขอบเขต…" · โหลดไม่สำเร็จ → "โหลดขอบเขตไม่สำเร็จ" + "ลองใหม่" · ไม่พบ (404) → "ไม่พบการเตรียมสอบนี้" + ลิงก์กลับหน้าหลัก (แบบเดียวกับห้องติว · room-http.md)
- `topics` ว่าง → "ยังไม่มีหัวข้อ" และปุ่มยืนยันกดไม่ได้
- ขอบเขตยืนยันแล้ว (`status = "confirmed"`) → **อ่านอย่างเดียว**: ไม่มีปุ่ม "ขอแก้ก่อน" และ "ยืนยันขอบเขตนี้" · มีข้อความ "ยืนยันขอบเขตแล้ว" และลิงก์ "ไปห้องติว" (`/preps/{id}/room`) · ยังกดดูรายละเอียดหัวข้อได้ (ตัดสินแล้ว OQ 4)

## 3. Inputs and outputs (ข้อเสนอ · OQ 5)

| | Type / schema | ตัวอย่าง |
|---|---|---|
| `GET /exam-preps/{id}/scope` | `{prep_name, days_left, status: "draft" \| "confirmed", topics: [{id, order, name, stars, reason, source_label, origin: "doc" \| "user"}], unmapped_questions: [{id, label, text, map_note}]}` | `{topics: [{id: "t3", order: 3, name: "ผลต่างกำลังสอง", stars: 3, reason: "ออกทุกชุด", source_label: "ch3 น.5–6", origin: "doc"}], unmapped_questions: [{id: "q11", label: "midterm-2567 ข้อ 11", text: "แก้สมการ $x^2 - 5x + 6 = 0$", map_note: "เป็นเรื่องสมการกำลังสอง ไม่มีในชีทที่ใส่มา"}]}` |
| `GET /topics/{id}/sources` | `{excerpts: [{material_name, page, text}], questions: [{id, label, text, map_note}]}` | `{excerpts: [{material_name: "ch3-factorization.pdf", page: 5, text: "a² − b² = (a − b)(a + b) ใช้เมื่อ…"}], questions: [{id: "q3", label: "midterm-2566 ข้อ 3", text: "$x^2 - 49$", map_note: null}]}` |
| `POST /exam-preps/{id}/scope/confirm` | `{}` | 200 / non-2xx |

- `text` ของข้อสอบมีสมการ → render ผ่าน `MessageText` (`$…$` แบบเดียวกับข้อความในห้อง · api.md Conventions) (OQ 7)
- `source_label` เป็นข้อความพร้อมแสดงจาก backend (หน้าเว็บไม่ตัดชื่อไฟล์หรือรวมช่วงหน้าเอง) (OQ 6)

## 4. Acceptance criteria

ใช้ fixture `tests/fixtures/scope/scope-s12.json` (หัวข้อ 6 ข้อตาม wireframe S12 + ข้อสอบไม่เข้าหัวข้อ 1 ข้อตาม S38) และ `sources-t3.json` (S38) · fetch จำลอง ไม่ใช้ API จริง

**รายการ**

- **AC-1 (SM02)** Given fixture When เปิดหน้า Then มีหัวข้อ 6 แถวเรียงตาม fixture: "1 · คูณพหุนาม", "2 · ดึงตัวประกอบร่วม", "3 · ผลต่างกำลังสอง", "5 · แยก x²+bx+c", "7 · การจัดกลุ่ม", "9 · กำลังสาม" (ลำดับและเลขมาจาก API ไม่เรียงใหม่)
- **AC-2 (SM03)** Then ดาวที่เติมของแต่ละแถว = `stars` ใน fixture (2, 3, 3, 3, 2, 1) และ `aria-label` "{n} ดาว"
- **AC-3 (SM03)** Given หัวข้อที่ `stars` เป็น 4 หรือ `null` Then ไม่มีดาวที่เติม และ `aria-label` "—" ไม่ crash
- **AC-3b (SM03 · OQ 3)** Given fixture ที่หัวข้อ "กำลังสาม" มี `stars: 0` อยู่กลางรายการ Then แถวนั้นอยู่**ท้ายรายการ** มีป้าย "ตัดออก" ดาวว่าง `aria-label` "0 ดาว" · แถวอื่นยังเรียงตาม API · กดดูรายละเอียดได้
- **AC-4 (SM04)** Then แต่ละแถวมี "{source_label} · {reason}" เช่น "ch3 น.5–6 · ออกทุกชุด"
- **AC-5 (SM03)** Given หัวข้อ `origin = "user"` Then มีป้าย "นอกเอกสาร" · `origin = "doc"` ไม่มี
- **AC-6 (SM03)** หน้าเว็บไม่คำนวณดาว: Given fixture ที่ `stars` ขัดกับ `reason` (เช่น `stars: 1`, `reason: "ออกทุกชุด"`) Then แสดง 1 ดาวตาม API

**รายละเอียด (S38)**

- **AC-7 (SM04)** Given หัวข้อ 3 พับอยู่ (`aria-expanded="false"`) When กด Then `aria-expanded="true"`, fetch `GET /topics/t3/sources` 1 ครั้ง, เห็น "จากชีท · ch3-factorization.pdf หน้า 5" และข้อความต้นฉบับ, "ข้อสอบเก่าในหัวข้อนี้ · 3 ข้อ" และ 3 ข้อตาม fixture
- **AC-8 (SM04)** Given ข้อสอบที่มี `map_note` Then มี "AI: {map_note}" ใต้ข้อนั้น · `map_note = null` ไม่มีบรรทัด "AI:"
- **AC-9 (SM04)** Given ข้อความต้นฉบับมี `<b>ตัวหนา</b><script>` Then แสดงเป็นตัวอักษรตามนั้น ไม่มี element `b` หรือ `script` ในการ์ด
- **AC-10 (SM04)** Given หัวข้อเปิดอยู่ When กดอีกครั้ง Then พับ · When กดเปิดอีกครั้ง Then ไม่ fetch ซ้ำ (ใช้ของเดิม)
- **AC-11 (SM04)** Given `questions` ว่าง Then "ยังไม่เคยออกในข้อสอบเก่า"
- **AC-12 (SM04)** Given fetch sources ล้ม When เปิดหัวข้อ Then "โหลดที่มาไม่สำเร็จ" + ปุ่ม "ลองใหม่" · กด "ลองใหม่" แล้ว fetch อีกครั้ง
- **AC-13 (TM08)** Given ข้อสอบ `text = "$x^2 - 49$"` Then มี KaTeX ที่ source `x^2 - 49`

**ข้อสอบไม่เข้าหัวข้อ**

- **AC-14 (SM04)** Given `unmapped_questions` 1 ข้อ Then มีกล่อง "ข้อสอบที่ไม่เข้าหัวข้อไหน · 1 ข้อ" พร้อม label, ข้อความ และ "AI: …" · Given ว่าง Then ไม่มีกล่อง

**ปุ่มและสถานะ**

- **AC-15 (SM09)** When กด "ยืนยันขอบเขตนี้" Then POST `/exam-preps/{id}/scope/confirm` 1 ครั้ง ระหว่างรอปุ่มกดไม่ได้ · สำเร็จ Then ไปที่ `/preps/{id}/room`
- **AC-16 (SM09)** Given POST ล้ม Then "ยืนยันไม่สำเร็จ ลองอีกครั้งนะ" อยู่หน้าเดิม ปุ่มกดได้อีก
- **AC-17** Given โหลด scope ระหว่างทาง Then "กำลังโหลดขอบเขต…" · ล้ม Then "โหลดขอบเขตไม่สำเร็จ" + "ลองใหม่" · 404 Then "ไม่พบการเตรียมสอบนี้" + ลิงก์ "กลับหน้าหลัก"
- **AC-18** Given `topics` ว่าง Then "ยังไม่มีหัวข้อ" และปุ่มยืนยันกดไม่ได้
- **AC-19 (OQ 1)** ปุ่ม "ขอแก้ก่อน" มีแต่กดไม่ได้ และมี "แก้ผ่านแชทได้เร็วๆ นี้"
- **AC-19b (SM09 · OQ 4)** Given `status = "confirmed"` Then ไม่มีปุ่ม "ขอแก้ก่อน" และ "ยืนยันขอบเขตนี้" · มี "ยืนยันขอบเขตแล้ว" และลิงก์ "ไปห้องติว" ที่ `href = /preps/{id}/room` · ยังกดเปิดรายละเอียดหัวข้อได้
- **AC-20** แถวหัวข้อเป็นปุ่มที่กดด้วย keyboard ได้ (Enter / Space) และมี `aria-expanded`

**AC-boundary:** หน้าเว็บไม่ใช้ threshold ของดาว (`stars.three_star_min_r` ฯลฯ อยู่ใน backend) · ขอบของค่าที่แสดง: `stars` 0, 1, 3, 4, `null` (AC-2, AC-3) · **AC-tenant (SA-06):** หน้าเว็บไม่อ่าน DB เอง · API ใช้ RLS ของ `topics` และ `past_exam_questions` (ฝั่ง backend · Junior)

## 5. Data changes

ไม่มีในหน้าเว็บ · ฝั่ง backend ต้องมีที่เก็บช่วงหน้า (data-model "รอผล" ข้อ 1) และ `map_note` (ข้อ 3) จึงจะส่ง `source_label`, `excerpts` และ `map_note` ได้ (OQ 6, 8)

## 6. API / SSE changes

| Endpoint | Request | Response |
|---|---|---|
| `GET /exam-preps/{id}/scope` | — | **ยังไม่กำหนดรูปร่าง** · ข้อเสนอ §3 |
| `GET /topics/{id}/sources` | — | **ยังไม่กำหนดรูปร่าง** · ข้อเสนอ §3 (รวมข้อสอบเก่าในหัวข้อ) |
| `POST /exam-preps/{id}/scope/confirm` | — | มีชื่อใน api.md แล้ว · ยังไม่มี stub |

ยังไม่มีใน OpenAPI → type เขียนเองชั่วคราว (เหมือน `OcrPreviewData`) จนกว่าจะมี schema แล้ว `pnpm gen:api`

## 7. AI calls

ไม่มี (หน้าเว็บอ่านผลที่ backend คำนวณแล้ว)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/scope/ScopeReview.test.tsx` (ใหม่) | component + fetch จำลอง | AC-1 ถึง AC-20 |

## 9. Out of scope

- แชทแก้ขอบเขต (S13 · SM-06, SM-07) และหน้าสรุป (S14 · SM-08) · feature ถัดไป
- หัวข้อที่ระบบเสนอให้ตัด (SM-05 · deferred)
- แสดง skills (SM-12 · ไม่แสดงใน S12)
- หน้าก่อนหน้า (S07–S11) และเมนูด้านซ้าย (`SIDE` ใน wireframe)

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-28)

1. **"ขอแก้ก่อน" ระหว่างที่ยังไม่มี S13:** แสดงแต่กดไม่ได้ + "แก้ผ่านแชทได้เร็วๆ นี้" (AC-19)
2. **เปิดรายละเอียด:** หลายหัวข้อพร้อมกัน
3. **หัวข้อ 0 ดาว:** แสดงท้ายรายการ สีจาง ป้าย "ตัดออก" (AC-3b) · API ต้องส่งหัวข้อที่ `status = excluded` มาด้วย (OQ 5)
4. **หลังยืนยันแล้ว:** อ่านอย่างเดียว + ลิงก์ไปห้องติว (AC-19b)

ให้ Junior ตอบ (api.md · ไฟล์ร่วม)

5. **รูปร่างของ `GET /scope`:** ตามข้อเสนอ §3 ได้ไหม · `order` คือ `topics.order_index` (นับจาก 1?) · `reason` ทำจาก template ฝั่ง backend (§2.3.5) · `status` ของ scope · ส่งหัวข้อที่ตัดออก (`topics.status = excluded`, 0 ดาว) มาด้วย
6. **`source_label` และ `excerpts`:** ต้องมีที่เก็บช่วงหน้า (data-model "รอผล" ข้อ 1) · ใครย่อชื่อไฟล์ ("ch3") · ข้อความต้นฉบับมาจาก `material_pages` ใช่ไหม
7. **`text` ของข้อสอบเก่า:** ใช้ `$…$` แบบข้อความในห้อง (api.md Conventions) ได้ไหม
8. **`map_note`:** เก็บที่ `past_exam_questions.map_note` (data-model "รอผล" ข้อ 3 · ตกลงใน #67 ว่าเก็บ + แสดง)

## 11. Spec changes needed

- **api.md** (Junior): OQ 5–8 · response ของ `GET /exam-preps/{id}/scope`, `GET /topics/{id}/sources`, stub ของทั้งสอง + `scope/confirm`
- **data-model.md** "รอผล" ข้อ 1, 3 (Junior)
