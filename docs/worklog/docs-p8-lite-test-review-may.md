# P8-lite: May review test ของ compute_importance ย้อนหลัง

| | |
|---|---|
| Owner | May |
| Branch | `docs/p8-lite-test-review-may` |
| Checklist item | P8-lite ร่วมกับทีม (review test) |
| Status | in progress · 2026-11-11 |

## Plan

test อยู่ใน `main` แล้ว (PR #113 merge 8 พ.ย.) · review ย้อนหลังตามที่ checklist บอก · **ห้ามแก้ test** (Jam review แล้ว) · เจออะไรให้จดใน `poc/P8-lite/metrics.md` แล้วแก้ใน PR ใหม่ถ้าจำเป็น

- [x] 1. 🤖 อ่าน `specs/features/scope/compute-importance.md` (27 AC) และ `apps/api/tests/unit/test_stars.py` · ทำตาราง AC → test เป็นภาษาไทย · หา AC ที่ไม่มี test และ test ที่ไม่ตรง AC · 2026-11-11 27 AC มี test ครบ (AC-19 อยู่ใน `test_settings.py`, AC-pure ดูจาก CI) · 39 test ผ่าน · เจอ 4 เรื่องให้ May ตัดสิน: ไม่มี test ของ §10 ข้อ 9 และข้อ 10 · comment ใน test AC-13 ทำให้เข้าใจผิด · AC-9 ไม่ assert ดาวของ B
- [x] 2. 🙋 May review: จดเวลาเริ่มตอนเริ่มอ่าน และเวลาจบ · ตอบเรื่องที่ Claude เจอเป็นตัวเลือก (test ถูก / test ผิด / เปราะ) · 2026-11-11 11:35–11:36 (1 นาที · อ่านตารางสรุปของ Claude ไม่ได้อ่านโค้ด test) · ก+ข ช่องโหว่ เสนอ Jam เพิ่ม test · ค ไม่เป็นปัญหา · ง test เปราะ เสนอ Jam แก้ comment
- [x] 3. 🤖 กรอก `poc/P8-lite/metrics.md`: §4 แถว May (เวลาจริง) · §3 test ที่ผิดหรือเปราะ (ถ้ามี) · §6 เวลาที่คนใช้ · 2026-11-11 กรอกแล้ว
- [x] 4. 🤖 ติ๊ก checklist ข้อของ May (ทำใน `/work-done`) ถ้า Junior ยังไม่ review ให้จดเป็นบรรทัดย่อยว่าส่วนของ May เสร็จแล้ว

## Definition of done

- `metrics.md` มีเวลาที่ May ใช้ review (เริ่ม–จบจากนาฬิกาจริง) และผล review
- test ไม่ถูกแก้ · ถ้าเจอ test ผิด มีบันทึกใน §3 และบอก Jam

## Decisions

- 2026-11-11 · ใช้ type `docs` · แก้แค่ metrics และ checklist

## Next step

ทุกขั้นเสร็จแล้ว · May พิมพ์ `/work-done` · แจ้ง Jam เรื่อง test 2 ตัวที่ขาดและ comment AC-13

## Waiting on

ไม่มี

## Notes for next time

- `poc/P8-lite/` เป็นของทั้งทีม (P8-lite ร่วมกัน) · Jam เป็นเจ้าของ spec `compute_importance`
