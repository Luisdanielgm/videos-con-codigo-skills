"""Motor de pizarra (técnica 4): dibuja cuadro a cuadro con cairo, estilo marcador sobre pizarra blanca,
y lo manda a ffmpeg junto con la narración. No usa navegador.

Uso típico (desde el script de un video):
    from pizarra import Pizarra
    pz = Pizarra(__file__)                # lee tiempos.js de la carpeta del video
    def escenas(pz, t): ...               # dibuja el instante t con pz.linea, pz.texto, etc.
    pz.main(escenas)                      # CLI: --capturas 3.5,40  |  --exportar [--fps 60]
Autoprueba:  .venv/Scripts/python herramientas/pizarra.py --probar   (pizarra de 1 s en una carpeta temporal)

Todo trazo acepta `p` (0..1): cuánto del trazo ya se dibujó. Así se "escribe" en la pizarra.
El temblor de mano es determinista (sale de una semilla por trazo): el mismo t da el mismo cuadro.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import cairo

from color_mp4 import COLOR_709

RAIZ = Path(__file__).resolve().parent.parent
W, H = 1920, 1080
FPS = int(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 30    # --fps 60: nivel de estudio
FUENTE = "Segoe Print"          # letra manuscrita que trae Windows; alternativa: "Ink Free"
TINTA = {
    "negro": (0.12, 0.14, 0.19), "azul": (0.12, 0.36, 0.85), "rojo": (0.84, 0.2, 0.25),
    "verde": (0.12, 0.62, 0.33), "naranja": (0.88, 0.48, 0.12), "gris": (0.55, 0.58, 0.64),
    "amarillo": (0.97, 0.78, 0.2),
}


def clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))


def lerp(a, b, k):
    return a + (b - a) * k


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else float(t >= b)


def ease(k):
    return 4 * k ** 3 if k < .5 else 1 - (-2 * k + 2) ** 3 / 2


def ruido(semilla, i=0):
    """Número pseudoaleatorio en [-1, 1], fijo para (semilla, i)."""
    x = math.sin(semilla * 12.9898 + i * 78.233) * 43758.5453
    return (x - math.floor(x)) * 2 - 1


class Pizarra:
    def __init__(self, script):
        self.carpeta = Path(script).resolve().parent
        js = (self.carpeta / "tiempos.js").read_text(encoding="utf-8")
        self.TI = json.loads(re.sub(r"^window\.TIEMPOS\s*=\s*|;\s*$", "", js.strip()))
        self.DUR = self.TI["total"]
        self.ctx = None
        self.trozos_cache = {}
        self.colores = {}   # color del subtítulo por personaje, p. ej. {"visitante": (1, .85, .54)} (usa `quien`)

    # ───── tiempos relativos a la narración (igual que Reproductor.ayudantes) ─────
    def A(self, i): return self.TI["seg"][i]["inicio"]
    def D(self, i): return self.TI["seg"][i]["dur"]
    def F(self, i, f): return self.A(i) + f * self.D(i)
    def P(self, t, i, f0, f1): return ease(seg(t, self.F(i, f0), self.F(i, f1)))

    def SIG(self, i):
        o = self.TI["orden"]; k = o.index(i)
        return self.A(o[k + 1]) if k < len(o) - 1 else self.DUR

    def vis(self, t, desde, hasta):
        return min(seg(t, self.A(desde) - .5, self.A(desde)), 1 - seg(t, self.SIG(hasta) - .4, self.SIG(hasta)))

    # ───── trazos a mano ─────
    def _color(self, c, a=1.0):
        r, g, b = TINTA.get(c, c) if isinstance(c, str) else c
        self.ctx.set_source_rgba(r, g, b, a)

    def linea(self, x1, y1, x2, y2, p=1, color="negro", ancho=4, a=1, semilla=0):
        """Línea levemente curva (como a mano), dibujada hasta la fracción p."""
        if p <= 0 or a <= 0:
            return
        L = math.hypot(x2 - x1, y2 - y1) or 1
        off = ruido(semilla, 1) * min(12, L * .03)
        cx, cy = (x1 + x2) / 2 - (y2 - y1) / L * off, (y1 + y2) / 2 + (x2 - x1) / L * off
        # corte de la curva cuadrática en p (de Casteljau)
        ax, ay = lerp(x1, cx, p), lerp(y1, cy, p)
        bx, by = lerp(cx, x2, p), lerp(cy, y2, p)
        ex, ey = lerp(ax, bx, p), lerp(ay, by, p)
        c = self.ctx
        c.set_line_width(ancho); c.set_line_cap(cairo.LINE_CAP_ROUND)
        self._color(color, a)
        c.move_to(x1, y1)
        c.curve_to(x1 + 2 / 3 * (ax - x1), y1 + 2 / 3 * (ay - y1), ex + 2 / 3 * (ax - ex), ey + 2 / 3 * (ay - ey), ex, ey)
        c.stroke()

    def trazo(self, puntos, p=1, color="negro", ancho=4, a=1):
        """Polilínea dibujada hasta la fracción p de su largo total."""
        if p <= 0 or a <= 0 or len(puntos) < 2:
            return
        largos = [math.dist(puntos[i], puntos[i + 1]) for i in range(len(puntos) - 1)]
        meta = sum(largos) * p
        c = self.ctx
        c.set_line_width(ancho); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        self._color(color, a)
        c.move_to(*puntos[0])
        for i, l in enumerate(largos):
            if meta <= 0:
                break
            f = min(1, meta / l) if l else 1
            x = lerp(puntos[i][0], puntos[i + 1][0], f); y = lerp(puntos[i][1], puntos[i + 1][1], f)
            c.line_to(x, y); meta -= l
        c.stroke()

    def circulo(self, cx, cy, r, p=1, color="negro", ancho=4, a=1, semilla=0, relleno=None, a_relleno=.35):
        """Círculo a mano: el final se pasa un poco del principio, como cuando se dibuja rápido."""
        if a <= 0:
            return
        if relleno and p >= 1:
            self._color(relleno, a * a_relleno)
            self.ctx.arc(cx, cy, r * .92, 0, 2 * math.pi); self.ctx.fill()
        n = 64; a0 = ruido(semilla, 3) * math.pi
        f1, f2 = ruido(semilla, 4) * math.pi, ruido(semilla, 5) * math.pi
        pts = []
        for k in range(n + 5):
            ang = a0 + k / n * 2 * math.pi
            u = k / n * 2 * math.pi
            # temblor suave (pocas ondas), no punto a punto: si no, el círculo sale dentado
            rr = r * (1 + .025 * math.sin(2 * u + f1) + .012 * math.sin(3 * u + f2) + .02 * k / n)
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        self.trazo(pts, p, color, ancho, a)

    def rect(self, x, y, w, h, p=1, color="negro", ancho=4, a=1, semilla=0, relleno=None, a_relleno=.3):
        if relleno and p >= 1 and a > 0:
            self._color(relleno, a * a_relleno); self.ctx.rectangle(x, y, w, h); self.ctx.fill()
        lados = [(x, y, x + w, y), (x + w, y, x + w, y + h), (x + w, y + h, x, y + h), (x, y + h, x, y)]
        for i, (a1, b1, a2, b2) in enumerate(lados):
            self.linea(a1, b1, a2, b2, clamp(p * 4 - i), color, ancho, a, semilla * 7 + i)

    def flecha(self, x1, y1, x2, y2, p=1, color="negro", ancho=4, a=1, semilla=0):
        self.linea(x1, y1, x2, y2, p, color, ancho, a, semilla)
        if p >= .98:
            ang = math.atan2(y2 - y1, x2 - x1); s = 14 + ancho * 2
            for d in (.5, -.5):
                self.linea(x2, y2, x2 - s * math.cos(ang + d), y2 - s * math.sin(ang + d), 1, color, ancho, a, semilla + 5)

    def resaltar(self, x, y, w, h, p=1, a=1):
        """Resaltador amarillo translúcido, que avanza de izquierda a derecha."""
        if p <= 0 or a <= 0:
            return
        self._color("amarillo", .38 * a)
        self.ctx.rectangle(x, y, w * p, h); self.ctx.fill()

    def texto(self, s, x, y, tam=40, color="negro", p=1, a=1, alinear="izq", negrita=False, fuente=FUENTE):
        """Texto manuscrito que se va escribiendo letra a letra (p = fracción escrita)."""
        if p <= 0 or a <= 0 or not s:
            return
        c = self.ctx
        c.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if negrita else cairo.FONT_WEIGHT_NORMAL)
        c.set_font_size(tam)
        ancho = c.text_extents(s).x_advance
        visible = s[:max(1, round(len(s) * p))]
        dx = {"izq": 0, "centro": -ancho / 2, "der": -ancho}[alinear]
        self._color(color, a)
        c.move_to(x + dx, y + tam * .35)
        c.show_text(visible)
        return ancho

    def ancho_texto(self, s, tam=40, negrita=False, fuente=FUENTE):
        c = self.ctx
        c.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if negrita else cairo.FONT_WEIGHT_NORMAL)
        c.set_font_size(tam)
        return c.text_extents(s).x_advance

    # ───── subtítulos (franja inferior) ─────
    def _trozos(self, texto, maximo=80):
        partes = re.split(r"(?<=[.:;?!,])\s+", texto)
        out = []
        for p in partes:
            if out and len(out[-1]) + 1 + len(p) <= maximo:
                out[-1] += " " + p
            else:
                out.append(p)
        return out

    def subtitulos(self, t):
        for i in self.TI["orden"]:
            s = self.TI["seg"][i]
            if t < s["inicio"] - .1 or t > s["inicio"] + s["dur"] + .25:
                continue
            ts = self.trozos_cache.setdefault(i, self._trozos(s["texto"]))
            total = sum(len(x) for x in ts); a = s["inicio"]; k = 0
            for k in range(len(ts)):
                b = a + s["dur"] * len(ts[k]) / total
                if t < b or k == len(ts) - 1:
                    break
                a = b
            linea = ts[k]; c = self.ctx
            c.select_font_face("Segoe UI", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL); c.set_font_size(38)
            w = min(1760, c.text_extents(linea).x_advance + 64)
            c.set_source_rgba(.12, .14, .19, .82)
            x0 = W / 2 - w / 2; r = 14
            c.new_sub_path(); c.arc(x0 + w - r, 978 + r, r, -math.pi / 2, 0); c.arc(x0 + w - r, 1042 - r, r, 0, math.pi / 2)
            c.arc(x0 + r, 1042 - r, r, math.pi / 2, math.pi); c.arc(x0 + r, 978 + r, r, math.pi, 3 * math.pi / 2); c.close_path(); c.fill()
            c.set_source_rgb(*self.colores.get(s.get("quien"), (.97, .97, .96)))
            c.move_to(W / 2 - c.text_extents(linea).x_advance / 2, 1023); c.show_text(linea)
            return

    # ───── cuadro completo ─────
    def cuadro(self, escenas, t):
        sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.ctx = cairo.Context(sup)
        self.ctx.set_source_rgb(.985, .98, .965); self.ctx.paint()      # pizarra blanca, apenas cálida
        escenas(self, t)
        self.subtitulos(t)
        fin = seg(t, self.DUR - .8, self.DUR)
        if fin > 0:
            self.ctx.set_source_rgba(1, 1, 1, fin); self.ctx.paint()
        return sup

    def capa(self, alpha, dibujar):
        """Dibuja algo con transparencia global (para fundir una escena entera)."""
        if alpha <= 0:
            return
        self.ctx.push_group(); dibujar(); self.ctx.pop_group_to_source(); self.ctx.paint_with_alpha(alpha)

    def nombre(self):
        return f"{self.carpeta.parent.name}_{self.carpeta.name}"

    def capturas(self, escenas, lista):
        out = RAIZ / "render" / "capturas"; out.mkdir(parents=True, exist_ok=True)
        for t in lista:
            # mismo formato de nombre que las capturas del navegador: 27 → "27", 3.5 → "3-5"
            self.cuadro(escenas, t).write_to_png(str(out / f"{self.nombre()}_{f'{t:g}'.replace('.', '-')}.png"))
        print(f"capturas: {len(lista)} en {out}")

    def exportar(self, escenas, salida=None):
        # salida sólo la cambia --probar (escribe en una carpeta temporal, sin tocar render/)
        salida = salida or RAIZ / "render" / f"{self.nombre()}.mp4"; salida.parent.mkdir(exist_ok=True)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-"]
        audio = self.carpeta / "mezcla.wav"  # narración + ambiente (herramientas/sonido.py)
        if not audio.exists():
            audio = self.carpeta / "narracion.wav"
        if audio.exists():
            cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "160k"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", *COLOR_709, str(salida)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = math.ceil(self.DUR * FPS)
        for f in range(n + 1):
            sup = self.cuadro(escenas, f / FPS)
            proc.stdin.write(bytes(sup.get_data()))
            if f % 300 == 0:
                print(f"  {f}/{n}", flush=True)
        proc.stdin.close()
        ok = proc.wait() == 0
        print(f"exportar: {'listo' if ok else 'ERROR'} -> {salida} ({n + 1} cuadros)")
        sys.exit(0 if ok else 1)

    def main(self, escenas):
        args = sys.argv[1:]
        if args[:1] == ["--capturas"]:
            self.capturas(escenas, [float(x) for x in args[1].split(",")])
        elif args[:1] == ["--exportar"]:
            self.exportar(escenas)
        else:
            sys.exit("uso: video.py --capturas 3.5,40 | --exportar")


def probar():
    """Una pizarra de 1 s en una carpeta temporal (una línea que se dibuja + subtítulo + audio) → MP4 con color
    etiquetado, 31 cuadros y audio (color_mp4.probar_salida); no toca render/."""
    from color_mp4 import probar_salida

    def hacer(_entrada, salida, t):
        carpeta = t / "video"; carpeta.mkdir()
        ti = {"total": 1.0, "orden": ["a"], "seg": {"a": {"inicio": .1, "dur": .6, "texto": "Prueba de la pizarra."}}}
        (carpeta / "tiempos.js").write_text("window.TIEMPOS = " + json.dumps(ti) + ";", encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=1.2",
                        str(carpeta / "mezcla.wav")], check=True)
        pz = Pizarra(carpeta / "video.py")
        try:
            pz.exportar(lambda p, tt: p.linea(300, 540, 1620, 540, p=seg(tt, 0, .8), semilla=1), salida=salida)
        except SystemExit:
            pass
    return probar_salida("pizarra", hacer, cuadros=math.ceil(1.0 * FPS) + 1)


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    sys.exit(__doc__)
