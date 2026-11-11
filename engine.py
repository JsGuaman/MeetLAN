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
        self.tx_log = None
        self.rx_log = None
        self.pip_log = None

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
        time.sleep(0.15)
        
        # 2. Iniciar Receptor Remoto (RX de fondo)
        self.rx_process = self._spawn_rx(local_rx_port)
        
        # 3. Iniciar PiP (Cámara propia en esquina inferior izquierda)
        time.sleep(0.15)
        self.pip_process = self._spawn_pip()

        # 4. Verificación de estabilidad inicial
        time.sleep(0.3)
        if self.tx_process and self.tx_process.poll() is not None:
            print(f"[ENGINE ERROR] FFmpeg TX se detuvo prematuramente con código {self.tx_process.returncode}!")
            try:
                with open("ffmpeg_tx.log", "r", encoding="utf-8", errors="replace") as lf:
                    lines = lf.readlines()[-15:]
                    print("".join(lines))
            except Exception:
                pass

    def restart_tx(self, remote_ip, remote_port):
        """Reinicia en caliente el transmisor TX con la nueva configuración sin cortar la llamada."""
        if not self.is_running:
            return
        print(f"[ENGINE] Reiniciando transmisor TX en caliente hacia {remote_ip}:{remote_port}...")
        if self.tx_process and self.tx_process.poll() is None:
            try:
                self.tx_process.kill()
                self.tx_process.wait(timeout=0.5)
            except Exception:
                pass
        if self.tx_log and self.tx_log != subprocess.DEVNULL:
            try:
                self.tx_log.close()
            except Exception:
                pass
        self.tx_process = self._spawn_tx(remote_ip, remote_port)

    def stop_call(self):
        """Detiene de forma limpia e instantánea todos los procesos de video/audio."""
        self.is_running = False
        
        procs = [self.pip_process, self.rx_process, self.tx_process]
        self.tx_process = None
        self.rx_process = None
        self.pip_process = None

        for p in procs:
            if p and p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass

        # Cerrar archivos de registro
        for lf in [self.tx_log, self.rx_log, self.pip_log]:
            if lf and lf != subprocess.DEVNULL:
                try:
                    lf.close()
                except Exception:
                    pass
        self.tx_log = None
        self.rx_log = None
        self.pip_log = None

        # Asegurar liberación inmediata de sockets y hardware de ffplay
        try:
            if self.is_win:
                subprocess.run(["taskkill", "/F", "/IM", "ffplay.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["killall", "-9", "ffplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

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
        # Sanitizar formato de píxel: libx264 requiere yuv420p / nv12 / yuvj420p (yuyv422 rompe el encoder H.264)
        if pix_fmt not in ["yuv420p", "nv12", "yuvj420p"]:
            pix_fmt = "yuv420p"

        w = int(self.config.get("width", 640))
        h = int(self.config.get("height", 480))
        # Garantizar dimensiones pares estrictas (evita error 'height not divisible by 2' en H.264)
        w = w if w % 2 == 0 else w + 1
        h = h if h % 2 == 0 else h + 1
        audio_b = self.config.get("audio_bitrate", "64k")
        local_pip_port = self.config.get("local_preview_port", 4000)
        
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]

        if self.is_win:
            win_devs = self.config.get("devices", {}).get("windows", {})
            v_dev = win_devs.get("video", "FaceTime HD Camera (Built-in)")
            a_dev = win_devs.get("audio", "")

            # Validación dinámica de dispositivos físicos disponibles en Windows
            try:
                from devices import get_available_devices
                det_v, det_a = get_available_devices()
                
                # Validar video
                if not any(d["ffmpeg_id"] == v_dev or d["display_name"] == v_dev for d in det_v) and det_v:
                    v_dev = det_v[0]["ffmpeg_id"]
                    print(f"[ENGINE TX] Cámara previa no encontrada, usando disponible: {det_v[0]['display_name']}")
                    
                # Validar audio contra hardware actualmente conectado
                matched_a = any(d["ffmpeg_id"] == a_dev or d["display_name"] == a_dev or d.get("alt_id") == a_dev for d in det_a)
                if not matched_a and det_a:
                    print(f"[ENGINE TX] Micrófono previo desconectado. Conmutando a disponible: {det_a[0]['display_name']}")
                    a_dev = ""
                    for d in det_a:
                        d_low = d["display_name"].lower()
                        if "cirrus" in d_low or "integrado" in d_low or "realtek" in d_low or "interno" in d_low:
                            a_dev = d["ffmpeg_id"]
                            break
                    if not a_dev:
                        a_dev = det_a[0]["ffmpeg_id"]
            except Exception as e:
                print(f"[ENGINE TX] Aviso de hardware de audio: {e}")

            if not v_dev:
                v_dev = "FaceTime HD Camera (Built-in)"
            
            cmd.extend([
                "-rtbufsize", str(self.config.get("rtbufsize", "250M")),
                "-audio_buffer_size", str(self.config.get("audio_buffer_size_ms", 40)),
                "-framerate", fps,
                "-f", "dshow",
                "-use_video_device_timestamps", "false",
                "-i", f"video={v_dev}:audio={a_dev}" if a_dev else f"video={v_dev}"
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
                    "-thread_queue_size", "32",
                    "-f", "v4l2",
                    "-use_wallclock_as_timestamps", "1",
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
                    "-thread_queue_size", "32",
                    "-f", "alsa",
                    "-i", alsa_target
                ])
            elif raw_a.startswith("pulse:"):
                pulse_target = raw_a.split(":", 1)[1]
                cmd.extend([
                    "-thread_queue_size", "32",
                    "-f", "pulse",
                    "-i", pulse_target
                ])
            elif raw_a.startswith("hw:") or raw_a.startswith("plughw:"):
                cmd.extend([
                    "-thread_queue_size", "32",
                    "-f", "alsa",
                    "-i", raw_a
                ])
            else:
                cmd.extend([
                    "-thread_queue_size", "32",
                    "-f", "pulse",
                    "-i", raw_a
                ])

        # Filtro Split: Escala a dimensiones pares y divide en flujo remoto y PiP local (220x164)
        filter_str = f"[0:v]scale={w}:{h},split=2[tx_v][local_v]; [local_v]scale=220:164[pip_v]"
        cmd.extend(["-filter_complex", filter_str])

        # Mapeo de Audio:
        # En Windows: DirectShow captura video y audio juntos en input 0 ("0:a?")
        # En Linux: Video es input 0 y Audio es input 1 ("1:a?")
        audio_map = "0:a?" if self.is_win else "1:a?"

        # Salida 1: Flujo a la red para el compañero (H.264 + AAC MPEG-TS UDP)
        remote_url = f"udp://{remote_ip}:{remote_port}?pkt_size={self.config.get('pkt_size', 1316)}"
        cmd.extend([
            "-map", "[tx_v]",
            "-map", audio_map,
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
            "-af", "aresample=async=1:first_pts=0,volume=2.5",
            "-f", "mpegts",
            "-muxdelay", "0",
            "-muxpreload", "0",
            "-flush_packets", "1",
            remote_url
        ])

        # Salida 2: Flujo local loopback para PiP (Previsualización ultra-rápida sin delay)
        local_url = f"udp://127.0.0.1:{local_pip_port}?pkt_size=1316"
        cmd.extend([
            "-map", "[pip_v]",
            "-vcodec", "libx264",
            "-pix_fmt", pix_fmt,
            "-b:v", "200k",
            "-threads", "1",
            "-r", fps,
            "-g", "12",
            "-tune", "zerolatency",
            "-preset", "ultrafast",
            "-f", "mpegts",
            "-muxdelay", "0",
            "-muxpreload", "0",
            "-flush_packets", "1",
            local_url
        ])

        print(f"[ENGINE TX] Ejecutando: {' '.join(cmd)}")
        try:
            self.tx_log = open("ffmpeg_tx.log", "w", encoding="utf-8", errors="replace")
        except Exception:
            self.tx_log = subprocess.DEVNULL
        return subprocess.Popen(cmd, stdout=self.tx_log, stderr=subprocess.STDOUT)

    def _spawn_rx(self, local_rx_port):
        """Abre la ventana principal FFplay para el flujo remoto de fondo."""
        fifo = self.config.get("fifo_size", 0)
        fifo_param = f"&fifo_size={fifo}" if fifo > 0 else ""
        rx_url = f"udp://0.0.0.0:{local_rx_port}?overrun_nonfatal=1{fifo_param}"

        # Ventana principal en el centro
        cmd = [
            "ffplay",
            "-window_title", "MeetLAN - Videollamada (Remoto)",
            "-x", "960",
            "-y", "720",
            "-left", "160",
            "-top", "60",
            "-probesize", "32768",
            "-analyzeduration", "0",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-f", "mpegts",
            rx_url
        ]
        print(f"[ENGINE RX] Ejecutando: {' '.join(cmd)}")
        try:
            self.rx_log = open("ffplay_rx.log", "w", encoding="utf-8", errors="replace")
        except Exception:
            self.rx_log = subprocess.DEVNULL
        return subprocess.Popen(cmd, stdout=self.rx_log, stderr=subprocess.STDOUT)

    def _spawn_pip(self):
        """Abre la ventana flotante en la esquina inferior izquierda (PiP)."""
        local_pip_port = self.config.get("local_preview_port", 4000)
        pip_url = f"udp://127.0.0.1:{local_pip_port}?overrun_nonfatal=1"

        # Esquina inferior izquierda sobre la ventana principal (solo video, sin audio)
        cmd = [
            "ffplay",
            "-window_title", "MeetLAN - Mi Camara (PiP)",
            "-x", "220",
            "-y", "164",
            "-left", "180",
            "-top", "590",
            "-noborder",
            "-an",
            "-probesize", "32768",
            "-analyzeduration", "0",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-f", "mpegts",
            pip_url
        ]
        if self.is_win:
            cmd.insert(cmd.index("-an"), "-alwaysontop")
        print(f"[ENGINE PiP] Ejecutando: {' '.join(cmd)}")
        try:
            self.pip_log = open("ffplay_pip.log", "w", encoding="utf-8", errors="replace")
        except Exception:
            self.pip_log = subprocess.DEVNULL
        return subprocess.Popen(cmd, stdout=self.pip_log, stderr=subprocess.STDOUT)
