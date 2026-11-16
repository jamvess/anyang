# หน้าอัปโหลดหลายไฟล์ + สถานะรายไฟล์ (demo ขั้น 3 ฝั่งเว็บ)

| | |
|---|---|
| Owner | Jam (item of May) |
| Branch | `feat/web-upload-page` |
| Checklist item | ⭐ demo ขั้น 3: หน้าอัปโหลดหลายไฟล์ + สถานะรายไฟล์ (CM-03, CM-07) |
| Status | in progress · 2026-11-16 |

## Plan

สิ่งที่มีแล้ว: สัญญา API ของ materials ใน api.md v1.10 + v1.13 (ข้อเสนอ · รอ Junior) · stub ครบทุก endpoint (`X-Stub: true` · URL อัปโหลดของ stub ใช้จริงไม่ได้ ข้าม `PUT` แบบห้องติว `room-photo-send.md`) · `GET /exam-preps/{id}/ingestion` อ่าน DB แล้ว (v1.16) · Junior ทำ API จริงอยู่ใน #140 · ยังไม่มี feature spec ของหน้าจอ S09–S11

- [ ] 1. 🤖 `/spec-feature` → `specs/features/exam-prep/upload-page.md` (CM-03, CM-07 · CM-06 ส่วนแสดงประเภทที่ AI เดา + ยืนยันโดยไม่แก้ · SA-06):
  - S09 เลือกหลายไฟล์ → ต่อไฟล์: `POST /exam-preps/{id}/materials` → `PUT` (ข้ามเมื่อ `X-Stub`) → `POST /materials/{id}/uploaded` · สถานะรายไฟล์ · error `unsupported_type` / `file_too_large` เป็นภาษาไทย
  - S10 แบบย่อ: poll `GET /exam-preps/{id}/materials` จนทุกไฟล์มี `kind` → แสดงประเภท + confidence → ปุ่มยืนยัน (`POST /materials/confirm` ด้วยประเภทที่ AI เดา · แก้ประเภทเป็น S5)
  - S11: poll `GET /exam-preps/{id}/ingestion` แสดงสถานะรายไฟล์ + ขั้นรวม → `scope_ready` แล้วไปหน้า scope
  - หน้ารายการ: การ์ด `materials` / `processing` ลิงก์มาหน้าใหม่ (`prepHref`) · หลังสร้าง prep ไปหน้าอัปโหลด (`prep-list-page.md` §10 ข้อ 2)
  - → 🙋 Jam review spec (เรื่องหน้าจอเป็นของ May: Jam ตัดสินไปก่อน May ดูย้อนหลัง)
- [ ] 2. 🤖 `/spec-to-tests` (fetch จำลอง · test เดิมที่ review แล้วไม่แตะ) → 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · lint · typecheck · build · test ทั้งชุด
- [ ] 4. 🙋 ลองในเบราว์เซอร์บน stub (เลือกไฟล์ → สถานะรายไฟล์ → ประเภท → ยืนยัน → หน้ารอ) · Claude ให้ขั้นตอนตอนถึงขั้นนี้
- [ ] 5. 🤖 จดผลลง spec · ส่วนที่ต้องรอ #140 (อัปโหลดเข้า Storage จริง → ingestion → scope) จดไว้ใน Waiting on

## Definition of done

- ผู้ใช้เลือกหลายไฟล์ในหน้าเดียว เห็นสถานะรายไฟล์ตั้งแต่อัปโหลดจนอ่านเสร็จ แล้วไปหน้า scope เอง (CM-03, CM-07) · ตามสัญญา api.md v1.10
- test จาก AC ผ่าน · test เดิมผ่านโดยไม่แก้ · lint, typecheck, build, CI เขียว
- ลองในเบราว์เซอร์บน stub ผ่าน · ทางจริง (Storage + ingestion) จดว่ารอ #140

## Decisions

- 2026-11-16 · ทำงานของ May ช่วง solo (Jam เลือกข้อ 1 ของ `/work-start ALL`) · May บอกไว้แล้วว่าจัดการได้ เดี๋ยวมา review ทีหลัง
- 2026-11-16 · ทำตามสัญญา api.md v1.10 ไปก่อน ถ้า spec ของ #140 (`materials-db.md`) เปลี่ยนสัญญา แก้ตามใน PR ใหม่

## Next step

ข้อ 1: `/spec-feature` เขียน `specs/features/exam-prep/upload-page.md` ตามแผน แล้วให้ Jam review

## Waiting on

- Junior #140: API materials จริง + Storage · จนกว่าจะเสร็จ ลองได้แค่บน stub

## Notes for next time

- เทส web ทั้งชุดบนเครื่องนี้ใช้ `npx vitest run --maxWorkers=2`
