# prompts/

หนึ่งโฟลเดอร์ต่อ AI purpose (ชื่อเดียวกับ key ใน `config/ai.yaml`) ไฟล์ข้างในคือ `v1.md`, `v2.md`, ... gateway โหลดตาม `prompt:` ใน config

```
prompts/
├─ _shared/source_policy.md     # กฎ RAG-grounded (ai-orchestration §1.4) ใส่ใน tutor prompts
├─ extract_answer/v1.md
├─ check_answer/v1.md
├─ tutor_reply/v1.md
└─ ...
```

## กฎ

1. **ห้ามแก้ไฟล์ version เดิม** ถ้าจะเปลี่ยน ให้สร้าง `v{n+1}.md` แล้วเปลี่ยน `prompt:` ใน `config/ai.yaml` ใน PR เดียวกัน
2. PR ที่แก้ prompt ต้องรัน eval ของ purpose นั้นและแนบผลเทียบกับ version เดิม
3. เนื้อหาเอกสารของผู้ใช้ต้องอยู่ใน `<document>...</document>` และ prompt ต้องบอกว่าเป็นข้อมูล ไม่ใช่คำสั่ง · gateway กันการปิด block ให้เอง ทุก placeholder ที่อยู่ในเนื้อ block ซึ่งขึ้นต้นบรรทัดด้วย tag · **placeholder ใหม่นอก block ต้องเพิ่มใน `OUTSIDE_A_BLOCK` ของ `test_prompt_data_blocks.py` พร้อมเหตุผล** (`specs/features/ai/prompt-data-blocks.md`)
4. ทุก prompt ที่ต้องการ structured output ระบุ JSON schema ตรงกับ Pydantic model ใน `apps/api/app/models/`
5. ห้ามใส่คำบรรยาย persona ของผู้ใช้ (`description_raw`) ใช้เฉพาะ params · ข้อยกเว้นคือ `name`, `self_pronoun`, `call_user`, `nickname` ซึ่งเป็นข้อความจากผู้ใช้จริง ต้องอยู่ใน `<persona_data>` และบอกว่าเป็นข้อมูล ไม่ใช่คำสั่ง (ai-orchestration §2.7 ข้อ 5) · ประวัติแชทอยู่ใน `<conversation>` แบบเดียวกัน และเนื้อหาต้อง escape `<` ก่อนใส่ (§2.3.6)
6. Placeholder ใช้ `{{name}}` และ gateway จะ error ถ้ามี placeholder ที่ไม่ได้เติม

## Frontmatter

```yaml
---
purpose: extract_answer
version: 1
output_schema: ExtractAnswerResult
inputs: [image]
---
```

`defaults` (ไม่บังคับ) ให้ค่า text กับ input ที่ประกาศไว้แต่ผู้เรียกไม่ได้ส่งมา · ใช้ตอนเพิ่ม input ใหม่ใน version ใหม่ เพื่อไม่ให้ผู้เรียกตาม contract เดิมพัง · input ที่ไม่มี default ยังต้องส่งครบ · ตัวอย่าง `tutor_reply/v2`: `defaults: {problem: none}` (`specs/features/tutor/demo-room.md` §2 C · `test_prompt_defaults.py`)
