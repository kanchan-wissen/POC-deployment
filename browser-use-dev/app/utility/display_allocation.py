import subprocess

import psutil


VNC_PORTS={}
VNC_DISPLAYS={}
USED_PORTS=set()
USED_DISPLAY=set()
def get_next_display_port():
    base_display = 100  # Xvfb :100, :101, etc.
    base_port = 6080
    for i in range(1, 100):
        display_num = base_display + i
        port = base_port + i
        if display_num not in USED_DISPLAY and port not in USED_PORTS:
            USED_DISPLAY.add(display_num)
            USED_PORTS.add(port)

            return display_num, port
    raise Exception("No available VNC displays/ports")
def start_novnc_proxy(vnc_port: int, web_port: int):
    subprocess.Popen([
        "websockify", str(web_port), f"localhost:{vnc_port}",
        "--web", "/usr/share/novnc",
        "--cert=/dev/null"  # remove if you have SSL certs
    ])
def start_vnc_session(display_num: int, port: int):
    display = f":{display_num}"
    screen = "1280x720x24"
    subprocess.Popen(["Xvfb", display, "-screen", "0", screen])
    subprocess.Popen(["x11vnc", "-display", display, "-nopw", "-forever", "-rfbport", str(port)])
    return display

def cleanup_session_processes(display_num: int):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any(f":{display_num}" in arg for arg in cmdline):
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
