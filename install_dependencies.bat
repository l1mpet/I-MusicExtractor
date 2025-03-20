@echo off
echo Installing I-MusicExtractor dependencies...
echo.

:: Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

:: Install dependencies
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

:: Optional: Install cx_Freeze for building executable
echo.
echo Do you want to install cx_Freeze for building standalone executables? (Y/N)
set /p INSTALL_CX_FREEZE=
if /i "%INSTALL_CX_FREEZE%"=="Y" (
    echo Installing cx_Freeze...
    python -m pip install cx_freeze
)

echo.
echo Installation complete!
echo.
echo You can now run the GUI by double-clicking run_gui.bat or by running:
echo python I-MusicExtractor-GUI.py
echo.
echo Press any key to exit...
pause > nul 