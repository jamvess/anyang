# รวบรวมรูปลายมือ ≥ 30 รูป + ขอความยินยอม (D8)

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/handwriting-photos` |
| Checklist item | รวบรวมรูปลายมือจากทุกคนให้ได้ ≥ 30 รูป + ขอความยินยอมเพื่อน (D8) |
| Status | paused · 2026-10-19 |

## Done today (2026-10-19)

- เขียนคู่มือเก็บรูป (`README.md`), โจทย์ 17 ข้อที่ตรวจเฉลยด้วย SymPy แล้ว (`problems.md`), ข้อความ consent (`consent.md`)
- เขียน `make_labels.py` + test 9 ตัว (ผ่านหมด)
- เปลี่ยนแผนเป็นให้คนเขียน 5 คนลอกจากใบลอกคนละ 6 ใบ (รวม 30 ใบ มีใบที่ผิด 8 ใบ และใบที่ขีดฆ่า 3 ใบ) · อัปโหลดใบลอกขึ้น Drive แล้ว สร้าง Google Form แล้ว และส่งให้ทุกคนแล้ว

## Plan

- [x] 1. 🤖 `evals/handwriting/README.md`: วิธีถ่ายรูป, การตั้งชื่อไฟล์, เป้าความหลากหลายของชุดรูป, ที่เก็บใน Drive, ขั้นตอนขอความยินยอม
- [x] 2. 🤖 `evals/handwriting/problems.md`: โจทย์ ~15 ข้อจาก MTH10101 (limit, อนุพันธ์, chain rule, implicit, แยกตัวประกอบ, สมการ) ครอบคลุม `answer_format` ทั้ง 3 แบบ เพื่อให้ P2 นำไปใช้ต่อได้
- [x] 3. 🤖 `evals/handwriting/consent.md`: ข้อความขอความยินยอมสำหรับทำ Google Form + template ตารางรหัสคนเขียน (เก็บใน Drive เท่านั้น)
- [x] 4. 🤖 `evals/handwriting/make_labels.py` (stdlib อย่างเดียว): อ่าน `photos.csv` + `raw/` แล้วสร้าง `labels.jsonl` แบบโครง (`lines` ว่างไว้ให้ May) เช็คไฟล์ที่ขาดหรือซ้ำ และสรุปความหลากหลายของชุดรูป
- [x] 5. 🙋 Jam: อัปโหลดใบลอก + เฉลยขึ้น Drive, สร้างโฟลเดอร์ `inbox`/`raw` + Google Form แล้วส่งใบลอกให้คนเขียน 5 คน (Jam, Junior, May, เพื่อน 2 คน) คนละ 6 รูป
- [ ] 6. 🙋 Jam: เก็บรูปให้ได้ ≥ 30 รูป เปลี่ยนชื่อเป็น `hw_001.jpg` … กรอกตารางรหัสใน Drive และ `photos.csv` แล้วก๊อปรูปลง `evals/handwriting/raw/`
- [ ] 7. 🤖 รัน `make_labels.py` แล้ว commit `labels.jsonl` แบบโครง เช็คว่าครบตามเป้า ติ๊ก checklist และเขียนข้อความส่งงานให้ May

## Definition of done

- มีรูปลายมือ ≥ 30 รูป ทั้งใน Drive ทีม และใน `evals/handwriting/raw/` บนเครื่อง
- คนเขียนทุกคนมีหลักฐานการให้ความยินยอมเก็บอยู่ใน Drive
- มี `evals/handwriting/labels.jsonl` แบบโครง 1 บรรทัดต่อ 1 รูป (มี `id`, `image`, `writer`, `problem`) ให้ May พิมพ์ `lines` ต่อได้
- ใน git ไม่มีรูปและไม่มีชื่อจริงของคนเขียน
- ติ๊ก checklist ข้อนี้ใน `docs/team/sprint-checklists.md`

## Decisions

- 2026-10-19 · เขียนวิธีเก็บรูปไว้ในไฟล์ใหม่ `evals/handwriting/README.md` ไม่แก้ `evals/README.md` · เพราะ PR #10 ยังแก้ไฟล์นั้นอยู่ ถ้าแก้ทั้งสองที่จะ conflict
- 2026-10-19 · เป้าชุดรูป: ≥ 30 รูป, ≥ 5 คนเขียน, ≤ 10 รูปต่อคน, แต่ละ answer_format ≥ 5, มีบรรทัดผิด ≥ 8, มีขีดฆ่า ≥ 3 · เพื่อให้ P2 ใช้รูปชุดเดียวกันได้และไม่มีลายมือคนใดมีน้ำหนักมากเกินไป
- 2026-10-19 · ใช้ `photos.csv` (มีแค่รหัส) เป็นที่จดว่ารูปไหนใครเขียน ส่วนตารางที่จับคู่รหัสกับชื่อจริงอยู่ใน Drive
- 2026-10-19 · โจทย์ 17 ข้อ แบ่ง 3 หมวด (ก factored 4 ข้อ, ข expression 10 ข้อ, ค equation 3 ข้อ) · ให้คนเขียนทำอย่างน้อยหมวดละ 1 ข้อ · ถ้าคนเขียน ≥ 5 คน ทุก answer_format จะมี ≥ 5 รูปได้โดยไม่ต้องคุมรายคน
- 2026-10-19 · ถ้ารูปที่มีบรรทัดผิดยังไม่ถึง 8 รูป Jam เขียนคำตอบผิดเพิ่มเองโดยไม่จด error type ที่ตั้งใจไว้ · เพื่อให้ May label error type แบบไม่รู้คำตอบล่วงหน้า
- 2026-10-19 · consent บอกชัดว่าส่งรูปให้ Gemini, Claude, Mathpix ผ่าน API · เก็บถึง 31 พ.ค. 2570 · ถอนได้ (ลบใน 7 วัน) · ขออนุญาตแยกถ้าจะใส่รูปในรายงาน · ไม่รับรูปจากคนอายุต่ำกว่า 18 ปี (PDPA)
- 2026-10-19 · `make_labels.py` ใช้ stdlib อย่างเดียว รันผ่าน `uv run --project apps/api` · test อยู่ข้างๆ กัน (`evals/handwriting/test_make_labels.py`) แต่ CI ยังไม่รัน เพราะ CI รันแค่ `apps/api/tests`
- 2026-10-19 · เพื่อนนอกทีมทำโจทย์เลขไม่เป็น จึงเปลี่ยนให้**ลอก**วิธีทำจากใบลอกแทน (5 คน × 4 รูป) ส่วน Junior กับ May ทำโจทย์เอง (2 × 10) · ใบลอกตั้งใจให้มีบรรทัดผิด 8 ใบ (ครอบคลุม error type 5 แบบ) และมีการขีดฆ่า 3 ใบ · ข้อดีคือรูปที่ผิดมาจากลายมือหลายคน · ใบลอกและเฉลยเก็บใน Drive เท่านั้น เพื่อให้ May label แบบไม่รู้คำตอบล่วงหน้า · ทุกบรรทัดตรวจด้วย SymPy แล้ว
- 2026-10-19 · ลบตาราง "คำตอบผิดที่พบบ่อย" ออกจาก `problems.md` · เพราะเฉลยของใบลอกไม่ควรอยู่ใน repo
- 2026-10-19 · (แทนที่ 2 ข้อก่อนหน้าเรื่องจำนวนคนและใครเขียนอะไร) คนเขียนมีแค่ 5 คน (Jam, Junior, May + เพื่อน 2 คน) จึงเปลี่ยนแผนเป็นลอกคนละ 6 ใบ รวม 30 ใบ แทนแผนเดิม (เพื่อน 5 × 4 + ทีมทำเอง 2 × 10) · ใบลอกของ May เป็นฉบับถูกทั้งหมด เพราะ May เป็นคน label · ใบที่ผิด 8 ใบ แบ่งให้ Jam, Junior, เพื่อน 1, เพื่อน 2 คนละ 2 ใบ · ครบทั้ง 17 ข้อ (factored 7, expression 17, equation 6) · ใช้ดินสอ 12 ใบ (เพื่อน 2 และ May)
- 2026-10-19 · ได้รูปครบ 30 รูป · ทุกคนยินยอมผ่าน Form แล้ว (Jam ยืนยัน) · รหัส: w01 Jam, w02 Junior, w03 เพื่อน 1, w04 เพื่อน 2, w05 May (Jam ต้องจดลงแท็บ `writers` ใน Sheet ให้ตรงกัน) · Claude เปิดดูทุกรูปแล้ว: เลขข้อและฉบับ (ถูก/ผิด/ขีดฆ่า) ตรงกับใบลอกครบ 30/30
- 2026-10-19 · **ไม่มีใครเขียนบนกระดาษ** · เพื่อน 1, เพื่อน 2, May เขียนบน iPad แล้วแคปหน้าจอ (มีแถบเครื่องมือ ชื่อแท็บ และเวลาติดมา) · Junior เขียนบน tablet แล้ว crop มาแล้ว (ไฟล์ JPEG ~950 px ที่ตั้งชื่อเป็น `.PNG`) · Jam ใช้มือถือถ่ายหน้าจอ tablet (มี moiré และเงาสะท้อน) · (Jam เลือก) ใช้ชุดนี้เป็นกลุ่ม tablet · เพิ่มคอลัมน์ `medium` (`tablet_screenshot` / `screen_photo` / `paper`) และ `tool=stylus` · ใน report P1 ต้องเขียนว่ายังไม่ได้วัดกับรูปถ่ายกระดาษจริง ถ้ามีเวลาให้เก็บรูปกระดาษเพิ่มประมาณ 10 รูป
- 2026-10-19 · `crop_screenshots.py`: crop ภาพแคปหน้าจอให้เหลือแค่ลายมือในกรอบหน้ากระดาษของแต่ละเครื่อง (`PAGE_AREA` วัดจากภาพจริง) + ขอบ 40 px · ลองหาหน้ากระดาษอัตโนมัติก่อนแล้วแต่พังกับภาพของ May (ครึ่งล่างของหน้าจอเป็นสีขาว) จึงใช้กรอบตายตัว · ตรวจผลทั้ง 18 รูปด้วยตาแล้ว · ภาพของ Jam กับ Junior ไม่ crop
- 2026-10-19 · ไฟล์ `raw/hw_001`–`hw_030` (เรียงตามรหัสคนเขียน แล้วตามลำดับในใบลอก) · `photos.csv` ครบ 30 แถว · กรอก `hw_id` + รหัสลงในเฉลยในเครื่องแล้ว (`raw/copy-sheets/copy_sheets_key.md`) · ต้นฉบับยังอยู่ใน `raw/inbox/`
- 2026-10-19 · test ใหม่ของ `make_labels.py` 3 ตัว (stylus + medium) ต่อท้ายไฟล์ ยัง red · รอ Jam review

## Next step

ขั้น 6 ที่เหลือ: หลัง Jam review test ใหม่ ให้แก้ `make_labels.py` (`TOOLS` เพิ่ม `stylus` · คอลัมน์ `medium` ไม่บังคับ ค่าที่ใช้ได้ `paper`/`tablet_screenshot`/`screen_photo` · สรุปนับตาม medium) แล้วอัปเดต README (หัวข้อ photos.csv + การ crop) → ขั้น 7: รัน `make_labels.py` แล้ว commit `labels.jsonl`

## Waiting on

Jam review test ใหม่ของ `make_labels.py` · Jam อัปโหลดรูป `raw/hw_*` ขึ้น Drive `evals/handwriting/raw/` (May ต้องใช้รูปตอนพิมพ์เฉลย)

## Notes for next time

- 2026-10-19 (session 2) · ไฟล์ PDF ของ P3 ถูกย้ายมาอยู่ใน `evals/handwriting/raw/` ผิดที่ จึงย้ายกลับไป `evals/topics/mth10101/raw/` แล้ว · สร้าง `evals/handwriting/raw/inbox/{jam,junior,may,friend1,friend2}/` ไว้รอรูป · ระหว่างรอรูปไปทำงานอื่นก่อน

- กติกาการ label ลายมือ (LaTeX รายบรรทัด, `writer` เป็นรหัส) อยู่ใน `evals/README.md` ของ PR #10 (`docs/label-guide`)
- โจทย์ต้องไม่มาจากข้อสอบกลางภาค 2562/1 เพราะเป็นชุด held-out ของ P3
- ใบลอก (`copy_sheets.html`) และ script ที่ใช้สร้าง (`build_sheets.py`) อยู่ใน Drive `evals/handwriting/` · เฉลย `copy_sheets_key.md` อยู่ใน Drive ส่วนตัวของ Jam · ถ้าจะแก้ใบลอก ให้แก้ `build_sheets.py` แล้วรัน `python -I build_sheets.py <โฟลเดอร์ output>` · ห้าม commit ไฟล์ทั้ง 3 ไฟล์นี้
- การแบ่งใบลอก: Jam (P01✗ P05✗ P07 P12 P16 P03) · Junior (P08✗ P15✗ P02 P11✂ P14 P17) · เพื่อน 1 (P09✗ P10✗ P04 P06 P13 P15) · เพื่อน 2 ดินสอ (P13✗ P14✗ P01 P08 P16 P05) · May ดินสอ (P04✂ P06✂ P02 P09 P10 P17) · ✗ = ตั้งใจให้ผิด ✂ = มีบรรทัดที่ต้องขีดฆ่า · เวลากรอก `photos.csv` คอลัมน์ `tool` ให้ดูจากตารางนี้
- คำสั่ง test: `uv run --project apps/api pytest evals/handwriting` · lint: `uv run --project apps/api ruff check evals/handwriting`
- console ของ Windows ใช้ cp874 ถ้า `print` ตัวอักษรอย่าง `·` ใน script จะ crash ด้วย `UnicodeEncodeError` · ข้อความที่ script พิมพ์ออกมาจึงใช้แค่ ASCII
