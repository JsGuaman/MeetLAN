#!/bin/bash
# ==============================================================================
# Script de Instalación de Dependencias para Ubuntu / Debian
# MeetLAN - Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

echo "=========================================================================="
echo "   Instalando dependencias de MeetLAN en Ubuntu..."
echo "=========================================================================="
echo ""

# 1. Actualizar repositorios e instalar paquetes multimedia base y ufw
sudo apt update
sudo apt install -y \
    ffmpeg \
    python3-tk \
    python3-pil \
    python3-numpy \
    pulseaudio-utils \
    v4l-utils \
    ufw

# 2. Intentar instalar agente de elevación gráfica (compatible con Ubuntu 20.04, 22.04 y 24.04)
sudo apt install -y pkexec 2>/dev/null || sudo apt install -y policykit-1 2>/dev/null || true

# 3. Asegurar que el usuario tenga permisos para acceder a cámara (/dev/video*) y audio
sudo usermod -aG video,audio "$USER" 2>/dev/null || true

# 4. Dar permisos de ejecución a los scripts del proyecto
chmod +x run_meetlan.sh abrir_firewall_linux.sh install_ubuntu.sh 2>/dev/null || true

echo ""
echo "=========================================================================="
echo "   ¡Instalación completada con éxito!"
echo "   - Paquetes multimedia (FFmpeg, PulseAudio, V4L2): Instalados"
echo "   - Firewall UFW: Instalado y listo"
echo ""
echo "   Ya puedes ejecutar la aplicación con: ./run_meetlan.sh"
echo "=========================================================================="
