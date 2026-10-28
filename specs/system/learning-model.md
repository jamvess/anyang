# Learning model · สูตรและที่มาของตัวเลข (v1.2)

**v1.2 (26 ต.ค. 2569):** BKT ไม่รู้ความยากของโจทย์ จึงเพิ่มระดับเป้าตามดาวและ mode และเพดาน mastery ตามระดับยากสุดที่ทำถูกเอง (§4) · ความพร้อมใช้ mastery หลังเพดาน (§5)

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

**ข้อจำกัด: BKT ไม่รู้ความยากของโจทย์** ตอบถูกโจทย์ง่ายดัน mastery ขึ้นเท่ากับโจทย์ระดับข้อสอบ ตอบถูกโจทย์ difficulty 1 ติดกัน 3 ข้อก็ถึง 0.986 ทั้งที่ยังไม่เคยเจอโจทย์ระดับข้อสอบ · ปรับ guess/slip ตามความยากอย่างเดียว (แนว KT-IDEM) แค่ชะลอ ไม่กัน ทำง่ายติดกันมากพอก็ยังถึงเกณฑ์ · MVP จึงเก็บค่า BKT ดิบไว้ใน `topic_progress.mastery` แล้วจำกัดด้วยเพดานตามระดับยากสุดที่ทำถูกเอง ตอนคิดระดับ, เงื่อนไขผ่าน และความพร้อม (§4)

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
| w ของข้อสอบคนละอาจารย์ | 0.5 | [C] | วัดว่าหัวข้อในข้อสอบของอาจารย์ 2 คนซ้อนทับกันกี่ % แล้วใช้สัดส่วนนั้น · **P3 วัดไม่ได้** เพราะข้อสอบเก่าทั้ง 2 ชุดมาจากอาจารย์ชุดเดียวกัน (`specs/poc/reports/P3.md`) · วัดกับวิชาแรกที่มีข้อสอบของ 2 อาจารย์ |
| three_star_min_r | 0.6 | [calc] | ค่ากลางของช่วงที่ให้ผลเหมือนกันทุกกรณีที่พบบ่อย (ตารางล่าง) · **P3:** สูตร + map ข้อสอบของทีมให้ ★★★ ตรงกับ label 10/12 = 83% (เป้า ≥ 80%) · มีข้อสอบ 2 ชุด r จึงเป็นได้แค่ 0, 0.5, 1 · P3 ยืนยันได้แค่ว่าเกณฑ์ต้องมากกว่า 0.5 |
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
gap_k = round_half_up(first_gap_days × growth_factor^(k−1))   // 1, 3 (2.5→3), 6, 16, ...
ถ้า gap_k > max(min_gap_days, max_gap_ratio × days_left) → หยุดตั้งรอบใหม่
                                                     → หัวข้อนี้ถูกทวนอีกครั้งใน Final mode (วันก่อนสอบ)
ทวนผิด → ระดับกลับเป็น developing และเริ่ม k = 1 ใหม่
```

- `round_half_up(x) = floor(x + 0.5)` · ห้ามใช้ `round()` ของ Python เพราะปัดครึ่งไปเลขคู่ (`round(2.5) = 2`) จะได้ 1, 2, 6, ... ไม่ตรงกับตัวอย่าง
- `days_left` = วันที่เหลือก่อนสอบ **ณ วันที่ตั้งรอบถัดไป** (วันที่หัวข้อผ่าน หรือวันที่ทวนรอบล่าสุด) ไม่ใช่ค่าคงที่ ณ วันที่ผ่าน · ตารางด้านล่างคำนวณแบบนี้ (ถ้านับ ณ วันที่ผ่าน แถว 30 วันจะได้ 1, 4, 10)

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

**ระดับยากสุดที่ทำถูกเอง** `d_max` = difficulty สูงสุดของ attempt ในหัวข้อนี้ที่ independent และตอบถูก (ยังไม่มี = 0) · ทำผิดภายหลังไม่ลด `d_max` เพราะ BKT ลด mastery ให้อยู่แล้ว

**ระดับเป้า** `d_target` ตามดาวและ mode ของ planner (ai-orchestration §2.5.2)

| ดาว | Normal | Tight | Triage |
|---|---|---|---|
| ★★★ | 3 | 3 | 3 |
| ★★ | 3 | 2 | 2 |
| ★ | 2 | 2 | ข้าม |

**Mastery หลังเพดาน** `mastery_eff` ใช้คิดระดับ, เงื่อนไขผ่าน และความพร้อม (§5) · BKT ยังอัปเดตค่าดิบตาม §1 ทุก attempt

```
mastery_eff = mastery                                                  ถ้า d_max ≥ d_target
            = min(mastery, (bkt.weak_below + bkt.mastery_threshold) / 2)   ถ้า d_max = d_target − 1
            = min(mastery, bkt.weak_below)                             ถ้า d_max ≤ d_target − 2
```

| ระดับ | เงื่อนไข |
|---|---|
| ยังไม่เริ่ม | ไม่มี attempt |
| อ่อน | mastery_eff < 0.5 |
| กำลังดี | อื่นๆ ที่ยังไม่ผ่าน |
| ผ่าน | (1) ทุก skill ที่ `exam_freq > 0` มี independent correct ≥ 1 (ถ้าไม่มีข้อสอบเก่า นับทุก skill) และ (2) mastery_eff ≥ 0.95 และ (3) d_max ≥ d_target |

ข้อ (3) เกิดเองจากข้อ (2) เพราะเพดานทุกขั้นต่ำกว่า 0.95 แต่เขียนไว้ให้อ่านแล้วเข้าใจทันที

**ตัวอย่าง** หัวข้อ ★★★ ใน Normal mode (d_target = 3) ตอบถูกทุกข้อ

| ลำดับ | mastery ดิบ | d_max | mastery_eff | ระดับ |
|---|---|---|---|---|
| ถูก difficulty 1 ข้อ 1–3 | 0.71 → 0.93 → 0.986 | 1 | 0.5 | กำลังดี |
| ถูก difficulty 2 | 0.997 | 2 | 0.725 | กำลังดี |
| ถูก difficulty 3 | 0.9995 | 3 | 0.9995 | ผ่าน (ถ้า skill ครบ) |

| ค่า | ค่า | ป้าย | ที่มา / วิธี calibrate |
|---|---|---|---|
| min_independent_correct_per_skill | 1 | [C] | หลัง Alpha: ดูว่าคนที่ผ่าน skill ด้วยการตอบถูกเอง 1 ข้อ ตอบข้อทวน (spaced review) ของ skill นั้นถูกกี่ % ถ้าต่ำให้เพิ่มเป็น 2 |
| three_star_final_difficulty | 3 | [calc] | = ระดับสูงสุดของความยาก 1–3 (ระดับข้อสอบ) |
| two_star_final_difficulty | 3 | [calc] | = ระดับข้อสอบ เหมือน ★★★ · ★★ ออกสอบเหมือนกันแค่ไม่ทุกชุด (§2) |
| one_star_final_difficulty | 2 | [calc] | = ระดับกลางของความยาก 1–3 · ★ ไม่เคยออกสอบ ใช้เป็นพื้นฐานของหัวข้ออื่น |
| tight_mode_two_star_difficulty | 2 | [calc] | = ระดับกลางของความยาก 1–3 · ใช้ทั้ง Tight และ Triage |
| เพดานเมื่อขาด 1 ขั้น | 0.725 | [calc] | = (weak_below + mastery_threshold) ÷ 2 กึ่งกลางช่วง "กำลังดี" · ไม่อยู่ใน config เพราะคิดจาก `bkt.*` |
| เพดานเมื่อขาด ≥ 2 ขั้น | 0.5 | [calc] | = weak_below ขอบล่างของ "กำลังดี" · ไม่อยู่ใน config |

เหตุผลที่ต้องมี skill coverage นอกจาก mastery: BKT ของเราวัดระดับหัวข้อ หัวข้อกว้างอย่างการแยกตัวประกอบมีโจทย์หลายแบบ ถ้าดูแค่ mastery ผู้เรียนอาจผ่านทั้งที่เคยเจอโจทย์แบบเดียว · เพดานตามความยากแก้ปัญหาคู่กัน: ผู้เรียนอาจผ่านทั้งที่เคยเจอแค่โจทย์ง่าย

## 5. ความพร้อม (readiness)

```
readiness = Σ_t (r_t × mastery_eff_t) ÷ Σ_t r_t      (ไม่รวมหัวข้อ 0 ดาว)
```

ความหมาย: สัดส่วนของเนื้อหาข้อสอบที่คาดว่าผู้เรียนทำได้ ไม่มีตัวเลขตั้งเองเพิ่ม เพราะ r_t มาจากข้อสอบเก่า (§2) และ mastery_eff มาจาก BKT (§1) หลังเพดานตามความยาก (§4) ถ้าไม่มีข้อสอบเก่าใช้สัดส่วนจำนวนหน้าแทน r_t · ใช้ mastery_eff เพื่อไม่ให้ความพร้อมสูงเกินจริงตอนที่ยังทำได้แค่โจทย์ง่าย · ผลข้างเคียง: เมื่อ mode เปลี่ยน d_target ของ ★★ เปลี่ยน ความพร้อมจึงขยับได้โดยไม่มี attempt ใหม่

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
| return_after_sessions | 1 | [C] | หัวข้อที่ Park ไว้กลับเข้า queue เมื่อผ่านไปอย่างน้อยกี่ session (ai-orchestration §2.5.3) · ค่าเดิมในเอกสาร v1.0 ยังไม่มีที่มา · หลัง Alpha: เทียบอัตราผ่านของหัวข้อที่กลับมาทำหลัง 1 กับ 2+ session |

## 8. ตัวเลขอื่นที่เกี่ยวข้อง

| ค่า | ค่า | ป้าย | ที่มา / วิธี calibrate |
|---|---|---|---|
| OCR always_confirm | true | policy (PoC P1) | P1: confidence ที่ model ให้ตัวเองแยกบรรทัดที่อ่านผิดไม่ได้ (บรรทัดผิดทั้ง 6 อยู่ที่ 0.85–0.98 · ไม่มี threshold ที่จับได้ ≥ 95%) จึงยืนยันทุกครั้ง (`specs/poc/reports/P1.md`) · S3 ลองสัญญาณอื่น เช่นอ่าน 2 รอบแล้วเทียบ |
| Checker targets | verdict ≥ 95%, error type ≥ 80%, บรรทัดผิด ≥ 85% | requirement | ~20 คำตอบต่อ session → ผิดประมาณ 1 ครั้ง/session ซึ่งรับได้เพราะมี dispute flow |
| SymPy timeout | 2 วินาที | [calc] | งบเวลาเพื่อให้ verdict มาก่อนเป้า TTFT p95 < 2 วินาที (เดิมติดป้าย [B] แต่ไม่ใช่มาตรฐานหรือค่า default ของ library) |
| numeric_rel_tolerance | 0.01 | [C] | Should: แทนด้วยจำนวนเลขนัยสำคัญที่โจทย์กำหนด · P2 วัดว่ามีคำตอบทศนิยมที่ตัดสินผิดเพราะค่านี้กี่ข้อ |
| max_generate_retries | 2 | [C] | P2/S3: วัด % ของโจทย์ที่สร้างแล้วเฉลยผ่าน SymPy ในรอบที่ 1, 2, 3 แล้วเลือกจำนวนรอบที่ครอบคลุม ≥ 95% (เดิมติดป้าย [B] โดยไม่มีอ้างอิง) |
| idle_minutes_to_end | 15 | [C] | หลัง Alpha: ดูการกระจายของช่วงเว้นระหว่างข้อความของผู้ใช้ใน session แล้วใช้ค่า p95 |
| TTFT p95 | < 2 วินาที | [A]+[B] | Nielsen: ภายใน 1 วินาทีความคิดไม่ขาดตอน · LLM มี latency พื้นฐาน จึงใช้ 2 วินาทีกับ streaming |
| context_recent_turns, grounding_chunks | 8, 4 | [C] | Liu et al. (2023): LLM ใช้ข้อมูลกลาง context ยาวได้แย่ลง จึงส่งเฉพาะที่เกี่ยวข้อง · **P3b:** `gemini-embedding-2` @768 หาหน้าคำตอบเจอใน 4 อันดับแรก 19/20 (อันดับ 1: 15/20) จึงคง 4 |
| token_budget | 6,000 | [calc] | ~2 เท่าของ prompt ~3,200 tokens (ai-orchestration 2.2.3) |
| Circuit breaker | 50%, 10 calls, 60 วินาที | [B] | ค่า default ของ Resilience4j |
| Buddy quota, ระยะห่าง, encourage | 1/2/3, 4 turns, 2 | [C] | Alpha: อัตรา mute buddy + survey "ช่วยไหม / กวนไหม" |

## 9. แผน calibrate

| เมื่อไหร่ | ค่าที่ปรับ | ข้อมูลที่ใช้ |
|---|---|---|
| PoC P1 (S2) · ทำแล้ว | ocr.always_confirm (เดิม confirm_below_confidence) | golden set ลายมือ 30 รูป |
| P2 (S3) | สัญญาณแยกบรรทัดที่อ่านผิด เพื่อลดการยืนยัน | golden set ลายมือ + คำตอบ |
| PoC P3 (S2) · ทำแล้ว (บางส่วน) | three_star_min_r (ยืนยันได้แค่ > 0.5), grounding_chunks (คง 4) · weight_other_instructor วัดไม่ได้ | ไฟล์วิชา pilot + label ของทีม · `specs/poc/reports/P3.md` |
| PoC P4-lite (S3) | default_minutes_per_problem (ค่าแรก) | เวลาตอบใน demo |
| หลัง Alpha | bkt.p_init, bkt.p_transit (pyBKT), max_fail_streak, planner ratios, buddy quota | ตาราง `attempts`, `planner_decisions`, `buddy_events` |
| หลัง Alpha | เพดาน mastery ตามความยาก (§4) | ตาราง `attempts` + `problems.difficulty`: คนที่ผ่านตามกติกา §4 ทำโจทย์ difficulty 3 ในรอบทวนถูกกี่ % · เทียบกับ BKT ที่มี guess/slip ต่อระดับความยาก (KT-IDEM) และ Elo |

## 10. หัวข้อที่จะลงรายละเอียดต่อ (งานวิจัยรองรับ learning path และ progress tracking)

รายการงานวิจัยที่ตรวจแล้ว (20 ต.ค. 2569) อยู่ใน [`docs/research/learning-path.md`](../../docs/research/learning-path.md) · ครอบคลุม 7 ด้านที่ MVP ใช้จริง: knowledge tracing, mastery learning, progress/readiness, learning path, ฝึกด้วยโจทย์ + feedback, spaced review และการพิสูจน์ผล · interleaving และการแบ่งเวลาเมื่อเวลาไม่พอ ไม่อยู่ใน MVP

ประเด็นที่งานวิจัยท้าทาย design ปัจจุบัน และรอคุยกับทีมและอาจารย์ (ยังไม่ได้เปลี่ยนสูตรหรือค่าใน config)

- BKT ระดับหัวข้อ หรือระดับ skill (§1, §4)
- BKT หรือ logistic model หลังมีข้อมูลจาก Alpha (§1)
- เกณฑ์ mastery 0.95 หรือสูงกว่า (§1, §4)
- ความพร้อม % ทำให้ผู้เรียนมั่นใจเกินไหม และ validate กับคะแนนสอบจริงยังไง (§5)
- mastery ควรลดลงตามเวลาไหม (§3, §5)
- ความยากของโจทย์ใน BKT (§1, §4) · MVP ใช้ระดับเป้า + เพดาน (v1.2) · หลัง Alpha เทียบกับ BKT ที่มี guess/slip ต่อระดับความยาก (Pardos & Heffernan 2011, KT-IDEM) และ Elo ที่ประมาณความยากของโจทย์ไปพร้อมกับความสามารถของผู้เรียน (Pelánek 2016) · ◐ ยังไม่ได้เปิดต้นฉบับทั้ง 2 งาน

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
