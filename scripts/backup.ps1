$ErrorActionPreference = 'Stop'
$backupDir = Join-Path $PSScriptRoot '..\backups'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$target = Join-Path $backupDir "gpxaccess-$stamp.sql"
docker compose exec -T db pg_dump -U gpxaccess -d gpxaccess | Set-Content -Encoding utf8 -LiteralPath $target
if (-not (Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -eq 0) { throw 'Sauvegarde vide' }
Write-Output "Sauvegarde créée : $target"

