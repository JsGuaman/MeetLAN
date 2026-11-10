"""
MeetLAN - Gestor Integrado de Firewall y Verificación de Puertos
Comunicaciones Multimedia - Universidad de Cuenca
"""

import socket
import platform
import subprocess
import os
import sys
import shutil

def test_udp_port(port):
    """
    Comprueba si un puerto UDP está libre para escuchar en 0.0.0.0
    Retorna (True, "Puerto UDP [port] libre y disponible") o (False, "Detalle del error")
    """
    try:
        port = int(port)
        if port < 1024 or port > 65535:
            return False, f"Puerto {port} fuera de rango válido de usuario (1024-65535)."
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", port))
        s.close()
        return True, f"Puerto UDP {port} libre y disponible para usar."
    except OSError as e:
        err_str = str(e)
        if "10048" in err_str:
            return False, f"Puerto UDP {port} OCUPADO por otro proceso en Windows (ej. National Instruments / TimeSync)."
        elif "98" in err_str:
            return False, f"Puerto UDP {port} OCUPADO en Linux (Address already in use)."
        elif "10013" in err_str:
            return False, f"Puerto UDP {port} restringido por el sistema o requiere permisos elevados."
        return False, f"No se puede enlazar el puerto UDP {port}: {err_str}"
    except ValueError:
        return False, f"Valor de puerto no numérico: {port}"

def apply_firewall_rules(ports, config=None):
    """
    Abre los puertos configurados en el Firewall del sistema operativo
    directamente desde la interfaz gráfica sin usar consola manualmente.
    """
    is_win = platform.system() == "Windows"
    valid_ports = []
    for p in ports:
        try:
            val = int(p)
            if 1024 <= val <= 65535:
                valid_ports.append(val)
        except Exception:
            pass
    
    unique_ports = sorted(list(set(valid_ports)))
    if not unique_ports:
        return False, "No se proporcionaron puertos válidos para configurar."

    ports_str = ",".join(str(p) for p in unique_ports)

    if is_win:
        return _apply_windows_firewall(unique_ports, ports_str)
    else:
        return _apply_linux_firewall(unique_ports)

def _apply_windows_firewall(ports, ports_str):
    """
    Abre las reglas en Windows Defender Firewall solicitando elevación UAC nativa.
    Permite tanto los puertos UDP como los ejecutables ffplay y python.
    """
    try:
        commands = [
            f'netsh advfirewall firewall delete rule name="MeetLAN_UDP_Dynamic" >nul 2>&1',
            f'netsh advfirewall firewall add rule name="MeetLAN_UDP_Dynamic" dir=in action=allow protocol=UDP localport={ports_str} profile=any >nul'
        ]

        # También autorizar ffplay y python para evitar advertencias de Windows Defender
        ffplay_path = shutil.which("ffplay")
        if ffplay_path:
            commands.append(f'netsh advfirewall firewall delete rule name="MeetLAN_FFplay" >nul 2>&1')
            commands.append(f'netsh advfirewall firewall add rule name="MeetLAN_FFplay" dir=in action=allow program="{ffplay_path}" enable=yes profile=any >nul')

        python_path = sys.executable
        if python_path:
            commands.append(f'netsh advfirewall firewall delete rule name="MeetLAN_Python" >nul 2>&1')
            commands.append(f'netsh advfirewall firewall add rule name="MeetLAN_Python" dir=in action=allow program="{python_path}" enable=yes profile=any >nul')

        combined_cmd = " & ".join(commands)
        
        # Ejecutar mediante PowerShell con elevación UAC (RunAs)
        ps_script = f'$cmd = \'{combined_cmd}\'; Start-Process cmd -ArgumentList "/c $cmd" -Verb RunAs -Wait'
        
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True, text=True, timeout=25
        )
        return True, f"Reglas de Firewall configuradas exitosamente en Windows Defender para puertos UDP: {ports_str} y binarios (ffplay/python)."
    except Exception as e:
        return False, f"Error al solicitar permisos de Administrador en Windows: {e}"

def _apply_linux_firewall(ports):
    """
    Abre las reglas en Ubuntu (UFW) de forma segura y sin arrojar error 127.
    """
    try:
        ports_str = ", ".join(str(p) for p in ports)

        # 1. Localizar binario ufw en rutas estándar
        ufw_bin = None
        for candidate in ["/usr/sbin/ufw", "/sbin/ufw", "/usr/bin/ufw"]:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                ufw_bin = candidate
                break
        if not ufw_bin:
            ufw_bin = shutil.which("ufw")

        # CASO 1: UFW no está instalado en este sistema Linux
        if not ufw_bin:
            # En GNU/Linux, la política predeterminada del kernel iptables es ACCEPT.
            # Sin UFW instalado, no existe ningún cortafuegos bloqueando tráfico UDP.
            return True, (
                f"ℹ️ Firewall UFW no instalado en Linux:\n\n"
                f"En Ubuntu / Linux, cuando UFW no está instalado, el kernel NO bloquea ningún puerto.\n\n"
                f"✅ Tus puertos UDP ({ports_str}) están totalmente ABIERTOS por defecto y listos para transmitir y recibir video sin ninguna restricción.\n\n"
                f"💡 (Si deseas instalar UFW de todas formas, ejecuta en tu terminal: sudo apt update && sudo apt install -y ufw)"
            )

        # CASO 2: UFW sí está instalado. Ejecutamos las reglas directamente sobre el binario ufw.
        pkexec_bin = shutil.which("pkexec") or (
            "/usr/bin/pkexec" if os.path.isfile("/usr/bin/pkexec") else None
        )

        success = True
        err_details = []

        for p in ports:
            # Si pkexec está disponible, invocar directamente el binario ufw sin wrappers de shell que causen error 127
            if pkexec_bin:
                cmd = [pkexec_bin, ufw_bin, "allow", f"{p}/udp", "comment", "MeetLAN"]
            else:
                cmd = ["sudo", "-n", ufw_bin, "allow", f"{p}/udp", "comment", "MeetLAN"]

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                if res.returncode != 0:
                    success = False
                    err_details.append(res.stderr.strip() or res.stdout.strip())
            except Exception as e:
                success = False
                err_details.append(str(e))

        if success:
            return True, f"Reglas UFW aplicadas exitosamente para puertos UDP: {ports_str}."
        else:
            # Si la autenticación gráfica falló o fue cancelada
            return False, (
                f"Se requiere elevación de permisos para modificar UFW.\n\n"
                f"Para habilitar los puertos en UFW, ejecuta en tu terminal:\n"
                f"sudo ./abrir_firewall_linux.sh\n\n"
                f"(Detalle: {'; '.join(filter(None, err_details)) or 'Autenticación cancelada'})"
            )

    except Exception as e:
        return False, f"Error al verificar Firewall en Linux: {e}"
