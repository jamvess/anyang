# Manual deploy of apps/api to Cloud Run api-staging (P6-lite fallback until the merge trigger exists).
# Builds the image with Cloud Build (no local Docker needed), then deploys it.
#
#   powershell -ExecutionPolicy Bypass -File infra\deploy-staging.ps1

$ErrorActionPreference = 'Stop'

$Project = 'anyang-513006'
$Region  = 'asia-southeast1'
$Service = 'api-staging'
$Root    = Split-Path -Parent $PSScriptRoot

# Tag the image with the commit; mark it when the working tree has uncommitted changes.
$Tag = git -C $Root rev-parse --short HEAD
if (git -C $Root status --porcelain) { $Tag = "$Tag-dirty-$(Get-Date -Format yyyyMMddHHmmss)" }
$Image = "$Region-docker.pkg.dev/$Project/anyang/api:$Tag"

function Invoke-Gcloud {
    gcloud @args
    if ($LASTEXITCODE -ne 0) { throw "gcloud $($args[0]) $($args[1]) failed (exit $LASTEXITCODE)" }
}

Write-Host "Building $Image"
Invoke-Gcloud builds submit $Root `
    --project=$Project `
    --region=$Region `
    --config="$Root\infra\cloudbuild-image.yaml" `
    --substitutions="_IMAGE=$Image"

Write-Host "Deploying $Service"
Invoke-Gcloud run deploy $Service `
    --project=$Project `
    --region=$Region `
    --image=$Image `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=2 `
    --concurrency=40 `
    --timeout=600 `
    --env-vars-file="$Root\infra\env\api-staging.yaml"

$Url = gcloud run services describe $Service --project=$Project --region=$Region --format='value(status.url)'
Write-Host "api-staging: $Url"
Write-Host "check: $Url/health"
