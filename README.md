# อ่านยัง? · ระบบห้องติวเตรียมสอบด้วยปัญญาประดิษฐ์

Senior project · ภาควิชาวิศวกรรมคอมพิวเตอร์ มจธ. · อาจารย์ที่ปรึกษา ดร.สุเทพ มาดารัศมี

ผู้เรียนอัปโหลดชีท สไลด์ และข้อสอบเก่า ระบบสกัดหัวข้อพร้อมดาวความสำคัญให้ยืนยัน แล้วติวในห้องแชทเดียวกับ AI Tutor (และ AI Buddy ถ้าเปิด) ที่เลือกหัวข้อเอง ให้โจทย์ ตรวจคำตอบลายมือ สอนทันทีเมื่อผิด และติดตามความก้าวหน้า

## เริ่มต้น

1. ตั้งค่าเครื่องตาม [`docs/team/setup.md`](docs/team/setup.md)
2. อ่านหน้าที่ของตัวเองใน [`docs/team/roles.md`](docs/team/roles.md)
3. ดูงาน sprint ปัจจุบันใน [`docs/team/sprint-checklists.md`](docs/team/sprint-checklists.md)
4. ก่อนเขียนโค้ด อ่าน [`CLAUDE.md`](CLAUDE.md) และ [`specs/README.md`](specs/README.md)

## โครงสร้าง

| Path | เนื้อหา |
|---|---|
| `apps/web` | Frontend · Next.js + TypeScript + Tailwind + KaTeX · Vercel |
| `apps/api` | Backend · FastAPI + SSE · Google Cloud Run |
| `supabase/migrations` | Data model (PostgreSQL + pgvector + RLS) |
| `specs/` | Requirements, system design, AI flows, learning model, API, feature specs, PoC specs |
| `config/` | ค่า threshold ของ learning model และการเลือก model ของ AI |
| `prompts/` | Prompt แยกตาม purpose มี version |
| `evals/` | Golden sets และ script วัดผล AI |
| `infra/` | Cloud Build และ deploy |
| `docs/team/` | หน้าที่ วิธีตั้งค่า checklist ราย sprint |

## Tech stack (สรุป)

Next.js · TypeScript · Tailwind · KaTeX · Vercel · FastAPI · Pydantic · SSE · Cloud Run · Cloud Build · GitHub Actions · Supabase (PostgreSQL, pgvector, Auth, Storage, RLS) · Gemini บน Vertex AI (primary) · Claude API (fallback) · SymPy · Google Cloud STT/TTS · Sentry · Claude Code

รายละเอียดและเหตุผลอยู่ใน [`specs/system/architecture.md`](specs/system/architecture.md)
