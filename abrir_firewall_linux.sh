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
ufw allow 5000/udp comment 'MeetLAN Video RX 5000'
ufw allow 5001/udp comment 'MeetLAN Video RX 5001'
ufw allow 5200:5201/udp comment 'MeetLAN Puertos Alternativos'
ufw allow 6000/udp comment 'MeetLAN Senalizacion 6000'
ufw allow 6050/udp comment 'MeetLAN Senalizacion 6050'

echo ""
echo "Estado actual del Firewall UFW:"
ufw status verbose

echo ""
echo "=========================================================================="
echo "   [ÉXITO] ¡Puertos de MeetLAN abiertos en Ubuntu!"
echo "=========================================================================="
