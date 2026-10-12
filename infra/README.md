# infra/

- `cloudbuild.yaml` · build + deploy backend ไป Cloud Run staging เมื่อ push เข้า `main`
- frontend deploy ผ่าน Vercel (เชื่อม GitHub repo, root directory = `apps/web`)
- Terraform ย้ายไปเทอม 2 (S6) ตอนนี้สร้าง resource ด้วยคำสั่งใน `docs/team/setup.md` §5

ค่า `--concurrency` และ `--timeout` เป็นค่าเริ่มต้น ปรับตามผลวัดใน PoC P6-lite
