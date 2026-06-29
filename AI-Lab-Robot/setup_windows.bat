@echo off
REM Autonomous Rover AI System - Windows Setup Script
REM ================================================

echo.
echo ========================================================
echo  AUTONOMOUS ROVER AI SYSTEM - Windows Setup
echo ========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Show Python version
echo Python version:
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated.
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo Installing requirements from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo.

REM Verify scikit-learn
echo Verifying scikit-learn installation...
python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"
if %errorlevel% neq 0 (
    echo WARNING: scikit-learn may not be properly installed
) else (
    echo scikit-learn verified.
)
echo.

REM Test imports
echo Testing core imports...
python -c "from data.datasets import DatasetLoader; from data.radar_dataset import RadarMissionDataset; print('All imports OK')"
if %errorlevel% neq 0 (
    echo WARNING: Some imports failed
) else (
    echo Core imports verified.
)
echo.

REM List datasets
echo Available datasets:
python main.py --list-datasets
echo.

echo ========================================================
echo  Setup Complete!
echo ========================================================
echo.
echo To run the interactive menu:
echo   python main.py
echo.
echo To run a specific mission:
echo   python main.py --dataset simple --mission explore
echo.
echo To list available datasets:
echo   python main.py --list-datasets
echo.
pause
