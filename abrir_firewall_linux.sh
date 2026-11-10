#!/bin/bash
# ==============================================================================
# Apertura de Puertos de Firewall UFW para MeetLAN (Ubuntu / Linux)
# Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

echo "=========================================================================="
echo "   MeetLAN - Apertura de Puertos en Firewall UFW (Linux)"
echo "   Comunicaciones Multimedia - Universidad de Cuenca"
echo "=========================================================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "[AVISO] Solicitando permisos sudo..."
    exec sudo bash "$0" "$@"
fi

echo "Habilitando puertos UDP para video, audio y señalización..."
ufw allow 5000:5010/udp comment 'MeetLAN Video RX Rango 5000-5010'
ufw allow 5200:5210/udp comment 'MeetLAN Video RX Rango 5200-5210'
ufw allow 6000:6020/udp comment 'MeetLAN Senalizacion Rango 6000-6020'
ufw allow 6050/udp comment 'MeetLAN Senalizacion 6050'

echo ""
echo "Estado actual del Firewall UFW:"
ufw status verbose

echo ""
echo "=========================================================================="
echo "   [ÉXITO] ¡Puertos de MeetLAN abiertos en Ubuntu!"
echo "=========================================================================="
