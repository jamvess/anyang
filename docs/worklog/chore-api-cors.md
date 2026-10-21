# CORS ใน FastAPI ให้หน้าเว็บเรียก API ได้

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/api-cors` |
| Checklist item | ไม่มีข้อตรงๆ · งานที่ May ขอ (room-http.md Open question 6 ทาง ก) เพื่อให้ "หน้าแชทของ May คุยกับ Gemini ผ่าน staging ได้" (Done ของ S3) |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 test `tests/unit/test_cors.py` จาก requirement ของ May → red · Junior review test แล้ว ok (แก้ regex เป็น `+` + เพิ่มกรณี hash 8 ตัว)
- [x] 2. 🤖 `EnvSettings.cors_allow_origins` (comma-separated, default `http://localhost:3000`, ห้าม `*` / `/` ท้าย / ว่าง) + `cors_allow_origin_regex` (default ว่าง = ปิด · ตรวจว่า compile ได้)
- [x] 3. 🤖 `app/cors.py` → `add_cors(app, env)` · `main.py` เรียกตอนสร้าง app → green
- [x] 4. 🤖 `.env.example` + ตาราง env ใน `docs/team/setup.md` A5
- [ ] 5. 🤖 ruff + pytest ทั้งหมดในเครื่องผ่านแล้ว (156) · รอ CI เขียวบน PR #49
- [x] 6. 🙋 ตอบ May ใน PR #42 (OQ5, OQ6, OQ7) + comment #40 (`exam_prep_not_found`) + เปิด issue #50 (X-Request-Id middleware)

## Definition of done

- preflight จาก `http://localhost:3000` และ preview ที่ตรง regex ได้ `Access-Control-Allow-Origin` · origin อื่นไม่ได้
- `Authorization`, `Content-Type` ผ่าน preflight · methods GET/POST/PUT/DELETE · expose `X-Request-Id`, `X-Stub` · ไม่มี credentials
- origin มาจาก env ไม่ hard-code · มีใน `.env.example` และ `setup.md`
- test ผ่านทั้งหมด

## Decisions

- 2026-10-21 · (Junior) regex `^https://anyang-[a-z0-9]+-anyang4\.vercel\.app$` · hash ไม่มี `-` จึงกัน team อื่นที่ slug ลงท้าย `-anyang4` ได้อยู่แล้ว (เช่น `anyang-abc-evil-anyang4`) และไม่พังถ้า Vercel เปลี่ยนความยาว hash (URL จริงตอนนี้เป็น 9 ตัว) · มี test hash 8 ตัวที่ต้องผ่าน · branch alias (`anyang-git-<branch>-anyang4`) ไม่ match
- 2026-10-21 · (Junior) ชื่อ test ใช้ `test_roomhttp_cors_*` เพราะที่มาคือ room-http.md OQ6 · ข้อความ CORS ใน api.md Conventions ไปรวมกับ PR api.md ข้อ 5
- 2026-10-21 · (Junior) `CORS_ALLOW_ORIGINS=""` ให้พังตอน boot · `X-Request-Id` middleware แยกเป็น issue

## Next step

ครบทุกขั้นแล้ว · รัน `/work-done` · เรื่อง env ของ staging ย้ายไปอยู่ใน `sprint-checklists.md` ใต้ข้อ Cloud Build (P6-lite) แล้ว · 500 ที่หลุด CORS อยู่ใน issue #50

## Waiting on

ไม่มี

## Notes for next time

- Starlette ตรวจ `allow_origin_regex` ด้วย `fullmatch`
- `X-Request-Id` ยังไม่มี middleware ที่ใส่ header นี้ (api.md Conventions บอกว่าทุก response ต้องมี) · CORS แค่ expose ไว้ให้พร้อม
