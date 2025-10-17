@echo off
REM Combined Server Starter for AI Interview Platform (Windows)
REM Starts both Django backend and React frontend servers simultaneously

echo 🎯 AI Interview Platform - Combined Server Starter
echo ==================================================

REM Get the directory of the batch file
set "SCRIPT_DIR=%~dp0"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
set "VENV_DIR=%SCRIPT_DIR%venv"

echo 🔍 Checking prerequisites...

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo ❌ Virtual environment not found at %VENV_DIR%
    echo 💡 Please run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "%FRONTEND_DIR%" (
    echo ❌ Frontend directory not found at %FRONTEND_DIR%
    pause
    exit /b 1
)

REM Check if node_modules exists, install if not
if not exist "%FRONTEND_DIR%\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install frontend dependencies
        pause
        exit /b 1
    )
    cd /d "%SCRIPT_DIR%"
)

echo ✅ All prerequisites met!

REM Start backend server
echo 🚀 Starting Django backend server...
cd /d "%SCRIPT_DIR%"
start "Backend Server" cmd /k "venv\Scripts\activate && python manage.py runserver 127.0.0.1:8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo 🚀 Starting React frontend server...
cd /d "%FRONTEND_DIR%"
start "Frontend Server" cmd /k "npm run dev"

echo.
echo 🎉 Both servers are starting!
echo 📍 Backend:  http://127.0.0.1:8000
echo 📍 Frontend: http://localhost:5173
echo.
echo 💡 Two command windows will open for each server
echo 💡 Close those windows to stop the servers
echo.

pause
