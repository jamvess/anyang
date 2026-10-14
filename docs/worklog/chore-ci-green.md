# CI เขียวครบบน main + ปิด S1 ข้อที่เสร็จแล้ว

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/ci-green` |
| Checklist item | GitHub Actions รันครบ (Prompt 4) |
| Status | paused · 2026-10-14 |

## Plan

- [x] 1. 🤖 เทียบ `.github/workflows/ci.yml` กับ app ที่ scaffold แล้ว และรันทุกคำสั่งของ job `api`, `api-integration`, `web` บนเครื่อง แก้คำสั่งที่พัง
- [x] 2. 🙋 ดูผล CI บน GitHub: เปิด https://github.com/jamvess/anyang/actions → workflow `ci` → run ล่าสุดของ `main` ต้องเขียวทั้ง 3 job (`api`, `api-integration`, `web`) ถ้ามี job แดง copy log ส่วนที่แดงมาให้ Claude
- [ ] 3. 🙋 ตั้ง/เช็ก branch protection: https://github.com/jamvess/anyang/settings/branches → Add rule (หรือ Edit ของ `main`) → Branch name pattern `main` → ติ๊ก "Require a pull request before merging" + "Require approvals: 1" → ติ๊ก "Require status checks to pass" แล้วค้นหาเพิ่ม `api`, `api-integration`, `web` → Save
- [ ] 4. 🤖 ติ๊ก checklist S1 ใน `docs/team/sprint-checklists.md`: ⭐ 3 ข้อที่ merge แล้ว + ข้อ GitHub Actions
- [ ] 5. 🤖 ปิดงาน: อัปเดต worklog, ให้พร้อม `/work-done`

## Definition of done

- CI เขียวบน `main` ทั้ง 3 job (เงื่อนไข "Done เมื่อ" ของ S1)
- `main` มี branch protection: ต้องผ่าน PR, review 1 คน, CI ผ่าน (`setup.md` §4.1)
- checklist S1 ของ Junior ติ๊กตรงกับความจริง

## Decisions

- 2026-10-14 · ไม่ทำ PR "chore: scaffold apps" ตาม Prompt 4 แยก · scaffold merge ไปแล้วใน PR #1–#3
- 2026-10-14 · ข้อ 1 ไม่ต้องแก้ `ci.yml` · ทุกคำสั่งของ job `api` และ `web` ผ่านบนเครื่อง ส่วน `api-integration` รันบนเครื่องไม่ได้เพราะ Docker ไม่ได้เปิด จึงใช้ผลจาก CI แทน (3 passed)
- 2026-10-14 · ข้อ 2 เช็กด้วย `gh run view` แทนการเปิดเว็บ · run 38520144020 บน `main` เขียวครบ 3 job
- 2026-10-14 · ยังไม่อัปเกรด action ที่ใช้ Node 20 (checkout@v4, setup-uv@v5, setup-cli@v1) · ตอนนี้ยังเป็นแค่ warning ทำแยกเป็นงานเล็กทีหลังได้

## Done today

- 2026-10-14 · รันทุกคำสั่งของ CI บนเครื่องแล้ว ผ่านหมด ไม่ต้องแก้ `ci.yml` (ข้อ 1)
- 2026-10-14 · เช็ก CI บน `main` ด้วย `gh run view 38520144020` แล้ว เขียวครบ 3 job (ข้อ 2)
- 2026-10-14 · ลองตั้ง branch protection แล้วติด 2 เรื่อง: (1) account `jnmonsicha2000` ไม่ใช่ admin (มีแค่ push) (2) repo private บน account free ใช้ไม่ได้ API ตอบ 403 "Upgrade to GitHub Pro or make this repository public"

## Next step

ทีมต้องเลือกก่อนว่าจะปิดงานนี้ทางไหน แล้วค่อยทำต่อ:
1. (แนะนำ) แยก branch protection ออกจากงานนี้ ย้ายข้อ 3 ไปไว้ใน Waiting on แล้วตัดออกจาก Definition of done จากนั้นทำข้อ 4 ใน `docs/team/sprint-checklists.md`
   - ติ๊ก "GitHub Actions รันครบ", ⭐ scaffold `apps/api` และ ⭐ `supabase init`
   - ⭐ "สร้าง repo…" ยังไม่ติ๊ก ให้เพิ่ม sub-bullet ว่า "repo + starter files เสร็จ · branch protection รอ GitHub Pro"
   - แล้วรัน `/work-done`
2. รอให้ `jamvess` ได้ GitHub Pro (Student Pack) แล้วตั้ง protection ก่อน ค่อยปิดทั้งหมดในครั้งเดียว
3. เปลี่ยน repo เป็น public (ถามทีม/อาจารย์ก่อน และเช็ก secret ใน history ก่อน)

## Waiting on

- 🙋 เจ้าของ repo `jamvess`: สมัคร GitHub Student Developer Pack ที่ https://education.github.com/pack ด้วยอีเมล @kmutt.ac.th เพื่อได้ Pro
  - จากนั้นเปิด https://github.com/jamvess/anyang/settings/branches → Add classic branch protection rule → pattern `main`
  - ติ๊ก Require a pull request (approvals 1) และ Require status checks: `api`, `api-integration`, `web` แล้วกด Create
- 🙋 ทีม: เลือกทาง 1 / 2 / 3 ใน Next step

## Notes for next time

- เครื่อง Junior มี `gh` CLI แล้ว (14 ต.ค.) แต่ login เป็น `jnmonsicha2000` ซึ่งไม่ใช่ admin ของ repo
- เช็ก protection ได้ด้วย `gh api repos/jamvess/anyang/branches/main/protection` ถ้าได้ 404 แปลว่ายังไม่ได้ตั้ง (หรือไม่มีสิทธิ์ดู)
- Docker Desktop ต้องเปิดก่อน ถ้าจะรัน `supabase start` บนเครื่อง
- CI มี warning: action ที่ใช้ Node 20 (`checkout@v4`, `setup-uv@v5`, `setup-cli@v1`) และ `ubuntu-latest` จะเปลี่ยนเป็น Ubuntu 26 ตั้งแต่ 19 ต.ค. ถ้า `api-integration` พังหลังวันนั้น ให้ลองล็อก `runs-on: ubuntu-24.04`
