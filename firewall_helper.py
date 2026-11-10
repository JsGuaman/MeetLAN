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
    
    # ÚNICAMENTE se configuran los puertos seleccionados por el usuario
    # Evita abrir puertos innecesarios para máxima seguridad y mínima exposición
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
    Abre las reglas en Ubuntu, Debian y Kali Linux de forma segura y sin error 127.
    """
    try:
        ports_str = ", ".join(str(p) for p in ports)

        # 1. Detectar distribución Linux
        distro = "Linux"
        if os.path.isfile("/etc/os-release"):
            try:
                with open("/etc/os-release", "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    if "kali" in content:
                        distro = "Kali Linux"
                    elif "ubuntu" in content:
                        distro = "Ubuntu"
                    elif "debian" in content:
                        distro = "Debian"
            except Exception:
                pass

        # 2. Localizar binario ufw en rutas estándar
        ufw_bin = None
        for candidate in ["/usr/sbin/ufw", "/sbin/ufw", "/usr/bin/ufw"]:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                ufw_bin = candidate
                break
        if not ufw_bin:
            ufw_bin = shutil.which("ufw")

        # CASO A: En Kali Linux (o sistemas sin UFW instalado)
        if not ufw_bin:
            # Comprobar si se ejecuta como root (común en Kali) y añadir reglas iptables si iptables existe
            is_root = (hasattr(os, "geteuid") and os.geteuid() == 0)
            iptables_bin = None
            for candidate in ["/usr/sbin/iptables", "/sbin/iptables", "/usr/bin/iptables"]:
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    iptables_bin = candidate
                    break

            if iptables_bin and is_root:
                for p in ports:
                    # Verificar si ya existe antes de insertar
                    check_cmd = [iptables_bin, "-C", "INPUT", "-p", "udp", "--dport", str(p), "-j", "ACCEPT"]
                    if subprocess.run(check_cmd, capture_output=True).returncode != 0:
                        subprocess.run([iptables_bin, "-I", "INPUT", "-p", "udp", "--dport", str(p), "-j", "ACCEPT"], capture_output=True)
                return True, (
                    f"🛡️ {distro} (Modo Root detectado):\n\n"
                    f"Reglas iptables añadidas con éxito para tráfico UDP en puertos: {ports_str}.\n"
                    f"¡Tus puertos están 100% abiertos y operativos!"
                )

            # En Kali Linux por defecto, la política del kernel en INPUT es ACCEPT
            return True, (
                f"ℹ️ Sistema detectado: {distro}\n\n"
                f"En {distro}, el cortafuegos UFW no viene instalado por defecto y la "
                f"política de red del kernel Linux para tráfico entrante es ACCEPT.\n\n"
                f"✅ Tus puertos UDP ({ports_str}) están totalmente ABIERTOS por defecto a nivel de kernel.\n\n"
                f"💡 ¡No necesitas configurar nada más, tu videollamada funcionará sin bloqueos!"
            )

        # CASO B: UFW sí está instalado. Ejecutamos las reglas directamente sobre el binario ufw.
        pkexec_bin = shutil.which("pkexec") or (
            "/usr/bin/pkexec" if os.path.isfile("/usr/bin/pkexec") else None
        )

        success = True
        err_details = []

        for p in ports:
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
            return True, f"Reglas UFW aplicadas exitosamente en {distro} para puertos UDP: {ports_str}."
        else:
            return False, (
                f"Se requiere elevación de permisos para modificar UFW en {distro}.\n\n"
                f"Para habilitar los puertos en UFW, ejecuta en tu terminal:\n"
                f"sudo ./abrir_firewall_linux.sh\n\n"
                f"(Detalle: {'; '.join(filter(None, err_details)) or 'Autenticación cancelada'})"
            )

    except Exception as e:
        return False, f"Error al verificar Firewall en Linux: {e}"
