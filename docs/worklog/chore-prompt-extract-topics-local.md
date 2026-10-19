# ร่าง prompt `extract_topics_local/v1` (A5) + ตรวจ `extract_answer/v1`

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/prompt-extract-topics-local` |
| Checklist item | ร่าง prompt `extract_answer/v1` (มีร่างแล้ว) และ `extract_topics_local/v1` |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🤖 เขียน `prompts/extract_topics_local/v1.md` (A5 · ai-orchestration §2.3.4, §2.3.7): frontmatter ตรงกับ `config/ai.yaml`, ครอบเนื้อหาไฟล์ด้วย `<document>`, กำหนดขนาดหัวข้อให้ตรงกับคู่มือ label P3 (`evals/topics/README.md`), output `{name, pages, prereq_hint}`
- [x] 2. 🤖 ตรวจ `prompts/extract_answer/v1.md` เทียบกับคู่มือ label ลายมือ (`evals/README.md`) แล้วเขียนรายการจุดที่ไม่ตรงกัน · ถ้าต้องแก้ ให้ Jam ตัดสินใจก่อน
- [x] 3. 🤖 Smoke test: ดึงข้อความรายหน้าจาก `sheet-03.pdf` (ใช้ PyMuPDF ชั่วคราว ไม่เพิ่ม dependency) แล้วเติมลงใน prompt เป็นไฟล์ใน scratchpad พร้อมให้ก๊อปไปวาง
- [ ] 4. 🙋 Jam: วาง prompt ที่เติมแล้วลงใน Google AI Studio (Gemini) แล้วส่ง output กลับมาให้ Claude ตรวจ schema กับขนาดหัวข้อ
- [ ] 5. 🤖 ปรับ v1 ตามผล smoke test (ยังเป็น v1 เพราะยังไม่เคยรัน eval จริง) แล้วติ๊ก checklist

## Definition of done

- มี `prompts/extract_topics_local/v1.md` และ frontmatter ตรงกับ `config/ai.yaml` (purpose, `prompt: v1`)
- เนื้อหาไฟล์ของผู้ใช้อยู่ใน `<document>` และ prompt บอกว่าเป็นข้อมูล ไม่ใช่คำสั่ง (prompts/README กฎข้อ 3)
- output ตรงกับ A5 `[{name, pages, prereq_hint}]` และใช้เลขหน้า PDF แบบเดียวกับ `labels.json`
- ตรวจ `extract_answer/v1` แล้ว และ Jam ตัดสินใจเรื่องจุดที่ไม่ตรงกันแล้ว
- smoke test กับไฟล์จริง 1 ไฟล์ได้ JSON ที่ถูก schema
- ติ๊ก checklist ข้อนี้

## Decisions

- 2026-10-19 · ไม่เพิ่ม PyMuPDF ใน `apps/api/pyproject.toml` (ของ Junior) · smoke test ใช้ `uv run --with pymupdf` ชั่วคราว · การ ingest จริงเป็นงานของ Junior ใน S2
- 2026-10-19 · output ของ A5 เป็น object `{"topics": [...], "notes": ""}` ไม่ใช่ array เปล่าแบบที่เขียนใน §2.3.7 · เพื่อให้รูปแบบเหมือน `extract_answer` และมีช่องให้บอกเหตุผลเมื่อไฟล์อ่านไม่ได้ · ตัว list ข้างในยังเป็น `{name, pages, prereq_hint}` ตาม spec · Jam อนุมัติให้แก้ §2.3.7 ใน PR นี้
- 2026-10-19 · ขนาดหัวข้อ, กติกาเลขหน้า (`"start-end"` ตามป้าย `[p.N]`) และสิ่งที่ข้าม ใช้นิยามเดียวกับคู่มือ label P3 · เพื่อให้เทียบกับ `labels.json` ได้ตรงๆ · `prereq_hint` จำกัดไว้ไม่เกิน 3 รายการ
- 2026-10-19 · `prereq_hint` ใส่หัวข้อที่อยู่ในไฟล์อื่นได้ (ใช้ชื่อมาตรฐาน + ศัพท์อังกฤษ) · เพราะ `sheet-02` ต้องใช้ลิมิตและอนุพันธ์จาก `sheet-01` ถ้าห้ามใส่ prerequisite ข้ามไฟล์จะหายหมด · A6 จะจับคู่กับหัวข้อจริงหรือทิ้งไป
- 2026-10-19 · แก้ `extract_answer/v1.md` ในไฟล์เดิม ไม่สร้าง v2 (Jam เลือก) · v1 ยังไม่เคยรัน eval และยังไม่มีใครใช้ จึงไม่มีผลเก่าที่จะเสีย ต่างจากเจตนาของกฎข้อ 1 ใน `prompts/README.md` · เพิ่ม: ข้ามเลขข้อ/ชื่อ/วันที่, ตัดคำเชื่อม, รูปแบบ LaTeX ตามคู่มือ label, ขีดฆ่าบางส่วน, อ่าน 2 คอลัมน์ · ไม่ใช้ `?` แบบคู่มือ เพราะใช้ confidence ต่ำแทน

## Next step

ขั้น 4 (🙋 Jam): วาง `a5_sheet-03.txt` และ `a5_sheet-02.txt` จาก scratchpad ลงใน Google AI Studio (Gemini, temperature 0.2, JSON mode) แล้วส่ง output กลับมาให้ Claude ตรวจ

## Waiting on

ไม่มี

## Notes for next time

- งานที่พักไว้: `chore/handwriting-photos` (PR #11) รอรูปถึง พ. 21 ต.ค.
- PyMuPDF อ่านสมการจาก Equation Editor ของ Word ออกมาเป็นตัวอักษรกระจายทีละบรรทัด (เช่น `lim` / `x` / `→` คนละบรรทัด) · ข้อความภาษาไทยอ่านได้ แต่สระอำแตกเป็น `น ามา` · คำสั่ง render: `uv run --no-project --with pymupdf python -I <scratchpad>/render_a5.py <pdf> prompts/extract_topics_local/v1.md <out.txt> <kind>`
