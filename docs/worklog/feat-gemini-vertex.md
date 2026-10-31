# Gemini ผ่าน Vertex AI ใน gateway (ใช้เครดิต GCP ของทีม)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/gemini-vertex` |
| Checklist item | ไม่มีข้อตรงใน checklist · `infra/README.md`: "`GeminiProvider` ตอนนี้ยังใช้ API key ต้องเพิ่มทาง Vertex ก่อนเปิด live (งาน AI gateway ใน S3)" · ต่อจากข้อของ Junior S1 "AI gateway แบบ lite `app/ai/`" · จะเสนอเพิ่มเป็นข้อใน S3 ของ Jam ตอน `/work-done` |
| Status | in progress · 2026-10-31 |

## Plan

- [ ] 1. 🙋 Jam แจ้ง Junior ในแชทกลุ่ม: `apps/api/app/ai/` เป็นส่วนที่ Junior เขียน (`roles.md`, CODEOWNERS `/apps/api/`) · Jam จะเพิ่มทาง Vertex ให้ `GeminiProvider` และ `build_default_gateway` · Junior เป็นคน review PR · รอ Junior ตอบ ok (หรือบอกว่าอยากทำเอง)
- [x] 2. 🤖 `/spec-feature AI-01 AI-02 AI-04 AI-07` → `specs/features/ai/gemini-vertex.md` · สร้าง client ด้วย `vertexai=True` + `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` (ADC ไม่ใช้ key file) · `build_default_gateway` ลงทะเบียน provider `vertex` (ตรงกับ `vertex:` ใน `config/ai.yaml`) และ `gemini` เฉพาะเมื่อมี key · token ของ embedding บน Vertex (AI-04) · คำถามที่ต้องตัดสินใส่ใน §10 (เช่น location ของ Gemini 3 บน Vertex อาจต้องเป็น `global`)
- [x] 3. 🙋 Jam review spec และตอบคำถามใน §10
- [ ] 4. 🤖 `/spec-to-tests` → test ใช้ client ปลอม ไม่เรียก network (ต้องแดง)
- [ ] 5. 🙋 Jam review test
- [ ] 6. 🤖 `/implement-feature` → test เขียว + ruff ผ่าน · อัปเดต `.env.example` และวิธีตั้งเครื่องใน `docs/team/setup.md` / `infra/README.md` (ไฟล์ของ Junior · ถามก่อน)
- [ ] 7. 🙋 Jam ตั้งเครื่อง: ติดตั้ง Google Cloud CLI → `gcloud auth application-default login` → ตั้ง `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` ใน `.env` → รัน smoke 1 call บน Vertex · คำสั่งทีละคลิกจะเขียนให้ตอนถึงขั้นนี้
- [ ] 8. 🤖 จดผล smoke (model ที่ตอบจริง, token, เวลา) ใน worklog และ PR · ให้ Junior review

## Definition of done

- `AI_PROVIDER=live` + `GOOGLE_CLOUD_PROJECT=anyang-513006` → `ai.call(...)` ที่ tier เป็น `vertex:<model>` เรียก Gemini บน Vertex AI ได้ (smoke 1 call ผ่านบนเครื่อง Jam) โดยไม่ต้องใส่ `AI_MODEL_OVERRIDE`
- Google SDK ยัง import ที่ `app/ai/providers/gemini.py` ที่เดียว (AI-01) · สลับ Gemini API ↔ Vertex ด้วย config/env เท่านั้น (AI-02)
- ไม่มี key file หรือ secret ใน repo · local ใช้ ADC
- test ขึ้นต้นด้วย requirement ID ผ่านด้วย client ปลอม · `uv run pytest` และ `uv run ruff check .` ผ่าน
- ใช้เครดิต Free Trial ได้โดยไม่กด Activate / Upgrade
- PR review โดย Junior

## Decisions

- 2026-10-31 · spec approved · Jam ok ข้อเสนอทั้ง 6 ข้อใน §10: location `global` (ยืนยันด้วย smoke) · เลิกใช้ key file (`GOOGLE_APPLICATION_CREDENTIALS`) · `GeminiProvider.vertex(project, location)` · ไม่มี provider → `AIConfigError` (Junior ยืนยันตอน review) · AI-07 กับ Free Trial Jam เช็คเอกสารแล้วจดใน PR · smoke ใช้ `check_answer` กับ ans_003
- 2026-10-31 · Jam ok แผน 8 ขั้น · Claude เริ่มร่าง spec ระหว่างรอ Junior ตอบเรื่องแก้ `apps/api/app/ai/`
- 2026-10-31 · (ร่าง spec) ส่ง `vertexai=True/False` ให้ SDK ทุกครั้ง เพราะ SDK เดาจาก env `GOOGLE_GENAI_USE_VERTEXAI` ได้ · ส่ง project / location จาก `EnvSettings` ตรงๆ เพราะ pydantic-settings ไม่ใส่ค่าจาก `.env` ลง `os.environ` · token ของ embed บน Vertex มาจาก `ContentEmbedding.statistics.token_count` (google-genai 2.29.0 มี field นี้)
- 2026-10-31 · Jam เลือกใช้เครดิต Free Trial ของทีมผ่าน Vertex แทนจ่าย API key เอง (ดู worklog `feat-check-answer-classifier.md`) · ไม่กด "Activate billing" ใน AI Studio เพราะ `infra/README.md` ห้าม และเครดิต trial ไม่ครอบคลุม AI Studio key

## Next step

ขั้น 4 (🤖): `/spec-to-tests specs/features/ai/gemini-vertex.md` → test ใน `apps/api/tests/unit/test_gemini_provider.py`, `test_ai_gateway.py` และ test scan import (ต้องแดง) · ถ้า Junior ยังไม่ตอบเรื่องแก้ `apps/api/` ถาม Jam ก่อน

## Waiting on

- Junior ตอบเรื่องแก้ `apps/api/app/ai/`

## Notes for next time

- เครื่อง Jam ยังไม่มี `gcloud` (31 ต.ค.) และยังไม่มี ADC (`%APPDATA%\gcloud\application_default_credentials.json`)
- `EnvSettings` มี `google_cloud_project`, `google_cloud_location`, `google_application_credentials` อยู่แล้วแต่ยังไม่มีใครใช้ · `.env.example` ตั้ง location เป็น `asia-southeast1`
- `aiplatform.googleapis.com` เปิดใน `anyang-513006` แล้ว (PR #20) · Jam เป็น Owner ของ project
- พอ merge แล้วกลับไปทำขั้น 6 ของ `feat/check-answer-classifier` (รัน P2 ใหม่ครบ 50 ข้อบน Vertex)
