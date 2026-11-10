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

# 2. Asegurar que /usr/sbin y /sbin estén en PATH
export PATH="$PATH:/usr/sbin:/sbin"

# 3. Localizar binario ufw o instalarlo si falta
UFW_BIN=""
for candidate in /usr/sbin/ufw /sbin/ufw /usr/bin/ufw ufw; do
    if command -v "$candidate" &> /dev/null || [ -x "$candidate" ]; then
        UFW_BIN="$candidate"
        break
    fi
done

if [ -z "$UFW_BIN" ]; then
    echo "[AVISO] 'ufw' no está instalado en este sistema."
    echo "[1/2] Instalando 'ufw' mediante apt-get..."
    apt-get update && apt-get install -y ufw
    if [ $? -ne 0 ]; then
        echo "[ERROR] No se pudo instalar ufw. Puedes instalarlo con: sudo apt install -y ufw"
        exit 1
    fi
    UFW_BIN="/usr/sbin/ufw"
    echo "[OK] 'ufw' instalado exitosamente."
    echo ""
fi

# 4. Habilitar reglas de puertos UDP para MeetLAN
echo "[2/2] Habilitando puertos UDP para video, audio y señalización..."
"$UFW_BIN" allow 5000:5010/udp comment 'MeetLAN Video RX Rango 5000-5010'
"$UFW_BIN" allow 5200:5210/udp comment 'MeetLAN Video RX Rango 5200-5210'
"$UFW_BIN" allow 6000:6020/udp comment 'MeetLAN Senalizacion Rango 6000-6020'
"$UFW_BIN" allow 6050/udp comment 'MeetLAN Senalizacion 6050'

echo ""
echo "Estado actual del Firewall UFW:"
"$UFW_BIN" status verbose

echo ""
if "$UFW_BIN" status | grep -q "inactive"; then
    echo "💡 [NOTA]: El firewall UFW se encuentra 'inactivo' por defecto en Ubuntu."
    echo "   Esto significa que tus puertos ya están totalmente abiertos y listos para MeetLAN."
    echo "   (Si deseas activar la protección estricta de UFW con estas reglas, ejecuta: sudo ufw enable)"
fi

echo ""
echo "=========================================================================="
echo "   [ÉXITO] ¡Puertos de MeetLAN configurados correctamente en Ubuntu!"
echo "=========================================================================="
