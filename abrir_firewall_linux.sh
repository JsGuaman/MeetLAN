#!/bin/bash
# ==============================================================================
# Apertura de Puertos de Firewall para MeetLAN (Ubuntu / Debian / Kali Linux)
# Comunicaciones Multimedia - Universidad de Cuenca
# ==============================================================================

echo "=========================================================================="
echo "   MeetLAN - Apertura de Puertos de Firewall en Linux (Ubuntu / Kali)"
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

# 3. Localizar binario ufw o intentar instalarlo
UFW_BIN=""
for candidate in /usr/sbin/ufw /sbin/ufw /usr/bin/ufw ufw; do
    if command -v "$candidate" &> /dev/null || [ -x "$candidate" ]; then
        UFW_BIN="$candidate"
        break
    fi
done

if [ -z "$UFW_BIN" ]; then
    echo "[AVISO] 'ufw' no está instalado en este sistema."
    echo "[1/2] Intentando instalar 'ufw' mediante apt-get..."
    apt-get update && apt-get install -y ufw 2>/dev/null
    for candidate in /usr/sbin/ufw /sbin/ufw /usr/bin/ufw ufw; do
        if command -v "$candidate" &> /dev/null || [ -x "$candidate" ]; then
            UFW_BIN="$candidate"
            break
        fi
    done
fi

# 4. Aplicar reglas con UFW o directamente con iptables (estándar en Kali Linux)
if [ -n "$UFW_BIN" ]; then
    echo "[2/2] Habilitando puertos UDP en UFW..."
    "$UFW_BIN" allow 5000:5010/udp comment 'MeetLAN Video RX Rango 5000-5010'
    "$UFW_BIN" allow 5200:5210/udp comment 'MeetLAN Video RX Rango 5200-5210'
    "$UFW_BIN" allow 6000:6020/udp comment 'MeetLAN Senalizacion Rango 6000-6020'
    "$UFW_BIN" allow 6050/udp comment 'MeetLAN Senalizacion 6050'

    echo ""
    echo "Estado actual del Firewall UFW:"
    "$UFW_BIN" status verbose

    if "$UFW_BIN" status | grep -q "inactive"; then
        echo ""
        echo "💡 [NOTA]: El firewall UFW se encuentra 'inactivo' por defecto en Linux."
        echo "   Esto significa que tus puertos ya están totalmente abiertos y listos para MeetLAN."
        echo "   (Si deseas activar la protección estricta de UFW con estas reglas, ejecuta: sudo ufw enable)"
    fi
else
    echo "[2/2] UFW no disponible. Aplicando reglas directamente con iptables (Kali Linux)..."
    IPT_BIN=""
    for candidate in /usr/sbin/iptables /sbin/iptables /usr/bin/iptables iptables; do
        if command -v "$candidate" &> /dev/null || [ -x "$candidate" ]; then
            IPT_BIN="$candidate"
            break
        fi
    done

    if [ -n "$IPT_BIN" ]; then
        "$IPT_BIN" -I INPUT -p udp --dport 5000:5010 -j ACCEPT 2>/dev/null || true
        "$IPT_BIN" -I INPUT -p udp --dport 5200:5210 -j ACCEPT 2>/dev/null || true
        "$IPT_BIN" -I INPUT -p udp --dport 6000:6020 -j ACCEPT 2>/dev/null || true
        "$IPT_BIN" -I INPUT -p udp --dport 6050 -j ACCEPT 2>/dev/null || true
        echo "[OK] Reglas aplicadas en iptables para puertos UDP: 5000-5010, 5200-5210, 6000-6020."
    fi
fi

echo ""
echo "=========================================================================="
echo "   [ÉXITO] ¡Puertos de MeetLAN configurados correctamente en Linux!"
echo "=========================================================================="
