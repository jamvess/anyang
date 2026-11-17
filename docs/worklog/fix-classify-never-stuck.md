# `classify_material` ไม่ให้ไฟล์ค้าง "AI กำลังดูไฟล์…"

| | |
|---|---|
| Owner | Jam |
| Branch | `fix/classify-never-stuck` |
| Checklist item | ⭐ ก่อนอัดวิดีโอ · `classify_material` ไม่ให้ไฟล์ค้าง "AI กำลังดูไฟล์…": อ่านแถว/ตั้ง job ล้มก่อน `try` → ไฟล์ค้าง `uploaded` ตลอด ไม่มี error ไม่มีทางลองใหม่ · ทุกกรณีต้องจบที่ `failed` ที่ลองใหม่ได้ (พบใน #151) |
| Status | in progress · 2026-11-17 |

## Plan

ตอนนี้ (`app/services/ingestion.py` · `classify_material`): `get_material` และ `set_job(running)` อยู่นอก `try` · เขียนผลตอนจบ (`update_material` classified, `set_job` done) ก็อยู่นอก `try` · ล้มตรงนั้น → `IngestionRunner._classify` แค่ log · ไฟล์ค้าง `uploaded` · หน้าเว็บ poll "AI กำลังดูไฟล์…" ตลอด · `/uploaded` ซ้ำได้ `409` และ `/retry` รับแต่ `failed` จึงไม่มีทางออก (เจอจริงใน #151 ตอน key ผิด)

- [x] 1. 🤖 แก้ spec `specs/features/scope/ingestion.md` §2.2 (spec ของ Jam): ทุกความล้มหลัง `/uploaded` จบที่ `status = failed` + ข้อความที่ลองใหม่ได้ · อ่านแถวไม่ได้ → ยังตั้ง `failed` ด้วย id ได้ · DB ล่มทั้งหมด → log ระดับ ERROR ที่บอกว่าไฟล์ค้าง · AC-29 ขึ้นไป (#152 ใช้ AC-28 แล้ว) → 🙋 Jam review
- [x] 2. 🤖 `/spec-to-tests` (unit · `InMemoryIngestionStore` + fake provider) → 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · ruff · pytest ทั้งชุด

## Definition of done

- ล้มที่ขั้นไหนของ classify (อ่านแถว · ตั้ง job · อ่านไฟล์ · AI · เขียนผล) ไฟล์ไม่ค้าง `uploaded`: จบที่ `failed` ที่ `/retry` ลองใหม่ได้ · ถ้าเขียนอะไรไม่ได้เลย มี log ERROR ที่บอก id ของไฟล์ที่ค้าง
- test ใหม่ผ่าน · test เดิมผ่านโดยไม่แก้ · ruff, pytest, CI เขียว

## Decisions

- 2026-11-17 · Jam เลือกข้อ 1 ของ `/work-start Jam` · ไม่ซ้อนกับ #152 ของ Junior (แก้ `material_files.py`) แต่แก้ `ingestion.md` ไฟล์เดียวกัน: ใช้เลข AC ต่อจาก AC-28 ของ #152

## Next step

ข้อ 2 รอ Jam review test (`tests/unit/test_classify_never_stuck.py` · 6 test แดงทั้งหมด) · ok แล้วทำข้อ 3

## Waiting on

ไม่มี

## Notes for next time

- integration test ในเครื่องรันได้แล้วหลังแก้ service role key ใน `.env` (#151)
