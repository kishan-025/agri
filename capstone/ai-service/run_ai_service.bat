@echo off
set "KMP_DUPLICATE_LIB_OK=TRUE"
title Python AI Satellite Microservice (Port 7000)

:: Automatically detect and switch to ai-service directory
if exist "%~dp0app.py" (
    cd /d "%~dp0"
) else if exist "%~dp0ai-service\app.py" (
    cd /d "%~dp0ai-service"
)

echo ========================================================
echo Starting Soil Fertility AI Microservice on Port 7000...
echo Working Directory: %CD%
echo ========================================================

:: Detect Python environment with PyTorch and Presto support
set "PY_EXE=python"
if exist "C:\Users\kisha\anaconda3\python.exe" (
    set "PY_EXE=C:\Users\kisha\anaconda3\python.exe"
)

echo Using Python: %PY_EXE%
"%PY_EXE%" -c "import torch; print('[OK] PyTorch Version:', torch.__version__)"
if errorlevel 1 (
    echo [ERROR] PyTorch not available in %PY_EXE%.
    pause
    exit /b 1
)

echo Starting Uvicorn server on http://127.0.0.1:7000 ...
"%PY_EXE%" -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload

pause
