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
- [ ] 3. 🙋 Junior review test
- [ ] 4. 🤖 `config/ai.yaml` `ingestion.storage_read_attempts`, `storage_read_backoff_s` (+ `IngestionConfig`) · `SupabaseMaterialFiles.read` retry + เปลี่ยน client ใต้ล็อกพร้อมเลขรุ่น
- [ ] 5. 🙋 Junior seed บัญชี demo ใหม่ด้วย `try_materials_flow --title` (หลัง merge) · ทุกไฟล์ต้อง classify ผ่าน
- [ ] 6. 🙋 บอกกลุ่ม (`config/ai.yaml`) + บอก Jam (`material_files.py`, `ingestion.md`) → `/work-done`

## Definition of done

- connection หลุดระหว่าง download → อ่านซ้ำด้วย client ใหม่ได้ · หลาย thread ที่ล้มพร้อมกันสร้าง client ใหม่ครั้งเดียว
- `StorageApiError` ไม่อ่านซ้ำ · ล้มครบจำนวนครั้ง → error เดิม (ไฟล์ `failed` ตามเดิม)
- ค่าจำนวนครั้งและเวลารออยู่ใน `config/ai.yaml` · CI ผ่าน

## Decisions

- 2026-11-17 · Junior: retry การอ่าน Storage (ไม่ใช่จำกัด concurrency หรือเพิ่ม max_tokens) · เปลี่ยน client แบบ thread-safe · test ต้องมี 2 read พร้อมกันที่ล้มพร้อมกันแล้วรอดทั้งคู่ · `config/ai.yaml` ok (Junior บอกกลุ่มเองก่อน merge) · ถ้ามีเวลาก่อน 23 พ.ย. ทำ `/retry` จริงเป็น PR แยก

## Next step

Junior review test ใน `tests/unit/test_material_files_retry.py` (ตาราง AC → test ในแชท)

## Waiting on

ไม่มี

## Notes for next time

- storage3 ตั้ง `http2=True` ใน client ของ Storage · ดาวน์โหลดพร้อมกันจากหลาย thread จึงวิ่งบน connection เดียว และล้มพร้อมกันเมื่อ server ปิด connection
