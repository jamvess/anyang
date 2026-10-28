# งานวิจัยรองรับ learning path และ progress tracking (MVP)

เอกสารนี้รวมงานวิจัยที่อยู่เบื้องหลังการตัดสินใจหลักของ learning model ใน MVP เพื่อใช้คุยกับทีมและอาจารย์ และใช้ในบทที่ 2 ของรายงาน · สูตรและตัวเลขจริงอยู่ใน `specs/system/learning-model.md` และ `config/learning.yaml`

ตรวจเมื่อ 20 ต.ค. 2569 · ผู้ดูแล: Jam

## ขอบเขต

เลือกเฉพาะเรื่องที่ MVP คำนวณหรือตัดสินจริง 7 ด้าน

| # | ด้าน | ตอบคำถาม | ใน MVP |
|---|---|---|---|
| 1 | Knowledge tracing | ผู้เรียนรู้หัวข้อนี้แค่ไหน | mastery (PM-02) |
| 2 | Mastery learning | เมื่อไหร่นับว่า "ผ่าน" | เงื่อนไข Done (TM-16) |
| 3 | Progress / readiness | พร้อมสอบแค่ไหน และแสดงยังไง | ความพร้อม %, progress card (PM-03, TM-15) |
| 4 | Learning path | เรียนหัวข้อไหนก่อน | เรียงตาม prerequisite (SM-02, TM-01) |
| 5 | ฝึกด้วยโจทย์ + feedback | ทำไมให้โจทย์ก่อน และสอนทันทีเมื่อผิด | Probe → Teach → Verify (TM-03, AM-07, AM-08) |
| 6 | Spaced review | ทวนหัวข้อที่ผ่านแล้วตอนไหน | รอบทวน (TM-17) |
| 7 | พิสูจน์ผล | แอปช่วยได้จริงไหม | pilot และรายงาน (ไม่ใช่ feature) |

**ไม่อยู่ใน MVP:** การแบ่งเวลาเมื่อเวลาไม่พอ (study time allocation), interleaving (เป็น Could ใน spec), แรงจูงใจและ affect (มี wheel-spinning รองรับ Park แล้วใน `learning-model.md` §7), ความเสี่ยงของ LLM tutor

## วิธีอ่าน

- **✔** = เปิดอ่าน abstract หรือ full text แล้ว · **◐** = ยืนยันได้แค่ว่ามีอยู่จริงจากแหล่งรอง ต้องอ่านต้นฉบับก่อนอ้างตัวเลข
- **ใช้ที่ไหน:** `code` (`apps/api/app/domain/`) · `config` (`config/learning.yaml`) · `prompt` (`prompts/`) · `UI` (หน้าเว็บ) · `↩️` วิเคราะห์นอกแอปแล้วกลับมาแก้ config · `รายงาน`
- **กับ design:** 🟢 รองรับ · 🟡 รองรับแต่มีเงื่อนไข · 🔴 ท้าทาย ต้องคุย
- งานที่ `learning-model.md` อ้างอยู่แล้ว (Corbett & Anderson 1995, Cepeda et al. 2008, SM-2, Beck & Gong 2013, Rohrer & Taylor 2007) ไม่ได้ค้นซ้ำ

## 1. Knowledge tracing

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ✔ Gervet, Koedinger, Schneider & Mitchell (2020) | เทียบโมเดลบน 9 datasets: logistic regression ที่เลือก feature ดีชนะใน data ขนาดกลาง, Deep Knowledge Tracing ชนะใน data ใหญ่, BKT แพ้ทั้งสองแบบ | 🔴 เราเลือก BKT · เหตุผลที่ยังใช้ใน MVP: ไม่มี data ให้ fit, ค่า fixed ตาม Corbett & Anderson อธิบายได้ · ควรลอง logistic model หลัง Alpha | code, ↩️, รายงาน |
| ✔ Khajah, Lindsey & Mozer (2016) | BKT ที่เพิ่ม recency, ความต่างของแต่ละคน และความคล้ายระหว่าง skill ทำได้พอๆ กับ DKT และตีความได้ง่ายกว่า | 🟡 ถ้าจะปรับ BKT มีทางขยายโดยไม่ต้องทิ้ง | code, รายงาน |
| ✔ Pelánek (2017) | overview ของ BKT กับ logistic models · ไม่มีโมเดลที่ดีที่สุดทุกกรณี ต้องเลือกตามบริบทและจุดประสงค์ | 🟢 ใช้อธิบายในรายงานว่าทำไมเลือกโมเดลที่อธิบายได้ | รายงาน |

## 2. Mastery learning

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ✔ Kulik, Kulik & Bangert-Drowns (1990) | meta-analysis 108 การทดลอง: mastery learning ทำให้คะแนนสอบดีขึ้น ได้ผลมากกับนักเรียนที่อ่อน แต่ใช้เวลาเรียนมากขึ้น | 🟢 รองรับ Done · 🟡 แอปเรามีวันสอบเป็นเส้นตาย เวลาที่เพิ่มต้องคุมด้วย planner | code, รายงาน |
| ✔ Pelánek (2018) | ค่า 0.95 ของ BKT แปลว่า "มั่นใจ 95% ว่ารู้แล้ว" ได้เฉพาะเมื่อ knowledge component ละเอียดและเป็นแบบรู้/ไม่รู้ · ถ้า skill หยาบ ความหมายจะเพี้ยน | 🔴 เราทำ BKT ระดับ **หัวข้อ** ซึ่งหยาบ แต่ Done ตรวจระดับ skill · เป็นเหตุผลให้ย้าย BKT ไปไว้ระดับ skill | code, config, รายงาน |
| ✔ Zhang, Vanacore, Baker et al. (2025) | ข้อมูลจาก Rori: เกณฑ์ 0.95 ยังใช้ได้ แต่คนที่ถึง ≥ 0.98 เรียนบทถัดไปได้ดีกว่า (เป็นความสัมพันธ์ ไม่ใช่เหตุผล) | 🟡 `bkt.mastery_threshold` อาจขยับขึ้น · ต้องชั่งกับเวลาที่เหลือก่อนสอบ | config, ↩️ |
| ◐ Bloom (1968) "Learning for Mastery" | ที่มาของแนวคิด mastery learning | 🟢 อ้างเป็นประวัติในรายงาน | รายงาน |

## 3. Progress / readiness

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ◐ Dunlosky & Rawson (2012) | ผู้เรียนที่ประเมินตัวเองสูงเกินจะหยุดทวนเร็วเกิน แล้วผลออกมาแย่ | 🔴 ความพร้อม % อาจทำให้มั่นใจเกิน · คำอธิบายใต้ตัวเลขใน progress card ต้องออกแบบให้ดี | UI, รายงาน |
| ✔ Bull & Kay (2016) SMILI☺ | กรอบออกแบบ open learner model คือหน้าจอที่ให้ผู้เรียนเห็นสิ่งที่ระบบคิดว่าเขารู้ | 🟢 ใช้เป็นกรอบออกแบบ progress card | UI, รายงาน |
| ◐ Al-Shanfari, Demmans Epp & Baber (2020) | แสดงความมั่นใจของผู้เรียนคู่กับค่าของระบบ ช่วยให้ประเมินตัวเองแม่นขึ้น โดยเฉพาะคนที่อ่อน | 🟡 ไอเดียหลัง MVP: ให้ผู้เรียนบอกความมั่นใจแล้วเทียบกับ mastery | UI |
| ✔ Feng, Heffernan & Koedinger (2009) | ข้อมูลระหว่างติว (ต้องช่วยมากแค่ไหน) ทำนายคะแนนสอบปลายปีได้ดีกว่าดูแค่ตอบถูกหรือผิด | 🟡 สูตรความพร้อมของเรายังไม่เคยเทียบกับคะแนนสอบจริง · ใช้เป็นแนวทาง validate และอาจใช้จำนวนครั้งที่ต้อง Teach เป็นตัวแปรเพิ่ม | ↩️, รายงาน |

## 4. Learning path

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ✔ Doignon & Falmagne (1985), Falmagne & Doignon (2011) Knowledge Space Theory | อธิบายความรู้เป็นโครงสร้างของ prerequisite · เป็นฐานของ ALEKS ซึ่งพาผู้เรียนไปตามโครงสร้างนี้ | 🟢 รองรับการเรียงหัวข้อตาม `prereqs` ที่ A6 สกัด | prompt (A6), code, รายงาน |
| ✔ Doroudi, Aleven & Brunskill (2019) | review การใช้ reinforcement learning จัดลำดับการสอน: ได้ผลเมื่อถูกจำกัดด้วยทฤษฎีจากจิตวิทยาการเรียนรู้ | 🟢 รองรับ planner แบบกฎที่อธิบายได้ แทน RL ที่ต้องใช้ข้อมูลเยอะ | code, รายงาน |

## 5. ฝึกด้วยโจทย์ + feedback

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ✔ Dunlosky, Rawson, Marsh, Nathan & Willingham (2013) | ประเมิน 10 เทคนิคการเรียน: practice testing และ distributed practice ได้ "high utility" เพียงสองเทคนิค · อ่านซ้ำและขีดเส้นใต้ได้ "low" | 🟢 รองรับทั้ง loop: ให้โจทย์ + ทวนเป็นรอบ แทนการให้อ่านชีท | code, prompt, รายงาน |
| ✔ Richland, Kornell & Kao (2009) | ทำแบบทดสอบก่อนเรียนช่วยให้จำดีขึ้น แม้จะตอบผิด (pretesting effect) | 🟢 รองรับ Probe ก่อนสอน (TM-03) | code, รายงาน |
| ✔ Hattie & Timperley (2007) · ✔ Shute (2008) | feedback มีผลมากทั้งทางบวกและลบ · formative feedback ที่ดีต้องเจาะจง ทันเวลา และไม่ตัดสิน | 🟢 รองรับการชี้บรรทัดแรกที่ผิดและอธิบายทันที (AM-05, AM-07) · 🟡 ยังไม่เจองานที่ตอบตรงว่า "ไม่ให้ hint" ดีกว่าให้ hint | prompt (`tutor_reply`), รายงาน |

## 6. Spaced review

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ✔ Cepeda, Pashler, Vul, Wixted & Rohrer (2006) | meta-analysis 317 การทดลอง: ระยะห่างที่ดีที่สุดระหว่างการทวนจะยาวขึ้นเมื่อเวลาจนถึงการสอบยาวขึ้น | 🟢 รองรับสูตร gap ≤ 20% ของวันที่เหลือ (คู่กับ Cepeda et al. 2008) | config, รายงาน |
| ✔ Settles & Meeder (2016) half-life regression | โมเดลทำนายว่าแต่ละคำจะถูกลืมเมื่อไหร่ ลด error ได้มากกว่า 45% เทียบกับ baseline | 🟡 ตอนนี้ mastery ไม่ลดลงตามเวลา · เป็นทางเลือกหลัง Alpha ถ้าจะให้ความพร้อมสะท้อนการลืม | code, ↩️ |

## 7. พิสูจน์ผล

| งานวิจัย | พบอะไร | กับ design | ใช้ที่ไหน |
|---|---|---|---|
| ✔ Hake (1998) | normalized gain = คะแนนที่เพิ่ม ÷ คะแนนที่เพิ่มได้สูงสุด · เทียบ 62 วิชา 6,542 คน | 🟢 ใช้เป็นตัวชี้วัด pre/post test ของ pilot | รายงาน |
| ◐ VanLehn (2011) | เทียบ human tutoring กับ ITS: ระบบที่ตรวจทีละขั้น (step-based) ได้ผลใกล้ครูตัวต่อตัว | 🟢 ระบบตรวจทีละบรรทัดของเราเป็น step-based · ตัวเลข effect size ต้องเช็คกับต้นฉบับก่อนใส่รายงาน | รายงาน |
| ✔ Kulik & Fletcher (2016) | meta-analysis 50 การทดลอง ITS: median 0.66 SD · ผลใหญ่กว่าเมื่อวัดด้วยข้อสอบที่ทำเองเทียบกับข้อสอบมาตรฐาน | 🟡 ตอนออกแบบ pre/post test ต้องระวังไม่ให้ผลดูดีเกินจริง | รายงาน |

## ประเด็นที่งานวิจัยท้าทาย design (สำหรับคุยกับทีม)

1. **BKT ระดับหัวข้อ หรือระดับ skill** (Pelánek 2018) · Done ตรวจระดับ skill อยู่แล้ว แต่ mastery คิดระดับหัวข้อ
2. **BKT หรือ logistic model** (Gervet et al. 2020, Khajah et al. 2016) · ใช้ BKT ใน MVP แล้วเทียบหลัง Alpha ไหม
3. **เกณฑ์ mastery 0.95 หรือสูงกว่า** (Zhang et al. 2025, Kulik et al. 1990) · ชั่งกับเวลาก่อนสอบ
4. **ความพร้อม % จะทำให้ผู้เรียนมั่นใจเกินไหม** (Dunlosky & Rawson 2012, Bull & Kay 2016) · และจะ validate กับคะแนนสอบจริงยังไง (Feng et al. 2009)
5. **mastery ควรลดลงตามเวลาไหม** (Settles & Meeder 2016)

## References

- Al-Shanfari, L., Demmans Epp, C., & Baber, C. (2020). ◐ งานเรื่องการแสดงความสอดคล้องระหว่างความมั่นใจของผู้เรียนกับ learner model · ยังไม่ได้เปิดต้นฉบับ · [Birmingham](https://research.birmingham.ac.uk/en/publications/visualising-alignment-to-support-students-judgment-of-confidence-/)
- Bloom, B. S. (1968). Learning for mastery. *UCLA Evaluation Comment, 1*(2). ◐
- Bull, S., & Kay, J. (2016). SMILI☺: A framework for interfaces to learning data in open learner models, learning analytics and related fields. *IJAIED, 26*(1), 293–331. [link](https://research.birmingham.ac.uk/en/publications/smili-a-framework-for-interfaces-to-learning-data-in-open-learner/)
- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. *Psychological Bulletin, 132*(3), 354–380. [PubMed](https://pubmed.ncbi.nlm.nih.gov/16719566/)
- Doignon, J.-P., & Falmagne, J.-C. (1985). Spaces for the assessment of knowledge. *International Journal of Man-Machine Studies, 23*, 175–196. ◐
- Doignon, J.-P., & Falmagne, J.-C. (2015). Knowledge spaces and learning spaces (survey). [arXiv:1511.06757](https://arxiv.org/abs/1511.06757) · Falmagne, J.-C., & Doignon, J.-P. (2011). *Learning Spaces*. Springer.
- Doroudi, S., Aleven, V., & Brunskill, E. (2019). Where's the reward? A review of reinforcement learning for instructional sequencing. *IJAIED, 29*(4), 568–620. [doi](https://doi.org/10.1007/s40593-019-00187-x)
- Dunlosky, J., & Rawson, K. A. (2012). Overconfidence produces underachievement: Inaccurate self evaluations undermine students' learning and retention. *Learning and Instruction, 22*(4), 271–280. ◐ [doi](https://doi.org/10.1016/j.learninstruc.2011.08.003)
- Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving students' learning with effective learning techniques. *Psychological Science in the Public Interest, 14*(1), 4–58. [doi](https://doi.org/10.1177/1529100612453266)
- Feng, M., Heffernan, N., & Koedinger, K. (2009). Addressing the assessment challenge with an online system that tutors as it assesses. *User Modeling and User-Adapted Interaction, 19*(3), 243–266. [SRI](https://www.sri.com/publication/education-learning-pubs/digital-learning-pubs/addressing-the-assessment-challenge-in-an-online-system-that-tutors-as-it-assesses/)
- Gervet, T., Koedinger, K., Schneider, J., & Mitchell, T. (2020). When is deep learning the best approach to knowledge tracing? *Journal of Educational Data Mining, 12*(3), 31–54. [JEDM](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/451)
- Hake, R. R. (1998). Interactive-engagement versus traditional methods: A six-thousand-student survey of mechanics test data for introductory physics courses. *American Journal of Physics, 66*(1), 64–74. [PDF](https://web.mit.edu/jrankin/www/Active_Learning/hake_active_phys.pdf)
- Hattie, J., & Timperley, H. (2007). The power of feedback. *Review of Educational Research, 77*(1), 81–112. [PDF](https://www.uky.edu/~gmswan3/575/Hattie_Timperly_2007.pdf)
- Khajah, M., Lindsey, R. V., & Mozer, M. C. (2016). How deep is knowledge tracing? *EDM 2016*. [arXiv:1604.02416](https://arxiv.org/abs/1604.02416)
- Kulik, C.-L. C., Kulik, J. A., & Bangert-Drowns, R. L. (1990). Effectiveness of mastery learning programs: A meta-analysis. *Review of Educational Research, 60*(2), 265–299. [doi](https://doi.org/10.3102/00346543060002265)
- Kulik, J. A., & Fletcher, J. D. (2016). Effectiveness of intelligent tutoring systems: A meta-analytic review. *Review of Educational Research, 86*(1), 42–78. [IDA](https://www.ida.org/research-and-publications/publications/all/e/ef/effectiveness-of-intelligent-tutoring-systems-a-meta-analytic-review)
- Pelánek, R. (2017). Bayesian knowledge tracing, logistic models, and beyond: An overview of learner modeling techniques. *User Modeling and User-Adapted Interaction, 27*(3–5), 313–350. [preprint](https://www.fi.muni.cz/~xpelanek/publications/umuai-overview.pdf)
- Pelánek, R. (2018). Conceptual issues in mastery criteria: Differentiating uncertainty and degrees of knowledge. *AIED 2018*, 450–461. [PDF](https://www.fi.muni.cz/~xpelanek/publications/mastery-modeling.pdf)
- Richland, L. E., Kornell, N., & Kao, L. S. (2009). The pretesting effect: Do unsuccessful retrieval attempts enhance learning? *Journal of Experimental Psychology: Applied, 15*(3), 243–257. [PDF](https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf)
- Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. *ACL 2016*, 1848–1858. [ACL Anthology](https://aclanthology.org/P16-1174/)
- Shute, V. J. (2008). Focus on formative feedback. *Review of Educational Research, 78*(1), 153–189. [PDF](https://myweb.fsu.edu/vshute/pdf/shute%202008_b.pdf)
- VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. *Educational Psychologist, 46*(4), 197–221. ◐
- Zhang, J., Vanacore, K., Baker, R. S., Ch, N., Mills, C., & Henkel, O. (2025). How much mastery is enough mastery? The relationship between mastery in a lesson and the performance on the subsequent lesson. *EDM 2025* (short paper). [EDM](https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.short-papers.4/index.html)
