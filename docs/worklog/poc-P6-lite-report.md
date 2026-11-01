# PoC P6-lite: วัดผลและเขียน report (SaaS + CI/CD)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `poc/P6-lite-report` |
| Checklist item | เขียน report P6-lite ด้วย `/poc-report P6-lite` |
| Status | in progress · 2026-11-01 |

## Plan

- [x] 1. 🤖 ติ๊ก checklist "Cloud Build trigger: merge → deploy `api-staging` อัตโนมัติ (P6-lite)" ที่เสร็จใน PR #83 (28 ต.ค.) พร้อมหมายเหตุ
- [x] 2. 🙋 Jam `gcloud auth login` (บัญชีที่เป็น Owner ของ `anyang-513006`) · ใน terminal: `gcloud auth login` → browser เปิด → เลือกบัญชี → Allow → กลับมา terminal เห็น "You are now logged in as …" · แล้ว `gcloud config set project anyang-513006`
- [x] 3. 🤖 `poc/P6-lite/deploy_latency.py` + `README.md`: ทุก PR ที่ merge เข้า `main` หลังตั้ง trigger และแก้ path ที่ trigger ดู (`apps/api/**`, `config/**`, `prompts/**`, `infra/**`) → หา build ของ commit นั้น (`gcloud builds list`) → เวลาจาก merge ถึง build (deploy) เสร็จ · เช็คว่า image ที่ `api-staging` รันอยู่ = commit ล่าสุดที่ควร deploy · ผลลง `poc/P6-lite/results/deploy-latency.json` · รันซ้ำได้คำสั่งเดียว
- [x] 4. 🤖 เก็บหลักฐานข้อ isolation และ secret: run ของ CI job `api-integration` บน `main` (`test_SA06_*`) · GitHub secret scanning alerts (ตอนนี้ 0) · grep pattern ของ key ที่รู้จักทั้ง `git log -p` · Secret Manager ยังไม่มี secret เพราะ staging ใช้ fake (ไม่มีอะไรต้องเก็บ)
- [x] 5. 🤖 `/poc-report P6-lite` → `specs/poc/reports/P6-lite.md` + บรรทัด "ผล" ใน `specs/poc/README.md` §P6-lite
- [x] 6. 🙋 Jam review report · การตัดสิน PASS/FAIL ใช้เกณฑ์ใน spec · ข้อเสนอต่อ deploy (Cloud Build ต่อ หรือ fallback script) จดให้ Junior ยืนยัน
- [ ] 7. 🤖 `/work-done`

## Definition of done

- มี report `specs/poc/reports/P6-lite.md` ที่ตอบ 3 เกณฑ์ใน `specs/poc/README.md` P6-lite (staging อัปเดตเองภายใน 10 นาทีหลัง merge · isolation test ผ่านใน CI · ไม่มี secret ใน git history) พร้อมตัวเลขจริงและจำนวนตัวอย่าง
- ตัวเลขรันซ้ำได้ด้วยคำสั่งเดียวใน `poc/P6-lite/README.md`
- checklist ข้อ trigger และข้อ report ของ Junior ติ๊กพร้อมหมายเหตุ solo

## Decisions

- 2026-11-01 · Jam หยิบข้อนี้ช่วง solo (`/work-start ALL`) · trigger เสร็จแล้วตั้งแต่ #83 แต่ยังไม่มีใครวัดผล · ปิด PoC ของ S2 ก่อนเข้า S3

- 2026-11-01 · Jam review report P6-lite: ok · ผ่านครบ · ข้อเสนอ §4 (Cloud Build ต่อ) และ §5 (pin Supabase CLI ใน `ci.yml`) รอ Junior

## Next step

ขั้น 7: `/work-done` (ติ๊ก checklist ข้อ report P6-lite ของ Junior + หมายเหตุ solo)

## Waiting on

- Junior: ยืนยันการตัดสินใน report §4 (เรื่อง deploy เป็นของ Junior ตาม `roles.md`) · ตัดสินข้อเสนอ §5 pin version ของ `supabase/setup-cli` ใน `.github/workflows/ci.yml`

## Notes for next time

- 1 พ.ย. ผลขั้น 4: `api-integration` บน `main` 84/89 success · 5 failure เป็น CI ทั้งหมด ไม่ใช่ test: 1346e9b `toomanyrequests` (Docker Hub) · 543e2f5, ce93a93 `Data limit exceeded` (registry) · f195d25 `Failed to resolve latest Supabase CLI release: rate limit exceeded` · 861bfca port 54322 ถูกใช้อยู่ · secret: scanning + push protection enabled, alert 0, pattern 10 ตัว = 0 ใน 705 commit, ไฟล์ `.env`/key = 0, Secret Manager 0

- 1 พ.ย. ผลขั้น 3 (วัด 2026-11-01): merge 14 ครั้งตั้งแต่สร้าง trigger · ควร deploy 8 · deploy เองครบ 8 · 3.40–4.58 นาที (median 4.02) · staging รัน #95 (ล่าสุด) · ไม่มี build ที่ไม่ควรเกิด

- 1 พ.ย. gcloud login เป็น `jamsadog@gmail.com` + project `anyang-513006` แล้ว · ADC ของ Vertex แยกกับ `gcloud auth login`
