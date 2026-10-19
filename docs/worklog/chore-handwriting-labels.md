# พิมพ์เฉลย LaTeX รายบรรทัดของรูปลายมือ 30 รูป (P1)

| | |
|---|---|
| Owner | May |
| Branch | `chore/handwriting-labels` |
| Checklist item | พิมพ์เฉลย LaTeX รายบรรทัดของรูปลายมือทุกรูป ลง `evals/handwriting/labels.jsonl` (ให้ P1) |
| Status | in progress · 2026-10-19 |

## Plan

คู่มือ: `evals/README.md` หัวข้อ "คู่มือ label ลายมือ · P1" (กติกา 7 ข้อ + ตารางรูปแบบ LaTeX)

**กฎสำคัญ:** ห้ามใช้ AI อ่านรูป (ทั้ง Claude, Gemini, ChatGPT) เพราะ P1 วัดว่า AI อ่านลายมือแม่นแค่ไหน · Claude ไม่เปิดดูรูปเลย ช่วยได้แค่ทำไฟล์ให้กรอก ตรวจ syntax และแปลง JSONL · ห้ามเปิดเฉลยใบลอกใน Drive (ใช้ตรวจ label ทีหลัง)

- [x] 1. 🙋 May โหลดโฟลเดอร์ `raw/` จาก Drive ทีม `evals/handwriting/raw/` มาไว้ที่ `evals/handwriting/raw/` ในเครื่อง (30 ไฟล์ `hw_001`–`hw_030`) · 2026-10-19 ครบ 30 (001–012 .jpg, 013–030 .png) path ใน labels.jsonl ตรงทุกแถว
- [x] 2. 🤖 สร้างไฟล์ร่าง `evals/handwriting/labels-draft.md` (1 หัวข้อต่อรูป · พิมพ์ 1 บรรทัดต่อ 1 บรรทัดในรูป) + script ทำหน้า preview (รูปคู่กับ LaTeX ที่ render แล้ว) ไว้ใน `raw/` ซึ่งไม่ขึ้น git · 2026-10-19 `raw/preview.py` → `raw/preview.html` (KaTeX จาก CDN, render ไม่ได้ขึ้นสีแดง)
- [x] 3. 🙋 ~~May พิมพ์ LaTeX ทีละรูป~~ → Claude เติมจากใบลอกแล้ว (ดู Decisions) · May เปิด preview เทียบกับรูปอีกรอบ · 2026-10-19 May เช็คครบ 30 รูป ok · ไม่มี unclear_lines · พักเมื่อไหร่บอก "พัก" Claude ตรวจและ commit ให้
- [x] 4. 🤖 ตรวจทุกบรรทัด: KaTeX render ได้ · SymPy parse ได้ (ยกเว้นบรรทัดใน `unclear_lines`) · ไม่มี `$` · ไม่มีรูปที่ว่าง · บอกจุดที่ผิดรูปแบบให้ May แก้เอง · 2026-10-19 125 บรรทัด: KaTeX error 0, SymPy parse fail 0 (ตัด `=` ต้นบรรทัด และแยกที่ `,` ก่อน parse)
- [ ] 5. 🤖 แปลงร่างเป็น `labels.jsonl` (ไม่แก้เนื้อหา · `labeled_by: "May"`) แล้วลบร่าง

## Definition of done

- `evals/handwriting/labels.jsonl` ครบ 30 แถว ทุกแถวมี `lines` ไม่ว่าง และ `labeled_by: "May"`
- ทุกบรรทัด KaTeX render ได้ และ SymPy parse ได้ (ยกเว้นใน `unclear_lines`)
- Junior review PR (คน label ไม่ใช่คนทำ PoC) · แจ้ง Jam ว่าพร้อมรัน P1

## Decisions

- 2026-10-19 · ใช้ type `chore` · เป็นงาน label ข้อมูล
- 2026-10-19 · **เปลี่ยนวิธี (Jam ยืนยันแล้ว):** May เช็คด้วยตาแล้วว่าทั้ง 30 รูปลอกตรงกับใบลอกเป๊ะ จึงใช้ใบลอก (PDF ที่ May ให้) เป็นแหล่งของ `lines` · Claude พิมพ์ LaTeX จากใบลอก ไม่ได้เปิดดูรูป · ตัดบรรทัดที่ใบลอกให้ขีดฆ่า 3 บรรทัด (hw_010 P11, hw_025 P04, hw_026 P06) · จับคู่ w01–w05 กับหน้าใบลอกจากลำดับเลขข้อใน `photos.csv` (ไม่ใช้ชื่อ) · ข้อจำกัดที่ต้องเขียนใน report P1: label ไม่ได้อิสระจากใบลอก จึงใช้ใบลอกตรวจ label ไม่ได้แล้ว
- 2026-10-19 · May เห็นใบลอกที่ตั้งใจให้ผิดแล้ว · แจ้ง Jam ให้ตัดสินเรื่องคน label error type ของ P2 (S3)
- 2026-10-19 · ใช้ไฟล์ร่าง Markdown แทนการพิมพ์ JSON ตรง · ไม่ต้องพิมพ์ `\` ซ้อน และเหมือนตอนทำ label P3
- 2026-10-19 · ตรวจ SymPy ด้วย `uv run --with antlr4-python3-runtime==4.11` ชั่วคราว · ไม่เพิ่ม dependency ใน `apps/api`

## Next step

Claude ทำขั้น 5: แปลงร่างเป็น labels.jsonl

## Waiting on

ไม่มี

## Notes for next time

- `evals/` เป็นโฟลเดอร์ของ Jam แต่ `labels.jsonl` เป็นงานของ May ตามคู่มือ
- รูปทั้ง 30 รูปเขียนบน tablet (ดู `evals/handwriting/README.md` "สิ่งที่ได้จริง")
