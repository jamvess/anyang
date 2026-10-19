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
- [ ] 3. 🙋 เปิด PR แล้วดูว่า job `deploy` ของ `web-deploy` รันและเขียว (เปิด PR → แท็บ **Checks** → `web-deploy / deploy` ต้องเป็น ✓ และมีปุ่ม **View deployment**)

## Definition of done

- PR ที่แก้แค่ `config/ai.yaml` ทำให้ `web-deploy` รัน (preview ใน PR, production เมื่อ merge เข้า `main`)
- `infra/README.md` บอกเงื่อนไขที่ทำให้ deploy ตรงกับ workflow
- CI เขียว · May รู้ว่าอ่าน `config/ai.yaml` ตอน build ได้แล้ว

## Decisions

- 2026-10-19 · เพิ่มแค่ `config/ai.yaml` ไม่ใช่ `config/**` · หน้าเว็บใช้แค่ `guards` ใน `ai.yaml` ส่วนตัวเลขของ learning model ต้องมาจาก API (กฎ UI ใน `roles.md`) จึงไม่ควรทำให้เว็บ deploy ใหม่เมื่อ `learning.yaml` เปลี่ยน
- 2026-10-19 · ไม่ต้องแก้ `ci.yml` · job `web` รันกับทุก PR อยู่แล้ว (ไม่มี `paths` filter)
- 2026-10-19 · ตรวจ YAML ด้วย PyYAML (parse ได้, `paths` ครบทั้ง 2 event) · ไม่มี `actionlint` บนเครื่อง ใช้ผลรันจริงบน GitHub แทน

## Next step

🙋 Junior: commit + push แล้วเปิด PR #19 แท็บ **Checks** ดูว่า `web-deploy / deploy` เป็น ✓ และมีปุ่ม **View deployment**

## Waiting on

ไม่มี

## Notes for next time

- การแก้ `web-deploy.yml` เองก็ทำให้ workflow รันอยู่แล้ว ดังนั้นการที่ PR นี้รันยังไม่ได้พิสูจน์ว่า path ของ `config/ai.yaml` ใช้ได้ ต้องดูจาก PR ถัดไปที่แก้แค่ `config/ai.yaml`
