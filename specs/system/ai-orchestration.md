# AI Orchestration Design (v1.1)

ฉบับ markdown สำหรับ repo ของเอกสาร AI Orchestration Design v1.0 (30 ก.ย. 2569) พร้อมการแก้ v1.1: เกณฑ์ mastery 0.95, ระดับอ่อน 0.5, ความพร้อม = Σ(r × mastery) ÷ Σr, spaced review ตาม Cepeda/SM-2, เพดาน 10 ข้อ/skill/วัน, จำนวนข้อต่อ skill จำลองจาก BKT, circuit breaker ตาม Resilience4j

**ตัวเลขทุกตัวในเอกสารนี้เป็นค่าอธิบาย ค่าจริงที่โค้ดใช้อยู่ใน `config/learning.yaml` และ `config/ai.yaml` ที่มาของแต่ละตัวอยู่ใน `learning-model.md`**



# 1. บทนำ

## 1.1 วัตถุประสงค์ของเอกสาร

เอกสารนี้อธิบาย AI orchestration ของระบบ "อ่านยัง?" ครบทุกส่วนที่มี AI เกี่ยวข้อง ได้แก่ ข้อมูลอะไรเข้า AI, AI ส่งอะไรกลับ, ส่วนไหน code เป็นคนตัดสินใจ และผลลัพธ์ถูกเก็บลงตารางไหน เพื่อให้อาจารย์ที่ปรึกษายืนยันก่อนส่ง Proposal ฉบับสมบูรณ์ และใช้เป็น **system-level design spec** สำหรับการพัฒนาแบบ Spec-Driven Development (SDD) ในเทอม 2

| สิ่งที่อาจารย์ขอ | หัวข้อในเอกสาร |
|---|---|
| 2.1 AI Buddy: algorithm ทำงานอย่างไร | 2.1 |
| 2.2 AI Tutor session: ข้อมูลที่ AI ได้, สิ่งที่คุยกับ user, รับ input หลายช่องทาง, ประเมินและติดตาม progress ใน database ไหน | 2.2, 2.4, 2.5 |
| 2.3 Content upload: เก็บที่ DB ไหน, ส่งอะไรให้ AI, ได้อะไรกลับ, user แก้ scope อย่างไร, เก็บผลที่ไหน | 2.3 |
| Flow อื่นที่เกี่ยวข้อง | 2.6 Context management, 2.7 Persona, 2.8 Voice, 2.9 Guardrails, 2.10 Model routing, 2.11 Observability |

ลำดับในเอกสารเรียงตามการไหลของข้อมูล (upload → ติว → ตรวจคำตอบ → วางแผน → buddy → infrastructure) ส่วนรหัส flow ใช้ตามที่อาจารย์กำหนด

> **สถานะ:** ทีมตกลงทุกการตัดสินใจในเอกสารนี้ร่วมกันแล้วเมื่อ 30 ก.ย. 2569 ส่วนตัวเลข threshold ต่างๆ เป็นค่าเริ่มต้นที่จะปรับตามผล Proof of Concept (ดูหัวข้อ 3.6)

## 1.2 ภาพรวม

> แผนภาพ: ภาพรวม AI orchestration ของระบบ (ดูภาพในไฟล์ AI Orchestration Design .docx)

ระบบแบ่งเป็น 3 ชั้น

- **ชั้น flow:** เตรียมข้อมูลครั้งเดียวต่อการเตรียมสอบ (2.7 persona, 2.3 upload → scope) แล้วใช้ซ้ำทุกครั้งที่เข้าห้องติว (2.2)
- **ชั้นห้องติว:** ทุก turn ผ่าน context builder (2.6), planner (2.5), answer checker (2.4), buddy (2.1) และ voice (2.8)
- **ชั้น AI Gateway:** ทุก AI call ผ่าน guardrails (2.9), routing และ fallback (2.10) และถูก log (2.11) เก็บข้อมูลทั้งหมดใน Supabase โดยแยกข้อมูลด้วย `tenant_id`

## 1.3 หลักการออกแบบ

| หลักการ | ความหมาย | เหตุผล |
|---|---|---|
| **P1 · Code ตัดสินใจ, LLM พูด** | stage การสอน, หัวข้อถัดไป, ดาว, buddy จะพูดไหม: code ตัดสินจากข้อมูลใน DB แล้วส่งเป็น directive ให้ LLM แปลงเป็นคำพูด | test ได้ (TDD), อธิบายได้, LLM ไม่หลุดแผน |
| **P2 · AI ไม่เขียน database เอง** | AI คืน structured output หรือ action จาก whitelist แล้ว code ตรวจก่อน apply | กัน hallucination และ prompt injection |
| **P3 · คณิตตัดสินด้วย math engine** | ถ้า parse ได้ ให้ SymPy เป็นคนตัดสินว่าคำตอบถูกหรือผิด | LLM ตรวจพีชคณิตหลายบรรทัดพลาดบ่อย |
| **P4 · RAG-grounded ไม่ใช่ RAG-only** | เอกสารเป็นหลักเรื่อง scope, วิธีทำ, นิยาม ส่วน internal knowledge ใช้สำหรับคำอธิบายและสร้างโจทย์ (หัวข้อ 1.4) | ได้ทั้งความถูกต้องตามรายวิชาและคุณภาพการสอน |
| **P5 · Never-compact context** | scope, ลำดับที่ตกลงกัน และ performance ถูกประกอบใหม่จาก DB ทุก turn ไม่ถูกสรุปทิ้ง | tutor ไม่ลืมแผนเมื่อบทสนทนายาว |
| **P6 · Human-in-the-loop ที่จุดเสี่ยง** | ยืนยันประเภทไฟล์, ยืนยัน scope, ยืนยันผลอ่านลายมือทุกครั้ง, แก้ transcript ก่อนส่ง, แย้งผลตรวจได้ | ความผิดพลาดของ AI ไม่ถูกใช้โดยไม่มีคนเห็น |
| **P7 · Gateway เดียว** | ทุก AI call ผ่าน `ai.call()` ที่มี guard, routing, fallback และ log | เขียนครั้งเดียว, สลับ provider หรือ fake provider ได้ |
| **P8 · Stateless** | Cloud Run ไม่เก็บ state ใน memory ทุกอย่างอยู่ใน DB | scale ได้, ออกจากห้องแล้วกลับมาต่อได้ (TM-13) |

## 1.4 Source policy: RAG-grounded

AI ไม่ได้ตอบจากเอกสารอย่างเดียว (RAG-only) และไม่ได้ตอบจากความรู้ของ model อย่างเดียว แต่ใช้กฎชัดเจนว่าข้อมูลแต่ละประเภทต้องมาจากไหน กฎนี้อยู่ใน system prompt ของ tutor ทุกครั้ง

| ประเภทข้อมูล | แหล่งที่ใช้ | พฤติกรรม |
|---|---|---|
| ขอบเขตและหัวข้อ | เอกสาร (scope ที่ยืนยันแล้ว) | ไม่สอนนอก scope ถ้า user ถามนอก scope ให้ตอบสั้นแล้วดึงกลับ |
| วิธีทำ สัญลักษณ์ ศัพท์ | เอกสาร | ใช้วิธีในชีท ถ้าจะสอนวิธีอื่นต้องถามก่อน (SM-11) |
| นิยามและข้อเท็จจริงเฉพาะวิชา | เอกสาร | ถ้าชีทไม่มี ให้บอกว่า "ในชีทไม่มี" ห้ามแต่งเอง |
| สไตล์ข้อสอบ | ข้อสอบเก่า | โจทย์ระดับยากสุดอิงข้อสอบเก่า |
| คำอธิบาย อุปมา มุมมองใหม่ | Internal knowledge | ใช้ได้ (AM-09) |
| การสร้างโจทย์ใหม่ | Internal knowledge + วิธีตามชีท | ต้องผ่าน SymPy verify ก่อนใช้ (2.4.6) |
| หัวข้อที่ user เพิ่มเอง | Internal knowledge | ติดป้าย "นอกเอกสาร" และ tutor บอก user ทุกครั้ง |
| เมื่อเอกสารน่าจะผิด | — | ไม่แก้เงียบๆ ให้บอกว่าน่าจะพิมพ์ผิด และแนะนำให้ถามอาจารย์ |

**Retrieval:** ช่องทางหลักคือ `topic_chunks` ของหัวข้อปัจจุบัน ซึ่งเป็นแบบ deterministic ส่วน vector search ใช้เฉพาะตอน user ถามคำถามอิสระและตอนตรวจว่าคำถามอยู่นอก scope ไหม ไม่ส่งเอกสารทั้งก้อนเข้า long context เพราะแพงและทำให้ model เสียโฟกัส

**ความต่างตามวิชา:** คณิตศาสตร์พึ่ง internal knowledge มากกว่า (เนื้อหามาตรฐาน) ส่วน Database และฟิสิกส์พึ่งเอกสารมากขึ้น (นิยามและสัญลักษณ์ของผู้สอน) และวิชาภาษา (LNG) พึ่งเอกสารเกือบทั้งหมด

## 1.5 คำศัพท์

| คำ | ความหมาย |
|---|---|
| Exam prep | การเตรียมสอบ 1 ครั้ง ประกอบด้วยวิชา วันสอบ และไฟล์ |
| Material | ไฟล์ที่ upload เช่น ชีท สไลด์ ข้อสอบเก่า โน้ต |
| Topic | หัวข้อที่ต้องสอบ สกัดจากเอกสาร มีดาว 0–3 |
| Skill | ประเภทโจทย์ย่อยในหัวข้อ เช่น "ผลต่างกำลังสอง" ในหัวข้อการแยกตัวประกอบ (ไม่แสดงใน UI แต่แก้ผ่าน chat ได้) |
| Scope version | snapshot ของรายการหัวข้อที่ user ยืนยันแล้ว |
| Stage | สถานะการสอนของหัวข้อ: Probe, Teach, Verify, Practice, Done, Park |
| Directive | คำสั่งที่ code ส่งให้ LLM ว่า turn นี้ต้องทำอะไร |
| Attempt | การตอบโจทย์ 1 ครั้ง พร้อมผลตรวจ |
| Mastery | ความน่าจะเป็นว่า user เข้าใจหัวข้อแล้ว คำนวณด้วย BKT มีค่า 0–1 |
| Error type | 6 ประเภท: calculation, sign, wrong method, concept, prerequisite, no answer |
| Tenant | หน่วยแยกข้อมูลและโควตา ใน v1 คือนักเรียน 1 คน (personal tenant) |
| SSE | Server-Sent Events: server stream ข้อความทีละส่วนไปที่ browser |
| Tier | ขนาดของ model: small, mid, main, vision, embed |
| TTFT | Time to first token: เวลาตั้งแต่ user ส่งจนเห็นตัวอักษรแรกของคำตอบ |


# 2. AI Orchestration Flows

## 2.3 Content upload → Scope

### 2.3.1 ภาพรวม

แปลงไฟล์ของ user เป็นรายการหัวข้อพร้อมดาว skills และความเชื่อมโยงกับเนื้อหาต้นฉบับ (เลขหน้า) จากนั้นให้ user แก้และยืนยันก่อนนำไปใช้ติว flow นี้ใช้ AI หนักที่สุด แต่เกิดครั้งเดียวต่อการเตรียมสอบ

> แผนภาพ: Flow 2.3 Content upload → Scope (สีม่วง = user, สีเขียว = AI call, สีเทา = code) (ดูภาพในไฟล์ AI Orchestration Design .docx)

### 2.3.2 Input และ output ของแต่ละขั้น

| ขั้น | Input | Output | เขียนลงที่ |
|---|---|---|---|
| 1 · Upload (S09) | ไฟล์ + note รายไฟล์ | ไฟล์อยู่ใน Storage | Storage `materials/{tenant}/{exam_prep}/{id}`<br>แถวใหม่ใน `materials` (status `uploaded`) |
| 2 · Classify | ชื่อไฟล์ + 3 หน้าแรก + note | `kind`, `confidence`, `relevance_weight` | `materials` |
| 3 · Confirm (S10) | ค่าที่ AI เดา | `kind` ที่ยืนยันแล้ว แล้วเริ่ม job | `materials.kind_confirmed` |
| 4 · Ingest | ไฟล์เต็ม | ข้อความรายหน้า, chunk + vector, ข้อสอบเก่าแยกรายข้อ | `material_pages`, `chunks`, `past_exam_questions` |
| 5 · Topics | chunk ทุกไฟล์ + ข้อสอบรายข้อ + note | หัวข้อที่เรียงลำดับแล้ว + skills + ดาว + ที่มา | `topics`, `topic_skills`, `topic_chunks`, `past_exam_questions.topic_id` |
| 6 · Edit (S13) | ข้อความ user + รายการหัวข้อปัจจุบัน | action ที่ code ตรวจแล้ว | `topics` (draft), `scope_changes` |
| 7 · Confirm (S14) | สรุปการเปลี่ยนแปลง | scope ถูก lock | `scope_versions` (snapshot), `exam_preps.active_scope_version_id` |

ความคืบหน้าของทุกขั้นถูกเขียนลง `ingestion_jobs` หน้า S11 อ่านจากตารางนี้เพื่อแสดงความคืบหน้าทีละขั้น

### 2.3.3 ขั้น 4 · Ingest

**Extract ตามชนิดไฟล์** (ทุกแบบต้องได้ `page_no` ติดมาด้วย)

- PDF ที่มี text layer ใช้ PyMuPDF **แต่ต้องเช็คคุณภาพของข้อความก่อน** · ไฟล์สแกนมักมี OCR layer ภาษาอังกฤษซ่อนอยู่ ซึ่งดูเหมือนมีข้อความแต่เป็นขยะ · PoC P3 ใช้สัดส่วนตัวอักษรไทยต่อตัวอักษรทั้งหมด < 30% = ไฟล์สแกน (MTH10101: ข้อสอบสแกน 0%, ชีท 48–85%)
- PDF สแกนหรือไฟล์รูป ส่ง vision model อ่าน (A2 ทีละหน้า หรือ A2b ทั้งไฟล์) · **P3:** A2b อ่านข้อสอบสแกน 14 หน้าใน 40.5 วินาที และ A4 ตัดรายข้อตรง label 43/43 จึงไม่ใช้ Google Document AI (`specs/poc/reports/P3.md`)
- ข้อจำกัดของ PyMuPDF ที่เจอใน P3: สมการจาก Equation Editor ของ Word ออกมาเป็นตัวอักษรกระจายทีละบรรทัด และสัญลักษณ์ ∞ หายไป ข้อความภาษาไทยอ่านได้แต่สระอำแตก (`น ามา`)
- PPTX อ่านทีละสไลด์, DOCX อ่านทีละหัวข้อ

**Chunk**

- ชีทและโน้ต ตัดตามหัวข้อหรือสไลด์ ขนาดประมาณ 400–800 tokens ห้ามคร่อมเกิน 2 หน้า
- **นับ token ภาษาไทยที่ประมาณ 1.7 ตัวอักษรต่อ token** (P3b วัดด้วย `count_tokens` ของ `gemini-embedding-2` ได้ 1.47–1.82) ไม่ใช่ 3–4 แบบภาษาอังกฤษ ถ้าใช้ค่าภาษาอังกฤษ chunk จะใหญ่เกินจริงเกือบ 2 เท่า · MTH10101 ตัดได้ 116 chunk (median 486 token, ไม่มีอันไหนเกิน 800)
- ข้อสอบเก่า **ใช้ AI ตัดรายข้อ** ไม่ตัดตามความยาว เพราะต้องนำไปจับคู่กับหัวข้อทีละข้อ

**Embed** แบบ batch และเก็บ `text` กับ `content_hash` ไว้คู่กับ vector เสมอ เพื่อให้ re-index ได้หากเปลี่ยน embedding model

- **Model:** `gemini-embedding-2` ที่ 768 มิติ (`config/ai.yaml` → `embedding.dimensions` ส่งเป็น `output_dimensionality`) · P3b: recall@4 95% ที่ 768 มิติ เทียบกับ 90% ที่ 3,072 มิติ และ 45% ของ `bge-m3` · ตรงกับ `chunks.embedding vector(768)`
- **ทีละข้อความ:** embedding-2 เป็น model แบบ multimodal ถ้าส่ง string หลายอันใน request เดียวจะได้ vector เดียวรวมกัน provider จึงต้องห่อแต่ละข้อความเป็น `Content` แยกกัน
- **ขนาด batch:** embedding-2 รับรวมไม่เกิน 8,192 token ต่อ request และ chunk ยาวได้ถึง 800 → `embedding.batch_size: 10`
- **ตรวจขนาด:** gateway แจ้ง error ถ้า vector ยาวไม่เท่า `embedding.dimensions` (ไม่ตัดหรือเติมให้เอง)
- **ค้นด้วย cosine** (`<=>`, HNSW `vector_cosine_ops`) · Gemini ไม่ normalize vector ที่ต่ำกว่า 3,072 มิติ ถ้าเปลี่ยนไปใช้ inner product ต้อง normalize ก่อนเก็บ
- Gemini API ไม่บอกจำนวน token ของ embedding → `ai_calls.tokens_in` ของ purpose `embed` เป็น 0 จนกว่าจะย้ายไป Vertex AI (AI-04)

### 2.3.4 ขั้น 5 · Topic extraction

| ขั้นย่อย | ผู้ทำ | ทำอะไร |
|---|---|---|
| 5a Map | AI (A5) | ทีละไฟล์ชีท ส่ง chunk ที่มีป้าย `[p.5]` ติดอยู่ ได้หัวข้อของไฟล์นั้นพร้อมเลขหน้า |
| 5b Merge | AI (A6, main) | รวมหัวข้อจากทุกไฟล์ + note ได้หัวข้อกลางที่ไม่ซ้ำกัน เรียงตาม prerequisite พร้อม **skills ของแต่ละหัวข้อ** และ **common mistakes ของแต่ละ skill** |
| 5c Map ข้อสอบ | AI (A7) | ข้อสอบเก่าทีละข้อ ระบุ `topic_id`, `skill_id` และ **กับดัก (trap)** ถ้ามี |
| 5d คำนวณ | **Code** | คำนวณดาว, `exam_freq` ของ skill และสร้าง `topic_chunks` จากช่วงหน้าของแต่ละหัวข้อ เรียงด้วย vector similarity |

เหตุผลที่แบ่งเป็น map → merge แทนการส่งทีเดียว

- เลขหน้าอ้างอิงแม่นกว่า
- ไฟล์ใหญ่ไม่ล้น context
- เมื่อเพิ่มไฟล์ภายหลัง ทำ map แค่ไฟล์ใหม่แล้ว merge ใหม่

### 2.3.5 สูตรดาว (code คำนวณ ไม่ให้ AI เดา)

- `w` = น้ำหนักของข้อสอบเก่าแต่ละชุด ค่าปกติ 1.0 ถ้า note บอกว่าคนละอาจารย์ให้ 0.5 (ได้ค่าจากขั้น 2)
- `r` = ผลรวม `w` ของชุดที่หัวข้อนี้ออก ÷ ผลรวม `w` ทั้งหมด
- ★★★ เมื่อ `r ≥ 0.6`
- ★★ เมื่อ `0 < r < 0.6` หรือเป็นพื้นฐาน (prerequisite) ของหัวข้อ ★★★
- ★ เมื่อไม่เคยออกเลย
- ตัดออก (0) เมื่อ user หรือ note บอกว่าไม่ออก
- ถ้าไม่มีข้อสอบเก่าเลย ใช้สัดส่วนจำนวนหน้าแทน
- เหตุผลที่แสดงให้ user สร้างจาก template เช่น "ออกในข้อสอบเก่า 2 ใน 2 ชุด"

### 2.3.6 ขั้น 6–7 · แก้และยืนยัน scope

LLM ไม่แตะ database โดยตรง แต่คืน JSON ในรูปแบบนี้

```
{ "reply": "ปรับการจัดกลุ่มเป็น 3 ดาวแล้ว ที่ให้ดาวน้อยตอนแรกเพราะ...",
  "actions": [{ "op": "set_importance", "topic_id": "t_07", "value": 3,
                "reason": "user: อาจารย์เน้นมาก" }] }
```

- op ที่อนุญาต: `set_importance`, `exclude`, `include`, `rename`, `reorder`, `add_topic`, `exclude_skill`, `include_skill`
- code ตรวจว่า `topic_id` มีอยู่จริง ค่าอยู่ในช่วงที่กำหนด และ op อยู่ใน whitelist
- ถ้าผ่าน: apply ลง draft แล้วเขียน `scope_changes` และส่ง SSE event `scope_patch` ให้การ์ดใน UI เปลี่ยนทันที
- ถ้าไม่ผ่าน: ไม่ apply และให้ AI ถาม user ใหม่
- Skills ไม่แสดงในหน้า S12 แต่ user สั่งผ่าน chat ได้ เช่น "กำลังสามไม่ออก" → `exclude_skill`
- หัวข้อที่ user เพิ่มเองได้ `origin = user` และติดป้าย "นอกเอกสาร"
- ถ้าเพิ่มไฟล์หลังยืนยันแล้ว ระบบเปิด draft ใหม่และให้ยืนยันอีกครั้ง โดยแสดงเฉพาะส่วนที่เปลี่ยน

### 2.3.7 AI calls ใน flow นี้

| # | Call | Tier | Output schema | ความถี่ |
|---|---|---|---|---|
| A1 | `classify_material` | small | `{kind, confidence, relevance_weight, reason}` | 1 ครั้ง/ไฟล์ |
| A2 | `vision_extract` | vision | `{text, latex_blocks, notes}` | เฉพาะหน้าสแกนหรือรูป |
| A2b | `vision_extract_pages` | vision | `{pages: [{page, text}], notes}` | 1 ครั้ง/ไฟล์สแกน (ทุกหน้าใน call เดียว · เพิ่มใน PoC P3) |
| A3 | `embed` | embed | vector | 1 ครั้ง/chunk |
| A4 | `split_past_exam` | small | `{questions: [{q_no, text, page, points}], notes}` | 1 ครั้ง/ข้อสอบเก่า |
| A5 | `extract_topics_local` | mid | `{topics: [{name, pages, prereq_hint}], notes}` | 1 ครั้ง/ไฟล์ชีท |
| A6 | `merge_topics` | **main** | `{topics: [{id, name, order, sources, prereqs, excluded_by_note, skills: [{id, name, common_mistakes: [{text, error_type}]}]}], notes}` | 1 ครั้ง/การเตรียมสอบ |
| A7 | `map_questions` | small | `{mappings: [{q_id, topic_id, skill_id, trap, note}]}` | batch |
| A8 | `scope_edit` | mid | `{reply, actions[]}` | ทุกข้อความที่ user แก้ |

A5: `pages` เป็นช่วง `"start-end"` ตามป้าย `[p.N]` (เลขหน้า PDF) · `prereq_hint` อาจเป็นหัวข้อที่อยู่ในไฟล์อื่น ให้ A6 จับคู่กับหัวข้อจริงหรือทิ้งไป · `notes` ใช้บอกเหตุผลเมื่อไฟล์ไม่มีเนื้อหาที่อ่านได้ (เช่นไฟล์สแกนที่มีข้อความขยะ)

ทุก output มี `notes` และเป็น object ไม่ใช่ array (structured output เสถียรกว่า) · Pydantic model อยู่ใน `apps/api/app/models/scope_ai.py` และตรวจกฎเหล่านี้ด้วย ถ้าผิดจะถูกส่งกลับให้ model แก้ (AI-05)

- A2b: เพิ่มใน PoC P3 เพราะ free tier ได้ 20 request ต่อวันต่อ model ทำทีละหน้าไม่ไหว · `page` ต้องเรียง 1..n ครบตามจำนวนรูป · จะใช้แทน A2 ในระบบจริงหรือไม่ ตัดสินจากผล P3
- A4: `q_no` แบบ `ก1.2` / `ข3` / `3.2` ไม่ซ้ำกัน · ข้อย่อยที่มีคำนำร่วมกันต้องใส่คำนำในทุกข้อย่อย · `points` เป็น `null` ได้
- A6: `sources` = ช่วงหน้า `<file>:<start>-<end>` ของหัวข้อ ใช้สร้าง `topic_chunks` ในขั้น 5d และแสดงที่มา (SM-04) · `prereqs` ต้องเป็น id ในรายการ ห้ามวน และต้องมาก่อนใน `order` · skill id ขึ้นต้นด้วย id ของหัวข้อ · `error_type` เป็นได้ 5 ค่า (ไม่มี `no_answer`) · `excluded_by_note` จาก note ของ user
- A7: `topic_id` + `skill_id` เป็น `null` ทั้งคู่ได้เมื่อไม่มีหัวข้อไหนเข้า (พร้อม `note`) · skill ต้องเป็นของหัวข้อที่เลือก

ทุก purpose ของ flow นี้ตั้ง `thinking` ใน `config/ai.yaml` (Gemini 3 นับ thinking token รวมใน `max_tokens`)

ทุก call ผ่าน AI Gateway (2.9–2.11), ตรวจ schema ด้วย Pydantic และ log ลง `ai_calls`

### 2.3.8 API

1. `POST /exam-preps/{id}/materials` → คืน `material_id` + signed upload URL
2. `PUT {signed_url}` → browser ส่งไฟล์เข้า Storage โดยตรง
3. `POST /materials/{id}/uploaded {user_note}` → 202 เริ่ม classify
4. `GET /exam-preps/{id}/materials` → ค่าที่ AI เดา + สถานะ
5. `POST /exam-preps/{id}/materials/confirm` → 202 เริ่ม ingest และ extract topics
6. `GET /exam-preps/{id}/ingestion` → ความคืบหน้าทีละขั้น
7. `GET /exam-preps/{id}/scope` → หัวข้อ draft + ดาว + เหตุผล
8. `GET /topics/{id}/sources` → ข้อความต้นฉบับ + เลขหน้า
9. `POST /exam-preps/{id}/scope/chat` → SSE: `token`, `scope_patch`, `done`
10. `GET /exam-preps/{id}/scope/changes` → change log สำหรับหน้า S14
11. `POST /exam-preps/{id}/scope/confirm` → lock version

### 2.3.9 การตัดสินใจเชิงออกแบบ

1. **แยก classify ก่อน ingest** เพราะประเภทไฟล์กำหนดวิธี chunk (ข้อสอบเก่าต้องตัดรายข้อ) และกำหนดน้ำหนักข้อสอบ
2. **AI ให้สัญญาณ ส่วน code คำนวณดาว** ผลทำซ้ำได้ อธิบายได้ และเขียน test ได้
3. **มีตาราง** `topic_chunks` ตอนติว tutor ดึงเนื้อหาตามหัวข้อก่อน แล้วใช้ vector search เป็นตัวเสริม เป็นกลไกหลักในการคุม scope
4. **AI ไม่เขียน database เอง** ทุกการแก้ต้องผ่าน action ใน whitelist
5. **กัน prompt injection จากไฟล์ที่ upload 3 ชั้น:** (1) เนื้อหาไฟล์ถูกครอบด้วย `<document>` และประกาศว่าเป็นข้อมูล ไม่ใช่คำสั่ง (2) output ต้องตรง schema (3) user ต้องยืนยัน scope ก่อนใช้
6. **Job แยกต่อไฟล์และรันซ้ำได้ (idempotent)** รันใหม่จะลบ chunk เดิมของไฟล์นั้นแล้วสร้างใหม่


## 2.2 AI Tutor session

### 2.2.1 ภาพรวม

หลักของ flow นี้คือ **code ตัดสินใจเรื่องการสอน ส่วน LLM ทำหน้าที่พูด** การเลือกหัวข้อ, stage ปัจจุบัน และการเปลี่ยนเรื่อง ล้วนตัดสินด้วย code จากข้อมูลใน DB แล้วส่งให้ LLM เป็น directive

> แผนภาพ: สิ่งที่เกิดขึ้นในหนึ่ง turn ของห้องติว (ดูภาพในไฟล์ AI Orchestration Design .docx)

### 2.2.2 การเปิด session

1. User กดเข้าห้องติว ระบบสร้าง row ใน `tutor_sessions` ผูกกับ `scope_version` ที่ยืนยันแล้ว (scope ไม่เปลี่ยนกลาง session)
2. Planner (2.5) สร้างแผนวันนี้จาก progress, ดาว, วันที่เหลือ และรอบทวน
3. Backend ส่ง SSE event `progress_card` ซึ่งเป็น **dashboard ย่อที่ render จาก DB โดยตรง ไม่ผ่าน LLM** ตัวเลขจึงไม่มีทางถูกแต่งขึ้น
4. Tutor เขียนสรุป 2–3 ประโยคจาก facts ที่ code คำนวณไว้ (ไม่ต้องคิดเอง) แล้วส่งโจทย์ข้อแรกต่อทันทีโดยไม่ต้องรอ user ตอบ
5. ถ้า user อยากเปลี่ยนแผน ก็พิมพ์บอกได้ intent router จับเป็น command และ planner คิดแผนใหม่

> แผนภาพ: ตัวอย่างข้อความเปิดห้องติว: progress card + สรุป + โจทย์ข้อแรก (ดูภาพในไฟล์ AI Orchestration Design .docx)

**ระดับความเก่ง 4 ขั้น** (แสดงใน card)

| ระดับ | เงื่อนไข |
|---|---|
| ยังไม่เริ่ม | ยังไม่มี attempt ในหัวข้อนี้ |
| อ่อน | mastery < `bkt.weak_below` (0.5) |
| กำลังดี | mastery ≥ 0.5 แต่ยังไม่ครบเงื่อนไข Done |
| ผ่าน | ครบเงื่อนไข Done (2.2.4) |

**ความพร้อม (%)** = Σ(r × mastery) ÷ Σr โดย r คือสัดส่วนที่หัวข้อออกในข้อสอบเก่า (2.3.5) และ mastery มาจาก BKT (หัวข้อที่ตัดออกไม่นับ) ความหมายคือ "สัดส่วนของเนื้อหาข้อสอบที่คาดว่าทำได้" ไม่มีตัวเลขตั้งเองเพิ่ม (learning-model.md §5) ใต้ตัวเลขมีคำอธิบายสั้นๆ เพื่อไม่ให้ถูกอ่านเป็นคะแนนสอบ

**Facts ที่ส่งให้ tutor** (directive `open_session`)

```
{ "days_left": 12, "passed": 2, "total": 6, "readiness": 0.46,
  "changed": [{"topic": "แยกตัวประกอบ", "from": "อ่อน", "to": "กำลังดี"}],
  "missing_skills": {"แยกตัวประกอบ": ["กำลังสาม", "จัดกลุ่ม"]},
  "concern": {"topic": "สมการกำลังสอง", "stars": 3, "level": "อ่อน"},
  "review_due": ["ฟังก์ชันและโดเมน"],
  "plan_today": ["review:t_03", "t_01", "t_02"] }
```

- Session แรก: card แสดงทุกหัวข้อเป็น "ยังไม่เริ่ม" ตามลำดับที่ตกลงกัน ใช้เป็นการทวนแผนไปในตัว
- Card เก็บใน `messages` (role `card`, content เป็น jsonb snapshot) ย้อนดูแชทเก่าจะเห็นสถานะ ณ วันนั้น
- User ขอดูความคืบหน้าระหว่างติวได้ ("ขอดูความคืบหน้า") ใช้ card เดียวกัน (TM-11)

### 2.2.3 ข้อมูลที่ AI ได้ในแต่ละ turn

ประกอบใหม่จาก DB ทุก turn (P5, P8) เรียงจาก static ไป dynamic เพื่อให้ได้ประโยชน์จาก prompt caching (2.6)

| # | Layer | เนื้อหา | มาจาก | ~Tokens | สรุปทิ้งได้ |
|---|---|---|---|---|---|
| 1 | System | บทบาท, teaching rules, source policy (1.4), รูปแบบ output | code constant | 500 | ไม่ |
| 2 | Persona | params ของ tutor และ buddy (2.7) + ชื่อเล่น user | `tutor_profiles`, `buddy_profiles` | 150 | ไม่ |
| 3 | Scope | รายการหัวข้อ + ดาว + ลำดับที่ตกลงกัน + สถานะ | `scope_versions.snapshot` | 250 | **ไม่** |
| 4 | Performance | mastery รายหัวข้อ, skill coverage, error_type ที่พบบ่อย, 3 attempts ล่าสุด | `topic_progress`, `attempts` | 200 | **ไม่** |
| 5 | Exam context | วันที่เหลือ, เวลาของ session ที่เหลือ | `exam_preps`, `tutor_sessions` | 30 | ไม่ |
| 6 | Directive | stage + สิ่งที่ต้องทำใน turn นี้ + buddy scene (ถ้ามี) | planner (code) | 80 | — |
| 7 | Grounding | `topic_chunks` ของหัวข้อปัจจุบัน 3–4 ก้อน + ข้อสอบเก่าของหัวข้อ | `topic_chunks`, `past_exam_questions` | 1,100 | เปลี่ยนตามหัวข้อ |
| 8 | Checker result | ผลตรวจคำตอบล่าสุด (ถ้า turn นี้เป็นการตอบ) | `attempts` | 80 | — |
| 9 | Conversation | running summary + 8 turns ล่าสุด | `tutor_sessions`, `messages` | 800 | ได้ |
| 10 | Input | ข้อความ user ที่ normalize แล้ว | — | 50 | — |

รวมประมาณ 3,200 tokens ต่อ turn ตัวอย่าง directive:

```
{ "stage": "teach", "topic_id": "t_04", "skill_id": "s_12",
  "do": "explain_error", "error_type": "sign", "first_wrong_line": 2,
  "then": "give_problem", "problem_id": "p_221",
  "buddy_scene": null }
```

### 2.2.4 สิ่งที่ tutor พูด: stage ของแต่ละหัวข้อ

> แผนภาพ: Stage machine ของการสอนหนึ่งหัวข้อ (ดูภาพในไฟล์ AI Orchestration Design .docx)

| Stage | Tutor พูดอะไร | ห้ามทำ |
|---|---|---|
| Probe | ส่งโจทย์ 1 ข้อเลย ("ลองข้อนี้ดูก่อน") ถ้า user บอกว่ายังไม่เคยเรียน ให้ข้ามไป Teach | บรรยายทฤษฎียาว |
| Teach | ชี้บรรทัดแรกที่ผิด อธิบายตาม error_type ด้วยวิธีเดียวกับชีท | ให้ hint แล้วให้ลองเอง, ถาม "งงตรงไหน" |
| Verify | โจทย์ skill เดิม เปลี่ยนแค่ตัวเลขหรือรูปแบบ | โจทย์ยากขึ้น |
| Practice | ไล่ skill ที่ยังไม่ครอบคลุม ยากขึ้นจนถึงระดับข้อสอบ อ้างข้อสอบเก่าได้ | — |
| Done | ชม 1 ประโยค แล้วบอกหัวข้อถัดไปพร้อมเหตุผล | สรุปยาว |
| Park | บอกว่าจะกลับมาเรื่องนี้ทีหลัง หรือพาไปทวนพื้นฐาน (prerequisite) ก่อน | ทำให้ user รู้สึกว่าล้มเหลว |

**เงื่อนไข Done** (ต้องครบทุกข้อ)

- ทุก skill ที่เคยออกสอบ (`exam_freq > 0`) มี independent correct อย่างน้อย 1 ครั้ง ถ้าไม่มีข้อสอบเก่าเลย ให้นับทุก skill
- mastery ของหัวข้อ ≥ `bkt.mastery_threshold` (0.95 = ถูก 3 ข้อติดจากค่าเริ่มต้น)
- หัวข้อ ★★★ ต้องมีข้อที่ถูกล่าสุดอยู่ที่ระดับข้อสอบ (difficulty 3) ส่วนใน Tight mode หัวข้อ ★★ ผ่านที่ difficulty 2 ได้ (2.5.2)

ด้วยเงื่อนไขนี้ จำนวนโจทย์จะปรับตามความกว้างของหัวข้อเอง หัวข้อที่มี 1 skill ใช้ประมาณ 2 ข้อ ส่วนหัวข้อที่มี 5 skills ใช้อย่างน้อย 5–7 ข้อ Teach/Verify loop ทำงานระดับ skill: ผิดที่ skill ไหน ก็สอนและ verify skill นั้น ไม่ต้องเริ่มหัวข้อใหม่ทั้งหมด

**Park** เกิดเมื่อผิดครั้งที่ 3 ใน skill เดียวกัน หรือทำ skill เดียวเกิน 10 ข้อในวันเดียวโดยยังไม่ผ่าน (Beck & Gong 2013) ถ้า error_type ล่าสุดคือ prerequisite ให้ push หัวข้อพื้นฐานขึ้นมาก่อน นอกนั้นให้กลับมาทำใน session ถัดไป

**การสอนตาม error type**

- **calculation, sign:** ชี้จุดเดียว บอกค่าที่ถูก แล้วไป Verify ทันที
- **wrong method:** อธิบายว่าทำไมวิธีนี้ใช้กับโจทย์แบบนี้ไม่ได้ แล้วสาธิตวิธีตามชีท
- **concept:** อธิบาย concept ใหม่ ถ้าต้อง Teach ครั้งที่สอง ใช้มุมใหม่ (AM-09)
- **prerequisite:** ถ้าผิดซ้ำ ไป Park แล้วพาไปทวนหัวข้อพื้นฐาน
- **no answer:** ทำ step แรกให้ดู แล้วให้ user ทำต่อจากตรงนั้น

**ที่มาของโจทย์:** เมื่อ directive ต้องการโจทย์ใหม่ code เรียก `generate_problem` ก่อน (structured output: โจทย์, เฉลย, solution steps, difficulty, skill, answer_format) แล้วเก็บลง `problems` จากนั้น tutor จึงพูดครอบโจทย์นั้น ผลคือ **โจทย์ทุกข้อมีเฉลยที่ verify แล้วอยู่ใน DB ก่อนถึงมือ user** (2.4.6)

**เมื่อ user พิมพ์สิ่งที่ไม่ใช่คำตอบ** (intent router)

| Intent | ระบบทำอะไร |
|---|---|
| `answer` | ส่งเข้า answer checker (2.4) |
| `question_on_topic` | ตอบจาก grounding แล้วกลับมาที่โจทย์ที่ค้างอยู่ |
| `question_off_scope` | vector search ไม่พบในเอกสาร บอกว่านอกชีท ตอบสั้น ถามว่าอยากเพิ่มเป็นหัวข้อไหม แล้วดึงกลับ (SM-10) · ถ้าตกลง บันทึกเป็น `add_topic` ใน draft ใหม่ของ scope (2.3.6) มีผลตั้งแต่ session ถัดไป เพราะ scope ไม่เปลี่ยนกลาง session (2.2.2) |
| `command` | เปลี่ยนเรื่อง, พอแค่นี้, ขอยากขึ้น, ดูความคืบหน้า, mute buddy: planner ปรับตาม |
| `dispute` | user แย้งผลตรวจ (2.4.7) |
| `teach_back` | user อธิบายให้ buddy ฟัง (2.1) tutor ให้ feedback สั้นๆ ไม่นับเข้า mastery |
| `off_topic` / `emotion` | buddy ตอบ 1 ประโยค (2.1.7) แล้ว tutor ดึงกลับ |
| `distress` | ตอบด้วย template ที่ดูแลความรู้สึก พร้อมสายด่วนสุขภาพจิต 1323 (2.9) |

### 2.2.5 Input หลายช่องทาง

| ช่องทาง | Pipeline | จุดยืนยัน |
|---|---|---|
| พิมพ์ | ส่งตรง มี KaTeX preview เมื่อมีสูตร | ไม่มี |
| พูด | กดค้างอัด (≤ 60 วินาที) → Storage → Google STT → transcript ลงช่องพิมพ์ | user แก้แล้วกดส่งเอง **ไม่ auto-send** |
| รูป | upload ลง Storage → `extract_answer` (vision) ได้คำตอบรายบรรทัดเป็น LaTeX พร้อม confidence | แสดง "อ่านได้แบบนี้ ถูกไหม" **ทุกครั้ง** (`ocr.always_confirm`) |

- เหตุผลที่รูปต้องยืนยันทุกครั้ง: PoC P1 พบว่า confidence ที่ model ให้ตัวเองแยกบรรทัดที่อ่านผิดไม่ได้ (บรรทัดผิดอยู่ที่ 0.85–0.98) และพบกรณีที่ model แก้คำตอบผิดของนักเรียนให้ถูกเอง ซึ่งจะทำให้ checker ตัดสินว่าถูก (`specs/poc/reports/P1.md`)
- รูปพร้อมข้อความกำกับ: ข้อความเป็นคำบรรยายของรูป อยู่ใน conversation ให้ tutor เห็น แต่ไม่ส่งเข้า `extract_answer` และ checker · ผลตรวจใช้แค่บรรทัดที่ user ยืนยันแล้ว (api.md · PR #45)
- เหตุผลที่เสียงไม่ auto-send: คณิตที่พูดออกมา (เช่น "x กำลังสองลบสี่") STT มักพลาด ถ้าตรวจผิดเพราะอ่านผิด user จะหมดความเชื่อใจ ให้ user แก้ก่อนส่งจึงคุ้มกว่า
- ข้อความที่พิมพ์หรือพูดเป็นคณิต ถูกแปลงเป็น LaTeX ด้วย small model (`normalize_math`) ก่อนเข้า checker
- Optimization: ถ้ามีโจทย์ค้างอยู่และ user ส่งรูปมา ให้ถือเป็นคำตอบทันทีโดยไม่เรียก intent router
- ฝั่ง output: tutor อ่านออกเสียงได้ด้วย TTS (2.8)

### 2.2.6 การประเมินและติดตาม progress

| Table | Columns หลัก | เขียนเมื่อ |
|---|---|---|
| `tutor_sessions` | tenant_id, user_id, exam_prep_id, scope_version_id, current_topic_id, stage, running_summary, summary, buddy_muted, started_at, ended_at, end_reason | เริ่ม, ทุก turn, จบ |
| `messages` | session_id, role (user / tutor / buddy / card), content, input_mode (text / voice / image), attachment_path, extracted_text, intent | ทุกข้อความ |
| `problems` | session_id, topic_id, skill_id, source (generated / past_exam / doc), source_ref, text, reference_answer, solution_steps, answer_format, verified, difficulty 1–3, purpose (probe / verify / practice / review) | ก่อนส่งโจทย์ |
| `attempts` | problem_id, user_id, topic_id, skill_id, answer_text, verdict, is_correct, error_type, first_wrong_line, evidence, method, decided_by, confidence, independent, overridden | ทุกครั้งที่ตอบ |
| `topic_progress` | user_id, exam_prep_id, topic_id, mastery, level, stage, skill_coverage (jsonb), attempts_n, correct_n, error_counts (jsonb), fail_streak, review_step, next_review_at, parked_reason, parked_at, last_seen_at | หลัง attempt |

**Mastery: Bayesian Knowledge Tracing (BKT)** แบบ fixed parameters ซึ่งตรงกับทฤษฎีที่อ้างไว้ใน Proposal บทที่ 2

- p_init 0.3, p_transit 0.15, p_guess 0.2, p_slip 0.1 ค่าและที่มาอยู่ใน `config/learning.yaml` และ learning-model.md §1 (p_init, p_transit fit ใหม่ด้วย pyBKT หลัง Alpha)
- update เฉพาะ attempt ที่ `independent = true` คือไม่ได้ทำตามสิ่งที่ tutor เพิ่งสาธิตใน turn เดียวกัน
- `skill_coverage` เก็บ `{skill_id: correct_count}` ใช้ตรวจเงื่อนไข Done
- `error_counts` เก็บแยก 6 ประเภท ใช้ใน prompt layer 4 และแสดงเมื่อ user ขอ

**ลำดับการเขียน DB ใน 1 turn ที่เป็นการตอบ:** `messages` (user) → `attempts` → `topic_progress` → `tutor_sessions` → `problems` (ถ้ามีโจทย์ใหม่) → `messages` (tutor, buddy) → `ai_calls`

### 2.2.7 AI calls ต่อ turn

| Call | Tier | เมื่อไหร่ |
|---|---|---|
| `route_intent` | small | input เป็น text/voice และไม่แน่ชัดว่าเป็นคำตอบ |
| `extract_answer` | vision | input เป็นรูป |
| `normalize_math` | small | คำตอบที่พิมพ์หรือพูดเป็นคณิต |
| `check_answer` | mid | เป็นคำตอบ (2.4) |
| `generate_problem` | mid | directive ต้องการโจทย์ใหม่ที่ไม่ได้มาจากข้อสอบเก่า |
| `tutor_reply` | main | ทุก turn (stream) รวมฉาก buddy ถ้ามี |
| `update_running_summary` | small | ทุก 8 turns (`session.context_recent_turns`) ทำเบื้องหลังหลังตอบ user แล้ว |

โดยเฉลี่ย 2–4 calls ต่อ turn ส่วนต้นทุนดูที่ 2.10

### 2.2.8 SSE events และ API

**SSE events:** `progress_card`, `token` (แยกตาม speaker), `problem` (การ์ดโจทย์ render KaTeX), `ocr_preview` (ต้องยืนยัน), `verdict` (✓/✗), `buddy`, `session_end`, `done`

| API | ทำอะไร |
|---|---|
| `POST /exam-preps/{id}/sessions` | สร้าง session แล้ว stream progress card + ข้อความเปิดห้อง |
| `POST /sessions/{id}/uploads` | ขอ signed URL สำหรับรูปหรือเสียง |
| `POST /sessions/{id}/transcribe` | เสียง → text (ใส่ช่องพิมพ์) |
| `POST /sessions/{id}/messages` (SSE) | ส่ง `{text}` หรือ `{image_path}` แล้วได้ stream คำตอบ |
| `POST /sessions/{id}/ocr/confirm` | ยืนยันหรือแก้ข้อความที่อ่านจากรูป |
| `POST /sessions/{id}/end` | จบ session |
| `GET /sessions/{id}/messages` | ประวัติแชท |
| `GET /exam-preps/{id}/progress` | ข้อมูล progress card |

### 2.2.9 การจบ session

Session จบเมื่อ user บอกว่าพอ, หมดเวลาที่ตั้งไว้ (tutor ชวนปิดหลังจบโจทย์ข้อที่ทำอยู่), ทำหัวข้อตามแผนวันนี้ครบ หรือ idle เกิน 15 นาที (ปิดอัตโนมัติ) ตอนจบ code คำนวณการเปลี่ยนแปลงของ mastery ใน session นี้ แล้วให้ small model เขียนสรุป **2 บรรทัด** แสดงในแชทและเก็บใน `tutor_sessions.summary` เพื่อใช้ตอนเปิดห้องครั้งหน้า ไม่มีหน้าสรุปแยก

### 2.2.10 การตัดสินใจเชิงออกแบบ

1. Probe ก่อนสอน ยกเว้น user บอกว่ายังไม่เคยเรียน
2. Code คุม stage ส่วน LLM ทำตาม directive
3. สร้างโจทย์พร้อมเฉลยและ verify ก่อนส่ง (แลกกับ latency ประมาณ 1–2 วินาที)
4. Transcript เสียงลงช่องพิมพ์ ไม่ auto-send
5. รูปขอให้ยืนยันทุกครั้ง (PoC P1: confidence แยกบรรทัดที่อ่านผิดไม่ได้)
6. Mastery ใช้ BKT และนับเฉพาะ independent attempts
7. Done ต้องครอบคลุมทุก skill ไม่ใช่นับจำนวนข้อ, Park เมื่อผิดครั้งที่ 3 หรือเกิน 10 ข้อ/skill/วัน
8. Progress card ทุกครั้งที่เปิด session โดย code render ส่วน tutor สรุปจาก facts


## 2.4 Answer checking

### 2.4.1 หลักการ

**อะไรที่คณิตศาสตร์ตัดสินได้ ห้ามให้ LLM ตัดสิน** แบ่งหน้าที่ดังนี้

- **SymPy** (Python library คณิตศาสตร์เชิงสัญลักษณ์) ตัดสินว่าถูกหรือผิด และผิดตั้งแต่บรรทัดไหน
- **LLM** อธิบายว่าผิดแบบไหน (error_type) และชี้หลักฐาน
- **Code** รวมผลตามกฎที่ตายตัว

> แผนภาพ: Answer checker pipeline (ดูภาพในไฟล์ AI Orchestration Design .docx)

### 2.4.2 Input

- จาก `problems`: โจทย์, `reference_answer`, `solution_steps`, `skill_id`, `answer_format`
- จาก user: คำตอบรายบรรทัดในรูป LaTeX (จากรูปผ่าน `extract_answer` หรือจากข้อความผ่าน `normalize_math`)
- วิธีที่ชีทใช้ (จาก grounding chunk) สำหรับเช็ค method

### 2.4.3 ตรวจตาม answer_format

field `answer_format` จำเป็นเพราะ "ถูก" มีหลายความหมาย เช่น โจทย์ให้แยกตัวประกอบ x² − 4 ถ้า user ตอบ x² − 4 กลับมา คำตอบนั้นเท่ากับเฉลยทางคณิตศาสตร์ แต่ไม่ได้แยกตัวประกอบ

| answer_format | ตรวจคำตอบสุดท้าย | ตรวจทีละบรรทัด | Priority |
|---|---|---|---|
| `expression` | `simplify(a − b) == 0` | SymPy | Must |
| `factored` | เท่ากัน **และ** อยู่ในรูป factor แล้ว (เทียบ `factor_list`) | SymPy | Must |
| `equation` / `solution_set` | เทียบ solution set ด้วย `solveset` | solution set ของแต่ละบรรทัดต้องเท่าเดิม | Must |
| `numeric` (+unit) | tolerance 1% + ตรวจหน่วยด้วย `pint` | LLM | Should (ฟิสิกส์) |
| `short_text` | LLM เทียบกับ rubric จาก chunk ในชีท | — | Should (LNG, DB theory) |
| `sql` | รันบน SQLite fixture แล้วเทียบผลลัพธ์ | — | Could |

- **First wrong line:** ไล่เทียบบรรทัด i กับ i − 1 บรรทัดแรกที่ค่าไม่เท่ากันคือจุดที่ผิด ใช้เวลาระดับ millisecond และแม่นกว่าให้ LLM อ่านเอง
- **Safety:** `simplify` บางครั้งค้าง จึงรันใน subprocess พร้อม timeout 2 วินาที ถ้าเกินหรือ parse ไม่ได้ ให้ LLM ตัดสินเองพร้อมค่า `confidence`

### 2.4.4 LLM classifier

Input: โจทย์ + เฉลย + คำตอบ user + **ผลจาก SymPy** (บรรทัดไหนเท่ากันหรือไม่เท่า) + รายชื่อหัวข้อพื้นฐาน + นิยาม error type ทั้ง 6

ตัวอย่าง: user แยก x² − 5x + 6 ได้ (x − 2)(x + 3) → SymPy: คำตอบสุดท้ายไม่เท่า บรรทัดที่ 2 ผิด → LLM: `sign` เพราะ −3 กลายเป็น +3 ส่วน method ถูก

- Code ส่ง hint ให้ด้วย เช่น `sign_flip_detected` (กลับเครื่องหมายหนึ่งพจน์แล้วบรรทัดนั้นถูก) ช่วยแยก `sign` ออกจาก `calculation`
- `no answer` ตัดสินด้วย code (คำตอบว่าง, "ไม่รู้", "ทำไม่ได้")

### 2.4.5 Merge rules

| สถานการณ์ | verdict | นับ mastery |
|---|---|---|
| คำตอบสุดท้ายถูก ทุกบรรทัดถูก | `correct` | ถูก |
| คำตอบสุดท้ายถูก แต่มีบรรทัดผิด (ผิดสองทีหักล้างกัน) | `correct_with_flaw` | **ผิด** และ tutor ชี้บรรทัดนั้น |
| คำตอบสุดท้ายถูก แต่ใช้วิธีต่างจากชีท | `correct` + `method: other` | ถูก และ tutor บอกวิธีในชีท |
| ค่าเท่ากันแต่ผิดรูปแบบ (เช่น ยังไม่ factor) | `incomplete` | ผิด, error_type = concept |
| คำตอบสุดท้ายผิด | `incorrect` | ผิด |
| SymPy กับ LLM ขัดกันเรื่องถูก/ผิด | ใช้ผลของ SymPy | log ลง `checker_disagreements` |

Output ที่เก็บลง `attempts` และส่ง SSE `verdict` ก่อน tutor เริ่มพิมพ์

```
{ "verdict": "incorrect", "final_answer_correct": false,
  "first_wrong_line": 2, "error_type": "sign",
  "evidence": "บรรทัด 2: −3 กลายเป็น +3", "method": "doc",
  "decided_by": "sympy", "confidence": 0.97 }
```

### 2.4.6 เฉลยต้องถูกก่อน

- **โจทย์ที่ AI สร้าง:** SymPy แก้โจทย์ซ้ำ ถ้าไม่ตรงกับเฉลยของ AI สร้างใหม่ได้สูงสุด 2 รอบ ถ้ายังไม่ผ่านให้ใช้โจทย์จากข้อสอบเก่าแทน
- **ข้อสอบเก่า:** ถ้าชีทมีเฉลยก็ใช้ ถ้าไม่มีให้ LLM แก้แล้ว SymPy verify ถ้า verify ไม่ได้ ให้ติด `verified = false` และตอนตรวจให้ LLM แก้ 2 รอบเทียบกัน (self-consistency)

### 2.4.7 Dispute: user แย้งผลตรวจ

1. Intent router จับข้อความอย่าง "ผมว่าข้อนี้ถูกนะ" เป็น `dispute`
2. ตรวจใหม่ด้วย model tier main พร้อมให้เหตุผลทีละบรรทัด
3. ถ้าพลิกผล: `attempts.overridden = true`, คำนวณ mastery ใหม่ และ tutor ขอโทษสั้นๆ
4. เคสนี้ถูกเพิ่มเข้า golden set อัตโนมัติเพื่อใช้ปรับปรุง

### 2.4.8 วัดคุณภาพ checker

- Golden set: PoC P2 ใช้ 50 คำตอบ (`evals/answers/`) · เป้าก่อน Beta ประมาณ 100 คำตอบ โดยเพิ่มจากเคส dispute (2.4.7) · ลายมือจริงของทีมและเพื่อน พร้อม label verdict, error_type และ first_wrong_line
- เป้าหมาย: verdict accuracy ≥ 95%, error_type accuracy ≥ 80%, first_wrong_line ≥ 85%
- รันเป็น test suite ทุกครั้งที่แก้ prompt หรือเปลี่ยน model (2.11)

### 2.4.9 การตัดสินใจเชิงออกแบบ

1. SymPy ตัดสินถูก/ผิดทุกกรณีที่ parse ได้ LLM ทำหน้าที่จำแนกเท่านั้น
2. `correct_with_flaw` นับเป็นผิดสำหรับ mastery
3. ใช้วิธีอื่นที่ไม่ใช่ในชีทแต่ถูก นับเป็นถูก และ tutor บอกวิธีในชีทด้วย
4. Checker scope: Must = คณิต (expression, factored, equation), Should = ตัวเลข + หน่วย และ short text, Could = SQL
5. มี dispute flow
6. เป้าของ golden set ตาม 2.4.8


## 2.5 Tutor planner

### 2.5.1 หลักการ

**Planner เป็น code ล้วน ไม่มี LLM** ในมุม user จะรู้สึกว่า "AI เลือกหัวข้อให้" แต่จริงๆ แล้วเป็น algorithm ที่ test ได้และอธิบายเหตุผลได้ LLM มีหน้าที่แค่แปลง `reason_code` เป็นประโยค เช่น `review_due` → "ทวนฟังก์ชันก่อน เพราะผ่านมา 3 วันแล้ว"

> แผนภาพ: Tutor planner (ดูภาพในไฟล์ AI Orchestration Design .docx)

### 2.5.2 ขั้นที่ 1 · เลือก mode

**ประมาณเวลาที่ต้องใช้**

- need = Σ ของหัวข้อที่ยังไม่ผ่าน [ จำนวน skill ที่ยังไม่ครอบคลุม × จำนวนข้อที่คาดว่าต้องใช้ (จำลองจาก BKT params) × นาทีต่อข้อของ user ]
- นาทีต่อข้อเรียนรู้จาก `attempts` (เวลาตั้งแต่ส่งโจทย์ถึงตอบ) ค่าเริ่มต้น 4 นาที
- available = วันที่เหลือ × นาทีต่อวัน (ช่อง optional "วันละประมาณกี่นาที" ในหน้าข้อมูลการสอบ S08 แล้วปรับตามการใช้งานจริง ค่าเริ่มต้น 45 นาที)
- ratio = need ÷ available

| Mode | เงื่อนไข | Planner ทำอะไร |
|---|---|---|
| Normal | ratio ≤ 0.8 | ตามลำดับที่ตกลงกัน ครบทุก skill ทวนตาม spaced review (2.5.5) |
| Tight | 0.8 < ratio ≤ 1.2 | ย้ายหัวข้อ ★ ไปท้ายสุด, หัวข้อ ★★ ผ่านที่ difficulty 2 ได้ |
| Triage | ratio > 1.2 หรือเหลือ ≤ 3 วัน | ทำเฉพาะ ★★★ และ ★★ ที่อ่อน, ข้าม ★, ทวนเฉพาะ ★★★, quota buddy ลดครึ่ง |
| Final | วันก่อนสอบ | ไม่เปิดหัวข้อใหม่ ทำโจทย์คละแนวข้อสอบเก่าจากหัวข้อ ★★★ |

เมื่อ mode เปลี่ยน tutor บอก user **ครั้งเดียว** ตอนเปิดห้อง พร้อมเหตุผล เช่น "เหลือ 3 วัน ขอข้ามลำดับ (★) ไปก่อนนะ ถ้าอยากทำบอกได้"

### 2.5.3 ขั้นที่ 2 · เรียง topic queue

เรียงด้วยกฎตามลำดับ ไม่ใช้สูตรคะแนนรวม เพื่อให้อธิบายและเขียน test ได้ง่าย

1. **Review due:** สูงสุด 2 ข้อตอนต้น session (หัวข้อละ 1 โจทย์)
2. **หัวข้อที่ค้างอยู่** จาก session ก่อน: ทำให้จบก่อนเปิดหัวข้อใหม่
3. **Prerequisite** ที่ถูก push มาจาก Park
4. **หัวข้อที่ Park ไว้:** กลับมาทำเมื่อผ่านไปอย่างน้อย 1 session (`park.return_after_sessions`)
5. **หัวข้อถัดไปตามลำดับที่ตกลงกัน** โดยข้ามหัวข้อที่ mode ปัจจุบันตัดออก

**User override ชนะเสมอ:** "อยากทำสมการกำลังสอง" → ทำทันที (ถ้าเป็นหัวข้อที่ตัดออก tutor บอกก่อน), "ข้ามเรื่องนี้" → Park ด้วย `reason = user_skip`

### 2.5.4 ขั้นที่ 3 · เลือกโจทย์

| มิติ | กฎ |
|---|---|
| Skill | Verify ใช้ skill เดิมที่ผิด, Probe/Practice ใช้ skill ที่ยังไม่ครอบคลุม เรียงตาม `exam_freq` มากไปน้อย |
| Difficulty | Probe = 2, Practice ไล่ 2 → 3, Verify = ระดับเดิมหรือต่ำลง 1 |
| Source | Difficulty 3 ใช้ข้อสอบเก่าที่ยังไม่เคยใช้ก่อน ถ้าหมดแล้วค่อยสร้างใหม่ (ผ่าน SymPy verify), difficulty 1–2 สร้างใหม่ |
| ห้ามซ้ำ | ไม่ใช้โจทย์เดิมซ้ำใน exam prep เดียวกัน (ตรวจจาก `problems`) |
| Interleaving | ทุก 4 ข้อใน Practice แทรกโจทย์จากหัวข้อที่ผ่านแล้วที่เกี่ยวข้อง 1 ข้อ (Could) |

### 2.5.5 Spaced review

- รอบที่ k ห่าง `round_half_up(1 × 2.5^(k−1))` วัน (1, 3, 6, ...) ตามค่าเริ่มต้นของ SM-2 · ปัดครึ่งขึ้นด้วย `floor(x + 0.5)` ห้ามใช้ `round()` ของ Python ซึ่งปัด 2.5 เป็น 2
- ถ้ารอบถัดไปห่างเกิน 20% ของวันที่เหลือก่อนสอบ (Cepeda et al. 2008) ให้หยุดตั้งรอบ แล้วทวนอีกครั้งใน Final mode · วันที่เหลือนับ ณ วันที่ตั้งรอบถัดไป ไม่ใช่วันที่หัวข้อผ่าน
- ตัวอย่าง: ผ่านตอนเหลือ 30 วัน → ทวนวันที่ 1, 4 แล้ว Final mode (รายละเอียด learning-model.md §3)
- ทวนผิด: ลดระดับเป็น "กำลังดี", reset รอบ และหัวข้อกลับเข้า queue ในลำดับที่ 2
- รอบที่เลยวันสอบถูกตัดทิ้ง ส่วน Final mode ดึงหัวข้อ ★★★ ทั้งหมดมาทวนรวมกัน

### 2.5.6 แผนวันนี้

ตอนเปิด session planner เติม queue ลงในเวลาของ session ตามเวลาที่ประมาณไว้ แล้วส่ง `plan_today` ให้ tutor ใช้ในข้อความเปิดห้อง (2.2.2) แผนไม่ถูกล็อก ถ้าหัวข้อ Done เร็วกว่าที่ประมาณ planner หยิบรายการถัดไปใน queue มาทำต่อ

### 2.5.7 Data และการตัดสินใจ

- `exam_preps.daily_minutes` (nullable), `user_stats.avg_minutes_per_problem`
- `topic_progress.review_step`, `next_review_at`, `parked_reason`, `parked_at`
- `planner_decisions` (session_id, mode, decision, reason_code, inputs jsonb) ใช้ debug และตอบคำถามว่า "ทำไมระบบเลือกแบบนี้"

1. นาทีต่อวัน: ถามแบบ optional ใน S08 และเรียนรู้จากการใช้งานจริง
2. เกณฑ์ ratio 0.8 / 1.2 / ≤ 3 วัน (`planner.tight_ratio`, `planner.triage_ratio`, `planner.triage_days_left`) เป็นค่าเริ่มต้น ปรับตอน pilot
3. Queue ใช้กฎเรียงลำดับ ไม่ใช้สูตรคะแนนรวม
4. Interleaving เป็น Could


## 2.1 AI Buddy

### 2.1.1 หลักการ

**Buddy ไม่ใช่ agent ที่คิดเองว่าจะพูดอะไร** แต่เป็น rule engine (code) ที่ตัดสินว่าจะพูดไหมและพูดบทไหน แล้วให้ LLM เขียนบทตาม persona เหตุผลคือ buddy ที่พูดตามใจตัวเองจะกวนและอาจสอนผิด การใช้กฎทำให้เขียน test ได้ว่า buddy "ไม่แทรกตอนรอคำตอบ" จริง (TM-05)

| | Tutor | Buddy |
|---|---|---|
| บทบาท | ผู้สอน | เพื่อนที่เรียนอยู่ระดับเดียวกับ user |
| สอนเนื้อหาใหม่ | ได้ | **ไม่ได้** ทำได้แค่ถาม ลองทำ และให้กำลังใจ |
| ให้โจทย์และตรวจคำตอบ | ได้ | ไม่ได้ |
| ผูกกับ | exam prep | user (ตัวเดียวทุกวิชา) |
| ปิดได้ไหม | ไม่ได้ | ได้ ทั้งตอน onboarding และระหว่างติว ("มีนเงียบก่อน") |

### 2.1.2 ข้อมูลที่ buddy ใช้

ทุกอย่างมาจาก DB ไม่ได้คิดขึ้นเอง

- `past_exam_questions.trap`: กับดักของข้อสอบเก่า (จาก A7) เช่น "x² + 49 แยกไม่ได้ในจำนวนจริง"
- `topic_skills.common_mistakes`: error ที่พบบ่อยต่อ skill พร้อม error_type (จาก A6) เมื่อมี user มากพอ จะใช้สถิติจริงจาก `attempts` (aggregate ภายใน tenant) แทน

### 2.1.3 Algorithm

> แผนภาพ: AI Buddy algorithm (ดูภาพในไฟล์ AI Orchestration Design .docx)

**จังหวะที่ buddy พูดได้ (gap):** ช่วงที่ tutor อธิบายหรือให้ feedback จบแล้ว แต่ยังไม่ส่งโจทย์ข้อถัดไป buddy จึงไม่มีทางพูดแทรกตอนที่ user กำลังคิด

**Hard gates** (ต้องผ่านทุกข้อ)

1. User เปิด buddy และไม่ได้สั่ง mute ใน session นี้
2. ไม่มีโจทย์ค้างรอคำตอบจาก user
3. จำนวนครั้งที่แทรกในหัวข้อนี้ยังไม่เกิน quota: ความถี่ต่ำ 1, กลาง 2, สูง 3 (จาก persona · `buddy.quota_per_topic`) และใน Triage/Final mode หารครึ่งแล้วปัดขึ้น (`buddy.halve_quota_in_modes` · ได้ 1/1/2 ความถี่ต่ำยังแทรกได้ 1 ครั้ง)
4. ห่างจากการแทรกครั้งก่อนอย่างน้อย 4 user turns (`buddy.min_user_turns_between`)

### 2.1.4 Roles

| Role | Trigger | Seed | ข้อห้าม |
|---|---|---|---|
| **ให้กำลังใจ** | `fail_streak ≥ buddy.encourage_fail_streak` (2) หรือ intent = บ่นเหนื่อย/ท้อ | error ล่าสุดของ user | **ห้ามตอบถูกหรือบอกว่าตัวเองทำได้** (TM-05) |
| **ขอให้สอน** (protégé effect) | หัวข้อเพิ่ง Done | skill ที่ยากที่สุดในหัวข้อ | ถามได้ไม่เกิน 1 ครั้งต่อหัวข้อ |
| **ถามแทน** | Teach จบ และ skill นี้มี trap ที่ user ยังไม่เจอ | `trap` จากข้อสอบเก่า | ต้องเป็นคำถาม ไม่ใช่เฉลย |
| **ตอบผิดให้ดู** | Practice + user ตอบถูกข้อล่าสุด + skill มี common mistake ที่ user ยังไม่เคยทำผิด | `common_mistakes` | tutor ต้องแก้ในฉากเดียวกันเสมอ ห้ามปล่อยคำตอบผิดค้างไว้ |

ถ้า trigger ตรงหลายอัน เลือกตามลำดับในตาราง (ความรู้สึกของ user มาก่อนเนื้อหา)

### 2.1.5 Pseudocode (feature spec สำหรับ SDD)

ตัวเลขทุกตัวอ่านจาก `config/learning.yaml` (`cfg = learning.buddy`) ห้าม hard-code

```
def buddy_decide(s: TurnState, cfg: BuddyConfig) -> BuddyScene | None:
    if not s.buddy.enabled or s.buddy.muted: return None
    if s.problem_pending: return None
    if s.buddy_count[s.topic] >= quota(cfg, s.buddy.frequency, s.mode): return None
    if s.turns_since_buddy < cfg.min_user_turns_between: return None
    for role in (ENCOURAGE, TEACH_BACK, ASK_TRAP, WRONG_DEMO):
        seed = role.match(s)          # คืน None ถ้า trigger ไม่ตรง
        if seed: return BuddyScene(role, seed)
    return None
```

### 2.1.6 เขียนทั้งฉากใน call เดียว

ถ้า buddy พูดแล้ว tutor ต้องตอบ วิธีตรงไปตรงมาต้องเรียก LLM 3 ครั้ง (tutor → buddy → tutor) ซึ่งช้าและเปลือง ระบบจึงให้ `tutor_reply` **call เดียวเขียนทั้งฉาก** โดยใช้ speaker marker แล้ว backend แยก stream ออกเป็น message ของแต่ละคน

```
directive: { "buddy_scene": { "role": "ask_trap",
             "seed": "x² + 49 แยกไม่ได้ในจำนวนจริง · midterm-2566 ข้อ 3" } }

@tutor: ถูกแล้ว (2x−5)(2x+5) เพราะ 4x² คือ (2x)²
@buddy: เดี๋ยวนะพี่ แล้ว x² + 49 ล่ะ แยกแบบนี้ได้ป่ะ
@tutor: แยกไม่ได้ ผลต่างกำลังสองต้องเป็น "ลบ" เท่านั้น ข้อสอบปี 66 หลอกตรงนี้เลย ข้อถัดไปนะ...
```

ข้อแลกเปลี่ยน: model ตัวเดียวพูดสองบทอาจทำให้ persona ปนกันบ้าง แต่ได้บทสนทนาที่ต่อเนื่องและเร็วกว่ามาก ถ้า pilot พบว่าปนกันจริง จึงค่อยแยก call

**ขอให้สอน:** ข้อความถัดไปของ user คือการอธิบายให้ buddy ฟัง intent router จับเป็น `teach_back` แล้ว tutor ให้ feedback สั้นๆ ผลนี้ **ไม่นับเข้า mastery** แต่ถูก log ไว้

### 2.1.7 ข้อยกเว้น: นอกเรื่อง

ถ้า user พิมพ์นอกเรื่องหรือบ่น เช่น "เหนื่อยจัง" buddy ตอบได้ 1 ประโยคก่อนที่ tutor จะดึงกลับ แม้จะอยู่นอก gap ก็ตาม ช่วยให้ห้องมีชีวิต และนับเข้า quota ด้วย ข้อยกเว้นนี้ไม่ใช้กับ `distress` (2.9)

### 2.1.8 Data และการวัดผล

- `buddy_events` (session_id, topic_id, role, trigger, seed jsonb, message_id, created_at) ใช้นับ quota
- `tutor_sessions.buddy_muted`, `buddy_profiles` (2.7)
- วัดผล: อัตราการ mute buddy ต่อ session (ถ้าสูงแปลว่ากวน), pilot survey "เพื่อนติวช่วยไหม" และ "เพื่อนติวกวนไหม", เทียบ retention ของ user ที่เปิดกับปิด buddy (ไม่ทำเป็น A/B test เต็มรูปแบบ)


## 2.6 Context management

> แผนภาพ: AI Gateway: เส้นทางเดียวที่ทุก AI call ผ่าน (ใช้ร่วมกันใน 2.6–2.11) (ดูภาพในไฟล์ AI Orchestration Design .docx)

- **ประกอบใหม่จาก DB ทุก turn** (10 layers ใน 2.2.3) Cloud Run ไม่เก็บ state ใน memory การออกจากห้องแล้วกลับมาต่อ (TM-13) จึงทำได้ตามธรรมชาติ
- **เรียงเพื่อ prompt caching:** static (system, source policy, persona) → semi-static (scope snapshot, grounding ของหัวข้อ) → dynamic (performance, directive, conversation, input) prefix ที่ไม่เปลี่ยนจะถูก cache ทั้งฝั่ง Gemini และ Claude ทำให้ถูกและเร็วขึ้น
- **Rolling window:** เก็บ 8 turns ล่าสุดแบบเต็ม ส่วนที่เก่ากว่ารวมเป็น `running_summary` ด้วย small model ทุก 8 turns (ทำเบื้องหลัง · ใช้ `session.context_recent_turns` ตัวเดียวกับขนาด window เพราะสรุปเมื่อ turn หลุดจาก window) summary เก็บสิ่งที่สอนไปแล้ว และสิ่งที่ user บอกว่าชอบ เช่น "ชอบให้ยกตัวอย่างก่อน"
- **Token budget 6,000:** ถ้าเกิน ตัด turns เก่าก่อน แล้วลด chunks จาก 4 เหลือ 2 **ห้ามตัด layer 1–6**
- **ความจำข้าม session:** ใช้ `tutor_sessions.summary` ของ session ล่าสุด + ข้อมูลใน `topic_progress`

## 2.7 Persona จาก free text

1. User พิมพ์บรรยาย เช่น "อยากได้พี่ผู้หญิงใจดี พูดกันเอง อธิบายด้วยตัวอย่างก่อน" (มีคำแนะนำวิธีเขียนในหน้า S05)
2. `persona_extract` (small, structured output) แปลงเป็น params ที่เป็น enum ทั้งหมด
3. คำขอที่ทำไม่ได้ (เช่น "ด่าหยาบๆ", "เฉลยเลยไม่ต้องสอน") ถูกทิ้ง และบอก user ว่าส่วนไหนทำไม่ได้
4. แสดงตัวอย่างประโยคจาก params ให้ดู (`persona_preview`) ถ้ายังไม่ถูกใจก็พิมพ์ปรับต่อได้ แล้วกดบันทึก
5. Prompt ใช้ template ที่เติม params เท่านั้น **text ดิบของ user ไม่เคยเข้า prompt** (กัน injection)

| Param | ค่า | ใช้กับ |
|---|---|---|
| `name`, `self_pronoun`, `call_user` | ข้อความสั้นที่ผ่าน whitelist ตัวอักษร | tutor, buddy |
| `formality`, `energy`, `strictness` | 1–3 | tutor, buddy |
| `humor` | 0–2 | tutor, buddy |
| `explain_style` | step_by_step / example_first / concise | tutor |
| `emoji` | true / false | tutor, buddy |
| `voice_id` | รายการเสียงภาษาไทยของ Google TTS | tutor, buddy |
| `frequency` | low / med / high | buddy |
| `personality` | ขี้สงสัย / ขี้เล่น / ขยัน | buddy |

Data: `tutor_profiles`, `buddy_profiles` (user_id, description_raw, params jsonb, version) ส่วน preset (tutor 3 แบบ, buddy 2 แบบ) คือชุด params ที่เติมไว้ล่วงหน้า แก้ persona ได้ตลอด มีผลตั้งแต่ turn ถัดไป

## 2.8 Voice I/O

| | Input (STT) | Output (TTS) |
|---|---|---|
| Service | Google Cloud Speech-to-Text (th-TH) | Google Cloud Text-to-Speech (th-TH) |
| Flow | กดค้างอัด (≤ 60 วินาที) → Storage → STT → transcript ลงช่องพิมพ์ | กดลำโพงราย message หรือเปิด auto-read (ค่าเริ่มต้นปิด, TM-09) |
| เทคนิค | ส่งชื่อหัวข้อและศัพท์จาก scope เป็น phrase hints ให้ STT จำศัพท์เฉพาะได้แม่นขึ้น | แปลง LaTeX เป็นคำอ่านก่อน (x² → "เอกซ์กำลังสอง") ด้วยกฎ และมี small model สำรอง |
| Cache และการลบ | ลบไฟล์เสียงหลัง 7 วัน เก็บแค่ transcript | cache ด้วย hash(text + voice_id) ใน Storage |
| Persona | — | tutor กับ buddy ใช้คนละเสียง |

Auto-read: client ขอ TTS ทีละประโยคที่ stream จบแล้ว ไม่ต้องรอข้อความจบทั้งก้อน ถ้า STT ใช้ไม่ได้ ให้ user พิมพ์แทน (degrade, 2.10)

## 2.9 Guardrails

**Input**

- Prompt injection จากเอกสาร: `<document>` tags + output schema + user ยืนยัน scope (2.3.9)
- Injection จาก persona: ใช้ params เท่านั้น (2.7)
- Limits: ข้อความ ≤ 2,000 ตัวอักษร, 20 ข้อความ/นาที, รูป ≤ 10 MB, เสียง ≤ 60 วินาที
- ขอให้ทำงานนอกขอบเขต (เช่น "เขียนรายงานวิชาอื่นให้หน่อย"): ปฏิเสธสั้นๆ แล้วดึงกลับ
- **Distress** (เครียดหนัก, สัญญาณทำร้ายตัวเอง): intent router จับได้ ตอบด้วย template ที่ดูแลความรู้สึก พร้อมสายด่วนสุขภาพจิต 1323 buddy ไม่เล่นมุก และ log ไว้โดยไม่ตัดสิน

**Output**

- Schema validation (Pydantic) ทุก structured call ไม่ผ่านให้ retry 1 ครั้งพร้อม error message ถ้ายังไม่ผ่านให้ degrade
- **ซ่อม backslash ของ LaTeX เฉพาะ field ที่เป็นสูตร:** model มักลืม escape `\` ใน JSON ทำให้ `\frac` `\beta` `\theta` `\right` `\neq` ถูก parse เป็นตัวอักษรควบคุม (form feed + `rac`) และยังผ่าน schema แบบเงียบๆ (เจอใน PoC P1) · ซ่อมด้วย type ของ field ใน output model (`app/ai/latex.py`) ไม่ซ่อมทุก string เพราะข้อความธรรมดามี newline และ tab จริง (review ของ PR #15: newline ก่อน `mid-term` ถูกแก้ผิด): `LatexStr` = ทั้ง string เป็น LaTeX (`AnswerLine.latex`, `latex_blocks`) · `MathTextStr` = ข้อความปนสูตร ซ่อมเฉพาะใน `$...$` และ `$$...$$` (`text` ของ A2, A2b, A4) · กฎการซ่อม: form feed/backspace ทุกครั้ง · tab/CR ที่มีตัวอักษรตามหลัง · newline เฉพาะเมื่อตามด้วยชื่อคำสั่งเต็มคำ (`neq` `nabla` `notin` ...) · ไม่ซ่อม `\ne` `\ni` `\nu` `\not` เพราะชนกับบรรทัดที่ขึ้นต้นด้วย `e^{x}` `i)` `u =` หรือคำว่า not (ข้อความ PyMuPDF ของชีท MTH10101 ชน 296 จุด) · newline และ tab ทั่วไปไม่แตะ · คำสั่งที่ไม่ใช่ escape ของ JSON (เช่น `\lim`) ทำให้ parse ไม่ผ่าน จึงเข้า retry ตามข้อบน
- **Answer-leak check:** ถ้า tutor reply มี `reference_answer` ของโจทย์ที่ยังค้างอยู่ (ตรวจด้วย string match และ SymPy) ให้ generate ใหม่ เป็นการบังคับกฎ "ไม่เฉลยก่อนตอบ" แบบ deterministic
- กฎของ buddy บังคับด้วย code (2.1)

**Data**

- RLS ตาม `tenant_id` (3.4)
- Prompt ไม่มีข้อมูลของ user อื่น สถิติ common mistakes ใช้แบบ aggregate เท่านั้น
- ส่งเฉพาะชื่อเล่นให้ LLM ไม่ส่งอีเมลหรือข้อมูลส่วนตัวอื่น
- ตั้งแต่ Beta ทุก tier ต้องใช้ provider ที่ไม่นำข้อมูลไป train (Vertex AI แบบเสียเงิน) · free tier ใช้ได้เฉพาะ PoC กับข้อมูลที่เจ้าของให้ consent แล้ว (AI-07)

## 2.10 Model routing, cost และ fallback

| Tier | Purposes | Primary (Vertex AI) | Fallback |
|---|---|---|---|
| small | route_intent, classify_material, split_past_exam, map_questions, normalize_math, persona_extract, persona_preview, latex_to_speech, summaries (update_running_summary, session_summary) | Gemini รุ่นเล็ก | Claude Haiku |
| mid | check_answer, generate_problem, extract_topics_local, scope_edit | Gemini รุ่นกลาง | Claude Haiku |
| main | tutor_reply (+ buddy scene), merge_topics, dispute re-check | Gemini รุ่นกลางหรือใหญ่ (เลือกจาก spike) | Claude Sonnet |
| vision | vision_extract, vision_extract_pages, extract_answer | Gemini รุ่นกลาง | Mathpix (ถ้า OCR < 80% ใน PoC P1) |
| embed | ingest, คำถามอิสระ | เลือกจาก spike ใน PoC P3 (3.6) | — |

- **Config อยู่ใน YAML ใน repo** (purpose → tier, model, temperature, max_tokens, timeout, fallback, prompt_version) เปลี่ยน model ได้โดยไม่แก้ code
- **Fallback chain:** retry 1 ครั้ง (backoff: รอตามที่ provider ขอ เช่น `retryDelay` ของ Gemini 429 ถ้าไม่บอกรอ `gateway.retry_backoff_seconds` · ถ้าต้องรอเกิน `gateway.max_retry_wait_seconds` ไม่ retry เพราะรอนานกลาง turn แย่กว่าล้มทันที) → provider สำรองใน tier เดียวกัน → degrade (checker: ใช้ผล SymPy อย่างเดียวไม่มี error_type, tutor: ข้อความ template "ระบบช้า ลองส่งอีกทีนะ", STT: ให้พิมพ์แทน)
- **Circuit breaker:** ใช้ค่า default ของ Resilience4j คือ error ≥ 50% จากอย่างน้อย 10 calls ให้ route ไป fallback 60 วินาที แล้วลองกลับ
- **ควบคุมต้นทุน:** quota token ต่อ user/วัน และต่อ tenant (ผูกกับ plan), prompt caching, ข้าม router เมื่อส่งรูป, cache TTS, embed เฉพาะตอน ingest
- **เป้าหมาย:** ต้นทุน ≤ 5 บาทต่อ session 45 นาที และ TTFT p95 < 2 วินาที (ตัวเลขประมาณการ วัดจริงใน PoC)

## 2.11 Observability และ evaluation

- `ai_calls` เก็บทุก call: tenant_id, user_id, session_id, purpose, provider, model, prompt_version, tokens_in, tokens_out, cached_tokens, latency, cost, status, fallback_used, request_id
- **Prompt versioning:** prompts อยู่ใน repo (`prompts/{purpose}/v{n}.md`) แก้ผ่าน PR และต้องผ่าน eval ก่อน merge
- **Eval suites** (รันใน CI เฉพาะเมื่อ prompt หรือ model เปลี่ยน เพราะมีค่าใช้จ่าย)
  - checker: golden answers (2.4.8)
  - topic extraction: เทียบกับหัวข้อที่ทีม label เอง 2–3 วิชา
  - tutor behavior: scenarios + LLM-as-judge rubric (ไม่เฉลยก่อน, ใช้วิธีในชีท, ไม่ถาม "งงตรงไหน")
- **Monitoring:** request_id ไล่ได้ตั้งแต่ FastAPI → AI call → DB, Sentry + Cloud Logging (structured JSON), dashboard: TTFT p95, error rate, cost/วัน/tenant
- **Quality signals จากการใช้งาน:** อัตรา dispute (2.4), อัตราแก้ OCR (AM-03), อัตรา mute buddy (2.1), จำนวนครั้งที่แก้ scope (2.3)
- **Retention:** เก็บ prompt/response เต็ม 30 วันช่วง dev และ pilot เพื่อ debug หลังจากนั้นเก็บแค่ metadata, ไฟล์เสียง 7 วัน


# 3. สรุปรวม

## 3.1 AI call inventory

| ID | Call | Flow | Tier | Output |
|---|---|---|---|---|
| A1 | `classify_material` | 2.3 | small | kind, confidence, relevance_weight, reason |
| A2 | `vision_extract` | 2.3 | vision | text, latex_blocks ต่อหน้า |
| A2b | `vision_extract_pages` | 2.3 | vision | text ทุกหน้าของไฟล์สแกนใน call เดียว (PoC P3) |
| A3 | `embed` | 2.3 | embed | vector |
| A4 | `split_past_exam` | 2.3 | small | ข้อสอบรายข้อ + เลขหน้า |
| A5 | `extract_topics_local` | 2.3 | mid | หัวข้อของไฟล์ + เลขหน้า |
| A6 | `merge_topics` | 2.3 | main | หัวข้อกลาง + ลำดับ + prereqs + skills + common_mistakes |
| A7 | `map_questions` | 2.3 | small | topic_id, skill_id, trap ต่อข้อ |
| A8 | `scope_edit` | 2.3 | mid | reply + actions |
| T1 | `route_intent` | 2.2 | small | intent (9 ประเภท ตาม 2.2.4) |
| T2 | `extract_answer` | 2.2 | vision | คำตอบรายบรรทัด LaTeX + confidence |
| T3 | `normalize_math` | 2.4 | small | LaTeX รายบรรทัด |
| T4 | `check_answer` | 2.4 | mid | error_type, evidence, method (+ verdict ถ้าไม่มี SymPy) |
| T5 | `generate_problem` | 2.2 | mid | โจทย์, เฉลย, steps, difficulty, skill, answer_format |
| T6 | `tutor_reply` | 2.2, 2.1 | main | ข้อความ stream (@tutor / @buddy) |
| T7 | `update_running_summary` | 2.6 | small | summary |
| T8 | `session_summary` | 2.2 | small | สรุป 2 บรรทัด |
| T9 | `dispute_recheck` | 2.4 | main | verdict + เหตุผลทีละบรรทัด |
| P1 | `persona_extract` | 2.7 | small | params + รายการที่ทำไม่ได้ |
| P2 | `persona_preview` | 2.7 | small | ประโยคตัวอย่าง |
| V1 | STT | 2.8 | Google STT | transcript |
| V2 | TTS | 2.8 | Google TTS | audio |
| V3 | `latex_to_speech` | 2.8 | small | คำอ่าน (สำรองเมื่อกฎแปลงไม่ได้) |

## 3.2 Data tables

ทุก table มี `tenant_id` และเปิด RLS

| Table | Columns หลัก | Flow |
|---|---|---|
| `tenants` | type (personal / organization), name, plan, quota_tokens_day, status | 3.4 |
| `org_units` | tenant_id, parent_id, name (schema มีแล้ว ยังไม่มี UI ใน v1) | 3.4 |
| `memberships` | user_id, tenant_id, org_unit_id, role | 3.4 |
| `profiles` | user_id, nickname, education_level, explain_language | 2.2, 2.7 |
| `tutor_profiles`, `buddy_profiles` | user_id, description_raw, params, version, enabled (buddy) | 2.7 |
| `exam_preps` | subject, exam_date, daily_minutes, active_scope_version_id | 2.3, 2.5 |
| `materials` | exam_prep_id, storage_path, kind, kind_confidence, kind_confirmed, user_note, relevance_weight, status, error | 2.3 |
| `material_pages` | material_id, page_no, text, extract_method | 2.3 |
| `chunks` | material_id, page_from, page_to, text, content_hash, embedding | 2.3 |
| `past_exam_questions` | material_id, q_no, page_no, text, topic_id, skill_id, trap, reference_answer | 2.3 |
| `topics` | exam_prep_id, name, order_index, prereq_ids, importance, importance_reason, signal_r, origin, status | 2.3 |
| `topic_skills` | topic_id, name, exam_freq, common_mistakes, excluded | 2.3 |
| `topic_chunks` | topic_id, chunk_id, score | 2.3 |
| `scope_changes` | topic_id, op, before, after, reason, actor | 2.3 |
| `scope_versions` | exam_prep_id, version, status, snapshot, confirmed_at | 2.3 |
| `ingestion_jobs` | material_id, stage, progress, status, error | 2.3 |
| `tutor_sessions` | ดู 2.2.6 | 2.2 |
| `messages` | ดู 2.2.6 | 2.2 |
| `problems` | ดู 2.2.6 | 2.2, 2.4 |
| `attempts` | ดู 2.2.6 | 2.4 |
| `topic_progress` | ดู 2.2.6 | 2.2, 2.5 |
| `user_stats` | user_id, avg_minutes_per_problem | 2.5 |
| `planner_decisions` | session_id, mode, decision, reason_code, inputs | 2.5 |
| `buddy_events` | session_id, topic_id, role, trigger, seed, message_id | 2.1 |
| `checker_disagreements` | attempt_id, sympy_result, llm_result | 2.4 |
| `golden_answers` | image_path, lines, label_verdict, label_error_type, label_line · **เทอม 2** (เก็บเคส dispute ตาม 2.4.7) ยังไม่อยู่ใน migration · v1 เก็บ golden set เป็นไฟล์ใน `evals/` | 2.4, 2.11 |
| `ai_calls` | ดู 2.11 | 2.11 |

## 3.3 SSE events

| Event | Flow | ความหมาย |
|---|---|---|
| `token` | 2.2, 2.3 | ข้อความ stream (แยก speaker ในห้องติว) |
| `scope_patch` | 2.3 | การ์ดหัวข้อเปลี่ยนหลัง action ผ่านการตรวจ |
| `progress_card` | 2.2 | dashboard ย่อตอนเปิด session หรือเมื่อ user ขอ |
| `problem` | 2.2 | การ์ดโจทย์ใหม่ |
| `ocr_preview` | 2.2 | ข้อความที่อ่านจากรูป รอ user ยืนยัน |
| `verdict` | 2.4 | ผลตรวจ ✓/✗ ส่งก่อน tutor เริ่มพิมพ์ |
| `buddy` | 2.1 | ข้อความจาก buddy |
| `session_end` | 2.2 | สรุป 2 บรรทัด |
| `done` | ทั้งหมด | จบ stream |

## 3.4 ข้อมูลกับ multi-tenant

Target user ของ v1 คือนักเรียนรายคน แต่ data architecture ออกแบบเป็น multi-tenant ตั้งแต่แรก

- นักเรียนแต่ละคนคือ **personal tenant** สร้างอัตโนมัติตอนสมัคร พร้อม membership role `owner`
- Schema รองรับ **organization tenant** (สถาบัน → สาขา → ห้อง ผ่าน `org_units`) ได้โดยไม่ต้อง migrate
- RLS: `tenant_id` ต้องตรงกับ tenant ใน JWT (custom claim ผ่าน Supabase auth hook) และข้อมูลส่วนตัว (attempts, progress, messages) ต้อง `user_id = auth.uid()` ด้วย
- Storage path ขึ้นต้นด้วย `{tenant_id}/`
- Quota token และ rate limit นับต่อ tenant ผูกกับ `plan`
- Automated test สร้าง 2 tenants แล้วยืนยันว่ามองไม่เห็นข้อมูลของกันและกัน รันใน CI ทุกครั้ง

## 3.5 ผลกระทบต่อ SRS และ wireframe

| รายการ | การเปลี่ยนแปลง |
|---|---|
| AM-02 | v1.0 เสนอยืนยันผลอ่านลายมือเฉพาะเมื่อ min confidence < 0.8 · **หลัง PoC P1 กลับเป็นยืนยันทุกครั้ง** (21 ต.ค. · PR #45) |
| TM-07 | transcript เสียงลงช่องพิมพ์ให้ user แก้แล้วกดส่งเอง, priority เป็น Should |
| TM-11 | แสดง progress card ทุกครั้งที่เปิด session และเมื่อ user ขอ |
| TM-05 | ระบุ 4 roles, hard gates, quota ตามความถี่ และข้อยกเว้นนอกเรื่อง |
| SM (ใหม่) | skills ต่อหัวข้อ (ซ่อนใน UI, แก้ผ่าน chat), op `exclude_skill` / `include_skill` |
| TM (ใหม่) | เงื่อนไข Done แบบ skill coverage, Park, spaced review, ความพร้อม %, planner modes |
| AM (ใหม่) | answer_format, dispute flow, answer-leak check |
| SA (ใหม่) | distress handling, retention ของข้อมูล |
| SA-02 | multi-tenant (personal tenant) เป็น Must |
| S08 | เพิ่มช่อง optional "วันละประมาณกี่นาที" |
| S15 | ข้อความเปิดห้องเป็น progress card + สรุป + โจทย์ข้อแรก |

## 3.6 สิ่งที่ต้องพิสูจน์ใน Proof of Concept

| สมมติฐาน / threshold | ค่าเริ่มต้น | PoC |
|---|---|---|
| Vision LLM อ่านลายมือคณิตได้แม่นพอ | ≥ 80% ของบรรทัด | P1 ✅ **95.2%** (30 รูป 125 บรรทัด · `gemini-3.5-flash-lite` · ไม่ได้ทดสอบ Claude/Mathpix เพราะงบ) |
| OCR confidence ใช้แยกบรรทัดที่อ่านผิดได้ | threshold 0.8 | P1 ❌ ไม่มี threshold ที่จับได้ ≥ 95% → ยืนยันทุกครั้ง (`specs/poc/reports/P1.md`) |
| Topic extraction ตรงกับที่คนทำ | หัวข้อ ≥ 80%, ★★★ ≥ 80%, ≤ 3 นาที/ไฟล์ | P3 เอกสาร → หัวข้อ + ดาว |
| Embedding model สำหรับภาษาไทย | ยังไม่เลือก | P3 (ลอง 2–3 ตัวกับคำถาม 20 ข้อ) |
| Checker แม่นตามเป้า | verdict ≥ 95%, error_type ≥ 80% | P2 Answer checker |
| TTFT และต้นทุน | < 2 วินาที, ≤ 5 บาท/session | P4 Tutor loop + P7 AI gateway |
| Fallback ทำงาน | สลับอัตโนมัติ, log ครบ | P7 |
| STT ภาษาไทยปนคณิต | word error rate ≤ 15% เมื่อใช้ phrase hints | P5 Voice |
| BKT params, ratio ของ planner, quota buddy | ตามเอกสารนี้ | ปรับตอน Alpha/Beta |

## 3.7 Requirement → section

ใช้ไล่ว่า requirement แต่ละข้อใน `specs/requirements/requirements.md` ถูกออกแบบไว้ที่ไหน (กลุ่ม SM, TM, AM, PM, AI ที่ยังใช้อยู่) · "นอก AI flow" = เป็นงานหน้าเว็บหรือ API ล้วน ดู spec อื่น · ⚠️ = spec ยังไม่ครอบคลุมทั้งข้อ

ไม่อยู่ในตาราง: SM-05, PM-07 (deferred) · AM-10 (obsolete)

| Req | Section | หมายเหตุ |
|---|---|---|
| SM-01 | 1.4, 2.3.4 | |
| SM-02 | 2.3.4 (5b), 2.3.7 A6 `prereqs` | |
| SM-03 | 2.3.5, learning-model §2 | |
| SM-04 | 2.3.7 A6 `sources`, 2.3.8 (API 8) | |
| SM-06 | 2.3.6, 2.8 | พูดผ่าน STT ลงช่องพิมพ์เหมือนห้องติว |
| SM-07 | 2.3.6 (`scope_patch`) | |
| SM-08 | 2.3.2 (ขั้น 7), 2.3.8 (API 10–11) | |
| SM-09 | 2.3.2 (ขั้น 7), 2.2.2 | |
| SM-10 | 1.4, 2.2.4 (`question_off_scope`) | |
| SM-11 | 1.4 | |
| SM-12 | 2.3.4, 2.3.6 | |
| TM-01 | 2.5 | |
| TM-02 | 2.5.1 (`reason_code`), 2.5.6 | |
| TM-03 | 2.2.4 (Probe) | |
| TM-04 | 2.2.4 | |
| TM-05 | 2.1 | |
| TM-06 | 2.2.5 | ไม่มีปุ่ม choice เป็นงาน UI |
| TM-07 | 2.2.5, 2.8 | |
| TM-08 | นอก AI flow | KaTeX ฝั่งหน้าเว็บ · 2.2.8 การ์ดโจทย์ |
| TM-09 | 2.8 | |
| TM-10 | — | ⚠️ ยังไม่มี spec: ตอบไม่ตรงคำถามแล้วถามกลับให้แคบลง · ออกแบบใน feature spec ห้องติว (S3) |
| TM-11 | 2.2.2 | |
| TM-12 | 2.2.9 | |
| TM-13 | 1.3 (P8), 2.6 | |
| TM-14 | 2.2.4 | ให้โจทย์ทีละข้อ ไม่มี flow ที่สร้าง mock exam |
| TM-15 | 2.2.2 | |
| TM-16 | 2.2.4 (Done), learning-model §4 | |
| TM-17 | 2.5.5, learning-model §3 | |
| TM-18 | 2.5.2, learning-model §6 | |
| TM-19 | 2.2.4 (Park), 2.5.3, learning-model §7 | |
| TM-20 | นอก AI flow | `specs/features/tutor/chat-room-ui.md`, `specs/features/tutor/chat-streaming.md` · 2.1.6 แยก speaker |
| TM-21 | 2.9 (Limits) | ค่าจาก `config/ai.yaml` → `guards` |
| AM-01 | 2.2.5 (`extract_answer`), 3.6 (P1) | |
| AM-02 | 2.2.5 | |
| AM-03 | 2.11 (quality signals) | |
| AM-04 | 2.4.3 | |
| AM-05 | 2.4.3 (first wrong line) | |
| AM-06 | 1.5, 2.4.4 | |
| AM-07 | 2.2.4 (Teach) | |
| AM-08 | 2.2.4 (Verify) | |
| AM-09 | 1.4, 2.2.4 | |
| AM-11 | 2.2.4 (ที่มาของโจทย์), 2.4.6 | |
| AM-12 | 2.4.7 | |
| AM-13 | 2.9 (Output) | |
| PM-01 | 2.2.6 (`attempts`) | |
| PM-02 | 2.2.6, learning-model §1 | |
| PM-03 | 2.2.2, learning-model §5 | |
| PM-04 | นอก AI flow | หน้า home · ข้อมูลจาก `GET /exam-preps/{id}/progress` (2.2.8) |
| PM-05 | 2.2.9 | |
| PM-06 | 2.2.6 (`topic_progress` แยกตาม `exam_prep_id`) | |
| AI-01 | 1.3 (P7), 2.6–2.11 | |
| AI-02 | 2.10 | |
| AI-03 | 1.3 (P7) | |
| AI-04 | 2.11 (`ai_calls`) | |
| AI-05 | 2.9 (Output) | |
| AI-06 | 2.6 | |
| AI-07 | 2.9 (Data), 2.10 | |
| AI-08 | 2.3.3 (Embed) | |
