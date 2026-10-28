# Report P2 · ตรวจคำตอบ (SymPy + LLM)

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/poc-report-p2` |
| Checklist item | Report P2 |
| Status | paused · 2026-10-28 |

## Plan

- [x] 1. 🤖 ร่าง `specs/poc/reports/P2.md` จาก `specs/poc/_REPORT_TEMPLATE.md` · ส่วนที่มีข้อมูลแล้ว: คำถาม, วิธีทดสอบ, ผลของ SymPy อย่างเดียว (PR #75: ตัดสินได้ 45/50 · verdict 45/45 · first_wrong_line 20/22 · 0.14 วินาทีต่อข้อ), ปัญหาที่เจอตอนรันจริง (429 ต่อนาที, timeout จาก default thinking → `thinking: low`, เพดานต่อวัน) · เว้นช่องตัวเลข 3 ตัวของ LLM ไว้เป็น "รอผล"
- [x] 2. 🙋 Jam อ่านร่าง แล้วตอบในแชทว่าวิธีทดสอบและข้อจำกัดถูกต้องไหม
- [ ] 3. 🙋 (รอ) Jam รัน eval ให้ครบ 50 ข้อใน branch `feat/check-answer-classifier` (ดู worklog ของ branch นั้น) · หลัง PR #80 merge แล้ว `git merge origin/main` ที่ branch นี้
- [ ] 4. 🤖 เติมตัวเลข verdict, error_type, first_wrong_line จาก `evals/answers/results/v1.json` · PASS / FAIL · ดูข้อที่พลาดแยกตามที่มา (SymPy / LLM) · เสนอการตัดสินใจและสิ่งที่ต้องแก้ใน spec/config (ยังไม่แก้จนกว่า Jam ok)
- [ ] 5. 🙋 Jam ตัดสินผล P2 (ผ่าน / ใช้ fallback "ลด error types เหลือ 4" / แก้ prompt เป็น v2)
- [ ] 6. 🤖 อัปเดตสถานะ P2 ใน `specs/poc/README.md` (บรรทัด "ผล" แบบ P1, P3)

## Definition of done

- `specs/poc/reports/P2.md` ยาว 1 หน้า ตาม template · ตัวเลขตรงกับที่วัดจริงพร้อมจำนวนตัวอย่าง · เทียบเกณฑ์ P2 (verdict ≥ 95%, error_type ≥ 80%, first_wrong_line ≥ 85%) พร้อม PASS / FAIL
- มีคำสั่งรันซ้ำ (`evals/run_checker.py` + `evals/run_eval.py`) และชื่อ model ที่ใช้จริง
- การตัดสินใจและไฟล์ spec/config ที่ต้องแก้ ได้ Jam ok แล้ว
- `specs/poc/README.md` P2 มีบรรทัดผล

## Decisions

- 2026-10-28 · Jam ok ร่าง (§2 วิธีทดสอบ, §6 ความเสี่ยง) · รวมข้อเสนอให้คนอื่นที่ไม่ใช่ Jam ตรวจ label ซ้ำในข้อที่ checker กับ label ไม่ตรงกัน
- 2026-10-28 · ตัวหารของเกณฑ์จาก golden set: verdict 50 · error_type 28 (label ไม่ใช่ `correct`) · first_wrong_line 24 (label มีเลขบรรทัด) → ผ่านเมื่อ ≥ 47, ≥ 23, ≥ 21 ข้อ · เขียนไว้ใน report เพื่อให้อ่านผลง่าย
- 2026-10-28 · ร่าง report ล่วงหน้าระหว่างรอ quota รายวันของ Gemini free tier · ทำคนละ branch กับ PR #80 เพราะ checklist แยกเป็นคนละข้อ

## Done today (2026-10-28)

- ร่าง `specs/poc/reports/P2.md` ครบ 6 หัวข้อ · ผล SymPy อย่างเดียวจาก PR #75 (45/50 · 45/45 · 20/22 · 0.14 วินาที) · ตาราง pipeline เต็มเป็น "รอผล" · Jam ok ร่าง
- ลบ branch ในเครื่องที่ merge แล้ว (`feat/verdict-mark`, `feat/sympy-service`)

## Next step

ขั้น 3 (🙋 รอ): หลัง quota รีเซ็ต (~14:00 วันที่ 29 ต.ค.) ทำต่อที่ branch `feat/check-answer-classifier` ก่อน (รัน eval ตาม worklog ของ branch นั้น) · พอ PR #80 merge แล้ว กลับมาที่ branch นี้ `git merge origin/main` แล้วทำขั้น 4 (เติมตัวเลขจาก `evals/answers/results/v1.json`)

## Waiting on

- ผล eval 50 ข้อจาก PR #80 (รอ quota free tier รีเซ็ต ~14:00 เวลาไทยของวันที่ 29 ต.ค.) · แล้ว PR #80 ต้อง merge ก่อน (Junior review)

## Notes for next time

- ผล SymPy อย่างเดียวมาจาก script ชั่วคราวตอนทำ PR #75 (ไม่ได้ commit) · ตัวเลขอยู่ใน description ของ PR #75 · ผลรวมของ pipeline จะมาจาก `run_checker.py` + `run_eval.py` ซึ่งรันซ้ำได้
- label ของ golden set ร่างโดย AI (`evals/answers/worksheet.md`) ต้องเขียนเป็นข้อจำกัดใน report
- branch `feat/sympy-service` บน GitHub ยังไม่ถูกลบ · Claude ลบด้วย `git push --delete` ไม่ได้ (auto mode ไม่อนุญาต) · Jam กด Delete branch ในหน้า PR #75 เอง
- ไฟล์ `evals/answers/predictions/v1.jsonl` (4 ข้อ) และ `evals/answers/results/` อยู่ในเครื่อง Jam ไม่ได้ commit · ใช้กับ `--resume` ใน branch `feat/check-answer-classifier`
- 429 บอก model เป็น `gemini-3.6-flash` ทั้งที่ override เป็น `gemini-3.5-flash` · ต้องจดชื่อ model ที่ใช้จริง
