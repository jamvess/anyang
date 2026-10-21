# Requirements (v1.2)

สรุปจาก SRS v1.0 พร้อมการเปลี่ยนแปลงหลังออกแบบ AI orchestration (30 ก.ย. 2569) ใช้ ID ในตารางนี้อ้างอิงใน feature spec, test และ PR

**v1.2 (19 ต.ค. 2569 · review D1 ฝั่ง UI/UX):** ข้อ `changed` เขียนความหมายปัจจุบันในช่อง Requirement และบอกของเดิมในหมายเหตุ · CM-01 เวลาต่อวันไม่บังคับ · เพิ่ม TM-20, TM-21, NFR-A1 · อัปเดตคอลัมน์ Screen ตาม wireframe ที่แก้แล้ว (`docs/design/wireframe-s2-review.md`)

**Status:** `active` ใช้ตามเดิม · `changed` แก้ความหมายแล้ว (ช่อง Requirement เป็นความหมายปัจจุบัน หมายเหตุบอกของเดิม) · `new` เพิ่มใหม่ใน v1.1 · `deferred` เลื่อนไปหลัง pilot · `obsolete` ยกเลิก

Screen ID (S01–S27) อ้างอิงถึง wireframe

## UM · User & persona

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| UM-01 | ระบบต้องให้ user สมัครสมาชิกด้วย email และ password | Must | S02 | active |  |
| UM-02 | ระบบต้องรองรับ Google OAuth โดยขอ scope เพียงชื่อ email และรูป profile | Must | S02, S03 | active |  |
| UM-03 | ระบบต้องให้ user เลือก AI Tutor จาก preset ไม่น้อยกว่า 3 แบบ โดยแสดงตัวอย่างประโยคของแต่ละแบบ | Must | S04 | active |  |
| UM-04 | ระบบต้องให้ user เลือก AI Buddy จาก preset หรือเลือกไม่ใช้ AI Buddy ก็ได้ | Must | S04 | active |  |
| UM-05 | ระบบต้องให้ user custom persona ของ AI Tutor และ AI Buddy ด้วยการ describe เป็น free text โดยระบบแปลงเป็น parameter ที่กำหนดไว้ ไม่นำ text ของ user ไปใช้เป็น prompt โดยตรง | Must | S05 | active |  |
| UM-06 | ระบบต้องแสดง checklist ว่าควร describe เรื่องอะไรบ้าง และ mark หัวข้อที่ user เขียนถึงแล้วอัตโนมัติ | Should | S05 | deferred | เลื่อนไปหลัง pilot |
| UM-07 | ระบบต้อง preview ตัวอย่างประโยคที่ได้จาก description ให้ user ดูก่อน save | Should | S05 | changed | เดิมรวมการทดลองฟังเสียงด้วย ซึ่งเลื่อนไปหลัง pilot · ประโยคตัวอย่างมาจาก `persona_preview` (ai-orchestration 2.7) |
| UM-08 | ระบบต้องให้ user ตั้งชื่อเล่น ระดับการศึกษา และภาษาที่ใช้อธิบาย | Must | S06 | active |  |
| UM-09 | ระบบต้องให้ user แก้ persona และ setting ได้ตลอดเวลาหลังสมัครสมาชิก | Must | ยังไม่มีหน้าจอ | active | ต้องเพิ่มหน้าตั้งค่าใน wireframe (D6 · S4) |
| UM-10 | ระบบต้องให้ user ลบ account และข้อมูลทั้งหมดของตัวเองได้ | Must | ยังไม่มีหน้าจอ | active | ต้องเพิ่มในหน้าตั้งค่าใน wireframe (D6 · S4) |

## CM · Content & exam prep

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| CM-01 | ระบบต้องให้ user สร้าง exam prep โดยระบุชื่อการสอบและวันสอบ และระบุเวลาที่ติวได้ต่อวันได้โดยไม่บังคับ | Must | S08 | changed | เดิมเวลาต่อวันเป็นช่องบังคับ · ถ้าไม่ระบุ planner ใช้ค่าเริ่มต้นจาก config แล้วปรับจากการใช้งานจริง (ai-orchestration 2.5.2, `exam_preps.daily_minutes` nullable) |
| CM-02 | ระบบต้องแสดงจำนวนวันที่เหลือก่อนสอบโดยคำนวณอัตโนมัติจากวันสอบ | Must | S08, S27 | active |  |
| CM-03 | ระบบต้องรองรับการ upload หลายไฟล์พร้อมกัน รองรับ PDF รูปภาพ และไฟล์เอกสาร | Must | S09 | active |  |
| CM-04 | ระบบต้องมีช่องให้ user เขียน note กำกับแต่ละไฟล์ในขั้นตอน upload โดยไม่บังคับกรอก และส่ง note เข้าไป process พร้อมเอกสาร | Must | S09 | active |  |
| CM-05 | ระบบต้องให้เพิ่มไฟล์ทีหลังได้ และ process เฉพาะไฟล์ใหม่ ไม่ process ไฟล์เดิมซ้ำ | Must | S09 | active |  |
| CM-06 | ระบบต้อง classify ประเภทไฟล์อัตโนมัติ พร้อมแสดง confidence และให้ user confirm หรือแก้ก่อน process | Must | S10 | active |  |
| CM-07 | ระบบต้องแสดง processing status เป็นราย file และแจ้ง progress ระหว่างรอ | Must | S11 | active |  |
| CM-08 | ระบบต้องย้าย exam prep ที่พ้นวันสอบไป archive โดยไม่ลบข้อมูลและไฟล์ | Should | S27 | active |  |
| CM-09 | ระบบต้องให้ user เปิด exam prep ที่ archive ไว้กลับมาใช้ต่อ และเพิ่มไฟล์ใหม่เข้าไปได้ | Should | S27 | active |  |
| CM-10 | ระบบต้องให้ user ลบไฟล์รายไฟล์ หรือลบ exam prep ทั้งรายการได้ | Must | ยังไม่มีหน้าจอ | active | ต้องเพิ่มหน้าจัดการไฟล์ของการเตรียมสอบใน wireframe (D6 · S4) |

## SM · Scope

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| SM-01 | ระบบต้อง extract topic ที่ต้องเตรียมสอบจากเอกสารที่ upload โดยใช้เฉพาะ content ในเอกสารเป็น source | Must | S12 | active |  |
| SM-02 | ระบบต้องจัดลำดับ topic ตาม prerequisite ก่อนหลัง | Must | S12 | active |  |
| SM-03 | ระบบต้องกำหนด importance ของแต่ละ topic เป็นดาว 1 ถึง 3 โดยดูจากความถี่ที่ปรากฏในข้อสอบเก่าและ note ที่ user เขียนกำกับไฟล์ | Must | S12 | active |  |
| SM-04 | ระบบต้องแสดง source reference ของแต่ละ topic เป็นชื่อไฟล์และเลขหน้า และให้ user กดดู text ต้นฉบับได้ | Must | S12 | active |  |
| SM-05 | ระบบต้องเสนอ topic ที่ควรตัดออกจาก scope พร้อมเหตุผลประกอบ | Should | S12 | deferred | เลื่อนไปหลัง pilot |
| SM-06 | ระบบต้องให้ user แก้ scope ผ่าน chat ทั้งการพิมพ์และการพูด โดยไม่ต้องหาปุ่มแก้ | Must | S13 | active |  |
| SM-07 | ระบบต้อง update รายการ topic ให้เห็นผลทันทีทุกครั้งที่ตกลงเปลี่ยนแปลงระหว่าง chat | Must | S13 | active |  |
| SM-08 | ระบบต้องแสดงหน้าสรุป change log พร้อมเหตุผล และให้ user กด confirm ก่อนเริ่มติว | Must | S14 | active |  |
| SM-09 | ระบบต้อง persist scope decision และไม่ถามซ้ำตลอดอายุของ exam prep นั้น | Must | — | active |  |
| SM-10 | เมื่อ user ถามเรื่องที่อยู่นอก scope ระบบต้องตอบสั้นๆ แจ้งว่าอยู่นอก scope เสนอให้เพิ่มเข้า scope และดึง conversation กลับสู่ topic เดิม | Must | S20 | active |  |
| SM-11 | ระบบต้องไม่สอนวิธีที่ไม่ปรากฏในเอกสารของ user เว้นแต่ได้รับ confirm จาก user ก่อน | Must | — | active |  |
| SM-12 | แต่ละ topic มี skills (ประเภทโจทย์ย่อย) ที่ระบบสกัดเอง ไม่แสดงในหน้า scope แต่ user ตัดหรือเพิ่ม skill ผ่าน chat ได้ (op exclude_skill / include_skill) | Must | S13 | new | |

## TM · Tutoring

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| TM-01 | ระบบต้องเป็นผู้ตัดสินใจเลือก topic ที่จะติวถัดไป โดยดูจาก importance, mastery ของ user และจำนวนวันที่เหลือ user ไม่ต้องวางแผนเอง | Must | S15 | active |  |
| TM-02 | ระบบต้องแจ้งเหตุผลของการเลือก topic สั้นๆ แต่ต้องไม่แสดง study plan ทั้งหมดล่วงหน้า | Must | S15 | active |  |
| TM-03 | ระบบต้อง probe ความรู้เดิมด้วยโจทย์ก่อนเริ่มอธิบาย และข้ามการอธิบายพื้นฐานเมื่อ user ตอบถูก | Must | S15, S16, S19 | active |  |
| TM-04 | ระบบต้องดำเนินการติวแบบสลับระหว่าง explain กับ practice ทีละ topic ตามลำดับที่กำหนดไว้ | Must | S15–S23 | active |  |
| TM-05 | AI Buddy ต้องแทรก conversation ตาม rule ที่ code กำหนดเท่านั้น: พูดได้ 4 roles, ผ่าน hard gates (ไม่แทรกขณะรอคำตอบจาก user, ไม่เกิน quota ตามความถี่ใน persona, เว้นระยะจากครั้งก่อนตาม config), ห้ามตอบถูกเมื่อ user เพิ่งตอบผิดติดกัน และตอบเรื่องนอกบทเรียนได้ 1 ประโยค | Must | S17, S26 | changed | เดิม: quota ต่อ topic + ห้ามตอบโจทย์ขณะรอคำตอบ + ห้ามตอบถูกเมื่อ user ผิดติดกัน (ai-orchestration 2.1) |
| TM-06 | ระบบต้องรับคำตอบ 3 ทาง คือ พิมพ์ พูดผ่าน microphone และส่งรูป โดยต้องไม่มีปุ่ม choice ให้กดตอบในห้องติว | Must | S15–S26 | active |  |
| TM-07 | ระบบต้องแปลง speech เป็น text แล้วใส่ในช่องพิมพ์ให้ user แก้และกดส่งเอง โดยไม่ส่งอัตโนมัติ | Should | S13, S18 | changed | เดิม: ทวน text ให้ confirm เฉพาะเมื่อ confidence ต่ำ (ai-orchestration 2.2.5) |
| TM-08 | ระบบต้อง render สมการคณิตศาสตร์ให้จัดหน้าถูกต้อง | Must | S15–S26 | active |  |
| TM-09 | ระบบต้องให้ user สั่ง TTS อ่านข้อความของ AI Tutor เป็นราย message และตั้ง auto-play ได้ โดย default คือปิด | Must | S05, S16 | active |  |
| TM-10 | เมื่อ user ตอบไม่ตรงคำถามหรือตอบไม่ชัดเจน ระบบต้องถามกลับให้แคบลง แทนการอธิบายเนื้อหาเดิมซ้ำทั้งหมด | Must | S19 | active |  |
| TM-11 | เมื่อ user ขอดู progress ระบบต้องแสดง progress card ใบเดียวกับ TM-15 ในแชท พร้อมสรุปสั้นๆ โดยไม่ต้องมีหน้า dashboard แยก | Must | S24 | changed | เดิม: รายงานเป็นข้อความในแชทอย่างเดียว (ai-orchestration 2.2.2) |
| TM-12 | ระบบต้องเสนอให้จบ session เมื่อครบเป้าหมาย หมดเวลาที่ตั้งไว้ หรือประเมินว่า user พร้อมแล้ว แต่ต้องไม่บังคับให้จบ | Must | S26 | active |  |
| TM-13 | ระบบต้องให้ user ออกจากห้องติวระหว่างทางและกลับมาติวต่อจากจุดเดิมได้ | Must | S27 | active |  |
| TM-14 | ระบบต้องไม่ generate mock exam แบบจับเวลา ให้โจทย์ทีละข้อระหว่าง chat เท่านั้น | Must | — | active |  |
| TM-15 | ทุกครั้งที่เปิด session ระบบต้องแสดง progress card (หัวข้อ ดาว ระดับ ความพร้อม %) ที่ render จาก DB แล้วให้ tutor สรุป 2–3 ประโยคจาก facts ที่ code คำนวณ แล้วส่งโจทย์ข้อแรกทันที | Must | S15 | new | |
| TM-16 | topic นับว่าผ่านเมื่อทุก skill ที่เคยออกสอบมี independent correct อย่างน้อย 1 ครั้ง และ mastery ถึง threshold ใน config | Must | — | new | |
| TM-17 | topic ที่ผ่านแล้วต้องถูกนำกลับมาทวนตามรอบ spaced review ที่คำนวณจากจำนวนวันที่เหลือก่อนสอบ ถ้าทวนผิดให้ลดระดับ | Must | S15 | new | |
| TM-18 | planner ต้องเลือก mode (normal, tight, triage, final) จากเวลาที่ต้องใช้เทียบกับเวลาที่เหลือ และบอก user เมื่อ mode เปลี่ยน | Must | S15 | new | |
| TM-19 | ระบบต้อง Park skill ที่ทำเกินเพดานโจทย์ต่อวันโดยยังไม่ผ่าน และพาไปทวน prerequisite หรือกลับมาวันหลัง | Must | — | new | |
| TM-20 | ห้องติวต้องแสดงข้อความของ AI Tutor, AI Buddy และ user แยกกันชัดเจน แต่ละข้อความมีชื่อผู้พูดและเวลา และ render สมการตาม TM-08 | Must | S15–S26 | new | spec: `specs/features/tutor/chat-room-ui.md`, `specs/features/tutor/chat-streaming.md` |
| TM-21 | ระบบต้องบอก user เมื่อข้อความยาวเกิน แนบไฟล์ที่ไม่ใช่รูป หรือรูปใหญ่เกิน โดยขีดจำกัดมาจาก config (`config/ai.yaml` → `guards`) ไม่ hard-code | Should | S15–S26 | new | API ส่งค่าขีดจำกัดมากับข้อมูลห้อง (ข้อเสนอใน PR #16) |

## AM · Answer checking

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| AM-01 | ระบบต้องอ่านคำตอบที่เขียนด้วยลายมือจากรูป และแปลงเป็น LaTeX ที่ render ได้ | Must | S21 | active |  |
| AM-02 | ระบบต้องแสดงผลที่อ่านได้ให้ user confirm ก่อนตรวจทุกครั้งที่ส่งรูป | Must | S21 | changed | กลับเป็นแบบเดิมตามผล PoC P1 (21 ต.ค. · ทีมตกลงใน PR #45): confidence ที่ model ให้ตัวเองแยกบรรทัดที่อ่านผิดไม่ได้ · ฉบับก่อนหน้า: confirm เฉพาะเมื่อ confidence ต่ำกว่า threshold |
| AM-03 | ระบบต้อง log กรณีที่ user แจ้งว่าอ่านผิด เพื่อใช้วัด OCR accuracy | Should | — | active |  |
| AM-04 | ระบบต้องตรวจคำตอบโดยดู mathematical equivalence ไม่ใช่เทียบ string ตรงตัว | Must | — | active |  |
| AM-05 | เมื่อคำตอบผิด ระบบต้องระบุบรรทัดแรกที่ผิด ไม่ใช่แจ้งแค่ว่าผิด | Must | S22 | active |  |
| AM-06 | ระบบต้อง classify error อย่างน้อย 6 ประเภท ได้แก่ calculation, sign, wrong method, concept, prerequisite และ no answer | Must | S22 | active |  |
| AM-07 | เมื่อคำตอบผิด ระบบต้องอธิบายวิธีแก้ทันที โดยไม่ให้ hint แล้วให้ลองใหม่ และไม่ถามว่า user งงตรงไหน | Must | S22 | active |  |
| AM-08 | ระบบต้องออกโจทย์แบบเดียวกันเพื่อวัดความเข้าใจ แทนการถามว่าเข้าใจแล้วหรือยัง | Must | S23 | active |  |
| AM-09 | เมื่อ user ยังไม่เข้าใจหลังอธิบายแล้ว ระบบต้องอธิบายด้วยมุมมองที่ต่างจากครั้งก่อน | Must | S25 | active |  |
| AM-10 | ระบบต้อง log ว่า user ขอ hint หรือไม่ และไม่นับว่า pass เต็มถ้าตอบถูกหลังขอ hint | Should | — | obsolete | ระบบไม่มี hint (AM-07) จึงไม่ต้อง log การขอ hint |
| AM-11 | โจทย์ทุกข้อต้องมี answer_format และเฉลยที่ผ่าน SymPy verify ก่อนส่งถึง user | Must | — | new | |
| AM-12 | user แย้งผลตรวจได้ ระบบตรวจซ้ำด้วย model ใหญ่ ถ้าพลิกผลให้แก้ attempt และคำนวณ mastery ใหม่ | Should | S22 | new | |
| AM-13 | tutor reply ต้องไม่มีเฉลยของโจทย์ที่ยังรอคำตอบ (answer-leak check แบบ deterministic) | Must | — | new | |

## PM · Progress

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| PM-01 | ระบบต้องบันทึกทุก attempt ประกอบด้วย topic, skill, โจทย์, คำตอบ, verdict, error type, first_wrong_line และ independent | Must | — | changed | เดิมรวมการขอ hint ซึ่งไม่มีแล้ว (AM-07) |
| PM-02 | ระบบต้อง maintain mastery state รายหัวข้อ และ update ตามผลการตอบ | Must | — | active |  |
| PM-03 | ระบบต้องคำนวณ readiness = Σ(r × mastery) ÷ Σr จาก mastery รายหัวข้อ ถ่วงด้วยสัดส่วน r ที่หัวข้อออกในข้อสอบเก่า | Must | S15, S24, S27 | changed | เดิมมี decay เมื่อไม่ได้ทบทวน ซึ่งแทนด้วย spaced review (TM-17) · learning-model §5 |
| PM-04 | ระบบต้องแสดง readiness และจำนวน topic ที่ยังไม่แม่นบนหน้า home | Must | S27 | active |  |
| PM-05 | ระบบต้อง summary ผลการติวเมื่อจบ session ในรูปแบบ chat message สั้นๆ โดยไม่ต้องมีหน้า report แยก | Must | S26 | active |  |
| PM-06 | ข้อมูล weak topic และ progress ต้องแยกตาม exam prep ไม่นำข้อมูลข้ามรายการมารวมกัน | Must | — | active |  |
| PM-07 | ระบบควรนำ weak topic จาก session ก่อนมา warm-up ในช่วงต้นของ session ถัดไป | Could | — | deferred | แทนด้วย spaced review (TM-17) |

## AI · AI platform

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| AI-01 | การเรียก AI ทุกครั้งต้องผ่าน AI Provider Layer เท่านั้น ห้ามเรียก external SDK โดยตรงจากส่วนอื่นของระบบ | Must | — | active |  |
| AI-02 | ระบบต้องสลับ LLM provider ได้ด้วยการแก้ config โดยไม่ต้องแก้ business logic | Must | — | active |  |
| AI-03 | ระบบต้องมี fake provider ที่ให้ output คงที่ เพื่อใช้ใน automated test โดยไม่เกิด cost | Must | — | active |  |
| AI-04 | ระบบต้อง log จำนวน token ที่ใช้ทุกครั้งที่เรียก แยกตาม user และประเภทงาน | Must | — | active |  |
| AI-05 | ระบบต้อง validate structured output จาก AI ตาม schema ที่กำหนด และ retry ไม่เกิน 2 ครั้งเมื่อ format ไม่ถูก | Must | — | active |  |
| AI-06 | ระบบควรใช้ prompt caching กับส่วนของ prompt ที่ส่งซ้ำทุกครั้ง เพื่อลด cost | Should | — | active |  |
| AI-07 | ระบบต้องไม่ส่งข้อมูลของ user จริงผ่าน free tier ที่มีเงื่อนไขนำข้อมูลไป train โมเดล ตั้งแต่ระยะ Beta เป็นต้นไป | Must | — | active |  |
| AI-08 | ระบบต้องเก็บ text ต้นฉบับของ chunk คู่กับ vector เสมอ เพื่อให้ re-index ได้หากเปลี่ยน embedding model | Must | — | active |  |

## SA · SaaS & security

| ID | Requirement | Priority | Screen | Status | หมายเหตุ |
|---|---|---|---|---|---|
| SA-01 | Database ต้องรองรับ role 3 ระดับ คือ student, teacher และ admin | Must | — | active |  |
| SA-02 | Database ต้องรองรับการจัดกลุ่ม user ภายใต้ institution หรือ organization โดย v1 ใช้ personal tenant ต่อ user | Must | — | changed | schema มี tenants, org_units, memberships รองรับ organization ภายหลัง |
| SA-03 | ระบบต้อง log usage ราย user ได้แก่ จำนวน token จำนวน message และ storage ที่ใช้ | Must | — | active |  |
| SA-04 | Database ต้องรองรับการกำหนด quota ตาม plan | Should | — | active |  |
| SA-05 | Database ต้องมี field รองรับ billing แต่ไม่เชื่อม payment gateway จริงในโปรเจกต์นี้ | Should | — | active |  |
| SA-06 | ระบบต้องบังคับ data isolation ระหว่าง user ที่ระดับ database เพื่อให้ user หนึ่งเข้าถึงข้อมูลของอีกคนไม่ได้ แม้ backend logic จะเขียนผิด | Must | — | active |  |
| SA-07 | ระบบต้องให้ user export และลบข้อมูลของตัวเองได้ | Should | — | deferred | เลื่อนไปหลัง pilot |
| SA-08 | ระบบควรเก็บ analytics ราย user และรายวิชาเพื่อการวิเคราะห์ | Could | — | deferred | เลื่อนไปหลัง pilot |
| SA-09 | เมื่อพบสัญญาณความเครียดรุนแรงหรือการทำร้ายตัวเอง ระบบต้องตอบด้วย template ที่ดูแลความรู้สึกพร้อมสายด่วน 1323 และไม่ให้ buddy เล่นมุก | Must | — | new | |
| SA-10 | ไฟล์เสียงเก็บไม่เกิน 7 วัน prompt/response เต็มเก็บไม่เกิน 30 วัน หลังจากนั้นเก็บเฉพาะ metadata | Should | — | new | |

## Non-functional requirements (สรุป)

| ID | Requirement | ค่า | ที่มา |
|---|---|---|---|
| NFR-P1 | Time to first token ของห้องติว (p95) | < 2 วินาที | learning-model.md §8 |
| NFR-P2 | ต้นทุน AI ต่อ session 45 นาที | ≤ 5 บาท | วัดจาก ai_calls (PoC P4-lite) |
| NFR-R1 | AI provider หลักล่ม ระบบยังตอบได้ | fallback อัตโนมัติ | ai-orchestration 2.10 |
| NFR-S1 | user คนหนึ่งเข้าถึงข้อมูลของอีกคนไม่ได้ที่ระดับ DB | RLS + test ใน CI | SA-06 |
| NFR-M1 | ทุก requirement ที่ Must มี test ที่ชื่อขึ้นต้นด้วย ID | 100% ก่อน Beta | CLAUDE.md |
| NFR-A1 | ทุกปุ่มและช่องกรอกใช้ด้วย keyboard ได้และมี label ภาษาไทย · สมการมี MathML ให้ screen reader อ่านได้ | ทุกหน้าจอใน wireframe | `apps/web/CLAUDE.md` |
