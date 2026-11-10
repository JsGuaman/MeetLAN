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

# 1. Asegurar permisos de superusuario
if [ "$EUID" -ne 0 ]; then
    echo "[AVISO] Solicitando permisos sudo..."
    exec sudo bash "$0" "$@"
fi

# 2. Asegurar que /usr/sbin y /sbin estén en PATH (donde reside ufw)
export PATH="$PATH:/usr/sbin:/sbin"

# 3. Comprobar si ufw está instalado; si no, instalarlo con apt
if ! command -v ufw &> /dev/null; then
    echo "[AVISO] El comando 'ufw' no está instalado en este sistema."
    echo "[1/2] Instalando 'ufw' mediante apt-get..."
    apt-get update && apt-get install -y ufw
    if [ $? -ne 0 ]; then
        echo "[ERROR] No se pudo instalar ufw automáticamente."
        echo "Por favor ejecuta: sudo apt update && sudo apt install -y ufw"
        exit 1
    fi
    echo "[OK] 'ufw' instalado exitosamente."
    echo ""
fi

# 4. Habilitar reglas de puertos UDP para MeetLAN
echo "[2/2] Habilitando puertos UDP para video, audio y señalización..."
ufw allow 5000:5010/udp comment 'MeetLAN Video RX Rango 5000-5010'
ufw allow 5200:5210/udp comment 'MeetLAN Video RX Rango 5200-5210'
ufw allow 6000:6020/udp comment 'MeetLAN Senalizacion Rango 6000-6020'
ufw allow 6050/udp comment 'MeetLAN Senalizacion 6050'

echo ""
echo "Estado actual del Firewall UFW:"
ufw status verbose

echo ""
# Si UFW está inactivo, informar al usuario
if ufw status | grep -q "inactive"; then
    echo "💡 [NOTA]: El firewall UFW se encuentra 'inactivo' por defecto en Ubuntu."
    echo "   Esto significa que tus puertos ya están totalmente abiertos y listos para MeetLAN."
    echo "   (Si deseas activar la protección estricta de UFW con estas reglas, ejecuta: sudo ufw enable)"
fi

echo ""
echo "=========================================================================="
echo "   [ÉXITO] ¡Puertos de MeetLAN configurados correctamente en Ubuntu!"
echo "=========================================================================="
