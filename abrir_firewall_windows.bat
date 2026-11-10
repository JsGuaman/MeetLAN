@echo off
title MeetLAN - Configurador Automatico de Firewall de Windows

echo ==========================================================================
echo    MeetLAN - Apertura de Puertos en Firewall de Windows
echo    Comunicaciones Multimedia - Universidad de Cuenca
echo ==========================================================================
echo.

REM Comprobacion de permisos de Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Este script requiere permisos de Administrador para configurar el Firewall.
    echo Por favor, haz clic derecho sobre este archivo y selecciona:
    echo        "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo [1/3] Habilitando puertos UDP (5000, 5001, 5200, 5201, 6000, 6010, 6050)...
netsh advfirewall firewall delete rule name="MeetLAN_UDP_Ports" >nul 2>&1
netsh advfirewall firewall add rule name="MeetLAN_UDP_Ports" dir=in action=allow protocol=UDP localport=5000,5001,5200,5201,6000,6010,6050 profile=any >nul

echo [2/3] Habilitando ejecutable ffplay.exe en el Firewall...
for /f "delims=" %%i in ('where ffplay.exe 2^>nul') do set FFPLAY_PATH=%%i

if not "%FFPLAY_PATH%"=="" (
    netsh advfirewall firewall delete rule name="MeetLAN_FFplay" >nul 2>&1
    netsh advfirewall firewall add rule name="MeetLAN_FFplay" dir=in action=allow program="%FFPLAY_PATH%" enable=yes profile=any >nul
    echo       -> ffplay permitido en: %FFPLAY_PATH%
) else (
    echo       -> ffplay.exe no encontrado en PATH (se aplican solo reglas por puerto).
)

echo [3/3] Habilitando ejecutable python.exe en el Firewall...
for /f "delims=" %%i in ('where python.exe 2^>nul') do set PYTHON_PATH=%%i

if not "%PYTHON_PATH%"=="" (
    netsh advfirewall firewall delete rule name="MeetLAN_Python" >nul 2>&1
    netsh advfirewall firewall add rule name="MeetLAN_Python" dir=in action=allow program="%PYTHON_PATH%" enable=yes profile=any >nul
    echo       -> python permitido en: %PYTHON_PATH%
)

echo.
echo ==========================================================================
echo [EXITO] ¡Reglas de Firewall configuradas correctamente para MeetLAN!
echo El trafico de video, audio y senalizacion P2P no sera bloqueado.
echo ==========================================================================
echo.
pause
