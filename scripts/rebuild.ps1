# Rebuild Script for VivaCampo
# This script rebuilds containers and cleans up dangling images to keep your environment clean.

param (
    [string[]]$Services = $null,
    [switch]$NoCache
)

$ErrorActionPreference = "Stop"

Write-Host "🏗️  Starting Build Process..." -ForegroundColor Cyan

$composeArgs = @("up", "-d", "--build")

if ($NoCache) {
    Write-Host "🚫 No-Cache mode enabled" -ForegroundColor Yellow
    # Note: --no-cache is a build option, so we need to run build separately if we want to be precise,
    # or pass it if compose supports it (newer versions do as 'docker compose build --no-cache')
    docker compose build --no-cache $Services
    docker compose up -d $Services
} else {
    docker compose up -d --build $Services
}

Write-Host "✅ Build Complete!" -ForegroundColor Green

Write-Host "🧹 Cleaning up dangling images (<none>)..." -ForegroundColor Cyan
$dangling = docker images -f "dangling=true" -q

if ($dangling) {
    docker rmi $dangling
    Write-Host "✨ Cleanup Complete! Removed $($dangling.Count) dangling images." -ForegroundColor Green
} else {
    Write-Host "✨ No dangling images to clean." -ForegroundColor Green
}
