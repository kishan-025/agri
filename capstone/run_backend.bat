@echo off
title Spring Boot 3.3 Backend (Port 9090)
cd /d "%~dp0backend-spring"
echo ========================================================
echo Starting Spring Boot 3.3 (Java 21) on Port 9090...
echo Connecting to Aiven Cloud PostgreSQL PostGIS...
echo ========================================================
mvn spring-boot:run
pause
