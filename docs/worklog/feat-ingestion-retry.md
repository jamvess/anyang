# ปุ่ม "ลองใหม่" ในหน้าความคืบหน้า (ขั้นรวม + รายไฟล์)

| | |
|---|---|
| Owner | May |
| Branch | `feat/ingestion-retry` |
| Checklist item | ไม่มีใน checklist · UC-02 E5 ("ลองใหม่") + api.md "รอตัดสิน" ข้อ 8 (ขั้นรวมล้มไม่มีทางออก) · เจอ 19 พ.ย. (`merge_topics: ProviderRateLimited`) · เสนอเพิ่มเข้า checklist ของ May ตอน `/work-done` |
| Status | in progress · 2026-11-19 |

## Plan

- [x] 1. 🤖 `/spec-feature` → `specs/features/exam-prep/ingestion-retry.md` (CM-07 · UC-02 E5): หน้าเว็บ S11 (ปุ่มที่ขั้นรวมและแถวไฟล์ที่ล้ม) + API (endpoint ใหม่สำหรับขั้นรวม · ต่อ `/materials/{id}/retry` ที่เป็น stub กับ `IngestionRunner.retry` ที่มีแล้ว) + ข้อที่ต้องแก้ใน `api.md` (shared)
- [x] 2. 🙋 May อ่าน spec + ตอบ open questions (ถามเป็นตัวเลือก)
- [ ] 3. 🤖 `/spec-to-tests` ทั้ง `apps/api` และ `apps/web` → test แดง
- [ ] 4. 🙋 May review test
- [ ] 5. 🤖 `/implement-feature` ฝั่ง API (router ของ Junior · service ของ Jam) + แก้ `api.md`
- [ ] 6. 🤖 `/implement-feature` ฝั่งหน้าเว็บ + `pnpm gen:api`
- [ ] 7. 🙋 ลองในเบราว์เซอร์: prep ของ May ที่ "หาหัวข้อ" ล้ม 19 พ.ย. → กดลองใหม่ → ไปหน้า scope
- [ ] 8. 🙋 ส่งข้อความกลุ่ม: แก้ router ของ Junior, `api.md` (shared), เรียก service ของ Jam

## Definition of done

- หน้า S11: ขั้นรวมที่ล้มและไฟล์ที่ล้มมีปุ่ม "ลองใหม่" · กดแล้วกลับไปหมุนในหน้าเดิม poll ต่อ แล้วไปหน้า scope เองเมื่อเสร็จ
- API: endpoint ลองขั้นรวมใหม่ + `/materials/{id}/retry` ทำงานจริง (ไม่ใช่ stub) บนทางที่มี token
- test จาก acceptance criteria ผ่าน · `api.md` อัปเดต · บอกกลุ่มแล้ว
- ลองเส้นจริงบนเครื่อง May ผ่าน

## Decisions

- 2026-11-19 · May เลือก: ครอบคลุมทั้งขั้นรวมและรายไฟล์ · "ไปต่อโดยไม่มีไฟล์นี้" ไม่ทำ (ต้องใช้ลบไฟล์ CM-10 · S5)
- 2026-11-19 · May เลือก: May ทำ API เองด้วย (แบบ #160) · บอก Junior/Jam ในกลุ่ม
- 2026-11-19 · May เลือก: กดแล้วไม่ถามยืนยัน ขั้นนั้นกลับเป็น ◐ แล้ว poll ต่อในหน้าเดิม
- 2026-11-19 · spec §10 ตัดสินทุกข้อตามข้อเสนอ: ไม่แก้ test เดิม AC-19 (แก้ข้อความใน upload-page.md แทน) · ข้อความตาม §2.1 · ขั้นรวมตอบ 202 ไม่มี body · ลองขั้นรวมใหม่ทำ topics ใหม่เสมอ · กดซ้ำไม่จำกัด

## Next step

ขั้น 3: รัน `/spec-to-tests` กับ `specs/features/exam-prep/ingestion-retry.md` · test ใหม่ตาม §8 (`apps/web/tests/materials/ProgressRetry.test.tsx`, `apps/api/tests/unit/test_ingestion_retry_api.py`, `test_ingestion_retry_runner.py`) · ห้ามแตะ `ProgressPage.test.tsx`

## Waiting on

ไม่มี

## Notes for next time

- `IngestionRunner.retry(material_id)` มีแล้วใน `apps/api/app/services/ingestion.py` · `start(prep_id)` ที่ไม่มีไฟล์รอก็รัน `build_scope` ใหม่ได้ (loop `first`) · ขั้นรวมรันซ้ำได้หัวข้อชุดใหม่แทนชุดเดิม (`ingestion.md` §2.4 ข้อ 6)
- prep ของ May ที่ "หาหัวข้อ" ล้ม 19 พ.ย. (`ingestion_jobs.error` = `merge_topics: ProviderRateLimited`) ใช้ลองเส้นจริงได้
