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

echo [CrashTrace] Python 3 was not found. Please install Python 3 or use CrashTraceViewer.exe.
exit /b 1
