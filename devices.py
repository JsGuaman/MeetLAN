"""
MeetLAN - Detector Automático de Dispositivos de Hardware (Cámaras y Micrófonos)
Comunicaciones Multimedia - Universidad de Cuenca
"""

import subprocess
import platform
import re
import os
import glob

def get_available_devices():
    """
    Retorna una tupla de listas: (video_devices, audio_devices)
    Cada elemento es un diccionario:
      {
         'display_name': Nombre visible en el menú desplegable (tipo Zoom),
         'ffmpeg_id': Identificador que usa FFmpeg para abrir el hardware,
         'is_default': booleano
      }
    """
    is_win = platform.system() == "Windows"
    
    if is_win:
        return _get_windows_devices()
    else:
        return _get_linux_devices()

def _get_windows_devices():
    video_devices = []
    audio_devices = []
    
    cmd = ["ffmpeg.exe", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        lines = res.stderr.splitlines()
        
        current_section = None
        last_dev = None
        
        for line in lines:
            line_str = line.strip()
            if "DirectShow video devices" in line_str:
                current_section = "video"
                continue
            elif "DirectShow audio devices" in line_str:
                current_section = "audio"
                continue
            
            if not current_section:
                continue
            
            # Buscar nombre entre comillas
            # Formato: [dshow @ ...]  "Nombre del Dispositivo" (video/audio)
            # o [dshow @ ...]   Alternative name "@device_..."
            m_alt = re.search(r'Alternative name\s+"([^"]+)"', line_str)
            if m_alt and last_dev:
                last_dev["alt_id"] = m_alt.group(1)
                # Para audio en Windows, preferir el alternative ID para evitar líos con tildes
                if current_section == "audio" and m_alt.group(1).startswith("@device"):
                    last_dev["ffmpeg_id"] = m_alt.group(1)
                continue
            
            m_name = re.search(r'"([^"]+)"', line_str)
            if m_name:
                dev_name = m_name.group(1)
                dev_obj = {
                    "display_name": dev_name,
                    "ffmpeg_id": dev_name,
                    "alt_id": dev_name,
                    "is_default": False
                }
                
                if current_section == "video":
                    video_devices.append(dev_obj)
                else:
                    audio_devices.append(dev_obj)
                
                last_dev = dev_obj
                
    except Exception as e:
        print(f"[DEVICES] Error detectando dispositivos Windows: {e}")
        
    # Fallback si no se detectó nada
    if not video_devices:
        video_devices.append({
            "display_name": "FaceTime HD Camera (Built-in)",
            "ffmpeg_id": "FaceTime HD Camera (Built-in)",
            "alt_id": "",
            "is_default": True
        })
        
    if not audio_devices:
        audio_devices.append({
            "display_name": "Auriculares con micrófono (ENVTWBUDS)",
            "ffmpeg_id": "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{F0032157-24DD-4BEB-8357-70A9E7997E47}",
            "alt_id": "",
            "is_default": True
        })
        audio_devices.append({
            "display_name": "Micrófono Integrado (Cirrus Logic)",
            "ffmpeg_id": "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{4A719366-ED8A-4363-908C-251F8B300B2E}",
            "alt_id": "",
            "is_default": False
        })
        
    return video_devices, audio_devices

def _get_linux_devices():
    video_devices = []
    audio_devices = []
    
    # 1. Detectar Video en Linux (V4L2)
    v4l2_paths = sorted(glob.glob("/sys/class/video4linux/video*"))
    for vpath in v4l2_paths:
        vnode = "/dev/" + os.path.basename(vpath)
        name_file = os.path.join(vpath, "name")
        vname = vnode
        if os.path.exists(name_file):
            try:
                with open(name_file, "r") as f:
                    vname = f.read().strip() + f" ({vnode})"
            except Exception:
                pass
        
        video_devices.append({
            "display_name": vname,
            "ffmpeg_id": vnode,
            "alt_id": vnode,
            "is_default": (vnode == "/dev/video0")
        })
        
    # Añadir siempre opción de cámara virtual de prueba (ideal para Kali en Máquinas Virtuales)
    video_devices.append({
        "display_name": "Cámara Virtual de Prueba (lavfi testsrc)",
        "ffmpeg_id": "lavfi:testsrc",
        "alt_id": "lavfi:testsrc",
        "is_default": (len(video_devices) == 0)
    })
        
    # 2. Detectar Audio en Linux (PulseAudio / PipeWire / ALSA)
    audio_devices.append({
        "display_name": "Micrófono Predeterminado (PulseAudio / PipeWire)",
        "ffmpeg_id": "pulse:default",
        "alt_id": "pulse:default",
        "is_default": True
    })
    
    # Intentar detectar fuentes PulseAudio vía pactl
    try:
        res = subprocess.run(["pactl", "list", "short", "sources"], capture_output=True, text=True, timeout=2)
        for line in res.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                src_name = parts[1]
                if "monitor" not in src_name:
                    audio_devices.append({
                        "display_name": f"Fuente PulseAudio: {src_name}",
                        "ffmpeg_id": f"pulse:{src_name}",
                        "alt_id": f"pulse:{src_name}",
                        "is_default": False
                    })
    except Exception:
        pass

    # Detectar dispositivos ALSA directamente (clave en Kali Linux si PulseAudio está inactivo)
    audio_devices.append({
        "display_name": "Micrófono Directo ALSA (default)",
        "ffmpeg_id": "alsa:default",
        "alt_id": "alsa:default",
        "is_default": False
    })

    try:
        res_alsa = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=2)
        for line in res_alsa.stdout.splitlines():
            m = re.search(r"card (\d+):.*\[(.*?)\], device (\d+):.*\[(.*?)\]", line)
            if m:
                card_num, card_name, dev_num, dev_name = m.groups()
                dev_id = f"hw:{card_num},{dev_num}"
                audio_devices.append({
                    "display_name": f"ALSA {card_name} ({dev_id})",
                    "ffmpeg_id": f"alsa:{dev_id}",
                    "alt_id": f"alsa:{dev_id}",
                    "is_default": False
                })
    except Exception:
        pass

    # Opción audio mudo de prueba
    audio_devices.append({
        "display_name": "Sin micrófono (Audio mudo de prueba lavfi)",
        "ffmpeg_id": "lavfi:anullsrc",
        "alt_id": "lavfi:anullsrc",
        "is_default": False
    })
        
    return video_devices, audio_devices

if __name__ == "__main__":
    v, a = get_available_devices()
    print("--- VIDEO DEVICES ---")
    for d in v:
        print(f" * {d['display_name']} -> {d['ffmpeg_id']}")
    print("\n--- AUDIO DEVICES ---")
    for d in a:
        print(f" * {d['display_name']} -> {d['ffmpeg_id']}")
