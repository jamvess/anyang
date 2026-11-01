# PoC P6-lite · SaaS + CI/CD

spec: `specs/poc/README.md` P6-lite · report: `specs/poc/reports/P6-lite.md` · trigger: `infra/trigger-api-staging.yaml` + `infra/cloudbuild.yaml` (`infra/README.md` "Deploy อัตโนมัติ")

## รัน

ต้องมี `gh` ที่ login แล้ว และ `gcloud` ที่ login ด้วยบัญชีที่ดู Cloud Build และ Cloud Run ของ `anyang-513006` ได้ (`gcloud auth login` แล้ว `gcloud config set project anyang-513006`) · อ่านอย่างเดียว ไม่ deploy และไม่แก้อะไร

```bash
cd apps/api
uv run python ../../poc/P6-lite/deploy_latency.py
uv run pytest ../../poc/P6-lite -q     # test ส่วนที่คิดตัวเลข
cd ../.. && bash poc/P6-lite/evidence.sh   # เกณฑ์ข้อ 2, 3 · เขียน results/evidence.txt เองเมื่อรันจบ
```

## วัดอะไร

ทุก PR ที่ merge เข้า `main` หลังวันที่สร้าง trigger `api-staging-deploy`:

| คอลัมน์ | มาจาก |
|---|---|
| `should_deploy` | ไฟล์ใน PR ตรงกับ `includedFiles` ของ trigger (`apps/api/**`, `config/**`, `prompts/**`, `infra/**`) · ใช้ `fnmatch` ซึ่งตรงกับ Cloud Build สำหรับ glob แบบ `<folder>/**` เท่านั้น · `gh` ส่งรายชื่อไฟล์ได้ไม่เกิน 100 ไฟล์ต่อ PR |
| `build_status` | build ของ merge commit (`gcloud builds list --filter=buildTriggerId=...`) · commit เดียวกันที่มีหลาย build ใช้ตัวแรกที่ SUCCESS (ตอนที่ staging เปลี่ยน) ถ้าไม่มีใช้ตัวล่าสุด |
| `minutes_to_deployed` | `mergedAt` ของ PR (gh) ถึง `finishTime` ของ build · ขั้นสุดท้ายของ build คือ `gcloud run deploy` ซึ่งจบเมื่อ revision ใหม่รับ traffic แล้ว |
| `revision`, `revision_created_at` | revision แรกของ `api-staging` ที่สร้างจาก image digest ของ build นั้น (revision ที่ตามมาด้วย image เดิม เช่น `services update --min-instances` คือการเปลี่ยน setting ไม่ใช่ deploy) |
| `within_target` | `minutes_to_deployed` ≤ 10 (เกณฑ์ของ P6-lite) · `null` ถ้า PR นั้นไม่ควร deploy |

`summary.serving_newest_deploy` เช็คว่า revision ที่รับ traffic อยู่ตอนวัด รัน image ของ PR ล่าสุดที่ควร deploy

ผลอยู่ที่ `results/deploy-latency.json` (commit ได้ · มีแค่เลข PR, ชื่อ PR, commit, build id และเวลา)

## เกณฑ์ข้อ 2, 3 (`evidence.sh`)

- **isolation test ใน CI:** ผลของ job `api-integration` (รัน `tests/integration` ซึ่งมี `test_SA06_*`) ในทุก run ของ `ci.yml` ที่ push เข้า `main` · run ที่ไม่ผ่านต้องเปิด log ดูเองว่าล้มเพราะ test หรือเพราะ CI (`gh run view <id> --log-failed`)
- **secret:** สถานะ GitHub secret scanning + push protection + จำนวน alert ที่ยังเปิด · นับ pattern ของ key ที่รู้จักใน `git log -p --all` ยกเว้น `evidence.sh` เอง (พิมพ์แค่จำนวน ไม่พิมพ์ข้อความที่เจอ · ไฟล์ dump ชั่วคราวถูกลบเสมอแม้ script ล้ม) · ไฟล์ `.env*` หรือ key file ที่เคยถูก add · จำนวน secret ใน Secret Manager
- ผลอยู่ที่ `results/evidence.txt`
