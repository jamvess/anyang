# specs/ · แหล่งความจริงของโปรเจกต์

ทุกอย่างที่ระบบทำต้องมีที่มาจากไฟล์ในโฟลเดอร์นี้ ทั้งคนและ AI coding agent อ่านที่นี่ก่อนเขียนโค้ดเสมอ

## โครงสร้าง 3 ระดับ (Spec-Driven Development)

| ระดับ | ไฟล์ | ตอบคำถาม | ใครแก้ |
|---|---|---|---|
| 1 · Requirement | `requirements/requirements.md` | ระบบต้องทำอะไร (FR, NFR) | ทั้งทีม ต้อง review |
| 2 · System design | `system/*.md`, `../supabase/migrations/*.sql`, `../config/*.yaml` | ส่วนประกอบไหนทำอะไร ต่อกันยังไง ข้อมูลอยู่ไหน | เจ้าของส่วนนั้น + review 1 คน |
| 3 · Feature | `features/<area>/<feature>.md` | feature นี้ทำงานยังไงแบบละเอียดพอให้เขียน test ได้ | คนทำ feature (ร่างด้วย `/spec-feature`) + review |
| PoC | `poc/README.md`, `poc/reports/*.md` | ส่วนเสี่ยงทำได้จริงไหม ผลเท่าไหร่ ตัดสินใจอะไร | เจ้าของ PoC |

## ไฟล์ใน `system/`

| ไฟล์ | เนื้อหา |
|---|---|
| `architecture.md` | Tech stack, components, deployment, environments, multi-tenant |
| `ai-orchestration.md` | AI flows 2.1–2.11 ฉบับเต็ม (v1.1) |
| `learning-model.md` | สูตรและตัวเลขของ learning model พร้อมที่มา (งานวิจัย / มาตรฐาน / calibrate) |
| `data-model.md` | ERD และคำอธิบายตาราง (SQL จริงอยู่ที่ `supabase/migrations/`) |
| `api.md` | REST endpoints, SSE events, รูปแบบ error |
| `glossary.md` | คำศัพท์ |

## วงจรทำงานของ 1 feature

1. **Spec:** `/spec-feature scope/compute-importance SM-03` → ได้ร่าง feature spec → คน review
2. **Tests:** `/spec-to-tests specs/features/scope/compute-importance.md` → ได้ test ที่ fail → **คน review test** (จุดสำคัญที่สุด)
3. **Implement:** `/implement-feature specs/features/scope/compute-importance.md` → เขียนจน test ผ่าน
4. **CI:** lint, unit, integration, RLS isolation, evals (ถ้าแก้ prompt)
5. **PR review** โดยเพื่อนในทีม → merge → deploy staging อัตโนมัติ

ถ้าระหว่างทางพบว่า spec ไม่ชัด ให้หยุดแล้วแก้ spec ก่อน ห้ามให้ agent เดา

## กฎการแก้ spec

- แก้ spec ผ่าน PR เหมือนโค้ด
- เปลี่ยนตัวเลขใน `config/learning.yaml` ต้องแก้ `learning-model.md` ส่วนที่มาของตัวเลขด้วย
- เปลี่ยน behavior ที่มีอยู่แล้ว → แก้ feature spec + test ใน PR เดียวกัน
- เพิ่ม requirement ใหม่ → เพิ่ม ID ใหม่ใน `requirements.md` ห้ามใช้ ID ซ้ำ
