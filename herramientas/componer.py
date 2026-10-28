"""Montaje final de un video renderizado fuera del navegador (p. ej. Blender): le pone título, subtítulos
del color de quien habla, fundidos y «Continuará…», y lo une con el audio en un MP4.

Uso:
    .venv/Scripts/python herramientas/componer.py <carpeta-del-video> --capturas   # render/blender_crudo → render/capturas
    .venv/Scripts/python herramientas/componer.py <carpeta-del-video> --video       # render/blender_cuadros → render/<técnica>_<video>.mp4
      --borrador          toma render/blender_borrador (720p, se agranda) → <nombre>_borrador.mp4
      --tramo 26.8 47.3   monta sólo ese tramo (segundos), con su audio → <nombre>_26.8-47.3.mp4
      --ia                los cuadros de la escena con los niños de Hunyuan3D (render/…_ia) → <nombre>_ia….mp4
    .venv/Scripts/python herramientas/componer.py --probar      # montaje de 1 s en una carpeta temporal (no toca render/)

Lee de la carpeta del video: tiempos.js, mezcla.wav (o narracion.wav) y montaje.json:
    {"titulo": ["El faro", "un cuento propio", "Capítulo 1 · La tormenta"],
     "titulo_hasta": "atardecer",            # el título se va al empezar esa frase
     "continuara": "cierre",                 # «Continuará…» al final de esa frase
     "negro_en": ["cierre"],                 # fundido a negro breve al empezar esas frases (cambio de lugar)
     "colores": {"farera": "#ffd98a", "nino": "#a9d4ff"}}
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from color_mp4 import COLOR_709

RAIZ = Path(__file__).resolve().parent.parent
W, H, FPS = 1920, 1080, 30
FUENTES = Path("C:/Windows/Fonts")


def fuente(nombre, tam):
    for n in nombre.split("|"):
        try:
            return ImageFont.truetype(str(FUENTES / n), tam)
        except OSError:
            continue
    return ImageFont.load_default()


def clamp(x, a=0.0, b=1.0): return min(b, max(a, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b != a else float(t >= b)


class Montaje:
    def __init__(self, carpeta):
        self.carpeta = Path(carpeta).resolve()
        txt = (self.carpeta / "tiempos.js").read_text(encoding="utf-8")
        self.TI = json.loads(re.search(r"=\s*(\{.*\})\s*;", txt, re.S).group(1))
        self.cfg = json.loads((self.carpeta / "montaje.json").read_text(encoding="utf-8"))
        self.DUR = self.TI["total"]
        self.f_sub = fuente("segoeui.ttf", 38)
        self.f_tit = fuente("georgiaz.ttf|georgiab.ttf", 104)
        self.f_sub2 = fuente("georgiai.ttf|georgia.ttf", 46)
        self.f_cap = fuente("georgia.ttf", 30)
        self.cache = {}

    def A(self, i): return self.TI["seg"][i]["inicio"]
    def fin(self, i): s = self.TI["seg"][i]; return s["inicio"] + s["dur"]

    def trozos(self, texto, maximo=80):
        partes = re.split(r"(?<=[.:;?!,])\s+", texto); out = []
        for p in partes:
            if out and len(out[-1]) + 1 + len(p) <= maximo: out[-1] += " " + p
            else: out.append(p)
        return out

    def subtitulo(self, t):
        for i in self.TI["orden"]:
            s = self.TI["seg"][i]
            if t < s["inicio"] - .1 or t > s["inicio"] + s["dur"] + .25:
                continue
            ts = self.cache.setdefault(i, self.trozos(s["texto"]))
            total = sum(len(x) for x in ts); a = s["inicio"]; k = 0
            for k in range(len(ts)):
                b = a + s["dur"] * len(ts[k]) / total
                if t < b or k == len(ts) - 1: break
                a = b
            return ts[k], s.get("quien")
        return None, None

    def texto_centrado(self, d, xy, txt, f, color, alfa, sombra=True):
        if alfa <= 0: return
        c = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        x, y = xy; w = d.textlength(txt, font=f)
        if sombra:
            d.text((x - w / 2 + 3, y + 3), txt, font=f, fill=(0, 0, 0, int(140 * alfa)), anchor="lm")
        d.text((x - w / 2, y), txt, font=f, fill=(*c, int(255 * alfa)), anchor="lm")

    def cuadro(self, img, t):
        img = img.convert("RGBA")
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
        # título
        tit = self.cfg.get("titulo")
        if tit:
            th = self.A(self.cfg.get("titulo_hasta", self.TI["orden"][1]))
            k = seg(t, .3, 1.4) * (1 - seg(t, th + 1.5, th + 3))
            if k > 0:
                self.texto_centrado(d, (600, 250), tit[0], self.f_tit, "#fff4dc", k)
                if len(tit) > 1: self.texto_centrado(d, (600, 330), tit[1], self.f_sub2, "#fff4dc", k)
                if len(tit) > 2: self.texto_centrado(d, (600, 395), tit[2], self.f_cap, "#ffd98a", k)
        cont = self.cfg.get("continuara")
        if cont:
            s = self.TI["seg"][cont]; a = s["inicio"] + s["dur"] * .75; b = s["inicio"] + s["dur"] + .4
            k = seg(t, a, b) * (1 - seg(t, self.DUR - 1, self.DUR - .2))
            self.texto_centrado(d, (W / 2, 190), "Continuará…", self.f_sub2, "#fff4dc", k)
        # subtítulo
        linea, quien = self.subtitulo(t)
        if linea:
            w = min(1760, d.textlength(linea, font=self.f_sub) + 64)
            d.rounded_rectangle((W / 2 - w / 2, 978, W / 2 + w / 2, 1042), 14, fill=(0, 0, 0, 184))
            col = self.cfg.get("colores", {}).get(quien, "#f2f5fa")
            c = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
            d.text((W / 2, 1011), linea, font=self.f_sub, fill=(*c, 255), anchor="mm")
        img = Image.alpha_composite(img, capa)
        # fundidos a negro: al empezar, al terminar y en los cambios de lugar
        neg = max(1 - seg(t, 0, .8), seg(t, self.DUR - 1.2, self.DUR))
        for i in self.cfg.get("negro_en", []):
            a = self.A(i); neg = max(neg, 1 - min(1, abs(t - a) / .45))
        if neg > 0:
            img = Image.blend(img, Image.new("RGBA", img.size, (0, 0, 0, 255)), neg)
        return img.convert("RGB")

    def capturas(self):
        crudo = RAIZ / "render" / "blender_crudo"; out = RAIZ / "render" / "capturas"
        n = 0
        for f in sorted(crudo.glob("*.jpg")):
            t = float(re.search(r"_([\d-]+)\.jpg$", f.name).group(1).replace("-", "."))
            self.cuadro(Image.open(f), t).save(out / f.name, quality=92); n += 1
        print(f"capturas compuestas: {n}")

    def video(self, borrador=False, tramo=None, ia=False, cuadros=None, salida=None):
        # cuadros y salida sólo los cambia --probar (trabaja en una carpeta temporal, sin tocar render/)
        cuadros = cuadros or RAIZ / "render" / (("blender_borrador" if borrador else "blender_cuadros") + ("_ia" if ia else ""))
        nombre = f"{self.carpeta.parent.name}_{self.carpeta.name}" + ("_ia" if ia else "") + ("_borrador" if borrador else "")
        if tramo: nombre += f"_{tramo[0]:g}-{tramo[1]:g}"
        salida = salida or RAIZ / "render" / f"{nombre}.mp4"
        audio = self.carpeta / "mezcla.wav"
        if not audio.exists(): audio = self.carpeta / "narracion.wav"
        n = math.ceil(self.DUR * FPS) + 1
        f0, f1 = (int(tramo[0] * FPS) + 1, min(n, int(tramo[1] * FPS) + 1)) if tramo else (1, n)
        faltan = [f for f in range(f0, f1 + 1) if not (cuadros / f"c_{f:04d}.jpg").exists() or (cuadros / f"c_{f:04d}.jpg").stat().st_size == 0]
        if faltan:
            sys.exit(f"faltan {len(faltan)} cuadros (el primero: {faltan[0]}); terminar el render antes de montar")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               *(["-ss", f"{(f0 - 1) / FPS:.3f}"] if tramo else []), "-i", str(audio), "-c:a", "aac", "-b:a", "160k", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", *COLOR_709, "-shortest", str(salida)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(f0, f1 + 1):
            img = Image.open(cuadros / f"c_{f:04d}.jpg")
            if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS)     # el borrador viene a 720p
            img = self.cuadro(img, (f - 1) / FPS)
            p.stdin.write(img.tobytes())
            if f % 300 == 0: print(f"  {f}/{n}", flush=True)
        p.stdin.close()
        ok = p.wait() == 0
        print(f"montaje: {'listo' if ok else 'ERROR'} -> {salida}")
        sys.exit(0 if ok else 1)


def probar():
    """Un montaje de 1 s en una carpeta temporal: 31 cuadros JPEG + subtítulo + audio → MP4 con color etiquetado,
    31 cuadros y audio (color_mp4.probar_salida); no toca render/."""
    from color_mp4 import probar_salida

    def hacer(_entrada, salida, t):
        carpeta, cuadros = t / "video", t / "cuadros"
        carpeta.mkdir(); cuadros.mkdir()
        ti = {"total": 1.0, "orden": ["a"], "seg": {"a": {"inicio": .1, "dur": .6, "texto": "Prueba del montaje."}}}
        (carpeta / "tiempos.js").write_text("window.TIEMPOS = " + json.dumps(ti) + ";", encoding="utf-8")
        (carpeta / "montaje.json").write_text("{}", encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=1.2",
                        str(carpeta / "mezcla.wav")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={W}x{H}:r={FPS}:d=1.04",
                        "-frames:v", "31", "-start_number", "1", str(cuadros / "c_%04d.jpg")], check=True)
        try:
            Montaje(carpeta).video(cuadros=cuadros, salida=salida)
        except SystemExit:
            pass
    return probar_salida("componer", hacer, cuadros=31)


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    m = Montaje(sys.argv[1])
    if "--capturas" in sys.argv: m.capturas()
    else:
        tr = sys.argv[sys.argv.index("--tramo") + 1:sys.argv.index("--tramo") + 3] if "--tramo" in sys.argv else None
        m.video(borrador="--borrador" in sys.argv, tramo=tuple(map(float, tr)) if tr else None, ia="--ia" in sys.argv)
