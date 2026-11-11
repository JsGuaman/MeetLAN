"""
MeetLAN - Panel Flotante de Control de Videollamada en Curso
Comunicaciones Multimedia - Universidad de Cuenca
"""

import tkinter as tk
import time

class CallControlBar(tk.Toplevel):
    def __init__(self, parent, peer_info, on_hangup, on_change_quality=None):
        super().__init__(parent)
        self.peer_info = peer_info
        self.on_hangup = on_hangup
        self.on_change_quality = on_change_quality
        
        self.title("MeetLAN - Control de Llamada")
        
        # Posicionamiento dinámico adaptativo a la resolución de pantalla
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        bar_w = 480
        bar_h = 165
        x = max(10, (screen_w - bar_w) // 2)
        y = max(30, screen_h - bar_h - 70)
        self.geometry(f"{bar_w}x{bar_h}+{x}+{y}")
        self.resizable(False, False)
        self.configure(bg="#11111b")
        self.attributes("-topmost", True)
        
        self.start_time = time.time()
        self.is_running = True

        # Contenedor principal
        f = tk.Frame(self, bg="#11111b")
        f.pack(fill="both", expand=True, padx=12, pady=8)

        # Información del contacto y tiempo
        self.lbl_info = tk.Label(
            f,
            text=f"En llamada con: {peer_info.get('name', 'Compañero')} ({peer_info.get('ip', '')})",
            bg="#11111b",
            fg="#a6e3a1",
            font=("Segoe UI", 11, "bold")
        )
        self.lbl_info.pack(pady=1)

        self.lbl_timer = tk.Label(
            f,
            text="Duración: 00:00",
            bg="#11111b",
            fg="#cdd6f4",
            font=("Segoe UI", 10)
        )
        self.lbl_timer.pack(pady=1)

        # Selector rápido de calidad en vivo (ideal para pruebas y demostración al docente)
        q_frame = tk.Frame(f, bg="#11111b")
        q_frame.pack(pady=4)

        tk.Label(q_frame, text="Calidad:", bg="#11111b", fg="#89b4fa", font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 4))

        qualities = [
            ("Baja (100k)", "100k", 320, 240, "#fab387"),
            ("Media (300k)", "300k", 640, 480, "#89b4fa"),
            ("Alta (800k)", "800k", 640, 480, "#a6e3a1"),
            ("HD (1500k)", "1500k", 1280, 720, "#cba6f7")
        ]

        for label, br, w, h, col in qualities:
            btn = tk.Button(
                q_frame, text=label, bg="#313244", fg=col,
                font=("Segoe UI", 8, "bold"), relief="flat", padx=5, pady=2,
                command=lambda b=br, w_val=w, h_val=h: self._change_quality(b, w_val, h_val)
            )
            btn.pack(side="left", padx=2)

        # Botón de Colgar
        self.btn_hangup = tk.Button(
            f,
            text="Colgar Videollamada",
            bg="#f38ba8",
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            activebackground="#eba0ac",
            command=self._hangup_clicked
        )
        self.btn_hangup.pack(pady=3)

        # Capturar el cierre de ventana [X] para que siempre cuelgue y libere recursos
        self.protocol("WM_DELETE_WINDOW", self._hangup_clicked)

        # Loop de actualización del cronómetro
        self._update_timer()

    def _change_quality(self, bitrate, width, height):
        if self.on_change_quality:
            self.on_change_quality(bitrate, width, height)

    def _update_timer(self):
        if not self.is_running:
            return
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        try:
            self.lbl_timer.config(text=f"Duración: {mins:02d}:{secs:02d}")
            self.after(1000, self._update_timer)
        except Exception:
            pass

    def _hangup_clicked(self):
        if not self.is_running:
            return
        self.is_running = False
        try:
            self.btn_hangup.config(state="disabled", text=" Colgando... ")
        except Exception:
            pass
        if self.on_hangup:
            self.on_hangup()
        try:
            self.destroy()
        except Exception:
            pass

    def close_bar(self):
        self.is_running = False
        try:
            self.destroy()
        except Exception:
            pass
