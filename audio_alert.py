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

    def start_ringing(self):
        if self.ringing:
            return
        self.ringing = True
        self.ring_thread = threading.Thread(target=self._ring_worker, daemon=True)
        self.ring_thread.start()

    def stop_ringing(self):
        self.ringing = False

    def _ring_worker(self):
        is_win = platform.system() == "Windows"
        while self.ringing:
            try:
                # 1. Intentar tono senoidal puro mediante FFplay lavfi (880 Hz)
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
                
                # Esperar hasta que termine o hasta que se detenga la llamada
                while proc.poll() is None:
                    if not self.ringing:
                        proc.terminate()
                        return
                    time.sleep(0.05)
                
                # Pausa entre timbrazos (cadencia de timbre telefónico)
                for _ in range(10):
                    if not self.ringing:
                        return
                    time.sleep(0.06)

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
