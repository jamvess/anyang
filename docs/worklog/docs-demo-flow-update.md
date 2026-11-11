# อัปเดตลำดับ demo รวมตามของที่มีจริงตอนนี้

| | |
|---|---|
| Owner | May |
| Branch | `docs/demo-flow-update` |
| Checklist item | เตรียมลำดับหน้าจอสำหรับ demo รวม |
| Status | in progress · 2026-11-11 |

## Plan

ไฟล์: `docs/design/demo-flow.md` (ร่าง 21 ต.ค. · PR #61) · demo รวม ศ. 27 พ.ย. · ตัวเลขทุกตัวต้องอ้าง `specs/poc/reports/*.md` หรือ `poc/P8-lite/metrics.md`

- [x] 1. 🤖 เทียบร่างเดิมกับของที่มีตอนนี้ (P1–P4-lite, P6-lite, P8-lite, ห้องเดโม่ในเครื่อง #115, canvas #117, staging ยังเปิด AI จริงไม่ได้) · สรุปเป็นรายการ "เปลี่ยนอะไร" + เรื่องที่ May ต้องตัดสิน
- [x] 2. 🙋 May ตัดสินเรื่องลำดับและช่วง live (Claude ถามเป็นตัวเลือก)
- [x] 3. 🤖 แก้ `demo-flow.md`: ตารางลำดับ, รายละเอียดช่วง live, ตัวเลข PoC, ตาราง "สิ่งที่ต้องพร้อม" (เจ้าของ + สถานะ), checklist ก่อน demo, คำถามที่น่าจะโดนถาม
- [x] 4. 🤖 ตรวจว่าตัวเลขทุกตัวตรงกับ report · เวลารวม 15 นาที
- [x] 5. 🙋 May ส่งร่างให้ทีมตกลงลำดับในแชทกลุ่ม (Claude ร่างข้อความ) · 2026-11-11 ส่งแล้ว · May เลือก merge ก่อนไม่รอทีมตอบ

## Definition of done

- ตัวเลข P2, P4-lite, P8-lite เติมแล้ว (ไม่มี "รอผล") และตรงกับ report
- ช่วง live ตรงกับของที่ทำได้จริง พร้อมทางสำรอง
- ทีมตกลงลำดับ (ถ้ายังไม่ตอบตอน merge → ไม่ติ๊ก checklist แต่เพิ่มบรรทัดย่อยว่าเหลือรอทีมตกลง)

## Decisions

- 2026-11-11 · ใช้ type `docs` · แก้เอกสาร design
- 2026-11-11 · May ตัดสิน: (1) live ในเครื่องเป็นหลัก staging เป็นโบนัส · (2) รวมช่วง 3+4 เป็น live 5:30 ช่วง 4 เหลือตัวเลข 1:00 · (3) ใช้รูปที่เตรียมไว้ พูดถึง canvas สั้นๆ · (4) ใช้เครื่อง May ขอ role Vertex AI User จาก Jam
- 2026-11-11 · เจอระหว่างเขียน: รูปใน `evals/handwriting/raw/` ใช้ในสไลด์/demo ได้เฉพาะคนที่ติ๊ก consent ข้อ 5 → เสนอให้ May เขียนรูปเอง
- 2026-11-11 · merge ก่อนทีมตอบ (May เลือก) · ตามกติกา 31 ต.ค. ไม่ต้องรอ approve · ถ้าทีมอยากแก้ลำดับ เปิด PR ใหม่
- 2026-11-11 · ตรวจ: เวลารวม 15:00 · ขั้นของช่วง live รวม 5:30 · ตัวเลขทุกตัวตรงกับ P1, P2, P3 (รอบ Vertex), P4-lite, P6-lite, P8-lite metrics

## Next step

ทุกขั้นเสร็จแล้ว · May พิมพ์ `/work-done` · **ไม่ติ๊ก** checklist (รอทีมตกลงลำดับ) แต่เพิ่มบรรทัดย่อย

## Waiting on

- Jam: ให้ role Vertex AI User แก่บัญชีของ May (ก่อนซ้อม)
- ทีม: ตกลงลำดับ demo

## Notes for next time

- staging เปิด `AI_PROVIDER=live` ไม่ได้จนกว่า `AUTH_REQUIRED=true` + เปลี่ยน runtime SA (`specs/features/platform/api-auth.md`) · งานของ Junior
- `answer-canvas.md` §10 รอ May ตัดสินหน้าตาย้อนหลัง (งานแยก)
