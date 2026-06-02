@echo off
echo ================================================================================
echo Trading System - Environment Setup
echo ================================================================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.7 or higher.
    pause
    exit /b 1
)
echo.

echo Installing required packages...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ================================================================================
echo Testing installation...
echo ================================================================================
python -c "import pandas; import numpy; import yfinance; print('SUCCESS: All packages installed correctly!')"

if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed. See error above.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Setup Complete!
echo ================================================================================
echo.
echo You can now run:
echo   - python test_position_calculator.py
echo   - cd backtesting ^& python run_backtest.py --system 2
echo.
echo See SETUP.md for more details.
echo.
pause
