@echo off
title MeetLAN - Sistema de Videollamada P2P en Tiempo Real
cd /d "%~dp0"

echo ==========================================================================
echo    MeetLAN - Videollamadas P2P en Red Local (Windows)
echo    Comunicaciones Multimedia - Universidad de Cuenca
echo ==========================================================================
echo.
echo Iniciando aplicacion MeetLAN...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ocurrio un error al ejecutar MeetLAN.
    echo Asegurate de tener Python y FFmpeg instalados en tu sistema.
    pause
)
