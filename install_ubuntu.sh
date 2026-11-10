#!/bin/bash
# ==============================================================================
# Script de Instalación de Dependencias para Ubuntu / Debian
# MeetLAN - Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

echo "=========================================================================="
echo "   Instalando dependencias de MeetLAN en Ubuntu..."
echo "=========================================================================="
echo ""

# 1. Actualizar repositorios e instalar dependencias multimedia, python y firewall
sudo apt update
sudo apt install -y \
    ffmpeg \
    python3-tk \
    python3-pil \
    python3-numpy \
    pulseaudio-utils \
    v4l-utils \
    ufw \
    policykit-1

# 2. Asegurar que el usuario tenga permisos para acceder a cámara (/dev/video*) y audio
sudo usermod -aG video,audio "$USER" 2>/dev/null || true

# 3. Dar permisos de ejecución a los scripts del proyecto
chmod +x run_meetlan.sh abrir_firewall_linux.sh install_ubuntu.sh 2>/dev/null || true

echo ""
echo "=========================================================================="
echo "   ¡Instalación completada con éxito!"
echo "   - Paquetes multimedia (FFmpeg, PulseAudio, V4L2): Instalados"
echo "   - Firewall UFW y PolicyKit (pkexec): Instalados"
echo ""
echo "   Ya puedes ejecutar la aplicación con: ./run_meetlan.sh"
echo "=========================================================================="
