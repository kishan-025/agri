@echo off
title Start All Services - Soil Fertility Diagnosis System
echo ==============================================================================
echo Launching Soil Precision Nutrient Diagnosis System:
echo 1. Python AI Microservice (Port 7000)
echo 2. Spring Boot 3.3 Backend (Port 9090)
echo 3. Modern HTML5/Leaflet Farmer Web Portal (Port 8501)
echo ==============================================================================

start "Python AI Satellite Microservice (Port 7000)" cmd /c "%~dp0run_ai_service.bat"
timeout /t 3 /nobreak >nul

start "Spring Boot 3.3 Backend (Port 9090)" cmd /c "%~dp0run_backend.bat"
timeout /t 5 /nobreak >nul

start "Modern HTML5/Leaflet Farmer Web Portal (Port 8501)" cmd /c "%~dp0run_frontend.bat"

echo All services launched in separate windows!
