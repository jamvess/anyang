# ร่าง prompt `extract_topics_local/v1` (A5) + ตรวจ `extract_answer/v1`

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/prompt-extract-topics-local` |
| Checklist item | ร่าง prompt `extract_answer/v1` (มีร่างแล้ว) และ `extract_topics_local/v1` |
| Status | ready for review · 2026-10-19 |

## Plan

- [x] 1. 🤖 เขียน `prompts/extract_topics_local/v1.md` (A5 · ai-orchestration §2.3.4, §2.3.7): frontmatter ตรงกับ `config/ai.yaml`, ครอบเนื้อหาไฟล์ด้วย `<document>`, กำหนดขนาดหัวข้อให้ตรงกับคู่มือ label P3 (`evals/topics/README.md`), output `{name, pages, prereq_hint}`
- [x] 2. 🤖 ตรวจ `prompts/extract_answer/v1.md` เทียบกับคู่มือ label ลายมือ (`evals/README.md`) แล้วเขียนรายการจุดที่ไม่ตรงกัน · ถ้าต้องแก้ ให้ Jam ตัดสินใจก่อน
- [x] 3. 🤖 Smoke test: ดึงข้อความรายหน้าจาก `sheet-03.pdf` (ใช้ PyMuPDF ชั่วคราว ไม่เพิ่ม dependency) แล้วเติมลงใน prompt เป็นไฟล์ใน scratchpad พร้อมให้ก๊อปไปวาง
- [x] 4. 🙋 Jam: วาง prompt ที่เติมแล้วลงใน Google AI Studio (Gemini) แล้วส่ง output กลับมาให้ Claude ตรวจ schema กับขนาดหัวข้อ
- [x] 5. 🤖 ปรับ v1 ตามผล smoke test (ยังเป็น v1 เพราะยังไม่เคยรัน eval จริง) แล้วติ๊ก checklist

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
- 2026-10-19 · แก้ `extract_answer/v1.md` ในไฟล์เดิม ไม่สร้าง v2 (Jam เลือก) · v1 ยังไม่เคยรัน eval และยังไม่มีใครใช้ จึงไม่มีผลเก่าที่จะเสีย ต่างจากเจตนาของกฎข้อ 1 ใน `prompts/README.md` · เพิ่ม: ข้ามเลขข้อ/ชื่อ/วันที่, ตัดคำเชื่อม, รูปแบบ LaTeX ตามคู่มือ label, ขีดฆ่าบางส่วน, อ่าน 2 คอลัมน์ · ไม่ใช้ `\?` แบบคู่มือ เพราะใช้ confidence ต่ำแทน
- 2026-10-19 · smoke test ใน AI Studio (Gemini 3.8 Flash, thinking Low, ปิด grounding, ไม่ใช้ structured output): sheet-03 ได้ 9 หัวข้อ, sheet-02 ได้ 5 หัวข้อ · JSON ถูก schema ทั้ง 2 ไฟล์ · หัวข้อของ sheet-02 ตรงกับหัวข้อที่พิมพ์อยู่ในชีททุกหัวข้อ และซ่อมสระไทยที่แตกได้ · จึงปรับ v1 3 จุด (แก้ในไฟล์เดิมด้วยเหตุผลเดียวกับ extract_answer): ห้ามนับหน้าเฉลยเข้าไปในช่วงหน้า (sheet-02 นับหน้า 23 เข้าไป), ใส่ศัพท์อังกฤษมาตรฐานเสมอ, เทคนิคที่มีแค่ 1–2 ข้อให้รวมไว้ในหัวข้อที่ใช้ (sheet-03 แยก Squeeze เป็นหัวข้อของตัวเอง)
- 2026-10-19 · ตัวอย่างใน prompt ห้ามใช้เนื้อหาจาก MTH10101 · เพราะเป็นข้อมูลที่ใช้วัดผล P3 ถ้าใส่ไว้จะเหมือนบอกใบ้ prompt
- 2026-10-19 · ยังไม่แก้ `max_tokens` ของ `extract_topics_local` ใน `config/ai.yaml` (ไฟล์ shared) · ประมาณว่า 0.4 token ต่อตัวอักษร (sheet-03 ทั้งแชทใช้ 2,915 tokens) ดังนั้น sheet-01 (140 หน้า) น่าจะได้ 2,000–2,500 tokens เกินค่า 2000 เล็กน้อย · ให้ดูผลจริงใน P3 แล้วเพิ่มเป็น 4000 ใน PR อัปเดต config ของ S2

## Next step

ทุกขั้นเสร็จแล้ว · พิมพ์ `/work-done` เพื่อปิดงานและขอ review

## Waiting on

ไม่มี

## Notes for next time

- งานที่พักไว้: `chore/handwriting-photos` (PR #11) รอรูปถึง พ. 21 ต.ค.
- ต้องแจ้ง Junior (ingest P3): PyMuPDF ทำสัญลักษณ์ ∞ หายหมด (`x → −∞` ออกมาเป็น `x →−`) และ `f⁽⁵⁾(x)` ออกมาเหลือ `5` · สมการ Equation Editor กระจายออกมาบรรทัดละตัว (เช่น `lim` / `x` / `→` คนละบรรทัด) · ข้อความภาษาไทยอ่านได้ แต่สระอำแตกเป็น `น ามา`
- คำสั่ง render prompt สำหรับ smoke test: `uv run --no-project --with pymupdf python -I <scratchpad>/render_a5.py <pdf> prompts/extract_topics_local/v1.md <out.txt> <kind>` (script อยู่ใน scratchpad ของ session 2026-10-19 ไม่ได้ commit)
