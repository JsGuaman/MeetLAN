"""
MeetLAN - Sistema de Alerta Audible de Llamada Entrante
Comunicaciones Multimedia - Universidad de Cuenca
"""

import threading
import subprocess
import time
import platform

class RingtoneManager:
    def __init__(self):
        self.ringing = False
        self.ring_thread = None
        self.current_proc = None

    def start_ringing(self):
        if self.ringing:
            return
        self.ringing = True
        self.ring_thread = threading.Thread(target=self._ring_worker, daemon=True)
        self.ring_thread.start()

    def stop_ringing(self):
        self.ringing = False
        if self.current_proc and self.current_proc.poll() is None:
            try:
                self.current_proc.kill()
            except Exception:
                pass
        self.current_proc = None

    def _ring_worker(self):
        is_win = platform.system() == "Windows"
        while self.ringing:
            try:
                # 1. Intentar tono senoidal mediante FFplay lavfi (880 Hz)
                proc = subprocess.Popen(
                    [
                        "ffplay",
                        "-nodisp",
                        "-autoexit",
                        "-loglevel", "error",
                        "-f", "lavfi",
                        "-i", "sine=frequency=880:duration=0.5"
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.current_proc = proc
                
                # Esperar hasta que termine o hasta que se detenga la llamada
                while proc.poll() is None:
                    if not self.ringing:
                        proc.kill()
                        return
                    time.sleep(0.04)
                
                self.current_proc = None

                # Pausa entre timbrazos (cadencia de timbre telefónico)
                for _ in range(12):
                    if not self.ringing:
                        return
                    time.sleep(0.05)

            except Exception:
                # 2. Fallback nativo en Windows mediante winsound
                if is_win:
                    try:
                        import winsound
                        winsound.Beep(880, 500)
                        time.sleep(0.6)
                    except Exception:
                        pass
                else:
                    time.sleep(1.0)
