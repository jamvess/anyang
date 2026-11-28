# 2.3 เทคโนโลยี AI ที่เกี่ยวข้อง · ร่าง 1

## อยากเล่าอะไร (ก่อนอ่านร่าง)

- อธิบายเทคโนโลยี AI ที่ระบบใช้ **พร้อมข้อจำกัดของแต่ละอย่าง** เพราะข้อจำกัดเหล่านี้คือเหตุผลที่ทีมต้องออกแบบระบบรอบ AI แทนการให้ AI ตอบเอง (ตอบคอมเมนต์ข้อ 2: ไม่ใช่แค่ยิง API)
- ลำดับ: LLM และข้อจำกัด → การควบคุมผลลัพธ์ (structured output, prompt injection) → RAG และ embedding → การอ่านลายมือ → computer algebra system
- เล่าเฉพาะทฤษฎีและงานวิจัย · การนำมาใช้อยู่ในตาราง 2.6 · ผล PoC ของเราอยู่ในบทที่ 4
- ใช้เฉพาะแหล่งที่เปิดอ่านแล้ว 28 พ.ย. (ดูตารางอ้างอิงท้ายไฟล์)

---

## 2.3 เทคโนโลยี AI ที่เกี่ยวข้อง

### 2.3.1 Large Language Model และข้อจำกัด

Large Language Model (LLM) คือ model ภาษาที่ train จากข้อความจำนวนมาก และสร้างข้อความตอบกลับตามข้อความที่ได้รับ LLM ทำให้สร้างระบบที่สนทนาเป็นภาษาธรรมชาติ อธิบายเนื้อหา และอ่านเอกสารได้ด้วยต้นทุนต่ำ แต่มีข้อจำกัดสำคัญสามข้อเมื่อนำมาใช้เป็นผู้ติว

ข้อแรก LLM อาจสร้างเนื้อหาที่ฟังดูถูกต้องแต่ไม่ตรงกับข้อเท็จจริงหรือข้อมูลที่ได้รับ เรียกว่า hallucination [Ji 2023] ข้อที่สอง ความสามารถทางคณิตศาสตร์ของ LLM ยังไม่สม่ำเสมอ Frieder และคณะ [Frieder 2023] ประเมิน ChatGPT และ GPT-4 กับโจทย์คณิตศาสตร์หลายระดับ และพบว่า GPT-4 ใช้กับคณิตศาสตร์ระดับปริญญาตรีได้ แต่ทำโจทย์ระดับบัณฑิตศึกษาไม่ได้ และความสามารถโดยรวมยังต่ำกว่านักศึกษาระดับบัณฑิตศึกษา

ข้อที่สาม การให้ผู้เรียนใช้ LLM อย่างอิสระอาจทำให้เรียนรู้น้อยลง Bastani และคณะ [Bastani 2025] ทดลองกับนักเรียนมัธยมปลายเกือบ 1,000 คน โดยให้ใช้ GPT-4 สองแบบระหว่างการฝึกทำโจทย์ คือ GPT Base ที่ทำงานเหมือน ChatGPT ทั่วไป และ GPT Tutor ที่มี prompt ออกแบบมาเพื่อปกป้องการเรียนรู้ ระหว่างการฝึก คะแนนของทั้งสองกลุ่มสูงขึ้น (ร้อยละ 48 สำหรับ GPT Base และร้อยละ 127 สำหรับ GPT Tutor) แต่เมื่อไม่มี AI ให้ใช้ กลุ่ม GPT Base ได้คะแนนต่ำกว่ากลุ่มที่ไม่เคยใช้ AI เลยร้อยละ 17 ผู้วิจัยอธิบายว่าผู้เรียนใช้ AI เป็นไม้ค้ำ คือให้ AI ทำโจทย์แทนการคิดเอง

### 2.3.2 การควบคุมผลลัพธ์ของ LLM

ระบบที่นำผลลัพธ์ของ LLM ไปประมวลผลต่อด้วยโปรแกรมต้องได้ผลลัพธ์ในรูปแบบที่กำหนด LLM รุ่นปัจจุบันรองรับ structured output ซึ่งบังคับให้ model ตอบตาม JSON Schema ที่กำหนด ทำให้ได้ผลลัพธ์ที่มีรูปแบบคาดเดาได้และตรวจชนิดข้อมูลได้ [Google 2025]

ความเสี่ยงอีกด้านคือ prompt injection ซึ่ง OWASP จัดเป็นความเสี่ยงอันดับหนึ่งของแอปพลิเคชันที่ใช้ LLM โดยนิยามว่าเป็นกรณีที่ข้อความที่ส่งเข้า model ทำให้พฤติกรรมหรือผลลัพธ์ของ model เปลี่ยนไปโดยไม่ตั้งใจ [OWASP 2025] รูปแบบที่เกี่ยวข้องกับระบบนี้คือ indirect prompt injection ซึ่งเกิดเมื่อ LLM รับข้อมูลจากแหล่งภายนอก เช่น ไฟล์หรือเว็บไซต์ Greshake และคณะ [Greshake 2023] แสดงว่าผู้โจมตีสามารถแฝงคำสั่งไว้ในข้อมูลที่แอปพลิเคชันจะดึงมาใช้ และทำให้แอปพลิเคชันจริงทำงานผิดไปได้โดยไม่ต้องเข้าถึงแอปพลิเคชันโดยตรง ระบบที่ให้ผู้ใช้อัปโหลดเอกสารและบรรยายบุคลิกของ AI ด้วยข้อความอิสระจึงต้องป้องกันความเสี่ยงนี้

### 2.3.3 Retrieval-Augmented Generation และ Embedding

Retrieval-Augmented Generation (RAG) [Lewis 2020] คือการให้ LLM สร้างคำตอบจากเนื้อหาที่ค้นมาจากแหล่งข้อมูลภายนอก แทนการใช้เพียงความรู้ที่อยู่ใน model ทำให้คำตอบอ้างอิงเนื้อหาที่ตรวจสอบได้ การค้นเนื้อหาทำโดยแปลงข้อความเป็นเวกเตอร์ตัวเลขที่เรียกว่า embedding แล้วค้นส่วนของเอกสารที่มีเวกเตอร์ใกล้กับคำถามมากที่สุด

คุณภาพของการค้นขึ้นกับ embedding model Gemini Embedding [Lee 2025] เป็น embedding model ที่สร้างจาก Gemini รองรับข้อความหลายภาษา และได้รับการประเมินด้วย Massive Multilingual Text Embedding Benchmark ซึ่งมีมากกว่า 100 งานในกว่า 250 ภาษา ส่วนเทคนิค Matryoshka Representation Learning [Kusupati 2022] ทำให้ embedding เดียวใช้งานได้หลายขนาด จึงเลือกขนาดเวกเตอร์ที่เล็กลงเพื่อประหยัดพื้นที่จัดเก็บและเวลาค้นได้

นอกจากการค้นให้ตรงแล้ว ปริมาณเนื้อหาที่ส่งให้ LLM ก็มีผล Liu และคณะ [Liu 2023] พบว่า LLM ใช้ข้อมูลที่อยู่ต้นหรือท้ายข้อความได้ดีที่สุด และทำงานได้แย่ลงอย่างมีนัยสำคัญเมื่อข้อมูลที่ต้องใช้อยู่กลางข้อความยาว การส่งเฉพาะเนื้อหาที่เกี่ยวข้องจึงดีกว่าการส่งเอกสารทั้งหมด

### 2.3.4 การอ่านคำตอบที่เขียนด้วยลายมือ

LLM รุ่นปัจจุบันหลายรุ่นรับภาพเป็นข้อมูลนำเข้าได้ (multimodal) จึงอ่านลายมือในภาพและแปลงเป็นข้อความหรือสมการในรูปแบบ LaTeX ได้ อย่างไรก็ตาม model อาจอ่านผิดโดยไม่แสดงอาการ และด้วยลักษณะของ hallucination (หัวข้อ 2.3.1) model อาจ "แก้" คำตอบที่ผิดของผู้เรียนให้เป็นคำตอบที่ถูก ซึ่งเป็นความเสี่ยงเฉพาะของการใช้ LLM ตรวจคำตอบ ทีมจึงวัดความแม่นยำของการอ่านลายมือด้วย PoC ก่อนพัฒนาส่วนนี้ (หัวข้อ 4.4)

### 2.3.5 Computer Algebra System

Computer algebra system คือโปรแกรมที่จัดการนิพจน์ทางคณิตศาสตร์ในรูปสัญลักษณ์ เช่น การจัดรูป การแยกตัวประกอบ การหาอนุพันธ์ และการแก้สมการ โดยให้ผลที่แน่นอนตามกฎทางคณิตศาสตร์ SymPy [Meurer 2017] เป็น computer algebra system แบบ open source ที่เขียนด้วยภาษา Python การตรวจว่าคำตอบสองแบบเท่ากันทางคณิตศาสตร์ทำได้โดยลบนิพจน์ทั้งสองแล้วจัดรูปผลต่าง ถ้าได้ศูนย์แปลว่าเท่ากัน วิธีนี้ตัดสินได้ถูกต้องแม้คำตอบจะเขียนต่างรูปกัน เช่น 2(x + 1) กับ 2x + 2 และไม่มีปัญหา hallucination แบบ LLM แต่ใช้ได้เฉพาะคำตอบที่แปลงเป็นนิพจน์ทางคณิตศาสตร์ได้

---

## อ้างอิงที่ใช้ในหัวข้อนี้

| key | อ้างอิง | สิ่งที่ยืนยันแล้ว (28 พ.ย.) |
|---|---|---|
| Ji 2023 | Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Chen, D., Dai, W., Chan, H. S., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*. https://doi.org/10.1145/3571730 · arXiv:2202.03629 | ✔ abstract (arXiv) · หน้า arXiv ระบุ "ACM Computing Surveys (2022)" · ❓ ปีและ volume ของฉบับตีพิมพ์ (ACM CSUR 55(12), 2023?) ยังไม่ได้ตรวจ |
| Frieder 2023 | Frieder, S., Pinchetti, L., Chevalier, A., Griffiths, R.-R., Salvatori, T., Lukasiewicz, T., Petersen, P. C., & Berner, J. (2023). Mathematical capabilities of ChatGPT. *NeurIPS 2023 Datasets and Benchmarks*. arXiv:2301.13867 | ✔ abstract: GPT-4 ใช้ได้ระดับปริญญาตรี "fails on graduate-level difficulty" · ต่ำกว่า "graduate student" · ไม่มีตัวเลข |
| Bastani 2025 | Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakcı, Ö., & Mariman, R. (2025). Generative AI without guardrails can harm learning: Evidence from high school mathematics. *Proceedings of the National Academy of Sciences, 122*(26), e2422633122. https://doi.org/10.1073/pnas.2422633122 | ✔ abstract (RePEc/IDEAS): เกือบ 1,000 คน · GPT Base vs GPT Tutor · ฝึก +48% / +127% · เมื่อเอาออก GPT Base −17% · ไม้ค้ำ (crutch) · ⚠ abstract ไม่ได้บอกผลของ GPT Tutor หลังเอา AI ออก → ไม่เขียน |
| Google 2025 | Google. (2025). Structured output. *Gemini API documentation*. https://aistudio.google.com/docs/structured-output | ✔ "generate responses that adhere to a provided JSON Schema … predictable, type-safe results" · ❓ วันที่เข้าถึงใส่ตอนรวมเล่ม |
| OWASP 2025 | OWASP. (2025). LLM01:2025 Prompt injection. *OWASP Top 10 for LLM Applications 2025*. https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | ✔ นิยาม prompt injection และ indirect prompt injection · หน้าชื่อ "LLM01:2025" |
| Greshake 2023 | Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection. arXiv:2302.12173 | ✔ abstract · ❓ venue (AISec 2023) ไม่ได้ระบุบนหน้า arXiv |
| Lewis 2020 | Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. arXiv:2005.11401 | ✔ abstract · "Accepted at NeurIPS 2020" |
| Lee 2025 | Lee, J., et al. (2025). Gemini Embedding: Generalizable embeddings from Gemini. arXiv:2503.07891 | ✔ abstract: MMTEB > 100 งาน 250+ ภาษา · หลายภาษา · ⚠ model ที่ระบบใช้ (`gemini-embedding-2` ใน `config/ai.yaml`) อาจเป็นรุ่นใหม่กว่าที่ paper บรรยาย → เขียนว่า "ตระกูล" ในตาราง 2.6 |
| Kusupati 2022 | Kusupati, A., Bhatt, G., Rege, A., Wallingford, M., Sinha, A., Ramanujan, V., Howard-Snyder, W., Chen, K., Kakade, S., Jain, P., & Farhadi, A. (2022). Matryoshka representation learning. arXiv:2205.13147 | ✔ abstract: embedding เดียวปรับตามข้อจำกัดของงาน · ❓ venue (NeurIPS 2022) ไม่ได้ระบุบนหน้า arXiv |
| Liu 2023 | Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). Lost in the middle: How language models use long contexts. *Transactions of the Association for Computational Linguistics*. arXiv:2307.03172 | ✔ abstract · ❓ ปีและ volume ของ TACL |
| Meurer 2017 | Meurer, A., et al. (2017). SymPy: symbolic computing in Python. *PeerJ Computer Science, 3*, e103. https://doi.org/10.7717/peerj-cs.103 | ✔ หน้า citing ของ docs.sympy.org และหน้าแรก sympy.org ("a Python library for symbolic mathematics … computer algebra system") · หน้า PeerJ เปิดไม่ได้ (403) |

**ไม่ใช้:** CROHME (การแข่งขันอ่านสมการลายมือ) · ยังไม่ได้เปิดต้นฉบับ · 2.3.4 จึงไม่มีอ้างอิงภายนอก ใช้ผล PoC ของเราแทน

## คำถามสำหรับร่างนี้

1. **2.3.4 ไม่มีอ้างอิงภายนอก** · ใช้ผล P1 ของเรา (บทที่ 4) เป็นหลักฐาน · พอไหม หรือจะให้หางานวิจัยเรื่องการอ่านสมการลายมือเพิ่ม
2. **Bastani 2025** ตรงกับระบบเรามาก (AI ที่ให้คำตอบเลยทำให้เรียนรู้น้อยลง) · ใช้เป็นเหตุผลของการตรวจเฉลยหลุดและการใบ้ทีละระดับในตาราง 2.6 · โอเคไหม
