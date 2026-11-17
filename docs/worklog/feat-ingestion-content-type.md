# ingestion ตัดสินชนิดไฟล์จาก `content_type`

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/ingestion-content-type` |
| Checklist item | หลัง #140 · ingestion ตัดสินชนิดไฟล์จาก `materials.content_type` แทนนามสกุลของ `file_name` (`_image_type` ใน `app/services/ingestion.py` · ไฟล์ของ Jam: บอก Jam) · ชนิดที่ยังอ่านไม่ได้ (WEBP, HEIC, PPTX, DOCX) ล้มด้วยข้อความที่บอกให้ส่ง PDF/JPG/PNG · แถวเก่าที่ `content_type` null ใช้นามสกุลเหมือนเดิม (`materials-db.md` §10 ข้อ 1 · CM-03) |
| Status | in progress · 2026-11-17 |

## Plan

ตอนนี้ `_image_type` ดูนามสกุลของ `file_name` และรู้จักแค่ `.png`, `.jpg`, `.jpeg` · อย่างอื่นถือเป็น PDF · API รับ PDF, JPEG, PNG, WEBP, HEIC, PPTX, DOCX และ #140 เก็บ `materials.content_type` ที่ตรวจกับ object จริงแล้ว · ผล: WEBP, HEIC, PPTX, DOCX และรูปที่ชื่อไม่มีนามสกุลล้มด้วย "เปิดไฟล์นี้ไม่ได้" · ห้องติวส่ง WEBP/HEIC ให้ Gemini vision อยู่แล้ว (`app/models/room.py`)

- [x] 1. 🤖 แก้ spec `specs/features/scope/ingestion.md` (spec ของ Jam): ชนิดไฟล์มาจาก `content_type` · PDF → ทางเดิม · JPEG/PNG/WEBP/HEIC → `vision_extract` 1 หน้า (ข้อเสนอ: อ่าน WEBP/HEIC ได้เลยแทนที่จะล้มตาม checklist) · PPTX/DOCX → ล้มตั้งแต่ classify ด้วยข้อความใหม่ที่บอกให้ส่ง PDF หรือรูป · `content_type` null (แถวเก่า) → นามสกุลเหมือนเดิม · ตอบ `materials-db.md` §10 ข้อ 1 (spec ของ Junior · ถามก่อนแก้) → 🙋 Jam review
- [x] 2. 🤖 `/spec-to-tests` (unit · `InMemoryIngestionStore` + fake provider) → 🙋 Jam review test
- [x] 3. 🤖 `/implement-feature`: `MaterialRow.content_type` + `_material` + `add_material(content_type=…)` + ตัดสินชนิดใน `ingestion.py` · ruff · pytest ทั้งชุด
- [ ] 4. 🙋 (ถ้าอยาก) ลองในเบราว์เซอร์: อัปโหลดรูป PNG 1 ไฟล์ + DOCX 1 ไฟล์ · PNG ต้องผ่าน · DOCX ต้องขึ้นข้อความใหม่

## Definition of done

- ชนิดไฟล์มาจาก `content_type` · ไฟล์ทุกชนิดที่ API รับมีทางที่ถูกต้อง (อ่านได้ หรือล้มด้วยข้อความที่บอกว่าให้ส่งแบบไหน) · แถวเก่าทำงานเหมือนเดิม
- test ใหม่ผ่าน · test เดิมผ่านโดยไม่แก้ · ruff, pytest, CI เขียว

## Decisions

- 2026-11-17 · Jam เลือกข้อ 2 ของ `/work-start Jam`

## Next step

ข้อ 3: implement เสร็จ · API ทั้งชุด 1958 ผ่าน 1 ล้ม (`test_SA06_the_job_writes_rows_of_the_preps_tenant_only` · รันซ้ำเดี่ยว 1 ครั้งและทั้งไฟล์ 2 ครั้งผ่านหมด · ไม่ได้เก็บ error ของรอบที่ล้ม) · รอ Jam ok แล้วข้อ 4 (ถ้าอยากลองในเบราว์เซอร์)

## Waiting on

ไม่มี

## Notes for next time

- API ทั้งชุดในเครื่องใช้ราว 11 นาที (integration บน `anyang-dev`) · unit อย่างเดียวราว 4 นาที
