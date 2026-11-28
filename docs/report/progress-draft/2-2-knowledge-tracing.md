# 2.2 การติดตามความรู้และการวางลำดับการเรียนรู้ · ร่าง 1

## อยากเล่าอะไร (ก่อนอ่านร่าง)

- หัวข้อนี้เป็นฐานทฤษฎีของการติดตามความก้าวหน้าและการวางลำดับการเรียน ซึ่งกรรมการถามถึงความน่าเชื่อถือ (คอมเมนต์ข้อ 1)
- เล่าครบ 4 เรื่อง: ระบบรู้ได้อย่างไรว่าผู้เรียนเข้าใจแค่ไหน (BKT) · เมื่อไรนับว่าผ่าน (mastery learning) · บอกผู้เรียนว่าพร้อมแค่ไหนอย่างไร (readiness) · เรียนอะไรก่อนหลัง (learning path)
- **บอกตรงๆ ว่า BKT ไม่ใช่ model ที่แม่นที่สุด** (Gervet 2020) แล้วอธิบายเหตุผลที่ยังเลือก และแผนเทียบกับ model อื่น · กรรมการจะเห็นว่าทีมรู้ข้อจำกัดและเลือกอย่างมีเหตุผล
- การเชื่อมทฤษฎีกับการออกแบบย้ายไปเป็นตารางท้ายบท (2.6 Design Rationale) ตามแบบตัวอย่าง ENG (Jam 28 พ.ย.) · หัวข้อนี้เล่าเฉพาะทฤษฎี

---

## 2.2 การติดตามความรู้และการวางลำดับการเรียนรู้

ระบบติวที่ปรับตามผู้เรียนต้องตอบคำถาม 4 ข้อ ได้แก่ ผู้เรียนเข้าใจแต่ละหัวข้อแค่ไหน เมื่อไรจึงนับว่าผ่าน จะบอกผู้เรียนอย่างไรว่าพร้อมสอบแค่ไหน และควรเรียนหัวข้อใดก่อนหลัง หัวข้อนี้สรุปงานวิจัยที่ใช้ตอบคำถามแต่ละข้อ ส่วนการนำมาใช้ในระบบสรุปไว้ในหัวข้อ 2.6

### 2.2.1 Bayesian Knowledge Tracing

Knowledge tracing คือการประมาณความรู้ของผู้เรียนจากประวัติการตอบคำถาม โดยความรู้ของผู้เรียนเปลี่ยนไปเรื่อยๆ ระหว่างที่ระบบกำลังประเมิน Bayesian Knowledge Tracing (BKT) [Corbett 1995] เป็นวิธีที่นิยมที่สุดวิธีหนึ่ง และใช้ในระบบติวอัตโนมัติที่มีผู้ใช้จำนวนมาก เช่น Cognitive Tutor [Slater 2018] BKT มองว่าความรู้ในแต่ละทักษะมีสองสถานะ คือ "ยังไม่รู้" และ "รู้แล้ว" และใช้ parameter 4 ตัวต่อทักษะ ได้แก่

- p(L₀) ความน่าจะเป็นที่ผู้เรียนรู้ทักษะนั้นอยู่แล้วก่อนทำข้อแรก
- p(G) ความน่าจะเป็นที่ผู้เรียนตอบถูกทั้งที่ยังไม่รู้ (guess)
- p(S) ความน่าจะเป็นที่ผู้เรียนตอบผิดทั้งที่รู้แล้ว (slip)
- p(T) ความน่าจะเป็นที่ผู้เรียนเรียนรู้ทักษะนั้นหลังทำแต่ละข้อ (transit)

หลังผู้เรียนตอบแต่ละข้อ BKT ปรับความน่าจะเป็นที่ผู้เรียนรู้แล้ว p(L) ด้วยทฤษฎีบทของ Bayes ตามสมการที่ 2.1 และ 2.2 แล้วเพิ่มโอกาสที่ผู้เรียนเรียนรู้จากข้อนั้นตามสมการที่ 2.3

```
ตอบถูก:   p(L | ถูก) = p(L)(1 − p(S)) / [ p(L)(1 − p(S)) + (1 − p(L)) p(G) ]      (2.1)
ตอบผิด:   p(L | ผิด) = p(L) p(S) / [ p(L) p(S) + (1 − p(L))(1 − p(G)) ]            (2.2)
หลังเรียนรู้: p(L_next) = p(L | คำตอบ) + (1 − p(L | คำตอบ)) p(T)                   (2.3)
```

ระบบที่ใช้ BKT เกือบทั้งหมดถือว่าผู้เรียนผ่านทักษะนั้นเมื่อ p(L) ถึง 0.95 [Slater 2018] และต้องจำกัดค่า guess และ slip ไม่ให้สูงเกินไป เพราะ model อาจเพี้ยนจนการตอบผิดกลายเป็นหลักฐานว่ารู้มากกว่าการตอบถูก (model degeneracy) ขอบที่ Corbett และ Anderson ใช้คือ p(G) ไม่เกิน 0.30 และ p(S) ไม่เกิน 0.10 [Slater 2018]

**ทางเลือกอื่นและเหตุผลที่เลือก BKT:** BKT ไม่ใช่ model ที่ทำนายผลได้แม่นที่สุด Gervet และคณะ [Gervet 2020] เปรียบเทียบ model หลายแบบบน 9 ชุดข้อมูล และพบว่า logistic regression ที่เลือก feature ดีทำได้ดีที่สุดในชุดข้อมูลขนาดกลาง Deep Knowledge Tracing (DKT) ซึ่งใช้ neural network ทำได้ดีที่สุดในชุดข้อมูลขนาดใหญ่ ส่วน BKT ทำได้ด้อยกว่าทั้งสองแบบ อย่างไรก็ตาม Khajah และคณะ [Khajah 2016] แสดงว่า BKT ที่เพิ่มปัจจัยด้านเวลา ความแตกต่างระหว่างผู้เรียน และความคล้ายระหว่างทักษะ ทำได้ใกล้เคียง DKT และตีความได้ง่ายกว่า และ Pelánek [Pelánek 2017] สรุปว่าไม่มี model ใดดีที่สุดในทุกกรณี ต้องเลือกตามบริบทและจุดประสงค์ของระบบ

### 2.2.2 Mastery Learning และเกณฑ์การผ่าน

Mastery learning คือแนวทางที่ให้ผู้เรียนเรียนหัวข้อหนึ่งจนเข้าใจตามเกณฑ์ก่อนไปหัวข้อถัดไป โดยมีการทดสอบระหว่างเรียนและการแก้ไขจุดที่ยังไม่เข้าใจ Kulik และคณะ [Kulik 1990] ทำ meta-analysis จาก 108 การทดลอง และพบว่า mastery learning ทำให้คะแนนสอบดีขึ้น โดยได้ผลมากกับผู้เรียนที่อ่อน แต่ต้องใช้เวลาเรียนมากขึ้น

การใช้ BKT เป็นเกณฑ์ผ่านมีข้อควรระวัง Pelánek [Pelánek 2018] ชี้ว่าค่า 0.95 จะหมายถึง "มั่นใจร้อยละ 95 ว่าผู้เรียนรู้แล้ว" ได้ก็ต่อเมื่อหน่วยความรู้ที่วัดมีขนาดเล็กและเป็นแบบรู้หรือไม่รู้ ถ้าหน่วยความรู้กว้าง เช่น หัวข้อทั้งหัวข้อ ความหมายของค่านี้จะคลาดเคลื่อน นอกจากนี้ BKT ไม่ได้คำนึงถึงความยากของโจทย์ ผู้เรียนที่ตอบโจทย์ง่ายถูกติดกันหลายข้อจึงอาจถึงเกณฑ์ทั้งที่ยังไม่เคยทำโจทย์ระดับข้อสอบ

### 2.2.3 ความพร้อมสอบและการแสดงความก้าวหน้า

การแสดงสิ่งที่ระบบประเมินเกี่ยวกับความรู้ของผู้เรียนให้ผู้เรียนเห็นเรียกว่า open learner model Bull และ Kay [Bull 2016] เสนอกรอบการออกแบบหน้าจอลักษณะนี้ ซึ่งช่วยให้ผู้เรียนรู้จุดแข็งและจุดอ่อนของตนเอง อย่างไรก็ตาม ผลการทดลองของ Roediger และ Karpicke ในหัวข้อ 2.1.1 แสดงว่าผู้เรียนมักประเมินความพร้อมของตนเองสูงเกินจริง ตัวเลขความพร้อมที่ระบบแสดงจึงต้องมาจากผลการทำโจทย์จริง ไม่ใช่จากความรู้สึกของผู้เรียน ส่วนการตรวจว่าตัวเลขที่ระบบคำนวณเชื่อถือได้ Feng และคณะ [Feng 2009] แสดงว่าข้อมูลระหว่างการติว เช่น จำนวนความช่วยเหลือที่ผู้เรียนต้องใช้ ทำนายคะแนนสอบปลายปีได้ดีกว่าการดูเพียงว่าตอบถูกหรือผิด ซึ่งเป็นแนวทางในการเทียบค่าที่ระบบคำนวณกับคะแนนสอบจริง

### 2.2.4 การวางลำดับการเรียนรู้ (Learning Path)

Knowledge Space Theory [Falmagne 2011] อธิบายความรู้ในวิชาหนึ่งเป็นโครงสร้างของความรู้พื้นฐานที่ต้องมีก่อน (prerequisite) และใช้โครงสร้างนี้พาผู้เรียนไปยังหัวข้อที่พร้อมจะเรียนต่อ แนวคิดนี้เป็นฐานของระบบติวเชิงพาณิชย์อย่าง ALEKS ส่วนการเลือกลำดับการสอนด้วย reinforcement learning Doroudi และคณะ [Doroudi 2019] ทบทวนงานวิจัยและพบว่าได้ผลดีเมื่อถูกจำกัดด้วยทฤษฎีจากจิตวิทยาการเรียนรู้ และวิธีนี้ต้องใช้ข้อมูลจำนวนมาก

อีกประเด็นหนึ่งคือผู้เรียนที่ทำโจทย์ทักษะเดิมซ้ำนานโดยไม่ผ่าน Beck และ Gong เรียกพฤติกรรมนี้ว่า wheel-spinning โดยนิยามว่าผู้เรียนทำโจทย์ทักษะเดียวกันตั้งแต่ 10 ข้อขึ้นไปโดยยังไม่ถึงเกณฑ์ผ่าน และระบบ ASSISTments หยุดให้ผู้เรียนทำโจทย์ชุดเดิมต่อเมื่อทำครบ 10 ข้อในวันเดียว [Kai 2018]

---

## อ้างอิงที่ใช้ในหัวข้อนี้

| key | อ้างอิง | สิ่งที่ยืนยันแล้ว |
|---|---|---|
| Corbett 1995 | Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction, 4*(4), 253–278. https://doi.org/10.1007/BF01099821 | ⚠ ยังเปิดหน้า publisher ไม่ได้ · ปี: DBLP และงานที่อ้างส่วนใหญ่ใช้ 1995 แต่หน้า Springer ใช้ 1994 (volume 4 คาบปี) → ใช้ 1995 ทั้งเล่ม (ตรงกับ `learning-model.md`) · เนื้อหาที่อ้างในเล่มยืนยันผ่าน Slater 2018 |
| Slater 2018 | Slater, S., & Baker, R. S. (2018). Degree of error in Bayesian knowledge tracing estimates from differences in sample sizes. *Behaviormetrika*. | ✔ อ่าน preprint 28 พ.ย. (learninganalytics.upenn.edu): BKT = HMM 4 parameter (หน้า 2) · Cognitive Tutor (หน้า 2) · สมการ 1–2 (หน้า 5) · "p(S) = 0.10, p(G) = 0.30 (Corbett & Anderson, 1995)" เพื่อกัน model degeneracy (หน้า 7) · "0.95 … commonly-used (almost always-used in systems that use BKT) threshold" (หน้า 13) · ❓ volume/issue/หน้าของฉบับตีพิมพ์ยังไม่ได้ตรวจ |
| Gervet 2020 | Gervet, T., Koedinger, K., Schneider, J., & Mitchell, T. (2020). When is deep learning the best approach to knowledge tracing? *Journal of Educational Data Mining, 12*(3), 31–54. | `learning-path.md` ✔ |
| Khajah 2016 | Khajah, M., Lindsey, R. V., & Mozer, M. C. (2016). How deep is knowledge tracing? *EDM 2016*. | `learning-path.md` ✔ |
| Pelánek 2017 | Pelánek, R. (2017). Bayesian knowledge tracing, logistic models, and beyond: An overview of learner modeling techniques. *User Modeling and User-Adapted Interaction, 27*(3–5), 313–350. | `learning-path.md` ✔ |
| Kulik 1990 | Kulik, C.-L. C., Kulik, J. A., & Bangert-Drowns, R. L. (1990). Effectiveness of mastery learning programs: A meta-analysis. *Review of Educational Research, 60*(2), 265–299. | `learning-path.md` ✔ |
| Pelánek 2018 | Pelánek, R. (2018). Conceptual issues in mastery criteria: Differentiating uncertainty and degrees of knowledge. *AIED 2018*, 450–461. | `learning-path.md` ✔ |
| Bull 2016 | Bull, S., & Kay, J. (2016). SMILI☺: A framework for interfaces to learning data in open learner models, learning analytics and related fields. *International Journal of Artificial Intelligence in Education, 26*(1), 293–331. | `learning-path.md` ✔ |
| Feng 2009 | Feng, M., Heffernan, N., & Koedinger, K. (2009). Addressing the assessment challenge with an online system that tutors as it assesses. *User Modeling and User-Adapted Interaction, 19*(3), 243–266. | `learning-path.md` ✔ |
| Falmagne 2011 | Falmagne, J.-C., & Doignon, J.-P. (2011). *Learning Spaces*. Springer. | `learning-path.md` ✔ (ผ่าน survey arXiv:1511.06757) |
| Doroudi 2019 | Doroudi, S., Aleven, V., & Brunskill, E. (2019). Where's the reward? A review of reinforcement learning for instructional sequencing. *International Journal of Artificial Intelligence in Education, 29*(4), 568–620. | `learning-path.md` ✔ |
| Kai 2018 | Kai, S., Almeda, M. V., Baker, R. S., Heffernan, C., & Heffernan, N. (2018). Decision tree modeling of wheel-spinning and productive persistence in skill builders. *Journal of Educational Data Mining, 10*(1), 36–71. | ✔ อ่านต้นฉบับ 28 พ.ย. (files.eric.ed.gov EJ1183799): Beck & Gong (2013) นิยาม wheel-spinning = 10 opportunities ขึ้นไปโดยยังไม่ mastery (ถูก 3 ข้อติด) (หน้า 5, 8) · ASSISTments หยุดผู้เรียนเมื่อทำครบ 10 ข้อในโจทย์ชุดเดียวกันภายในวันเดียว (หน้า 7) · หน้า 36–71 (หน้าที่ 4 ของไฟล์คือหน้า 39 ของวารสาร · ไฟล์มี 36 หน้า) |

**อ้างผ่านงานอื่น ไม่อ้างตรง:** Beck & Gong (2013) อ้างผ่าน Kai 2018 เพราะยังไม่ได้เปิดต้นฉบับ · Corbett & Anderson อ้างตรงได้เพราะเป็นต้นกำเนิดของ BKT แต่เนื้อหาเฉพาะ (ขอบของ guess/slip) อ้าง Slater 2018 ที่อ่านแล้ว

**ไม่ใช้:** Zhang et al. (2025) เกณฑ์ 0.98 (เป็นความสัมพันธ์ ไม่ใช่เหตุผล · ใช้ตอน calibrate) · Dunlosky & Rawson (2012) (◐) · Bloom (1968) (◐)

## คำถามสำหรับร่างนี้

1. **ชื่อหัวข้อ:** ตกลง (Jam 28 พ.ย.)
2. **สมการ BKT:** ใส่ (Jam 28 พ.ย.) · ตอนรวมเล่มใช้ Equation Editor แทนบล็อกโค้ด
3. **สถานะ:** ใส่ "อยู่ระหว่างพัฒนา" ในส่วนที่ยังไม่ต่อเข้าห้องติว (Jam 28 พ.ย.)
