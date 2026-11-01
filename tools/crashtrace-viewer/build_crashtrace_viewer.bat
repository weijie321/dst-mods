@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SPEC_FILE=%SCRIPT_DIR%CrashTraceViewer.spec"
set "DIST_EXE=%SCRIPT_DIR%dist\CrashTraceViewer.exe"

echo [CrashTrace] Building CrashTraceViewer.exe...

where pyinstaller >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "BUILDER=pyinstaller"
    goto run_build
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON=python"
    ) else (
        echo [CrashTrace] Python 3 was not found.
        exit /b 1
    )
)

call %PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [CrashTrace] Python 3 is unavailable.
    exit /b 1
)

set "BUILDER=%PYTHON% -m PyInstaller"

call %BUILDER% --version >nul 2>&1
if errorlevel 1 (
    echo [CrashTrace] Installing PyInstaller...
    call %PYTHON% -m pip install pyinstaller
    if errorlevel 1 (
        echo [CrashTrace] Failed to install PyInstaller.
        exit /b 1
    )
)

if not exist "%SPEC_FILE%" (
    echo [CrashTrace] Spec file not found: %SPEC_FILE%
    exit /b 1
)

:run_build
call %BUILDER% --noconfirm --clean --distpath "%SCRIPT_DIR%dist" --workpath "%SCRIPT_DIR%build" "%SPEC_FILE%"
if errorlevel 1 (
    echo [CrashTrace] Build failed.
    exit /b 1
)

if not exist "%DIST_EXE%" (
    echo [CrashTrace] Build completed but exe was not found: %DIST_EXE%
    exit /b 1
)

echo [CrashTrace] Build completed.
echo [CrashTrace] Output: %DIST_EXE%
exit /b 0
