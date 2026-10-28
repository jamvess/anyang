# P2: LLM classifier `check_answer/v1` + ต่อ SymPy + merge rules

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/check-answer-classifier` |
| Checklist item | P2: merge rules + LLM classifier (`prompts/check_answer/v1`) ใช้ SymPy service |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 `/spec-feature AM-06 AM-05 AM-04` → `specs/features/check/check-answer-classifier.md` · input ของ LLM (โจทย์, เฉลย, `solution_steps`, `lines`, ผล SymPy รายบรรทัด, hint `sign_flip_detected`) · output schema `CheckAnswerResult` = `LlmResult` ใน `checker.py` · ฟังก์ชันตรวจ 1 คำตอบที่ต่อ SymPy → `ai.call("check_answer")` → `merge_check` · script `evals/run_checker.py` เขียน predictions ให้ `run_eval.py` · คำถามที่ต้องตัดสินใส่ใน §10
- [x] 2. 🙋 Jam review spec และตอบคำถามใน §10 (เปิดไฟล์ spec อ่าน §2, §4, §10 แล้วตอบในแชทนี้เป็นข้อ)
- [x] 3. 🤖 `/spec-to-tests` → test ของ schema, การประกอบ input (ห่อ `<document>`, สรุปผล SymPy), ฟังก์ชันตรวจ (fake provider) และ `run_checker.py` (ต้องแดง)
- [x] 4. 🙋 Jam review test
- [x] 5. 🤖 `/implement-feature` → `prompts/check_answer/v1.md`, `apps/api/app/models/check.py`, ฟังก์ชันตรวจ, `evals/run_checker.py` จน test เขียว + ruff ผ่าน
- [ ] 6. 🙋 Jam รัน eval กับ Gemini จริงในเครื่องตัวเอง (ใช้ key ใน `.env` ของ Jam · Claude ห้ามอ่าน `.env`) · คำสั่งจะเขียนให้ตอนถึงขั้นนี้ · ส่งผลกลับมาในแชท
- [ ] 7. 🤖 อ่านผลเทียบเป้า (verdict ≥ 95%, error_type ≥ 80%, first_wrong_line ≥ 85%) · ดูข้อที่พลาด · ถ้าต้องแก้ prompt สร้าง `v2.md` (ห้ามแก้ `v1.md` หลังรัน eval แล้ว) · จดตัวเลขใน worklog ให้ Report P2

## Definition of done

- `prompts/check_answer/v1.md` มี frontmatter และ schema ตรงกับ Pydantic model ใน `apps/api/app/models/` · คำตอบของ user อยู่ใน `<document>`
- เรียก AI ผ่าน `ai.call("check_answer", ...)` เท่านั้น · routing ใช้ `config/ai.yaml` ที่มีอยู่ (`tier: mid`)
- ผลของ LLM เข้า `merge_check` ได้เลย · SymPy ตัดสินถูก/ผิดเมื่อตัดสินได้ (CLAUDE.md กฎ 4)
- test ขึ้นต้นด้วย requirement ID ใช้ fake provider ผ่าน · test ที่เรียก model จริง mark `live` · `uv run ruff check .` และ `uv run pytest` ผ่าน
- มีตัวเลข 3 ตัวของ P2 จาก `run_eval.py` เทียบกับเป้า (checklist: "มีตัวเลข 3 ตัวของ P2 เทียบกับเป้า")
- PR review โดย Junior (`apps/api/`)

## Decisions

- 2026-10-28 · Jam ตอบ ok กับข้อเสนอทั้ง 8 ข้อใน spec §10 (Claude ถือว่า "ok" = ทุกข้อ · ข้อ 2 เลือก (b) ส่ง error ขึ้นไป ไม่เดา error_type) · spec approved
- 2026-10-28 · (ร่าง spec) hint `sign_flip_detected` กลับเครื่องหมายทีละพจน์ของทุกผลบวกในบรรทัด (ไม่ใช่แค่ระดับบนสุด) เพราะตัวอย่างใน §2.4.4 `(x-2)(x+3)` เป็นผลคูณ · ลองกับ SymPy แล้ว AC-16, AC-17 เจอ hint และ AC-18 ไม่เจอตามที่ต้องการ
- 2026-10-28 · test กำหนดชื่อ: `CheckProblem`, `check_answer(problem, lines, *, gateway=None, pool=None)`, `describe_sympy(answer_format, sympy)` ใน `app/services/checker.py` · `CheckAnswerResult.to_llm_result(line_count)` ใน `app/models/check.py` · `sign_flip_line(answer_format, reference, lines)` + `detect_sign_flip(..., pool=)` ใน `sympy_service.py` · `run(rows, *, out_path, gateway, pool) -> skipped ids` ใน `evals/run_checker.py` · เลขบรรทัดในพรอมต์รูป `1. <line>`
- 2026-10-28 · เพิ่ม `evals/conftest.py` ใส่ `apps/api` ใน `sys.path` เพราะ `evals/` ไม่มี pytest config ของตัวเอง · test ใน `evals/` ใช้ `pytestmark = pytest.mark.asyncio` (asyncio_mode auto ของ apps/api ไม่มีผลที่นี่)
- 2026-10-28 · implement: red → green 3 รอบ (model · sign flip · pipeline + run_checker) ไม่มี test ที่ต้องแก้ · แยก `_parse_answer` / `_lines_ok` ใน `sympy_service.py` ให้ `evaluate_lines` กับ `sign_flip_line` ใช้ร่วมกัน · เรียก `detect_sign_flip` เฉพาะเมื่อ SymPy ตัดสินได้และมีบรรทัดที่ไม่ follow · `evals/README.md` ชี้ไป `run_checker.py` แล้ว (spec §11)
- 2026-10-28 · ไม่รวม Report P2 ใน branch นี้ (เป็นข้อแยกใน checklist) · ทำ `/poc-report P2` หลัง merge

## Next step

ขั้น 6: Jam รันในเครื่องตัวเอง (ต้องมี `GEMINI_API_KEY` ใน `.env`) จาก root ของ repo:
`AI_PROVIDER=live AI_MODEL_OVERRIDE=gemini:gemini-3.5-flash uv run --project apps/api python evals/run_checker.py`
แล้ว `uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 --predictions evals/answers/predictions/v1.jsonl` · ก๊อปผลทั้ง 2 คำสั่งมาในแชท

## Waiting on

ไม่มี

## Notes for next time

- ผล SymPy กับ golden set (PR #75): ตัดสินได้ 45/50 · ไปที่ LLM 5 ข้อ (ans_004, 041, 046 implicit dy/dx · ans_047 จบที่ `f'(x)` · ans_034 solveset แก้ไม่ได้) · ข้อ wrong_method ans_037, ans_038 ทุกบรรทัดเท่ากันทางคณิต LLM ต้องชี้บรรทัดเอง (merge-rules ข้อ 6)
- label ของ golden set ร่างโดย AI (หมายเหตุใน `evals/answers/worksheet.md`) · ตอนอ่านผลต้องคำนึงว่าอาจเอนไปทางเดียวกับ LLM
- `config/ai.yaml` เป็นไฟล์ร่วม · `check_answer` มี routing อยู่แล้ว ถ้าต้องแก้ต้องขอทีมก่อน
