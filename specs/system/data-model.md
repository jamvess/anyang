# Data model (v1.2)

SQL จริงอยู่ที่ `supabase/migrations/` เริ่มจาก `0001_init.sql` (ทดสอบรันบน PostgreSQL + pgvector แล้ว และทดสอบ RLS ว่า user A มองไม่เห็นข้อมูลของ user B) แล้วแก้ต่อด้วย migration ใหม่ทีละไฟล์ ไม่แก้ไฟล์เดิม ไฟล์นี้อธิบายภาพรวมและเหตุผล

| Migration | เปลี่ยนอะไร |
|---|---|
| `0002_messages_attachment_name.sql` | เพิ่ม `messages.attachment_name` (api.md v1.3 · 2026-10-21) |

## กฎทั่วไป

- ทุกตารางมี `tenant_id` และเปิด RLS (SA-06)
- ตารางที่เป็นข้อมูลส่วนตัว (profiles, exam_preps, tutor_sessions, attempts, topic_progress, ...) ต้องผ่านทั้ง `tenant_id = current_tenant_id()` และ `user_id = auth.uid()`
- `tenant_id` อยู่ใน JWT เป็น custom claim ใส่โดย `custom_access_token_hook` ต้องเปิด hook นี้ใน Supabase (Authentication → Hooks)
- สมัครสมาชิกแล้ว trigger `handle_new_user` สร้าง personal tenant + membership + profile ให้อัตโนมัติ
- งานเบื้องหลัง (ingestion) ใช้ service role ซึ่งข้าม RLS จึงต้องใส่ `tenant_id` เองทุกครั้ง
- ค่า threshold ไม่อยู่ใน DB ทั้งหมดอยู่ใน `config/learning.yaml`
- Storage path: `{tenant_id}/{exam_prep_id}/{material_id}` และตั้ง storage policy ให้อ่านได้เฉพาะ prefix ของ tenant ตัวเอง
- `messages.attachment_name` คือชื่อไฟล์เดิมที่ user เห็น (เช่น "วิธีทำ.jpg") · ค่ามาจาก user จึงใช้แสดงผลอย่างเดียว **ห้ามใช้ประกอบ path ใน Storage** · `attachment_path` ตั้งชื่อด้วย uuid เสมอ · ความยาวสูงสุดคือ `config/ai.yaml` → `guards.max_attachment_name_chars` (นับเป็น grapheme cluster) ตรวจที่ API ไม่มี `CHECK` ใน SQL · ชื่อที่ยาวเกินให้ **ตัดให้สั้น ไม่ปฏิเสธ**: ตัดเป็น grapheme cluster (สระและวรรณยุกต์ไทยต้องติดกับพยัญชนะ ไม่ตัดตาม code point) และเก็บนามสกุลไฟล์ไว้ (2026-10-21 · ข้อความใน api.md จะตามมาพร้อม PR ของ api.md ข้อ 5 · guard จริงทำพร้อม endpoint uploads ใน S3)

## ERD

ครบทุกตาราง (27 ตารางใน `public`) และทุก foreign key ใน `0001_init.sql` แบ่งเป็น 3 รูปตามกลุ่ม

วิธีอ่าน:

- `users` ในรูปคือ `auth.users` ของ Supabase (ไม่ได้อยู่ใน `public`)
- **ไม่ได้ลากเส้น `tenant_id`** · ทุกตารางยกเว้น `tenants` มี `tenant_id → tenants(id) on delete cascade` (26 ตาราง) รูป 1 ลากให้ดูแค่ `org_units` กับ `memberships` และรูป 2–3 ไม่ได้ใส่ `tenant_id` ใน column
- ข้อความบนเส้นคือชื่อ FK column ฝั่งลูก
- `||` = มี 1 แถวเสมอ · `|o` = มี 0 หรือ 1 แถว (FK เป็น null ได้) · `o{` = 0 แถวขึ้นไป · `o|` ฝั่งลูก = ไม่เกิน 1 แถว
- ตารางที่มี column แค่ `id` เป็นตารางจากรูปอื่น ใส่ไว้ให้เห็นว่าเส้นเชื่อมไปไหน
- แสดงเฉพาะ PK, FK และ column สำคัญ ส่วน column ทั้งหมดดูใน SQL

### รูป 1 · Tenancy + User

```mermaid
erDiagram
  tenants ||--o{ org_units : "tenant_id"
  tenants ||--o{ memberships : "tenant_id"
  org_units |o--o{ org_units : "parent_id"
  org_units |o--o{ memberships : "org_unit_id"
  users ||--o{ memberships : "user_id"
  users ||--o| profiles : "user_id"
  users ||--o{ tutor_profiles : "user_id"
  users ||--o{ buddy_profiles : "user_id"

  tenants {
    uuid id PK
    text type "personal | organization"
    text plan
    int quota_tokens_day
    text status "active | suspended"
  }
  org_units {
    uuid id PK
    uuid tenant_id FK
    uuid parent_id FK "null = root"
    text name
  }
  memberships {
    uuid user_id PK, FK
    uuid tenant_id PK, FK
    uuid org_unit_id FK
    text role "owner | student | teacher | admin"
  }
  users {
    uuid id PK "auth.users"
  }
  profiles {
    uuid user_id PK, FK
    text nickname
    text education_level
    text explain_language
  }
  tutor_profiles {
    uuid id PK
    uuid user_id FK
    jsonb params "enum-only persona"
    int version
  }
  buddy_profiles {
    uuid id PK
    uuid user_id FK
    bool enabled
    jsonb params
    int version
  }
```

### รูป 2 · Content + Scope

```mermaid
erDiagram
  users ||--o{ exam_preps : "user_id"
  exam_preps ||--o{ materials : "exam_prep_id"
  exam_preps ||--o{ topics : "exam_prep_id"
  exam_preps ||--o{ scope_versions : "exam_prep_id"
  exam_preps ||--o{ scope_changes : "exam_prep_id"
  scope_versions |o--o{ exam_preps : "active_scope_version_id"
  materials ||--o{ material_pages : "material_id"
  materials ||--o{ chunks : "material_id"
  materials ||--o{ ingestion_jobs : "material_id"
  materials ||--o{ past_exam_questions : "material_id"
  topics ||--o{ topic_skills : "topic_id"
  topics ||--o{ topic_chunks : "topic_id"
  chunks ||--o{ topic_chunks : "chunk_id"
  topics |o--o{ past_exam_questions : "topic_id"
  topic_skills |o--o{ past_exam_questions : "skill_id"
  topics |o--o{ scope_changes : "topic_id"

  users {
    uuid id PK "auth.users"
  }
  exam_preps {
    uuid id PK
    uuid user_id FK
    uuid active_scope_version_id FK
    text title
    date exam_date
    int daily_minutes
    text status "active | archived"
  }
  materials {
    uuid id PK
    uuid exam_prep_id FK
    text storage_path
    text kind "sheet | slides | past_exam | notes | other"
    numeric relevance_weight
    text status
  }
  material_pages {
    uuid id PK
    uuid material_id FK "unique with page_no"
    int page_no
    text extract_method
  }
  chunks {
    uuid id PK
    uuid material_id FK
    int page_from
    int page_to
    text text
    vector embedding "768 dims, wait P3"
  }
  ingestion_jobs {
    uuid id PK
    uuid material_id FK
    text stage
    numeric progress
    text status
  }
  topics {
    uuid id PK
    uuid exam_prep_id FK
    text name
    int order_index
    uuid_array prereq_ids "no FK, array of topics.id"
    smallint importance "0-3 stars"
    text importance_source "computed | user"
    numeric signal_r
    text status "draft | confirmed | excluded"
  }
  topic_skills {
    uuid id PK
    uuid topic_id FK
    text name
    int exam_freq
    jsonb common_mistakes
  }
  past_exam_questions {
    uuid id PK
    uuid material_id FK
    uuid topic_id FK
    uuid skill_id FK
    text q_no
    text reference_answer
  }
  topic_chunks {
    uuid topic_id PK, FK
    uuid chunk_id PK, FK
    numeric score
  }
  scope_changes {
    uuid id PK
    uuid exam_prep_id FK
    uuid topic_id FK
    text op
    jsonb before
    jsonb after
    text actor "user | ai | system"
  }
  scope_versions {
    uuid id PK
    uuid exam_prep_id FK "unique with version"
    int version
    text status "draft | confirmed"
    jsonb snapshot
  }
```

### รูป 3 · Tutoring + Progress + Logs

```mermaid
erDiagram
  users ||--o{ tutor_sessions : "user_id"
  exam_preps ||--o{ tutor_sessions : "exam_prep_id"
  scope_versions ||--o{ tutor_sessions : "scope_version_id"
  topics |o--o{ tutor_sessions : "current_topic_id"
  tutor_sessions ||--o{ messages : "session_id"
  tutor_sessions ||--o{ problems : "session_id"
  topics ||--o{ problems : "topic_id"
  topic_skills |o--o{ problems : "skill_id"
  problems ||--o{ attempts : "problem_id"
  users ||--o{ attempts : "user_id"
  topics ||--o{ attempts : "topic_id"
  topic_skills |o--o{ attempts : "skill_id"
  attempts ||--o{ checker_disagreements : "attempt_id"
  users ||--o{ topic_progress : "user_id"
  exam_preps ||--o{ topic_progress : "exam_prep_id"
  topics ||--o{ topic_progress : "topic_id"
  users ||--o| user_stats : "user_id"
  tutor_sessions ||--o{ planner_decisions : "session_id"
  tutor_sessions ||--o{ buddy_events : "session_id"
  topics |o--o{ buddy_events : "topic_id"
  messages |o--o{ buddy_events : "message_id"
  users |o--o{ ai_calls : "user_id"
  tutor_sessions |o--o{ ai_calls : "session_id"

  users {
    uuid id PK "auth.users"
  }
  exam_preps {
    uuid id PK "see figure 2"
  }
  scope_versions {
    uuid id PK "see figure 2"
  }
  topics {
    uuid id PK "see figure 2"
  }
  topic_skills {
    uuid id PK "see figure 2"
  }
  tutor_sessions {
    uuid id PK
    uuid user_id FK
    uuid exam_prep_id FK
    uuid scope_version_id FK
    uuid current_topic_id FK
    text stage "probe | teach | verify | practice | done | park"
    text mode "normal | tight | triage | final"
    bool buddy_muted
    text end_reason
  }
  messages {
    uuid id PK
    uuid session_id FK
    text role "user | tutor | buddy | card | system"
    text content
    jsonb card
    text input_mode "text | voice | image"
    text attachment_path "uuid path in Storage"
    text attachment_name "display only (0002)"
  }
  problems {
    uuid id PK
    uuid session_id FK
    uuid topic_id FK
    uuid skill_id FK
    text source "generated | past_exam | doc"
    uuid source_ref "no FK"
    text answer_format
    bool verified
    text purpose "probe | verify | practice | review"
  }
  attempts {
    uuid id PK
    uuid user_id FK
    uuid problem_id FK
    uuid topic_id FK
    uuid skill_id FK
    text verdict
    bool is_correct
    text error_type
    text decided_by "sympy | llm"
    bool independent
  }
  checker_disagreements {
    uuid id PK
    uuid attempt_id FK
    jsonb sympy_result
    jsonb llm_result
  }
  topic_progress {
    uuid user_id PK, FK
    uuid topic_id PK, FK
    uuid exam_prep_id FK
    numeric mastery
    text level "not_started | weak | developing | passed"
    jsonb skill_coverage
    int review_step
    date next_review_at
  }
  user_stats {
    uuid user_id PK, FK
    numeric avg_minutes_per_problem
    numeric avg_session_minutes
  }
  planner_decisions {
    uuid id PK
    uuid session_id FK
    jsonb decision
    text reason_code
  }
  buddy_events {
    uuid id PK
    uuid session_id FK
    uuid topic_id FK
    uuid message_id FK
    text role
    text trigger
  }
  ai_calls {
    uuid id PK
    uuid user_id FK
    uuid session_id FK
    text purpose
    text model
    text prompt_version
    int tokens_in
    int tokens_out
  }
```

### FK ที่ไม่ใช่ `on delete cascade`

FK ส่วนใหญ่เป็น `on delete cascade` (ลบแม่แล้วลูกหายตาม) ยกเว้น:

- `on delete set null` (ลบแม่แล้วลูกยังอยู่ แต่ FK กลายเป็น null): `memberships.org_unit_id`, `exam_preps.active_scope_version_id`, `past_exam_questions.topic_id` / `skill_id`, `tutor_sessions.current_topic_id`, `problems.skill_id`, `attempts.skill_id`, `buddy_events.topic_id` / `message_id`, `ai_calls.user_id` / `session_id`
- ไม่มี `on delete` (ลบแม่ไม่ได้ถ้ายังมีลูก): `tutor_sessions.scope_version_id`
- ไม่มี FK แต่เก็บ id: `topics.prereq_ids` (array ของ `topics.id`) และ `problems.source_ref` (spec ยังไม่ได้ระบุว่าชี้ไปตารางไหน · ดู "สิ่งที่ยังไม่ชัด" ด้านล่าง)

## ตารางตาม flow

| กลุ่ม | ตาราง | หน้าที่ | Flow |
|---|---|---|---|
| Tenancy | `tenants`, `org_units`, `memberships` | แยกข้อมูลและโควตา v1 ใช้ personal tenant ส่วน `org_units` เตรียมไว้สำหรับสถาบัน | 3.4 |
| User | `profiles`, `tutor_profiles`, `buddy_profiles` | ข้อมูลผู้ใช้และ persona (params เท่านั้นที่เข้า prompt) | 2.7 |
| Content | `exam_preps`, `materials`, `material_pages`, `chunks`, `ingestion_jobs` | ไฟล์ ข้อความรายหน้า chunk + vector และความคืบหน้า | 2.3 |
| Scope | `topics`, `topic_skills`, `past_exam_questions`, `topic_chunks`, `scope_changes`, `scope_versions` | หัวข้อ ดาว skills ข้อสอบเก่ารายข้อ ประวัติการแก้ และ snapshot ที่ยืนยันแล้ว | 2.3 |
| Tutoring | `tutor_sessions`, `messages`, `problems`, `attempts` | บทสนทนา โจทย์พร้อมเฉลย และผลตรวจแต่ละครั้ง | 2.2, 2.4 |
| Progress | `topic_progress`, `user_stats` | mastery, skill coverage, รอบทวน, เวลาเฉลี่ยต่อข้อ | 2.2, 2.5 |
| Logs | `planner_decisions`, `buddy_events`, `checker_disagreements`, `ai_calls` | อธิบายการตัดสินใจย้อนหลัง, quota buddy, ปรับ prompt, ต้นทุน | 2.5, 2.1, 2.4, 2.11 |

Golden sets ของการวัดผล AI ไม่อยู่ใน DB แต่อยู่ในโฟลเดอร์ `evals/`

## สิ่งที่ยังไม่ชัด

- `problems.source_ref` เป็น `uuid` ที่ไม่มี FK · `ai-orchestration.md` §3 ระบุแค่ชื่อ column ไม่ได้บอกว่าตอน `source = past_exam` หรือ `doc` ต้องชี้ไปตารางไหน (น่าจะเป็น `past_exam_questions` / `chunks` แต่ยังไม่ได้ตกลงกัน)

## สิ่งที่ยังรอผล PoC

- มิติของ `chunks.embedding` (ตอนนี้ `vector(768)`) เปลี่ยนตาม embedding model ที่เลือกใน P3 ด้วย migration ใหม่
- index แบบ HNSW ใช้ cosine distance ยืนยันอีกครั้งหลังเลือก model

### สิ่งที่อาจต้องแก้ใน schema จาก P3a (จดไว้ 2026-10-20 · ยังไม่เขียน migration)

อ่านจาก branch `poc/P3` (`apps/api/app/models/scope_ai.py`, `poc/P3/`, `docs/worklog/poc-P3.md`) · ทุกข้อด้านล่างเป็นแค่ข้อเสนอ รอผลจริงก่อน

**ตรวจสถานะ 2026-10-21:** ยังไม่มีข้อไหนยืนยันได้ จึงยังไม่เขียน migration · A6 และ A7 ยังไม่เคยรันผ่าน (19 ต.ค. ได้ 503 แล้วโควตาหมด · 20 ต.ค. ได้ 503 ทั้ง 2 รอบ · 21 ต.ค. โควตารายวันของ `gemini-3.5-flash` หมด) · ยังไม่มี report P3a (PR #37) · P3b (PR #39 embedding) ไม่เกี่ยวกับ 5 ข้อนี้

| # | ที่มาใน P3 | schema ตอนนี้ | ข้อเสนอ | สถานะ 2026-10-21 |
|---|---|---|---|---|
| 1 | A6 `merge_topics` คืน `sources` (ช่วงหน้าของแต่ละหัวข้อ) เพราะขั้น 5d ต้องใช้สร้าง `topic_chunks` และ SM-04 ต้องแสดงเลขหน้า | `topics` ไม่มีที่เก็บช่วงหน้า | เพิ่มตาราง `topic_sources (topic_id, material_id, page_from, page_to)` หรือ `topics.sources jsonb` · ต้องเลือกหลังรู้ว่าจะ query ช่วงหน้าไหม | รอผล · A6 ยังไม่เคยผ่าน schema |
| 2 | A4 `split_past_exam` คืน `points` (คะแนนของข้อ) | `past_exam_questions` ไม่มี column คะแนน | ถ้าสูตรดาวหรือ planner จะใช้คะแนน ให้เพิ่ม `points numeric` · ถ้าไม่ใช้ ไม่ต้องเพิ่ม | รอผล · A4 ตรงกับ label 43/43 และคืน `points` จริง แต่ `poc/P3/stars.py` ไม่ใช้ `points` · ตัดสินตอนทำ `compute_importance` (P8-lite, S4) |
| 3 | A7 `map_questions` คืน `topic_id: null` พร้อม `note` (ข้อที่ map ไม่ได้ ตรงกับ `unmapped` ใน label) | `topic_id` เป็น null ได้แล้ว แต่ไม่มีที่เก็บเหตุผล | อาจเพิ่ม `map_note text` ให้หน้า scope แสดงว่าทำไมข้อนี้ไม่มีหัวข้อ | รอผล · A7 ยังไม่ได้รัน |
| 4 | A6 คืน `excluded_by_note` (หัวข้อที่ตัดออกเพราะ note ของผู้ใช้) | มี `topics.status = 'excluded'` แต่ไม่รู้ว่าใครตัด | น่าจะพอด้วย `status = 'excluded'` + บันทึกใน `scope_changes` (`actor = 'ai'`) · ไม่ต้องเพิ่ม column ถ้าตกลงแบบนี้ | รอผล · A6 ยังไม่เคยผ่าน schema |
| 5 | ingest ใช้ `vision_extract_pages` อ่านทั้งไฟล์ใน call เดียว และวัด % ตัวอักษรไทยเพื่อเลือกระหว่าง text layer กับ vision | `material_pages.extract_method` มี `vision` อยู่แล้ว · ไม่มีที่เก็บค่าคุณภาพข้อความ | ไม่ต้องแก้ ถ้าไม่ต้องการ debug ย้อนหลัง · ถ้าต้องการ ให้เพิ่ม `material_pages.text_quality numeric` | รอตัดสิน · ingest ยืนยันว่าเกณฑ์ % ไทยแยกได้ (สแกน 0%, ชีท 48–85%) และ `extract_method` พอสำหรับการเลือกวิธี · จะเก็บค่าไว้ debug หรือไม่ ข้อมูล P3 ตอบไม่ได้ |

ไม่กระทบ schema: `thinking` อยู่ใน `config/ai.yaml` · ค่า `stars.*` อยู่ใน `config/learning.yaml` · `q_no` แบบ `ก1.2` เก็บใน `text` ได้อยู่แล้ว
