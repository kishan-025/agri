@echo off
set KMP_DUPLICATE_LIB_OK=TRUE
title Python AI Satellite Microservice (Port 7000)
cd /d "%~dp0ai-service"
echo ========================================================
echo Starting Soil Fertility AI Microservice on Port 7000...
echo ========================================================

REM Prefer Python environment with PyTorch for Presto Foundation Model
python -c "import torch" >nul 2>&1
if %errorlevel% equ 0 (
    echo Using Python environment with PyTorch (Presto Engine enabled)
    python -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
) else (
    if exist "%~dp0ai-service\env1\Scripts\python.exe" (
        echo Using custom virtual environment: env1
        "%~dp0ai-service\env1\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
    ) else (
        python -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
    )
)

pause
