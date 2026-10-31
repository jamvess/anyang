# P2: LLM classifier `check_answer/v1` + ต่อ SymPy + merge rules

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/check-answer-classifier` |
| Checklist item | P2: merge rules + LLM classifier (`prompts/check_answer/v1`) ใช้ SymPy service |
| Status | paused · 2026-10-31 · รอ `feat/gemini-vertex` |

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
- 2026-10-28 · รันจริงครั้งแรก: ได้ prediction 6/50 (5 ข้อแรกตรง label) ที่เหลือ 429 · free tier ของ Gemini 5 request ต่อนาที · gateway ไม่รอนานกว่า `max_retry_wait_seconds: 10` (ตั้งใจไว้สำหรับห้องแชท ไม่แก้) · แก้ที่ `run_checker.py`: `--pause` 13 วินาที, รอ 60 วินาทีเมื่อ 429 แล้วลองใหม่ ≤ 3 ครั้ง, `--resume` · เพิ่ม test 1 ตัว (รอ Jam review) · spec §2.6
- 2026-10-28 · รันจริงครั้งที่ 2: timeout 15 วินาที (ans_001, ans_002) · ไฟล์ prediction ว่างเพราะไม่ได้ flush → เพิ่ม `out.flush()` · Jam เลือก: `config/ai.yaml` 1.3 เพิ่ม `thinking: low` ให้ `check_answer` (ไฟล์ร่วม · บอกแชทกลุ่ม) · คง `max_tokens: 600`, `timeout_s: 15` · เหตุผล: P3 วัด default thinking ~4,000 token เทียบ low 396 (`settings.py`)
- 2026-10-28 · Jam review test rate limit แล้ว · เพิ่ม test ของ `--resume` 2 ตัว · แยก `remaining_rows(rows, out_path)` ใน `run_checker.py` ให้ test ได้โดยไม่เรียก `main()` (main สร้าง gateway จาก settings ถ้า `.env` เป็น live จะเรียก Gemini จริง) · test ทั้งไฟล์เป็น `async` เพราะ `pytestmark = asyncio` ติดทุก test ในไฟล์ · ruff ของ `evals/answers/` เดิมมี error อยู่แล้ว (RUF100, FURB167) ไม่ได้แก้
- 2026-10-28 · ไม่รวม Report P2 ใน branch นี้ (เป็นข้อแยกใน checklist) · ทำ `/poc-report P2` หลัง merge
- 2026-10-31 · รัน `--resume` บน free tier ได้ถึง 23/50 (ans_001–023) แล้วโดน 429 รายวัน (`limit: 20` ต่อวันต่อ model) · Jam เลือกใช้เครดิต Free Trial ของทีมผ่าน **Vertex AI** (`anyang-513006`) แทน API key แบบจ่ายเงิน · ไม่กด "Activate billing" ใน AI Studio (`infra/README.md`: ห้าม Activate/Upgrade · เครดิต trial ใช้กับ AI Studio key ไม่ได้) · ทำ Vertex provider ใน branch `feat/gemini-vertex` ก่อน แล้วรัน P2 **ใหม่ครบ 50 ข้อบน Vertex** ให้ผลมาจากรอบเดียวกันและตรงกับ `vertex:` ใน `config/ai.yaml` · ค่าใช้จ่ายประมาณ ~$0.45 ต่อ 50 ข้อ (input ~2,000 + output ~600 token ต่อข้อ · ยังไม่ได้วัดจริง)

## Done today (2026-10-28)

- spec `check-answer-classifier.md` approved · test 29 ตัว review แล้ว · implement เสร็จ (prompt v1, `CheckAnswerResult`, `app/services/checker.py`, hint sign flip, `evals/run_checker.py`) · `apps/api` 329 passed · `evals/` 67 passed
- รันกับ Gemini จริง 3 รอบ: รอบ 1 โดน 429 (5 request/นาที) · รอบ 2 timeout 15 วินาที (default thinking) · รอบ 3 หลังเพิ่ม `thinking: low` ไม่ timeout แต่โดน 429 ซ้ำแม้รอ 60 วินาที → น่าจะหมดเพดานต่อวันของ free tier
- `run_checker.py`: `--pause` 13 วินาที, รอ 60 วินาทีเมื่อ 429 (≤ 3 ครั้ง), `--resume`, flush ทีละข้อ · `ai.yaml` 1.3 `check_answer` เพิ่ม `thinking: low`

## Next step

ขั้น 6 (🙋 Jam · หลัง PR ของ `feat/gemini-vertex` merge): `git merge origin/main` · ย้ายไฟล์ prediction 23 ข้อของ free tier ไปเก็บไว้ (`evals/answers/predictions/v1.jsonl` → `v1-free-tier.jsonl`) · รัน **ไม่ใส่** `--resume` ให้ครบ 50 ข้อบน Vertex (`AI_PROVIDER=live` · ไม่ใส่ `AI_MODEL_OVERRIDE` หรือใส่ `vertex:<model>`) · คำสั่งที่แน่นอนดูใน worklog ของ `feat/gemini-vertex` · แล้ว `uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 --predictions evals/answers/predictions/v1.jsonl` · ก๊อปบรรทัด `skipped` และผลคำสั่งที่ 2 มาในแชท

## Waiting on

- `feat/gemini-vertex` (Vertex provider ใน gateway) merge ก่อน แล้ว Jam รันขั้น 6
- (Jam review test rate limit และ `--resume` 2 ตัวแล้ว 28 ต.ค.)
- Jam บอกแชทกลุ่มเรื่อง `config/ai.yaml` 1.3 (`thinking: low`) ถ้ายังไม่ได้บอก

## Notes for next time

- ผล SymPy กับ golden set (PR #75): ตัดสินได้ 45/50 · ไปที่ LLM 5 ข้อ (ans_004, 041, 046 implicit dy/dx · ans_047 จบที่ `f'(x)` · ans_034 solveset แก้ไม่ได้) · ข้อ wrong_method ans_037, ans_038 ทุกบรรทัดเท่ากันทางคณิต LLM ต้องชี้บรรทัดเอง (merge-rules ข้อ 6)
- label ของ golden set ร่างโดย AI (หมายเหตุใน `evals/answers/worksheet.md`) · ตอนอ่านผลต้องคำนึงว่าอาจเอนไปทางเดียวกับ LLM
- `config/ai.yaml` เป็นไฟล์ร่วม · `check_answer` มี routing อยู่แล้ว ถ้าต้องแก้ต้องขอทีมก่อน
- 31 ต.ค. project `jam-p2-eval` และ key …OZzQ ใน AI Studio สร้างไว้ตอนจะจ่ายเงินเอง แต่ไม่ได้ใช้ (ผูกกับ Free Trial · ลบได้)
- `evals/answers/predictions/v1.jsonl` (31 ต.ค. มี 23 ข้อ: ans_001–023 บน free tier) และ `evals/answers/results/` อยู่ในเครื่อง Jam เท่านั้น ยังไม่ commit เพราะยังไม่ครบ · `--resume` อ่านไฟล์นี้ · commit ไฟล์ prediction + results ตอนรันครบ (ใช้ใน Report P2)
- 429 ของ free tier บอก model เป็น `gemini-3.6-flash` ทั้งที่ override เป็น `gemini-3.5-flash` · น่าจะเป็น alias ของ Google · ต้องจดชื่อ model ที่ใช้จริงใน Report P2
- ถ้า quota รายวันไม่พอ 50 ข้อ (แต่ละข้อใช้ 1 request + retry) ทางเลือก: key แบบจ่ายเงิน / Vertex (รอ GCP #20 ของ Junior) · `gemini-3.5-flash-lite` มี quota แยกแต่ไม่ใช่ tier `mid` ใช้ตัดสิน P2 ไม่ได้
- รัน `run_checker.py` แบบไม่ใส่ `--resume` จะเขียนทับไฟล์ prediction ทั้งไฟล์
