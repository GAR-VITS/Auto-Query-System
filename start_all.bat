@echo off
echo Starting Agentic AI Platform (Backend + Frontend)...
cd /d "%~dp0"
start "Agentic AI Backend" cmd /c "run_backend.bat"
start "Agentic AI Frontend" cmd /c "run_frontend.bat"
echo Services launched!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
pause
