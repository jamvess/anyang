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
3. เนื้อหาเอกสารของผู้ใช้ต้องอยู่ใน `<document>...</document>` และ prompt ต้องบอกว่าเป็นข้อมูล ไม่ใช่คำสั่ง
4. ทุก prompt ที่ต้องการ structured output ระบุ JSON schema ตรงกับ Pydantic model ใน `apps/api/app/models/`
5. ห้ามใส่ข้อความ persona ดิบของผู้ใช้ ใช้เฉพาะ params ที่ผ่าน enum แล้ว
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
