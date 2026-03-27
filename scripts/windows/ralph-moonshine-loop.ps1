param(
  [string]$RepoRoot = "C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw",
  [int]$Port = 18789,
  [int]$RestartDelaySeconds = 2
)

$ErrorActionPreference = 'Stop'

$nodeExe = "C:\Program Files\nodejs\node.exe"
$entry = Join-Path $RepoRoot "dist\entry.js"

if (-not (Test-Path $nodeExe)) { throw "node.exe not found: $nodeExe" }
if (-not (Test-Path $entry)) { throw "dist entry missing: $entry (run build first)" }

Write-Host "[ralph-loop] Starting crash-resistant moonshine loop on port $Port" -ForegroundColor Cyan
Write-Host "[ralph-loop] Repo: $RepoRoot"

while ($true) {
  try {
    $existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
      Select-Object -First 1 -ExpandProperty OwningProcess
    if ($existing) {
      Write-Host "[ralph-loop] Stopping existing listener pid=$existing" -ForegroundColor Yellow
      Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
      Start-Sleep -Seconds 1
    }
  } catch {
    # ignore stale connection errors
  }

  Write-Host "[ralph-loop] Launching gateway..." -ForegroundColor Green
  & $nodeExe $entry gateway run --bind loopback --port $Port --force --allow-unconfigured --verbose
  $exitCode = $LASTEXITCODE

  Write-Host "[ralph-loop] Gateway exited with code $exitCode. Restarting in $RestartDelaySeconds sec..." -ForegroundColor Red
  Start-Sleep -Seconds $RestartDelaySeconds
}
