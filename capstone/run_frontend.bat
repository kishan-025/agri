@echo off
title Modern Farmer Web Portal (Port 8501)
cd /d "%~dp0frontend"
echo ========================================================
echo Starting Modern HTML5/Leaflet Farmer Web Portal...
echo Listening on: http://localhost:8501
echo ========================================================

start "" "http://localhost:8501"
python -m http.server 8501
pause
