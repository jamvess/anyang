# อัปเดตลำดับ demo รวมตามของที่มีจริงตอนนี้

| | |
|---|---|
| Owner | May |
| Branch | `docs/demo-flow-update` |
| Checklist item | เตรียมลำดับหน้าจอสำหรับ demo รวม |
| Status | in progress · 2026-11-11 |

## Plan

ไฟล์: `docs/design/demo-flow.md` (ร่าง 21 ต.ค. · PR #61) · demo รวม ศ. 27 พ.ย. · ตัวเลขทุกตัวต้องอ้าง `specs/poc/reports/*.md` หรือ `poc/P8-lite/metrics.md`

- [ ] 1. 🤖 เทียบร่างเดิมกับของที่มีตอนนี้ (P1–P4-lite, P6-lite, P8-lite, ห้องเดโม่ในเครื่อง #115, canvas #117, staging ยังเปิด AI จริงไม่ได้) · สรุปเป็นรายการ "เปลี่ยนอะไร" + เรื่องที่ May ต้องตัดสิน
- [ ] 2. 🙋 May ตัดสินเรื่องลำดับและช่วง live (Claude ถามเป็นตัวเลือก)
- [ ] 3. 🤖 แก้ `demo-flow.md`: ตารางลำดับ, รายละเอียดช่วง live, ตัวเลข PoC, ตาราง "สิ่งที่ต้องพร้อม" (เจ้าของ + สถานะ), checklist ก่อน demo, คำถามที่น่าจะโดนถาม
- [ ] 4. 🤖 ตรวจว่าตัวเลขทุกตัวตรงกับ report · เวลารวม 15 นาที
- [ ] 5. 🙋 May ส่งร่างให้ทีมตกลงลำดับในแชทกลุ่ม (Claude ร่างข้อความ)

## Definition of done

- ตัวเลข P2, P4-lite, P8-lite เติมแล้ว (ไม่มี "รอผล") และตรงกับ report
- ช่วง live ตรงกับของที่ทำได้จริง พร้อมทางสำรอง
- ทีมตกลงลำดับ (ถ้ายังไม่ตอบตอน merge → ไม่ติ๊ก checklist แต่เพิ่มบรรทัดย่อยว่าเหลือรอทีมตกลง)

## Decisions

- 2026-11-11 · ใช้ type `docs` · แก้เอกสาร design

## Next step

Claude ทำขั้น 1: สรุปสิ่งที่เปลี่ยน + เรื่องที่ต้องตัดสิน

## Waiting on

ไม่มี

## Notes for next time

- staging เปิด `AI_PROVIDER=live` ไม่ได้จนกว่า `AUTH_REQUIRED=true` + เปลี่ยน runtime SA (`specs/features/platform/api-auth.md`) · งานของ Junior
- `answer-canvas.md` §10 รอ May ตัดสินหน้าตาย้อนหลัง (งานแยก)
