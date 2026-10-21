# CORS ใน FastAPI ให้หน้าเว็บเรียก API ได้

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/api-cors` |
| Checklist item | ไม่มีข้อตรงๆ · งานที่ May ขอ (room-http.md Open question 6 ทาง ก) เพื่อให้ "หน้าแชทของ May คุยกับ Gemini ผ่าน staging ได้" (Done ของ S3) |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 test `tests/unit/test_cors.py` จาก requirement ของ May → red · Junior review test ก่อน implement
- [ ] 2. 🤖 `EnvSettings.cors_allow_origins` (comma-separated, default `http://localhost:3000`, ห้าม `*` / `/` ท้าย / ว่าง) + `cors_allow_origin_regex` (default ว่าง = ปิด)
- [ ] 3. 🤖 `app/cors.py` → `add_cors(app, env)` · `main.py` เรียกตอนสร้าง app → green
- [ ] 4. 🤖 `.env.example` + ตาราง env ใน `docs/team/setup.md` A5
- [ ] 5. 🤖 ruff + pytest ทั้งหมด · CI เขียว
- [ ] 6. 🙋 ตอบ May ใน PR #42 (OQ5, OQ6, OQ7) หลัง Junior อนุมัติข้อความ

## Definition of done

- preflight จาก `http://localhost:3000` และ preview ที่ตรง regex ได้ `Access-Control-Allow-Origin` · origin อื่นไม่ได้
- `Authorization`, `Content-Type` ผ่าน preflight · methods GET/POST/PUT/DELETE · expose `X-Request-Id`, `X-Stub` · ไม่มี credentials
- origin มาจาก env ไม่ hard-code · มีใน `.env.example` และ `setup.md`
- test ผ่านทั้งหมด

## Decisions

- 2026-10-21 · regex `^https://anyang-[a-z0-9]{9}-anyang4\.vercel\.app$` · เพราะ URL preview จริง 8 อันจาก deployment ของ repo เป็น hash 9 ตัว a-z0-9 ทุกอัน · ไม่ใช้ `[a-z0-9-]+` เพราะ team อื่นที่ slug ลงท้าย `-anyang4` จะ match ได้ · branch alias (`anyang-git-<branch>-anyang4`) ไม่ match ตั้งใจ

## Next step

ขั้น 1: Junior review `tests/unit/test_cors.py`

## Waiting on

ไม่มี

## Notes for next time

- Starlette ตรวจ `allow_origin_regex` ด้วย `fullmatch`
- `X-Request-Id` ยังไม่มี middleware ที่ใส่ header นี้ (api.md Conventions บอกว่าทุก response ต้องมี) · CORS แค่ expose ไว้ให้พร้อม
