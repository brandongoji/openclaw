@echo off
setlocal

for /f "tokens=2 delims=," %%P in ('tasklist /fo csv /nh ^| findstr /i "node.exe"') do (
  wmic process where "ProcessId=%%~P and CommandLine like '%%openclaw.mjs%%gateway run%%'" call terminate >nul 2>nul
)

echo Requested stop for OpenClaw gateway node processes.
exit /b 0
