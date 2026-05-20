@echo off
echo ============================================
echo    UsagiMon - OpenGL
echo ============================================
echo.

:: Activate venv (skip if not found)
call venv\Scripts\activate.bat 2>nul

echo Starting game...
echo.
python main.py

if errorlevel 1 pause
