# รายการงานวิจัยรองรับ learning path และ progress tracking

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/learning-path-research` |
| Checklist item | เตรียมรายการงานวิจัยเรื่อง learning path และ progress tracking สำหรับคุยกับทีม (`learning-model.md` §10) |
| Status | in progress · 2026-10-20 |

## Plan

- [x] 1. 🤖 ตั้งคำถามต่อด้าน (คุยกับ Jam แล้ว 20 ต.ค. · ดู Decisions)
- [x] 2. 🤖 ค้นและตรวจงานวิจัยด้านละ 2–3 ชิ้นใน 7 ด้าน (เริ่มจาก 1–3) · ทุกชิ้นต้องเปิดลิงก์ได้จริงและอ่าน abstract แล้ว · ชิ้นที่อ้างอยู่แล้วใน learning-model.md ไม่ค้นซ้ำ · สรุป: พบอะไร · รองรับหรือท้าทาย design ข้อไหน · ใช้ที่ไหน (code / config / prompt / UI / รายงาน)
- [x] 3. 🤖 เขียนเป็นเอกสาร `docs/research/learning-path.md` (ภาษาไทย) และลิงก์จาก `learning-model.md` §10 · งานวิจัยที่ใช้อ้างค่าใน config อยู่แล้ว (Corbett & Anderson, Cepeda, Beck & Gong ฯลฯ) ไม่ต้องค้นซ้ำ แค่อ้างถึง
- [x] 4. 🙋 Jam อ่านแล้วเลือก: ชิ้นไหนจะเอาไปคุยกับทีมและอาจารย์ · ข้อเสนอเปลี่ยน design ข้อไหนที่จะเสนอ · ตอบเป็นเลขข้อ
- [x] 5. 🤖 ทำ agenda 1 หน้าสำหรับคุยกับทีม/อาจารย์: คำถามที่ต้องตัดสิน + งานวิจัยที่รองรับแต่ละข้อ
- [ ] 6. 🤖 ติ๊ก checklist แล้ว `/work-done`

## Definition of done

- ครบ 7 ด้าน (ดู Decisions) · แต่ละด้านมีงานวิจัยอย่างน้อย 2 ชิ้นที่ตรวจแล้วว่ามีจริง (ลิงก์เปิดได้)
- แต่ละชิ้นบอกว่ารองรับหรือท้าทายการตัดสินใจไหนของเรา
- Jam เลือกแล้วว่าจะเอาอะไรไปคุย · มี agenda พร้อมใช้
- checklist ข้อนี้ติ๊กแล้ว

## Decisions

- 2026-10-20 · เลือกทำข้อนี้ระหว่างรอโควตา free tier (P1/P3 รันได้หลัง 14:00 น.)
- 2026-10-20 · (Jam ตัดสิน) เอาเฉพาะ core ของ MVP 7 ด้าน: 1 knowledge tracing · 2 mastery learning · 3 progress/readiness · 4 learning path (prerequisite) · 5 ฝึกด้วยโจทย์ + feedback (retrieval practice, pretesting, formative feedback) · 6 spaced review · 7 พิสูจน์ผล (learning gain) · ตัดออกจาก MVP: แบ่งเวลาเมื่อเวลาไม่พอ, interleaving, motivation/affect, LLM tutor risk
- 2026-10-20 · (Jam ok) เอกสารมีคอลัมน์ "ใช้ที่ไหน": ด้าน 1–6 อยู่ในแอป (code/config/prompt/UI) และใช้ในรายงาน · ด้าน 7 อยู่นอกแอป (pilot + รายงาน) แอปแค่เก็บ log · calibration หลัง Alpha (↩️) ทำนอกแอปแล้วแก้ config
- 2026-10-20 · คำถามที่จะใส่ agenda: ด้าน 1 BKT ระดับหัวข้อ vs ระดับ skill (Done ดูระดับ skill) · ด้าน 3 สูตรความพร้อมยังไม่เคยเทียบกับคะแนนสอบจริง และ mastery ไม่มี forgetting
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) ประเด็นที่เอาไปคุย: 1 BKT ระดับ skill (เสนอเปลี่ยน · ต้องตกลงก่อน Junior เขียน domain ใน S3), 2 BKT vs logistic (คุย ไม่เปลี่ยน · เทียบหลัง Alpha), 4 ความพร้อม % กับความมั่นใจเกิน + validate กับคะแนนสอบจริง (เกี่ยวกับ May และแผน pilot) · ไม่คุยตอนนี้: 3 เกณฑ์ 0.95, 5 mastery ลดตามเวลา

## Research notes (ขั้น 2 · ตรวจแล้ว 20 ต.ค. · ✔ = เปิด abstract หรือ full text แล้ว · ◐ = ยืนยันแค่ citation จากแหล่งรอง)

**1 Knowledge tracing**
- ✔ Gervet, Koedinger, Schneider, Mitchell (2020) When is Deep Learning the Best Approach to Knowledge Tracing? JEDM 12(3) 31–54 · 9 datasets: logistic regression ดีสุดใน data ขนาดกลาง, DKT ดีสุดใน data ใหญ่, **BKT แพ้ทั้งคู่** → ท้าทายการเลือก BKT · https://jedm.educationaldatamining.org/index.php/JEDM/article/view/451
- ✔ Khajah, Lindsey, Mozer (2016) How Deep is Knowledge Tracing? EDM 2016 (best paper) · BKT ที่เพิ่ม recency, ความต่างระหว่างคน ฯลฯ ทำได้พอๆ กับ DKT และอธิบายได้ง่ายกว่า → รองรับ BKT ที่ขยายได้ · https://arxiv.org/abs/1604.02416
- ✔ Pelánek (2017) Bayesian knowledge tracing, logistic models, and beyond. UMUAI 27(3–5) 313–350 · overview + การเลือกโมเดลขึ้นกับบริบท · https://www.fi.muni.cz/~xpelanek/publications/umuai-overview.pdf

**2 Mastery learning**
- ✔ Kulik, Kulik, Bangert-Drowns (1990) Effectiveness of Mastery Learning Programs: A Meta-Analysis. RER 60(2) 265–299 · 108 การทดลอง: คะแนนสอบดีขึ้น ได้ผลมากกับนักเรียนอ่อน แต่ใช้เวลาเพิ่ม → รองรับ Done + เตือนเรื่องเวลา · https://doi.org/10.3102/00346543060002265
- ✔ Pelánek (2018) Conceptual Issues in Mastery Criteria. AIED 2018 450–461 · 0.95 ของ BKT แปลว่า "95% ว่ารู้แล้ว" ได้เฉพาะ KC ละเอียด ถ้า skill หยาบ ความหมายเพี้ยน → **รองรับย้าย BKT ไประดับ skill** · https://www.fi.muni.cz/~xpelanek/publications/mastery-modeling.pdf
- ✔ Zhang, Vanacore, Baker et al. (2025) How Much Mastery is Enough Mastery? EDM 2025 short · Rori: 0.95 ยังใช้ได้ แต่ ≥ 0.98 สัมพันธ์กับผลบทถัดไปดีกว่า (correlational) · https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.short-papers.4/index.html
- ◐ Bloom (1968) Learning for Mastery. UCLA Evaluation Comment 1(2) · ที่มาของ mastery learning · ใช้เป็นการอ้างอิงประวัติเท่านั้น

**3 Progress / readiness**
- ◐ Dunlosky & Rawson (2012) Overconfidence produces underachievement. Learning and Instruction 22(4) 271–280 · มั่นใจเกิน → เรียนน้อยลง → ผลแย่ · https://doi.org/10.1016/j.learninstruc.2011.08.003
- ✔ Bull & Kay (2016) SMILI☺: A Framework for Interfaces to Learning Data in Open Learner Models. IJAIED 26(1) 293–331 · กรอบออกแบบหน้าจอที่ให้ผู้เรียนเห็นโมเดลของตัวเอง → progress card · https://research.birmingham.ac.uk/en/publications/smili-a-framework-for-interfaces-to-learning-data-in-open-learner/
- ◐ Al-Shanfari, Demmans Epp, Baber (2020) แสดงความมั่นใจของผู้เรียนคู่กับค่าของระบบ ช่วย knowledge monitoring โดยเฉพาะคนอ่อน (เจอจาก search ยังไม่ได้เปิด)
- ✔ Feng, Heffernan, Koedinger (2009) Addressing the assessment challenge with an online system that tutors as it assesses. UMUAI 19(3) 243–266 · ข้อมูลระหว่างติว (ต้องช่วยมากแค่ไหน) ทำนายคะแนนสอบปลายปีได้ดีกว่าดูแค่ถูก/ผิด → แนวทาง validate readiness + อาจใช้จำนวนครั้งที่ต้อง Teach

**4 Learning path**
- ✔ Doroudi, Aleven, Brunskill (2019) Where's the Reward? A Review of RL for Instructional Sequencing. IJAIED 29(4) 568–620 · RL ได้ผลเมื่อถูกจำกัดด้วยทฤษฎีจิตวิทยา → รองรับ planner แบบกฎ · https://doi.org/10.1007/s40593-019-00187-x
- ✔ Doignon & Falmagne: Knowledge Space Theory (1985) · Falmagne & Doignon (2011) Learning Spaces, Springer · ฐานของ ALEKS: เรียนตามโครงสร้าง prerequisite → รองรับเรียงหัวข้อตาม prereqs ของ A6 · https://arxiv.org/abs/1511.06757

**5 ฝึกด้วยโจทย์ + feedback**
- ✔ Dunlosky, Rawson, Marsh, Nathan, Willingham (2013) Improving Students' Learning With Effective Learning Techniques. PSPI 14(1) 4–58 · 10 เทคนิค: practice testing + distributed practice = high utility · rereading/highlighting = low → รองรับทั้ง loop · https://doi.org/10.1177/1529100612453266
- ✔ Richland, Kornell, Kao (2009) The Pretesting Effect. J Exp Psych: Applied 15(3) 243–257 · ตอบผิดก่อนเรียนยังช่วยให้จำดีขึ้น → รองรับ Probe ก่อนสอน (TM-03)
- ✔ Hattie & Timperley (2007) The Power of Feedback. RER 77(1) 81–112 · ✔ Shute (2008) Focus on Formative Feedback. RER 78(1) 153–189 · feedback ต้องเจาะจง ทันเวลา ไม่ตัดสิน → รองรับชี้บรรทัดแรกที่ผิด · คำถาม no-hint ยังไม่มีคำตอบตรง

**6 Spaced review**
- ✔ Cepeda, Pashler, Vul, Wixted, Rohrer (2006) Distributed Practice in Verbal Recall Tasks. Psych Bulletin 132(3) 354–380 · 317 การทดลอง: ระยะห่างที่ดีที่สุดโตตามเวลาจนถึงสอบ → รองรับสูตร ratio (คู่กับ Cepeda 2008 ที่อ้างอยู่แล้ว)
- ✔ Settles & Meeder (2016) A Trainable Spaced Repetition Model for Language Learning. ACL 2016 1848–1858 · half-life regression ทำนายการลืม ลด error 45%+ → ทางเลือกถ้าจะให้ mastery ลดลงตามเวลา (หลัง Alpha) · https://aclanthology.org/P16-1174/

**7 พิสูจน์ผล**
- ✔ Hake (1998) Interactive-engagement versus traditional methods. Am J Physics 66(1) 64–74 · normalized gain = gain ÷ gain สูงสุดที่ได้ → ตัวชี้วัด pre/post ของ pilot
- ◐ VanLehn (2011) The Relative Effectiveness of Human Tutoring, ITS, and Other Tutoring Systems. Educational Psychologist 46(4) 197–221 · human d ≈ 0.79, step-based ITS ≈ 0.76 (ตัวเลขจากแหล่งรอง ต้องเช็คกับต้นฉบับ) → ระบบตรวจทีละบรรทัดของเราเป็น step-based
- ✔ Kulik & Fletcher (2016) Effectiveness of Intelligent Tutoring Systems: A Meta-Analytic Review. RER 86(1) 42–78 · 50 การทดลอง median 0.66 SD · ผลใหญ่กว่าเมื่อวัดด้วยข้อสอบที่ทำเองเทียบกับข้อสอบมาตรฐาน → ระวังตอนออกแบบ pre/post test

## Next step

ขั้น 6: ติ๊ก checklist ข้อ "เตรียมรายการงานวิจัยเรื่อง learning path และ progress tracking" (S1 Jam) → `/work-done` · reviewer Junior (แตะ learning-model.md ซึ่งเป็นของ Jam · ไม่ได้แตะไฟล์ของคนอื่น)

## Waiting on

ไม่มี

## Notes for next time

- `poc/` ขึ้นเป็น untracked บน branch นี้ (คือ `out/` และ `results/` ของ P1) · ห้าม commit
