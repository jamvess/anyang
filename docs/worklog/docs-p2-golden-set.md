# Label golden set คำตอบ 50 ข้อ (P2 · D8)

| | |
|---|---|
| Owner | May (แบ่งกับ Junior ถ้าตกลงกัน) |
| Branch | `docs/p2-golden-set` |
| Checklist item | Label golden set คำตอบ 50 ข้อ (D8) (ข้อของ Jam ใน S3 · คน label คือ May หรือ Junior ตาม PR #51) |
| Status | ready for work-done · 2026-10-21 |

## Plan

- [x] 1. 🤖 branch + worklog + draft PR (reviewer Jam เพราะเป็นข้อมูลของ P2)
- [x] 2. 🙋 May ตกลงกับ Junior ในกลุ่มว่าแบ่งข้อไหนใครทำ (หรือ May ทำทั้งหมด)
- [x] 3. 🙋 May label ข้อจากรูป (ans_001–ans_030 หรือส่วนที่ตกลง) ใน `evals/answers/worksheet.md` · เปิดรูปจาก `evals/handwriting/raw/` (gitignored อยู่ในเครื่องแล้ว)
- [x] 4. 🙋 May เขียนคำตอบพิมพ์ ans_031–ans_050 ตามโควตาใน `evals/README.md` "ใบงาน" แล้ว label
- [x] 5. 🤖 รัน `--build` หลังแต่ละช่วง · รายงานเฉพาะข้อที่ผิดกติกาและนับโควตา · **ไม่เสนอ verdict / error_type / บรรทัดที่ผิด**
- [x] 6. 🙋 May แก้ตามที่ `--build` แจ้ง

## Definition of done

- `--build` ผ่าน และได้ `evals/answers/labels.jsonl` ครบ 50 ข้อ (หรือครบส่วนที่ตกลง) · ข้อพิมพ์ครบโควตา
- label โดยคน (ไม่ใช่ Jam และไม่ใช่ AI)

## Done today (2026-10-21)

- เปิด branch + worklog + draft PR #52 · อ่านคู่มือ golden set (`evals/README.md`) และใบงาน
- ยังไม่ได้ label ข้อไหน · `worksheet.md` ยังไม่ถูกแก้

## Decisions

- 2026-10-21 · Claude ไม่ label และไม่เสนอคำตอบ เพราะ golden set ใช้วัด checker ที่เป็น AI · ช่วยแค่รัน script และอธิบาย error ของ script
- 2026-10-21 · ห้ามเปิด `handwriting/raw/copy-sheets/copy_sheets_key.md` จนกว่าจะ label ครบ (`evals/README.md` ข้อ 5)

- 2026-10-21 · ทีม (May + Jam) ตกลงให้ใช้ AI ช่วย label · verdict/error_type/first_wrong_line ทั้ง 50 ข้อ และคำตอบพิมพ์ ans_031–050 ร่างโดย AI นอก session นี้ · writer `w06` = คำตอบพิมพ์ที่ AI เขียน · หมายเหตุอยู่หัวใบงาน · ตอนอ่านผล P2 ต้องคำนึงว่า label อาจเอนไปทางเดียวกับ checker ที่เป็น LLM
- 2026-10-21 · Jam อนุญาตแก้ `handwriting/labels.jsonl` แถว hw_018 บรรทัดสุดท้าย `x=3, x=-1` → `x=3, x=1` ให้ตรงกับรูป (กระทบข้อมูล P1 ด้วย)
- 2026-10-21 · build ครั้งแรกไม่ผ่าน 26 ข้อเพราะใบงานเขียน `first_wrong_line: null` (script ต้องการช่องว่าง) · May ให้แก้เป็นว่าง → ผ่าน 50/50 · โควตาข้อพิมพ์ครบ · test `evals/answers` 32 ผ่าน

## Next step

รัน /work-done

## Waiting on

ไม่มี

## Notes for next time

- May ถามว่าต้อง label เองไหม · อธิบายแล้วว่าต้องเป็นคน เพราะ golden set ใช้วัด checker ที่เป็น AI (และ `handwriting/README.md` บอกว่าจะใช้เฉลยใบลอกตรวจ label ของ May) · ทางเลือกที่เสนอ: แบ่งกับ Junior, ให้ Junior ทำมากกว่าครึ่ง, หรือทำทีละส่วน


- build: `uv run --project apps/api python evals/answers/make_worksheet.py --build` (ทำทีละส่วนได้ · ข้อที่ยังไม่มี verdict ถือว่ายังไม่ label)
- ข้อพิมพ์: `problem_id` P01–P17 ใน `evals/handwriting/problems.md`
