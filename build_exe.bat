@echo off
REM Build script for TestHead Control Executable
REM This creates a standalone .exe with all dependencies bundled

echo ========================================
echo Building TestHead Control Executable
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not installed or not in PATH
    pause
    exit /b 1
)

echo Step 1: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Building executable with PyInstaller...
pyinstaller testhead_control.spec --clean
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: dist\testhead_control.exe
echo.
echo To deploy, copy the entire dist\ folder to target PC
echo Make sure AIOUSB.dll is in System32 or create a drivers\ folder
echo.
pause
