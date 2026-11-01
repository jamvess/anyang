#!/usr/bin/env bash
# PoC P6-lite criteria 2 and 3 (specs/poc/README.md): isolation test in CI, no secret in git.
#   bash poc/P6-lite/evidence.sh > poc/P6-lite/results/evidence.txt
# Needs gh (logged in, repo admin for the secret scanning API) and gcloud (project anyang-513006).
# Read only. The history scan prints counts, never the matching text.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "measured_at $(date -Iseconds)"
echo
echo "## 2 · api-integration job (tests/integration, includes test_SA06_*) on every push to main"
for id in $(gh run list --workflow ci.yml --branch main --limit 500 --json databaseId,event \
  --jq '.[] | select(.event=="push") | .databaseId'); do
  gh run view "$id" --json jobs,createdAt,headSha \
    --jq '"\(.createdAt) \(.headSha[0:7]) " + ([.jobs[] | select(.name=="api-integration") | .conclusion] | join(","))'
done > "${TMPDIR:-/tmp}/p6_runs.txt"
echo "runs: $(wc -l < "${TMPDIR:-/tmp}/p6_runs.txt") · first: $(tail -1 "${TMPDIR:-/tmp}/p6_runs.txt" | cut -d' ' -f1)"
awk '{print $3}' "${TMPDIR:-/tmp}/p6_runs.txt" | sort | uniq -c
echo "not success (read the log with: gh run list --workflow ci.yml --branch main, then gh run view <id> --log-failed):"
grep -v " success$" "${TMPDIR:-/tmp}/p6_runs.txt" || echo "none"
rm -f "${TMPDIR:-/tmp}/p6_runs.txt"

echo
echo "## 3 · secrets"
echo "github secret scanning: $(gh api repos/{owner}/{repo} --jq '.security_and_analysis.secret_scanning.status') · push protection: $(gh api repos/{owner}/{repo} --jq '.security_and_analysis.secret_scanning_push_protection.status') · open alerts: $(gh api repos/{owner}/{repo}/secret-scanning/alerts --jq 'length')"
echo "commits scanned (all refs): $(git rev-list --all | wc -l)"
history="${TMPDIR:-/tmp}/p6_hist.txt"
git log -p --all --no-color > "$history"
while IFS='|' read -r name pattern; do
  echo "pattern $name: $(grep -cE -- "$pattern" "$history" || true)"
done <<'PATTERNS'
google_api_key|AIza[0-9A-Za-z_-]{35}
anthropic_key|sk-ant-[A-Za-z0-9_-]{20,}
openai_key|sk-[A-Za-z0-9]{32,}
private_key_pem|-----BEGIN [A-Z ]*PRIVATE KEY-----
gcp_service_account_json|"private_key_id"
supabase_secret_key|sb_secret_[A-Za-z0-9_-]{10,}
supabase_publishable_key|sb_publishable_[A-Za-z0-9_-]{10,}
jwt|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}
github_token|gh[pousr]_[A-Za-z0-9]{36}
mathpix_key|app_key["' :=]+[A-Za-z0-9]{20,}
PATTERNS
rm -f "$history"
echo "env or key files ever added: $(git log --all --format= --name-only --diff-filter=A \
  | grep -E '(^|/)\.env($|\.)|\.json\.key$|service-account.*\.json$' | grep -vc '\.env\.example$' || true)"
echo "secret manager secrets: $(gcloud secrets list --format='value(name)' | wc -l)"
