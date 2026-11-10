#!/usr/bin/env python3
"""
==============================================================================
MeetLAN - Sistema Completo de Videollamadas P2P en Red de Área Local
Comunicaciones Multimedia - Facultad de Ingeniería, Universidad de Cuenca
==============================================================================
Características:
- Descubrimiento P2P automático en LAN mediante saludos iniciales
- Control de llamadas con alerta sonora y aceptación/rechazo obligatorio
- Transmisión y recepción en tiempo real (H.264 + AAC sobre MPEG-TS UDP)
- Vista Picture-in-Picture (PiP): Flujo remoto de fondo + cámara propia en esquina
- Panel de configuración completo para parámetros de FFmpeg / FFplay
- Compatibilidad multiplataforma: Windows 10/11 y GNU/Linux Ubuntu
==============================================================================
"""

import sys
import os
import tkinter as tk

# Asegurar que el directorio del script esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui_main import MeetLANApp

def main():
    root = tk.Tk()
    app = MeetLANApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
