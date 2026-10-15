# CI เขียวครบบน main + ปิด S1 ข้อที่เสร็จแล้ว

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/ci-green` |
| Checklist item | GitHub Actions รันครบ (Prompt 4) |
| Status | in progress · 2026-10-15 |

## Plan

- [x] 1. 🤖 เทียบ `.github/workflows/ci.yml` กับ app ที่ scaffold แล้ว และรันทุกคำสั่งของ job `api`, `api-integration`, `web` บนเครื่อง แก้คำสั่งที่พัง
- [x] 2. 🙋 ดูผล CI บน GitHub: เปิด https://github.com/jamvess/anyang/actions → workflow `ci` → run ล่าสุดของ `main` ต้องเขียวทั้ง 3 job (`api`, `api-integration`, `web`) ถ้ามี job แดง copy log ส่วนที่แดงมาให้ Claude
- [x] 3. 🙋 ตั้ง/เช็ก branch protection ของ `main` · Jam (admin) ตั้งเป็น ruleset 25137368 · เช็กด้วย `gh api` แล้ว: active, target default branch, require PR + 1 approval, status checks `api`, `api-integration`, `web`
- [x] 4. 🤖 ติ๊ก checklist S1 ใน `docs/team/sprint-checklists.md`: ⭐ 3 ข้อที่ merge แล้ว + ข้อ GitHub Actions · ทำแล้วใน PR #6
- [x] 5. 🤖 ปิดงาน: อัปเดต worklog, ให้พร้อม `/work-done`

## Definition of done

- CI เขียวบน `main` ทั้ง 3 job (เงื่อนไข "Done เมื่อ" ของ S1)
- `main` มี branch protection: ต้องผ่าน PR, review 1 คน, CI ผ่าน (`setup.md` §4.1)
- checklist S1 ของ Junior ติ๊กตรงกับความจริง

## Decisions

- 2026-10-14 · ไม่ทำ PR "chore: scaffold apps" ตาม Prompt 4 แยก · scaffold merge ไปแล้วใน PR #1–#3
- 2026-10-14 · ข้อ 1 ไม่ต้องแก้ `ci.yml` · ทุกคำสั่งของ job `api` และ `web` ผ่านบนเครื่อง ส่วน `api-integration` รันบนเครื่องไม่ได้เพราะ Docker ไม่ได้เปิด จึงใช้ผลจาก CI แทน (3 passed)
- 2026-10-14 · ข้อ 2 เช็กด้วย `gh run view` แทนการเปิดเว็บ · run 38520144020 บน `main` เขียวครบ 3 job
- 2026-10-14 · ยังไม่อัปเกรด action ที่ใช้ Node 20 (checkout@v4, setup-uv@v5, setup-cli@v1) · ตอนนี้ยังเป็นแค่ warning ทำแยกเป็นงานเล็กทีหลังได้
- 2026-10-15 · repo made public so branch protection is available · Jam (admin) set ruleset 25137368 per setup.md §4

## Done today

- 2026-10-14 · รันทุกคำสั่งของ CI บนเครื่องแล้ว ผ่านหมด ไม่ต้องแก้ `ci.yml` (ข้อ 1)
- 2026-10-14 · เช็ก CI บน `main` ด้วย `gh run view 38520144020` แล้ว เขียวครบ 3 job (ข้อ 2)
- 2026-10-14 · ลองตั้ง branch protection แล้วติด 2 เรื่อง: (1) account `jnmonsicha2000` ไม่ใช่ admin (มีแค่ push) (2) repo private บน account free ใช้ไม่ได้ API ตอบ 403 "Upgrade to GitHub Pro or make this repository public"
- 2026-10-15 · สแกน secret ใน git history ทุก branch (ชื่อไฟล์ + เนื้อหา + รูปแบบ key จริง) ไม่เจอ secret จริง เจอแค่รหัส default ของ Supabase local (`postgres:postgres@127.0.0.1`) ใน `.env.example` · `.gitignore` ครอบ `.env*` ครบ
- 2026-10-15 · เช็ก ruleset 25137368 ด้วย `gh api repos/jamvess/anyang/rules/branches/main` และ `rulesets/25137368` ผ่านครบ · `.protected` = `true` (ข้อ 3)

## Next step

พิมพ์ `/work-done` เพื่อเปิด PR ปิดงานนี้

## Waiting on

- 🙋 Jam: ยืนยัน secret scanning + push protection เปิดแล้ว (screenshot หน้า https://github.com/jamvess/anyang/settings/security_analysis ในแชทกลุ่ม) · account ที่ไม่ใช่ admin เช็กผ่าน `gh api` ไม่ได้

## Notes for next time

- เครื่อง Junior มี `gh` CLI แล้ว (14 ต.ค.) แต่ login เป็น `jnmonsicha2000` ซึ่งไม่ใช่ admin ของ repo
- protection ของ `main` เป็น ruleset (ไม่ใช่ classic) เช็กด้วย `gh api repos/jamvess/anyang/rules/branches/main` · endpoint `branches/main/protection` จะได้ 404 เสมอ
- Docker Desktop ต้องเปิดก่อน ถ้าจะรัน `supabase start` บนเครื่อง
- CI มี warning: action ที่ใช้ Node 20 (`checkout@v4`, `setup-uv@v5`, `setup-cli@v1`) และ `ubuntu-latest` จะเปลี่ยนเป็น Ubuntu 26 ตั้งแต่ 19 ต.ค. ถ้า `api-integration` พังหลังวันนั้น ให้ลองล็อก `runs-on: ubuntu-24.04`
