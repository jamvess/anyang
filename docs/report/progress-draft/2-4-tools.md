# 2.4 เครื่องมือและเทคโนโลยีที่ใช้พัฒนา · ร่าง 1

## อยากเล่าอะไร (ก่อนอ่านร่าง)

- ตัวอย่างใส่หัวข้อเครื่องมือในบทที่ 2 · rubric มีเกณฑ์ Tool Selection → บอก**ทางเลือกที่พิจารณาและเหตุผลที่เลือก** ไม่ใช่แค่รายชื่อ
- เครื่องมือ AI เลือกจาก**ผลการวัดจริง** (PoC) ไม่ได้เลือกตามความนิยม → จุดแข็งของเรา
- ทางเลือกที่ไม่เคยพิจารณาจริง ไม่เขียน (ช่อง "—" หรือ ❓ ให้เจ้าของส่วนเติม)
- บอกตรงๆ ว่าใช้ Claude Code ช่วยเขียนโค้ด (Teamwork & Ethics)
- รายละเอียดสถาปัตยกรรมอยู่ใน 3.2 · ที่นี่บอกแค่ว่าใช้อะไรและทำไม

---

## 2.4 เครื่องมือและเทคโนโลยีที่ใช้พัฒนา

ทีมเลือกเครื่องมือโดยพิจารณาสามด้าน ได้แก่ ความเหมาะกับงานของระบบ ความคุ้นเคยของทีม และค่าใช้จ่ายในช่วงพัฒนา สำหรับ model ของ AI ทีมเลือกจากผลการวัดด้วย PoC (หัวข้อ 4.4) ตารางที่ 2.1 สรุปเครื่องมือหลัก ทางเลือกที่พิจารณา และเหตุผลที่เลือก

ตารางที่ 2.1 เครื่องมือและเทคโนโลยีที่ใช้พัฒนา

| ส่วน | เครื่องมือที่ใช้ | ทางเลือกที่พิจารณา | เหตุผลที่เลือก |
|---|---|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS | — | ทีมคุ้นเคย และ deploy บน Vercel ได้ง่าย |
| การแสดงสมการ | KaTeX | — | แสดงสมการ LaTeX ในบทสนทนาได้เร็ว |
| Backend | FastAPI (Python) และ Pydantic | — | ภาษา Python ใช้ SymPy และ SDK ของ AI ได้โดยตรง และ Pydantic ใช้ตรวจ structured output ของ LLM [Google 2025] |
| การส่งข้อความแบบ streaming | Server-Sent Events (SSE) | WebSocket | แชทต้องการการส่งข้อมูลทิศทางเดียวจาก server ไปยัง browser SSE จึงเพียงพอและใช้งานบน Cloud Run ได้ง่ายกว่า |
| ฐานข้อมูลและบริการพื้นฐาน | Supabase (PostgreSQL, pgvector, Auth, Storage, Row-Level Security) | — | รวมฐานข้อมูล การค้นด้วย vector การยืนยันตัวตน และการเก็บไฟล์ไว้ที่เดียว และแยกข้อมูลผู้ใช้ที่ระดับฐานข้อมูลด้วย Row-Level Security |
| Hosting | Vercel (frontend) และ Google Cloud Run (backend) | — | Cloud Run ลดจำนวน instance ถึงศูนย์ได้เมื่อไม่มีผู้ใช้ ใช้เครดิตของ Google Cloud และอยู่ใกล้ Vertex AI |
| LLM สำหรับข้อความ | Gemini 3.5 Flash ผ่าน Vertex AI | Gemini ผ่าน AI Studio · Claude (แผนเป็นผู้ให้บริการสำรอง) | ผ่านเกณฑ์ของ P2 และ P3 · ใช้ Vertex AI เพราะใช้เครดิตของ Google Cloud ได้และไม่ติดโควตาของ free tier ซึ่งจำกัด 20 คำขอต่อวัน |
| ระดับ thinking ของ LLM ในห้องติว | minimal | low | ระดับ low ใช้เวลาถึงข้อความแรก (p95) 3.87 วินาที และค่าใช้จ่าย 6.51 บาทต่อการติว ซึ่งเกินเกณฑ์ ส่วน minimal ใช้ 1.20 วินาที และ 1.73 บาทต่อการติว (P4) |
| การอ่านลายมือ | Gemini 3.5 Flash-Lite | Claude และ Mathpix (ไม่ได้ทดสอบเพราะมีค่าใช้จ่าย) | อ่านถูกร้อยละ 95.2 ของบรรทัด ผ่านเกณฑ์ร้อยละ 80 และตอบเร็ว (P1) |
| Embedding | Gemini Embedding ขนาด 768 มิติ | ขนาด 3072 มิติ · BGE-M3 (รันในเครื่อง) | ค้นหน้าที่ตอบคำถามได้ 19 จาก 20 ข้อ เทียบกับ 18 ข้อของขนาด 3072 มิติ และ 9 ข้อของ BGE-M3 (P3) |
| การตรวจคำตอบคณิตศาสตร์ | SymPy | ให้ LLM ตัดสินเอง | ตัดสินความเท่ากันทางคณิตศาสตร์ได้แน่นอน ไม่มี hallucination (หัวข้อ 2.3.5) |
| Retrieval และการควบคุม AI | เขียนเอง (AI gateway, pgvector) | LangChain, LlamaIndex | โมดูลที่เขียนเองมีขนาดเล็ก ทดสอบได้ง่าย และควบคุม prompt ได้ทั้งหมด |
| CI/CD | GitHub Actions และ Google Cloud Build | — | test ทุกครั้งที่เปิด pull request และ deploy อัตโนมัติหลัง merge |
| เครื่องมือพัฒนา | uv, Ruff, pytest, pnpm, ESLint, Vitest, Figma | — | — |
| ผู้ช่วยเขียนโค้ด | Claude Code | — | ช่วยเขียน specification, test และโค้ดตามขั้นตอน Spec-Driven และ Test-Driven Development โดยสมาชิกตรวจ test และผลงานก่อน merge ทุกครั้ง |

---

## ที่มา

| ข้อความ | ที่มา | |
|---|---|---|
| stack และเหตุผลสั้นๆ | `specs/system/architecture.md` "Tech stack (ตกลงแล้ว)" | ✔ |
| SSE แทน WebSocket · ไม่ใช้ LangChain / LlamaIndex | `CLAUDE.md` rule 7, 9 · `architecture.md` | ✔ |
| free tier 20 request/วัน → Vertex | `specs/poc/reports/P2.md` บรรทัด 54 · fact sheet I | ✔ |
| thinking low vs minimal: 3.87 s, 6.51 บาท vs 1.20 s, 1.73 บาท | `P4-lite.md` (ในเครื่อง · สมมติ 45 ข้อความต่อ session) | ⚠ ยังไม่วัดบน staging |
| P1 flash-lite 95.2% · ไม่ได้ทดสอบ Claude/Mathpix เพราะงบ | `P1.md` บรรทัด 18, 24, 38 | ✔ |
| P3b 768 = 19/20 · 3072 = 18/20 · bge-m3 = 9/20 | `P3.md` บรรทัด 44–48 | ✔ |
| Claude Code ช่วยเขียน · สมาชิก review test ก่อน implement · self-review ก่อน merge | `CLAUDE.md` "How we work" · `roles.md` Dev tools | ✔ |

## อ้างอิงที่ใช้ในหัวข้อนี้

| key | อ้างอิง | สิ่งที่ยืนยันแล้ว |
|---|---|---|
| Google 2025 | Google. (2025). Structured output. *Gemini API documentation*. https://aistudio.google.com/docs/structured-output | ✔ 28 พ.ย. "generate responses that adhere to a provided JSON Schema" · ❓ วันที่เข้าถึงใส่ตอนรวมเล่ม |

## คำถามสำหรับร่างนี้

1. **ช่องทางเลือกที่ไม่เคยเทียบจริง:** ใส่ "—" (Jam 28 พ.ย.: เล่มไทยไม่มีคอลัมน์นี้เลย ไม่ต้องรอ May และ Junior)
2. **ผู้ช่วยเขียนโค้ด:** ใส่ Claude Code (Jam 28 พ.ย.) · → 4.1 ต้องมีย่อหน้าอธิบายการตรวจ test และผลงานก่อน merge (บันทึกใน `5-1-remaining.md` แล้ว)
