# Feature: คำนวณดาวความสำคัญของหัวข้อ (`compute_importance`)

| | |
|---|---|
| Area | scope |
| Requirements | SM-03, SM-09 |
| Owner | Jam |
| Reviewer | Junior |
| Status | draft (ใช้เป็นตัวอย่างของ PoC P8-lite) |
| Related system spec | ai-orchestration.md §2.3.4–2.3.5, learning-model.md §2, `config/learning.yaml` → `stars` |

## 1. Context

หลัง AI สกัดหัวข้อและ map ข้อสอบเก่าเข้าหัวข้อแล้ว (ขั้น 5a–5c) code ต้องคำนวณดาว 0–3 ของแต่ละหัวข้อ AI ไม่ได้เป็นคนให้ดาว เพื่อให้ผลทำซ้ำได้ อธิบายได้ และ test ได้ ฟังก์ชันนี้เป็น pure function อยู่ที่ `apps/api/app/domain/stars.py`

## 2. Behavior

ทุกค่าตัวเลขอ่านจาก `config/learning.yaml` → `stars`

1. **ตัดออก:** หัวข้อที่ user หรือ note สั่งตัด (`excluded = true`) ได้ดาว 0
2. **ไม่ทับค่าที่ user แก้:** หัวข้อที่ `importance_source = user` เก็บค่าเดิม ไม่คำนวณใหม่
3. **มีข้อสอบเก่าอย่างน้อย 1 ชุด:**
   - น้ำหนักของข้อสอบชุด e คือ `w_e` = `materials.relevance_weight` (ค่าเริ่มต้น `stars.weight_same_instructor`, หรือ `stars.weight_other_instructor` ถ้า note บอกว่าคนละอาจารย์)
   - หัวข้อ t "ออก" ในชุด e ถ้ามีข้อสอบอย่างน้อย 1 ข้อในชุดนั้นที่ map เข้า t
   - `r_t = Σ w_e × [t ออกใน e] ÷ Σ w_e`
   - ★★★ ถ้า `r_t ≥ stars.three_star_min_r`
   - ★★ ถ้า `0 < r_t < stars.three_star_min_r`
   - ★★ ถ้า `r_t = 0` และ t เป็น prerequisite **โดยตรง** ของหัวข้อที่ได้ ★★★
   - ★ ถ้า `r_t = 0` และไม่เข้าเงื่อนไขข้างบน
4. **ไม่มีข้อสอบเก่าเลย:** ใช้สัดส่วนจำนวนหน้า `p_t` ของหัวข้อ แบ่งเป็น 3 กลุ่มเท่ากัน (tercile) กลุ่มบนได้ ★★★ กลางได้ ★★ ล่างได้ ★ (ยังเป็น open question ดูข้อ 10)
5. **เหตุผล** สร้างจาก template ไม่ใช้ LLM เช่น
   - `ออกในข้อสอบเก่า {n_in} จาก {n_total} ชุด`
   - `เป็นพื้นฐานของ "{topic_name}"`
   - `ไม่พบในข้อสอบเก่า`
   - `ไม่มีข้อสอบเก่า จึงประเมินจากจำนวนหน้าในชีท`
   - `ตัดออกตามที่แจ้ง`
6. เก็บผลลง `topics.importance`, `topics.signal_r`, `topics.importance_reason`

## 3. Inputs and outputs

| | Type | ตัวอย่าง |
|---|---|---|
| Input | `topics: list[TopicIn]` (id, name, prereq_ids, excluded, importance_source, page_count) | `[{id:"t1", prereq_ids:[], excluded:false, importance_source:"computed", page_count:6}]` |
| Input | `exams: list[ExamIn]` (material_id, weight) | `[{material_id:"m1", weight:1.0}, {material_id:"m2", weight:0.5}]` |
| Input | `appearances: set[(topic_id, material_id)]` | `{("t1","m1"), ("t2","m2")}` |
| Input | `cfg: StarsConfig` | จาก `config/learning.yaml` |
| Output | `list[TopicImportance]` (topic_id, importance 0–3, signal_r, reason) | `[{topic_id:"t1", importance:3, signal_r:0.67, reason:"ออกในข้อสอบเก่า 1 จาก 2 ชุด"}]` |

## 4. Acceptance criteria

ใช้ค่า config ปัจจุบัน: `weight_same_instructor = 1.0`, `weight_other_instructor = 0.5`, `three_star_min_r = 0.6`

- **AC-1 (SM-03)** Given ข้อสอบ 2 ชุดของอาจารย์คนเดียวกัน When หัวข้อออกทั้ง 2 ชุด Then r = 1.0 และได้ ★★★
- **AC-2 (SM-03)** Given ข้อสอบ 2 ชุดของอาจารย์คนเดียวกัน When หัวข้อออก 1 ชุด Then r = 0.5 และได้ ★★
- **AC-3 (SM-03)** Given ชุดอาจารย์เรา (w 1.0) + ชุดอาจารย์อื่น (w 0.5) When หัวข้อออกเฉพาะชุดอาจารย์เรา Then r ≈ 0.667 และได้ ★★★
- **AC-4 (SM-03)** Given ชุดเดียวกับ AC-3 When หัวข้อออกเฉพาะชุดอาจารย์อื่น Then r ≈ 0.333 และได้ ★★
- **AC-5 (SM-03)** Given หัวข้อ A ได้ ★★★ และ B เป็น prerequisite โดยตรงของ A When B ไม่เคยออก Then B ได้ ★★ และเหตุผลคือ `เป็นพื้นฐานของ "A"`
- **AC-6 (SM-03)** Given C เป็น prerequisite ของ B (ซึ่ง B เป็น prerequisite ของ A ★★★) When C ไม่เคยออก Then C ได้ ★ (ไม่นับต่อเป็นทอด)
- **AC-7 (SM-03)** Given หัวข้อไม่เคยออกและไม่เป็นพื้นฐานของหัวข้อ ★★★ Then ได้ ★ และเหตุผล `ไม่พบในข้อสอบเก่า`
- **AC-8 (SM-03)** Given หัวข้อ excluded = true Then ได้ 0 ไม่ว่า r จะเท่าไหร่
- **AC-9 (SM-09)** Given importance_source = user Then ค่า importance เดิมไม่เปลี่ยน
- **AC-10 (SM-03)** Given ไม่มีข้อสอบเก่าเลย When มี 6 หัวข้อที่จำนวนหน้าต่างกัน Then 2 หัวข้อหน้ามากสุดได้ ★★★, 2 กลางได้ ★★, 2 น้อยสุดได้ ★ และเหตุผลระบุว่าประเมินจากจำนวนหน้า
- **AC-boundary (SM-03)** r = three_star_min_r − 0.001 → ★★ · r = three_star_min_r → ★★★ · r = three_star_min_r + 0.001 → ★★★
- **AC-config (SM-03)** When เปลี่ยน `three_star_min_r` ใน config fixture Then ผลเปลี่ยนตาม โดยไม่ต้องแก้โค้ด
- **AC-pure** ฟังก์ชันไม่อ่าน DB หรือ network (test ผ่านโดยไม่มี Supabase)

## 5. Data changes

| Table | Column | เพิ่ม / แก้ |
|---|---|---|
| `topics` | `importance smallint`, `signal_r numeric`, `importance_reason text`, `importance_source text check in ('computed','user')` | มีอยู่แล้วใน `0001_init.sql` |
| `materials` | `relevance_weight numeric` | มีอยู่แล้ว |

## 6. API / SSE changes

ไม่มี (เรียกจาก ingestion job ขั้น 5d และหลัง scope edit ที่เปลี่ยน prerequisite)

## 7. AI calls

ไม่มี (ใช้ผลของ A6 merge_topics และ A7 map_questions ที่เก็บใน DB แล้ว)

## 8. Test plan

| Test | ระดับ | ครอบคลุม |
|---|---|---|
| `test_SM03_stars_examples` (parametrize AC-1 ถึง AC-4) | unit | AC-1–4 |
| `test_SM03_direct_prerequisite_gets_two_stars` | unit | AC-5, AC-6 |
| `test_SM03_never_seen_gets_one_star` | unit | AC-7 |
| `test_SM03_excluded_gets_zero` | unit | AC-8 |
| `test_SM09_user_override_kept` | unit | AC-9 |
| `test_SM03_no_past_exam_uses_page_terciles` | unit | AC-10 |
| `test_SM03_three_star_boundary` | unit | AC-boundary |
| `test_SM03_threshold_from_config` | unit | AC-config |

## 9. Out of scope

- การ map ข้อสอบเข้าหัวข้อ (A7) และการหา prerequisite (A6)
- การแสดงดาวใน UI

## 10. Open questions

- กรณีไม่มีข้อสอบเก่า ใช้ tercile ของจำนวนหน้าเหมาะไหม หรือให้ทุกหัวข้อเป็น ★★ แล้วให้ user ปรับเอง (ตัดสินหลัง PoC P3)
- prerequisite นับแค่ชั้นเดียวพอไหม (AC-6)

## 11. Spec changes needed

ไม่มี
