"""
MeetLAN - Motor Multimedia FFmpeg/FFplay con Picture-in-Picture (PiP)
Comunicaciones Multimedia - Universidad de Cuenca
"""

import subprocess
import platform
import os
import signal
import time

class MediaEngine:
    def __init__(self, config):
        self.config = config
        self.is_win = platform.system() == "Windows"
        
        self.tx_process = None
        self.rx_process = None
        self.pip_process = None
        self.is_running = False

    def start_call(self, remote_ip, remote_port, local_rx_port):
        """
        Inicia simultáneamente:
        1. Transmisor TX hacia remote_ip:remote_port + split a local loopback 4000
        2. Receptor RX para el video remoto de fondo
        3. Previsualizador PiP para la cámara propia en la esquina inferior izquierda
        """
        self.stop_call()
        self.is_running = True
        
        # 1. Iniciar Transmisor (TX)
        self.tx_process = self._spawn_tx(remote_ip, remote_port)
        time.sleep(0.5)
        
        # 2. Iniciar Receptor Remoto (RX de fondo)
        self.rx_process = self._spawn_rx(local_rx_port)
        
        # 3. Iniciar PiP (Cámara propia en esquina inferior izquierda)
        time.sleep(0.5)
        self.pip_process = self._spawn_pip()

    def stop_call(self):
        """Detiene de forma limpia todos los procesos de video/audio."""
        self.is_running = False
        
        for p in [self.pip_process, self.rx_process, self.tx_process]:
            if p and p.poll() is None:
                try:
                    p.terminate()
                    p.wait(timeout=1.0)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass
        
        self.tx_process = None
        self.rx_process = None
        self.pip_process = None

    def _spawn_tx(self, remote_ip, remote_port):
        """Construye y ejecuta el comando FFmpeg para transmisión y split local."""
        bitrate = self.config.get("video_bitrate", "300k")
        maxrate = self.config.get("video_maxrate", "300k")
        bufsize = self.config.get("video_bufsize", "300k")
        fps = str(self.config.get("fps", 24))
        gop = str(self.config.get("gop", 24))
        preset = self.config.get("preset", "ultrafast")
        tune = self.config.get("tune", "zerolatency")
        pix_fmt = self.config.get("pix_fmt", "yuv420p")
        audio_b = self.config.get("audio_bitrate", "64k")
        local_pip_port = self.config.get("local_preview_port", 4000)
        
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]

        if self.is_win:
            win_devs = self.config.get("devices", {}).get("windows", {})
            v_dev = win_devs.get("video", "FaceTime HD Camera (Built-in)")
            a_dev = win_devs.get("audio", "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{F0032157-24DD-4BEB-8357-70A9E7997E47}")
            
            cmd.extend([
                "-rtbufsize", str(self.config.get("rtbufsize", "250M")),
                "-audio_buffer_size", str(self.config.get("audio_buffer_size_ms", 40)),
                "-framerate", fps,
                "-f", "dshow",
                "-use_video_device_timestamps", "false",
                "-i", f"video={v_dev}:audio={a_dev}"
            ])
        else:
            # GNU/Linux (Ubuntu / Debian / Kali Linux)
            lin_devs = self.config.get("devices", {}).get("linux", {})
            v_dev = lin_devs.get("video", "/dev/video0")
            raw_a = lin_devs.get("audio", "pulse:default")
            w = str(self.config.get("width", 640))
            h = str(self.config.get("height", 480))
            
            # 1. Configuración de Entrada de Video (V4L2 o lavfi de prueba en VMs de Kali)
            if v_dev.startswith("lavfi:") or not os.path.exists(v_dev):
                print(f"[ENGINE TX] Usando cámara virtual de prueba lavfi testsrc (nodo {v_dev} ausente)")
                cmd.extend([
                    "-f", "lavfi",
                    "-i", f"testsrc=size={w}x{h}:rate={fps}"
                ])
            else:
                cmd.extend([
                    "-thread_queue_size", "1024",
                    "-f", "v4l2",
                    "-video_size", f"{w}x{h}",
                    "-framerate", fps,
                    "-i", v_dev
                ])

            # 2. Configuración de Entrada de Audio (PulseAudio / ALSA / lavfi)
            if raw_a.startswith("lavfi:") or raw_a == "none":
                cmd.extend([
                    "-f", "lavfi",
                    "-i", "anullsrc=channel_layout=mono:sample_rate=44100"
                ])
            elif raw_a.startswith("alsa:"):
                alsa_target = raw_a.split(":", 1)[1]
                cmd.extend([
                    "-thread_queue_size", "1024",
                    "-f", "alsa",
                    "-i", alsa_target
                ])
            elif raw_a.startswith("pulse:"):
                pulse_target = raw_a.split(":", 1)[1]
                cmd.extend([
                    "-thread_queue_size", "1024",
                    "-f", "pulse",
                    "-i", pulse_target
                ])
            elif raw_a.startswith("hw:") or raw_a.startswith("plughw:"):
                cmd.extend([
                    "-thread_queue_size", "1024",
                    "-f", "alsa",
                    "-i", raw_a
                ])
            else:
                cmd.extend([
                    "-thread_queue_size", "1024",
                    "-f", "pulse",
                    "-i", raw_a
                ])

        # Filtro Split: 1 flujo para enviar a la red, 1 flujo miniatura local
        filter_str = "[0:v]split=2[tx_v][local_v]; [local_v]scale=220:165[pip_v]"
        cmd.extend(["-filter_complex", filter_str])

        # Salida 1: Flujo a la red para el compañero (H.264 + AAC MPEG-TS UDP)
        remote_url = f"udp://{remote_ip}:{remote_port}?pkt_size={self.config.get('pkt_size', 1316)}"
        cmd.extend([
            "-map", "[tx_v]",
            "-map", "0:a?",
            "-vcodec", "libx264",
            "-pix_fmt", pix_fmt,
            "-b:v", bitrate,
            "-maxrate", maxrate,
            "-bufsize", bufsize,
            "-r", fps,
            "-g", gop,
            "-tune", tune,
            "-preset", preset,
            "-acodec", "aac",
            "-ac", "1",
            "-b:a", audio_b,
            "-af", "aresample=async=1:first_pts=0",
            "-f", "mpegts",
            "-muxdelay", "0",
            "-muxpreload", "0",
            "-flush_packets", "1",
            remote_url
        ])

        # Salida 2: Flujo local loopback para PiP
        local_url = f"udp://127.0.0.1:{local_pip_port}?pkt_size=1316"
        cmd.extend([
            "-map", "[pip_v]",
            "-vcodec", "mpeg4",
            "-b:v", "200k",
            "-r", "15",
            "-f", "mpegts",
            "-muxdelay", "0",
            "-flush_packets", "1",
            local_url
        ])

        print(f"[ENGINE TX] Ejecutando: {' '.join(cmd)}")
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _spawn_rx(self, local_rx_port):
        """Abre la ventana principal FFplay para el flujo remoto de fondo."""
        fifo = self.config.get("fifo_size", 0)
        rx_url = f"udp://0.0.0.0:{local_rx_port}?fifo_size={fifo}&overrun_nonfatal=1"

        # Ventana principal en el centro
        cmd = [
            "ffplay",
            "-window_title", "MeetLAN - Videollamada (Remoto)",
            "-x", "960",
            "-y", "720",
            "-left", "160",
            "-top", "60",
            "-probesize", "32",
            "-analyzeduration", "0",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-sync", "ext",
            "-f", "mpegts",
            rx_url
        ]
        print(f"[ENGINE RX] Ejecutando: {' '.join(cmd)}")
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _spawn_pip(self):
        """Abre la ventana flotante en la esquina inferior izquierda (PiP)."""
        local_pip_port = self.config.get("local_preview_port", 4000)
        pip_url = f"udp://127.0.0.1:{local_pip_port}?fifo_size=0&overrun_nonfatal=1"

        # Esquina inferior izquierda sobre la ventana principal
        # left = 180, top = 590 (dentro de la ventana de 960x720)
        cmd = [
            "ffplay",
            "-window_title", "MeetLAN - Mi Camara (PiP)",
            "-x", "220",
            "-y", "165",
            "-left", "180",
            "-top", "590",
            "-alwaysontop",
            "-noborder",
            "-probesize", "32",
            "-analyzeduration", "0",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-sync", "ext",
            "-f", "mpegts",
            pip_url
        ]
        print(f"[ENGINE PiP] Ejecutando: {' '.join(cmd)}")
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
