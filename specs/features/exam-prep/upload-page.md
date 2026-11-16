# Feature: หน้าอัปโหลดหลายไฟล์ + สถานะรายไฟล์ (demo ขั้น 3 ฝั่งเว็บ)

| | |
|---|---|
| Area | platform (หน้าเว็บ · exam prep) |
| Requirements | CM-03 (อัปโหลดหลายไฟล์ PDF รูป เอกสาร) · CM-07 (สถานะรายไฟล์ + ความคืบหน้าระหว่างรอ) · CM-06 (ส่วนแสดงประเภทที่ AI เดาพร้อม confidence + ยืนยัน · แก้ประเภทอยู่ใน S5) · SA-06 (ทุก request ผ่าน `apiFetch` พร้อม token) |
| Owner | May (Jam ทำช่วง solo 16 พ.ย. · PR #142 · May ดูย้อนหลัง) |
| Reviewer | Jam · May ดูหน้าตาและ §10 ย้อนหลัง · Junior ดูสัญญา API (#140) |
| Status | approved 2026-11-16 (Jam ok spec · §10 ข้อ 1 เลือก (ก)) |
| Related system spec | api.md "สร้างการเตรียมสอบและใส่ไฟล์" v1.10 + v1.13 (materials · ข้อเสนอ รอ Junior) และ "ความคืบหน้า…" v1.11 + v1.16 (`Ingestion` อ่าน DB แล้ว) · ai-orchestration.md §2.3.2 ขั้น 1–4 · use-cases.md UC-02 ขั้น 3–6, A3, E5, E6 · wireframe S09, S10, S11 · `room-photo-send.md` §2 ข้อ 2 (ข้าม `PUT` เมื่อ `X-Stub`) · `prep-list-page.md` (การ์ดและหลังสร้าง) · `web-login.md` §2.3 (401) |

## 1. Context

demo ขั้น 3: หลังสร้างการเตรียมสอบ (#139) ผู้ใช้ต้องใส่ชีทและข้อสอบเก่าหลายไฟล์ แล้วรอระบบอ่านจนได้หัวข้อ (UC-02 ขั้น 3–6) · ตอนนี้การ์ด "รออัปโหลดไฟล์" ในหน้ารายการยังกดไม่ได้ เพราะไม่มีหน้านี้ · feature นี้ทำ 2 หน้า: หน้าใส่ไฟล์ (S09 + S10 แบบย่อ) และหน้ารออ่านไฟล์ (S11) ที่ไปหน้า scope (#141) เองเมื่ออ่านเสร็จ · API จริงของ materials อยู่ใน #140 (Junior) · จนกว่าจะเสร็จ endpoint ของ materials เป็น stub (`X-Stub: true`) หน้าเว็บทำตามสัญญา api.md v1.10 ไปก่อน

## 2. Behavior

ทุก request ผ่าน `apiFetch` (`lib/auth.ts` · ใส่ token · 401 พาไปหน้า login) · ข้อความทั้งหมดอยู่ใน `components/materials/strings.ts` · ตัวเลขที่แสดงมาจาก API ทั้งหมด (apps/web/CLAUDE.md)

### 2.1 หน้าใส่ไฟล์ `/preps/[id]/upload` (S09 → S10)

**เปิดหน้า:** โหลด `GET /exam-preps/{id}/materials` · มีไฟล์ที่ `kind_confirmed = false` → เริ่มที่ขั้นตรวจประเภท (2.1.2) ทันที (ผู้ใช้ปิดเว็บไประหว่างทาง · UC-02 E6) · ไม่มี → ขั้นใส่ไฟล์ (2.1.1) · `404` → "ไม่พบการเตรียมสอบนี้" + ลิงก์ "กลับหน้าหลัก" · error อื่น → "โหลดไฟล์ไม่สำเร็จ" + "ลองใหม่" · `401` → ไม่แสดง error

#### 2.1.1 ใส่ไฟล์ (S09 · CM-03)

1. หัว "ใส่สิ่งที่จะใช้สอบ" · บรรทัดรอง "ใส่ชีท ข้อสอบเก่า หรือรูปโน้ตได้หลายไฟล์พร้อมกัน"
2. ปุ่มเลือกไฟล์ (`<input type="file" multiple>` มี label "เลือกไฟล์") · `accept` = ชนิดที่ api.md รับ (PDF, JPEG, PNG, WebP, HEIC, PPTX, DOCX) เพื่อช่วยกรองในหน้าต่างเลือกไฟล์ · API เป็นคนตัดสินจริง (§2.1.1 ข้อ 6)
3. เลือกได้หลายรอบ ไฟล์ต่อท้ายรายการ · แต่ละแถว: ชื่อไฟล์ + ขนาด ("{n} MB" ทศนิยม 1 ตำแหน่ง หรือ "{n} KB" ถ้าไม่ถึง 1 MB) + ปุ่ม "เอาออก" (ก่อนส่งเท่านั้น)
4. ปุ่ม "ส่งทั้งหมดให้ AI อ่าน" กดได้เมื่อมีไฟล์อย่างน้อย 1 ไฟล์ และไม่ได้กำลังส่ง · ลิงก์ "ย้อนกลับ" ไป `/`
5. กดส่ง → ส่ง**ทีละไฟล์ตามลำดับในรายการ** ต่อไฟล์:
   1. `POST /exam-preps/{id}/materials` body `{file_name: file.name, content_type: file.type || "application/octet-stream", size_bytes: file.size}`
   2. response มี header `X-Stub: true` → **ข้าม** `PUT` (URL ของ stub ใช้จริงไม่ได้ · แบบเดียวกับ `room-photo-send.md` §2 ข้อ 2) · ไม่มี → `PUT {upload_url}` body = ไฟล์ · header `Content-Type: file.type` · **ไม่ส่ง** `Authorization` (signed URL) · ไม่ผ่าน `apiFetch`
   3. `POST /materials/{material_id}/uploaded` body `{}` (ไม่มี note · CM-04 อยู่ใน S5)
   - สถานะในแถว: รอส่ง → "กำลังอัปโหลด…" → "อัปโหลดแล้ว" · ล้ม → ข้อความสีแดงในแถวนั้น แล้วไปไฟล์ถัดไป (ไฟล์อื่นไม่รอ · แบบ UC-02 E5)
6. ข้อความเมื่อล้ม (ตาม error code ของ api.md):
   - `422 unsupported_type` → "ไฟล์ชนิดนี้ยังไม่รองรับ"
   - `422 file_too_large` → "ไฟล์ใหญ่เกินไป"
   - `PUT` ไม่ผ่าน, error อื่น, network → "อัปโหลดไม่สำเร็จ"
   - `401` → หยุดส่งไฟล์ที่เหลือ ไม่แสดง error (`apiFetch` พาไป login)
7. ส่งครบทุกไฟล์แล้ว:
   - สำเร็จอย่างน้อย 1 ไฟล์ → ไปขั้นตรวจประเภท (2.1.2)
   - ไม่สำเร็จเลย → อยู่ขั้นนี้ แถวที่ล้มยังแสดงข้อความ · ปุ่ม "เอาออก" กลับมาใช้ได้ · เลือกไฟล์ใหม่แล้วส่งได้อีก (ส่งเฉพาะแถวที่ยังไม่สำเร็จ)

#### 2.1.2 ตรวจประเภท (S10 แบบย่อ · CM-06 ส่วนแสดง + ยืนยัน)

1. หัว "AI เดาไว้แบบนี้" · บรรทัดรอง "ตรวจแล้วกดยืนยันเพื่อเริ่มอ่านไฟล์"
2. poll `GET /exam-preps/{id}/materials` ทุก `POLL_MS` (ค่าคงที่ของหน้าเว็บ · §10 ข้อ 3) · แสดงเฉพาะไฟล์ที่ `kind_confirmed = false` เรียงตาม API
3. แต่ละแถว: ชื่อไฟล์ และตาม `status`:
   - `uploaded` → "AI กำลังดูไฟล์…"
   - `classified` → ประเภทเป็นภาษาไทย (`sheet` ชีทเรียน · `slides` สไลด์ · `past_exam` ข้อสอบเก่า · `notes` โน้ต · `other` อื่นๆ) + "มั่นใจ {round(kind_confidence × 100)}%" (ไม่มี `kind_confidence` → ไม่แสดงส่วนนี้)
   - `failed` → `error` จาก API (ไม่มี → "อ่านไฟล์นี้ไม่ได้") สีแดง · ไม่ส่งไปยืนยัน (api.md: "ไฟล์ `failed` ไม่ต้องส่ง")
4. หยุด poll เมื่อไม่มีไฟล์ `uploaded` เหลือ
5. ปุ่ม "ยืนยันแล้วเริ่มประมวลผล" กดได้เมื่อไม่มีไฟล์ `uploaded` และมีไฟล์ `classified` อย่างน้อย 1 ไฟล์ → `POST /exam-preps/{id}/materials/confirm` body `{materials: [{id, kind}]}` ของทุกไฟล์ `classified` ด้วย `kind` ที่ AI เดา (ยังแก้ไม่ได้ · §9) · ระหว่างรอปุ่มกดไม่ได้
   - `202` → ไป `/preps/{id}/progress`
   - `409 not_classified` → โหลดรายการใหม่ แล้วเริ่ม poll อีกครั้ง (สถานะเปลี่ยนไประหว่างทาง) ไม่แสดง error
   - error อื่น, network → "เริ่มอ่านไฟล์ไม่สำเร็จ ลองอีกครั้งนะ" ปุ่มกดได้อีก · `401` → ไม่แสดง error
6. ไม่มีไฟล์ `classified` เลย (ทุกไฟล์ `failed`) → "ไม่มีไฟล์ที่อ่านได้" + ปุ่ม "ใส่ไฟล์ใหม่" กลับไปขั้นใส่ไฟล์ (รายการว่าง)
7. ไม่มีปุ่ม "ถูกหมดแล้ว ข้ามเลย" (UC-02 A3) แยก เพราะยังแก้ประเภทไม่ได้ ปุ่มยืนยันทำหน้าที่เดียวกัน (§10 ข้อ 2)

### 2.2 หน้ารออ่านไฟล์ `/preps/[id]/progress` (S11 · CM-07)

1. หัว "กำลังอ่านไฟล์ของคุณ" · บรรทัดรอง "หน้านี้ไปต่อเอง ไม่ต้องกดอะไร" (wireframe S11)
2. poll `GET /exam-preps/{id}/ingestion` ทุก `POLL_MS` (ครั้งแรกทันทีที่เปิดหน้า)
3. **ไฟล์** (`files` ตามลำดับของ API): สัญลักษณ์ตาม `status` (`queued` ○ · `running` ◐ · `done` ✓ · `failed` ✕ · มี `aria-label` เป็นข้อความ "รอ", "กำลังอ่าน", "เสร็จแล้ว", "ไม่สำเร็จ") + ชื่อไฟล์ + `detail` จาก API (เช่น "14 หน้า", "กำลังแยกรายข้อ") · `failed` → `error` จาก API สีแดง (ไม่มี → "อ่านไฟล์นี้ไม่สำเร็จ")
4. **ขั้นรวม** (`steps` ตามลำดับของ API): สัญลักษณ์แบบเดียวกัน (`pending` ○ · `running` ◐ · `done` ✓ · `failed` ✕) + `label` จาก API (ข้อความพร้อมแสดง · ไม่แปลเอง)
5. `scope_ready = true` → หยุด poll แล้วไป `/preps/{id}/scope` เอง
6. `files` ว่างและ `scope_ready = false` → "ยังไม่มีไฟล์ที่ส่งให้อ่าน" + ลิงก์ "ใส่ไฟล์" ไป `/preps/{id}/upload` · หยุด poll
7. error: `404` → "ไม่พบการเตรียมสอบนี้" + "กลับหน้าหลัก" · `401` → ไม่แสดง error · error อื่น, network → หยุด poll + "โหลดความคืบหน้าไม่สำเร็จ" + "ลองใหม่" (กดแล้ว poll ต่อ) · ถ้ามีผลครั้งก่อนอยู่ ยังแสดงผลนั้นไว้ด้านบนข้อความ
8. ไฟล์ที่ `failed` ไม่มีปุ่ม "ลองใหม่" / "ไปต่อโดยไม่มีไฟล์นี้" (UC-02 E5 · §9) · ลิงก์ "กลับหน้าหลัก" แสดงตลอด

### 2.3 การ poll กับหน้าที่ Next ซ่อนไว้

- Next 16 (`cacheComponents`) ซ่อนหน้าที่ออกไปด้วย React `<Activity>` และเก็บ state · ซ่อนแล้ว**หยุด poll** และยกเลิก request ที่ค้าง (effect cleanup) · แสดงอีกครั้ง → โหลดใหม่ทันทีแล้ว poll ต่อ
- เปลี่ยนหน้าเอง (ไป progress / scope) เกิดเฉพาะตอนหน้ายังแสดงอยู่ (แบบ `CreatePrepForm` · self-review #139)

### 2.4 หน้ารายการและหลังสร้าง (แก้ `prep-list-page.md` · §11)

- `prepHref`: `materials` → `/preps/{id}/upload` · `processing` → `/preps/{id}/progress` (เดิมไม่เป็นลิงก์) · `scope`, `tutoring` เหมือนเดิม
- สร้าง prep สำเร็จ (`201`) → ไป `/preps/{id}/upload` ของ prep ใหม่ (`id` จาก response) แทน `/` (`prep-list-page.md` §10 ข้อ 2 · ข้อเสนอเดิม "หลัง demo ขั้น 3 ไปหน้าอัปโหลด")

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| `POST /exam-preps/{id}/materials` | req `UploadMaterialRequest {file_name, content_type, size_bytes}` · res `MaterialUploadTicket {material_id, upload_url, path}` (+ `X-Stub: true` ตอนเป็น stub) | `{file_name: "sheet-01.pdf", content_type: "application/pdf", size_bytes: 2400000}` |
| `PUT {upload_url}` | body ไฟล์ · `Content-Type` ของไฟล์ | — |
| `POST /materials/{id}/uploaded` | req `{}` · res `202` + `Material` | — |
| `GET /exam-preps/{id}/materials` | `Material[]` | `{id, file_name: "midterm-2566.pdf", kind: "past_exam", kind_confidence: 0.93, kind_confirmed: false, user_note: null, status: "classified", error: null}` |
| `POST /exam-preps/{id}/materials/confirm` | req `{materials: [{id, kind}]}` · res `202 {queued}` | `{materials: [{id: "m1", kind: "sheet"}]}` |
| `GET /exam-preps/{id}/ingestion` | `Ingestion {scope_ready, files: IngestionFile[], steps}` | `{scope_ready: false, files: [{material_id, file_name: "midterm-2567.pdf", status: "running", detail: "กำลังแยกรายข้อ", error: null}], steps: [{label: "หาหัวข้อและลำดับการเรียน", status: "pending"}]}` |

type ทั้งหมดใช้ที่ generate จาก OpenAPI (`lib/api-schema.ts`) ไม่เขียนเอง

## 4. Acceptance criteria

fetch จำลองทั้งหมด (ไม่ใช้ API จริง) · ไฟล์จำลองด้วย `File` ของ jsdom · `POLL_MS` ใน test ใช้ fake timers

**ใส่ไฟล์ (S09)**

- **AC-1 (CM03)** Given prep ไม่มีไฟล์ When เปิด `/preps/p1/upload` Then เห็น "ใส่สิ่งที่จะใช้สอบ" · input file มี `multiple` และ label "เลือกไฟล์" · `accept` มี `.pdf`, `.pptx`, `.docx`, `image/*` · ปุ่ม "ส่งทั้งหมดให้ AI อ่าน" กดไม่ได้
- **AC-2 (CM03)** When เลือก 2 ไฟล์ ("sheet-01.pdf" 2,400,000 bytes, "โน้ต.jpg" 900,000 bytes) แล้วเลือกอีก 1 ไฟล์ Then มี 3 แถวตามลำดับ ขนาด "2.3 MB" และ "879 KB" · กด "เอาออก" ที่แถวแรก Then เหลือ 2 แถว
- **AC-3 (CM03)** Given 2 ไฟล์ และ API ไม่ใช่ stub When กดส่ง Then request ตามลำดับ: `POST /exam-preps/p1/materials` (body ตาม §2.1.1 ข้อ 5.1) → `PUT {upload_url}` (body เป็นไฟล์ · `Content-Type` ของไฟล์ · ไม่มี `Authorization`) → `POST /materials/m1/uploaded` body `{}` → แล้วไฟล์ที่ 2 แบบเดียวกัน · ระหว่างส่งปุ่มกดไม่ได้ และแถวที่กำลังส่งแสดง "กำลังอัปโหลด…"
- **AC-4 (CM03)** Given `POST /materials` ตอบ header `X-Stub: true` Then ไม่มี `PUT` และยังเรียก `/uploaded`
- **AC-5 (CM03)** Given ไฟล์ `file.type` ว่าง Then `content_type` เป็น `"application/octet-stream"`
- **AC-6 (CM03)** Given ไฟล์แรกได้ `422 unsupported_type` ไฟล์ที่สองได้ `422 file_too_large` ไฟล์ที่สามสำเร็จ Then แถวแรก "ไฟล์ชนิดนี้ยังไม่รองรับ" แถวที่สอง "ไฟล์ใหญ่เกินไป" ไม่มี `PUT` ของสองไฟล์นั้น และไฟล์ที่สามยังถูกส่ง แล้วไปขั้นตรวจประเภท
- **AC-7 (CM03)** Given `PUT` ตอบ 403 หรือ network ล้ม Then แถวนั้น "อัปโหลดไม่สำเร็จ" ไม่เรียก `/uploaded` ของไฟล์นั้น
- **AC-8 (CM03)** Given ทุกไฟล์ล้ม Then อยู่ขั้นใส่ไฟล์ · ข้อความในแถวยังอยู่ · เลือกไฟล์เพิ่มแล้วกดส่ง Then ส่งเฉพาะแถวที่ยังไม่สำเร็จ
- **AC-9 (UM01)** Given `POST /materials` ของไฟล์แรกตอบ `401` Then ไม่ส่งไฟล์ที่เหลือ และไม่มีข้อความ error ในหน้า

**ตรวจประเภท (S10 แบบย่อ)**

- **AC-10 (CM06)** Given อัปโหลดสำเร็จ และ `GET /materials` ครั้งแรกได้ไฟล์ m1 `uploaded`, ครั้งที่สอง (หลัง `POLL_MS`) m1 `classified` `kind: "past_exam"` `kind_confidence: 0.934` Then ครั้งแรกเห็น "AI กำลังดูไฟล์…" และปุ่ม "ยืนยันแล้วเริ่มประมวลผล" กดไม่ได้ · ครั้งที่สองเห็น "ข้อสอบเก่า" และ "มั่นใจ 93%" ปุ่มกดได้ · หลังจากนั้นไม่ poll อีก
- **AC-11 (CM06)** Given ทุกค่าของ `kind` Then แสดง "ชีทเรียน", "สไลด์", "ข้อสอบเก่า", "โน้ต", "อื่นๆ" · `kind_confidence = null` ไม่มีคำว่า "มั่นใจ"
- **AC-12 (CM06)** Given m1 `classified` (`sheet`), m2 `failed` (`error: "เปิดไฟล์นี้ไม่ได้"`), m3 `kind_confirmed: true` When กดยืนยัน Then เห็น "เปิดไฟล์นี้ไม่ได้" ที่ m2 · ไม่มีแถว m3 · POST confirm 1 ครั้ง body `{materials: [{id: "m1", kind: "sheet"}]}` · `202` Then ไป `/preps/p1/progress`
- **AC-13 (CM06)** Given confirm ตอบ `409 not_classified` Then `GET /materials` อีกครั้ง ไม่มีข้อความ error · Given ตอบ `503` Then "เริ่มอ่านไฟล์ไม่สำเร็จ ลองอีกครั้งนะ" ปุ่มกดได้อีก · Given ตอบ `401` Then ไม่มีข้อความ error
- **AC-14 (CM06)** Given ทุกไฟล์ `failed` Then "ไม่มีไฟล์ที่อ่านได้" + ปุ่ม "ใส่ไฟล์ใหม่" · กดแล้วกลับไปขั้นใส่ไฟล์ที่รายการว่าง
- **AC-15 (CM07 · UC-02 E6)** Given เปิดหน้าแล้ว `GET /materials` มีไฟล์ `kind_confirmed: false` Then เริ่มที่ขั้นตรวจประเภทเลย · Given ทุกไฟล์ `kind_confirmed: true` หรือไม่มีไฟล์ Then ขั้นใส่ไฟล์
- **AC-16** Given `GET /materials` ตอนเปิดหน้าได้ `404` Then "ไม่พบการเตรียมสอบนี้" + ลิงก์ "กลับหน้าหลัก" · `503` Then "โหลดไฟล์ไม่สำเร็จ" + "ลองใหม่" · `401` Then ไม่มีข้อความ error

**รออ่านไฟล์ (S11)**

- **AC-17 (CM07)** Given `Ingestion` มี 2 ไฟล์ (`done` "14 หน้า", `running` "กำลังแยกรายข้อ") และ 3 ขั้น (`done`, `running`, `pending`) Then เห็นชื่อไฟล์ + `detail` + สัญลักษณ์ที่ `aria-label` "เสร็จแล้ว", "กำลังอ่าน" · ขั้นตาม `label` จาก API ตามลำดับ
- **AC-18 (CM07)** Given ครั้งแรก `scope_ready: false` ครั้งที่สอง (หลัง `POLL_MS`) `scope_ready: true` Then ไป `/preps/p1/scope` 1 ครั้ง และไม่ poll อีก
- **AC-19 (CM07)** Given ไฟล์ `failed` `error: "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้"` Then ข้อความนั้นในแถว · ไม่มีปุ่ม "ลองใหม่" ในแถว
- **AC-20 (CM07)** Given `files: []` และ `scope_ready: false` Then "ยังไม่มีไฟล์ที่ส่งให้อ่าน" + ลิงก์ "ใส่ไฟล์" (`href = /preps/p1/upload`) และไม่ poll อีก
- **AC-21 (CM07)** Given poll ครั้งที่สองได้ `503` Then ผลครั้งแรกยังแสดง + "โหลดความคืบหน้าไม่สำเร็จ" + "ลองใหม่" และไม่ poll เอง · กด "ลองใหม่" Then `GET /ingestion` อีกครั้ง · `404` ครั้งแรก Then "ไม่พบการเตรียมสอบนี้" · `401` Then ไม่มีข้อความ error

**หน้าที่ Next ซ่อนไว้**

- **AC-22 (CM07)** Given หน้ารออ่านไฟล์ใน `<Activity mode="visible">` When ซ่อน แล้วเวลาผ่านไป 3 × `POLL_MS` Then ไม่มี `GET /ingestion` ระหว่างซ่อน · When แสดงอีกครั้ง Then `GET /ingestion` ทันที 1 ครั้ง
- **AC-23 (CM07)** Given `scope_ready: true` มาถึงหลังหน้าถูกซ่อนแล้ว (request ค้างตอนซ่อน) Then ไม่เรียก `navigate`

**หน้ารายการและหลังสร้าง (§2.4)**

- **AC-24 (CM01)** `prepHref`: `materials` → `/preps/{id}/upload` · `processing` → `/preps/{id}/progress` · `scope`, `tutoring` เหมือนเดิม · ในหน้ารายการการ์ดทั้ง 4 ขั้นเป็นลิงก์
- **AC-25 (CM01)** Given `POST /exam-preps` ตอบ `201` พร้อม `id: "p9"` Then ไป `/preps/p9/upload`

**AC-tenant (SA-06):** ทุก request ไป API ส่ง `Authorization` ของ session (ผ่าน `apiFetch`) · `PUT` ไป signed URL ไม่ส่ง · การแยก tenant ของแถวและ Storage ทำฝั่ง API + RLS + storage policy (#140 · Junior) · หน้าเว็บไม่ประกอบ path เอง (ใช้ `upload_url` และ `material_id` จาก API)

**AC-boundary:** ไม่มี threshold ของ learning model · ขอบของค่าที่แสดง: `kind_confidence` 0 → "มั่นใจ 0%", 1 → "100%", 0.934 → "93%", 0.935 → "94%" (ปัดแบบ `Math.round`), null → ไม่แสดง · ขนาด 1,048,575 bytes → "1024 KB", 1,048,576 → "1.0 MB" · ขนาดสูงสุดไม่เช็คในหน้าเว็บ (API ตอบ `file_too_large` · api.md v1.13)

## 5. Data changes

ไม่มี (หน้าเว็บ) · แถว `materials`, Storage bucket และ policy อยู่ใน #140

## 6. API / SSE changes

ไม่มี · ใช้ endpoint ตาม api.md v1.10, v1.13, v1.16 (§3) · ทุกตัวมีใน OpenAPI แล้ว

## 7. AI calls

ไม่มีในหน้าเว็บ (classify และ ingest เกิดฝั่ง API หลัง `/uploaded` และ `/materials/confirm`)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/materials/UploadPage.test.tsx` (ใหม่) | component + fetch จำลอง + fake timers | AC-1 ถึง AC-16 |
| `tests/materials/ProgressPage.test.tsx` (ใหม่) | component + fetch จำลอง + fake timers + `<Activity>` | AC-17 ถึง AC-23 |
| `tests/preps/PrepList.test.tsx`, `CreatePrepForm.test.tsx` (เดิม · review แล้ว) | component | AC-24, AC-25 · แก้ test ที่ review แล้ว 3 ตัว (Jam ok · §10 ข้อ 1) |
| ลองในเบราว์เซอร์บน stub | มือ | S09 → S10 → S11 · ทางจริงรอ #140 |

## 9. Out of scope

- note รายไฟล์ (CM-04) · เพิ่มไฟล์ทีหลังหลังยืนยัน scope (CM-05 · S36) · ลบไฟล์ (CM-10) · แก้ประเภทที่ AI เดา (CM-06 ส่วนแก้) และปุ่ม "ถูกหมดแล้ว ข้ามเลย" · ทั้งหมดอยู่ใน S5 (checklist ของ May "หน้าไฟล์: …")
- ปุ่ม "ลองใหม่" และ "ไปต่อโดยไม่มีไฟล์นี้" ของไฟล์ที่อ่านไม่สำเร็จ (UC-02 E5) · `retry` และ `DELETE` ยังเป็น stub หลัง demo (#140)
- ลากไฟล์มาวาง (drag and drop) · ใช้ปุ่มเลือกไฟล์อย่างเดียว
- แถบ progress ระหว่าง `PUT` (แสดงแค่ "กำลังอัปโหลด…")
- ขั้นของ wizard "1 ข้อมูลการสอบ › 2 ไฟล์ › 3 ตรวจไฟล์" ด้านบน (wireframe)

## 10. Open questions

ให้ Jam ตัดสินตอน review (Jam ตัดสินไปก่อนช่วง solo · May ดูย้อนหลัง)

1. **ตัดสินแล้ว (Jam 16 พ.ย.): (ก) แก้ใน PR นี้** · **แก้ test ที่ review แล้ว 3 ตัว** เพื่อ §2.4: `PrepList.test.tsx` "CM01 a prep at scope or tutoring links to its page, the others do not (AC-3)" (การ์ด `materials`, `processing` จะเป็นลิงก์) · `CreatePrepForm.test.tsx` "CM01 creates the prep with what was typed, then goes home (AC-8)" และ "CM01 a page hidden after a create comes back as a fresh, usable form" (ไป `/preps/p1/upload` แทน `/`) · ข้อเสนอ: แก้ใน PR นี้ (ชื่อ test เปลี่ยนตาม) · ทางเลือก: ไม่แก้ §2.4 ใน PR นี้ แล้วหน้าใหม่เข้าได้จาก URL อย่างเดียว (demo เดินไม่ต่อ)

ให้ May ดูย้อนหลัง (เรื่องหน้าจอ)

2. **S10 แบบย่อ:** ไม่มีปุ่ม "ถูกหมดแล้ว ข้ามเลย" แยก และยังแก้ประเภทไม่ได้จนถึง S5 · confidence แสดงเป็น % จาก API (wireframe ใช้คำว่า "มั่นใจ" / "ไม่ค่อยมั่นใจ" ซึ่งต้องมีเส้นแบ่ง · ยังไม่มีใน spec ไหน)
3. **`POLL_MS`:** ข้อเสนอ 2 วินาที เป็นค่าคงที่ใน `components/materials/` (ไม่ใช่ค่าของ learning model จึงไม่อยู่ใน `config/learning.yaml`) · api.md ไม่ได้กำหนด
4. **ส่งทีละไฟล์:** ช้ากว่าส่งพร้อมกัน แต่สถานะรายแถวชัดและไม่ชนเพดาน request · ไฟล์ demo มี 6 ไฟล์
5. **URL ของหน้า:** `/preps/[id]/upload` และ `/preps/[id]/progress` (แบบ `/scope`, `/room` เดิม)
6. **ข้อความใหม่ทั้งหมด** ใน §2 (แก้ได้ใน `components/materials/strings.ts`)

ให้ Junior ดู (#140)

7. หน้าเว็บพึ่ง `X-Stub: true` เพื่อข้าม `PUT` · เมื่อ `/materials` ใช้ Storage จริงต้องไม่ส่ง header นี้ · ถ้า `materials-db.md` เปลี่ยนสัญญา (body, status code, error code) หน้านี้แก้ตามใน PR ใหม่

## 11. Spec changes needed

- `prep-list-page.md` (spec ของ May · เปลี่ยนในเฟสนี้): §2.1 ข้อ 5 (`prepHref` ของ `materials`, `processing`) · §2.2 ข้อ 3 (หลังสร้างไปหน้าอัปโหลด) · §10 ข้อ 2 (ตัดสินแล้ว) · AC-3, AC-8 ตาม §2.4 · แก้ใน PR นี้ (§10 ข้อ 1 ตกลงแล้ว)
- ไม่แตะไฟล์กลาง (api.md, requirements.md, config)
