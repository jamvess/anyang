# P8-lite · ใบเก็บ metrics

ใช้ตอนทำ `compute_importance` ด้วยกันใน S4 (`specs/poc/README.md` P8-lite) · กรอกระหว่างทำ ไม่ใช่ย้อนนึกตอนจบ · ตัวเลขชุดนี้ใช้ใน report P8-lite และ Self-Assessment

Spec: `specs/features/scope/compute-importance.md` (approved 31 ต.ค. · 27 AC) · branch `feat/compute-importance` · PR #113 (เริ่ม 8 พ.ย. 2569 ช่วง solo ของ Jam)

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
| `apps/api/app` (โค้ด) | 166 | 0 | 166 | 100% |
| `apps/api/tests` (test) | 419 | 0 | 419 | 100% |

นับ 8 พ.ย. ก่อน `/code-review` · นับใหม่ตอน PR พร้อม merge ถ้ามี commit เพิ่ม

## 2. รอบ red → green

นับ 1 รอบ = test ชุดหนึ่งแดง แล้วแก้โค้ดจนเขียว · `/implement-feature` จะรายงานจำนวนรอบ · จดทุกรอบ

| # | test ที่แดง (ชื่อหรือกลุ่ม AC) | แดงเพราะ | เขียวหลังแก้อะไร |
|---|---|---|---|
| 1 | AC-19 `test_SM03_unknown_no_past_exam_method_fails_at_config_load` | `no_past_exam_method: str` รับค่าอะไรก็ได้ | `Literal["page_terciles"]` ใน `StarsConfig` |
| 2 | AC-1 ถึง AC-13b, AC-boundary, AC-config, AC-weight-zero-one (18 test) | ยังไม่มี `app/domain/stars.py` | กฎขั้นที่ 2 (มีข้อสอบเก่า) · 11 test ของโหมดไม่มีข้อสอบเก่ายังแดงตามแผน |
| 3 | AC-zero-weight, AC-14 ถึง AC-18, AC-order + test ที่เพิ่มจาก §2 (11 test) | โหมดไม่มีข้อสอบเก่ายังเป็น `NotImplementedError` | กฎขั้นที่ 3 (page terciles) · เขียวครบ 32 test ในรอบแรก ไม่มีรอบแก้ซ้ำ |

## 3. บั๊กที่จับได้ก่อน merge

ทุกครั้งที่เจอว่าโค้ดผิด **หลัง** คิดว่าเสร็จแล้ว (test ทั้งหมดเคยเขียว) · ไม่นับรอบ red → green ปกติในข้อ 2

| # | บั๊ก | จับได้ด้วย (unit test · CI · `/code-review` · คนอ่าน) | แก้ใน commit |
|---|---|---|---|
| 1 | กฎข้อ 6 ให้เหตุผล `พบเฉพาะในข้อสอบที่ไม่ได้ใช้คิดดาว` เมื่อหัวข้อมีแถวใน `appearances` ของ material ใดก็ได้ที่ไม่ถูกนับ รวม material ที่ไม่อยู่ใน `exams` (ควรนับเฉพาะชุดน้ำหนัก 0) | Claude อ่านทวนตอน refactor (หลัง test เขียวครบ) · ไม่มี test จับ เพราะ spec ไม่ได้พูดถึง material ที่ไม่อยู่ใน `exams` | commit implement (แก้ก่อน commit) |

ถ้าเจอว่า **test ผิด** (ไม่ใช่โค้ดผิด) ให้จดแยกด้านล่าง เพราะเป็นตัววัดคุณภาพของ `/spec-to-tests`

| # | test ที่ผิด | ผิดอย่างไร | แก้ spec ด้วยไหม |
|---|---|---|---|
| 1 | | | |

## 4. เวลาที่คนใช้

| ขั้น | ใคร | เริ่ม | จบ | นาที |
|---|---|---|---|---|
| review spec (ทำแล้ว 31 ต.ค. · Jam) | Jam | | | |
| `/spec-to-tests` (รอ Claude) | Claude | 13:47 | 13:50 | 3 |
| review test ด้วยกัน | Jam (8 พ.ย. · Junior, May ดูย้อนหลัง) | 13:52 | 13:56 | 4 |
| `/implement-feature` (รอ Claude + ตอบคำถาม) | Claude | 13:56 | 13:59 | 3 |
| อ่านผล `/code-review` และตัดสินใจ | | | | |
| รวม | | | | |

## 5. สิ่งที่ spec ไม่ชัด

ทุกครั้งที่ Claude หรือคนต้องถามเพราะ spec ไม่ได้บอก · ใช้ปรับ `/spec-feature` และเทมเพลตของ spec

| # | คำถาม | เจอตอนไหน (spec-to-tests · implement · review) | ตัดสินว่า | แก้ spec ใน commit |
|---|---|---|---|---|
| 1 | โหมดไม่มีข้อสอบเก่า: หัวข้อที่ผู้ใช้แก้ดาวเองคงดาวไว้แต่ยังนับอันดับ (§2 ขั้นที่ 3 ข้อ 1–3) ไม่มี AC ทดสอบ | spec-to-tests | เพิ่ม `test_SM03_no_past_exam_keeps_user_stars_and_counts_their_rank` (Jam ok) · §2 เขียนไว้แล้ว ไม่ต้องแก้ spec | ไม่แก้ |
| 2 | AC-17: `signal_r` ของหัวข้อที่ตัดออกหารด้วยหน้าของทุกหัวข้อรวมที่ตัดออกไหม (§2 ขั้นที่ 1 "ของทุกหัวข้อ") | spec-to-tests | รวม (9/21 · Jam ok) | ไม่แก้ |

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
