# Glossary

| คำ | ความหมาย |
|---|---|
| Exam prep | การเตรียมสอบ 1 ครั้ง ประกอบด้วยวิชา วันสอบ และไฟล์ |
| Material | ไฟล์ที่ upload เช่น ชีท สไลด์ ข้อสอบเก่า โน้ต |
| Topic | หัวข้อที่ต้องสอบ สกัดจากเอกสาร มีดาว 0–3 |
| Skill | ประเภทโจทย์ย่อยในหัวข้อ เช่น "ผลต่างกำลังสอง" ในการแยกตัวประกอบ (ซ่อนใน UI แก้ผ่าน chat ได้) |
| signal_r | สัดส่วน (ถ่วงน้ำหนัก) ของข้อสอบเก่าที่หัวข้อนี้ออก |
| Scope version | snapshot ของรายการหัวข้อที่ user ยืนยันแล้ว |
| Stage | สถานะการสอนของหัวข้อ: Probe, Teach, Verify, Practice, Done, Park |
| Directive | คำสั่งที่ code ส่งให้ LLM ว่า turn นี้ต้องทำอะไร |
| Attempt | การตอบโจทย์ 1 ครั้งพร้อมผลตรวจ |
| Independent attempt | attempt ที่ไม่ได้ทำทันทีหลัง tutor สาธิต นับเข้า mastery |
| Mastery | ความน่าจะเป็นว่าเข้าใจหัวข้อแล้ว คำนวณด้วย BKT (0–1) ผ่านที่ 0.95 |
| BKT | Bayesian Knowledge Tracing โมเดลประเมิน mastery จากลำดับถูก/ผิด |
| Verdict | ผลตรวจ: correct, correct_with_flaw, incomplete, incorrect |
| Error type | calculation, sign, wrong method, concept, prerequisite, no answer |
| Park | พักหัวข้อหรือ skill ไว้ก่อน (ผิดซ้ำหรือทำเกินเพดานต่อวัน) |
| Spaced review | การทวนหัวข้อที่ผ่านแล้วตามรอบที่ห่างขึ้นเรื่อยๆ |
| Readiness | ความพร้อม % = Σ(r × mastery_eff) ÷ Σr · mastery_eff = mastery หลังเพดานตามระดับยากสุดที่ทำถูกเอง (learning-model §4) |
| Planner mode | normal, tight, triage, final ตามเวลาที่ต้องใช้เทียบกับเวลาที่เหลือ |
| Progress card | dashboard ย่อในแชทตอนเปิด session |
| Tenant | หน่วยแยกข้อมูลและโควตา v1 คือนักเรียน 1 คน |
| RLS | Row Level Security: กฎใน Postgres ที่กันไม่ให้อ่านแถวของ tenant อื่น |
| SSE | Server-Sent Events: server ส่งข้อความทีละส่วนไป browser |
| TTFT | เวลาจนเห็นตัวอักษรแรกของคำตอบ |
| Gateway | `ai.call()` จุดเดียวที่เรียก AI ทุกครั้ง มี guard, routing, fallback, log |
| Golden set | ชุดข้อมูลพร้อมเฉลยที่ทีมทำเอง ใช้วัดผล AI |
| SDD / TDD | Spec-Driven / Test-Driven Development |
