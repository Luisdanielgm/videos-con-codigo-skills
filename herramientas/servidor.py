"""Servidor local del proyecto: sirve los archivos y recibe cuadros para exportar o revisar.

Uso:  python herramientas/servidor.py [puerto]      (por omisión 8790)

- GET  /...                         archivos del proyecto.
- POST /export/inicio?video=<ruta>&fps=30   abre ffmpeg; el audio sale de <ruta>/mezcla.wav (o narracion.wav) si existe.
- POST /export/cuadro               un cuadro JPEG; va directo a ffmpeg (no se guarda en disco).
- POST /export/fin                  cierra ffmpeg; el MP4 queda en render/<nombre>.mp4.
- POST /captura?nombre=<x>          guarda un cuadro en render/capturas/<x>.jpg para revisarlo.
- POST /audio?video=<ruta>          guarda el WAV que generó la página como <ruta>/mezcla.wav (técnica 20).

Sólo usa la biblioteca estándar de Python y ffmpeg.
"""
import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent.parent
RENDER = RAIZ / "render"
estado = {"ffmpeg": None, "salida": None, "cuadros": 0}


class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(RAIZ), **k)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def responder(self, datos, codigo=200):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        cuerpo = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if url.path == "/export/inicio":
            if estado["ffmpeg"] and estado["ffmpeg"].poll() is None:  # una exportación anterior quedó a medias
                estado["ffmpeg"].kill()
            video = RAIZ / q["video"]
            RENDER.mkdir(exist_ok=True)
            # el nombre lleva la técnica: 01-html-canvas/red-neuronal → 01-html-canvas_red-neuronal.mp4
            salida = RENDER / f"{q['video'].strip('/').replace('/', '_')}.mp4"
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", q.get("fps", "30"),
                   "-c:v", "mjpeg", "-i", "-"]
            audio = video / "mezcla.wav"  # narración + ambiente (herramientas/sonido.py)
            if not audio.exists():
                audio = video / "narracion.wav"
            if not audio.exists():
                audio = video / "musica.wav"  # comerciales: la música por cálculo (herramientas/musica.py)
            if audio.exists():
                cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "160k"]
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-shortest", str(salida)]
            estado.update(ffmpeg=subprocess.Popen(cmd, stdin=subprocess.PIPE), salida=salida, cuadros=0)
            return self.responder({"ok": True, "salida": str(salida)})
        if url.path == "/export/cuadro":
            estado["ffmpeg"].stdin.write(cuerpo)
            estado["cuadros"] += 1
            return self.responder({"ok": True, "n": estado["cuadros"]})
        if url.path == "/export/fin":
            p = estado["ffmpeg"]
            p.stdin.close()
            codigo = p.wait()
            r = {"ok": codigo == 0, "salida": str(estado["salida"]), "cuadros": estado["cuadros"]}
            estado["salida"].with_suffix(".listo").write_text(json.dumps(r))
            return self.responder(r)
        if url.path == "/audio":  # técnica 20: la página genera su propia pista (WebAudio) y la deja como mezcla.wav
            destino = (RAIZ / q["video"] / "mezcla.wav").resolve()
            if RAIZ.resolve() not in destino.parents:
                return self.responder({"error": "fuera del proyecto"}, 400)
            destino.write_bytes(cuerpo)
            return self.responder({"ok": True, "bytes": len(cuerpo)})
        if url.path == "/captura":
            carpeta = RENDER / "capturas"
            carpeta.mkdir(parents=True, exist_ok=True)
            (carpeta / f"{q['nombre']}.jpg").write_bytes(cuerpo)
            return self.responder({"ok": True})
        if url.path == "/capturas/fin":
            (RENDER / "capturas" / ".listo").write_text(cuerpo.decode() or "{}")
            return self.responder({"ok": True})
        self.responder({"error": "ruta desconocida"}, 404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
    print(f"sirviendo {RAIZ} en http://localhost:{puerto}")
    # con hilos: un GET de un archivo no bloquea el envío de cuadros (la página los manda de a uno)
    ThreadingHTTPServer(("127.0.0.1", puerto), Manejador).serve_forever()
