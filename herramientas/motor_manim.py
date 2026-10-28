"""Motor Manim del explicativo (técnica 4): estilo 3Blue1Brown, piezas dibujadas con formas, una escena base
que va al compás de la voz, efectos de sonido anotados en su momento y un CONTROL DE TEXTOS ENCIMADOS.

    from motor_manim import *          # (el video agrega herramientas/ a sys.path)
    class MiVideo(Explicativo):
        CARPETA = Path(__file__).resolve().parent     # tiene tiempos.json (narrar.py)
        def construct(self): ...

    <venv-manim>/Scripts/python herramientas/motor_manim.py --probar
        (rompe el control a propósito: cada caso dice «ok» o «FALLA»; sale con 1 si el control no detecta algo)

El control corre después de cada `play`: con lo que queda en pantalla, mira que ningún texto toque a otro
texto, que ninguna línea o borde de forma pase por encima de un texto, que ningún texto se salga del cuadro y
que ninguno sea chico. Lo que se encima a propósito (un sello, una tachadura) se marca con `encima(m)`.
Al terminar escribe `efectos.json` (lo lee mezclar.py) e imprime el control por frase; si hay fallas, la escena
se cae antes de juntar el video: primero se prueba rápido con `-s` (sin dibujar cuadros, ~1 min).

Pantalla nunca quieta: la cámara flota (`deriva`: un círculo de .04 unidades, ≤ 2 % de alejamiento) durante
cada animación y durante las esperas de más de RESPIRA_MIN, salvo en las pausas de voz (≥ 400 ms entre frases de
tiempos.json, la misma regla de critico.py). El cuadro 0 es una portada (TITULO) que se va con la primera animación.
Se apagan con RESPIRA = False, PORTADA = False o, en una sola espera, self.wait(d, respira=False).
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

# Dos motores con la misma API: ManimCE (por omisión) y ManimGX (VIDEOS_MOTOR=gx; venv aparte con Python 3.13,
# lo lanza herramientas/render_gx.py). Medido en una escena de 5:44: GX 4,6× más rápido, 1,7× más RAM.
GX = os.environ.get("VIDEOS_MOTOR") == "gx"
if GX:
    from manimgx import *  # noqa: F401,F403
    from manimgx.animation.timeline import prepare as prepare_animation
    from pathlib import Path   # manimgx exporta su propio Path: se vuelve al de la biblioteca estándar
else:
    from manim import *  # noqa: F401,F403
    from manim.animation.animation import prepare_animation

FONDO = "#0f1216"
AZUL, CELESTE, AMARILLO, VERDE, ROJO, GRIS, BLANCO = "#58C4DD", "#9CDCEB", "#F4D35E", "#83C167", "#FC6255", "#8A9099", "#ECEFF1"
SERIF, MONO = "Cambria", "Consolas"
config.background_color = FONDO

# efectos del banco (recursos/efectos/listos, Kenney CC0 y Mixkit)
POP, CLIC, BIEN, MAL = "pop/burbuja-pop.wav", "interfaz/kenney-click-001.wav", "exito/kenney-confirmation-001.wav", "error/kenney-error-004.wav"
BARRIDO, GOLPE, METAL, SUAVE = ("transicion/whoosh-rapido.wav", "impacto/kenney-punch-heavy-000.wav",
                                "impacto/kenney-metal-heavy-000.wav", "impacto/kenney-soft-heavy-000.wav")

MARGEN = .06         # distancia mínima entre un texto y cualquier otra cosa (unidades de Manim; el cuadro mide 8 de alto)
TAM_MIN = 24          # ningún texto más chico que esto (a 1080p, ~30 px de alto de letra)
BORDE_X, BORDE_Y = 7.0, 3.9

# respiración de las esperas: la cámara flota en un círculo chico que pasa por el centro, y se aleja lo justo
# (≤ 2 %) para que nada del cuadro original quede afuera. Se mueve sólo durante las esperas; entre una y otra queda
# donde estaba (sin saltos). Velocidad R·W = .08 unidades/s (~11 px/s a 1080p): lo mínimo que se ve en el MP4.
RESPIRA_R, RESPIRA_W = .04, 2.0
PAUSA_VOZ = .4        # un silencio entre frases de 400 ms o más es pausa de voz: ahí la pantalla puede quedar quieta


def deriva(tau, r=RESPIRA_R, w=RESPIRA_W):
    """Centro y escala de la cámara tras `tau` segundos de respiración (tau=0: el cuadro tal cual)."""
    c = r * np.array([np.cos(w * tau) - 1, np.sin(w * tau), 0.0])
    return c, 1 + np.linalg.norm(c) / (config.frame_height / 2)    # (s−1)·alto/2 = |c|: el cuadro original cabe


# ───────────── piezas ─────────────
def tx(s, tam=32, color=BLANCO, fuente=SERIF, **k):
    return Text(s, font=fuente, font_size=tam, color=color, **k)


def caja(s, color=AZUL, ancho=3.2, alto=.8, tam=30, fuente=SERIF, relleno=.12):
    r = RoundedRectangle(corner_radius=.14, width=ancho, height=alto, stroke_color=color, stroke_width=3,
                         fill_color=color, fill_opacity=relleno)
    t = tx(s, tam, BLANCO, fuente)
    if t.width > ancho - .4: t.scale_to_fit_width(ancho - .4)
    return VGroup(r, t.move_to(r))


def contador(valor, tam, color, pos):
    """Número que cuenta solo, con Text (Integer/DecimalNumber piden LaTeX, que no está). Devuelve
    (tracker, mobject, [color]); se anima con `tracker.animate.set_value(n)` y el color se cambia en la lista."""
    tr = ValueTracker(valor); col = [color]
    mob = always_redraw(lambda: tx(str(int(round(tr.get_value()))), tam, col[0]).move_to(pos))
    return tr, mob, col


def encima(*mobs):
    """Marca lo que se encima a propósito (sello, tachadura, resaltado): el control no lo cuenta."""
    for m in mobs:
        for f in m.get_family(): f.encima = True
    return mobs[0] if len(mobs) == 1 else VGroup(*mobs)


def nube_ic(color, s=1.0):
    c = VGroup(Circle(.26 * s), Circle(.36 * s).shift(RIGHT * .32 * s + UP * .12 * s), Circle(.24 * s).shift(RIGHT * .66 * s))
    return c.set_stroke(color, 3).set_fill(color, .22).center()


def llave_ic(color, s=1.0):
    aro = Circle(.14 * s, color=color, stroke_width=5)
    tallo = Line(RIGHT * .14 * s, RIGHT * .6 * s, color=color, stroke_width=5)
    dientes = VGroup(Line(RIGHT * .42 * s, RIGHT * .42 * s + DOWN * .13 * s, color=color, stroke_width=5),
                     Line(RIGHT * .54 * s, RIGHT * .54 * s + DOWN * .18 * s, color=color, stroke_width=5))
    return VGroup(aro, tallo, dientes).center()


def candado_ic(color, s=1.0):
    cuerpo = RoundedRectangle(corner_radius=.06 * s, width=.56 * s, height=.44 * s, color=color, fill_color=color,
                              fill_opacity=.3, stroke_width=4)
    arco = Arc(radius=.17 * s, start_angle=0, angle=PI, color=color, stroke_width=5).next_to(cuerpo, UP, buff=0)
    return VGroup(cuerpo, arco).center()


def check_ic(p=ORIGIN, color=VERDE, s=.3):
    return VMobject(stroke_color=color, stroke_width=7).set_points_as_corners(
        [p + s * np.array([-.9, 0, 0]), p + s * np.array([-.25, -.6, 0]), p + s * np.array([1, .8, 0])])


def equis_ic(p=ORIGIN, color=ROJO, s=.28):
    return VGroup(Line(p + s * UL, p + s * DR, color=color, stroke_width=7), Line(p + s * UR, p + s * DL, color=color, stroke_width=7))


def reloj_ic(color=AMARILLO, s=1.0):
    """El «pendiente» de todo el video: un reloj amarillo."""
    c = Circle(.32 * s, color=color, stroke_width=4, fill_color=color, fill_opacity=.12)
    a = VGroup(Line(ORIGIN, UP * .2 * s, color=color, stroke_width=4), Line(ORIGIN, RIGHT * .14 * s, color=color, stroke_width=4))
    return VGroup(c, a)


def alerta_ic(color=ROJO, s=1.0):
    t = Triangle(color=color, stroke_width=4, fill_color=color, fill_opacity=.15).scale(.42 * s)
    b = VGroup(Line(UP * .1 * s, DOWN * .1 * s, color=color, stroke_width=5), Dot(DOWN * .2 * s, .04 * s, color=color))
    return VGroup(t, b.move_to(t.get_center() + DOWN * .04 * s))


def escudo_ic(color=AZUL, s=1.0):
    e = VMobject(stroke_color=color, stroke_width=4, fill_color=color, fill_opacity=.15)
    e.set_points_smoothly([np.array(p) * s for p in [(-.36, .36, 0), (0, .44, 0), (.36, .36, 0), (.32, -.08, 0), (0, -.46, 0),
                                                     (-.32, -.08, 0), (-.36, .36, 0)]])
    return e


def lupa_ic(color=VERDE, s=1.0):
    return VGroup(Circle(.3 * s, color=color, stroke_width=5), Line(ORIGIN, DR * .38 * s, color=color, stroke_width=7).shift(DR * .25 * s))


def persona_ic(color=CELESTE, s=1.0):
    cabeza = Circle(.15 * s, color=color, stroke_width=4, fill_color=color, fill_opacity=.25).shift(UP * .2 * s)
    cuerpo = Arc(radius=.26 * s, start_angle=0, angle=PI, color=color, stroke_width=4).shift(DOWN * .22 * s)
    return VGroup(cabeza, cuerpo)


def telefono_ic(color=BLANCO, s=1.0):
    return VGroup(RoundedRectangle(corner_radius=.22 * s, width=1.3 * s, height=2.3 * s, color=color, stroke_width=4),
                  Line(LEFT * .2 * s, RIGHT * .2 * s, color=color, stroke_width=4).shift(DOWN * .95 * s))


def documento_ic(color=CELESTE, s=1.0):
    r = Rectangle(width=.7 * s, height=.9 * s, color=color, stroke_width=4, fill_color=color, fill_opacity=.12)
    ls = VGroup(*[Line(LEFT * .22 * s, RIGHT * (.22 - .08 * k) * s, color=color, stroke_width=3) for k in range(3)])
    return VGroup(r, ls.arrange(DOWN, buff=.14 * s, aligned_edge=LEFT).move_to(r))


def huella_ic(color=VERDE, s=1.0):
    return VGroup(*[Arc(radius=(.1 + .09 * k) * s, start_angle=PI * (.15 + .03 * k), angle=PI * (1.4 - .06 * k),
                        color=color, stroke_width=4) for k in range(5)])


# ───────────── el control de textos encimados ─────────────
def _hojas(mobs):
    """Textos (enteros) y formas sueltas que se ven, sin repetir."""
    textos, formas, vistos = [], [], set()
    def rec(m):
        if id(m) in vistos: return
        vistos.add(id(m))
        if isinstance(m, Text):
            if m.get_fill_opacity() > .05: textos.append(m)
            return
        if isinstance(m, VMobject) and len(m.points) >= 4 and (
                (m.get_stroke_opacity() > .05 and m.get_stroke_width() > 0) or m.get_fill_opacity() > .05):
            formas.append(m)
        for s in m.submobjects: rec(s)
    for m in mobs: rec(m)
    return textos, formas


def _caja(m, margen=0.0):
    a, b = m.get_critical_point(DL), m.get_critical_point(UR)
    return a[0] - margen, a[1] - margen, b[0] + margen, b[1] + margen


def _muestras(m, n=10):
    """Puntos a lo largo del trazo de una forma (curvas de Bézier cúbicas de Manim)."""
    p = m.points[: len(m.points) // 4 * 4].reshape(-1, 4, 3)
    t = np.linspace(0, 1, n)[None, :, None]
    b = ((1 - t) ** 3 * p[:, 0:1] + 3 * (1 - t) ** 2 * t * p[:, 1:2] + 3 * (1 - t) * t ** 2 * p[:, 2:3] + t ** 3 * p[:, 3:4])
    return b.reshape(-1, 3)


def _nombre(m):
    return getattr(m, "original_text", type(m).__name__)[:40].replace("\n", " ")


def revisar(mobs):
    """Lista de fallas de lo que está en pantalla: (tipo, texto, con qué)."""
    textos, formas = _hojas(mobs)
    ancho, alto = config.frame_width / 2, config.frame_height / 2
    fuera = lambda c: c[0] > ancho or c[2] < -ancho or c[1] > alto or c[3] < -alto
    textos = [t for t in textos if not fuera(_caja(t))]         # lo que salió entero del cuadro no se ve
    fallas = []
    for t in textos:
        if getattr(t, "encima", False): continue
        x0, y0, x1, y1 = _caja(t)
        if x0 < -BORDE_X or x1 > BORDE_X or y0 < -BORDE_Y or y1 > BORDE_Y: fallas.append(("fuera del cuadro", _nombre(t), ""))
        if getattr(t, "font_size", TAM_MIN) < TAM_MIN - .5: fallas.append(("chico", _nombre(t), f"{t.font_size:.0f}"))
    for i, t in enumerate(textos):
        a = _caja(t, MARGEN)
        for u in textos[i + 1:]:
            if getattr(t, "encima", False) or getattr(u, "encima", False): continue
            b = _caja(u)
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]: fallas.append(("texto sobre texto", _nombre(t), _nombre(u)))
        if getattr(t, "encima", False): continue
        for f in formas:
            if getattr(f, "encima", False): continue
            q = _muestras(f)
            dentro = (q[:, 0] > a[0]) & (q[:, 0] < a[2]) & (q[:, 1] > a[1]) & (q[:, 1] < a[3])
            if dentro.any(): fallas.append(("línea sobre texto", _nombre(t), type(f).__name__))
    return fallas


# ───────────── la escena base ─────────────
class _Deriva(Animation):
    """La cámara de tau0 a tau0 + run_time por `deriva`, siempre a ritmo parejo (no usa el rate_func del play)."""
    def __init__(self, frame, tau0, run_time):
        super().__init__(frame, run_time=run_time)
        self.tau0 = tau0

    def interpolate(self, alpha):
        c, s = deriva(self.tau0 + alpha * self.run_time)
        self.mobject.scale_to_fit_height(config.frame_height * s).move_to(c)


class Explicativo(MovingCameraScene):
    CARPETA = None        # carpeta del video (tiempos.json; ahí se escribe efectos.json)
    TITULO = None         # portada del primer cuadro: "título" o ("título", "subtítulo"); None: el nombre de la carpeta
    PORTADA = True        # False: el video arranca como lo arme construct (ojo: si arranca vacío, el primer cuadro es negro)
    RESPIRA = True        # False: las esperas quedan quietas (también por espera: self.wait(d, respira=False))
    RESPIRA_MIN = .5      # sólo respiran las esperas más largas que esto (s)
    SINCRO_VOZ = False    # True: en(i, frac) espera a la hora REAL de la voz (pausas de narracion.wav, sincro_voz.py),
                          # no a la cuenta proporcional al texto, que se corre hasta 3 s en frases largas

    def setup(self):
        self.T = json.loads((Path(self.CARPETA) / "tiempos.json").read_text(encoding="utf-8"))
        self.frase = "inicio"
        self.efectos, self.control = [], {}
        seg = sorted((s["inicio"], s["inicio"] + s["dur"]) for s in self.T["seg"].values())
        pausas = [(0.0, seg[0][0])] + [(a[1], b[0]) for a, b in zip(seg, seg[1:])] + [(seg[-1][1], self.T.get("total", 0))]
        self.pausas = [(a, b) for a, b in pausas if b - a >= PAUSA_VOZ]    # la misma regla que critico.py --quietos
        self.tau = 0.0
        self.portada = None
        if self.PORTADA:
            t = self.TITULO or Path(self.CARPETA).name.replace("-", " ").capitalize()
            titulo, sub = (t, None) if isinstance(t, str) else t
            g = tx(titulo, 60)
            if g.width > 12: g.scale_to_fit_width(12)
            raya = Line(LEFT * min(g.width / 2, 3), RIGHT * min(g.width / 2, 3), color=AZUL, stroke_width=4)
            self.portada = VGroup(g, raya, *([tx(sub, 34, GRIS)] if sub else [])).arrange(DOWN, buff=.4)
            self.add(self.portada)          # el cuadro 0 ya es una composición terminada, no un fundido desde negro

    def ini(self, i): return self.T["seg"][i]["inicio"]
    def dur(self, i): return self.T["seg"][i]["dur"]

    def hasta(self, t):
        d = t - self.renderer.time
        if d > 1 / 60: self.wait(d)

    def en(self, i, frac=0.0):
        """Espera al momento `frac` (0–1) de la frase i."""
        self.frase = i
        if self.SINCRO_VOZ and frac > 0:
            if not hasattr(self, "_voz"):
                from sincro_voz import Voz
                self._voz = Voz(self.CARPETA)
            return self.hasta(self._voz.momento(i, frac))
        self.hasta(self.ini(i) + self.dur(i) * frac)

    def sfx(self, archivo, db=-14, desfase=0.0, pico=False):
        """Un efecto real (recursos/efectos/listos) en el momento actual + desfase; `pico`: su golpe cae ahí."""
        self.efectos.append({"archivo": archivo, "en": round(self.renderer.time + desfase, 3), "db": db,
                             **({"alinear": "pico"} if pico else {})})

    # piezas de movimiento que se repiten (cada una anota su sonido)
    def aparece(self, *mobs, rt=.5, sonido=POP, db=-18):
        self.sfx(sonido, db, .05)
        self.play(*[FadeIn(m, shift=UP * .15) for m in mobs], run_time=rt)

    def salen(self, *mobs, rt=.45):
        mobs = [m for m in mobs if m is not None]          # un grupo sirve aunque sus piezas estén sueltas en la escena
        if mobs: self.play(*[FadeOut(m, shift=UP * .2) for m in mobs], run_time=rt)

    def uno_a_uno(self, mobs, rt=1.2, lag=.3, sonido=POP, db=-19):
        """Entrada escalonada con un sonido por pieza, en el momento en que empieza cada una."""
        n = len(mobs); d = rt / (1 + lag * (n - 1))
        for k in range(n): self.sfx(sonido, db, k * lag * d + .03)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * .15) for m in mobs], lag_ratio=lag), run_time=rt)

    def bien(self, *anims, rt=.5, db=-15):
        self.sfx(BIEN, db, .1)
        self.play(*anims, run_time=rt)

    def mal(self, *anims, rt=.5, db=-15):
        self.sfx(MAL, db, .1)
        self.play(*anims, run_time=rt)

    def capa(self, n, nombre, color=AZUL):
        """Cambio de capa sin corte: todo lo de antes se va a la izquierda y la cabecera nueva entra por la
        derecha, como si la cámara pasara a la pizarra siguiente (con un barrido)."""
        viejos = list(self.mobjects)
        cab = VGroup(*([tx(str(n), 52, color)] if n is not None else []), tx(nombre, 46)).arrange(RIGHT, buff=.3)
        cab.to_corner(UL, buff=.45).shift(RIGHT * 15)
        self.sfx(BARRIDO, -11, .45, pico=True)
        self.play(*[m.animate.shift(LEFT * 15) for m in viejos], cab.animate.shift(LEFT * 15), run_time=.9, rate_func=smooth)
        self.remove(*viejos)
        self.cab = cab
        return cab

    def play(self, *a, **k):
        if not all(isinstance(x, Wait) for x in a):
            a = [prepare_animation(x) for x in a]
            rt = k.get("run_time") or max(x.run_time for x in a)
            p = self.portada
            if p is not None and p in self.mobjects and not any(x.mobject is p for x in a):
                a.append(FadeOut(p, rate_func=lambda u: smooth(min(1.0, u * max(rt / .5, 1.0)))))  # se va en ≤ 0,5 s
            if self.RESPIRA:               # la deriva sigue durante la animación: sin cuadros quietos en sus bordes suaves
                a.append(_Deriva(self.camera.frame, self.tau, rt)); self.tau += rt
        super().play(*a, **k)
        self.remove(self.camera.frame)     # la cámara no es parte de la pizarra (capa, limpia, control)
        fallas = revisar(self.mobjects)
        c = self.control.setdefault(self.frase, [])
        for f in fallas:
            if f not in c: c.append(f)

    def wait(self, duration=DEFAULT_WAIT_TIME, stop_condition=None, frozen_frame=None, respira=None):
        """Las esperas de más de RESPIRA_MIN respiran (la cámara flota, ver `deriva`) salvo en las pausas de voz."""
        if not (self.RESPIRA if respira is None else respira) or stop_condition or frozen_frame \
                or duration <= self.RESPIRA_MIN:
            return super().wait(duration, stop_condition, frozen_frame)
        t0, t1 = self.renderer.time, self.renderer.time + duration
        cortes = sorted({t0, t1, *[x for a, b in self.pausas for x in (a, b) if t0 < x < t1]})
        tramos = []                                        # [duración, quieto]; los de menos de un cuadro se suman al anterior
        for a, b in zip(cortes, cortes[1:]):
            quieto = any(p <= (a + b) / 2 <= q for p, q in self.pausas)
            if tramos and (b - a < 1 / config.frame_rate or tramos[-1][1] == quieto): tramos[-1][0] += b - a
            else: tramos.append([b - a, quieto])
        if len(tramos) > 1 and tramos[0][0] < 1 / config.frame_rate: tramos[1][0] += tramos.pop(0)[0]
        for d, quieto in tramos:
            if quieto: super().wait(d)
            else:
                Scene.play(self, _Deriva(self.camera.frame, self.tau, d))
                self.remove(self.camera.frame)
                self.tau += d

    def tear_down(self):
        # VIDEOS_EFECTOS: otro nombre de archivo, para el render por tramos (-n): cada tramo escribe el suyo y sólo el
        # último (que recorre la escena entera) trae todos los efectos
        (Path(self.CARPETA) / os.environ.get("VIDEOS_EFECTOS", "efectos.json")).write_text(json.dumps(self.efectos, ensure_ascii=False, indent=1), encoding="utf-8")
        malas = 0
        print("\nControl de textos encimados (por frase):")
        for frase, fallas in self.control.items():
            print(f"  {'FALLA' if fallas else 'ok':5s} {frase}")
            for tipo, a, b in fallas: print(f"          {tipo}: «{a}»" + (f" · {b}" if b else ""))
            malas += bool(fallas)
        print(f"  {len(self.control) - malas} ok, {malas} FALLA · {len(self.efectos)} efectos en efectos.json")
        if malas: raise SystemExit(f"control de textos: {malas} frases con fallas (el video no se junta)")


# ───────────── prueba del control (se rompe a propósito) ─────────────
def probar():
    import tempfile
    config.media_dir = tempfile.mkdtemp(prefix="manim-probar-")      # la caché de textos no va al repo
    casos = []
    def caso(nombre, mobs, espera):
        f = revisar(mobs)
        encontro = {x[0] for x in f}
        bien = (espera in encontro) if espera else not f
        casos.append(bien)
        print(f"  {'ok' if bien else 'FALLA'}  {nombre}" + ("" if bien else f"  (esperaba {espera or 'nada'}, dio {sorted(encontro) or 'nada'})"))
    print("Prueba del control de textos:")
    caso("texto dentro de su caja", [caja("hola", AZUL, 3, .8)], None)
    caso("dos textos separados", [tx("uno").shift(LEFT * 2), tx("dos").shift(RIGHT * 2)], None)
    caso("texto sobre texto", [tx("uno"), tx("dos").shift(RIGHT * .3)], "texto sobre texto")
    caso("texto que cruza el borde de una caja", [Rectangle(width=2, height=1), tx("largo texto").shift(RIGHT * 1)], "línea sobre texto")
    caso("flecha que atraviesa un texto", [tx("en medio"), Arrow(LEFT * 3, RIGHT * 3)], "línea sobre texto")
    caso("flecha que llega cerca sin tocar", [tx("destino").shift(RIGHT * 2), Arrow(LEFT * 3, RIGHT * .3, buff=0)], None)
    caso("punto dentro de un texto", [tx("punto"), Dot(ORIGIN)], "línea sobre texto")
    caso("texto que se sale del cuadro", [tx("afuera").shift(RIGHT * 6.8)], "fuera del cuadro")
    caso("texto chico", [tx("chico", 16)], "chico")
    caso("sello marcado encima", [caja("depósito", GRIS, 3, 2), encima(tx("403", 60, ROJO).shift(UP * .5))], None)
    caso("tachadura marcada encima", [t := tx("promesa"), encima(Line(t.get_left(), t.get_right(), color=ROJO))], None)
    caso("texto invisible (opacidad 0)", [tx("oculto").set_opacity(0), Rectangle(width=.5, height=.5)], None)
    print(f"  {sum(casos)} ok, {len(casos) - sum(casos)} FALLA")
    # la respiración: la cámara a la deriva sigue viendo todo el cuadro original y se mueve lo bastante para notarse
    print("Prueba de la respiración de las esperas:")
    alto, ancho, dt = config.frame_height, config.frame_width, 1 / 30
    def cabe(tau, alejar=True):
        c, s = deriva(tau)
        s = s if alejar else 1.0
        return abs(c[0]) <= (s - 1) * ancho / 2 + 1e-9 and abs(c[1]) <= (s - 1) * alto / 2 + 1e-9
    def rapidez(tau, r=RESPIRA_R, w=RESPIRA_W):              # unidades/s en pantalla del centro de la pizarra
        (c0, s0), (c1, s1) = deriva(tau, r, w), deriva(tau + dt, r, w)
        return np.linalg.norm(c1 / s1 - c0 / s0) / dt
    taus = np.linspace(0, 60, 2401)
    def caso_r(nombre, bien_esperado, dio):
        casos.append(dio == bien_esperado)
        print(f"  {'ok' if dio == bien_esperado else 'FALLA'}  {nombre}")
    caso_r("en tau=0 el cuadro queda tal cual", True, bool(np.allclose(deriva(0)[0], 0) and deriva(0)[1] == 1))
    caso_r("la deriva nunca deja afuera el cuadro original", True, all(cabe(t) for t in taus))
    caso_r("sin alejarse sí lo dejaría afuera (la guardia ve)", False, all(cabe(t, alejar=False) for t in taus[1:]))
    caso_r("se aleja a lo más 2 %", True, max(deriva(t)[1] for t in taus) <= 1.02 + 1e-9)
    caso_r("se mueve a .07 unidades/s o más todo el tiempo (se nota en el MP4)", True, min(rapidez(t) for t in taus) >= .07)
    caso_r("a la mitad de rapidez no se notaría (la guardia ve)", False,
           min(rapidez(t, w=RESPIRA_W / 2) for t in taus) >= .07)
    print(f"  {sum(casos)} ok, {len(casos) - sum(casos)} FALLA en total")
    return all(casos)


if __name__ == "__main__" and "--probar" in sys.argv:
    sys.exit(0 if probar() else 1)
