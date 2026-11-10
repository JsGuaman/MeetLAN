#!/bin/bash
# ==============================================================================
# MeetLAN - Ejecutable para GNU/Linux (Ubuntu / Debian)
# Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================================="
echo "   MeetLAN - Videollamadas P2P en Red Local (Linux)"
echo "   Comunicaciones Multimedia - Universidad de Cuenca"
echo "=========================================================================="
echo ""

# Comprobar dependencias básicas
if ! command -v ffmpeg &> /dev/null; then
    echo "[AVISO] ffmpeg no está instalado. Ejecute: sudo apt install -y ffmpeg python3-tk"
fi

python3 main.py
