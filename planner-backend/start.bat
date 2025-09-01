@echo off
echo Starting Preauth Agent APIs...
echo ================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please update .env file with your configuration
)

:: Start the application
echo Starting FastAPI server...
echo.
echo API Documentation will be available at: http://host.docker.internal:8001/docs
echo Health Check: http://host.docker.internal:8001/health
echo.
python main.py
