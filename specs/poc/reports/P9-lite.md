# PoC P9-lite · โควตา free tier ของ Google AI Studio พอไหม · report

| | |
|---|---|
| Owner | Junior |
| Sprint | S4 (เป้าข้อ 9 ของ advisor · 30 พ.ย. 2569) |
| Date | 28 พ.ย. 2569 |
| Code | `poc/P9-lite/` (`load.py` + 10 test · คำสั่งรันซ้ำใน `poc/P9-lite/README.md`) · ผล `poc/P9-lite/results/*.json` · บันทึกละเอียด `docs/worklog/poc-p9-lite-free-tier-quota.md` |

## 1. คำถาม

ถ้าใช้ Gemini API free tier (AI Studio key ในโปรเจกต์ที่ไม่ผูก billing) แทน Vertex ได้กี่ session ต่อวัน และใช้ได้กับงานแบบไหน (dev ของทีม, demo กับเพื่อนร่วมชั้น) · Beta ใช้ไม่ได้อยู่แล้วตาม AI-07

## 2. วิธีทดสอบ

- **โควตา:** อ่านจากหน้า Rate Limit ของ AI Studio ในโปรเจกต์ free tier (Junior 28 พ.ย.) · เอกสารทางการไม่ลงตัวเลขแล้วและบอกว่า "not guaranteed"
- **Data:** ชีท PDF ไทยสังเคราะห์ 3 หน้า (`make_sheet.py`) + คำตอบพิมพ์ที่เขียนขึ้น · ไม่มีลายมือ ไม่มีข้อมูลผู้ใช้จริง (AI-07)
- **ขั้นตอน:** `load.py` ยิง `Gateway` ตัวจริง (prompt, `ai.yaml` 1.27, retry, SymPy) ด้วย provider `gemini` ตาม flow ของห้องติว · นับทุก attempt ที่ provider · 5 รอบบน `gemini-3.5-flash-lite`: burst 1 คน (ไม่มี think time · 16 request) · smoke think 30 s (1 session 3 โจทย์) · session 10 โจทย์ (68 request) · daily 40 session concurrency 3 (118 request) · และ `gemini-3.5-flash` 6 call
- **ingestion:** ไม่รัน · ประมาณจาก `ai_calls` และ log ของการซ้อม 20 พ.ย. (6 ไฟล์ · 116 chunk)
- **ไม่ได้ทดสอบ:** ชน RPD 500 จริง (ชน RPM ก่อน) · ingestion ทั้ง pipeline และ embedding · คุณภาพการสอนเทียบ Vertex (ต้องใช้ golden set ของ Jam) · session ที่ล้มในสคริปต์เริ่ม session ใหม่ทันที (ห้องจริงไม่ทำ) จึงยิงถี่กว่าผู้ใช้จริงในนาทีท้ายของรอบ daily

## 3. ผล

| Metric | เกณฑ์ผ่าน | ผล | PASS / FAIL |
|---|---|---|---|
| โควตา free tier | ได้ตัวเลขครบ | flash-lite **15 RPM · 250K TPM · 500 RPD** · `gemini-3.5-flash` ไม่มีใน free tier: AI Studio นับเป็น **Gemini 3.6 Flash 5 RPM · 20 RPD** (6 call ผ่าน แต่หน้า Usage นับใส่ 3.6 Flash) · `gemini-embedding-2` **100 RPM · 30K TPM · 1K RPD** | **PASS** |
| ต้นทุนต่อโจทย์ (flash-lite · n = 10 โจทย์) | มีตัวเลข | **6.5 request · 8.7K token in · 0.85K out** (รวม retry) · session 3 โจทย์ + chat 2 = 21 request | **PASS** |
| (ก) dev ของทีม ≥ 5 session/วัน [C] | ≥ 5 | flash-lite: 500 ÷ 21 ≈ **23** session 3 โจทย์ · 500 ÷ 68 ≈ **7** session 10 โจทย์ · 3.6 Flash: 20 ÷ 21 < **1** | flash-lite **PASS** · Flash **FAIL** |
| (ข) demo กับเพื่อน 1 กลุ่ม ≥ 30 session/วัน [C] | ≥ 30 | สูงสุด 23 (3 โจทย์) · 7 (10 โจทย์) | **FAIL** |
| (ค) ผู้ใช้พร้อมกันโดยไม่โดน 429 | ยืนยันด้วย burst | ผู้ใช้ 1 คนแบบคนจริง (think 30 s) peak **12 request/นาที** ใน 15 RPM · 0 ครั้ง 429 · ผู้ใช้ 1 คนยิงต่อกันชน RPM ที่ request 16 · **ผู้ใช้ 3 คน: 429 39/118 (33%) ต่อนาทีทั้งหมด · จบ 1/40 session** · token ~16K/นาที ไกลจาก 250K → ตัวจำกัดคือ RPM | **1 คน** |
| คุณภาพ: ห้องต้องไม่ไม่มีโจทย์เพราะ schema fail | ไม่มี | session 10 โจทย์: `generate_problem` schema error 3/13 call (23%) หลัง retry แต่ได้โจทย์ครบ 10 · SymPy ยืนยันทุกข้อ · `check_answer` ไม่มี schema error | **PASS** (เสีย request เพิ่ม) |
| latency flash-lite | (ดูประกอบ) | call p50 0.9 s · `tutor_reply` TTFT p95 1.0 s · `explain_check` TTFT p95 2.4 s · 503 "high demand" 2 ครั้งใน ~230 request | — |
| ingestion 1 วิชา (ประมาณ) | ดูประกอบ | ~17 generate request · input สูงสุด 46K/call · flash-lite: 3% ของ RPD แต่ P3 ตัด flash-lite ออกจาก A5/A6 เพราะคุณภาพ · 3.6 Flash: 17/20 RPD = 1 วิชา/วันไม่เหลือให้ติว · embedding: 116 chunk แต่ token ต่อ call สูงสุด 45.7K > 30K TPM → ต้องกระจายเกิน 1 นาที | **ไม่พอ** (คุณภาพ / RPD) |

## 4. การตัดสินใจ

**คงแผนเดิม: Vertex เป็นทางหลักของ staging, demo และ Beta** · free tier ใช้ได้แค่ **dev ของคนเดียวกับ `gemini-3.5-flash-lite` ในห้องติว** (ราว 7–23 session/วัน · ผู้ใช้ทีละ 1 คน) · ไม่ใช้กับ ingestion (คุณภาพของ flash-lite ไม่พอตาม P3 และ Flash ได้ 20 RPD) · ไม่ใช้กับ demo กับเพื่อน (FAIL ทั้ง session/วันและผู้ใช้พร้อมกัน) · ถ้าใช้ free tier ต้องตั้ง model เป็น flash-lite เอง เพราะ `gemini-3.5-flash` ใน `ai.yaml` จะได้ 3.6 Flash ที่ 20 RPD

## 5. สิ่งที่ต้องแก้ใน spec / config (เสนอ · ยังไม่แก้ · รอ Junior / Jam ok)

- [ ] `config/learning.yaml`: ไม่แก้
- [ ] `config/ai.yaml`: ไม่แก้ค่า · เสนอเพิ่ม comment ที่ `provider` ว่า "free tier (AI Studio): dev เท่านั้น · override เป็น `gemini:gemini-3.5-flash-lite` · `3.5-flash` ถูกนับเป็น 3.6 Flash 20 RPD (P9-lite)" (Jam ตัดสิน model)
- [ ] `docs/team/setup.md` "env สำหรับ dev": วิธีใช้ AI Studio key แทน Vertex (`AI_MODEL_OVERRIDE=gemini:gemini-3.5-flash-lite`) + เพดาน 1 คน / 15 RPM
- [ ] `specs/system/architecture.md`: แถว P9-lite ในตารางผล PoC ("free tier ไม่พอสำหรับ demo · Vertex คงเดิม")
- [ ] `specs/poc/README.md` P9-lite: ติ๊กว่าเสร็จ + ลิงก์ report นี้

## 6. ความเสี่ยงที่เหลือ

- ตัวเลขโควตาไม่รับประกันและเปลี่ยนได้โดยไม่แจ้ง (เอกสารทางการเลิกลงตัวเลขแล้ว) · RPD 500 ยังไม่ได้ยืนยันด้วยการชนจริง
- schema error 23% ของ `generate_problem` บน flash-lite (น่าจะ JSON + LaTeX แบบ P3) · ส่งต่อ Jam · บน Vertex ยังไม่ได้วัดอัตรานี้แยก
- การ map ชื่อ `gemini-3.5-flash` → 3.6 Flash บน AI Studio อาจเปลี่ยนอีก · dev ที่ใช้ key ผิดโปรเจกต์ (ผูก billing) จะเสียเงินโดยไม่รู้ตัว
