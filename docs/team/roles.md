# หน้าที่ของแต่ละคน · เทอม 1

อัปเดต 12 ต.ค. 2569 · ใช้คู่กับ `sprint-checklists.md` (งานราย sprint) และ `setup.md` (วิธีตั้งค่า)

ทุกคนเขียนโค้ดด้วย Claude Code เป็นหลัก แต่ **คนเป็นเจ้าของผลงาน** หน้าที่ของเราคือเขียน spec ให้ชัด, review test ก่อน AI เขียนโค้ด, review โค้ดก่อน merge และตัดสินใจจากผล PoC

## สรุปใน 1 ตาราง

| | Junior (มนสิชา) | May (จันทรัศม์) | Jam (เวสสภู) |
|---|---|---|---|
| GitHub | `@jnmonsicha2000` | `@jantarat32443` | `@jamvess` (เจ้าของ repo) |
| บทบาท | Backend + DevOps | Frontend + UX | AI + การวัดผล |
| เป็นเจ้าของโฟลเดอร์ | `apps/api/`, `supabase/`, `infra/`, `.github/` | `apps/web/`, wireframe/Figma | `prompts/`, `evals/`, `config/learning.yaml`, `specs/system/ai-orchestration.md`, `learning-model.md` |
| PoC | P6-lite, backend ของ P4-lite, SymPy service ให้ P2 | หน้าแชทของ P4-lite | P1, P3, P2 |
| Deliverables | D2 (architecture), D3, D4, D5 | D6, D7 | D2 (AI flows), D8 |
| Review PR ของ | May (ส่วนที่ต่อ API), Jam (โค้ด Python) | Junior (ส่วนที่กระทบ UI/UX) | Junior (domain logic, config) |
| ตัดสินใจเรื่อง | โครงสร้าง backend, DB, deploy, สิทธิ์ cloud | หน้าตาและ flow ของหน้าจอ | prompt, model, threshold, เกณฑ์วัดผล |
| เวลา | ~12.5 ชม./สัปดาห์ | ~12.5 ชม./สัปดาห์ | ~12.5 ชม./สัปดาห์ |

งานที่ทำร่วมกัน: D1 SRS v1.1, P8-lite (SDD/TDD), label ข้อมูลให้กันและกัน, รายงานและนำเสนอปลายเทอม

---

## Junior · Backend + DevOps

**ดูแลให้ระบบ "ต่อกันได้และขึ้นเว็บได้"** ทุกคนต้องทำงานบน repo, CI และ staging ที่ Junior ตั้งไว้ จึงต้องเสร็จก่อนคนอื่นใน S1–S2

หน้าที่หลัก

- ตั้ง repo, branch protection, CI (GitHub Actions), Cloud Build, Cloud Run, Secret Manager, Supabase dev/staging
- ดูแล data model (`supabase/migrations/`) และ RLS ทุกตารางต้องมี isolation test
- สร้างโครง FastAPI และ API spec (หน้า `/docs`) ให้ May ใช้ generate type
- เขียน AI gateway แบบ lite (provider interface + fake provider + log `ai_calls`) ให้ Jam ใช้
- เขียน SymPy service ให้ Jam ใช้ใน P2
- ช่วย Jam ทำ ingest pipeline ของ P3 (อ่าน PDF, ตัด chunk, เก็บลง DB)
- ดูแลเรื่อง secret: ไม่มี key ใน repo, ทุกคนมีสิทธิ์ cloud เท่าที่จำเป็น

สิ่งที่ส่งมอบ: P6-lite report, `schema.sql` + ERD, API spec, architecture ใน `specs/system/`

## May · Frontend + UX

**ดูแลให้สิ่งที่ผู้ใช้เห็น "ตรงกับ design ที่อาจารย์โอเคแล้ว"** และเป็นคนเล่า flow ของผู้ใช้ผ่าน wireframe และ use case

หน้าที่หลัก

- อัปเดต wireframe ตาม design ใหม่ (S05 คำแนะนำ persona, S08 นาทีต่อวัน, S15 progress card)
- เขียน use case scenarios 4 UC หลักแบบละเอียด (main flow, alternative, exception)
- สร้างโครง Next.js และหน้าแชทของ P4-lite (stream ข้อความ, KaTeX, ปุ่มส่งรูป)
- พิมพ์เฉลยของรูปลายมือให้ P1 และช่วย label หัวข้อให้ P3 (คน label ต้องไม่ใช่คนทำ PoC)
- รักษากฎของ UI: ห้องติวไม่มีปุ่ม choice, ตัวเลขทุกตัวมาจาก API

สิ่งที่ส่งมอบ: wireframe อัปเดต, use case 4 UC, หน้าแชทของ P4-lite, report P4-lite (ร่วมกับ Junior)

## Jam · AI + การวัดผล

**ดูแลให้ AI "แม่นพอและวัดได้"** ทุกตัวเลขของ AI ต้องมีที่มา ไม่ว่าจะมาจากงานวิจัยหรือจากการวัดของเราเอง

หน้าที่หลัก

- ย้าย AI flows 2.1–2.11 เข้า `specs/system/` และอัปเดตตามผล PoC
- เขียน prompt (`prompts/`) และ eval (`evals/`) ของ P1, P2, P3
- ทำ PoC P1 (อ่านลายมือ), P3 (เอกสาร → หัวข้อ + ดาว), P2 (ตรวจคำตอบ)
- ดูแล `config/learning.yaml` และ `learning-model.md` เมื่อเปลี่ยนตัวเลขต้องอัปเดตที่มา
- นำเรื่องงานวิจัยรองรับ learning path และ progress tracking (ตามที่อาจารย์แนะนำ)
- เขียน test strategy 1 หน้า

สิ่งที่ส่งมอบ: golden sets, report P1 P2 P3, AI flow specs ฉบับอัปเดต

---

## กติการ่วม

- **PR ทุกอันต้องมีคน review 1 คน** ตาม CODEOWNERS ไม่ merge งานตัวเอง
- **Review test ก่อน implement** คนที่ review test ควรเป็นคนละคนกับคนที่เขียน spec
- **ติดเกิน 1 วันให้บอกในแชทกลุ่ม** อย่ารอจน demo
- **คนที่เปลี่ยน spec หรือ config** ต้องบอกในแชทกลุ่ม เพราะกระทบงานคนอื่น
- **ตัวเลขทุกตัวใน learning model** ต้องมี source หรือแผน calibrate (ดู `learning-model.md`)

## ใครถามใคร

| เรื่อง | ถาม |
|---|---|
| API ไม่ตรงกับที่หน้าจอต้องการ, deploy พัง, สิทธิ์ cloud, DB | Junior |
| หน้าจอควรเป็นยังไง, flow ของผู้ใช้, ข้อความที่แสดง | May |
| Prompt, model, ทำไม AI ตอบแบบนี้, ตัวเลข threshold | Jam |
| scope ของงาน, ลำดับความสำคัญเมื่อเวลาไม่พอ | คุยกันทั้งทีมตอนวางแผน sprint |
