@echo off
echo ========================================
echo AutoOps Task Board - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python dependencies...
pip show flask >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed
)

echo.
echo [2/4] Checking SQL Server driver...
pip show pyodbc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing pyodbc for SQL Server...
    pip install pyodbc
)

echo.
echo [3/4] Checking .env file...
if not exist .env (
    echo Creating .env file with default values...
    (
        echo JWT_SECRET=your-secret-key-change-this-in-production
        echo PORT=3001
        echo DB_SERVER=SUMANTH\SQLEXPRESS
        echo DB_NAME=AutoOpsDB
        echo DB_USER=
        echo DB_PASSWORD=
        echo EMAIL_METHOD=api
        echo BREVO_API_KEY=
        echo BREVO_SENDER_EMAIL=noreply@autoops.com
        echo BREVO_SENDER_NAME=AutoOps Team
    ) > .env
    echo .env file created. Please edit it with your settings.
) else (
    echo .env file exists
)

echo.
echo [4/4] Starting Flask server...
echo.
echo Server will start at: http://localhost:3001
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

python run.py

pause
