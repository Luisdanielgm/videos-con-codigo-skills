"""Acabado de estilo sobre un video ya hecho: lo vuelve una impresión risográfica (técnica 7).

Uso:  .venv/Scripts/python herramientas/estilo.py <entrada.mp4> <salida.mp4> [--capturas 12,57] [--puntos]
       (--puntos: trama regular de puntos, más «pop», pero hace moiré; por omisión, trama de grano)

Cada cuadro se separa en cuatro tintas (azul, rosa flúor, amarillo y negro), cada tinta se imprime como
trama de puntos con su propio ángulo, las planchas quedan un poco corridas (y tiemblan apenas, como en
una impresora de verdad) y las tintas se multiplican sobre papel crema con grano. El audio se copia.
Es lo que usó @gcduncombe en su corto de la cabaña nevada: con dibujos simples, se ve de autor.
Todo determinista: el mismo cuadro da siempre la misma imagen.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 1920, 1080
RAIZ = Path(__file__).resolve().parent.parent
PAPEL = np.array([244, 236, 220], np.float32) / 255
# tinta: color al 100 % (sRGB 0..1), ángulo de la trama, corrimiento de la plancha (px)
TINTAS = [
    ("azul", np.array([0, 120, 191]) / 255, 15, (1, 0)),
    ("rosa", np.array([255, 72, 176]) / 255, 75, (-1, 1)),
    ("amarillo", np.array([255, 232, 0]) / 255, 0, (0, -1)),
    ("negro", np.array([30, 30, 40]) / 255, 45, (0, 0)),
]
CELDA = 7.0   # tamaño de la trama (px)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def trama(angulo):
    a = np.radians(angulo)
    u = (xx * np.cos(a) + yy * np.sin(a)) * 2 * np.pi / CELDA
    v = (-xx * np.sin(a) + yy * np.cos(a)) * 2 * np.pi / CELDA
    return (np.cos(u) + np.cos(v)) / 4 + .5           # 0..1: 1 en el centro de cada punto


def trama_grano(i):
    """Trama estocástica: puntos al azar, fijos en el tiempo (no parpadean). Sin patrón periódico no hay
    moiré: con la trama de puntos regular aparecían círculos grandes al achicar o comprimir el video."""
    return np.clip(np.random.default_rng(i + 1).random((H, W)).astype(np.float32) * .8 + .1, 0, 1)


TRAMAS = [trama_grano(i) for i in range(len(TINTAS))] if "--puntos" not in sys.argv else [trama(t[2]) for t in TINTAS]
rng = np.random.default_rng(3)
GRANO = (rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32).repeat(2, 0).repeat(2, 1) * .025
         + rng.normal(0, 1, (H, W)).astype(np.float32) * .012)
FIBRAS = np.clip(np.sin(xx * .013 + np.sin(yy * .021) * 3) * np.sin(yy * .007) * .015, -1, 1)


def separar(rgb):
    """RGB (0..1) → cobertura de cada tinta (0..1), con negro para las sombras."""
    rgb = np.clip((rgb - .04) * 1.12, 0, 1)                       # un poco más de contraste antes de separar
    c, m, y = 1 - rgb[..., 0], 1 - rgb[..., 1], 1 - rgb[..., 2]
    k = np.minimum(np.minimum(c, m), y)
    # el negro sólo para lo muy oscuro: en una risografía la noche es tinta azul densa, no gris
    kn = np.clip((k - .55) / .45, 0, 1) * .8
    return [np.clip((c - k * .25) * 1.2, 0, 1), np.clip((m - k * .55) * 1.1, 0, 1), np.clip((y - k * .6) * 1.1, 0, 1), kn]


def imprimir(rgb, f):
    cob = separar(rgb)
    out = np.broadcast_to(PAPEL, rgb.shape).copy()
    for i, ((_, color, _, (dx, dy)), c, tr) in enumerate(zip(TINTAS, cob, TRAMAS)):
        # un punto de trama se imprime donde la trama supera 1 - cobertura; borde suave (antialias)
        tinta = np.clip((tr - (1 - c)) * 6 + .5, 0, 1)
        j = np.random.default_rng(f * 10 + i).integers(-1, 2, 2) if f % 4 == 0 else (0, 0)   # la plancha tiembla apenas
        tinta = np.roll(tinta, (dy + int(j[1]), dx + int(j[0])), (0, 1))
        # tinta sobre papel: se multiplica (rosa + amarillo = rojo), con manchas de carga irregular
        carga = .88 + .12 * np.roll(GRANO, (i * 37, i * 91), (0, 1)) * 8
        out *= 1 - (tinta * carga)[..., None] * (1 - color)
    out += (GRANO + FIBRAS)[..., None]
    return np.clip(out, 0, 1)


def leer(entrada):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(entrada), "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-"],
                         stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255


def main():
    entrada, salida = Path(sys.argv[1]), Path(sys.argv[2])
    if "--capturas" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--capturas") + 1].split(",")]
        from PIL import Image
        for t in ts:
            b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(entrada), "-frames:v", "1", "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-"], capture_output=True).stdout
            rgb = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
            img = (imprimir(rgb, int(t * 30)) * 255).astype(np.uint8)
            Image.fromarray(img).save(RAIZ / "render" / "capturas" / f"{salida.stem}_{f'{t:g}'.replace('.', '-')}.jpg", quality=92)
        print(f"capturas: {len(ts)}")
        return
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(entrada)],
                         capture_output=True, text=True).stdout.strip().strip(",").split(",")[0]
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", fps, "-i", "-",
                            "-i", str(entrada), "-map", "0:v", "-map", "1:a?", "-c:a", "copy", "-c:v", "libx264", "-preset", "medium",
                            "-crf", "30", "-pix_fmt", "yuv420p", str(salida)], stdin=subprocess.PIPE)
    for f, rgb in enumerate(leer(entrada)):
        enc.stdin.write((imprimir(rgb, f) * 255).astype(np.uint8).tobytes())
        if f % 300 == 0:
            print(f"  cuadro {f}", flush=True)
    enc.stdin.close()
    print("estilo:", "listo" if enc.wait() == 0 else "ERROR", "->", salida)


if __name__ == "__main__":
    main()
