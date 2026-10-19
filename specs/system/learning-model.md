# Learning model · สูตรและที่มาของตัวเลข (v1.1)

ไฟล์นี้อธิบายทุกการคำนวณที่เกี่ยวกับการเรียนรู้ของผู้ใช้ ตัวเลขทุกตัวอยู่ใน `config/learning.yaml` ที่เดียว และแต่ละตัวมีที่มาเป็นหนึ่งใน 4 แบบ

| ป้าย | ความหมาย |
|---|---|
| **[A]** | มีงานวิจัยรองรับ (ดู References) |
| **[B]** | มาตรฐานวิศวกรรมหรือค่า default ของ library ที่ใช้กันทั่วไป |
| **[calc]** | คำนวณได้จากค่าอื่นหรือจากสูตร |
| **[C]** | ค่าเริ่มต้นชั่วคราว ต้อง calibrate จากข้อมูลของเรา ระบุว่าวัดยังไงและเมื่อไหร่ |

> **สถานะ:** อาจารย์แนะนำให้การออกแบบ learning path และการ tracking progress มีงานวิจัยรองรับมากขึ้น หัวข้อ §10 เป็นรายการที่ทีมจะลงรายละเอียดต่อ ไฟล์นี้จะอัปเดตตามผลการคุยนั้น

---

## 1. Mastery: Bayesian Knowledge Tracing (BKT)

ใช้ BKT (Corbett & Anderson, 1995) ประเมินความน่าจะเป็นที่ผู้เรียนเข้าใจหัวข้อแล้ว อัปเดตหลังทุก attempt ที่ `independent = true`

**สูตรอัปเดต** (p = mastery ก่อนตอบ)

```
ถ้าตอบถูก:  p' = p(1 − slip) / [ p(1 − slip) + (1 − p)·guess ]
ถ้าตอบผิด:  p' = p·slip / [ p·slip + (1 − p)(1 − guess) ]
หลังเรียนรู้:  p_next = p' + (1 − p')·transit
```

| Parameter | ค่า | ป้าย | ที่มา / วิธี calibrate |
|---|---|---|---|
| p_guess | 0.2 | [A] | ต้องไม่เกิน 0.3 ตามขอบที่ Corbett & Anderson (1995) ใช้กันโมเดลเพี้ยน (degenerate model) |
| p_slip | 0.1 | [A] | ต้องไม่เกิน 0.1 ตามขอบเดียวกัน |
| p_init | 0.3 | [C] | ไม่มีค่ากลาง ขึ้นกับ skill · หลัง Alpha fit ราย skill ด้วย pyBKT (EM) จากตาราง `attempts` |
| p_transit | 0.15 | [C] | เหมือน p_init |
| mastery_threshold | **0.95** | [A] | เกณฑ์ที่ระบบ BKT แทบทุกระบบใช้ (Slater & Baker) |
| weak_below | 0.5 | [calc] | จุดที่ "ยังไม่เข้าใจ" มีโอกาสมากกว่า "เข้าใจแล้ว" |

**ตัวอย่างการคำนวณ** (ค่าปัจจุบัน)

| ลำดับ | ตอบถูกทุกข้อ | หมายเหตุ |
|---|---|---|
| เริ่ม | 0.30 | p_init |
| ถูกข้อ 1 | 0.71 | |
| ถูกข้อ 2 | 0.93 | ยังไม่ถึง 0.95 |
| ถูกข้อ 3 | 0.986 | **ผ่าน** · ตรงกับเกณฑ์ "ถูก 3 ข้อติด" ของ ASSISTments Skill Builder |

ถ้าเริ่มแล้วตอบผิดทันที mastery ลดเหลือ 0.19

**กฎ independent:** attempt ที่ทำทันทีหลัง tutor สาธิตใน turn เดียวกันไม่นับ เพราะเป็นการทำตามมากกว่าการแสดงความเข้าใจ (`bkt.count_only_independent`)

## 2. ดาวความสำคัญของหัวข้อ

```
r_t = Σ w_e·[หัวข้อ t ออกในข้อสอบชุด e] ÷ Σ w_e
★★★ ถ้า r_t ≥ three_star_min_r
★★  ถ้า 0 < r_t < three_star_min_r  หรือเป็น prerequisite โดยตรงของหัวข้อ ★★★
★   ถ้า r_t = 0
0   ถ้า user หรือ note สั่งตัด
```

| ค่า | ค่า | ป้าย | ที่มา / วิธี calibrate |
|---|---|---|---|
| w ของข้อสอบอาจารย์เดียวกัน | 1.0 | [calc] | ค่าอ้างอิง |
| w ของข้อสอบคนละอาจารย์ | 0.5 | [C] | PoC P3: วัดว่าหัวข้อในข้อสอบของอาจารย์ 2 คนซ้อนทับกันกี่ % แล้วใช้สัดส่วนนั้น |
| three_star_min_r | 0.6 | [calc] | ค่ากลางของช่วงที่ให้ผลเหมือนกันทุกกรณีที่พบบ่อย (ตารางล่าง) · ตรวจกับ label ของทีมใน P3 (≥ 80% ตรงกัน) |
| prerequisite_of_three_star_gets | 2 | [calc] | = ★★ ตามสูตรดาว (ai-orchestration §2.3.5) · นับเฉพาะ prerequisite โดยตรง |

**Sensitivity analysis**

| กรณี | r | ผล |
|---|---|---|
| ข้อสอบ 2 ชุด อาจารย์เดียวกัน · ออกทั้ง 2 | 1.0 | ★★★ |
| ข้อสอบ 2 ชุด อาจารย์เดียวกัน · ออก 1 | 0.5 | ★★ |
| อาจารย์เรา 1 + อาจารย์อื่น 1 · ออกเฉพาะชุดอาจารย์เรา | 0.67 | ★★★ |
| อาจารย์เรา 1 + อาจารย์อื่น 1 · ออกเฉพาะชุดอาจารย์อื่น | 0.33 | ★★ |

threshold ใดก็ได้ในช่วง 0.51–0.66 ให้ผลเหมือนกัน 0.6 จึงเป็นค่ากลางของช่วงที่เสถียร ความหมายคือ "ออกทุกชุดของอาจารย์ผู้สอนเรา = สำคัญมาก"

ไม่มีข้อสอบเก่าเลย: ใช้ tercile ของจำนวนหน้า (open question ตัดสินหลัง P3)

## 3. Spaced review

Cepeda et al. (2008) พบว่าระยะห่างระหว่างการทบทวนที่ดีที่สุดขึ้นกับเวลาที่ต้องจำ: สอบอีก 7 วันควรห่าง 1 วัน, 35 วันควรห่าง 11 วัน สำหรับช่วงสั้นอัตราส่วนประมาณ **20%** ของเวลาที่เหลือ ส่วนการเพิ่มระยะห่างทีละขั้นใช้ค่าเริ่มต้นของ SM-2 (รอบแรก 1 วัน, easiness factor 2.5)

```
gap_k = round(first_gap_days × growth_factor^(k−1))        // 1, 3 (2.5→3), 6, 16, ...
ถ้า gap_k > max(min_gap_days, max_gap_ratio × days_left) → หยุดตั้งรอบใหม่
                                                     → หัวข้อนี้ถูกทวนอีกครั้งใน Final mode (วันก่อนสอบ)
ทวนผิด → ระดับกลับเป็น developing และเริ่ม k = 1 ใหม่
```

**ตัวอย่าง** (นับวันจากวันที่หัวข้อผ่าน)

| วันที่เหลือก่อนสอบตอนผ่าน | รอบทวน | ทวนสุดท้าย |
|---|---|---|
| 7 | วันที่ 1 | Final mode (วันที่ 6) |
| 12 | วันที่ 1 | Final mode (วันที่ 11) |
| 30 | วันที่ 1, 4 | Final mode (วันที่ 29) |
| 60 | วันที่ 1, 4, 10 | Final mode (วันที่ 59) |

| ค่า | ค่า | ป้าย |
|---|---|---|
| first_gap_days | 1 | [A] SM-2 |
| growth_factor | 2.5 | [A] SM-2 initial easiness factor |
| max_gap_ratio_of_days_left | 0.2 | [A] Cepeda et al. 2008 |
| review_slots_at_session_start | 2 | [C] ปรับตามความยาว session จริง |
| min_gap_days | 1 | [calc] = first_gap_days (หน่วยที่เล็กที่สุดที่ planner นัดได้) |

## 4. ระดับและเงื่อนไข "ผ่าน" (Done)

| ระดับ | เงื่อนไข |
|---|---|
| ยังไม่เริ่ม | ไม่มี attempt |
| อ่อน | mastery < 0.5 |
| กำลังดี | อื่นๆ ที่ยังไม่ผ่าน |
| ผ่าน | (1) ทุก skill ที่ `exam_freq > 0` มี independent correct ≥ 1 (ถ้าไม่มีข้อสอบเก่า นับทุก skill) และ (2) mastery ≥ 0.95 และ (3) หัวข้อ ★★★ ต้องจบด้วยโจทย์ difficulty 3 |

| ค่า | ค่า | ป้าย | ที่มา / วิธี calibrate |
|---|---|---|---|
| min_independent_correct_per_skill | 1 | [C] | หลัง Alpha: ดูว่าคนที่ผ่าน skill ด้วยการตอบถูกเอง 1 ข้อ ตอบข้อทวน (spaced review) ของ skill นั้นถูกกี่ % ถ้าต่ำให้เพิ่มเป็น 2 |
| three_star_final_difficulty | 3 | [calc] | = ระดับสูงสุดของความยาก 1–3 (ระดับข้อสอบ) |
| tight_mode_two_star_difficulty | 2 | [calc] | = ระดับกลางของความยาก 1–3 |

เหตุผลที่ต้องมี skill coverage นอกจาก mastery: BKT ของเราวัดระดับหัวข้อ หัวข้อกว้างอย่างการแยกตัวประกอบมีโจทย์หลายแบบ ถ้าดูแค่ mastery ผู้เรียนอาจผ่านทั้งที่เคยเจอโจทย์แบบเดียว

## 5. ความพร้อม (readiness)

```
readiness = Σ_t (r_t × mastery_t) ÷ Σ_t r_t      (ไม่รวมหัวข้อ 0 ดาว)
```

ความหมาย: สัดส่วนของเนื้อหาข้อสอบที่คาดว่าผู้เรียนทำได้ ไม่มีตัวเลขตั้งเองเพิ่ม เพราะ r_t มาจากข้อสอบเก่า (§2) และ mastery มาจาก BKT (§1) ถ้าไม่มีข้อสอบเก่าใช้สัดส่วนจำนวนหน้าแทน r_t

## 6. Planner: ประมาณเวลาและเลือก mode

```
problems_per_skill = จำนวนข้อที่คาดว่าต้องใช้ให้ mastery ถึง 0.95 (จำลองจาก BKT params)
need      = Σ_{topic ยังไม่ผ่าน} Σ_{skill ยังไม่ครอบคลุม} problems_per_skill × minutes_per_problem
available = days_left × daily_minutes
ratio     = need ÷ available
```

ผลจำลองด้วยค่าปัจจุบัน (100,000 รอบ): ค่าเฉลี่ย 7.8 ข้อ, median 6 ข้อ, p90 15 ข้อ ต่อการไปถึง 0.95 ตัวเลขนี้จะเปลี่ยนเองเมื่อ fit BKT params ใหม่

| ค่า | ค่า | ป้าย | วิธี calibrate |
|---|---|---|---|
| minutes_per_problem | 4 | [C] | ใช้ค่าเฉลี่ยของผู้ใช้เองจาก `attempts` ค่าแรกจาก PoC P4-lite |
| daily_minutes | 45 | [C] | ใช้ค่าที่ผู้ใช้กรอกใน S08 หรือเวลา session จริง |
| session_minutes | 45 | [C] | = daily_minutes (1 session ต่อวัน) · หลัง Alpha ใช้ความยาว session จริงของผู้ใช้แทน |
| tight_ratio / triage_ratio | 0.8 / 1.2 | [C] | หลัง Alpha เทียบเวลาที่ประมาณกับเวลาจริง ตั้งขอบตามความคลาดเคลื่อนที่วัดได้ |
| triage_days_left | 3 | [C] | หลัง Alpha: ดูว่าคนที่เข้า triage ตอนเหลือ ≤ 3 วัน ยังทำหัวข้อ ★★★ จบครบไหม แล้วเลื่อนจุดตัด |
| final_mode_days_left | 1 | [calc] | = วันก่อนสอบ (นิยามของ Final mode) |
| interleave_every_n_practice | 4 | [C] | Rohrer & Taylor (2007) รองรับการคละโจทย์ แต่ยังไม่มีอัตราส่วนมาตรฐาน (Could) |

## 7. Park และ wheel-spinning

| ค่า | ค่า | ป้าย | ที่มา |
|---|---|---|---|
| max_problems_per_skill_per_day | 10 | [A] | Beck & Gong (2013) นิยาม wheel-spinning ว่าทำเกิน 10 ข้อแล้วยังไม่ถูก 3 ข้อติด และ ASSISTments ให้พักเมื่อทำครบ 10 ข้อในวันเดียวโดยยังไม่ mastery |
| max_fail_streak_per_skill | 3 | [C] | ผิดครั้งที่ 3 = tutor สอนไปแล้ว 2 มุม (AM-09) แต่ไม่ได้ผล เป็นสัญญาณพื้นฐานขาด · หลัง Alpha วัดว่าคนที่ผิดครั้งที่ 3 แล้วทำต่อสุดท้ายผ่านกี่ % |

## 8. ตัวเลขอื่นที่เกี่ยวข้อง

| ค่า | ค่า | ป้าย | ที่มา / วิธี calibrate |
|---|---|---|---|
| OCR confirm_below_confidence | 0.8 | [C] | PoC P1: precision–recall บน golden set เลือกจุดที่จับบรรทัดอ่านผิดได้ ≥ 95% |
| Checker targets | verdict ≥ 95%, error type ≥ 80%, บรรทัดผิด ≥ 85% | requirement | ~20 คำตอบต่อ session → ผิดประมาณ 1 ครั้ง/session ซึ่งรับได้เพราะมี dispute flow |
| SymPy timeout | 2 วินาที | [calc] | งบเวลาเพื่อให้ verdict มาก่อนเป้า TTFT p95 < 2 วินาที (เดิมติดป้าย [B] แต่ไม่ใช่มาตรฐานหรือค่า default ของ library) |
| numeric_rel_tolerance | 0.01 | [C] | Should: แทนด้วยจำนวนเลขนัยสำคัญที่โจทย์กำหนด · P2 วัดว่ามีคำตอบทศนิยมที่ตัดสินผิดเพราะค่านี้กี่ข้อ |
| max_generate_retries | 2 | [C] | P2/S3: วัด % ของโจทย์ที่สร้างแล้วเฉลยผ่าน SymPy ในรอบที่ 1, 2, 3 แล้วเลือกจำนวนรอบที่ครอบคลุม ≥ 95% (เดิมติดป้าย [B] โดยไม่มีอ้างอิง) |
| idle_minutes_to_end | 15 | [C] | หลัง Alpha: ดูการกระจายของช่วงเว้นระหว่างข้อความของผู้ใช้ใน session แล้วใช้ค่า p95 |
| TTFT p95 | < 2 วินาที | [A]+[B] | Nielsen: ภายใน 1 วินาทีความคิดไม่ขาดตอน · LLM มี latency พื้นฐาน จึงใช้ 2 วินาทีกับ streaming |
| context_recent_turns, grounding_chunks | 8, 4 | [C] | Liu et al. (2023): LLM ใช้ข้อมูลกลาง context ยาวได้แย่ลง จึงส่งเฉพาะที่เกี่ยวข้อง · ปรับใน P3 |
| token_budget | 6,000 | [calc] | ~2 เท่าของ prompt ~3,200 tokens (ai-orchestration 2.2.3) |
| Circuit breaker | 50%, 10 calls, 60 วินาที | [B] | ค่า default ของ Resilience4j |
| Buddy quota, ระยะห่าง, encourage | 1/2/3, 4 turns, 2 | [C] | Alpha: อัตรา mute buddy + survey "ช่วยไหม / กวนไหม" |

## 9. แผน calibrate

| เมื่อไหร่ | ค่าที่ปรับ | ข้อมูลที่ใช้ |
|---|---|---|
| PoC P1 (S2) | ocr.confirm_below_confidence | golden set ลายมือ |
| PoC P3 (S2) | stars.weight_other_instructor, three_star_min_r, grounding_chunks | ไฟล์วิชา pilot + label ของทีม |
| PoC P4-lite (S3) | default_minutes_per_problem (ค่าแรก) | เวลาตอบใน demo |
| หลัง Alpha | bkt.p_init, bkt.p_transit (pyBKT), max_fail_streak, planner ratios, buddy quota | ตาราง `attempts`, `planner_decisions`, `buddy_events` |

## 10. หัวข้อที่จะลงรายละเอียดต่อ (งานวิจัยรองรับ learning path และ progress tracking)

รายการตั้งต้นสำหรับคุยกับทีมและอาจารย์ ยังไม่ได้สรุป

- การเรียงลำดับหัวข้อตาม prerequisite (learning path) และกรอบทฤษฎีที่รองรับ
- Mastery learning: เกณฑ์ผ่านก่อนไปหัวข้อถัดไป
- เปรียบเทียบโมเดล tracking: BKT, Performance Factors Analysis, Deep Knowledge Tracing ว่าตัวไหนเหมาะกับข้อมูลน้อยแบบโปรเจกต์เรา
- Retrieval practice และ immediate feedback ที่รองรับการ "ให้โจทย์ก่อน สอนทันทีเมื่อผิด"
- Spacing และ interleaving ในบริบทเตรียมสอบระยะสั้น
- วิธีประเมินผล (evaluation) ว่าระบบช่วยให้ผู้เรียนดีขึ้นจริงในช่วง pilot

## References

- Corbett & Anderson (1995) และขอบของ guess/slip, เกณฑ์ mastery 0.95 · อ้างผ่าน [Slater & Baker, Degree of Error in BKT Estimates](https://learninganalytics.upenn.edu/ryanbaker/behaviormetrika_vfinal.pdf)
- [Badrinath et al. (2021) pyBKT: An Accessible Python Library of BKT Models](https://arxiv.org/html/2105.00385v2)
- [Beck & Gong (2013) Wheel-Spinning: Students Who Fail to Master a Skill](https://www.researchgate.net/publication/290777423_Wheel-Spinning_Students_Who_Fail_to_Master_a_Skill) · นิยามและเพดาน 10 ข้อ/วันสรุปไว้ใน [Decision Tree Modeling of Wheel-Spinning and Productive Persistence](https://files.eric.ed.gov/fulltext/EJ1183799.pdf)
- [Cepeda et al. (2008) Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention](https://files.eric.ed.gov/fulltext/ED505660.pdf)
- [SM-2 algorithm (SuperMemo)](https://en.wikipedia.org/wiki/SM-2_(algorithm))
- [Rohrer & Taylor (2007) The Shuffling of Mathematics Practice Problems Boosts Learning](https://digitalcommons.usf.edu/psy_facpub/1767/)
- [Nielsen · Response Times: The 3 Important Limits](https://www.nngroup.com/articles/response-times-3-important-limits/)
- [Liu et al. (2023) Lost in the Middle: How Language Models Use Long Contexts](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf)
- [Resilience4j CircuitBreaker](https://resilience4j.readme.io/v1.0.0/docs/circuitbreaker)
