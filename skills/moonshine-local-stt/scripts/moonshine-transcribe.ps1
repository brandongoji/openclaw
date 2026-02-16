param(
  [ValidateSet('tiny','base')]
  [string]$Model = 'tiny',

  [string]$Language = 'en',

  [int]$MaxSeconds = 20,
  [int]$CooldownMs = 1000
)

$ErrorActionPreference = 'Stop'

# Moonshine-voice model arch mapping
$modelArch = if ($Model -eq 'base') { 1 } else { 0 }

Write-Host "[moonshine-local-stt] Starting mic transcriber: model=$Model arch=$modelArch lang=$Language"
Write-Host "[moonshine-local-stt] Safety: maxSeconds=$MaxSeconds cooldownMs=$CooldownMs"
Write-Host "[moonshine-local-stt] Press Ctrl+C to stop."

# Run moonshine mic transcriber in a child process so we can enforce timeout.
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'python'
$psi.Arguments = "-m moonshine_voice.mic_transcriber --language $Language --model-arch $modelArch"
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
$psi.UseShellExecute = $true

$proc = [System.Diagnostics.Process]::Start($psi)
if (-not $proc) {
  throw 'Failed to launch moonshine mic transcriber.'
}

$deadline = (Get-Date).AddSeconds($MaxSeconds)
while (-not $proc.HasExited -and (Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 250
}

if (-not $proc.HasExited) {
  Write-Host "[moonshine-local-stt] MaxSeconds reached; stopping process for safety." -ForegroundColor Yellow
  try { $proc.Kill() } catch {}
}

Start-Sleep -Milliseconds $CooldownMs
Write-Host "[moonshine-local-stt] Complete."
