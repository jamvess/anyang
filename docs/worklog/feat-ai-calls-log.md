# AI gateway: เขียน `CallRecord` ลงตาราง `ai_calls` (AI-04)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/ai-calls-log` |
| Checklist item | AI gateway แบบ lite `app/ai/`: `ai.call()`, provider Gemini + fake, อ่าน `config/ai.yaml`, log `ai_calls` |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 `/spec-feature` → `specs/features/ai/ai-calls-log.md` (AI-04 · ai-orchestration §2.11): listener ของ gateway แปลง `CallRecord` เป็นแถว `ai_calls` · เขียนด้วย service role + `tenant_id` ที่ระบุเอง (RLS ของ `ai_calls` เป็น select อย่างเดียว) · context (tenant, user, session, request id) มาจาก contextvar · ไม่มี tenant (eval, PoC, P4-lite ที่ยังไม่ตรวจ JWT) → เขียน structured log ลง Cloud Logging อย่างเดียว ไม่ลง DB · map `status` ให้ตรงกับ check constraint · เขียนนอกเส้นทางของ request (ไม่เพิ่ม TTFT) · จดคำถามที่เปิดอยู่ไว้ใน spec
- [x] 2. 🙋 Jam review spec และตัดสินเรื่องฝั่ง AI: `cost_usd` คิดจากตารางราคาใน `config/ai.yaml` (ไฟล์กลาง) หรือปล่อยเป็น null ไปก่อน · การ map `status`
- [x] 3. 🤖 `/spec-to-tests`: unit test ใช้ writer ปลอม · integration test กับ Supabase ในเครื่อง (service role insert ได้ · user อ่านได้เฉพาะแถวของ tenant ตัวเอง)
- [x] 4. 🙋 Jam review test
- [ ] 5. 🤖 `/implement-feature`: `app/db/ai_calls.py` + ต่อ listener ใน `build_default_gateway()` + contextvar ของ tenant
- [ ] 6. 🤖 ruff + pytest + integration (🙋 ถ้า Docker ไม่ได้เปิด: เปิด Docker Desktop แล้ว `npx supabase start`)
- [ ] 7. 🤖 `/work-done`

## Definition of done

- ทุก `ai.call` / `ai.stream` / `embed` ที่มี tenant context ได้ 1 แถวใน `ai_calls` ครบคอลัมน์ตาม §2.11 (AI-04: token แยกตาม user และ purpose)
- call ที่ไม่มี tenant context ไม่พังและไม่ลง DB · มี log 1 บรรทัด
- การเขียน log ล้มไม่ทำให้ AI call ล้ม และไม่เพิ่ม latency ของ call
- isolation test ของ `ai_calls` ผ่าน (SA-06) · CI เขียว
- checklist ข้อของ Junior ติ๊กหรือมีหมายเหตุว่าเหลืออะไร

## Decisions

- 2026-10-31 · test ของ AC-1 ถึง AC-17 + AC-tenant reviewed (Jam) · ห้ามแก้ test เหล่านี้

- 2026-10-31 · Jam หยิบข้อนี้ช่วง solo (`/work-start ALL`) · เพราะ P4-lite ต้องใช้ `ai_calls` วัดต้นทุน (≤ 5 บาท/session)

- 2026-10-31 · spec approved (Jam): `cost_usd` = null ไปก่อน · P4-lite คิดต้นทุนจาก token ใน log · ไม่แตะ `config/ai.yaml` (ไฟล์กลาง · ราคาต้องมีที่มา)
- 2026-10-31 · map status ตาม spec §2.2 (`ok`+retry → `schema_retry` · `schema_error`/`provider_error` → `error`) · `prompt_version` ของ `embed` = null (Jam)
- 2026-10-31 · spec §10 ข้อ 1 (supabase-py + service role) และข้อ 5 (insert ค้างตอนปิด instance หายได้) ใช้ข้อเสนอไปก่อน · รอ Junior

## Next step

ขั้น 5: `/implement-feature specs/features/ai/ai-calls-log.md` · เขียน `app/ai/call_context.py`, `app/db/ai_calls.py` (`to_row`, `AICallLog`, `SupabaseAICallsWriter`) และต่อ `AICallLog` ใน `build_default_gateway()` จน `tests/unit/test_ai_calls_log.py` ผ่าน (ห้ามแก้ test · Jam review แล้ว 31 ต.ค.)

## Waiting on

- Junior: spec §10 ข้อ 1 และ 5 · (1) รูปแบบของ `app/db/` (supabase-py ด้วย service role ซึ่งเป็น dependency อยู่แล้ว · หรือ psycopg ผ่าน `DATABASE_URL`) · ระหว่างนี้ใช้ supabase-py ไปก่อน Junior เปลี่ยนทีหลังได้ (2) tenant/user ของ request จะมาจากไหนเมื่อตรวจ JWT (ข้อ ⚠️ 28 ต.ค.) · feature นี้เตรียม contextvar ไว้ให้ JWT middleware เป็นคนตั้งค่า

## Notes for next time

- Docker ในเครื่อง Jam ไม่ได้เปิด (31 ต.ค.) · integration test ยังไม่ได้รันในเครื่อง · CI job `api-integration` รันให้ด้วย `supabase start`

- `CallRecord.status` (`ok`, `schema_error`, `provider_error`) ไม่ตรงกับ check ของตาราง (`ok`, `schema_retry`, `fallback`, `degraded`, `error`) ต้อง map
