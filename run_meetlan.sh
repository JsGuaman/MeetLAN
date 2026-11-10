#!/bin/bash
# ==============================================================================
# MeetLAN - Ejecutable para GNU/Linux (Ubuntu / Debian / Kali Linux)
# Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================================="
echo "   MeetLAN - Videollamadas P2P en Red Local (Linux / Kali)"
echo "   Comunicaciones Multimedia - Universidad de Cuenca"
echo "=========================================================================="
echo ""

# 1. Comprobar Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no está instalado. Ejecute: sudo apt install -y python3"
    exit 1
fi

# 2. Comprobar Tkinter (crucial en Kali Linux / Debian minimal)
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "[AVISO] La librería gráfica Tkinter no está instalada en tu sistema."
    echo "Instalando dependencia python3-tk..."
    if [ "$EUID" -eq 0 ]; then
        apt-get update && apt-get install -y python3-tk
    else
        sudo apt-get update && sudo apt-get install -y python3-tk
    fi
fi

# 3. Comprobar FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[AVISO] FFmpeg no está instalado. Instalándolo..."
    if [ "$EUID" -eq 0 ]; then
        apt-get update && apt-get install -y ffmpeg
    else
        sudo apt-get update && sudo apt-get install -y ffmpeg
    fi
fi

# 4. Lanzar la aplicación
python3 main.py
