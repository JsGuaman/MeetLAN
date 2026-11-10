"""
MeetLAN - Módulo de Configuración y Persistencia
Comunicaciones Multimedia - Universidad de Cuenca
"""

import os
import json
import socket
import platform

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def get_local_ip():
    """Detecta la IP local de la interfaz activa (Wi-Fi preferida)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Conexión dummy para forzar resolución de interfaz activa
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
                "audio": "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{F0032157-24DD-4BEB-8357-70A9E7997E47}",
                "audio_friendly": "Auriculares con micrófono (ENVTWBUDS Hands-Free AG Audio)"
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
