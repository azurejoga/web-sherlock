@echo off
REM Web Sherlock - Local Development Server Script for Windows
REM Quick start script for development

echo 🚀 Starting Web Sherlock Local Development Server
echo ================================================

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ Virtual environment not found. Run setup_venv.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Set environment variables for development
set FLASK_ENV=development
set FLASK_DEBUG=1
if not defined SESSION_SECRET set SESSION_SECRET=dev-secret-key-change-in-production

REM Check if required directories exist
if not exist "uploads\" mkdir uploads
if not exist "results\" mkdir results
if not exist "history\" mkdir history
if not exist "translations\" mkdir translations
if not exist "static\css\" mkdir static\css
if not exist "static\js\" mkdir static\js
if not exist "templates\" mkdir templates

echo ✅ Environment ready
echo 🌐 Starting Flask development server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Start the application
python main.py
pause