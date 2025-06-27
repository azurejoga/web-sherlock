@echo off
REM Web Sherlock - Virtual Environment Setup Script for Windows
REM This script creates and configures a Python virtual environment

echo 🔧 Web Sherlock - Virtual Environment Setup
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo ✅ Python detected

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🎉 Setup Complete!
echo.
echo To activate the virtual environment, run:
echo     venv\Scripts\activate.bat
echo.
echo To start Web Sherlock, run:
echo     python main.py
echo.
echo To deactivate the virtual environment, run:
echo     deactivate
pause