# web-deploy รันใหม่เมื่อ `config/ai.yaml` เปลี่ยน

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/web-deploy-config-paths` |
| Checklist item | — (งานเล็กนอก checklist · ให้หน้าแชทของ May อ่าน `guards` จาก `config/ai.yaml` ตอน build ได้) |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🤖 เพิ่ม `config/ai.yaml` ใน `paths` ของ `pull_request` และ `push` ใน `.github/workflows/web-deploy.yml` + อัปเดตหัวข้อ "ทำงานยังไง" ใน `infra/README.md`
- [x] 2. 🤖 ตรวจว่า YAML ของ workflow ถูกต้อง (parse ด้วย Python + `actionlint` ถ้ามีบนเครื่อง)
- [x] 3. 🙋 เปิด PR แล้วดูว่า job `deploy` ของ `web-deploy` รันและเขียว (เปิด PR → แท็บ **Checks** → `web-deploy / deploy` ต้องเป็น ✓ และมีปุ่ม **View deployment**)

## Definition of done

- PR ที่แก้แค่ `config/ai.yaml` ทำให้ `web-deploy` รัน (preview ใน PR, production เมื่อ merge เข้า `main`)
- `infra/README.md` บอกเงื่อนไขที่ทำให้ deploy ตรงกับ workflow
- CI เขียว · May รู้ว่าอ่าน `config/ai.yaml` ตอน build ได้แล้ว

## Decisions

- 2026-10-19 · เพิ่มแค่ `config/ai.yaml` ไม่ใช่ `config/**` · หน้าเว็บใช้แค่ `guards` ใน `ai.yaml` ส่วนตัวเลขของ learning model ต้องมาจาก API (กฎ UI ใน `roles.md`) จึงไม่ควรทำให้เว็บ deploy ใหม่เมื่อ `learning.yaml` เปลี่ยน
- 2026-10-19 · ไม่ต้องแก้ `ci.yml` · job `web` รันกับทุก PR อยู่แล้ว (ไม่มี `paths` filter)
- 2026-10-19 · ตรวจ YAML ด้วย PyYAML (parse ได้, `paths` ครบทั้ง 2 event) · ไม่มี `actionlint` บนเครื่อง ใช้ผลรันจริงบน GitHub แทน
- 2026-10-19 · GitHub ไม่ได้ส่ง event `synchronize` หลัง push `6247e0d` (PR ค้างที่ commit แรก) · แก้ด้วย Close/Reopen PR #19 · ได้ web-deploy 2 run: 39208944400 ถูก `concurrency` ยกเลิก (deployment ขึ้น `error`) และ 39208969564 สำเร็จ · preview https://anyang-ec90m7h4t-anyang4.vercel.app
- 2026-10-19 · web-deploy บน PR #16 พัง `Could not retrieve Project Settings` 3 รอบ · Jam แก้ Vercel token ให้ไม่หมดอายุแล้ว · rerun 39206089525 ผ่าน

## Next step

พิมพ์ `/work-done` เพื่อปิดงานและเปิด PR #19 ให้ review

## Waiting on

ไม่มี

## Notes for next time

- การแก้ `web-deploy.yml` เองก็ทำให้ workflow รันอยู่แล้ว ดังนั้นการที่ PR นี้รันยังไม่ได้พิสูจน์ว่า path ของ `config/ai.yaml` ใช้ได้ ต้องดูจาก PR ถัดไปที่แก้แค่ `config/ai.yaml`
