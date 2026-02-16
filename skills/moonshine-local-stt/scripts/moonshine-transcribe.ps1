param(
  [Parameter(Mandatory = $true)]
  [string]$InputFile,

  [ValidateSet('tiny','base')]
  [string]$Model = 'tiny',

  [int]$MaxSeconds = 20,
  [int]$CooldownMs = 1000,
  [string]$OutFile = ''
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $InputFile)) {
  throw "Input file not found: $InputFile"
}

if ([string]::IsNullOrWhiteSpace($OutFile)) {
  $OutFile = "$InputFile.moonshine.txt"
}

$moonshineBin = if ($env:MOONSHINE_BIN) { $env:MOONSHINE_BIN } else { 'moonshine' }

$cmd = Get-Command $moonshineBin -ErrorAction SilentlyContinue
if (-not $cmd) {
  Write-Host "[moonshine-local-stt] Moonshine binary not found: '$moonshineBin'" -ForegroundColor Yellow
  Write-Host "Set MOONSHINE_BIN to your executable path, or install Moonshine CLI/runtime first." -ForegroundColor Yellow
  exit 2
}

# Conservative defaults to reduce CPU/RAM spikes.
# The wrapper passes generic flags used by most Moonshine CLIs.
# If your local binary uses different flags, set MOONSHINE_EXTRA_ARGS.
$args = @(
  'transcribe',
  '--input', $InputFile,
  '--model', $Model,
  '--max-seconds', $MaxSeconds,
  '--workers', '1',
  '--output', $OutFile
)

if ($env:MOONSHINE_EXTRA_ARGS) {
  $args += $env:MOONSHINE_EXTRA_ARGS -split ' '
}

Write-Host "[moonshine-local-stt] Running: $moonshineBin $($args -join ' ')"
& $moonshineBin @args

if ($LASTEXITCODE -ne 0) {
  throw "Moonshine transcribe failed with exit code $LASTEXITCODE"
}

Start-Sleep -Milliseconds $CooldownMs
Write-Host "[moonshine-local-stt] Done. Transcript: $OutFile"
