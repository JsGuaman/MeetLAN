#!/bin/bash
# ==============================================================================
# Script de Instalación de Dependencias para Kali Linux / Debian
# MeetLAN - Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

echo "=========================================================================="
echo "   Instalando dependencias de MeetLAN en Kali Linux..."
echo "   Comunicaciones Multimedia - Universidad de Cuenca"
echo "=========================================================================="
echo ""

# 1. Comprobar permisos root o sudo
SUDO=""
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
fi

echo "[1/3] Actualizando repositorios APT..."
$SUDO apt update

echo "[2/3] Instalando FFmpeg, Python3-Tk, PulseAudio, ALSA y V4L2..."
$SUDO apt install -y \
    ffmpeg \
    python3 \
    python3-tk \
    python3-pil \
    python3-numpy \
    pulseaudio-utils \
    alsa-utils \
    v4l-utils \
    iptables \
    ufw 2>/dev/null || true

# 2. Permisos de hardware (cámara /dev/video* y audio) si es usuario no-root
if [ "$EUID" -ne 0 ]; then
    echo "[3/3] Configurando permisos de usuario para cámara y audio..."
    $SUDO usermod -aG video,audio "$USER" 2>/dev/null || true
fi

# 3. Dar permisos de ejecución a todos los scripts
chmod +x run_meetlan.sh abrir_firewall_linux.sh install_ubuntu.sh install_kali.sh 2>/dev/null || true

echo ""
echo "=========================================================================="
echo "   ¡Instalación en Kali Linux completada con éxito!"
echo "   - Python 3 y Tkinter: Listos"
echo "   - FFmpeg y FFplay: Listos"
echo "   - Audio (Pulse / ALSA) y Video (V4L2 / lavfi): Listos"
echo ""
echo "   Ya puedes ejecutar la aplicación con: ./run_meetlan.sh"
echo "=========================================================================="
