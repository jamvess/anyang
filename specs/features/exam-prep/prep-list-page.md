# Feature: หน้ารายการการเตรียมสอบ + ฟอร์มสร้าง (demo ขั้น 2 ฝั่งเว็บ)

| | |
|---|---|
| Area | exam-prep (หน้าเว็บ) |
| Requirements | CM-01, CM-02, SA-06 |
| Owner | Jam (งานของ May · ทำช่วง solo) |
| Reviewer | May (หน้าตา ข้อความ flow · ดูย้อนหลัง) · Jam |
| Status | approved 2026-11-15 (Jam ok spec + test) · implemented 2026-11-16 (PR #139) · รอ May review หน้าตา · 16 พ.ย. การ์ด `materials`/`processing` และหลังสร้าง เปลี่ยนตาม `upload-page.md` §2.4 (PR #142 · Jam ok แก้ AC-3, AC-8) |
| Related system spec | `create-exam-prep.md` (API `POST` / `GET /exam-preps` · `stage`, `days_left`) · api.md v1.14 `ExamPrep` · `web-login.md` (#138 · `apiFetch` แนบ token · 401 ไปหน้า login) · `docs/design/use-cases.md` UC-02 ขั้น 1–2 (S07, S08), UC-03 ขั้น 12 (S27) · `apps/web/CLAUDE.md` |

## 1. Context

หลัง login (#138) หน้า `/` ยังเป็นหน้า template ของ Next · API ของการเตรียมสอบอ่านเขียน DB จริงแล้ว (`create-exam-prep.md`) · feature นี้ทำหน้าหลักที่แสดงการเตรียมสอบของผู้ใช้ และฟอร์มสร้าง · ทุก request ผ่าน `apiFetch` (token แนบอัตโนมัติ · 401 ไปหน้า login) · ทุกตัวเลขมาจาก API (`apps/web/CLAUDE.md`)

## 2. Behavior

### 2.1 หน้า `/` (S07 ยังไม่มีรายการ · S27 มีรายการ · `components/preps/PrepList.tsx`)

1. โหลด `GET /exam-preps` · ระหว่างรอ "กำลังโหลด…" · ล้ม (เครือข่าย, `503`) → "โหลดรายการไม่สำเร็จ" + ปุ่ม "ลองอีกครั้ง" (โหลดใหม่)
2. ไม่มีรายการ (`[]`) → "ยังไม่มีการเตรียมสอบ" + ปุ่ม "สร้างการเตรียมสอบ"
3. มีรายการ → การ์ดละ 1 รายการ **เรียงตามที่ API ส่งมา** (API เรียงวันสอบใกล้ก่อนแล้ว) · ปุ่ม "สร้างการเตรียมสอบ" อยู่บนรายการ
4. การ์ดแสดง (ข้อความอยู่ใน `strings.ts`):
   - `title`
   - วันที่เหลือจาก `days_left` ของ API: ≥ 1 → "อีก {n} วัน" · 0 → "สอบวันนี้" · < 0 → "สอบผ่านไปแล้ว"
   - ขั้นจาก `stage`: `materials` "รออัปโหลดไฟล์" · `processing` "กำลังอ่านไฟล์" · `scope` "รอตรวจขอบเขต" · `tutoring` "พร้อมติว"
   - `readiness` ไม่เป็น null → "ความพร้อม {readiness × 100 ปัดเป็นจำนวนเต็ม}%" · `topics_not_passed` ไม่เป็น null → "ยังไม่ผ่าน {n} หัวข้อ" · เป็น null (ตอนนี้ API ส่ง null เสมอ) → ไม่แสดง
5. **การ์ดพาไปที่ไหน** (ฟังก์ชันเดียว `prepHref(prep)` · ขั้น 3 เพิ่มหน้าได้ที่นี่): `scope` → `/preps/{id}/scope` · `tutoring` → `/preps/{id}/room` · `materials` → `/preps/{id}/upload` · `processing` → `/preps/{id}/progress` (หน้าของ `upload-page.md` · PR #142) · ทุกการ์ดเป็นลิงก์
6. ลิงก์ "ออกจากระบบ" → `/logout` (#138)
7. ไม่มี token บนเครื่อง dev (`AUTH_REQUIRED=false`) → API ตอบ stub ของ `GET /exam-preps` · หน้าแสดงรายการของ stub (ไม่ต้อง login)

### 2.2 หน้า `/preps/new` (S08 · `components/preps/CreatePrepForm.tsx`)

1. ช่อง **ชื่อการสอบ** (text, required) · **วันสอบ** (`type="date"`, required) · **เวลาต่อวัน (นาที)** (`type="number"`, ไม่บังคับ, `min=1`, `max=1440`) · ปุ่ม **สร้าง** · ลิงก์ **ยกเลิก** → `/` · ทุกช่องมี label
2. กดสร้าง → `POST /exam-preps` body `{title, exam_date}` และ `daily_minutes` (integer) เฉพาะเมื่อกรอก · ระหว่างรอปุ่มเป็น "กำลังสร้าง…" และกดไม่ได้
3. `201` → ล้างฟอร์ม (ช่องว่าง · ปุ่มกลับเป็น "สร้าง") แล้วไปหน้าอัปโหลดของ prep ใหม่ `/preps/{id}/upload` (`id` จาก response · `upload-page.md` §2.4 · PR #142) · ถ้าผู้ใช้ออกจากหน้านี้ไปแล้วตอนคำตอบมาถึง → ไม่พากลับ (Next 16 `cacheComponents` ซ่อนหน้าที่ออกด้วย React `<Activity>` และเก็บ state ไว้ · ไม่ล้างจะเจอปุ่มค้าง "กำลังสร้าง…" ตอนกลับมา · พบตอนลองในเบราว์เซอร์ 15 พ.ย. · self-review PR #139)
4. error (ข้อความใน `role="alert"` · ค่าที่กรอกคงไว้):
   - `422 exam_date_past` → "วันสอบต้องไม่ก่อนวันนี้"
   - `422` อื่น (`validation_error`: ชื่อว่าง ยาวเกิน มีอักขระควบคุม เวลาเกินช่วง) → "ตรวจชื่อ วันสอบ และเวลาต่อวันอีกครั้ง"
   - อย่างอื่น (`503`, เครือข่าย) → "บันทึกไม่ได้ตอนนี้ ลองใหม่อีกครั้ง"
   - `401` → `apiFetch` พาไปหน้า login (#138) · ไม่แสดง error (หน้ารายการก็ไม่แสดง "โหลดรายการไม่สำเร็จ")
5. ไม่ตรวจกฎของ API ซ้ำในเบราว์เซอร์ (ความยาวชื่อ วันที่ผ่านไปแล้ว) · API เป็นคนตัดสิน · เบราว์เซอร์ใช้แค่ `required`, `min`, `max` ของช่อง
6. **ไม่แสดงจำนวนวันที่เหลือก่อนสร้าง** (UC-02 ขั้น 2 อยากให้แสดงทันที แต่ตัวเลขต้องมาจาก API · `apps/web/CLAUDE.md` · §10 ข้อ 1)

### 2.3 ข้อความ

ข้อความทั้งหมดของทั้ง 2 หน้าอยู่ใน `components/preps/strings.ts` (ภาษาไทย · May แก้ที่เดียว)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `GET /exam-preps` → `ExamPrep[]` · ฟอร์ม → `CreateExamPrepRequest` | `{"title": "MTH10101 Calculus I", "exam_date": "2026-12-08", "daily_minutes": 60}` |
| Output | การ์ด + ลิงก์ตาม `stage` · `POST /exam-preps` | |

## 4. Acceptance criteria

Vitest + Testing Library · `fetch` ปลอม (`NEXT_PUBLIC_API_URL` = `http://api.test`) · type จาก `lib/api.ts`

- **AC-1 (CM-01)** `GET /exam-preps` ได้ 4 รายการ (ทุก `stage`) → การ์ด 4 ใบตามลำดับของ API · ชื่อแต่ละใบ · ขั้นเป็นข้อความไทยตาม §2.1 ข้อ 4
- **AC-2 (CM-02)** `days_left` 12 → "อีก 12 วัน" · 0 → "สอบวันนี้" · −3 → "สอบผ่านไปแล้ว"
- **AC-3** การ์ด `scope` เป็นลิงก์ไป `/preps/{id}/scope` · `tutoring` → `/preps/{id}/room` · `materials` → `/preps/{id}/upload` · `processing` → `/preps/{id}/progress` (เปลี่ยน 16 พ.ย. · PR #142)
- **AC-4** `readiness` 0.416 และ `topics_not_passed` 5 → "ความพร้อม 42%" และ "ยังไม่ผ่าน 5 หัวข้อ" · null → ไม่มีทั้งสองข้อความ
- **AC-5 (CM-01)** `[]` → "ยังไม่มีการเตรียมสอบ" + ปุ่มสร้างไป `/preps/new`
- **AC-6** `GET` ได้ `503` → "โหลดรายการไม่สำเร็จ" · กด "ลองอีกครั้ง" → โหลดใหม่และแสดงรายการ
- **AC-7** มีลิงก์ "ออกจากระบบ" ไป `/logout`
- **AC-8 (CM-01)** กรอกชื่อ วันสอบ เวลา 60 กดสร้าง → `POST /exam-preps` body `{title, exam_date, daily_minutes: 60}` · ระหว่างรอปุ่ม "กำลังสร้าง…" กดไม่ได้ · `201` → `navigate("/preps/{id}/upload")` ของ prep ใหม่ (เปลี่ยน 16 พ.ย. · PR #142 · เดิม `/`)
- **AC-9** ไม่กรอกเวลาต่อวัน → body ไม่มี `daily_minutes`
- **AC-10** `422 exam_date_past` → "วันสอบต้องไม่ก่อนวันนี้" · `422 validation_error` → "ตรวจชื่อ วันสอบ และเวลาต่อวันอีกครั้ง" · `503` → "บันทึกไม่ได้ตอนนี้ ลองใหม่อีกครั้ง" · ทุกแบบอยู่ใน `role="alert"` · ค่าที่กรอกคงไว้ · ไม่ navigate · ปุ่มกดได้อีก
- **AC-11** ทุกช่องมี label · ชื่อและวันสอบ required · เวลา `min=1` `max=1440` · ลิงก์ยกเลิกไป `/`
- **AC-12** ทุก request ผ่าน `apiFetch` (มี session → แนบ `Authorization` · ทดสอบแบบ #138 `pagesAuth.test.tsx`)
- **AC-13** test เดิมทั้งหมดผ่านโดยไม่แก้

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ใช้ `GET` / `POST /exam-preps` ตาม api.md v1.14

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/preps/PrepList.test.tsx` (ใหม่) | component | AC-1 ถึง AC-7 |
| `tests/preps/CreatePrepForm.test.tsx` (ใหม่) | component | AC-8 ถึง AC-11 · หน้าที่ถูกซ่อนด้วย `<Activity>` กลับมาเป็นฟอร์มใหม่ · ไม่พากลับเมื่อออกไปแล้ว · 401 ไม่แสดง error (self-review) |
| `tests/preps/prepsAuth.test.tsx` (ใหม่ · session ปลอม) | component | AC-12 |
| test เดิมทั้งหมด | | AC-13 |
| ลองในเบราว์เซอร์กับ `anyang-dev` (ขั้น 4 ของ worklog · Jam) | มือ | login → หน้าหลักว่าง → สร้าง → เห็นการ์ด |

**ผลลองในเบราว์เซอร์กับ `anyang-dev` (15–16 พ.ย. · ขั้น 4 ของ worklog · Jam · API ในเครื่อง `AUTH_REQUIRED=true` + `pnpm dev`):** ไม่มี session เปิด `/` → เด้งไปหน้า login · login → หน้ารายการว่างพร้อมหัวข้อ ลิงก์ออกจากระบบ ปุ่มสร้าง ข้อความเชิญ · สร้าง → กลับ `/` เห็นการ์ด (ชื่อ · อีก n วัน · รออัปโหลดไฟล์ · ไม่เป็นลิงก์) · วันสอบเมื่อวาน → "วันสอบต้องไม่ก่อนวันนี้" ค่าคงไว้ · ยกเลิก → กลับ `/` · ออกจากระบบ → login · **ผ่านทุกข้อ (Jam)** · **ค้าง 1 ครั้ง:** การสร้างครั้งที่ 2 ในรอบแรกค้างที่ "กำลังสร้าง…" · ไม่ได้เก็บ log ของ API และ Network จึงยังไม่รู้ว่าค้างก่อนถึง API หรือหลังได้คำตอบแล้ว · รีเฟรชแล้วลองใหม่ผ่านทั้งหมด · ดูต่อใน self-review ของ PR #139

## 9. Out of scope

- หน้าอัปโหลด (S09) และหน้าความคืบหน้า (S11) ที่การ์ด `materials` / `processing` จะพาไป (demo ขั้น 3)
- แก้ ลบ หรือเก็บ (archive) การเตรียมสอบ · ปุ่ม "เพิ่มไฟล์" บนการ์ด (UC-02 A9 · S5)
- ความพร้อมและหัวข้อที่ยังไม่ผ่านจริง (API ส่ง null · PM-04 หน้า home · S5)
- หน้าตาตาม wireframe S07, S08, S27 (May ปรับทีหลัง)

## 10. Open questions

1. **(May) จำนวนวันที่เหลือก่อนสร้าง (UC-02 ขั้น 2):** ทางเลือก (ก) ไม่แสดงจนสร้างเสร็จ (ข้อเสนอ · ตัวเลขมาจาก API) (ข) คิดในเบราว์เซอร์จากวันที่ที่เลือก (ขัดกฎ "ตัวเลขมาจาก API" และวัน "วันนี้" ต้องเป็นเวลา Bangkok) (ค) API endpoint ใหม่ที่คืน `days_left` ของวันที่ที่เลือก
2. **(May) หลังสร้างไปไหน:** ~~ตอนนี้ `/`~~ · 16 พ.ย. ไปหน้าอัปโหลดของ prep ใหม่ (Jam ตัดสินไปก่อนช่วง solo · `upload-page.md` §2.4 · May ดูย้อนหลัง)

## 11. Spec changes needed

ไม่มี (ไม่แตะไฟล์กลาง)
