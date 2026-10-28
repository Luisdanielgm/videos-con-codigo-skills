"""Renderiza una escena de motor_manim con ManimGX (Rust + wgpu) y deja un MP4 de cuadros fijos.

Uso:  python herramientas/render_gx.py <escena.py> <Clase> [-o salida.mp4] [--fps 30] [-r 1920x1080] [--crf 18]
      python herramientas/render_gx.py --probar        (ok o FALLA por caso)

La escena es la misma que corre con ManimCE (`from motor_manim import *`): aquí se lanza con el Python del venv de ManimGX
y VIDEOS_MOTOR=gx. Diferencias con `python -m manim render`:
  · ManimGX escribe un MP4 de cuadros VARIABLES (se salta los cuadros quietos): 343,7 s salieron en 9.579 cuadros y no en
    10.311. Los reproductores y `mezclar.py` esperan cuadros fijos, así que se pasa a 30 fps fijos (los cuadros quietos se
    repiten) y el audio se copia tal cual. El MP4 de ManimGX queda al lado como `<salida>.gx.mp4`.
  · Escribe también un storyboard (un cuadro por `play`, con los problemas de maquetación marcados): `<Clase>.storyboard-N.png`.
  · No hay `-n` (render por tramos) ni caché: la escena entera cada vez (134 s para la de 5:44 con la PC cargada).
  · Typst en lugar de LaTeX; `Union` y CJK no funcionan en el navegador. `self.say` manda texto a fal.ai: no se usa.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from color_mp4 import COLOR_709

RAIZ = Path(__file__).resolve().parent.parent
PY_GX = Path(os.environ.get("VIDEOS_VENV_GX", r"<venv-manimgx>")) / "Scripts" / "python.exe"


def sonda(ruta):
    """(duración s, cuadros, intervalos distintos entre cuadros) del video de un MP4."""
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                   "stream=duration,nb_frames", "-of", "json", str(ruta)], capture_output=True, check=True).stdout)
    pts = sorted(float(x) for x in subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "packet=pts_time", "-of", "csv=p=0", str(ruta)],
        capture_output=True, check=True, text=True).stdout.split())
    saltos = {round(b - a, 3) for a, b in zip(pts, pts[1:])}
    return float(j["streams"][0]["duration"]), int(j["streams"][0]["nb_frames"]), saltos


def a_cuadros_fijos(entrada, salida, fps=30, crf=18):
    """Repite los cuadros quietos hasta tener exactamente fps por segundo; el audio no se toca."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(entrada), "-vf", f"fps={fps}", "-fps_mode", "cfr",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", "fast", "-c:a", "copy",
                    *COLOR_709, str(salida)], check=True)


def renderizar(escena, clase, salida, fps=30, res="1920x1080", crf=18):
    escena, salida = Path(escena).resolve(), Path(salida).resolve()
    if not PY_GX.exists():
        raise SystemExit(f"no está el venv de ManimGX ({PY_GX}); VIDEOS_VENV_GX lo cambia")
    crudo = salida.with_suffix(".gx.mp4")
    env = {**os.environ, "VIDEOS_MOTOR": "gx", "PYTHONUTF8": "1",
           "PYTHONPATH": str(RAIZ / "herramientas") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    subprocess.run([str(PY_GX), "-m", "manimgx", "render", str(escena), clase, "-o", str(crudo), "--fps", str(fps),
                    "-r", res, "--crf", "14"], check=True, env=env, cwd=escena.parent)
    a_cuadros_fijos(crudo, salida, fps, crf)
    return salida


MICRO = '''import sys
sys.path.insert(0, {herr!r})
from motor_manim import *
class Micro(Explicativo):
    CARPETA = Path(__file__).resolve().parent
    PORTADA = False
    def construct(self):
        a = tx("hola", 40)
        self.aparece(a)
        self.en("a", .5)
        self.play(a.animate.shift(RIGHT * 2), run_time=1)
        self.wait(1.2)
'''


def probar():
    casos = []
    def caso(bien, texto):
        casos.append(bien)
        print(f"  {'ok' if bien else 'FALLA'}  {texto}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 1) la conversión: un video con cuadros que faltan (como el de ManimGX) sale con intervalos todos iguales
        vfr = tmp / "vfr.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=30:duration=4",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-vf",
                        "select='lt(mod(n\\,30)\\,8)+gte(mod(n\\,30)\\,22)'", "-fps_mode", "vfr",
                        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(vfr)], check=True)
        d0, n0, saltos0 = sonda(vfr)
        fijo = tmp / "fijo.mp4"
        a_cuadros_fijos(vfr, fijo)
        d1, n1, saltos1 = sonda(fijo)
        caso(len(saltos0) > 1, f"el video de prueba tiene cuadros variables (intervalos {sorted(saltos0)})")
        caso(saltos1 == {0.033} or saltos1 <= {0.033, 0.034}, f"tras la conversión todos los intervalos son iguales (dio {sorted(saltos1)})")
        caso(abs(n1 - round(d1 * 30)) <= 1 and abs(d1 - d0) < .1, f"{n1} cuadros para {d1:.2f} s (antes {n0} para {d0:.2f} s)")
        audio = lambda r: subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name,duration",
                                          "-of", "csv=p=0", str(r)], capture_output=True, text=True).stdout.strip()
        caso(audio(fijo) == audio(vfr) != "", f"el audio pasa sin tocarse (antes {audio(vfr)!r}, después {audio(fijo)!r})")
        # 2) de punta a punta: una escena de motor_manim con ManimGX, cuadros fijos, efectos.json escrito
        (tmp / "tiempos.json").write_text(json.dumps({"seg": {"a": {"inicio": 0.0, "dur": 2.0}}, "total": 3.2}), encoding="utf-8")
        (tmp / "escena.py").write_text(MICRO.format(herr=str(RAIZ / "herramientas")), encoding="utf-8")
        mp4 = renderizar(tmp / "escena.py", "Micro", tmp / "micro.mp4", fps=30, res="640x360")
        d, n, saltos = sonda(mp4)
        caso(abs(d - 3.2) < .25 and abs(n - round(d * 30)) <= 1 and len(saltos) <= 2,
             f"escena de motor_manim con ManimGX: {d:.2f} s, {n} cuadros, intervalos {sorted(saltos)}")
        efectos = json.loads((tmp / "efectos.json").read_text(encoding="utf-8")) if (tmp / "efectos.json").exists() else None
        caso(bool(efectos) and efectos[0]["archivo"].startswith("pop/"), f"efectos.json escrito con el sonido de aparece ({efectos and efectos[0]})")
    print(f"  {sum(casos)} ok, {len(casos) - sum(casos)} FALLA")
    return all(casos)


def main():
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    ap = argparse.ArgumentParser()
    ap.add_argument("escena"); ap.add_argument("clase")
    ap.add_argument("-o", "--salida"); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("-r", "--res", default="1920x1080"); ap.add_argument("--crf", type=float, default=18)
    o = ap.parse_args()
    salida = o.salida or str(Path(o.escena).resolve().with_name(o.clase + ".mp4"))
    print(renderizar(o.escena, o.clase, salida, o.fps, o.res, o.crf))


if __name__ == "__main__":
    main()
