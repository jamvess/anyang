# หน้าตรวจขอบเขต + ดาว (S12, S38)

| | |
|---|---|
| Owner | May |
| Branch | `feat/scope-review` |
| Checklist item | ไม่มีข้อตรงใน checklist · SM-02, SM-03, SM-04 (แสดงผล) · UC-02 · wireframe S12, S38 |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 `/spec-feature` เขียน `specs/features/scope/scope-review.md` จาก SM-02, SM-03, SM-04, UC-02 (ขั้นตรวจขอบเขต, A4), ai-orchestration §2.3.4–2.3.6, wireframe S12 + S38, api.md (`GET /exam-preps/{id}/scope`, `GET /topics/{id}/sources`) · เสนอรูปร่างของ response (api.md ยังมีแค่ชื่อ endpoint) เป็นคำถามให้ Junior
- [x] 2. 🙋 May review spec และตอบคำถามเรื่อง UI (ถามเป็นตัวเลือก)
- [x] 3. 🤖 ถาม Junior เรื่อง api.md ใน PR: รูปร่างของ scope และ sources, ช่วงหน้า (`topic_sources` ยังไม่มี · data-model ข้อ 1), `map_note` (ข้อ 3)
- [x] 4. 🤖 `/spec-to-tests` · ใช้ fixture ของหน้า scope (ข้อมูลจาก S12/S38) · ต้องแดงก่อน
- [x] 5. 🙋 May review test
- [x] 6. 🤖 `/implement-feature` จน test เขียว · route `app/preps/[id]/scope`
- [ ] 7. 🙋 May ดูหน้าในเบราว์เซอร์เทียบกับ wireframe S12 / S38 (ข้อมูลจำลอง)

## Definition of done

- AC ทุกข้อใน `scope-review.md` มี test และผ่าน · lint, typecheck, test, build ผ่าน
- หน้าแสดงหัวข้อเรียงตามลำดับจาก API พร้อมดาว เหตุผล ที่มา · กดหัวข้อแล้วเห็นข้อความต้นฉบับ + ข้อสอบเก่าในหัวข้อ · มีกล่องข้อสอบที่ไม่เข้าหัวข้อไหน · ทุกค่ามาจาก API ไม่คำนวณดาวในหน้าเว็บ
- คำถาม api.md ส่งถึง Junior แล้ว

## Decisions

- 2026-10-28 · ทำเฉพาะหน้า S12 (+ รายละเอียด S38) · แชทแก้ขอบเขต (S13) และหน้าสรุปยืนยัน (S14) เป็นงานถัดไป · ปุ่ม "ขอแก้ก่อน" / "ยืนยันขอบเขตนี้" จะกำหนดใน spec ว่าทำอะไรในรอบนี้
- 2026-10-28 · May ตัดสิน OQ 1–4 ตามข้อเสนอ: "ขอแก้ก่อน" แสดงแต่กดไม่ได้ · เปิดรายละเอียดได้หลายหัวข้อ · หัวข้อ 0 ดาวแสดงท้ายรายการ ป้าย "ตัดออก" · หลังยืนยันแล้วอ่านอย่างเดียว + ลิงก์ไปห้องติว · ถาม Junior OQ 5–8 ใน PR #81
- 2026-10-28 · test 27 ตัว (รวมที่รันซ้ำ 2 ค่า) แดงทั้งไฟล์เพราะยังไม่มี `components/scope/ScopeReview` · fixture `scope-s12.json` (6 หัวข้อ + ข้อสอบไม่เข้าหัวข้อ 1 ข้อ ตาม S12/S38) และ `sources-t3.json` (S38) · `ScopeReview` รับ `navigate` ให้ test ตรวจการไปห้องติวได้โดยไม่ต้องมี router
- 2026-10-28 · implement เสร็จ: red → green 1 รอบ · test 242/242 · หน้า `/preps/[id]/scope` (`ScopeReviewRoute` ใช้ router · `ScopeReview` รับ `navigate`) · type ของ scope/sources เขียนเองชั่วคราวจนกว่า Junior มี schema · ไม่แก้ test เดิม

## Next step

ขั้น 7: May ดูหน้า /preps/[id]/scope ในเบราว์เซอร์เทียบ wireframe S12 / S38 ด้วยข้อมูลจำลอง (หน้าทดลองชั่วคราว ไม่ commit)

## Waiting on

- Junior ตอบ OQ 5–8 ใน PR #81 (รูปร่างของ scope และ sources, ช่วงหน้า, map_note) · ไม่บล็อก test

## Notes for next time

- ดาวคำนวณด้วย code ฝั่ง backend (§2.3.5) หน้าเว็บแสดงอย่างเดียว · เหตุผลเป็น template เช่น "ออกในข้อสอบเก่า 2 ใน 2 ชุด"
- data-model "รอผล" ข้อ 1 (ช่วงหน้า), ข้อ 3 (`map_note`) ยังไม่มีที่เก็บ
