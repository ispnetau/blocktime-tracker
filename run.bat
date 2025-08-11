@echo off
cd /d "C:\Projects\Blocktime Tracker"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Blocktime Tracker App...
uvicorn main:app --reload

echo.
pause
