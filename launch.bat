@echo off
title InterviewIQ Launcher
echo ====================================================
echo        Starting InterviewIQ AI Placement Coach
echo ====================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [.venv not found or incomplete] Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    ".venv\Scripts\pip.exe" install -r requirements.txt
)

echo Launching Streamlit Neumorphic Web Application...
".venv\Scripts\python.exe" -m streamlit run frontend/app.py
pause
