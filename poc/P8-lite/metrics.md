# P8-lite · ใบเก็บ metrics

ใช้ตอนทำ `compute_importance` ด้วยกันใน S4 (`specs/poc/README.md` P8-lite) · กรอกระหว่างทำ ไม่ใช่ย้อนนึกตอนจบ · ตัวเลขชุดนี้ใช้ใน report P8-lite และ Self-Assessment

Spec: `specs/features/scope/compute-importance.md` (approved 31 ต.ค. · 27 AC) · branch และ PR: กรอกตอนเริ่ม

## กติกาก่อนเริ่ม (ไม่งั้นตัวเลขเชื่อไม่ได้)

- **commit ที่ Claude เขียน** ต้องมีบรรทัด `Co-Authored-By: Claude …` ท้ายข้อความ (Claude Code ใส่ให้เอง)
- **ถ้าคนแก้โค้ดเอง** ให้ commit แยก และไม่มีบรรทัดนั้น · ห้ามแก้ไฟล์ที่ Claude เขียนแล้วรวมไปใน commit ของ Claude
- จับเวลาด้วยนาฬิกาจริง (เริ่ม–จบ) ไม่ใช่ประมาณ

## 1. % โค้ดที่ agent เขียน

รันจาก root ของ repo ตอน PR พร้อม merge:

```bash
bash poc/P8-lite/agent_lines.sh origin/main HEAD apps/api/app    # แถวโค้ด
bash poc/P8-lite/agent_lines.sh origin/main HEAD apps/api/tests  # แถว test
```

นับบรรทัดที่เพิ่ม (added) ต่อ commit แล้วแยกตามว่า commit นั้นมีบรรทัด `Co-Authored-By: Claude` ไหม · ไม่นับ merge commit · ไม่นับ spec และ worklog (อยู่นอก `apps/`) · ทดสอบกับ PR #87 ได้ agent 377/377 บรรทัด

| ส่วน | agent | คน | รวม | % agent |
|---|---|---|---|---|
| `apps/api/app` (โค้ด) | | | | |
| `apps/api/tests` (test) | | | | |

## 2. รอบ red → green

นับ 1 รอบ = test ชุดหนึ่งแดง แล้วแก้โค้ดจนเขียว · `/implement-feature` จะรายงานจำนวนรอบ · จดทุกรอบ

| # | test ที่แดง (ชื่อหรือกลุ่ม AC) | แดงเพราะ | เขียวหลังแก้อะไร |
|---|---|---|---|
| 1 | | | |

## 3. บั๊กที่จับได้ก่อน merge

ทุกครั้งที่เจอว่าโค้ดผิด **หลัง** คิดว่าเสร็จแล้ว (test ทั้งหมดเคยเขียว) · ไม่นับรอบ red → green ปกติในข้อ 2

| # | บั๊ก | จับได้ด้วย (unit test · CI · `/code-review` · คนอ่าน) | แก้ใน commit |
|---|---|---|---|
| 1 | | | |

ถ้าเจอว่า **test ผิด** (ไม่ใช่โค้ดผิด) ให้จดแยกด้านล่าง เพราะเป็นตัววัดคุณภาพของ `/spec-to-tests`

| # | test ที่ผิด | ผิดอย่างไร | แก้ spec ด้วยไหม |
|---|---|---|---|
| 1 | | | |

## 4. เวลาที่คนใช้

| ขั้น | ใคร | เริ่ม | จบ | นาที |
|---|---|---|---|---|
| review spec (ทำแล้ว 31 ต.ค. · Jam) | Jam | | | |
| `/spec-to-tests` (รอ Claude) | | | | |
| review test ด้วยกัน | Junior, May, Jam | | | |
| `/implement-feature` (รอ Claude + ตอบคำถาม) | | | | |
| อ่านผล `/code-review` และตัดสินใจ | | | | |
| รวม | | | | |

## 5. สิ่งที่ spec ไม่ชัด

ทุกครั้งที่ Claude หรือคนต้องถามเพราะ spec ไม่ได้บอก · ใช้ปรับ `/spec-feature` และเทมเพลตของ spec

| # | คำถาม | เจอตอนไหน (spec-to-tests · implement · review) | ตัดสินว่า | แก้ spec ใน commit |
|---|---|---|---|---|
| 1 | | | | |

## 6. ผล (กรอกตอนจบ)

| Metric | ค่า |
|---|---|
| merge ได้โดย CI เขียว (เกณฑ์ผ่านของ P8-lite) | |
| % โค้ดที่ agent เขียน (`apps/api/app` · `apps/api/tests`) | |
| จำนวนรอบ red → green | |
| บั๊กที่จับได้ก่อน merge (แยกตามวิธีที่จับได้) | |
| test ที่ผิด | |
| เวลาที่คนใช้รวม (นาที) | |
| จุดที่ spec ไม่ชัด | |
