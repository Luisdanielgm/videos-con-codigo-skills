"""Acabado ASCII sobre un video ya hecho: cada celda se vuelve el carácter que mejor calza con su forma.

Uso:  .venv/Scripts/python herramientas/ascii.py <entrada.mp4> <salida.mp4> [opciones]
  --celda 10          ancho de la celda en px (el alto es el doble, como en una terminal); 8 a 16 va bien
  --paleta fosforo    fosforo (verde sobre negro) · ambar · papel (tinta sobre papel) · color (el de la imagen)
  --invertir          lo oscuro lleva los glifos densos (para trazos oscuros sobre fondo claro en fosforo/ambar/color)
  --piso 0.25         lo que queda bajo ese gris sale vacío (limpia viñetas y cielos con degradado); 0.1 por omisión
  --revelado 2,5     de 2 s a 5 s pasa de la imagen real al ASCII, celda por celda
  --bordes 0.3        peso de los glifos de dirección (| / - \\) en los bordes (Sobel); 0 los apaga
  --histeresis 0.015  cuánto mejor tiene que ser un glifo nuevo para reemplazar al de la celda
  --sin-histeresis    la apaga (sólo para medir cuánto tiemblan los glifos sin ella)
  --tramo 30,10       sólo 10 s desde el segundo 30 (para probar; los demás tiempos cuentan desde el tramo)
  --capturas 3,7      no hace video: guarda esos cuadros en render/capturas/
  --probar            1 s de prueba: color, cuadros y audio de la salida, y su caso roto

Atlas: los 95 caracteres imprimibles en una monoespaciada del sistema (Consolas en Windows), cada uno medido
en una grilla de 3×6 (cuánta tinta cae en cada parte de la celda). Cada celda de la imagen se mide igual y elige
el glifo más parecido en forma, no sólo en densidad (idea de «ASCII que conoce la forma», Codrops, y de
niccolofanton/morphing-ascii-shader, MIT). En los bordes, Sobel vota la dirección y suma a | / - \\.
Histéresis: una celda sólo cambia de glifo si el nuevo es claramente mejor; así no tiembla con el ruido del MP4.
Sale en 1080p (1920×1080, o 1080×1920 si el original es vertical) con el mismo fps; el audio se copia.
Todo determinista: el mismo video da siempre el mismo resultado.
"""
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from color_mp4 import COLOR_709

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/CascadiaMono.ttf", "C:/Windows/Fonts/cour.ttf",
           "/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
GLIFOS = "".join(chr(i) for i in range(32, 127))   # los 95 imprimibles
DIRECCION = "|/-\\"        # borde vertical, diagonal que sube, horizontal, diagonal que baja
RAMPA = " .:-=+*#%@"       # para celdas planas (sin forma adentro): sólo densidad
PLANO = .12                # diferencia máxima entre partes de la celda para tratarla como plana
DENSO = .6                 # gris que equivale al glifo más denso: con 1 los trazos finos se pierden; con .35, letras sueltas
SX, SY = 3, 6              # grilla de forma de cada celda (ancho × alto)
NITIDEZ = 2.0              # realza el contraste dentro de la celda para que la forma pese más que el promedio
UMBRAL_BORDE = .2          # magnitud de Sobel (0..1) desde la que un píxel vota una dirección
LLENO_BORDE = .2           # fracción de píxeles de la celda que vale un voto completo
BASE = .35                 # brillo mínimo de un glifo (celdas oscuras con glifo)
# paleta: fondo, tinta (None = el color de la imagen), resplandor
PALETAS = {
    "fosforo": ((4, 10, 6), (110, 255, 150), .5),
    "ambar": ((12, 7, 2), (255, 182, 50), .5),
    "papel": ((244, 236, 220), (28, 26, 38), 0),
    "color": ((8, 8, 10), None, 0),
}
LUMA = np.array([.2126, .7152, .0722], np.float32)


def opcion(nombre, omision):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else omision


def pesos(n, k):
    """Matriz (n, k): qué parte de cada uno de n píxeles cae en cada una de k franjas iguales (promedio por franja)."""
    b = np.linspace(0, n, k + 1)
    x = np.arange(n)[:, None]
    w = np.clip(np.minimum(x + 1, b[None, 1:]) - np.maximum(x, b[None, :-1]), 0, None)
    return (w / w.sum(0)).astype(np.float32)


class Ascii:
    def __init__(self, W, H, celda, paleta, invertir, bordes, histeresis, revelado, piso=0.0):
        self.W, self.H, self.cw, self.ch = W, H, celda, 2 * celda
        self.piso = piso
        self.C, self.R = -(-W // self.cw), -(-H // self.ch)
        self.fondo = np.array(PALETAS[paleta][0], np.float32) / 255
        self.tinta = None if PALETAS[paleta][1] is None else np.array(PALETAS[paleta][1], np.float32) / 255
        self.brillo = PALETAS[paleta][2]
        self.invertir = (paleta == "papel") != invertir   # en papel la tinta va donde la imagen es oscura
        self.bordes, self.histeresis, self.revelado = bordes, histeresis, revelado
        self.px, self.py = pesos(self.cw, SX), pesos(self.ch, SY)
        self.atlas = self.dibujar_atlas()
        g = self.forma(self.atlas[:, :, None, :], len(GLIFOS), 1)
        self.G = g / g.mean(1).max() * DENSO              # el glifo más denso equivale a un gris de DENSO
        self.G2 = (self.G ** 2).sum(1)
        self.dir = np.array([GLIFOS.index(c) for c in DIRECCION])
        self.fuera_rampa = np.array([c not in RAMPA for c in GLIFOS])
        self.antes = None
        # revelado: cada celda cambia en su momento, de izquierda a derecha con algo de azar (fijo)
        col = np.arange(self.C)[None, :] / self.C
        self.umbral = (.75 * col + .25 * np.random.default_rng(7).random((self.R, self.C))).astype(np.float32)
        if self.tinta is not None:   # brillo 0..255 → color, de fondo a tinta
            k = np.arange(256, dtype=np.float32)[:, None] / 255
            self.tabla = (np.clip(self.fondo + k * (self.tinta - self.fondo), 0, 1) * 255).astype(np.uint8)

    def dibujar_atlas(self):
        ruta = next(p for p in FUENTES if Path(p).exists())
        for s in range(self.ch * 2, 4, -1):
            f = ImageFont.truetype(ruta, s)
            a, d = f.getmetrics()
            if f.getlength("M") <= self.cw and a + d <= self.ch * 1.1:
                break
        atlas = []
        for c in GLIFOS:
            img = Image.new("L", (self.cw, self.ch), 0)
            ImageDraw.Draw(img).text((self.cw / 2, self.ch / 2), c, fill=255, font=f, anchor="mm")
            atlas.append(np.asarray(img, np.float32) / 255)
        return np.stack(atlas)                            # (95, alto, ancho)

    def forma(self, t, R, C):
        """Bloques (R, alto, C, ancho) → (R·C, SX·SY): tinta promedio en cada parte de cada celda."""
        a = t.reshape(-1, self.cw) @ self.px                                  # (R·alto·C, SX)
        a = a.reshape(R, self.ch, C, SX).transpose(0, 2, 3, 1) @ self.py      # (R, C, SX, SY)
        return a.reshape(R * C, SX * SY)

    def votos(self, D):
        """Sobel sobre la grilla de forma (cada parte de celda es un «píxel» de ~3 px): fracción de las partes de
        cada celda que votan cada dirección de borde (R·C, 4). Mucho más barato que a resolución completa."""
        R, C = self.R, self.C
        t = D.reshape(R, C, SX, SY).transpose(0, 3, 1, 2).reshape(R * SY, C * SX)
        gx = np.zeros_like(t)
        gy = np.zeros_like(t)
        sx = t[:, 2:] - t[:, :-2]
        gx[1:-1, 1:-1] = (sx[:-2] + 2 * sx[1:-1] + sx[2:]) / 4
        sy = t[2:] - t[:-2]
        gy[1:-1, 1:-1] = (sy[:, :-2] + 2 * sy[:, 1:-1] + sy[:, 2:]) / 4
        ax, ay = np.abs(gx), np.abs(gy)
        fuerte = ax * ax + ay * ay > UMBRAL_BORDE ** 2
        recto_v, recto_h = ay < .4142 * ax, ax < .4142 * ay   # tan 22,5°: el borde es perpendicular al gradiente
        diag = fuerte & ~recto_v & ~recto_h
        sube = gx * gy > 0                                     # gradiente hacia abajo a la derecha: borde «/»
        v = [fuerte & recto_v, diag & sube, fuerte & recto_h, diag & ~sube]
        return np.stack([x.reshape(R, SY, C, SX).mean((1, 3), dtype=np.float32).ravel() for x in v], 1)

    def costos(self, rgb):
        """Cuadro (con relleno) → costo de cada glifo en cada celda (R·C, 95), brillo m (R·C, 1) y luminancia t."""
        t = rgb @ LUMA
        if self.invertir:
            t = 1 - t
        if self.piso > 0:   # lo más tenue queda vacío (viñetas, fondos con degradado)
            t = np.clip((t - self.piso) / (1 - self.piso), 0, 1)
        D = self.forma(t, self.R, self.C)
        m = D.max(1, keepdims=True) + 1e-6                     # 0..1: también da el brillo del glifo
        plana = m[:, 0] - D.min(1) < PLANO
        votos = self.votos(D) if self.bordes > 0 else None
        D = m * (D / m) ** NITIDEZ
        costo = ((D ** 2).sum(1)[:, None] - 2 * D @ self.G.T + self.G2[None]) / (SX * SY)
        costo += plana[:, None] & self.fuera_rampa[None]         # una celda plana no inventa formas («jjjj» en un cielo)
        if votos is not None:
            v = np.clip(votos / LLENO_BORDE, 0, 1)
            # un trazo tenue en una celda «plana» sigue siendo borde: se le devuelve el castigo según sus votos
            costo[:, self.dir] -= self.bordes * v + (plana[:, None] & self.fuera_rampa[self.dir]) * v
        return costo, m, t

    def elegir(self, costo, antes, histeresis):
        """Glifo de cada celda: el más barato, salvo que el de antes esté a menos de `histeresis` de él."""
        glifo = costo.argmin(1)
        if antes is not None and histeresis > 0:
            n = np.arange(len(glifo))
            glifo = np.where(costo[n, antes] - costo[n, glifo] <= histeresis, antes, glifo)
        return glifo

    def __call__(self, rgb, seg):
        """Un cuadro (alto, ancho, 3) en 0..1 → (cuadro ASCII uint8, glifos que cambiaron respecto del anterior)."""
        R, C, ch, cw = self.R, self.C, self.ch, self.cw
        if rgb.shape[0] != R * ch or rgb.shape[1] != C * cw:
            rgb = np.pad(rgb, ((0, R * ch - self.H), (0, C * cw - self.W), (0, 0)), mode="edge")
        costo, m, t = self.costos(rgb)
        glifo = self.elegir(costo, self.antes, self.histeresis)
        cambios = 0 if self.antes is None else int((glifo != self.antes).sum())
        self.antes = glifo
        p = 1.0
        if self.revelado:
            p = float(np.clip((seg - self.revelado[0]) / max(self.revelado[1] - self.revelado[0], 1e-3), 0, 1))
            if p == 0:   # todavía el video real (los glifos se calculan igual, para que la histéresis tenga historia)
                return (rgb[:self.H, :self.W] * 255).astype(np.uint8), cambios
        M = self.atlas[glifo]                                   # (R·C, alto, ancho)
        if self.tinta is not None:
            # monocromo: una sola capa de brillo (0..1) y una tabla fondo → tinta; mucho más barato que RGB
            b = BASE + (1 - BASE) * m[:, 0]
            S = (M * b[:, None, None]).reshape(R, C, ch, cw).transpose(0, 2, 1, 3).reshape(R * ch, C * cw)
            if self.brillo > 0:   # resplandor de pantalla de fósforo: la energía de cada celda, difusa
                e = Image.fromarray((np.clip(M.mean((1, 2)) * b, 0, 1).reshape(R, C) * 255).astype(np.uint8))
                e = e.filter(ImageFilter.GaussianBlur(.8)).resize((C * cw, R * ch), Image.BILINEAR)
                S += np.asarray(e, np.float32) * (self.brillo / 255)
            out = np.take(self.tabla, np.clip(S * 255, 0, 255).astype(np.uint8), axis=0)   # 2,4× más rápido que tabla[i]
        else:
            # el tono sale de lo brillante de la celda (un trazo blanco fino no se promedia con el fondo) y el brillo, de m
            w = (rgb * t[..., None]).reshape(R, ch, C, cw, 3).sum((1, 3)).reshape(-1, 3)
            frente = w / np.maximum(w.max(1, keepdims=True), 1e-6) * (BASE + (1 - BASE) * m)
            out = M[..., None] * (frente - self.fondo)[:, None, None, :]
            out += self.fondo
            out = out.reshape(R, C, ch, cw, 3).transpose(0, 2, 1, 3, 4).reshape(R * ch, C * cw, 3)
            out = (np.clip(out, 0, 1) * 255).astype(np.uint8)
        if p < 1:   # revelado: cada celda pasa de la imagen real al ASCII en su momento
            a = np.clip((p * 1.3 - self.umbral) / .3, 0, 1)[:, None, :, None, None]
            real = rgb.reshape(R, ch, C, cw, 3) * 255
            out = (real + (out.reshape(R, ch, C, cw, 3) - real) * a).reshape(R * ch, C * cw, 3).astype(np.uint8)
        return out[:self.H, :self.W], cambios


def medidas(entrada):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-of", "csv=p=0", str(entrada)], capture_output=True, text=True).stdout.strip().split(",")
    w, h, fps = int(r[0]), int(r[1]), r[2]
    return (1920, 1080, fps) if w >= h else (1080, 1920, fps)


def leer(entrada, W, H, tramo, salida=()):
    escala = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"
    p = subprocess.Popen(["ffmpeg", "-v", "error", *tramo, "-i", str(entrada), "-vf", escala, *salida, "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255


def main():
    entrada, salida = Path(sys.argv[1]), Path(sys.argv[2])
    W, H, fps = medidas(entrada)
    rev = opcion("--revelado", None)
    a = Ascii(W, H, int(opcion("--celda", 10)), opcion("--paleta", "fosforo"), "--invertir" in sys.argv,
              float(opcion("--bordes", .3)), 0 if "--sin-histeresis" in sys.argv else float(opcion("--histeresis", .015)),
              [float(x) for x in rev.split(",")] if rev else None, float(opcion("--piso", .1)))
    tr = [float(x) for x in opcion("--tramo", "0,0").split(",")]
    tramo = (["-ss", str(tr[0])] + (["-t", str(tr[1])] if tr[1] else [])) if tr != [0, 0] else []
    if "--capturas" in sys.argv:
        for t in [float(x) for x in opcion("--capturas", "").split(",")]:
            rgb = next(leer(entrada, W, H, ["-ss", str(tr[0] + t)], ["-frames:v", "1"]))
            img, _ = a(rgb, t)
            nombre = f"{salida.stem}_{f'{t:g}'.replace('.', '-')}.jpg"
            Image.fromarray(img).save(RAIZ / "render" / "capturas" / nombre, quality=92)
            a.antes = None
        print("capturas:", opcion("--capturas", ""))
        return
    num, den = (fps.split("/") + ["1"])[:2]
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", fps,
                            "-i", "-", *tramo, "-i", str(entrada), "-map", "0:v", "-map", "1:a?", "-c:a", "copy",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p", *COLOR_709, "-shortest",
                            str(salida)], stdin=subprocess.PIPE)
    cambios, proceso, t0 = [], 0.0, time.perf_counter()
    for f, rgb in enumerate(leer(entrada, W, H, tramo)):
        t1 = time.perf_counter()
        img, c = a(rgb, f * float(den) / float(num))
        proceso += time.perf_counter() - t1
        enc.stdin.write(img.tobytes())
        if f:
            cambios.append(c)
        if f % 300 == 0:
            print(f"  cuadro {f}", flush=True)
    enc.stdin.close()
    ok = enc.wait() == 0
    n = len(cambios) + 1
    celdas = a.R * a.C
    cm = np.array(cambios or [0])
    print(f"cuadros: {n}  ·  {proceso / n:.3f} s/cuadro de cálculo  ·  {(time.perf_counter() - t0) / n:.3f} s/cuadro en total")
    print(f"cambios de glifo por cuadro: media {cm.mean():.0f} ({100 * cm.mean() / celdas:.2f} % de {celdas} celdas), "
          f"mediana {np.median(cm):.0f}, máximo {cm.max()}")
    print("ascii:", "listo" if ok else "ERROR", "->", salida)


def probar():
    """1 s de prueba → ASCII: el MP4 sale con color etiquetado, los 30 cuadros y el audio copiado (color_mp4.probar_salida)."""
    from color_mp4 import probar_salida
    hacer = lambda e, s, _t: subprocess.run([sys.executable, __file__, str(e), str(s)], check=True, capture_output=True)
    return probar_salida("ascii", hacer, cuadros=30)


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    main()
