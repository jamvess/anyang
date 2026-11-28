# 2.3 เทคโนโลยี AI ที่เกี่ยวข้อง · ร่าง 2

## อยากเล่าอะไร (ก่อนอ่านร่าง)

- อธิบายเทคโนโลยี AI ที่ระบบใช้ **พร้อมข้อจำกัดของแต่ละอย่าง** เพราะข้อจำกัดเหล่านี้คือเหตุผลที่ทีมต้องออกแบบระบบรอบ AI แทนการให้ AI ตอบเอง (ตอบคอมเมนต์ข้อ 2: ไม่ใช่แค่ยิง API)
- ลำดับ: LLM และข้อจำกัด → การควบคุมผลลัพธ์ → RAG และ embedding → การอ่านลายมือ → computer algebra system
- **ร่าง 2 (Jam 28 พ.ย.):** เปิดแต่ละหัวข้อด้วย "X คือ …" · ตัด Frieder, Greshake, Lee, Kusupati, Liu (เหลือ 5 งาน) · เอกสาร Gemini structured output ย้ายไปอ้างใน 2.4
- **รูปที่ต้องวาด:** รูปที่ 2.2 ลำดับการทำงานของ RAG (แบ่งเอกสาร → embedding → ค้นส่วนที่ใกล้คำถาม → ส่งให้ LLM)

---

## 2.3 เทคโนโลยี AI ที่เกี่ยวข้อง

### 2.3.1 Large Language Model และข้อจำกัด

Large Language Model (LLM) คือ model ภาษาที่ train จากข้อความจำนวนมาก และสร้างข้อความตอบกลับตามข้อความที่ได้รับ LLM ทำให้สร้างระบบที่สนทนาเป็นภาษาธรรมชาติ อธิบายเนื้อหา และอ่านเอกสารได้ด้วยต้นทุนต่ำ แต่มีข้อจำกัดสำคัญสองข้อเมื่อนำมาใช้เป็นผู้ติว

ข้อแรก LLM อาจสร้างเนื้อหาที่ฟังดูถูกต้องแต่ไม่ตรงกับข้อเท็จจริงหรือข้อมูลที่ได้รับ เรียกว่า hallucination [Ji 2023] ซึ่งรวมถึงการคำนวณหรือตรวจคำตอบคณิตศาสตร์ผิดด้วย เพราะ LLM สร้างคำตอบจากรูปแบบของข้อความ ไม่ได้คำนวณตามกฎทางคณิตศาสตร์

ข้อที่สอง การให้ผู้เรียนใช้ LLM อย่างอิสระอาจทำให้เรียนรู้น้อยลง Bastani และคณะ [Bastani 2025] ทดลองกับนักเรียนมัธยมปลายเกือบ 1,000 คน โดยกลุ่มหนึ่งฝึกทำโจทย์กับ GPT-4 แบบทั่วไปที่ตอบให้ได้ทันที อีกกลุ่มใช้ GPT-4 ที่มี prompt ออกแบบมาเพื่อติวโดยไม่บอกคำตอบ ระหว่างการฝึกทั้งสองกลุ่มทำคะแนนได้ดีขึ้น แต่เมื่อไม่มี AI ให้ใช้ กลุ่มที่ใช้ GPT-4 แบบทั่วไปได้คะแนนต่ำกว่ากลุ่มที่ไม่เคยใช้ AI เลยร้อยละ 17 เพราะผู้เรียนให้ AI ทำโจทย์แทนการคิดเอง

### 2.3.2 การควบคุมผลลัพธ์ของ LLM

Structured output คือความสามารถของ LLM ที่ตอบตามโครงสร้างข้อมูลที่กำหนดไว้ล่วงหน้า เช่น JSON Schema แทนการตอบเป็นข้อความอิสระ ทำให้โปรแกรมนำผลลัพธ์ไปตรวจสอบและประมวลผลต่อได้

ความเสี่ยงอีกด้านคือ prompt injection ซึ่ง OWASP จัดเป็นความเสี่ยงอันดับหนึ่งของแอปพลิเคชันที่ใช้ LLM และนิยามว่าเป็นกรณีที่ข้อความที่ส่งเข้า model ทำให้พฤติกรรมหรือผลลัพธ์ของ model เปลี่ยนไปโดยไม่ตั้งใจ [OWASP 2025] รูปแบบที่เกี่ยวข้องกับระบบนี้คือ indirect prompt injection ซึ่งคำสั่งแฝงมากับข้อมูลจากภายนอก เช่น ไฟล์ที่ผู้ใช้อัปโหลด

### 2.3.3 Retrieval-Augmented Generation และ Embedding

Retrieval-Augmented Generation (RAG) [Lewis 2020] คือการให้ LLM สร้างคำตอบจากเนื้อหาที่ค้นมาจากแหล่งข้อมูลภายนอก แทนการใช้เพียงความรู้ที่อยู่ใน model ทำให้คำตอบอ้างอิงเนื้อหาที่ตรวจสอบได้ ขั้นตอนของ RAG แสดงในรูปที่ 2.2 คือ แบ่งเอกสารเป็นส่วนย่อย แปลงแต่ละส่วนเป็น embedding เก็บไว้ แล้วเมื่อมีคำถามจึงค้นส่วนที่ใกล้กับคำถามที่สุดส่งให้ LLM

Embedding คือเวกเตอร์ตัวเลขที่แทนความหมายของข้อความ ข้อความที่มีความหมายใกล้กันจะมีเวกเตอร์ใกล้กัน การค้นด้วย embedding จึงหาเนื้อหาที่ตรงกับคำถามได้แม้ใช้คำต่างกัน

รูปที่ 2.2 ลำดับการทำงานของ RAG (❓ ต้องวาด)

### 2.3.4 การอ่านคำตอบที่เขียนด้วยลายมือ

LLM แบบ multimodal คือ LLM ที่รับภาพเป็นข้อมูลนำเข้าได้ จึงอ่านลายมือในภาพและแปลงเป็นข้อความหรือสมการในรูปแบบ LaTeX ได้ อย่างไรก็ตาม model อาจอ่านผิดโดยไม่แสดงอาการ และด้วยลักษณะของ hallucination (หัวข้อ 2.3.1) model อาจ "แก้" คำตอบที่ผิดของผู้เรียนให้เป็นคำตอบที่ถูก ซึ่งเป็นความเสี่ยงเฉพาะของการใช้ LLM ตรวจคำตอบ ทีมจึงวัดความแม่นยำของการอ่านลายมือด้วย PoC ก่อนพัฒนาส่วนนี้ (หัวข้อ 4.4)

### 2.3.5 Computer Algebra System

Computer algebra system คือโปรแกรมที่จัดการนิพจน์ทางคณิตศาสตร์ในรูปสัญลักษณ์ เช่น การจัดรูป การแยกตัวประกอบ และการแก้สมการ โดยให้ผลที่แน่นอนตามกฎทางคณิตศาสตร์ SymPy [Meurer 2017] เป็น computer algebra system แบบ open source ที่เขียนด้วยภาษา Python การตรวจว่าคำตอบสองแบบเท่ากันทำได้โดยลบนิพจน์ทั้งสองแล้วจัดรูปผลต่าง ถ้าได้ศูนย์แปลว่าเท่ากัน วิธีนี้ตัดสินได้ถูกต้องแม้คำตอบจะเขียนต่างรูปกัน เช่น 2(x + 1) กับ 2x + 2 แต่ใช้ได้เฉพาะคำตอบที่แปลงเป็นนิพจน์ทางคณิตศาสตร์ได้

---

## อ้างอิงที่ใช้ในหัวข้อนี้

| key | อ้างอิง | สิ่งที่ยืนยันแล้ว (28 พ.ย.) |
|---|---|---|
| Ji 2023 | Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Chen, D., Dai, W., Chan, H. S., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*. https://doi.org/10.1145/3571730 · arXiv:2202.03629 | ✔ abstract · ❓ volume ของฉบับตีพิมพ์ |
| Bastani 2025 | Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakcı, Ö., & Mariman, R. (2025). Generative AI without guardrails can harm learning: Evidence from high school mathematics. *Proceedings of the National Academy of Sciences, 122*(26), e2422633122. https://doi.org/10.1073/pnas.2422633122 | ✔ abstract (RePEc/IDEAS): เกือบ 1,000 คน · GPT Base vs GPT Tutor · เมื่อเอา AI ออก GPT Base −17% · ไม้ค้ำ (crutch) · ⚠ abstract ไม่ได้บอกผลของ GPT Tutor หลังเอา AI ออก → ไม่เขียน |
| OWASP 2025 | OWASP. (2025). LLM01:2025 Prompt injection. *OWASP Top 10 for LLM Applications 2025*. https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | ✔ นิยาม prompt injection และ indirect prompt injection |
| Lewis 2020 | Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. arXiv:2005.11401 | ✔ abstract |
| Meurer 2017 | Meurer, A., et al. (2017). SymPy: symbolic computing in Python. *PeerJ Computer Science, 3*, e103. https://doi.org/10.7717/peerj-cs.103 | ✔ หน้า citing ของ docs.sympy.org และ sympy.org |

**ตัดออกในร่าง 2:** Frieder 2023, Greshake 2023, Lee 2025, Kusupati 2022, Liu 2023 · Google 2025 (structured output) ย้ายไป 2.4 · CROHME ไม่ใช้ (Jam 28 พ.ย.: ใช้ผล P1 พอ)

## คำถามสำหรับร่างนี้

ไม่มี
