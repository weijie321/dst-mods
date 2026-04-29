@echo off
setlocal

set "DEV_ROOT=E:\work\code\ai-generated\dst-mods"
set "GAME_MODS=S:\game\steam\steamapps\common\Don't Starve Together\mods"

echo [sync] dev root  : %DEV_ROOT%
echo [sync] game mods : %GAME_MODS%

if not exist "%DEV_ROOT%" (
    echo [sync][error] dev root does not exist
    exit /b 1
)

if not exist "%GAME_MODS%" (
    echo [sync][error] game mods directory does not exist
    exit /b 1
)

call :sync_one "dst-mod-crash-tracer"
if errorlevel 1 exit /b 1

call :sync_one "dst-mod-crash-tracer-test"
if errorlevel 1 exit /b 1

call :sync_one "dst-mod-crash-tracer-event-test"
if errorlevel 1 exit /b 1

call :sync_one "dst-mod-crash-tracer-task-test"
if errorlevel 1 exit /b 1

call :sync_one "dst-mod-crash-tracer-periodic-test"
if errorlevel 1 exit /b 1

call :sync_one "dst-mod-crash-tracer-grass-test"
if errorlevel 1 exit /b 1

echo [sync] done
exit /b 0

:sync_one
set "MOD_NAME=%~1"
set "SRC=%DEV_ROOT%\%MOD_NAME%"
set "DST=%GAME_MODS%\%MOD_NAME%"

if not exist "%SRC%" (
    echo [sync][warn] skip missing mod: %MOD_NAME%
    exit /b 0
)

if not exist "%DST%" mkdir "%DST%"

echo [sync] copying %MOD_NAME%
robocopy "%SRC%" "%DST%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP >nul
set "ROBOCODE=%ERRORLEVEL%"

if %ROBOCODE% GEQ 8 (
    echo [sync][error] robocopy failed for %MOD_NAME% with code %ROBOCODE%
    exit /b %ROBOCODE%
)

exit /b 0
