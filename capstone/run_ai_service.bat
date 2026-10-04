@echo off
title Python AI Satellite Microservice (Port 7000)
cd /d "%~dp0ai-service"
echo ========================================================
echo Starting Soil Fertility AI Microservice on Port 7000...
echo ========================================================

if exist "%~dp0ai-service\env1\Scripts\python.exe" (
    echo Using custom virtual environment: env1
    "%~dp0ai-service\env1\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
) else (
    python -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
)

pause
