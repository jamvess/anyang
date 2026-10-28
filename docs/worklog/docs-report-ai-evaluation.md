# รายงานเทอม 1 · ส่วน AI, การวัดผล และงานวิจัยรองรับ

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/report-ai-evaluation` |
| Checklist item | ส่วน AI, การวัดผล และงานวิจัยรองรับในรายงาน |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 สร้าง `docs/report/ai-evaluation.md` · โครง 4 หัวข้อ + เขียนหัวข้อ 1 **สถาปัตยกรรม AI** (code decides / LLM speaks, AI gateway, SymPy ตัดสินถูกผิด, prompt versioning, `<document>` กัน injection) จาก `CLAUDE.md`, `ai-orchestration.md` §1, `apps/api/app/ai/gateway.py`
- [x] 2. 🤖 หัวข้อ 2 **วิธีวัดผล**: golden set 3 ชุด (ลายมือ 30 รูป, หัวข้อ MTH10101, คำตอบ 50 ข้อ), กติกา label, metric และเป้า, คนทำ PoC ไม่ใช่คน label (และข้อยกเว้นที่ทีมตกลง) จาก `evals/README.md`, `specs/system/test-strategy.md`
- [ ] 3. 🤖 หัวข้อ 3 **ผล PoC**: P1, P3 จาก report · P2 ใช้ผล SymPy (PR #75) และเว้นตัวเลข LLM ไว้ "รอผล" (เติมหลัง PR #82)
- [ ] 4. 🤖 หัวข้อ 4 **งานวิจัยรองรับ learning model**: BKT, ระดับเป้า + เพดาน mastery, readiness, spaced review, wheel-spinning, ที่มาของตัวเลข [A]/[B]/[calc]/[C] จาก `learning-model.md`, `docs/research/learning-path.md`
- [ ] 5. 🙋 Jam อ่านทั้งไฟล์ แล้วบอกส่วนที่ต้องแก้ในแชท (ภาษา, ความยาว, สิ่งที่ขาด)
- [ ] 6. 🤖 (หลัง P2 เสร็จ) เติมตัวเลข P2 จาก `specs/poc/reports/P2.md`

## Definition of done

- `docs/report/ai-evaluation.md` มีครบ 4 หัวข้อ ภาษาไทยปน technical term อังกฤษ เขียนให้อาจารย์และกรรมการอ่าน
- ตัวเลขทุกตัวตรงกับ report ของ PoC และ `config/learning.yaml` พร้อมอ้างที่มา (ไฟล์หรือ PR)
- งานวิจัยที่อ้างอยู่ใน `docs/research/learning-path.md` · ไม่อ้างงานที่ยังไม่ได้เปิดอ่าน โดยไม่บอกว่ายังไม่ได้อ่าน
- Jam review แล้ว · ตัวเลข P2 เติมครบ (ขั้น 6) ก่อนติ๊ก checklist

## Decisions

- 2026-10-28 · หัวข้อ 1 ใช้ตัวอย่างตรวจคำตอบ ans_007 (sign error บรรทัด 3) เป็นเส้นเรื่องเดียวที่แสดงหลักทั้งหมด · อ้าง PR #80 ซึ่งยังไม่ merge · ต้องเช็คอีกครั้งตอนท้ายว่า merge แล้ว
- 2026-10-28 · (Jam ตามที่เสนอ) เขียนเป็น Markdown ใน repo ที่ `docs/report/ai-evaluation.md` ให้ทีม review ผ่าน PR แล้วค่อยย้ายเข้าไฟล์ของมหาวิทยาลัยตอนท้าย · โครง 4 หัวข้อ: สถาปัตยกรรม AI · วิธีวัดผล · ผล PoC · งานวิจัยรองรับ

## Next step

ขั้น 3: เขียนหัวข้อ 3 "ผล Proof of Concept" ใน `docs/report/ai-evaluation.md` จาก `specs/poc/reports/P1.md`, `P3.md` และร่าง `P2.md` (branch `docs/poc-report-p2`)

## Waiting on

ไม่มี (ขั้น 6 รอ P2)

## Notes for next time

- งาน Buffer (30 พ.ย.–4 ธ.ค.) ที่ทำล่วงหน้า · ยังไม่มีโครงรายงานของทั้งทีมหรือ template ของภาควิชาใน repo
