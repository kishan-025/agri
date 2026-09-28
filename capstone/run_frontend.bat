@echo off
title Streamlit Farmer Web Portal (Port 8501)
cd /d "%~dp0frontend"
echo ========================================================
echo Starting Streamlit Farmer Web Portal on Port 8501...
echo ========================================================
streamlit run app.py --server.port 8501
pause
