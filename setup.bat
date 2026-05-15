@echo off
echo ============================================
echo    SETUP - Game Platformer 2D OpenGL
echo ============================================
echo.

:: --- Step 1: Find Python 3.12 or lower ---
set PYTHON_CMD=

py -3.12 --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py -3.12
if defined PYTHON_CMD goto :found

py -3.11 --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py -3.11
if defined PYTHON_CMD goto :found

py -3.10 --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py -3.10
if defined PYTHON_CMD goto :found

py -3.9 --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py -3.9
if defined PYTHON_CMD goto :found

echo.
echo [ERROR] Python 3.9 - 3.12 not found!
echo Please install from: https://www.python.org/downloads/
echo (pygame does not support Python 3.13+)
pause
exit /b 1

:found
echo [1/3] Found: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

:: --- Step 2: Create virtual environment ---
if exist venv goto :skip_venv
echo [2/3] Creating virtual environment...
%PYTHON_CMD% -m venv venv
echo      Done.
goto :install

:skip_venv
echo [2/3] Virtual environment already exists.

:install
echo.

:: --- Step 3: Activate and install dependencies ---
echo [3/3] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

echo.
echo ============================================
echo    SETUP FINISHED!
echo    Run run.bat to start the game.
echo ============================================
pause
