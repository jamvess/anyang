# Test strategy · เทอม 1

| | |
|---|---|
| Owner | Jam (review: Junior, May) |
| Version | v1.1 · 28 ต.ค. 2569 (อัปเดตคอลัมน์ "ตอนนี้" และตัวเลขใน §5 · หลักการไม่เปลี่ยน) · v1.0 · 21 ต.ค. 2569 |
| ที่มา | `CLAUDE.md` · `apps/api/CLAUDE.md` · `apps/web/CLAUDE.md` · `ai-orchestration.md` §2.4.8, §2.11 · `specs/poc/README.md` · `.github/workflows/ci.yml` |

หน้านี้รวมกติกาที่กระจายอยู่ในไฟล์ข้างบนไว้ที่เดียว ถ้าขัดกัน ให้ไฟล์ต้นทางเป็นหลัก แล้วแก้หน้านี้ตาม

## 1. หลักการ

1. **Spec → test → code.** test เขียนจาก acceptance criteria ของ feature spec (`/spec-to-tests`) และคนต้อง review test ก่อน implement · test ที่ review แล้วห้ามแก้โดยไม่ถามคน review (`CLAUDE.md` "How we work")
2. **ทุก test โยงกลับไปที่ requirement ได้** ชื่อขึ้นต้นด้วย requirement ID (`test_SA06_...`, `it('TM08 ...')`) · test ของโครงสร้างพื้นฐานที่ไม่มี ID ใช้ชื่อ spec + section แทน
3. **Code ตัดสิน LLM แค่พูด** (`CLAUDE.md` กฎ 1) · ส่วนที่ตัดสินด้วย code (stage, ดาว, mastery, ถูก/ผิดด้วย SymPy) ต้องมี unit test ครบ · ส่วนที่ LLM ทำวัดด้วย golden set ไม่ใช่ unit test
4. **CI ไม่เรียก model จริง** ใช้ fake provider (AI-03) · test ที่ต้องใช้ model จริงต้องติด `@pytest.mark.live` ซึ่งไม่ถูกรันโดย default และไม่รันใน CI
5. **ไม่มีตัวเลข threshold ใน test** test อ่านค่าจาก `config/learning.yaml` แบบเดียวกับโค้ด (`CLAUDE.md` กฎ 5)

## 2. ชั้นของ test

| ชั้น | ทดสอบอะไร | เครื่องมือ | รันเมื่อ | ตอนนี้ (28 ต.ค. · `main`) |
|---|---|---|---|---|
| Domain `app/domain/` | stage, เลือกหัวข้อ, ดาว, mastery, buddy · ใช้ตัวอย่างใน spec เป็นตาราง (`parametrize`) | pytest | ทุก PR | ✅ 25 test · merge rules ของ checker (PR #68) · `compute_importance` ยังไม่มี (P8-lite, S4) |
| Math `app/math/` | ถูก/ผิดตาม `answer_format`, บรรทัดแรกที่ผิด, timeout | pytest | ทุก PR | ✅ 43 test · SymPy service (PR #75) · 5 ตัวเปิด worker process จริงเพื่อทดสอบ timeout |
| AI gateway + schema | routing, retry, ตรวจ schema, ซ่อม LaTeX, ขนาด vector | pytest + fake provider | ทุก PR | ✅ 108 test (gateway 51 · output schema 46 · Gemini provider 11) |
| API contract | รูปของ response, error, SSE event ตาม `api.md` | pytest + TestClient | ทุก PR | ✅ 115 test (ห้องติว, progress card, error, CORS, request id, settings) · รวม `tests/unit/` ทั้งหมด 291 |
| Isolation (SA-06) | user A อ่าน/เขียนแถวของ B ไม่ได้ | pytest + `supabase start` | ทุก PR | 🟡 1 test ครอบ 6 จาก 27 ตาราง (`exam_preps`, `messages`, `attempts`, `tutor_sessions`, `problems`, `topics`) |
| Web | component, การอ่าน SSE จาก fixture ที่อัดไว้, KaTeX | Vitest + Testing Library | ทุก PR (+ lint, typecheck, build) | ✅ 242 test ใน 19 ไฟล์ |
| คุณภาพ AI | golden set ของ P1, P2, P3 เทียบกับเป้าใน spec | `evals/run_eval.py`, `poc/*/score.py` + model จริง | เมื่อ prompt หรือ model เปลี่ยน (§2.11) | 🟡 รันมือ ยังไม่อยู่ใน CI · P2 จะรันทั้ง pipeline ด้วย `evals/run_checker.py` (PR #80) · free tier มีเพดาน 5 request ต่อนาทีและเพดานต่อวัน รัน golden set 50 ข้อในวันเดียวไม่ได้ |
| End-to-end | flow ของ demo ผ่านหน้าเว็บจริง | Playwright (ภายหลัง) | ก่อน demo | ❌ ใช้ทดลองมือตอน demo |

## 3. วัดคุณภาพ AI

- **เป้ามาจาก spec ไม่ได้ตั้งเอง:** P1 line accuracy ≥ 80% · P2 verdict ≥ 95%, error_type ≥ 80%, บรรทัดแรกที่ผิด ≥ 85% (§2.4.8) · P3 หัวข้อตรง ≥ 80%, ★★★ ตรง ≥ 80%
- **คน label ต้องไม่ใช่คนทำ PoC** และรายงานตัวเลขพร้อมขนาดตัวอย่าง (n) เสมอ (`evals/README.md`, `/poc-report`)
- **แก้ prompt = เพิ่ม version** (`v2.md` ไม่เขียนทับ `v1.md`) แล้วรัน eval เทียบกับ version เดิมใน PR เดียวกัน (Definition of Done ใน `CLAUDE.md`)
- ผลที่ commit ได้มีแค่ตัวเลขกับ id ห้ามมีข้อความจากชีทหรือรูปลายมือ (`poc/*/out/` และ `evals/**/raw/` อยู่ใน gitignore)

## 4. ข้อมูลทดสอบ

- fixture ใน repo เป็นข้อมูลสมมติ (SSE ที่อัดไว้ใน `apps/web/tests/fixtures/`, label ปลอมใน test ของ `evals/`)
- ลายมือของเพื่อนใช้ได้เฉพาะเมื่อได้รับความยินยอมแล้ว · ใช้รหัสคนเขียน (`w01`) แทนชื่อ · ไม่ commit รูป
- ไม่ใช้ข้อมูลของ user จริงใน test · ตั้งแต่ Beta ห้ามส่งข้อมูลของ user ผ่าน free tier (AI-07)
- integration test สร้าง tenant ทดสอบเองแล้วลบทิ้งเอง ไม่พึ่งข้อมูลที่ค้างอยู่ใน DB

## 5. ช่องว่างและเจ้าของ

Jam เลือก 21 ต.ค. · Junior ตกลง 2 แถวที่เป็นของ Junior (`evals/` เข้า CI, isolation test ทุกตาราง) ในแชทกลุ่ม 21 ต.ค.

| ช่องว่าง | ทำอย่างไร | เจ้าของ · เมื่อไหร่ |
|---|---|---|
| eval ไม่ได้รันใน CI | เทอม 1 รันมือแล้วแนบผลใน PR ที่แก้ prompt หรือ model · ย้ายเข้า CI เมื่อใช้ Vertex AI ที่จ่ายเงิน เพราะ free tier ตอบ 503 บ่อย ถ้าอยู่ใน CI จะทำให้ CI พังโดยไม่ใช่ความผิดของโค้ด | Jam · เทอม 2 |
| test ของ `evals/` (64 · +5 ใน PR #80) และ `poc/` (43) ไม่ได้รันใน CI | เพิ่ม `uv run pytest ../../evals` ใน job `api` (ไม่เรียก network) · `poc/` ไม่เพิ่ม เพราะเป็นโค้ดชั่วคราว · 28 ต.ค.: `poc/P3/test_p3.py` เก็บ test ไม่ได้ (ImportError) และไฟล์เดิมใน `evals/answers/` มี ruff error (RUF100, FURB167) ที่ CI ไม่เห็นเพราะไม่ได้ lint `evals/` | Junior (`.github/`) · S3 |
| isolation test ครอบ 6 จาก 27 ตาราง | ตารางใหม่ต้องมี test ตาม DoD เดิม · เปลี่ยนให้ test วนทุกตารางที่มี `tenant_id` เอง | Junior · S4 (พร้อมอัปเดต data model) |
| เป้า coverage | ไม่ตั้งเป็น % · ใช้ "ทุก acceptance criteria ใน feature spec มี test ที่ชื่อขึ้นต้นด้วย requirement ID" แทน | ทุกคน · ตรวจตอน review test |
| ยังไม่มี e2e | เทอม 1 ใช้ checklist demo แบบทำมือ · Playwright เทอม 2 | May · เทอม 2 |
