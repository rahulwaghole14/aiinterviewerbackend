@echo off
echo ========================================
echo    AI INTERVIEW PORTAL - SERVER START
echo ========================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Python version:
python --version
echo.
echo Starting Daphne ASGI server...
echo (This is the CORRECT way to start the server!)
echo.
daphne -b 127.0.0.1 -p 8000 -v 3 interview_app.asgi:application

