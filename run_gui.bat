@echo off
echo Starting I-MusicExtractor GUI...
python I-MusicExtractor-GUI.py
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo An error occurred. Press any key to exit.
  pause > nul
) 