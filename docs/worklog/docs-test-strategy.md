# Test strategy 1 หน้า

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/test-strategy` |
| Checklist item | Test strategy 1 หน้าใน `specs/system/` |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 สำรวจ test ที่มีจริง: จำนวนและชั้นของ test (api unit / integration, web Vitest, PoC, evals), job ใน CI, กติกาตั้งชื่อ, fake / live provider · สรุปเป็นตาราง "มีแล้ว / ยังไม่มี"
- [x] 2. 🤖 ร่าง `specs/system/test-strategy.md` 1 หน้า: test แต่ละชั้น (อะไร, เครื่องมือ, รันที่ไหน, ใครเขียน, ใคร review), การวัดคุณภาพ AI ด้วย golden set, กฎ SDD/TDD และ traceability, ข้อมูลทดสอบและความเป็นส่วนตัว, ช่องว่างที่ยังไม่มีพร้อมเจ้าของ · อ้างที่มาจาก spec ที่มีอยู่ ไม่คิดกฎใหม่เอง
- [x] 3. 🙋 Jam ตัดสินเรื่องที่ spec ยังไม่ได้บอก (Claude ให้ตัวเลือกพร้อมคำแนะนำ)
- [x] 4. 🤖 แก้ตามที่ตัดสิน + เช็คว่าไม่เกิน 1 หน้า

## Definition of done

- `specs/system/test-strategy.md` มีอยู่ ยาวประมาณ 1 หน้า ทุกกฎอ้างที่มา (CLAUDE.md, `apps/*/CLAUDE.md`, `ai-orchestration.md` §2.11, `specs/poc/README.md`, CI)
- เรื่องที่ยังไม่มีคำตอบเขียนเป็น "ช่องว่าง" พร้อมเจ้าของ ไม่แต่งเป็นกฎ
- PR ส่งให้ Junior และ May review (ไฟล์ใน `specs/system/` ไม่มี owner เฉพาะ จึงเป็นไฟล์ร่วม)

## Decisions

- 2026-10-21 · ทำล่วงหน้า (เป็นงาน S4) ระหว่างรอ flash ของ P3 หลัง 14:00 น.
- 2026-10-21 · `specs/system/test-strategy.md` เป็นไฟล์ใหม่ใน `specs/system/` ซึ่ง CODEOWNERS ให้ทั้ง 3 คน → ถือเป็นไฟล์ร่วม · ไม่แก้ `CLAUDE.md` หรือ `architecture.md` ใน PR นี้ (ถ้าจะลิงก์ ต้องถามก่อน)

- 2026-10-21 · (Jam เลือก ⭐ ทุกข้อ) §5: eval รันมือ + แนบผลใน PR จนถึง Vertex (เทอม 2) · `evals/` เข้า job `api` ของ CI (Junior · S3) · `poc/` ไม่เข้า CI · isolation test วนทุกตารางที่มี `tenant_id` (Junior · S4) · ไม่ตั้งเป้า coverage เป็น % ใช้ AC ↔ test ID แทน · e2e เป็น checklist ทำมือ, Playwright เทอม 2 · ข้อของ Junior ยังเป็นข้อเสนอจน Junior ตกลงใน PR
- 2026-10-21 · ข้อ 4: หน้าเดียว 56 บรรทัด

## Next step

ครบทุกขั้นแล้ว · `/work-done` (PR #55 ให้ Junior + May review · Junior ต้องตกลงข้อ `.github/` และ isolation test ใน §5)

## Waiting on

ไม่มี

## Notes for next time

**สำรวจ test บน main (21 ต.ค. · นับเป็นจำนวน function ไม่นับ case ของ parametrize)**

| ชั้น | ที่อยู่ | จำนวน | รันใน CI |
|---|---|---|---|
| api unit (gateway, provider, schema ของ AI, contract ห้องติว, CORS, settings) | `apps/api/tests/unit/` | 103 | ✅ job `api` (`AI_PROVIDER=fake`) |
| api integration: RLS isolation (SA-06) | `apps/api/tests/integration/` | 1 (ครอบ 3 ตาราง: `exam_preps`, `messages`, `attempts`) | ✅ job `api-integration` (`supabase start`) |
| web (Vitest + Testing Library, SSE fixture) | `apps/web/tests/` | 84 | ✅ job `web` (+ lint, typecheck, build) |
| domain (`apps/api/app/domain/`) | — | 0 · ยังไม่มีโค้ด | — |
| SymPy service (`app/math/`) | — | 0 · ยังไม่มีโค้ด | — |
| PoC | `poc/P1`, `poc/P3` | 26 | ❌ |
| เครื่องมือ eval | `evals/**/test_*.py` | 44 | ❌ |
| คุณภาพ AI (golden set) | `evals/run_eval.py`, `poc/*/score.py` | — | ❌ (§2.11 บอกให้รันเมื่อ prompt/model เปลี่ยน) |
| e2e (Playwright) | — | 0 · `apps/web/CLAUDE.md` เขียนว่า "later" | — |

- live provider: `@pytest.mark.live` ไม่รันโดย default (`addopts = "-m 'not live'"`) และไม่รันใน CI
- feature spec มี 5 ไฟล์ (`scope/compute-importance.md`, `tutor/*` 4 ไฟล์)
