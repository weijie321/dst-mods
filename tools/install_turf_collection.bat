@echo off
setlocal
chcp 65001 >nul
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_turf_collection.ps1" %*
set "TURF_INSTALL_EXIT=%ERRORLEVEL%"
pause
exit /b %TURF_INSTALL_EXIT%
