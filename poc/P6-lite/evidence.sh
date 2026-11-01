#!/usr/bin/env bash
# PoC P6-lite criteria 2 and 3 (specs/poc/README.md): isolation test in CI, no secret in git.
#   bash poc/P6-lite/evidence.sh        # writes poc/P6-lite/results/evidence.txt
# Needs gh (logged in, repo admin for the secret scanning API) and gcloud (project anyang-513006).
# Read only. The history scan prints counts, never the matching text.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

out=poc/P6-lite/results/evidence.txt
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT # the history dump holds every patch; never leave it behind

{
echo "measured_at $(date -Iseconds)"
echo
echo "## 2 · api-integration job (tests/integration, includes test_SA06_*) on every push to main"
for id in $(gh run list --workflow ci.yml --branch main --limit 500 --json databaseId,event \
  --jq '.[] | select(.event=="push") | .databaseId'); do
  gh run view "$id" --json jobs,createdAt,headSha \
    --jq '"\(.createdAt) \(.headSha[0:7]) " + ([.jobs[] | select(.name=="api-integration") | .conclusion] | join(","))'
done > "$work/runs.txt"
echo "runs: $(wc -l < "$work/runs.txt") · first: $(tail -1 "$work/runs.txt" | cut -d' ' -f1)"
awk '{print $3}' "$work/runs.txt" | sort | uniq -c
echo "not success (read the log with: gh run list --workflow ci.yml --branch main, then gh run view <id> --log-failed):"
grep -v " success$" "$work/runs.txt" || echo "none"

echo
echo "## 3 · secrets"
echo "github secret scanning: $(gh api repos/{owner}/{repo} --jq '.security_and_analysis.secret_scanning.status') · push protection: $(gh api repos/{owner}/{repo} --jq '.security_and_analysis.secret_scanning_push_protection.status') · open alerts: $(gh api --paginate 'repos/{owner}/{repo}/secret-scanning/alerts?state=open' --jq '.[].number' | wc -l)"
echo "commits scanned (all refs): $(git rev-list --all | wc -l)"
# This script holds the patterns as text, so it is left out of the scan.
git log -p --all --no-color -- . ':(exclude)poc/P6-lite/evidence.sh' > "$work/history.txt"
while IFS='|' read -r name pattern; do
  echo "pattern $name: $(grep -cE -- "$pattern" "$work/history.txt" || true)"
done <<'PATTERNS'
google_api_key|AIza[0-9A-Za-z_-]{35}
anthropic_key|sk-ant-[A-Za-z0-9_-]{20,}
openai_key|sk-(proj|svcacct|admin)-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,}
private_key_pem|-----BEGIN [A-Z ]*PRIVATE KEY-----
gcp_service_account_json|"private_key_id"
supabase_secret_key|sb_secret_[A-Za-z0-9_-]{10,}
supabase_publishable_key|sb_publishable_[A-Za-z0-9_-]{10,}
jwt|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}
github_token|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}
mathpix_key|app_key["' :=]+[A-Za-z0-9]{20,}
PATTERNS
echo "env or key files ever added: $(git log --all --format= --name-only --diff-filter=A \
  | grep -E '(^|/)\.env($|\.)|\.json\.key$|service-account.*\.json$' | grep -vc '\.env\.example$' || true)"
echo "secret manager secrets: $(gcloud secrets list --format='value(name)' | wc -l)"
} > "$work/evidence.txt"

# Replace the committed file only after every check above finished.
mv "$work/evidence.txt" "$out"
cat "$out"
