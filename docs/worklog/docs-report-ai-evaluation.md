# รายงานเทอม 1 · ส่วน AI, การวัดผล และงานวิจัยรองรับ

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/report-ai-evaluation` |
| Checklist item | ส่วน AI, การวัดผล และงานวิจัยรองรับในรายงาน |
| Status | paused · 2026-10-28 |

## Plan

- [x] 1. 🤖 สร้าง `docs/report/ai-evaluation.md` · โครง 4 หัวข้อ + เขียนหัวข้อ 1 **สถาปัตยกรรม AI** (code decides / LLM speaks, AI gateway, SymPy ตัดสินถูกผิด, prompt versioning, `<document>` กัน injection) จาก `CLAUDE.md`, `ai-orchestration.md` §1, `apps/api/app/ai/gateway.py`
- [x] 2. 🤖 หัวข้อ 2 **วิธีวัดผล**: golden set 3 ชุด (ลายมือ 30 รูป, หัวข้อ MTH10101, คำตอบ 50 ข้อ), กติกา label, metric และเป้า, คนทำ PoC ไม่ใช่คน label (และข้อยกเว้นที่ทีมตกลง) จาก `evals/README.md`, `specs/system/test-strategy.md`
- [x] 3. 🤖 หัวข้อ 3 **ผล PoC**: P1, P3 จาก report · P2 ใช้ผล SymPy (PR #75) และเว้นตัวเลข LLM ไว้ "รอผล" (เติมหลัง PR #82)
- [x] 4. 🤖 หัวข้อ 4 **งานวิจัยรองรับ learning model**: BKT, ระดับเป้า + เพดาน mastery, readiness, spaced review, wheel-spinning, ที่มาของตัวเลข [A]/[B]/[calc]/[C] จาก `learning-model.md`, `docs/research/learning-path.md`
- [x] 5. 🙋 Jam อ่านทั้งไฟล์ แล้วบอกส่วนที่ต้องแก้ในแชท (ภาษา, ความยาว, สิ่งที่ขาด)
- [ ] 6. 🤖 (หลัง P2 เสร็จ) เติมตัวเลข P2 จาก `specs/poc/reports/P2.md`

## Definition of done

- `docs/report/ai-evaluation.md` มีครบ 4 หัวข้อ ภาษาไทยปน technical term อังกฤษ เขียนให้อาจารย์และกรรมการอ่าน
- ตัวเลขทุกตัวตรงกับ report ของ PoC และ `config/learning.yaml` พร้อมอ้างที่มา (ไฟล์หรือ PR)
- งานวิจัยที่อ้างอยู่ใน `docs/research/learning-path.md` · ไม่อ้างงานที่ยังไม่ได้เปิดอ่าน โดยไม่บอกว่ายังไม่ได้อ่าน
- Jam review แล้ว · ตัวเลข P2 เติมครบ (ขั้น 6) ก่อนติ๊ก checklist

## Decisions

- 2026-10-28 · Jam อ่านครบ 4 หัวข้อแล้ว ok ไม่มีจุดแก้
- 2026-10-28 · หัวข้อ 4 ใช้เฉพาะงานใน `learning-path.md` และ References ของ `learning-model.md` · งานที่ติด ◐ (VanLehn 2011, Dunlosky & Rawson 2012, KT-IDEM, Elo) เขียนว่า "ยังไม่ได้เปิดต้นฉบับ" และไม่อ้างตัวเลข · จำนวนป้ายนับจาก `config/learning.yaml` (`# [A]` 7, `# [calc]` 14, `# [C]` 23 · 28 ต.ค.) ต้องนับใหม่ถ้า config เปลี่ยน
- 2026-10-28 · หัวข้อ 1 ใช้ตัวอย่างตรวจคำตอบ ans_007 (sign error บรรทัด 3) เป็นเส้นเรื่องเดียวที่แสดงหลักทั้งหมด · อ้าง PR #80 ซึ่งยังไม่ merge · ต้องเช็คอีกครั้งตอนท้ายว่า merge แล้ว
- 2026-10-28 · (Jam ตามที่เสนอ) เขียนเป็น Markdown ใน repo ที่ `docs/report/ai-evaluation.md` ให้ทีม review ผ่าน PR แล้วค่อยย้ายเข้าไฟล์ของมหาวิทยาลัยตอนท้าย · โครง 4 หัวข้อ: สถาปัตยกรรม AI · วิธีวัดผล · ผล PoC · งานวิจัยรองรับ

## Done today (2026-10-28)

- เขียน `docs/report/ai-evaluation.md` ครบ 4 หัวข้อ (สถาปัตยกรรม AI · วิธีวัดผล · ผล PoC · งานวิจัยรองรับ) · Jam ok ทุกหัวข้อ
- ตัวเลขของ LLM ใน P2 เว้นไว้ "รอผล" ใน §3.1 และ §3.4

## Next step

ขั้น 6 (รอ): หลัง `specs/poc/reports/P2.md` มีตัวเลขของ LLM แล้ว (branch `docs/poc-report-p2` · PR #82) เติมใน `docs/report/ai-evaluation.md` §3.1 แถว P2 และ §3.4 ย่อหน้า "ส่วน LLM" · เช็คด้วยว่า PR #80 merge แล้ว (อ้างใน §1.5)

## Waiting on

- ตัวเลข P2 จาก PR #80 → #82 (รอ quota Gemini free tier ~14:00 วันที่ 29 ต.ค.)

## Notes for next time

- ลำดับงานพรุ่งนี้: `feat/check-answer-classifier` (#80 รัน eval `--resume`) → `docs/poc-report-p2` (#82) → branch นี้ (#84)
- ตอนย้ายเข้าไฟล์รายงานของภาควิชา: path ของไฟล์ใน repo (เช่น `specs/...`) อาจต้องเปลี่ยนเป็นภาคผนวกหรือลิงก์ GitHub
- งาน Buffer (30 พ.ย.–4 ธ.ค.) ที่ทำล่วงหน้า · ยังไม่มีโครงรายงานของทั้งทีมหรือ template ของภาควิชาใน repo
