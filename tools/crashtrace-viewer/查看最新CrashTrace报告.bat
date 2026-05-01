@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "OUTPUT_FILE=%SCRIPT_DIR%latest_crashtrace_report.txt"

call :run_viewer
exit /b %ERRORLEVEL%

:run_viewer
py -3 "%SCRIPT_DIR%view_crashtrace_report.py" --output "%OUTPUT_FILE%" --open-output >nul 2>&1
if not errorlevel 9009 exit /b %ERRORLEVEL%

python "%SCRIPT_DIR%view_crashtrace_report.py" --output "%OUTPUT_FILE%" --open-output >nul 2>&1
if not errorlevel 9009 exit /b %ERRORLEVEL%

echo [CrashTrace] 未找到 Python 3，请先安装 Python 3，或直接使用 CrashTraceViewer.exe。
exit /b 1
