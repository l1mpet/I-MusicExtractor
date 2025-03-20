@echo off
rem I-MusicExtractor.bat - Launcher for Windows
rem This batch file allows you to double-click to run the application from File Explorer

echo Launching I-MusicExtractor GUI...

rem Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd "%SCRIPT_DIR%"

rem Check for Python
where python >nul 2>&1
if %ERRORLEVEL% == 0 (
    python "%SCRIPT_DIR%I-MusicExtractor-GUI.py"
    goto :end
)

rem Try py launcher (newer Python installations)
where py >nul 2>&1
if %ERRORLEVEL% == 0 (
    py "%SCRIPT_DIR%I-MusicExtractor-GUI.py"
    goto :end
)

echo Python is not installed or not in your PATH.
echo Please install Python 3.6 or later from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause

:end 