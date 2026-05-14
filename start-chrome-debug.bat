@echo off
REM start-chrome-debug.bat
REM Double-click to launch Chrome with remote debugging enabled so
REM Claude Code's chrome-devtools MCP server can attach.
REM
REM Uses a dedicated user-data dir so it doesn't clash with your normal
REM Chrome window. Profile persists at %LOCALAPPDATA%\ChromeDebugProfile
REM (sign in to Gmail/etc. once and it sticks).

setlocal

set "PROFILE=%LOCALAPPDATA%\ChromeDebugProfile"
if not exist "%PROFILE%" mkdir "%PROFILE%"

set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if not exist "%CHROME%" (
    echo Chrome not found in standard install locations.
    echo Install Chrome or edit this file with the correct path.
    pause
    exit /b 1
)

start "" "%CHROME%" --remote-debugging-port=9222 --user-data-dir="%PROFILE%" https://www.google.com

endlocal
