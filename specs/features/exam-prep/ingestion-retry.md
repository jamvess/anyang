# Feature: ปุ่ม "ลองใหม่" ในหน้ารออ่านไฟล์ (ขั้นรวม + รายไฟล์)

| | |
|---|---|
| Area | scope |
| Requirements | CM-07 · UC-02 E5 (ส่วน "ลองใหม่") · SA-06 |
| Owner | May (หน้าเว็บ + API · API แบบ #160 · router `exam_prep.py` ของ Junior · `IngestionRunner` ของ Jam) |
| Reviewer | May |
| Status | approved (May 19 พ.ย.) |
| Related system spec | api.md "ไฟล์และขอบเขต" (`POST /materials/{id}/retry`, `GET /exam-preps/{id}/ingestion`, รอตัดสินข้อ 8) · `specs/features/scope/ingestion.md` §2.1 ข้อ 3, §2.4, §2.6 · `specs/features/exam-prep/upload-page.md` §2.2 · `docs/design/use-cases.md` UC-02 E5 |

## 1. Context

หน้ารออ่านไฟล์ (S11 · `/preps/{id}/progress`) แสดงไฟล์หรือขั้นรวมที่ล้มด้วย ✕ แต่ผู้ใช้ทำอะไรต่อไม่ได้เลย เพราะ `/materials/{id}/retry` ยังเป็น stub และขั้นรวมไม่มี endpoint ลองใหม่ (api.md รอตัดสินข้อ 8) · 19 พ.ย. May อัปโหลด 1 ไฟล์แล้วขั้น "หาหัวข้อและลำดับการเรียน" ล้มด้วย `merge_topics: ProviderRateLimited` (Vertex 429) ทางเดียวที่เหลือคือสร้างการเตรียมสอบใหม่ · feature นี้เพิ่มปุ่ม "ลองใหม่" ที่แถวไฟล์ที่ล้มและที่ขั้นรวมที่ล้ม พร้อม API ที่ทำงานจริง (มี token) · ปุ่ม "ไปต่อโดยไม่มีไฟล์นี้" ของ UC-02 E5 ยังไม่ทำ (§9)

## 2. Behavior

### 2.1 หน้าเว็บ S11 (`components/materials/ProgressPage.tsx`)

1. **แถวไฟล์ที่ `failed`:** ใต้ข้อความ error มีปุ่ม ข้อความบนปุ่ม "ลองใหม่" · ชื่อสำหรับ screen reader (`aria-label`) "ลองอ่าน {file_name} ใหม่" เพื่อไม่ซ้ำกับปุ่ม "ลองใหม่" ของการโหลดความคืบหน้าไม่สำเร็จ (upload-page.md §2.2 ข้อ 7)
2. **ขั้นรวมที่ `failed`:** แสดงปุ่ม "ลองใหม่" ที่แถวของขั้นนั้น (`aria-label` "ลองขั้น {label} ใหม่") **เฉพาะเมื่อไม่มีไฟล์ที่ `failed`** · เหตุผล: ขั้น "อ่านสิ่งที่คุณเขียนกำกับไว้" เป็น `failed` เองเมื่อมีไฟล์ล้ม (`ingestion.md` §2.6 · `ingestion_view`) และขั้นหาหัวข้อไม่เริ่มจนกว่าไฟล์ที่ล้มจะถูกลองใหม่ (`ingestion.md` §2.4) ทางแก้จึงอยู่ที่แถวไฟล์ · มีหลายขั้นล้มพร้อมกัน → ปุ่มอยู่ที่ขั้นแรกที่ล้มเท่านั้น (endpoint ลองทุกขั้นที่ล้มในครั้งเดียว)
3. **กดปุ่ม (ไม่ถามยืนยัน · May 19 พ.ย.):**
   - ไฟล์ → `POST /materials/{material_id}/retry` (ไม่มี body) · ขั้นรวม → `POST /exam-preps/{id}/ingestion/retry` (ไม่มี body)
   - ระหว่างรอคำตอบ ปุ่มนั้น `disabled` (กดซ้ำไม่ส่งซ้ำ)
   - `202` → **poll `GET /ingestion` ทันที** (ไม่รอรอบ `POLL_MS`) แล้ว poll ตามปกติต่อ · สัญลักษณ์และปุ่มมาจากผล poll เท่านั้น (ไม่เปลี่ยนเป็น ◐ เองในหน้าเว็บ · กฎ "ตัวเลขและสถานะมาจาก API")
   - `409 not_failed` → ถือว่ามีคนลองใหม่ไปแล้ว: poll ทันทีแบบ `202` ไม่แสดง error
   - `404` → poll ทันที (หน้าเดิมจัดการ `404` ของ `GET /ingestion` ตาม upload-page.md §2.2 ข้อ 7)
   - `401` → ไม่แสดง error (`apiFetch` พาไปหน้า login)
   - error อื่น (`503`, network) → ข้อความ "ลองใหม่ไม่สำเร็จ ลองอีกครั้งได้" สีแดงใต้ปุ่มนั้น · ปุ่มกดได้อีก · poll ยังเดินตามเดิม
4. หลังกด ถ้าผล poll ครั้งถัดไปยัง `failed` อยู่ (เช่น API ยังไม่ได้เริ่ม) ปุ่มกลับมาให้กดได้ · ไม่มีตัวนับจำนวนครั้ง
5. การ poll เดิมไม่เปลี่ยน: ขั้นหรือไฟล์ที่ล้มไม่ทำให้หยุด poll (หยุดเฉพาะ `scope_ready`, ไม่มีไฟล์, poll ล้ม · upload-page.md §2.2)

### 2.2 API · `POST /materials/{id}/retry` (ต่อของจริง · เดิมเป็น stub)

1. ไม่มี token (`AUTH_REQUIRED=false`) → stub เดิม + `X-Stub` (ไม่เปลี่ยน)
2. มี token: อ่านแถวด้วย JWT ของผู้ใช้ (RLS) · ไม่พบ (ไม่มีจริงหรือของ tenant อื่น) → `404 not_found` · DB ล่ม → `503 db_unavailable`
3. `status` ไม่ใช่ `failed` → `409 not_failed` (api.md เดิม)
4. **ก่อนตอบ** (เพื่อให้ poll ถัดไปไม่เห็น `failed` เดิม):
   - `kind_confirmed = false` (ล้มตอน classify · S10) → `status = "uploaded"`, `error = null`
   - `kind_confirmed = true` (ล้มตอน ingest · S11) → `status = "confirmed"`, `error = null` และแถว `ingestion_jobs` ของไฟล์นี้ที่ `failed` กลับเป็น `queued`
5. ตอบ `202` + `Material` (แถวหลังข้อ 4) แล้วเริ่มงานเบื้องหลังโดยไม่รอ: classify ใหม่ (`runner.classify`) หรือ `runner.start(prep_id)` ซึ่งอ่านไฟล์ที่ `confirmed` แล้วสร้าง scope ใหม่เมื่อทุกไฟล์พร้อม (`ingestion.md` §2.1 ข้อ 3, §2.4 ข้อ 6) · งานเบื้องหลังมี tenant และ user ใน `ai_call_context` แบบ `/uploaded` และ `/confirm` (AI-04)

### 2.3 API · `POST /exam-preps/{id}/ingestion/retry` (ใหม่)

1. ไม่มี token → `202` + `X-Stub` ไม่ทำอะไร
2. มี token: อ่านความคืบหน้าด้วย JWT ของผู้ใช้แบบ `GET /ingestion` · ไม่พบ prep (ไม่มีจริงหรือของ tenant อื่น) → `404 not_found` · DB ล่ม → `503 db_unavailable`
3. ไม่มีขั้นรวม (`topics`, `stars`) ที่ `failed` **หรือ** มีไฟล์ที่ `failed` อยู่ → `409 not_failed` (ไฟล์ที่ล้มต้องลองใหม่ที่ไฟล์ · §2.1 ข้อ 2)
4. **ก่อนตอบ:** แถว `ingestion_jobs` ของขั้นรวม (`material_id` null) ทั้ง `topics` และ `stars` กลับเป็น `queued` (แบบ `_restart_steps` ที่ใช้ตอนมีไฟล์ใหม่ · ขั้นที่ `done` ก่อนหน้าทำใหม่ด้วย เพราะดาวคิดจากหัวข้อชุดใหม่)
5. ตอบ `202` ไม่มี body แล้ว `runner.start(prep_id)` โดยไม่รอ (ไม่มีไฟล์รอ → รัน `build_scope` รอบเดียว · หัวข้อชุดใหม่แทนชุดเดิม ไม่ซ้ำ · `ingestion.md` §2.4 ข้อ 6) · `ai_call_context` แบบ §2.2 ข้อ 5
6. runner ของ prep นี้ยังรันอยู่ → `start` คืน task เดิม (ไม่เริ่มซ้อน · `ingestion.md` §2.7) · ข้อ 3 กันกรณีนี้อยู่แล้วเพราะขั้นที่รันอยู่ไม่ใช่ `failed`

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (ไฟล์) | `POST /materials/{id}/retry` ไม่มี body | `POST /materials/7f…/retry` |
| Output (ไฟล์) | `202` + `Material` | `{"id": "7f…", "status": "confirmed", "error": null, …}` |
| Input (ขั้นรวม) | `POST /exam-preps/{id}/ingestion/retry` ไม่มี body | `POST /exam-preps/p1/ingestion/retry` |
| Output (ขั้นรวม) | `202` ไม่มี body | — |
| Error | `ErrorBody` ของ api.md | `409 {"error": {"code": "not_failed", …}}` |

## 4. Acceptance criteria

**หน้าเว็บ** (fetch จำลอง + fake timers · `tests/materials/ProgressPage.test.tsx` แบบเดิม)

- **AC-1 (CM-07)** Given ไฟล์ m1 `scan.pdf` `failed` When เปิดหน้า Then มีปุ่มชื่อ "ลองอ่าน scan.pdf ใหม่" ข้อความบนปุ่ม "ลองใหม่" · ไม่มีปุ่มชื่อ "ลองใหม่" ตรงตัว (ไม่ชนกับ AC-21 ของ upload-page.md)
- **AC-2 (CM-07)** Given AC-1 When กดปุ่ม Then `POST /materials/m1/retry` 1 ครั้ง ไม่มี body · ได้ `202` Then `GET /ingestion` ครั้งถัดไปเกิดก่อนครบ `POLL_MS` · ผลใหม่ m1 `running` Then ไม่มีปุ่มของ m1
- **AC-3 (CM-07)** Given AC-1 และ `POST` ยังไม่ตอบ When กดซ้ำ Then ปุ่ม `disabled` · `POST` 1 ครั้ง
- **AC-4 (CM-07)** Given ไม่มีไฟล์ `failed` · ขั้น "หาหัวข้อและลำดับการเรียน" `failed` Then มีปุ่ม "ลองขั้น หาหัวข้อและลำดับการเรียน ใหม่" · กดแล้ว `POST /exam-preps/p1/ingestion/retry` 1 ครั้ง · `202` Then poll ทันที · ผลใหม่ `scope_ready: true` Then ไป `/preps/p1/scope`
- **AC-5 (CM-07)** Given ไฟล์ m1 `failed` และขั้น "อ่านสิ่งที่คุณเขียนกำกับไว้" `failed` Then มีปุ่มของ m1 · ไม่มีปุ่มของขั้นรวมใดเลย
- **AC-6 (CM-07)** Given ขั้น "หาหัวข้อ…" และ "เทียบกับข้อสอบเก่า 2 ชุด" `failed` ทั้งคู่ (ไม่มีไฟล์ `failed`) Then ปุ่มขั้นรวม 1 ปุ่ม ที่ "หาหัวข้อ…"
- **AC-7 (CM-07)** Given ปุ่มไฟล์ (หรือขั้นรวม) When `POST` ได้ `409 not_failed` Then ไม่มีข้อความ error · poll ทันที
- **AC-8 (CM-07)** Given ปุ่มไฟล์ When `POST` ได้ `503` (หรือ network ล้ม) Then "ลองใหม่ไม่สำเร็จ ลองอีกครั้งได้" ใต้ปุ่ม · ปุ่มกดได้อีก · กดอีกครั้งได้ `202` Then ข้อความหาย · poll ยังเดินตาม `POLL_MS` ระหว่างนั้น
- **AC-9 (CM-07)** Given `POST` ได้ `401` Then ไม่มีข้อความ "ลองใหม่ไม่สำเร็จ…"
- **AC-10 (CM-07)** Given กดแล้ว `202` แต่ poll ถัดไปยังได้ m1 `failed` Then ปุ่มของ m1 กดได้อีก

**API** (fake repo / fake runner · ไม่เรียก AI จริง · `apps/api/tests/unit/`)

- **AC-11 (CM-07)** Given มี token · ไฟล์ของ tenant ตัวเอง `failed`, `kind_confirmed = true`, job `extract` `failed` When `POST /materials/{id}/retry` Then `202` · body `status = "confirmed"`, `error = null` · ก่อนตอบแถวไฟล์เป็น `confirmed` และ job `extract` เป็น `queued` · `runner.start(prep_id)` ถูกเรียก 1 ครั้ง · `classify` ไม่ถูกเรียก
- **AC-12 (CM-07)** Given ไฟล์ `failed`, `kind_confirmed = false` When retry Then `202` · `status = "uploaded"`, `error = null` · `runner.classify(id)` 1 ครั้ง · `start` ไม่ถูกเรียก
- **AC-13 (CM-07)** Given ไฟล์ `status` เป็น `ready` (และ `classified`, `confirmed`, `ingesting`, `uploaded` · parametrize) When retry Then `409 not_failed` · ไม่มีการเขียน · runner ไม่ถูกเรียก
- **AC-14 (SA-06)** Given ไฟล์ `failed` ของ tenant อื่น (JWT มองไม่เห็น) When retry Then `404 not_found` · ไฟล์นั้นไม่เปลี่ยน · runner ไม่ถูกเรียก · ไม่มีไฟล์นี้จริง → `404` เหมือนกัน
- **AC-15 (CM-07)** Given repo ล่ม (`DbUnavailableError`) When retry ไฟล์ หรือขั้นรวม Then `503 db_unavailable` · runner ไม่ถูกเรียก
- **AC-16 (CM-07)** Given ไม่มี token (`AUTH_REQUIRED=false`) When retry ไฟล์ Then stub เดิม (`X-Stub: true`) · When retry ขั้นรวม Then `202` + `X-Stub: true` · runner ไม่ถูกเรียกทั้งคู่
- **AC-17 (CM-07)** Given มี token · prep ของตัวเอง · ไฟล์ทั้งหมด `done` · job `topics` `failed` · `stars` `queued` When `POST /exam-preps/{id}/ingestion/retry` Then `202` ไม่มี body · ก่อนตอบ `topics` และ `stars` เป็น `queued` · `runner.start(prep_id)` 1 ครั้ง
- **AC-18 (CM-07)** Given `topics` `done` · `stars` `failed` When retry ขั้นรวม Then `202` · ทั้ง `topics` และ `stars` เป็น `queued` (ทำหัวข้อใหม่ด้วย · §2.3 ข้อ 4)
- **AC-19 (CM-07)** Given ไม่มีขั้นรวม `failed` (parametrize: ทุกขั้น `done` · `topics` `running` · ยังไม่มีแถวขั้นรวม) When retry ขั้นรวม Then `409 not_failed` · ไม่มีการเขียน · runner ไม่ถูกเรียก
- **AC-20 (CM-07)** Given `topics` `failed` แต่มีไฟล์ `failed` When retry ขั้นรวม Then `409 not_failed` · ไม่มีการเขียน
- **AC-21 (SA-06)** Given prep ของ tenant อื่น (หรือไม่มีจริง) ที่ `topics` `failed` When retry ขั้นรวม Then `404 not_found` · แถว job ไม่เปลี่ยน · runner ไม่ถูกเรียก
- **AC-22 (CM-07)** Given `IngestionRunner` กับ store ปลอม · ไฟล์ทุกไฟล์ `ready` · `topics` `failed` เพราะ A6 ได้ `ProviderRateLimited` When ลองขั้นรวมใหม่ (reset ตาม §2.3 ข้อ 4 แล้ว `start`) และ A6 ตอบได้ Then หัวข้อชุดใหม่ถูกเขียน · `topics`, `stars` เป็น `done` · `GET /ingestion` ได้ `scope_ready = true` (เส้นของ 19 พ.ย.)

## 5. Data changes

ไม่มี (ใช้ `materials.status`, `materials.error`, `ingestion_jobs.status` ที่มีอยู่ · ไม่มีตารางหรือ column ใหม่)

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /materials/{id}/retry` (มีแล้ว · เลิกเป็น stub เมื่อมี token) | ไม่มี body | `202` + `Material` · `404 not_found` · `409 not_failed` · `503 db_unavailable` |
| `POST /exam-preps/{id}/ingestion/retry` (**ใหม่**) | ไม่มี body | `202` ไม่มี body · `404 not_found` · `409 not_failed` · `503 db_unavailable` |

ไม่มี SSE event ใหม่ · ความคืบหน้ายังอ่านด้วย `GET /exam-preps/{id}/ingestion` (poll)

## 7. AI calls

ไม่มี call ใหม่ · ลองใหม่เรียก purpose เดิมของ ingestion (`classify_material`, A2–A7 ตาม `ingestion.md`) ผ่าน gateway ตามเดิม · 429 ใช้ตารางรอของ #159 (`gateway-rate-limit-backoff.md`)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `apps/web/tests/materials/ProgressRetry.test.tsx` (ใหม่ · ไฟล์แยกเพื่อไม่แตะ test ที่ review แล้ว) | component + fetch จำลอง + fake timers | AC-1 ถึง AC-10 |
| `apps/api/tests/unit/test_ingestion_retry_api.py` (ใหม่) | unit · TestClient + repo/reader/runner ปลอม | AC-11 ถึง AC-21 |
| `apps/api/tests/unit/test_ingestion_retry_runner.py` (ใหม่) | unit · `IngestionRunner` + store ปลอม + fake provider | AC-22 |
| ลองในเบราว์เซอร์บนเครื่อง May | manual | prep ที่ "หาหัวข้อ" ล้ม 19 พ.ย. → กด "ลองใหม่" → ไปหน้า scope |

Test เดิมที่ review แล้วไม่แก้: `ProgressPage.test.tsx` AC-19 ("…no retry button") ยังผ่าน เพราะ `aria-label` ไม่ใช่ "ลองใหม่" ตรงตัว (§10 ข้อ 1)

## 9. Out of scope

- ปุ่ม "ไปต่อโดยไม่มีไฟล์นี้" (UC-02 E5) · ต้องใช้ `DELETE /materials/{id}` และตัดสินเรื่องหัวข้อของไฟล์ที่ลบ (api.md รอตัดสินข้อ 3 · CM-10 · S5)
- ปุ่มลองใหม่ในหน้ายืนยันประเภท S10 (ไฟล์ที่ classify ล้ม) · API รองรับแล้ว (§2.2 ข้อ 4) แต่หน้าเว็บ S10 ยังไม่มีปุ่ม (upload-page.md AC-19 ที่ review แล้ว)
- ลองใหม่อัตโนมัติ, จำกัดจำนวนครั้ง, แจ้งเหตุผลว่าทำไมล้ม (เช่น "AI ไม่ว่าง") · ข้อความ error ยังมาจาก API ตามเดิม
- runner หลายเครื่อง (`ingestion.md` §2.7 · demo เครื่องเดียว)

## 10. Open questions

ตัดสินแล้ว (May 19 พ.ย. · ทุกข้อใช้ข้อเสนอ)

1. **test ที่ review แล้ว `ProgressPage.test.tsx` AC-19** ("…shows the API's message and no retry button") · **ไม่แก้ test** · แก้ข้อความ AC-19 ใน upload-page.md ให้ชี้มาที่ spec นี้ · test ยังผ่านเพราะเช็คชื่อปุ่ม "ลองใหม่" ตรงตัว
2. **ข้อความ:** ใช้ตาม §2.1 ("ลองใหม่" · "ลองอ่าน {file_name} ใหม่" · "ลองขั้น {label} ใหม่" · "ลองใหม่ไม่สำเร็จ ลองอีกครั้งได้") · อยู่ใน `components/materials/strings.ts`
3. **ขั้นรวมตอบ `202` ไม่มี body** · หน้าเว็บ poll เองทันที (ทางเดียวกับปุ่มไฟล์)
4. **ลองขั้นรวมใหม่ทำ `topics` ใหม่เสมอ** แม้ล้มแค่ `stars` (§2.3 ข้อ 4) · แยกขั้นเป็นงานของ Jam ทีหลังถ้าต้องการ
5. **กดซ้ำได้ไม่จำกัด** ในรอบนี้ (gateway รอ 429 ให้แล้ว #159)

## 11. Spec changes needed

- `specs/system/api.md` (**shared** · บอกกลุ่มก่อน merge): ตาราง endpoint เพิ่ม `POST /exam-preps/{id}/ingestion/retry` · ย่อหน้า v1.21 "`/retry` … ยังเป็น stub" → `/retry` ทำงานจริงเมื่อมี token · `POST /materials/{id}/retry` เพิ่ม `404`, `503` และ "ก่อนตอบ job ที่ล้มกลับเป็น `queued`" · รอตัดสินข้อ 8 → ตัดสินแล้ว (spec นี้) · bump version
- `specs/features/exam-prep/upload-page.md` (ของ May): §2.2 ข้อ 8 และ §9 ข้อ 2 → ปุ่ม "ลองใหม่" ย้ายมาที่ spec นี้ · "ไปต่อโดยไม่มีไฟล์นี้" ยังไม่มี · AC-19 ตาม §10 ข้อ 1
- `specs/features/scope/ingestion.md` (ของ Jam): §2.1 ข้อ 3 เพิ่มทางเข้า "ลองขั้นรวมใหม่" (reset `topics`, `stars` แล้ว `start`) · `retry_material` ไม่รอ classify ใน request (ปัจจุบัน `IngestionRunner.retry` await `classify_material` ตรงๆ)
