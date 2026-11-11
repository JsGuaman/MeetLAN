"""
MeetLAN - Módulo de Configuración y Persistencia
Comunicaciones Multimedia - Universidad de Cuenca
"""

import os
import json
import socket
import platform
import subprocess
import re

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def get_available_interfaces():
    """
    Detecta todas las interfaces de red IPv4 activas en el equipo.
    Separa y prioriza interfaces físicas reales (Wi-Fi, Ethernet)
    sobre interfaces virtuales (GNS3, Loopback, VMware, VirtualBox, WSL, Tailscale).
    """
    interfaces = []
    is_win = platform.system() == "Windows"
    virtual_keywords = [
        "gns3", "loopback", "pseudo", "vmware", "vmnet", "virtualbox",
        "vbox", "wsl", "vethernet", "tailscale", "teredo", "docker", "veth"
    ]

    if is_win:
        try:
            out = subprocess.check_output(
                ["netsh", "interface", "ipv4", "show", "addresses"],
                text=True, errors="ignore"
            )
            cur_name = ""
            for line in out.splitlines():
                line = line.strip()
                m_name = re.search(r'"([^"]+)"', line)
                if m_name and ("interfaz" in line.lower() or "interface" in line.lower()):
                    cur_name = m_name.group(1)
                m_ip = re.search(r':\s*(\d+\.\d+\.\d+\.\d+)', line)
                if m_ip and cur_name and ("ip" in line.lower() or "direcci" in line.lower()):
                    ip = m_ip.group(1)
                    if not ip.startswith("127.") and not ip.startswith("169.254."):
                        is_virt = any(vk in cur_name.lower() for vk in virtual_keywords)
                        interfaces.append({
                            "name": cur_name,
                            "ip": ip,
                            "is_virtual": is_virt
                        })
        except Exception:
            pass
    else:
        # GNU/Linux (Ubuntu, Debian, Kali)
        try:
            out = subprocess.check_output(["ip", "-4", "addr"], text=True, errors="ignore")
            cur_name = ""
            for line in out.splitlines():
                m_if = re.match(r'^\d+:\s+([^:]+):', line)
                if m_if:
                    cur_name = m_if.group(1)
                m_ip = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/', line)
                if m_ip and cur_name and cur_name != "lo":
                    ip = m_ip.group(1)
                    is_virt = any(vk in cur_name.lower() for vk in virtual_keywords)
                    interfaces.append({
                        "name": cur_name,
                        "ip": ip,
                        "is_virtual": is_virt
                    })
        except Exception:
            pass

    # Fallback general si no se detectaron con herramientas del sistema
    if not interfaces:
        try:
            host_ips = socket.gethostbyname_ex(socket.gethostname())[2]
            for ip in host_ips:
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    interfaces.append({
                        "name": f"Interfaz ({ip})",
                        "ip": ip,
                        "is_virtual": False
                    })
        except Exception:
            pass

    # Ordenar con prioridad: 1º Wi-Fi física, 2º Ethernet física, 3º Virtuales
    def _iface_sort_key(x):
        is_v = x.get("is_virtual", False)
        name_l = x.get("name", "").lower()
        if is_v:
            tier = 2
        elif "wi-fi" in name_l or "wlan" in name_l or "wireless" in name_l or "inalámbrica" in name_l:
            tier = 0
        else:
            tier = 1
        return (tier, x.get("name", ""))

    interfaces.sort(key=_iface_sort_key)
    return interfaces

def get_local_ip(preferred=None):
    """
    Obtiene la IP local para la aplicación.
    Si se especifica una interfaz preferida o IP, intenta usarla.
    Por defecto, selecciona la primera interfaz física activa (Wi-Fi / Ethernet),
    evitando interfaces virtuales como GNS3-Loopback o VMware.
    """
    ifaces = get_available_interfaces()
    if preferred:
        for iface in ifaces:
            if iface["ip"] == preferred or iface["name"] == preferred or f"{iface['name']}: {iface['ip']}" == preferred:
                return iface["ip"]

    # 1. Seleccionar la primera interfaz física (no virtual)
    for iface in ifaces:
        if not iface.get("is_virtual", False):
            return iface["ip"]

    # 2. Si solo hay virtuales, tomar la primera
    if ifaces:
        return ifaces[0]["ip"]

    # 3. Fallback a socket connect dummy
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def default_config():
    is_win = platform.system() == "Windows"
    user_name = os.getenv("USERNAME" if is_win else "USER", "Usuario")
    
    return {
        "user_name": user_name,
        "os_type": "Windows" if is_win else "Linux",
        
        # Parámetros de Video (optimizados en TC7 / Interciclo)
        "video_bitrate": "300k",
        "video_maxrate": "300k",
        "video_bufsize": "300k",
        "fps": 24,
        "gop": 24,
        "preset": "ultrafast",
        "tune": "zerolatency",
        "pix_fmt": "yuv420p",
        "width": 640,
        "height": 480,
        
        # Parámetros de Audio
        "audio_codec": "aac",
        "audio_bitrate": "64k",
        "audio_channels": 1,
        "audio_samplerate": 44100,
        "audio_buffer_size_ms": 40,
        "aresample_filter": "aresample=async=1:first_pts=0",
        
        # Parámetros de Red y Puertos (Evita colisiones con National Instruments / Windows)
        "signaling_port": 6010,
        "rx_port": 5200,
        "tx_port": 5200,
        "local_preview_port": 4000,
        "fifo_size": 0,
        "pkt_size": 1316,
        "rtbufsize": "250M",
        
        # Dispositivos de Hardware
        "devices": {
            "windows": {
                "video": "FaceTime HD Camera (Built-in)",
                "audio": "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{4A719366-ED8A-4363-908C-251F8B300B2E}",
                "audio_friendly": "Micrófono Integrado (Cirrus Logic)"
            },
            "linux": {
                "video": "/dev/video0",
                "audio": "default"
            }
        }
    }

def load_config():
    cfg = default_config()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Actualizar campos conservando defaults para claves faltantes
                for k, v in saved.items():
                    if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
        except Exception as e:
            print(f"[CONFIG] Error al cargar config.json: {e}")
    return cfg

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[CONFIG] Error al guardar config.json: {e}")
        return False
