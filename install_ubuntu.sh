#!/bin/bash
# ==============================================================================
# Script de Instalación de Dependencias para Ubuntu / Debian
# MeetLAN - Comunicaciones Multimedia
# ==============================================================================

echo "=========================================================================="
echo "   Instalando dependencias de MeetLAN en Ubuntu..."
echo "=========================================================================="
echo ""

sudo apt update
sudo apt install -y ffmpeg python3-tk python3-pil python3-numpy pulseaudio-utils v4l-utils

echo ""
echo "=========================================================================="
echo "   ¡Instalación completada! Ya puedes ejecutar ./run_meetlan.sh"
echo "=========================================================================="
