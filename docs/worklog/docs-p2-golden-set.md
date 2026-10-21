# Label golden set คำตอบ 50 ข้อ (P2 · D8)

| | |
|---|---|
| Owner | May (แบ่งกับ Junior ถ้าตกลงกัน) |
| Branch | `docs/p2-golden-set` |
| Checklist item | Label golden set คำตอบ 50 ข้อ (D8) (ข้อของ Jam ใน S3 · คน label คือ May หรือ Junior ตาม PR #51) |
| Status | paused · 2026-10-21 |

## Plan

- [x] 1. 🤖 branch + worklog + draft PR (reviewer Jam เพราะเป็นข้อมูลของ P2)
- [ ] 2. 🙋 May ตกลงกับ Junior ในกลุ่มว่าแบ่งข้อไหนใครทำ (หรือ May ทำทั้งหมด)
- [ ] 3. 🙋 May label ข้อจากรูป (ans_001–ans_030 หรือส่วนที่ตกลง) ใน `evals/answers/worksheet.md` · เปิดรูปจาก `evals/handwriting/raw/` (gitignored อยู่ในเครื่องแล้ว)
- [ ] 4. 🙋 May เขียนคำตอบพิมพ์ ans_031–ans_050 ตามโควตาใน `evals/README.md` "ใบงาน" แล้ว label
- [ ] 5. 🤖 รัน `--build` หลังแต่ละช่วง · รายงานเฉพาะข้อที่ผิดกติกาและนับโควตา · **ไม่เสนอ verdict / error_type / บรรทัดที่ผิด**
- [ ] 6. 🙋 May แก้ตามที่ `--build` แจ้ง

## Definition of done

- `--build` ผ่าน และได้ `evals/answers/labels.jsonl` ครบ 50 ข้อ (หรือครบส่วนที่ตกลง) · ข้อพิมพ์ครบโควตา
- label โดยคน (ไม่ใช่ Jam และไม่ใช่ AI)

## Done today (2026-10-21)

- เปิด branch + worklog + draft PR #52 · อ่านคู่มือ golden set (`evals/README.md`) และใบงาน
- ยังไม่ได้ label ข้อไหน · `worksheet.md` ยังไม่ถูกแก้

## Decisions

- 2026-10-21 · Claude ไม่ label และไม่เสนอคำตอบ เพราะ golden set ใช้วัด checker ที่เป็น AI · ช่วยแค่รัน script และอธิบาย error ของ script
- 2026-10-21 · ห้ามเปิด `handwriting/raw/copy-sheets/copy_sheets_key.md` จนกว่าจะ label ครบ (`evals/README.md` ข้อ 5)

## Next step

ถาม May ว่า Junior ตอบเรื่องแบ่งงานแล้วหรือยัง → จดผลใน Decisions · จากนั้น May เริ่ม label ข้อจากรูป `ans_001` ใน `evals/answers/worksheet.md` (เปิด `evals/handwriting/raw/hw_001.jpg` คู่กัน) · พอ May พิมพ์ "เช็ก" ให้รัน build แล้วรายงานเฉพาะข้อที่ผิดกติกา

## Waiting on

🙋 May ส่งข้อความถึง Junior ในกลุ่มเรื่องแบ่งงาน (ข้อเสนอ: May รูป ans_001–030 · Junior ข้อพิมพ์ ans_031–050) แล้วรอคำตอบ

## Notes for next time

- May ถามว่าต้อง label เองไหม · อธิบายแล้วว่าต้องเป็นคน เพราะ golden set ใช้วัด checker ที่เป็น AI (และ `handwriting/README.md` บอกว่าจะใช้เฉลยใบลอกตรวจ label ของ May) · ทางเลือกที่เสนอ: แบ่งกับ Junior, ให้ Junior ทำมากกว่าครึ่ง, หรือทำทีละส่วน


- build: `uv run --project apps/api python evals/answers/make_worksheet.py --build` (ทำทีละส่วนได้ · ข้อที่ยังไม่มี verdict ถือว่ายังไม่ label)
- ข้อพิมพ์: `problem_id` P01–P17 ใน `evals/handwriting/problems.md`
