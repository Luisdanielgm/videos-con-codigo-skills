"""Abre un video en Chrome/Edge sin ventana para exportarlo a MP4 o sacar capturas, todo por terminal.

Uso:
  python herramientas/navegador.py exportar <carpeta-del-video>
  python herramientas/navegador.py capturas <carpeta-del-video> 3,40.5,120
  VIDEOS_PARAMS="palabra=luz" python herramientas/navegador.py exportar 20-generativo/semilla   (parámetros extra)

Levanta herramientas/servidor.py si no está corriendo, espera a que termine y muestra los errores
de consola de la página (si hay). Sale con código 1 si hubo errores o si no terminó a tiempo.
Resultados (la técnica va en el nombre, p. ej. 01-html-canvas_red-neuronal):
  render/<tecnica>_<video>.mp4  ·  render/capturas/<tecnica>_<video>_<t>.jpg
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RENDER = RAIZ / "render"
PUERTO = int(os.environ.get("VIDEOS_PUERTO", "8790"))
CANDIDATOS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def navegador():
    for c in CANDIDATOS:
        if Path(c).exists() or shutil.which(c):
            return c
    sys.exit("No encontré Chrome, Chromium ni Edge.")


def servidor_arriba():
    try:
        urllib.request.urlopen(f"http://localhost:{PUERTO}/README.md", timeout=2)
        return True
    except Exception:
        return False


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("exportar", "capturas"):
        sys.exit(__doc__)
    modo, video = sys.argv[1], sys.argv[2].strip("/\\").replace("\\", "/")
    nombre = video.replace("/", "_")   # igual que el servidor: la técnica va en el nombre
    srv = None
    if not servidor_arriba():
        srv = subprocess.Popen([sys.executable, str(RAIZ / "herramientas" / "servidor.py"), str(PUERTO)])
        for _ in range(50):
            if servidor_arriba():
                break
            time.sleep(.2)
    extra = os.environ.get("VIDEOS_PARAMS", "")   # parámetros de la página, p. ej. palabra=luz (técnica 20)
    extra = "&" + extra if extra else ""
    if modo == "exportar":
        marca = RENDER / f"{nombre}.listo"
        url = f"http://localhost:{PUERTO}/{video}/?exportar{extra}"
        limite = 3600
    else:
        marca = RENDER / "capturas" / ".listo"
        url = f"http://localhost:{PUERTO}/{video}/?capturas={sys.argv[3]}{extra}"
        limite = 300
    marca.unlink(missing_ok=True)
    perfil = tempfile.mkdtemp(prefix="videos-nav-")
    log = RENDER / f"navegador-{modo}.log"
    RENDER.mkdir(exist_ok=True)
    # Sin --disable-gpu: la técnica 3D necesita WebGL. Si no hay GPU, Chrome cae a SwiftShader.
    cmd = [navegador(), "--headless=new", "--enable-unsafe-swiftshader", "--hide-scrollbars", "--mute-audio",
           "--window-size=1920,1080", "--disable-background-timer-throttling",
           "--disable-renderer-backgrounding", "--enable-logging=stderr", "--log-level=0",
           f"--user-data-dir={perfil}", url]
    t0 = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        nav = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        while not marca.exists() and time.time() - t0 < limite:
            time.sleep(1)
            # si la página tiró un error, no tiene sentido seguir esperando
            if "Uncaught" in log.read_text(encoding="utf-8", errors="replace"):
                break
        nav.kill()
    if srv:
        srv.kill()
    shutil.rmtree(perfil, ignore_errors=True)
    consola = [l.strip() for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
               if "CONSOLE" in l and ("Uncaught" in l or "Error" in l or "error" in l)]
    print(f"{modo}: {'listo' if marca.exists() else 'NO TERMINÓ'} en {time.time() - t0:.0f} s")
    if marca.exists():
        print(marca.read_text(encoding="utf-8"))
    for l in consola:
        print("error de consola:", l)
    sys.exit(0 if marca.exists() and not consola else 1)


if __name__ == "__main__":
    main()
