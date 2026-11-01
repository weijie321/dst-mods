@echo off
setlocal

rem 无参数仅预览旺达；部署需要 --mod NAME --apply --verified RESULT_JSON。
if "%~1"=="" (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0dst.ps1" deploy --mod wanda-skilltree
) else (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0dst.ps1" deploy %*
)
exit /b %ERRORLEVEL%
