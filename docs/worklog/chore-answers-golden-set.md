# เตรียม golden set คำตอบ 50 ข้อ (P2)

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/answers-golden-set` |
| Checklist item | Label golden set คำตอบ 50 ข้อ (D8) |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 test ก่อน: `evals/answers/make_worksheet.py` (a) สร้างใบงาน `evals/answers/worksheet.md` 50 หัวข้อ: ans_001–030 จากรูปลายมือ (image, writer, problem, answer_format, reference, lines ก๊อปจาก `handwriting/`) + ans_031–050 คำตอบแบบพิมพ์ (ช่องว่างให้เขียน) · ช่อง verdict / error_type / first_wrong_line / method ว่างทุกข้อ (b) `--build` อ่านใบงานที่กรอกแล้วเขียน `labels.jsonl` และตรวจกติกาใน `evals/README.md` (ค่าที่อนุญาต, error_type ว่างเมื่อ `correct`, `incomplete` → `concept`, first_wrong_line `null` ตามกฎ และไม่เกินจำนวนบรรทัด) → 🙋 Jam review test
- [x] 2. 🤖 implement จน test ผ่าน แล้วสร้าง `worksheet.md` จริง
- [x] 3. 🤖 `evals/README.md`: ขั้นตอนใช้ใบงาน + โควตา error type ของคำตอบพิมพ์ 20 ข้อ · แก้ข้อความ checklist (ไฟล์ร่วม · Jam ตกลงแล้ว 21 ต.ค.)
- [ ] 4. 🙋 Jam ส่งข้อความในกลุ่ม (Claude ร่างให้) ขอ May หรือ Junior เขียนคำตอบพิมพ์ 20 ข้อ และ label ครบ 50 ข้อ

## Definition of done

- `evals/answers/worksheet.md` พร้อมให้คน label กรอก (50 หัวข้อ) และ `--build` แปลงเป็น `labels.jsonl` ที่ `run_eval.py` อ่านได้
- คู่มือใช้ใบงานอยู่ใน `evals/README.md`
- ทีมรู้ว่าใครเป็นคน label (ข้อความในกลุ่มส่งแล้ว)
- การ label จริงทำใน branch ของคน label ข้อ checklist ยังไม่ติ๊กจนกว่า label ครบ

## Decisions

- 2026-10-21 · (Jam เลือก 1a) คน label verdict / error_type / first_wrong_line คือ May หรือ Junior ไม่ใช่ Jam เพราะ `evals/README.md` "กฎ": คน label ไม่ใช่คนทำ PoC และ Jam ทำ P2 · Jam + Claude เตรียมเฉพาะ field ที่ไม่ต้องตัดสิน · 20 ข้อที่ขาดเป็นคำตอบแบบพิมพ์ (`image: null`) จากโจทย์ P01–P17 ให้ May หรือ Junior เขียน
- 2026-10-21 · Claude ไม่เดา verdict ล่วงหน้า เพราะ golden set ต้องมาจากคนล้วนๆ
- 2026-10-21 · ใบงานเป็น markdown 1 หัวข้อต่อ 1 คำตอบ (ไม่ใช่ตาราง) เพราะ LaTeX มี `|` (`\left|x\right|`) ซึ่งทำให้ตาราง markdown พัง และกรอกง่ายกว่าแก้ JSONL ตรงๆ

- 2026-10-21 · (Jam ok) โควตาคำตอบพิมพ์ 20 ข้อ: sign 3 · prerequisite 3 · wrong_method 3 · concept 3 (มี incomplete ≥ 1) · calculation 3 · no_answer 2 · correct_with_flaw 2 · correct + method other 1
- 2026-10-21 · ข้อ 1 test (red): 15 function / 32 case ใน `evals/answers/test_make_worksheet.py` · ใบงานใช้ `problem_id` (P01–P17) แล้ว `--build` ดึง problem, reference, answer_format จาก `problems.md` · `--build` เขียนเฉพาะข้อที่กรอก verdict แล้ว (label ทีละส่วนได้ และ `run_eval.py` ไม่เจอแถวว่าง) · method ว่าง = `doc` · ถ้ามีข้อผิดกติกาแม้ข้อเดียว ไม่เขียนไฟล์เลย · ชื่อ test ใช้ `evals_readme_p2` แบบเดียวกับ `test_make_labels.py`

- 2026-10-21 · (Jam ok) แก้ `fill()` ใน test ที่ review แล้ว 2 จุด: `re.subn` อ่าน `\cos` ในข้อความแทนเป็น escape (`bad escape \c`) → เปลี่ยนเป็น `lambda` · สิ่งที่ test ตรวจเหมือนเดิม
- 2026-10-21 · ข้อ 2: `make_worksheet.py` ผ่าน 32/32 (evals ทั้งหมด 64) · สร้าง `worksheet.md` จริง: 50 หัวข้อ (รูป 30 · พิมพ์ 20) · ลอง `--build` กับใบงานว่างได้ 0 แถว (ลบไฟล์ทิ้ง ไม่ commit `labels.jsonl` ว่าง)

- 2026-10-21 · ข้อ 3: หัวข้อ "ใบงาน · `answers/worksheet.md`" ใน `evals/README.md` (5 ขั้น + โควตา 20 ข้อ) + ผังโฟลเดอร์ · checklist ของ Jam เพิ่ม sub-bullet (ไม่ติ๊ก) · ไม่ได้เพิ่มข้อใน checklist ของ May/Junior เอง เพราะเป็นส่วนของเพื่อน ให้เพื่อนเพิ่มเองหลังตกลงในกลุ่ม

## Next step

ข้อ 4: Jam ส่งข้อความในกลุ่ม (ร่างอยู่ในแชท session 2026-10-21) ขอ May หรือ Junior เขียนคำตอบพิมพ์ 20 ข้อ + label 50 ข้อ · ตกลงกันได้แล้วจด "ใคร · ภายในวันไหน" ไว้ใน Decisions แล้ว `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- เฉลยของใบลอก (`evals/handwriting/raw/copy-sheets/copy_sheets_key.md`, gitignored) บอกว่ารูปไหนตั้งใจผิด · คน label ห้ามเปิดดูก่อน label เสร็จ
- `reference` ทุกข้อใน `problems.md` ตรวจด้วย SymPy แล้ว (2026-10-19)
