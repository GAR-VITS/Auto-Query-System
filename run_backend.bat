@echo off
echo Starting Agentic AI Backend (FastAPI + Gemini 2.5 Flash)...
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)
pause
