<#
.SYNOPSIS
  Builds the frontend and ships a release to the AWS server.

.DESCRIPTION
  The server never installs Node: the SPA is built here and the bundle is
  uploaded together with the backend sources and the infra files.

.EXAMPLE
  ./infra/scripts/deploy.ps1 -Host 54.1.2.3
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [string]$User = 'ubuntu',
    [string]$IdentityFile = "$env:USERPROFILE\.ssh\migmusic-key.pem",
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

if (-not $SkipBuild) {
    Write-Host '==> Building the frontend'
    Push-Location (Join-Path $repoRoot 'frontend')
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'npm run build failed' }
    }
    finally { Pop-Location }
}

$stage = Join-Path $env:TEMP ("migmusic-deploy-" + (Get-Date -Format 'yyyyMMddHHmmss'))
New-Item -ItemType Directory -Path $stage | Out-Null
$tgz = Join-Path $stage 'migmusic-deploy.tgz'

Write-Host '==> Packaging the release'
$paths = @(
    'backend/src', 'backend/pyproject.toml', 'backend/uv.lock',
    'infra',
    'frontend/dist'
)
tar.exe -czf $tgz -C $repoRoot --exclude=__pycache__ --exclude='*.pyc' --exclude=.venv @paths
if ($LASTEXITCODE -ne 0) { throw 'tar failed' }
"{0:N1} MB" -f ((Get-Item $tgz).Length / 1MB)

Write-Host "==> Uploading to ${User}@${Target}"
scp -i $IdentityFile -o StrictHostKeyChecking=accept-new $tgz "${User}@${Target}:/tmp/migmusic-deploy.tgz"
if ($LASTEXITCODE -ne 0) { throw 'scp failed' }

Write-Host '==> Extracting and applying'
$remote = @(
    'set -euo pipefail',
    'sudo install -d -m 0755 /opt/migmusic',
    'sudo tar -xzf /tmp/migmusic-deploy.tgz -C /opt/migmusic',
    'sudo bash /opt/migmusic/infra/scripts/apply-deploy.sh'
) -join '; '
ssh -i $IdentityFile -o StrictHostKeyChecking=accept-new "${User}@${Target}" $remote
if ($LASTEXITCODE -ne 0) { throw 'remote apply failed' }

Remove-Item -Recurse -Force $stage
Write-Host '==> Deploy finished'
