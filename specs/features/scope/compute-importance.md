# Feature: คำนวณดาวความสำคัญของหัวข้อ (`compute_importance`)

| | |
|---|---|
| Area | scope |
| Requirements | SM-03, SM-09 |
| Owner | Jam |
| Reviewer | Junior |
| Status | draft (ใช้เป็นตัวอย่างของ PoC P8-lite) · ปรับตามผล P3 31 ต.ค. 2569 |
| Related system spec | ai-orchestration.md §2.3.4–2.3.5, learning-model.md §2, `config/learning.yaml` → `stars` · สูตรที่ P3 ใช้จริง: `poc/P3/stars.py` (★★★ ตรง label 10/12 · `specs/poc/reports/P3.md`) |

## 1. Context

หลัง AI สกัดหัวข้อและ map ข้อสอบเก่าเข้าหัวข้อแล้ว (ขั้น 5a–5c) code ต้องคำนวณดาว 0–3 ของแต่ละหัวข้อ AI ไม่ได้เป็นคนให้ดาว เพื่อให้ผลทำซ้ำได้ อธิบายได้ และ test ได้ ฟังก์ชันนี้เป็น pure function อยู่ที่ `apps/api/app/domain/stars.py` · ดาวถูกใช้ต่อในหน้าตรวจขอบเขต (S12 · `scope-review.md`), ระดับความยากเป้าของหัวข้อ (learning-model §4) และ `signal_r` ใช้เป็นน้ำหนักของความพร้อม % (PM-03)

## 2. Behavior

ทุกค่าตัวเลขอ่านจาก `config/learning.yaml` → `stars` (`StarsConfig` ใน `app/settings.py`)

**ขั้นที่ 1 · `signal_r` ของทุกหัวข้อ**

- น้ำหนักของข้อสอบชุด e คือ `w_e` = `materials.relevance_weight` (ค่าเริ่มต้น `stars.weight_same_instructor` หรือ `stars.weight_other_instructor` ถ้า note บอกว่าคนละอาจารย์ · ค่ามาจากขั้น 2 ของ flow 2.3)
- หัวข้อ t "ออก" ในชุด e ถ้ามีข้อสอบอย่างน้อย 1 ข้อในชุดนั้นที่ map เข้า t
- `r_t = Σ w_e × [t ออกใน e] ÷ Σ w_e`
- ถ้าไม่มีข้อสอบเก่า หรือ `Σ w_e = 0` (ทุกชุดน้ำหนัก 0) → ถือว่า**ไม่มีข้อสอบเก่า** (ไปขั้นที่ 3) และ `signal_r = null`
- คำนวณ `signal_r` ให้**ทุกหัวข้อ** รวมหัวข้อที่ตัดออกและหัวข้อที่ผู้ใช้แก้ดาวเอง (ความพร้อม % ใช้ค่านี้ · หัวข้อ 0 ดาวถูกกรองทิ้งที่ readiness ด้วย `readiness.exclude_zero_star`)

**ขั้นที่ 2 · ดาว เมื่อมีข้อสอบเก่า** (ตรวจตามลำดับ ข้อแรกที่ตรงคือคำตอบ)

1. **ตัดออก** (`excluded = true`) → ดาว 0 · เหตุผล `ตัดออกตามที่แจ้ง`
2. **ผู้ใช้แก้เอง** (`importance_source = user`) → ดาวและเหตุผลคงค่าเดิม (`current_importance`, `current_reason`) ไม่คำนวณใหม่
3. `r_t ≥ stars.three_star_min_r` → ★★★ · เหตุผล `ออกในข้อสอบเก่า {n_in} จาก {n_total} ชุด`
4. `0 < r_t < stars.three_star_min_r` → ★★ · เหตุผลแบบเดียวกับข้อ 3 (แม้จะเป็นพื้นฐานของหัวข้อ ★★★ ด้วยก็ใช้เหตุผลนี้)
5. `r_t = 0` และ t เป็น prerequisite **โดยตรง** ของหัวข้อที่ได้ ★★★ (ดูนิยามด้านล่าง) → ดาว `stars.prerequisite_of_three_star_gets` · เหตุผล `เป็นพื้นฐานของ "{ชื่อหัวข้อ ★★★}"` · ถ้ามีหลายหัวข้อ ใช้หัวข้อแรกตามลำดับใน input (`order_index`)
6. ไม่เข้าข้อไหนเลย → ★ · เหตุผล `ไม่พบในข้อสอบเก่า`

`{n_in}` = จำนวนชุดที่หัวข้อออก (นับชุด ไม่ถ่วงน้ำหนัก) · `{n_total}` = จำนวนชุดที่น้ำหนัก > 0

**หัวข้อ ★★★ ที่ทำให้ prerequisite ได้ ★★** คือหัวข้อที่ไม่ได้ตัดออก และดาว**สุดท้าย**เป็น 3 ทั้งจากการคำนวณ (ข้อ 3) และจากผู้ใช้แก้เอง (ข้อ 2 · `current_importance = 3`) · นับแค่ prerequisite โดยตรงชั้นเดียว ไม่ต่อเป็นทอด (config: `direct prerequisites only`)

**ขั้นที่ 3 · ดาว เมื่อไม่มีข้อสอบเก่า** (`stars.no_past_exam_method = page_terciles`)

1. ตัดออก → 0 และผู้ใช้แก้เอง → คงค่าเดิม (เหมือนขั้นที่ 2 ข้อ 1–2)
2. หัวข้อที่เหลือรวมกับหัวข้อที่ผู้ใช้แก้เอง (ไม่รวมหัวข้อที่ตัดออก) = n หัวข้อ · เรียงตาม `page_count` จากมากไปน้อย · หัวข้อที่ `page_count` เท่ากันได้อันดับเดียวกัน (อันดับของตัวแรกในกลุ่มที่เท่ากัน · เริ่มที่ 0)
3. อันดับ k: ★★★ ถ้า `k < n/3` · ★★ ถ้า `k < 2n/3` · ★ ถ้าไม่ใช่ · หัวข้อที่ผู้ใช้แก้เองนับอันดับด้วยแต่ไม่เปลี่ยนดาว
4. ไม่ใช้กฎ prerequisite ในโหมดนี้
5. เหตุผล `ไม่มีข้อสอบเก่า จึงประเมินจากจำนวนหน้าในชีท`
6. ค่า `no_past_exam_method` อื่นนอกจาก `page_terciles` → error ตอนเรียกฟังก์ชัน (ไม่เดา)

**ผลลัพธ์** เก็บลง `topics.importance`, `topics.signal_r`, `topics.importance_reason` (ผู้เรียกเป็นคนเขียน DB · ฟังก์ชันนี้ไม่เขียน)

**ผู้เรียก** (ไม่อยู่ใน feature นี้ · §9): ingestion job ขั้น 5d และหลัง scope edit ที่เปลี่ยน prerequisite หรือตัดออก/เอากลับ · ผู้เรียกแปลงข้อมูลจาก DB เป็น input: `excluded` = `topics.status = 'excluded'` · `page_count` = จำนวนหน้าที่ไม่ซ้ำของ chunk ที่ผูกกับหัวข้อ (`topic_chunks` → `chunks.page_from`–`page_to`) · `exams` = `materials` ชนิดข้อสอบเก่ากับ `relevance_weight` · `appearances` = `past_exam_questions.topic_id`

## 3. Inputs and outputs

| | Type | ตัวอย่าง |
|---|---|---|
| Input | `topics: list[TopicIn]` (id, name, prereq_ids, excluded, importance_source, current_importance, current_reason, page_count) · เรียงตาม `order_index` | `[TopicIn(id="t1", name="ลิมิต", prereq_ids=[], excluded=False, importance_source="computed", current_importance=None, current_reason=None, page_count=6)]` |
| Input | `exams: list[ExamIn]` (material_id, weight) | `[ExamIn("m1", 1.0), ExamIn("m2", 0.5)]` |
| Input | `appearances: set[tuple[topic_id, material_id]]` | `{("t1", "m1"), ("t2", "m2")}` |
| Input | `cfg: StarsConfig` | จาก `config/learning.yaml` |
| Output | `list[TopicImportance]` (topic_id, importance 0–3, signal_r: float \| None, reason) · ลำดับเดียวกับ input | `[TopicImportance("t1", 3, 0.667, "ออกในข้อสอบเก่า 1 จาก 2 ชุด")]` |

## 4. Acceptance criteria

ค่าใน config ปัจจุบัน: `weight_same_instructor = 1.0`, `weight_other_instructor = 0.5`, `three_star_min_r = 0.6`, `prerequisite_of_three_star_gets = 2`, `no_past_exam_method = page_terciles` · test อ่านค่าจาก config fixture ไม่ใส่ตัวเลขเอง ยกเว้นน้ำหนักข้อสอบใน fixture ของ input

**มีข้อสอบเก่า**

- **AC-1 (SM-03)** Given ข้อสอบ 2 ชุดน้ำหนัก `weight_same_instructor` When หัวข้อออกทั้ง 2 ชุด Then r = 1.0 · ★★★ · เหตุผล `ออกในข้อสอบเก่า 2 จาก 2 ชุด`
- **AC-2 (SM-03)** Given เหมือน AC-1 When หัวข้อออก 1 ชุด Then r = 0.5 · ★★ · `ออกในข้อสอบเก่า 1 จาก 2 ชุด`
- **AC-3 (SM-03)** Given ชุดน้ำหนัก `weight_same_instructor` + ชุดน้ำหนัก `weight_other_instructor` When หัวข้อออกเฉพาะชุดแรก Then r = 1.0 ÷ 1.5 ≈ 0.667 · ★★★
- **AC-4 (SM-03)** Given เหมือน AC-3 When หัวข้อออกเฉพาะชุดที่สอง Then r ≈ 0.333 · ★★
- **AC-5 (SM-03)** Given หัวข้อ A ★★★ และ B เป็น prerequisite โดยตรงของ A When B ไม่เคยออก Then B ได้ `prerequisite_of_three_star_gets` ดาว · เหตุผล `เป็นพื้นฐานของ "A"`
- **AC-6 (SM-03)** Given C เป็น prerequisite ของ B และ B เป็น prerequisite ของ A ★★★ When B และ C ไม่เคยออก Then B ได้ ★★ และ C ได้ ★ (ไม่นับต่อเป็นทอด)
- **AC-7 (SM-03)** Given หัวข้อไม่เคยออกและไม่เป็นพื้นฐานของหัวข้อ ★★★ Then ★ · `ไม่พบในข้อสอบเก่า` · r = 0
- **AC-8 (SM-03)** Given B เป็น prerequisite ของ A ★★★ When B ออก 1 จาก 2 ชุด Then B ได้ ★★ · เหตุผล `ออกในข้อสอบเก่า 1 จาก 2 ชุด` (ไม่ใช่ `เป็นพื้นฐานของ`)
- **AC-9 (SM-03)** Given B เป็น prerequisite ของ A1 และ A2 ซึ่งได้ ★★★ ทั้งคู่ และ A1 มาก่อนใน input When B ไม่เคยออก Then เหตุผลของ B คือ `เป็นพื้นฐานของ "A1"`

**ตัดออกและผู้ใช้แก้เอง**

- **AC-10 (SM-03)** Given หัวข้อ `excluded = true` ที่ออกทั้ง 2 ชุด Then ดาว 0 · `ตัดออกตามที่แจ้ง` · r = 1.0 (ยังคำนวณ)
- **AC-11 (SM-03)** Given A ออกทั้ง 2 ชุดแต่ `excluded = true` และ B เป็น prerequisite ของ A ที่ไม่เคยออก Then B ได้ ★ (หัวข้อที่ตัดออกไม่นับเป็น ★★★)
- **AC-12 (SM-09)** Given หัวข้อ `importance_source = user`, `current_importance = 1`, `current_reason = "user: อาจารย์ไม่เน้น"` ที่ออกทั้ง 2 ชุด Then ดาว 1 และเหตุผลเดิม · r = 1.0 (คำนวณใหม่)
- **AC-13 (SM-09)** Given A ไม่เคยออกแต่ `importance_source = user`, `current_importance = 3` และ B เป็น prerequisite ของ A ที่ไม่เคยออก Then A คง ★★★ และ B ได้ ★★ · `เป็นพื้นฐานของ "A"`

**ค่าขอบและ config**

- **AC-boundary (SM-03)** Given ข้อสอบ 2 ชุดน้ำหนักเท่ากัน หัวข้อออก 1 ชุด (r = 0.5) When `three_star_min_r` ใน config fixture เป็น 0.5 + ε → ★★ · = 0.5 → ★★★ · 0.5 − ε → ★★★ (ε = 0.001 · ใช้ r = 0.5 เพราะเป็นค่าที่ float แทนได้ตรง)
- **AC-config (SM-03)** When เปลี่ยน `prerequisite_of_three_star_gets` ใน config fixture เป็น 1 Then หัวข้อใน AC-5 ได้ ★ โดยไม่ต้องแก้โค้ด
- **AC-zero-weight (SM-03)** Given ข้อสอบ 2 ชุดน้ำหนัก 0 ทั้งคู่ Then ใช้กฎไม่มีข้อสอบเก่า (AC-14) · `signal_r = null` · ไม่ error หารด้วยศูนย์
- **AC-weight-zero-one (SM-03)** Given ชุดน้ำหนัก 1.0 และชุดน้ำหนัก 0 When หัวข้อออกเฉพาะชุดน้ำหนัก 0 Then r = 0 · `{n_total}` ในเหตุผลของหัวข้ออื่นนับเฉพาะชุดน้ำหนัก > 0

**ไม่มีข้อสอบเก่า**

- **AC-14 (SM-03)** Given ไม่มีข้อสอบเก่า และ 6 หัวข้อที่ `page_count` เป็น 12, 10, 8, 6, 4, 2 Then ★★★, ★★★, ★★, ★★, ★, ★ · เหตุผล `ไม่มีข้อสอบเก่า จึงประเมินจากจำนวนหน้าในชีท` · `signal_r = null` ทุกหัวข้อ
- **AC-15 (SM-03)** Given 7 หัวข้อ `page_count` 7, 6, 5, 4, 3, 2, 1 Then อันดับ 0–2 (k < 7/3) ★★★ · 3–4 (k < 14/3) ★★ · 5–6 ★
- **AC-16 (SM-03)** Given 6 หัวข้อ `page_count` 10, 8, 8, 8, 4, 2 Then 10 → ★★★ · 8 ทั้ง 3 หัวข้อได้อันดับ 1 → ★★★ · 4 (อันดับ 4) → ★ · 2 → ★ · หน้าเท่ากันได้ดาวเท่ากัน
- **AC-17 (SM-03)** Given ไม่มีข้อสอบเก่า, 4 หัวข้อ โดย 1 หัวข้อตัดออก Then หัวข้อที่ตัดออกได้ 0 และไม่นับใน n (n = 3 · อันดับ 0 ★★★, 1 ★★, 2 ★)
- **AC-18 (SM-03)** Given ไม่มีข้อสอบเก่า และ B เป็น prerequisite ของหัวข้อที่ได้ ★★★ จากจำนวนหน้า Then ดาวของ B มาจากอันดับจำนวนหน้าของตัวเอง (ไม่ใช้กฎ prerequisite)
- **AC-19 (SM-03)** Given `no_past_exam_method` ใน config fixture เป็นค่าอื่น และไม่มีข้อสอบเก่า Then ฟังก์ชัน raise error ที่บอกชื่อค่านั้น

**ทั่วไป**

- **AC-order** output มีครบทุกหัวข้อ เรียงเหมือน input · input ว่าง → output ว่าง
- **AC-pure** ฟังก์ชันไม่อ่าน DB, network หรือไฟล์ config เอง (รับ `cfg` เข้ามา) · test ผ่านโดยไม่มี Supabase

## 5. Data changes

ไม่มี · คอลัมน์ที่ใช้มีอยู่แล้วใน `supabase/migrations/0001_init.sql`

| Table | Column | ใช้เป็น |
|---|---|---|
| `topics` | `importance smallint (0–3)`, `signal_r numeric`, `importance_reason text`, `importance_source ('computed','user')`, `prereq_ids uuid[]`, `order_index`, `status ('draft','confirmed','excluded')` | output และ input |
| `materials` | `relevance_weight numeric default 1.0` | น้ำหนักข้อสอบ |
| `past_exam_questions` | `topic_id` | appearances |
| `topic_chunks` → `chunks` | `page_from`, `page_to` | จำนวนหน้าของหัวข้อ (ผู้เรียกนับ) |

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี (ใช้ผลของ A6 `merge_topics` และ A7 `map_questions` ที่เก็บใน DB แล้ว)

## 8. Test plan

ทั้งหมดเป็น unit test ใน `apps/api/tests/unit/test_stars.py` · ใช้ `StarsConfig` จาก `get_settings().learning.stars` แล้ว `model_copy` เมื่อต้องเปลี่ยนค่า

| Test | ครอบคลุม |
|---|---|
| `test_SM03_signal_and_stars_from_past_exams` (parametrize) | AC-1–4 |
| `test_SM03_direct_prerequisite_of_three_star` | AC-5, AC-6 |
| `test_SM03_never_seen_gets_one_star` | AC-7 |
| `test_SM03_seen_prerequisite_keeps_exam_reason` | AC-8 |
| `test_SM03_prerequisite_reason_names_first_three_star_topic` | AC-9 |
| `test_SM03_excluded_gets_zero_but_keeps_signal` | AC-10 |
| `test_SM03_excluded_topic_does_not_lift_its_prerequisites` | AC-11 |
| `test_SM09_user_stars_and_reason_are_kept` | AC-12 |
| `test_SM09_user_three_star_lifts_its_prerequisites` | AC-13 |
| `test_SM03_three_star_boundary` (parametrize −ε, =, +ε) | AC-boundary |
| `test_SM03_prerequisite_stars_from_config` | AC-config |
| `test_SM03_zero_total_weight_means_no_past_exam` | AC-zero-weight |
| `test_SM03_zero_weight_exam_is_not_counted` | AC-weight-zero-one |
| `test_SM03_no_past_exam_page_terciles` (parametrize) | AC-14, AC-15, AC-16 |
| `test_SM03_no_past_exam_skips_excluded` | AC-17 |
| `test_SM03_no_past_exam_ignores_prerequisites` | AC-18 |
| `test_SM03_unknown_no_past_exam_method_is_an_error` | AC-19 |
| `test_SM03_output_keeps_input_order` | AC-order |

AC-pure ตรวจจากการที่ test ทั้งหมดรันได้ใน job `api` ของ CI ซึ่งไม่มี Supabase

## 9. Out of scope

- การ map ข้อสอบเข้าหัวข้อ (A7) และการหา prerequisite (A6)
- การแปลงข้อมูลจาก DB เป็น input และการเขียนผลลง `topics` (ผู้เรียก: ingestion job 5d, scope edit)
- การแสดงดาวใน UI (`scope-review.md`)
- ความพร้อม % (PM-03) และระดับความยากเป้าตามดาว (learning-model §4) ซึ่งใช้ผลของฟังก์ชันนี้

## 10. Open questions

ข้อเสนอจากการเทียบกับ P3 และ config (31 ต.ค.) · **ตัดสินแล้ว 31 ต.ค.: Jam ok ทั้ง 5 ข้อ** (รวมผลของ AC-16 ที่หน้าเท่ากันทำให้มี ★★★ มากกว่า 1/3 ได้)

1. **ไม่มีข้อสอบเก่า:** ใช้ tercile ของจำนวนหน้าต่อใน MVP (P3 ไม่ได้ทดสอบกรณีนี้ เพราะ MTH10101 มีข้อสอบ 2 ชุด) · ผู้ใช้แก้ดาวในหน้า S12 ได้อยู่แล้ว · วิธีแบ่งเมื่อหารไม่ลงตัวและหน้าเท่ากันตาม §2 ขั้นที่ 3 · ไม่ใช้กฎ prerequisite ในโหมดนี้
2. **prerequisite นับชั้นเดียว** (AC-6) · ตรงกับ config และ learning-model §2
3. **ผู้ใช้แก้ดาวเอง:** ดาวและเหตุผลคงเดิม แต่ `signal_r` คำนวณใหม่เพราะความพร้อม % ใช้ (AC-12)
4. **หัวข้อที่ผู้ใช้ตั้ง ★★★ เอง** ทำให้ prerequisite ได้ ★★ ด้วย (AC-13) · ต่างจาก `poc/P3/stars.py` ที่ดูแค่ค่าที่คำนวณ · เหตุผล: ผู้ใช้รู้จักข้อสอบของวิชาดีกว่าข้อสอบเก่า 2 ชุด
5. **ข้อความเหตุผล:** ใช้ `ออกในข้อสอบเก่า {n_in} จาก {n_total} ชุด` ตาม spec เดิมและ P3 · ตัวอย่างใน ai-orchestration §2.3.5 ("2 ใน 2 ชุด") และ scope-review ("ออกทุกชุด") เป็นแค่ตัวอย่าง ไม่แก้

## 11. Spec changes needed

ไม่มีที่ต้องแก้ใน `specs/system/` หรือ `config/` · ข้อ 10.4 เพิ่มรายละเอียดที่ ai-orchestration §2.3.5 ไม่ได้พูดถึง (ไม่ขัดกัน)
