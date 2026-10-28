"""Abre un video en Chrome/Edge sin ventana para exportarlo a MP4 o sacar capturas, todo por terminal.

Uso:
  python herramientas/navegador.py exportar <carpeta-del-video>
  python herramientas/navegador.py capturas <carpeta-del-video> 3,40.5,120
  VIDEOS_PARAMS="palabra=luz" python herramientas/navegador.py exportar 20-generativo/semilla   (parámetros extra)
  VIDEOS_TRAMO=10 python herramientas/navegador.py exportar <carpeta>   (por tramos de 10 s, reanudable: si un tramo se
                                                                         cuelga sólo se repite ése; une y pega el audio)
  VIDEOS_SIN_AVANCE=300  segundos sin cuadros nuevos antes de dar el exporte por colgado (180 en cada tramo)

Levanta herramientas/servidor.py si no está corriendo, espera a que termine y muestra los errores
de consola de la página (si hay). Sale con código 1 si hubo errores o si no terminó a tiempo.
Resultados (la técnica va en el nombre, p. ej. 01-html-canvas_red-neuronal):
  render/<tecnica>_<video>.mp4  ·  render/capturas/<tecnica>_<video>_<t>.jpg
"""
import os
import shutil
import json
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


def tramos(video, tramo):
    """Exporta por tramos reanudables y los une (VIDEOS_TRAMO=<segundos>, p. ej. 10). Cada tramo es una exportación
    normal (su navegador, su servidor y su vigilante): si uno se cuelga sólo se repite ése, y al volver a correr el
    mismo comando continúa donde quedó. El audio entero se pega al final. La duración sale del audio de la carpeta
    (o de VIDEOS_DURACION); VIDEOS_SALIDA cambia el nombre del MP4 final. Los tramos hechos pasan a render/tramos/."""
    from urllib.parse import parse_qs
    t0 = time.time()
    nombre = video.replace("/", "_")
    carpeta = RAIZ / video
    audio = next((carpeta / n for n in ("mezcla.wav", "narracion.wav", "musica.wav") if (carpeta / n).exists()), None)
    dur = float(os.environ.get("VIDEOS_DURACION") or 0)
    if not dur and audio:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(audio)], capture_output=True, text=True).stdout)
    if not dur:
        sys.exit("No hay audio para medir la duración: pasa VIDEOS_DURACION=<segundos>.")
    base = os.environ.get("VIDEOS_PARAMS", "")
    fps = int(parse_qs(base).get("fps", ["30"])[0])
    n = int(-(-dur // tramo))
    final = os.environ.get("VIDEOS_SALIDA") or nombre
    # cada salida con sus propios tramos: si el vertical se cortaba a medias, el horizontal de la misma carpeta
    # (VIDEOS_SALIDA=<nombre>_horizontal) reusaba sus tramos y salía mezclado
    etiqueta = "" if final == nombre else (final[len(nombre) + 1:] if final.startswith(nombre + "_") else final) + "-"
    hechos = []
    for k in range(n):
        p = f"{etiqueta}p{k:03d}"
        a = k * tramo
        # el reproductor incluye el cuadro final de su tramo: el tramo termina un cuadro antes de donde empieza el siguiente
        b = dur if k == n - 1 else ((k + 1) * tramo * fps - 1.5) / fps
        marca, mp4 = RENDER / f"{nombre}_{p}.listo", RENDER / f"{nombre}_{p}.mp4"
        for intento in (1, 2):
            if marca.exists():                                  # ya hecho (reanuda)
                break
            env = dict(os.environ, VIDEOS_PARTE=p, VIDEOS_SIN_AVANCE=os.environ.get("VIDEOS_SIN_AVANCE", "180"),
                       VIDEOS_PARAMS=f"{base}{'&' if base else ''}desde={a:g}&hasta={b:.6f}&parte={p}&sin_audio=1")
            print(f"tramo {p} ({a:g}–{b:.2f} s), intento {intento}", flush=True)
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "exportar", video], env=env)
        if not marca.exists():
            sys.exit(f"El tramo {p} no terminó en 2 intentos: vuelve a correr el mismo comando para continuar desde ahí.")
        r = json.loads(marca.read_text(encoding="utf-8"))
        if not r.get("cuadros"):                                # el tramo quedó fuera de la duración de la página
            break
        if not r.get("ok"):
            sys.exit(f"El tramo {p} dio error al codificar: {marca}")
        hechos.append((mp4, r["cuadros"]))
    salida, lista = RENDER / f"{final}.mp4", RENDER / f"{nombre}_{etiqueta}tramos.txt"
    lista.write_text("".join(f"file '{m.as_posix()}'\n" for m, _ in hechos), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista)]
    cmd += (["-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest"] if audio else ["-c", "copy"])
    subprocess.run(cmd + ["-movflags", "+faststart", str(salida)], check=True)
    total = sum(c for _, c in hechos)
    (RENDER / f"{final}.listo").write_text(json.dumps({"ok": True, "salida": str(salida), "cuadros": total,
                                                       "tramos": len(hechos)}), encoding="utf-8")
    destino = RENDER / "tramos" / final
    destino.mkdir(parents=True, exist_ok=True)
    for m, _ in hechos + [(lista, 0)]:
        for f in (m, m.with_suffix(".listo")):
            if f.exists(): shutil.move(str(f), str(destino / f.name))
    print(f"exportar: listo en {time.time() - t0:.0f} s ({len(hechos)} tramos de {tramo:g} s, {total} cuadros) → {salida}")
    sys.exit(0)


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("exportar", "capturas"):
        sys.exit(__doc__)
    modo, video = sys.argv[1], sys.argv[2].strip("/\\").replace("\\", "/")
    if modo == "exportar" and os.environ.get("VIDEOS_TRAMO") and not os.environ.get("VIDEOS_PARTE"):
        tramos(video, float(os.environ["VIDEOS_TRAMO"]))
    global PUERTO
    if "VIDEOS_PUERTO" not in os.environ:
        # Cada corrida con su propio servidor en un puerto libre: dos exportes (o un exporte y las pruebas de
        # otro agente) en el mismo servidor se roban los cuadros, y dos corridas de capturas se cortaban por la
        # marca compartida. La marca de capturas ahora lleva el puerto.
        import socket
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            PUERTO = s.getsockname()[1]
    nombre = video.replace("/", "_")   # igual que el servidor: la técnica va en el nombre
    if os.environ.get("VIDEOS_PARTE"):  # exportar por tramos: VIDEOS_PARAMS="desde=0&hasta=65&parte=p1" VIDEOS_PARTE=p1
        nombre += "_" + os.environ["VIDEOS_PARTE"]
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
        marca = RENDER / "capturas" / f".listo-{PUERTO}"
        url = f"http://localhost:{PUERTO}/{video}/?capturas={sys.argv[3]}{extra}"
        limite = 300
    marca.unlink(missing_ok=True)
    perfil = tempfile.mkdtemp(prefix="videos-nav-")
    # un registro por corrida (con su puerto): con uno compartido, el error de una corrida abortaba las de otros agentes
    log = RENDER / f"navegador-{modo}-{PUERTO}.log"
    RENDER.mkdir(exist_ok=True)
    # Sin --disable-gpu: la técnica 3D necesita WebGL. Si no hay GPU, Chrome cae a SwiftShader.
    cmd = [navegador(), "--headless=new", "--enable-unsafe-swiftshader", "--hide-scrollbars", "--mute-audio",
           "--window-size=1920,1080", "--disable-background-timer-throttling",
           "--disable-renderer-backgrounding", "--enable-logging=stderr", "--log-level=0",
           f"--user-data-dir={perfil}", url]
    # VIDEOS_CHROME_ARGS: parámetros extra de Chrome. En esta laptop Chrome usa la Intel integrada. Con
    # "--use-angle=vulkan --enable-features=Vulkan" toma la NVIDIA (más rápido en capturas cortas), pero **NO PARA
    # EXPORTAR**: en exportes largos deja texturas negras, fondos faltantes y cuelgues sin avisar (15 exportes
    # seguidos con Vulkan salieron con defectos; con la Intel, bien). Vulkan sólo para pruebas cortas.
    cmd[1:1] = os.environ.get("VIDEOS_CHROME_ARGS", "").split()
    t0 = time.time()
    # Exporte sin avance (el servidor no recibe cuadros nuevos) = colgado: se corta en minutos y no al cabo de la
    # hora (pasó: tres colgados, dos de ellos de 3.600 s cada uno). VIDEOS_SIN_AVANCE son los segundos sin cuadros
    # nuevos que se toleran. Se cuentan los cuadros y no el tamaño del MP4: el archivo se escribe por bloques de
    # 256 KB y en una escena quieta con la máquina cargada un bloque tarda más que eso (falso colgado).
    sin_avance = int(os.environ.get("VIDEOS_SIN_AVANCE", "300"))
    tam, t_tam, colgado = -1, time.time(), False
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        nav = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        while not marca.exists() and time.time() - t0 < limite:
            time.sleep(1)
            # si la página tiró un error, no tiene sentido seguir esperando
            if "Uncaught" in log.read_text(encoding="utf-8", errors="replace"):
                break
            if modo == "exportar":
                try:
                    with urllib.request.urlopen(f"http://localhost:{PUERTO}/export/estado", timeout=5) as r:
                        t = json.loads(r.read())["cuadros"]
                except Exception:
                    t = tam                                    # el servidor no contestó: cuenta como sin avance
                if t != tam:
                    tam, t_tam = t, time.time()
                elif time.time() - t_tam > sin_avance:
                    colgado = True
                    break
        nav.kill()
    if srv:
        srv.kill()
    shutil.rmtree(perfil, ignore_errors=True)
    consola = [l.strip() for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
               if "CONSOLE" in l and ("Uncaught" in l or "Error" in l or "error" in l)]
    estado = "listo" if marca.exists() else (f"COLGADO (sin cuadros nuevos en {sin_avance} s)" if colgado else "NO TERMINÓ")
    print(f"{modo}: {estado} en {time.time() - t0:.0f} s")
    if marca.exists():
        print(marca.read_text(encoding="utf-8"))
    for l in consola:
        print("error de consola:", l)
    if marca.exists() and not consola:
        try:
            log.unlink(missing_ok=True)             # el registro sólo queda cuando hubo un problema que mirar
        except OSError:
            pass                                    # Chrome todavía lo tiene abierto (Windows): queda, no es un fallo
    sys.exit(0 if marca.exists() and not consola else 1)


if __name__ == "__main__":
    main()
