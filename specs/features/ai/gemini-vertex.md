# Feature: Gemini ผ่าน Vertex AI ใน gateway

| | |
|---|---|
| Area | platform |
| Requirements | AI-01, AI-02, AI-04, AI-07 |
| Owner | Jam |
| Reviewer | Junior (`apps/api/` · เป็นคนเขียน gateway lite) |
| Status | approved · 2026-10-31 (Jam) |
| Related system spec | ai-orchestration.md §2.10 (routing), §2.11 (`ai_calls`), §2.3.3 (embed token), §2.9 Data (AI-07) · architecture.md (Gemini · Vertex AI เป็น primary) · `infra/README.md` แถว Gemini |

## 1. Context

`config/ai.yaml` ตั้งทุก tier เป็น `vertex:<model>` แต่ gateway มีแค่ provider `gemini` ที่ใช้ API key ของ AI Studio · ตอนนี้จะรัน live ได้ต้องใส่ `AI_MODEL_OVERRIDE=gemini:<model>` และใช้ free tier ซึ่งให้แค่ 20 request ต่อวันต่อ model (P2 รันไม่ครบ 50 ข้อ · 31 ต.ค.) · เครดิต Free Trial ของ `anyang-513006` ใช้กับ AI Studio key ไม่ได้ ใช้ได้กับ Vertex AI เท่านั้น (`infra/README.md`) · feature นี้เพิ่ม provider `vertex` ให้ gateway เพื่อให้ eval, PoC และ staging ในอนาคตเรียก Gemini บน Vertex ตาม config ได้โดยไม่ต้อง override

## 2. Behavior

### 2.1 Client ของ Google SDK สองแบบ ใน module เดียว

`app/ai/providers/gemini.py` ยังเป็นที่เดียวที่ import Google SDK (AI-01) · `GeminiProvider` สร้าง `genai.Client` ได้สองแบบ ส่วน `generate` และ `embed` ใช้โค้ดเดียวกัน (SDK ใช้ interface เดียวกันทั้งสองทาง)

| แบบ | สร้าง client ด้วย | ชื่อ provider ใน gateway | ใช้เมื่อ |
|---|---|---|---|
| Gemini API | `api_key=GEMINI_API_KEY`, `vertexai=False` | `gemini` | PoC เดิม / `AI_MODEL_OVERRIDE=gemini:<model>` |
| Vertex AI | `vertexai=True`, `project=GOOGLE_CLOUD_PROJECT`, `location=GOOGLE_CLOUD_LOCATION` · ไม่ส่ง `api_key` | `vertex` | ค่า default ของ `config/ai.yaml` (`vertex:<model>`) |

- ส่ง `vertexai` ให้ SDK **ทุกครั้ง** (`True` หรือ `False`) ไม่ปล่อยให้ SDK เดาจาก environment variable `GOOGLE_GENAI_USE_VERTEXAI` · ป้องกันกรณีเครื่องใครตั้งตัวแปรนั้นไว้แล้ว client แบบ API key กลายเป็น Vertex โดยไม่รู้ตัว
- **Credential ของ Vertex มาจาก Application Default Credentials (ADC)** ที่ SDK หาเอง · เครื่อง dev ใช้ `gcloud auth application-default login` · Cloud Run ใช้ service account ของ service · ไม่มี key file และไม่มี secret ใหม่ใน repo (CLAUDE.md กฎ 10)
- ค่าใน `.env` ถูกอ่านผ่าน `EnvSettings` (`google_cloud_project`, `google_cloud_location` มีอยู่แล้ว) แล้วส่งให้ client ตรงๆ · ไม่พึ่งให้ SDK อ่าน `os.environ` เอง เพราะ pydantic-settings ไม่ได้ใส่ค่าจาก `.env` ลง `os.environ`
- สร้างแบบ Vertex โดยที่ project หรือ location ว่าง → `ValueError` ที่บอกชื่อตัวแปรที่ขาด (เหมือนที่ API key ว่างได้ `ValueError` อยู่แล้ว)

### 2.2 `build_default_gateway` เลือก provider จาก env

เมื่อ `AI_PROVIDER=live`

1. `GEMINI_API_KEY` ไม่ว่าง → ลงทะเบียน `gemini`
2. `GOOGLE_CLOUD_PROJECT` ไม่ว่าง → ลงทะเบียน `vertex`
3. ไม่ได้ลงทะเบียนเลยสักตัว → `AIConfigError` ตอนสร้าง gateway บอกว่าต้องตั้ง `GEMINI_API_KEY` หรือ `GOOGLE_CLOUD_PROJECT` อย่างน้อยหนึ่งตัว
4. การเลือก provider ต่อ call ยังเป็นแบบเดิม: prefix ของ model id (`vertex:` / `gemini:`) · ถ้า prefix ไม่มี provider ลงทะเบียน → `AIConfigError` "no provider for model …" (§2.10 · ของเดิม)

เมื่อ `AI_PROVIDER=fake` ไม่สร้าง Google client เลย แม้ตั้ง `GOOGLE_CLOUD_PROJECT` ไว้ (test และ CI ไม่แตะ network · AI-03)

ผลที่ได้: ตั้ง `AI_PROVIDER=live` + `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` โดยไม่ใส่ `AI_MODEL_OVERRIDE` → ทุก purpose ไปที่ Vertex ตาม tier ใน `config/ai.yaml` · ใส่ `AI_MODEL_OVERRIDE=vertex:<model>` ได้เพื่อลอง model อื่นบน Vertex

### 2.3 Token (AI-04)

- `generate`: นับจาก `usage_metadata` แบบเดิม (`prompt_token_count` → `tokens_in` · `candidates_token_count` + `thoughts_token_count` → `tokens_out`) · Vertex ส่ง field เดียวกัน
- `embed`: Vertex ส่ง `statistics.token_count` มากับทุก embedding · `tokens_in` = ผลรวมของ `token_count` ทุกตัว · embedding ที่ไม่มี `statistics` (Gemini API) นับเป็น 0 · ทำให้หมายเหตุใน ai-orchestration §2.3.3 ("`tokens_in` ของ `embed` เป็น 0 จนกว่าจะย้ายไป Vertex AI") หมดไปเมื่อใช้ Vertex

### 2.4 Rate limit และ error

- 429 จาก Vertex แปลงเป็น `ProviderRateLimited` เหมือนเดิม · ถ้าไม่มี `RetryInfo` → `retry_after=None` แล้ว gateway รอ `gateway.retry_backoff_seconds` ตาม §2.10 (ไม่มีค่าใหม่ใน config)
- error อื่นของ SDK ส่งต่อขึ้นไปแบบเดิม (gateway นับเป็น provider error)

### 2.5 AI-07

ai-orchestration §2.9 กำหนดว่าตั้งแต่ Beta ทุก tier ต้องใช้ "Vertex AI แบบเสียเงิน" · feature นี้ทำให้ทางนั้นใช้ได้ แต่ **ไม่ได้บังคับ** ว่า staging / production ต้องไม่ใช้ `gemini` (การบังคับเป็นงานตอนเปิด Beta · §9)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (env) | `AI_PROVIDER`, `GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `AI_MODEL_OVERRIDE` (มีอยู่แล้วทั้งหมดใน `EnvSettings`) | `AI_PROVIDER=live` · `GOOGLE_CLOUD_PROJECT=anyang-513006` · `GOOGLE_CLOUD_LOCATION=global` |
| Input (config) | model id ใน `config/ai.yaml` `tiers.*.primary` | `vertex:gemini-3.5-flash` |
| Output | `Gateway` ที่มี providers `{"vertex": GeminiProvider(Vertex), "gemini"?: GeminiProvider(API key)}` · `ProviderResponse` / `EmbedResponse` แบบเดิม · `CallRecord.provider = "vertex"` | `ai_calls.provider = 'vertex'`, `model = 'gemini-3.5-flash'` |

ชื่อ API ที่เสนอ (ตัดสินตอน `/spec-to-tests`): `GeminiProvider(api_key=...)` แบบเดิม + `GeminiProvider.vertex(project, location)` (classmethod) · `build_default_gateway()` ไม่เปลี่ยน signature

## 4. Acceptance criteria

ทุกข้อ test ด้วย client ปลอม (แทน `genai.Client` หรือ `provider._client`) ไม่มี network

**Client (§2.1)**

- **AC-1 (AI-01)** Given project `p-test` และ location `global` When สร้าง provider แบบ Vertex Then `genai.Client` ถูกสร้างด้วย `vertexai=True`, `project="p-test"`, `location="global"` และไม่มี `api_key`
- **AC-2 (AI-01)** Given environment มี `GOOGLE_GENAI_USE_VERTEXAI=true` When สร้าง provider แบบ API key `"k"` Then `genai.Client` ถูกสร้างด้วย `api_key="k"` และ `vertexai=False`
- **AC-3 (AI-01)** Given project ว่าง (`""`) When สร้าง provider แบบ Vertex Then `ValueError` ที่ข้อความมี `GOOGLE_CLOUD_PROJECT` · Given location ว่าง Then `ValueError` ที่มี `GOOGLE_CLOUD_LOCATION`
- **AC-4 (AI-01)** ไม่มีไฟล์ใน `apps/api/app/` นอก `app/ai/providers/gemini.py` ที่ import `google.genai` (test ที่ scan import อยู่แล้วต้องยังผ่าน ถ้ายังไม่มีให้เพิ่ม)

**การเลือก provider (§2.2)**

- **AC-5 (AI-02)** Given `AI_PROVIDER=live`, `GOOGLE_CLOUD_PROJECT=p-test`, location `global`, `GEMINI_API_KEY` ว่าง When `build_default_gateway()` Then gateway มี provider `vertex` ไม่มี `gemini` และไม่มี error
- **AC-6 (AI-02)** Given live, key `"k"`, project ว่าง When build Then มี `gemini` ไม่มี `vertex` (พฤติกรรมเดิม)
- **AC-7 (AI-02)** Given live, key และ project ครบ When build Then มีทั้ง `gemini` และ `vertex`
- **AC-8 (AI-02)** Given live, key และ project ว่างทั้งคู่ When build Then `AIConfigError` ที่ข้อความมีทั้ง `GEMINI_API_KEY` และ `GOOGLE_CLOUD_PROJECT`
- **AC-9 (AI-03)** Given `AI_PROVIDER=fake` และ project `p-test` When build Then ไม่มีการสร้าง `genai.Client` และ gateway ใช้ fake provider
- **AC-10 (AI-02)** Given gateway live ที่มี provider `vertex` (recorder) และ config จริงของ repo ไม่มี override When `call("check_answer", …)` Then provider `vertex` ได้ request ที่ `model` เท่ากับ `tiers.mid.primary` ที่ตัด `vertex:` ออก และ `CallRecord.provider == "vertex"`
- **AC-11 (AI-02)** Given gateway live ที่มีแค่ `vertex` When override เป็น `gemini:gemini-test` แล้ว call Then `AIConfigError` "no provider for model" (ไม่ตกไปใช้ `vertex` เอง)

**Token (§2.3)**

- **AC-12 (AI-04)** Given Vertex ตอบ embed 2 ตัวที่ `statistics.token_count` = 12 และ 30 When `embed` Then `EmbedResponse.tokens_in == 42` และ vectors เรียงตามลำดับเดิม
- **AC-13 (AI-04)** Given embedding ไม่มี `statistics` (แบบ Gemini API) When `embed` Then `tokens_in == 0` · Given มี 1 ตัวที่มี `token_count` 7 และ 1 ตัวที่ไม่มี Then `tokens_in == 7`
- **AC-14 (AI-04)** Given Vertex ตอบ generate ที่ `usage_metadata` = prompt 100, candidates 20, thoughts 50 When `generate` Then `tokens_in == 100`, `tokens_out == 70`

**Error (§2.4)**

- **AC-15 (AI-02)** Given client แบบ Vertex โยน `ClientError(429)` ที่ไม่มี `RetryInfo` When `generate` Then `ProviderRateLimited` ที่ `retry_after is None`

**ไม่มี**: AC-boundary (feature นี้ไม่ใช้ค่าใน `config/learning.yaml` หรือ threshold) · AC-tenant (ไม่อ่านหรือเขียนตาราง · `ai_calls.provider` เป็น `text` ไม่มี check constraint จึงรับ `'vertex'` ได้)

**Smoke (ไม่อยู่ใน CI)**

- **AC-16 (AI-01, AI-07)** test mark `live` 1 ตัว: Given ADC ของ Jam + `GOOGLE_CLOUD_PROJECT=anyang-513006` When `call` purpose เล็ก 1 ครั้งโดยไม่ override Then ได้ผลผ่าน schema และ `tokens_in > 0` · ข้ามเองถ้าไม่มี `GOOGLE_CLOUD_PROJECT` · จดชื่อ model, location และ latency ใน PR

## 5. Data changes

ไม่มี · `ai_calls.provider` (`0001_init.sql` บรรทัด 379) เป็น `text not null` ใส่ `'vertex'` ได้เลย

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี purpose ใหม่ · ทุก purpose เดิมเปลี่ยนแค่ provider ที่ตอบ (ตาม prefix ใน `config/ai.yaml`)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_gemini_provider.py` (เพิ่ม): client แบบ Vertex / API key, env ว่าง, embed token, generate token, 429 | unit | AC-1, 2, 3, 12, 13, 14, 15 |
| `tests/unit/test_ai_gateway.py` (เพิ่ม): `build_default_gateway` ตาม env (monkeypatch settings + `genai.Client`), routing ไป `vertex`, override ที่ไม่มี provider | unit | AC-5–11 |
| test scan import (เพิ่มถ้ายังไม่มี) | unit | AC-4 |
| smoke `live` บนเครื่อง Jam | integration (manual, mark `live`) | AC-16 |

## 9. Out of scope

- เปิด `AI_PROVIDER=live` บน Cloud Run `api-staging` และให้สิทธิ์ `roles/aiplatform.user` กับ service account (งาน infra ของ Junior)
- บังคับว่าระยะ Beta ห้ามใช้ provider `gemini` (AI-07 ตอนเปิด Beta)
- Provider `anthropic` (fallback) และ Mathpix
- Circuit breaker / fallback chain ข้าม provider (§2.10)
- Context caching ของ Vertex (AI-06)
- เปลี่ยน model ใน `config/ai.yaml` (P3 A6 ที่รอวัดบน Vertex เป็นงานแยก)

## 10. Open questions

**ตัดสินแล้ว 2026-10-31:** Jam ตอบ ok กับข้อเสนอทั้ง 6 ข้อ · ข้อ 4 ให้ Junior ยืนยันตอน review PR · ข้อ 5 Jam เช็คเอกสารแล้วจดใน PR

1. **Location:** Gemini 3.x บน Vertex มักเปิดที่ `global` ก่อน region · `.env.example` ตั้ง `asia-southeast1` ซึ่งอาจไม่มี `gemini-3.5-flash` · เสนอ: ใช้ `global` เป็นค่าใน `.env.example` แล้วยืนยันด้วย smoke (AC-16) · ถ้าต้องการให้ข้อมูลอยู่ในภูมิภาค (PDPA) ให้ตัดสินตอน Beta
2. **`GOOGLE_APPLICATION_CREDENTIALS`:** `.env.example` บอกว่าเป็น "path to service-account json for local dev" แต่ `infra/README.md` บอกว่าใช้ `gcloud auth application-default login` ไม่ต้องมี key file · เสนอ: เลิกใช้ key file · ลบตัวแปรนี้ออกจาก `.env.example` และ `EnvSettings` (ไม่มีโค้ดไหนใช้) หรือเก็บไว้แต่แก้ comment ว่าไม่แนะนำ
3. **ชื่อ API:** `GeminiProvider.vertex(project, location)` (classmethod) หรือแยก class `VertexGeminiProvider` · เสนอ classmethod เพราะ `generate` / `embed` เหมือนกันทุกบรรทัด
4. **Error เมื่อไม่มี provider:** ตอนนี้ key ว่างได้ `ValueError` จาก `GeminiProvider` · spec เสนอให้ `build_default_gateway` ตรวจก่อนแล้วโยน `AIConfigError` (AC-8) · Junior โอเคกับการเปลี่ยนชนิด error ไหม
5. **AI-07 กับ Free Trial:** ข้อมูลที่ส่งผ่าน Vertex ระหว่างใช้เครดิต Free Trial อยู่ใต้เงื่อนไขข้อมูลเดียวกับ Vertex แบบเสียเงิน (ไม่นำไป train) หรือไม่ · Jam เช็คเอกสาร Google Cloud แล้วจดไว้ใน PR · ระหว่างนี้ข้อมูลที่ส่งเป็นของทีมที่ให้ consent แล้ว (golden set) จึงไม่ติด AI-07
6. **Smoke purpose:** AC-16 ใช้ purpose ไหน · เสนอ `check_answer` กับ golden set ข้อ ans_003 เพราะเป็น tier `mid` ตัวเดียวกับที่จะรัน P2 ต่อ

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | เจ้าของ |
|---|---|---|
| `specs/system/ai-orchestration.md` §2.3.3 | หมายเหตุ "`tokens_in` ของ `embed` เป็น 0 จนกว่าจะย้ายไป Vertex AI" → บน Vertex นับจาก `statistics.token_count` · บน Gemini API ยังเป็น 0 | Jam |
| `config/ai.yaml` comment บรรทัด 3–4 | "until Beta needs a Vertex AI provider" → provider `vertex` มีแล้ว · `AI_MODEL_OVERRIDE=gemini:` ใช้เฉพาะเมื่อไม่มี GCP · ค่าไม่เปลี่ยน | ไฟล์ร่วม · ถามทีม |
| `.env.example` | `GOOGLE_CLOUD_LOCATION` (คำถาม 1) · `GOOGLE_APPLICATION_CREDENTIALS` (คำถาม 2) · comment บอกว่าตั้ง `GOOGLE_CLOUD_PROJECT` แล้วได้ provider `vertex` | ทุกคน |
| `infra/README.md` แถว Gemini | "`GeminiProvider` ตอนนี้ยังใช้ API key ต้องเพิ่มทาง Vertex" → มีแล้ว · วิธีตั้งเครื่องด้วย ADC | Junior |
| `docs/team/setup.md` | ขั้นติดตั้ง Google Cloud CLI + `gcloud auth application-default login` + `set-quota-project` | Junior |
