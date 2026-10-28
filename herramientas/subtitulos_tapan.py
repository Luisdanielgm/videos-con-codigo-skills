"""Mide si los subtítulos quemados taparían algo del video (antes de quemarlos).

    .venv/Scripts/python herramientas/subtitulos_tapan.py <video-sin-subtitulos.mp4> <subtitulos.srt>
                          [--fondo F6EEFA] [--franja 0.74,0.97] [--umbral 0.004]

Para cada subtítulo toma un cuadro en la mitad de su duración y mira la franja de abajo donde irá la caja (por omisión del
74 % al 97 % del alto). Cuenta los píxeles que NO son del color de fondo: si pasan del umbral (fracción de la franja,
0,4 % por omisión), hay contenido ahí y el subtítulo lo taparía. Imprime los subtítulos que chocan con su tiempo y la
fracción ocupada, y deja una hoja con esos cuadros en render/critica/. Sale con código 1 si alguno choca.
El texto de los subtítulos queda siempre abajo: si choca, hay que subir ese contenido en la escena (o acortar el texto).
"""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")


def tiempo(s):
    h, m, r = s.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(r)


def leer_srt(p):
    cues = []
    for bloque in re.split(r"\n\s*\n", Path(p).read_text(encoding="utf-8-sig").strip()):
        l = bloque.strip().splitlines()
        if len(l) >= 3 and "-->" in l[1]:
            a, b = [tiempo(x.strip()) for x in l[1].split("-->")]
            cues.append((a, b, " ".join(l[2:])))
    return cues


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    mp4, srt = a[0], a[1]
    op = lambda n, d: a[a.index(n) + 1] if n in a else d
    fondo = op("--fondo", "F6EEFA").lstrip("#")
    f0, f1 = [float(x) for x in op("--franja", "0.74,0.97").split(",")]
    umbral = float(op("--umbral", "0.004"))
    bg = np.array([int(fondo[i:i + 2], 16) for i in (0, 2, 4)])
    w, h = 1280, 720
    y0, y1 = int(h * f0), int(h * f1)
    malos = []
    cues = leer_srt(srt)
    for a_, b_, txt in cues:
        t = (a_ + b_) / 2
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", mp4, "-frames:v", "1", "-vf",
                              f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) < w * h * 3:
            continue
        img = np.frombuffer(raw, np.uint8).reshape(h, w, 3).astype(int)[y0:y1]
        ocupado = float((np.abs(img - bg).sum(axis=2) > 40).mean())
        if ocupado > umbral:
            malos.append((t, ocupado, txt))
    print(f"{len(cues)} subtítulos, {len(malos)} chocan con contenido en la franja {f0:.0%}-{f1:.0%} (umbral {umbral:.1%}):")
    for t, o, txt in malos:
        print(f"  {t:7.1f} s  ocupado {o:5.1%}  «{txt[:60]}»")
    sys.exit(1 if malos else 0)


def probar():
    """Regla: una guardia nueva se rompe a propósito antes de creerle. Videos sintéticos de 6 s (fondo F6EEFA, 320×180) con una caja
    negra en distintos lugares y dos subtítulos: uno de 0,5 a 2,5 s (siempre limpio) y otro de 3,2 a 4,8 s (el cuadro del medio, a 4 s,
    es el que tiene la caja). El script se corre como lo corre una persona: por línea de comandos, mirando código de salida y texto."""
    import tempfile
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        srt = tmp / "s.srt"
        srt.write_text("1\n00:00:00,500 --> 00:00:02,500\nlimpio\n\n2\n00:00:03,200 --> 00:00:04,800\ncon caja\n", encoding="utf-8")

        def video(nombre, caja=None, fondo="0xF6EEFA"):
            vf = f"drawbox=x={caja[0]}:y={caja[1]}:w={caja[2]}:h={caja[3]}:color=black@1:t=fill:enable='between(t,3,5)'" if caja else "null"
            f = tmp / f"{nombre}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={fondo}:s=320x180:d=6:r=10", "-vf", vf,
                            "-pix_fmt", "yuv420p", str(f)], check=True)
            return f

        def correr(f, *extra):
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(f), str(srt), *extra], capture_output=True, text=True,
                               encoding="utf-8")
            return r.returncode, r.stdout

        c, o = correr(video("limpio"))
        caso("sin nada en la franja: código 0 y 0 chocan", (c, "0 chocan" in o), (0, True))
        c, o = correr(video("caja", (40, 140, 240, 20)))
        caso("caja en la franja de abajo: código 1", c, 1)
        caso("choca sólo el subtítulo que tiene la caja (a 4,0 s), no el limpio", ("4.0 s" in o, "limpio" in o, "con caja" in o), (True, False, True))
        c, o = correr(video("alta", (40, 10, 240, 20)))
        caso("una caja arriba, fuera de la franja, no choca", c, 0)
        c, o = correr(video("chica", (100, 150, 2, 2)))
        caso("una caja diminuta queda bajo el umbral de 0,4 %", c, 0)
        c, o = correr(video("chica2", (100, 150, 2, 2)), "--umbral", "0.0001")
        caso("con un umbral más estricto la misma caja sí choca", c, 1)
        c, o = correr(video("alta2", (40, 10, 240, 20)), "--franja", "0,0.3")
        caso("--franja 0,0.3 mira arriba y ahí la caja choca", c, 1)
        c, o = correr(video("gris", fondo="0x808080"))
        caso("un fondo que no es el de por omisión se lee como contenido", c, 1)
        c, o = correr(video("gris2", fondo="0x808080"), "--fondo", "808080")
        caso("con --fondo igual al del video no choca", c, 0)
        c, o = correr(video("limpio2"), "--franja", "no,es")
        caso("una franja mal escrita no pasa en silencio (código distinto de 0)", c != 0, True)
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    if sys.argv[1:] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    main()
