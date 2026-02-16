@echo off
setlocal

set "NODE_EXE=C:\Program Files\nodejs\node.exe"
set "OPENCLAW_MJS=C:\Vibe Coding DO NOT DELETE\OpenClaw\openclaw\openclaw.mjs"

if not exist "%NODE_EXE%" (
  echo [ERROR] node.exe not found at: %NODE_EXE%
  exit /b 1
)

if not exist "%OPENCLAW_MJS%" (
  echo [ERROR] openclaw.mjs not found at: %OPENCLAW_MJS%
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Start-Process -WindowStyle Hidden -FilePath '%NODE_EXE%' -ArgumentList '--disable-warning=ExperimentalWarning ""%OPENCLAW_MJS%"" gateway run --bind loopback --port 18789 --force'"

exit /b %errorlevel%
