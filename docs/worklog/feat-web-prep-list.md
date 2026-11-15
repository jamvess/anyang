# หน้ารายการการเตรียมสอบ + ฟอร์มสร้าง (demo ขั้น 2 ฝั่งเว็บ)

| | |
|---|---|
| Owner | Jam (item of May · ช่วง solo · May มาดูหน้าตาทีหลังแบบ #138) |
| Branch | `feat/web-prep-list` |
| Checklist item | ⭐ demo ขั้น 2: หน้ารายการการเตรียมสอบ + ฟอร์มสร้าง แทนหน้า template ของ Next (CM-01, CM-02) |
| Status | in progress · 2026-11-15 |

## Plan

หลัง login (#138) หน้า `/` ยังเป็นหน้า template ของ Next · `GET /exam-preps` และ `POST /exam-preps` อ่านเขียน DB จริงแล้ว (`create-exam-prep.md` · Junior) · ทำหน้าหลักที่แสดงการเตรียมสอบของผู้ใช้ และฟอร์มสร้าง ต่อ API ผ่าน `apiFetch` (token แนบอัตโนมัติ)

- [x] 1. 🤖 (15 พ.ย. · Jam ok) `/spec-feature` → `specs/features/exam-prep/prep-list-page.md`: หน้า `/` (S07/S27) = การ์ดของ `GET /exam-preps` (ชื่อ, เหลือกี่วันจาก `days_left` ของ API, ขั้นจาก `stage`) · การ์ดพาไปหน้าตาม `stage` (`scope` → หน้า scope · `tutoring` → ห้องติว · `materials` / `processing` ยังไม่มีหน้า (ขั้น 3) จึงบอกสถานะอย่างเดียว) · ไม่มีรายการ → ข้อความเชิญสร้าง · ปุ่ม "สร้างการเตรียมสอบ" → `/preps/new` (S08): ชื่อ, วันสอบ, เวลาต่อวัน (ไม่บังคับ) → `POST` → กลับหน้า `/` · error 422 (`exam_date_past`, ชื่อว่าง/ยาวเกิน) และ 503 เป็นข้อความไทย · ลิงก์ออกจากระบบ · ข้อความอยู่ใน `strings.ts` · 🙋 Jam review spec
- [x] 2. 🤖 (15 พ.ย. · Jam ok) `/spec-to-tests` (Vitest + `fetch` ปลอม) · 🙋 Jam review test
- [x] 3. 🤖 (15 พ.ย. · web test 354 ผ่าน · build ผ่าน · Jam ok) `/implement-feature` จน green · `lint`, `typecheck`, `test`, `build`
- [ ] 4. 🙋 Jam ลองในเบราว์เซอร์กับ `anyang-dev`: login → หน้าหลักว่าง → สร้าง prep → เห็นการ์ด
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- หลัง login หน้า `/` แสดงการเตรียมสอบของผู้ใช้จาก API (ไม่มีตัวเลขที่เว็บคิดเอง) · สร้างได้จากฟอร์ม
- การ์ดที่ถึงขั้น scope / ติว พาไปหน้านั้น · ไม่มีรายการมีข้อความเชิญสร้าง
- error ของ API แสดงเป็นข้อความไทย · test เดิมไม่ต้องแก้

## Decisions

- 2026-11-15 · ไม่แสดงจำนวนวันที่เหลือก่อนสร้าง (ตัวเลขมาจาก API · รอ May ตัดสิน §10 ข้อ 1) · หลังสร้างกลับ `/` จนกว่าจะมีหน้าอัปโหลด (Jam ok spec)
- 2026-11-15 · Jam หยิบงานของ May ช่วง solo (ทำแบบเดียวกับ #138 · May มา review หน้าตาทีหลัง)

## Next step

ขั้น 4: Jam ลองในเบราว์เซอร์กับ anyang-dev (ขั้นละเอียดอยู่ในข้อความรายงาน)

## Waiting on

- May: review หน้าตาและข้อความ · หน้าอัปโหลด (ขั้น 3) ที่การ์ด `materials` จะพาไป

## Notes for next time

- ไม่มี
