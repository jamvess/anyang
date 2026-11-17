# อ่าน Storage ซ้ำเมื่อ connection หลุด (classify ล้มแบบสุ่มตอนอัปโหลดหลายไฟล์)

| | |
|---|---|
| Owner | Junior |
| Branch | `fix/storage-read-retry` |
| Checklist item | ⭐ demo ขั้น 3 (ต่อจาก #140 · ไม่มีข้อใหม่ใน checklist · พบตอน seed บัญชี demo 17 พ.ย.) |
| Status | in progress · 2026-11-17 |

## Plan

- [x] 1. 🤖 หาสาเหตุ: `ingestion_jobs` ของ prep `267aa44f…` · sheet-02, sheet-03 ล้มเวลาเดียวกันทุกหลัก `read …: Server disconnected` · `ai_calls` classify 4 ครั้ง `ok` ทั้งหมด (ไม่ใช่ 429 ไม่ใช่ MAX_TOKENS)
- [x] 2. 🤖 spec `ingestion.md` §2.1 ข้อ 4 + AC-28 · test แดง `tests/unit/test_material_files_retry.py`
- [x] 3. 🙋 Junior review test (ok · ค่า 3 / 0.5 s ok)
- [x] 4. 🤖 `config/ai.yaml` `ingestion.storage_read_attempts`, `storage_read_backoff_s` (+ `IngestionConfig`) · `SupabaseMaterialFiles.read` retry + เปลี่ยน client ใต้ล็อกพร้อมเลขรุ่น
- [ ] 5. 🙋 Junior seed บัญชี demo ใหม่ด้วย `try_materials_flow --title` (หลัง merge) · ทุกไฟล์ต้อง classify ผ่าน
- [ ] 6. 🙋 บอกกลุ่ม (`config/ai.yaml`) + บอก Jam (`material_files.py`, `ingestion.md`) → `/work-done`

## Definition of done

- connection หลุดระหว่าง download → อ่านซ้ำด้วย client ใหม่ได้ · หลาย thread ที่ล้มพร้อมกันสร้าง client ใหม่ครั้งเดียว
- `StorageApiError` ไม่อ่านซ้ำ · ล้มครบจำนวนครั้ง → error เดิม (ไฟล์ `failed` ตามเดิม)
- ค่าจำนวนครั้งและเวลารออยู่ใน `config/ai.yaml` · CI ผ่าน

## Decisions

- 2026-11-17 · Junior: retry การอ่าน Storage (ไม่ใช่จำกัด concurrency หรือเพิ่ม max_tokens) · เปลี่ยน client แบบ thread-safe · test ต้องมี 2 read พร้อมกันที่ล้มพร้อมกันแล้วรอดทั้งคู่ · `config/ai.yaml` ok (Junior บอกกลุ่มเองก่อน merge) · ถ้ามีเวลาก่อน 23 พ.ย. ทำ `/retry` จริงเป็น PR แยก

## Next step

ข้อ 5: Junior restart API (โหลด `config/ai.yaml` 1.23) แล้ว seed บัญชี demo ใหม่จาก branch นี้ · `uv run python -m scripts.try_materials_flow --title "MTH10101 กลางภาค"` (ต้อง merge #149 ก่อน หรือ cherry-pick) · ทุกไฟล์ต้อง classify ผ่าน · ถ้ามี warning `storage read … dropped` ใน log แปลว่า retry ทำงาน

## Waiting on

ไม่มี

## Notes for next time

- 2026-11-17 · ข้อ 4: unit 1880 ผ่าน · `test_material_files_retry.py` วน 40 รอบไม่ล้ม · test ที่ล้มพร้อมกันจับการสร้าง client ซ้ำได้เมื่อ thread หนึ่งสร้าง client ใหม่ก่อนอีก thread ทิ้ง (ลำดับขึ้นกับ scheduler)

- storage3 ตั้ง `http2=True` ใน client ของ Storage · ดาวน์โหลดพร้อมกันจากหลาย thread จึงวิ่งบน connection เดียว และล้มพร้อมกันเมื่อ server ปิด connection
