# Gateway กันข้อมูลหลุดจาก data block เอง

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/gateway-data-blocks` |
| Checklist item | ไม่มีข้อตรง · ต่อจาก self-review ของ PR #110 |
| Status | in progress · 2026-11-07 |

## Plan

ตอนนี้ต้องเรียก `as_data` เองทุกจุด และถ้าเปลี่ยนชื่อ tag การป้องกันจะหายเงียบๆ · ย้ายไปไว้ใน `_render` ของ gateway ซึ่งอ่านจาก prompt ได้เองว่า placeholder อยู่ใน block ไหน

- [x] 1. 🤖 `/spec-feature`: ร่าง `specs/features/ai/prompt-data-blocks.md`
- [x] 2. 🙋 Jam อ่าน spec และตอบ Open questions
- [x] 3. 🤖 `/spec-to-tests` · แดงก่อน
- [x] 4. 🙋 Jam review test
- [ ] 5. 🤖 `/implement-feature`: แก้ `_render` · เอา `as_data` ออกจาก `tutor_turn` และ `checker` · test เขียว · test เดิมผ่าน

## Definition of done

- ทุก placeholder ใน data block ถูกกันอัตโนมัติ ทั้ง `call` และ `stream` โดยผู้เรียกไม่ต้องทำอะไร
- เปลี่ยนชื่อ tag ใน prompt แล้วการป้องกันยังทำงาน
- มี test เดินทุก prompt: placeholder ที่อยู่นอก block ต้องอยู่ในรายการที่ระบุเหตุผล · input ใหม่นอก block ทำให้ test ล้ม
- ข้อความปกติถึง model เหมือนเดิมทุกตัวอักษร · ไม่แก้ไฟล์ prompt · test + ruff + CI เขียว

## Decisions

- 2026-11-07 · อ่านตำแหน่งจากเนื้อ prompt แทนการประกาศใน frontmatter · เพราะ `prompts/README.md` กฎ 1 ห้ามแก้ไฟล์ version เดิม และไม่มีทางลืมประกาศ

## Next step

ขั้น 4: Jam review `tests/unit/test_prompt_data_blocks.py` · แล้วขั้น 5

## Waiting on

ไม่มี

## Notes for next time

- placeholder นอก data block ตอนนี้: `reference_answer`, `answer_format`, `sympy_result`, `hints` (check_answer) · `file_name`, `material_kind` (extract_topics_local) · `file_name` (split_past_exam, vision_extract, vision_extract_pages) · `page_no`, `page_count`
- `file_name` เป็นข้อความจากผู้ใช้ และอยู่ทั้งใน attribute (`<document name="{{file_name}}">`) และบรรทัดคำสั่ง · ยังไม่มีอะไรกัน · ingest ยังไม่เปิดจึงยังไม่เกิดผล
- `poc/P3/` ส่งผ่าน gateway ด้วย จึงจะได้การป้องกันนี้ไปด้วย
