# ลำดับหน้าจอสำหรับ demo รวม (S4 · ศ. 27 พ.ย.)

| | |
|---|---|
| Owner | May |
| Branch | `docs/demo-flow` |
| Checklist item | เตรียมลำดับหน้าจอสำหรับ demo รวม |
| Status | ready for work-done · 2026-10-21 |

## Plan

- [x] 1. 🙋 May ตัดสินกรอบ: เวลารวม, ใครพูดช่วงไหน, ใช้ live / wireframe / ผล PoC แค่ไหน (Claude ถามเป็นตัวเลือก)
- [x] 2. 🤖 ร่าง `docs/design/demo-flow.md`: ลำดับช่วง (เรื่องเล่าของปาลตาม wireframe) · แต่ละช่วงบอกหน้าจอ, ของจริงหรือ wireframe, PoC/requirement ที่พิสูจน์, เวลา, คนพูด · ทางสำรองถ้า live พัง · checklist ก่อน demo (ใช้แทน e2e ตาม test-strategy §5)
- [x] 3. 🙋 May review
- [x] 4. 🤖 แจ้งงานที่ demo ต้องพึ่งเพื่อน (staging, `/uploads`, Vercel env) ใน "สิ่งที่ต้องพร้อมก่อน demo"

## Definition of done

- `docs/design/demo-flow.md` มีลำดับครบ เวลา คนพูด ทางสำรอง และ checklist ก่อน demo · May approve
- ติ๊ก checklist ได้เมื่อทีมเห็นด้วย (ลำดับอาจปรับหลังรู้ผล S3)

## Decisions

- 2026-10-21 · May เลือก: 15 นาที · แบ่งคนพูดตามงาน · ส่วนที่ไม่มีหน้าจริงใช้ wireframe คู่ผล PoC
- 2026-10-21 · ตัวเลขที่ยังไม่มี (P2, P4-lite TTFT, P8-lite) เขียนว่า "รอผล" ไม่เดา

## Next step

รัน /work-done · checklist ไม่ติ๊ก เพิ่ม sub-bullet ว่าร่างเสร็จ รอตัวเลขหลัง S3 (May ตกลง)

## Waiting on

ไม่มี

## Notes for next time

- ที่มา: `docs/design/wireframe.html` (37 หน้า), `use-cases.md`, `specs/poc/README.md` (P1, P2, P3, P4-lite, P6-lite, P8-lite), `sprint-checklists.md` (demo รวม ศ. 27 พ.ย.), `test-strategy.md` §5 (checklist demo แทน e2e)
