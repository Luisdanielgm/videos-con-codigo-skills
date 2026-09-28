"""Técnica 4: el video en pizarra, dibujado con cairo desde Python (sin navegador).

Uso:  .venv/Scripts/python 04-explicativo-narrado/red-neuronal/video.py --capturas 3.5,40
      .venv/Scripts/python 04-explicativo-narrado/red-neuronal/video.py --exportar
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "herramientas"))
from pizarra import Pizarra, clamp, ease, lerp, seg  # noqa: E402

pz = Pizarra(__file__)
P, A, F, vis, SIG = pz.P, pz.A, pz.F, pz.vis, pz.SIG
sig = lambda z: 1 / (1 + math.exp(-z))

TITULOS = {
    "idea": "1 · Aprender con ejemplos", "numeros": "2 · La computadora ve números", "neurona": "3 · Una neurona",
    "pesos": "3 · Una neurona: los pesos", "suma": "3 · Una neurona: la suma", "activacion": "3 · Una neurona: encenderse",
    "red": "4 · Una red de neuronas", "partes": "4 · Una red de neuronas", "intento": "5 · El primer intento",
    "error": "6 · Medir el error", "retro": "7 · Retropropagación", "ajuste": "8 · Ajustar los pesos",
    "montana": "9 · Descenso de gradiente", "repetir": "10 · Repetir", "resultado": "11 · El resultado",
}


def titulo(t):
    for i, s in TITULOS.items():
        al = min(seg(t, A(i) - .3, A(i) + .2), 1 - seg(t, SIG(i) - .3, SIG(i) + .2))
        if al > 0:
            pz.texto(s, 80, 70, 44, "azul", p=P(t, i, 0, .08) if i not in ("partes",) else 1, a=al, negrita=True)
            pz.linea(80, 110, 80 + pz.ancho_texto(s, 44, True), 112, P(t, i, .04, .12), "azul", 3, al, semilla=hash(i) % 97)


# ───── escena: título ─────
def escena_titulo(t):
    al = vis(t, "titulo", "titulo")
    def dib():
        pz.texto("¿Cómo aprende", 960, 400, 110, "negro", P(t, "titulo", 0, .25), alinear="centro", negrita=True)
        pz.texto("una red neuronal?", 960, 540, 110, "azul", P(t, "titulo", .15, .4), alinear="centro", negrita=True)
        pz.linea(560, 625, 1360, 630, P(t, "titulo", .4, .55), "rojo", 6, semilla=3)
        pz.texto("paso a paso, sin matemáticas difíciles", 960, 710, 40, "gris", P(t, "titulo", .5, .8), alinear="centro")
        # garabato de una red en la esquina
        for i, (x, y) in enumerate([(1560, 820), (1660, 780), (1660, 860), (1760, 820)]):
            pz.circulo(x, y, 18, P(t, "titulo", .6 + i * .05, .7 + i * .05), "naranja", 3, semilla=i)
        for i, (a, b) in enumerate([((1578, 820), (1642, 782)), ((1578, 820), (1642, 858)), ((1678, 780), (1742, 818)), ((1678, 860), (1742, 822))]):
            pz.linea(*a, *b, P(t, "titulo", .8 + i * .03, .88 + i * .03), "naranja", 3, semilla=20 + i)
    pz.capa(al, dib)


# ───── escena 1: aprender con ejemplos ─────
def escena_idea(t):
    al = vis(t, "idea", "idea")
    def dib():
        bx, by, bw, bh = 1180, 330, 460, 300
        pz.rect(bx, by, bw, bh, P(t, "idea", 0, .15), "negro", 5, semilla=1)
        pz.texto("red neuronal", bx + bw / 2, by + bh / 2, 54, "azul", P(t, "idea", .12, .25), alinear="centro", negrita=True)
        t0, v = A("idea"), 250
        vistos = 0
        for i in range(40):
            x = 120 + (t - t0) * v - i * 95
            if x > bx - 70:
                vistos += 1; continue
            if x < -80:
                continue
            y = 420 + math.sin(i * 2.3) * 70
            a = clamp((x + 80) / 150) * clamp((bx - 70 - x) / 100)
            pz.rect(x, y, 66, 84, 1, "negro", 3, a, semilla=100 + i, relleno="amarillo", a_relleno=.15)
            pz.texto(str(i % 10), x + 33, y + 36, 50, "negro", 1, a, alinear="centro")
        pz.texto(f"dibujos vistos: {vistos}", bx + bw / 2, by - 45, 38, "negro", P(t, "idea", .3, .4), alinear="centro")
        pz.texto("aprende mirando muchos ejemplos,", 120, 790, 46, "negro", P(t, "idea", .25, .45))
        pz.texto("como un niño que aprende los números", 120, 860, 46, "gris", P(t, "idea", .4, .6))
    pz.capa(al, dib)


# ───── escena 2: la imagen son números ─────
SEVEN = ["00000000", "01111110", "00000010", "00000100", "00001000", "00010000", "00100000", "00000000"]
PIX = [int(c) for fila in SEVEN for c in fila]


def escena_numeros(t):
    al = vis(t, "numeros", "numeros")
    def dib():
        gx, gy, cs = 260, 230, 64
        kG, kD, kN, kL = P(t, "numeros", 0, .15), P(t, "numeros", .1, .3), P(t, "numeros", .4, .62), P(t, "numeros", .72, .9)
        for k in range(9):   # la cuadrícula se dibuja a mano
            pz.linea(gx, gy + k * cs, gx + 8 * cs, gy + k * cs, clamp(kG * 9 - k * .5), "gris", 2, semilla=k)
            pz.linea(gx + k * cs, gy, gx + k * cs, gy + 8 * cs, clamp(kG * 9 - k * .5), "gris", 2, semilla=40 + k)
        n = 0
        for k, on in enumerate(PIX):
            r, c = divmod(k, 8)
            if on:
                n += 1
                if n <= kD * 11:
                    pz._color("negro", .85); pz.ctx.rectangle(gx + c * cs + 5, gy + r * cs + 5, cs - 10, cs - 10); pz.ctx.fill()
            pz.texto("1" if on else "0", gx + c * cs + cs / 2, gy + r * cs + cs / 2, 30, "amarillo" if on else "gris",
                     1, clamp(kN * 64 - k), alinear="centro", negrita=on)
        pz.texto("pintado = 1   ·   vacío = 0", gx + 4 * cs, gy + 8 * cs + 55, 36, "negro", kN, alinear="centro")
        for r in range(8):
            pz.texto("  ".join(SEVEN[r]), 1060, gy + r * cs + cs / 2, 40, "negro", clamp(kL * 8 - r))
        pz.flecha(gx + 8 * cs + 40, gy + 4 * cs, 1020, gy + 4 * cs, kL, "rojo", 5, semilla=9)
        pz.texto("= 64 números", 1260, gy + 8 * cs + 55, 54, "rojo", P(t, "numeros", .88, .97), alinear="centro", negrita=True)
    pz.capa(al, dib)


# ───── escena 3: una neurona ─────
N1 = dict(x=[.8, .2, .5], w=[.9, -.6, .4], b=.1)
N1["z"] = sum(x * w for x, w in zip(N1["x"], N1["w"])) + N1["b"]; N1["y"] = sig(N1["z"])
IN_Y, IN_X, NX, NY, OX = [300, 470, 640], 430, 960, 470, 1470


def perilla(x, y, w, a, resalta, semilla):
    pz.circulo(x, y, 30, 1, "rojo" if resalta else "negro", 5 if resalta else 3, a, semilla)
    ang = -math.pi / 2 + w * math.pi * .75
    pz.linea(x, y, x + math.cos(ang) * 24, y + math.sin(ang) * 24, 1, "azul" if w > 0 else "naranja", 5, a, semilla + 1)


def escena_neurona(t):
    al = vis(t, "neurona", "activacion")
    def dib():
        kN, kIn = P(t, "neurona", .05, .3), P(t, "neurona", .35, .7)
        kW, kK, kNeg = P(t, "pesos", .05, .25), P(t, "pesos", .3, .5), P(t, "pesos", .75, .9)
        kS = [P(t, "suma", .12, .25), P(t, "suma", .55, .62), P(t, "suma", .62, .7), P(t, "suma", .72, .8), P(t, "suma", .85, .95)]
        kOut, kAct, kGlow = P(t, "activacion", 0, .1), P(t, "activacion", .1, .35), P(t, "activacion", .3, .78)
        kO = P(t, "activacion", .2, .4)
        for i, y in enumerate(IN_Y):
            w = N1["w"][i]; x1, x2, y2 = IN_X + 55, NX - 82, NY + (i - 1) * 40
            pz.linea(x1, y, x2, y2, kIn, "azul" if w > 0 else "naranja", lerp(3, 3 + abs(w) * 9, kW), semilla=i)
            mx, my = lerp(x1, x2, .4), lerp(y, y2, .4)
            if kK > 0:
                perilla(mx, my, w, kK, i == 1 and kNeg > 0, 50 + i * 3)
            et = f"× {w}" if w > 0 else f"× −{abs(w)}  (resta)"
            pz.texto(et, mx - (120 if i == 1 else 30), my + (-52 if i == 0 else 56), 34, "azul" if w > 0 else "naranja", kK, negrita=True)
            pz.circulo(IN_X, y, 55, kIn, "negro", 4, semilla=10 + i)
            pz.texto(f"{N1['x'][i]}", IN_X, y, 44, "negro", kIn, alinear="centro", negrita=True)
        pz.texto("entradas", IN_X, 770, 34, "gris", kIn, alinear="centro")
        brillo = kGlow * N1["y"]
        pz.circulo(NX, NY, 82, kN, "negro", 5, semilla=30, relleno="amarillo" if brillo > .05 else None, a_relleno=.2 + .6 * brillo)
        pz.texto("neurona", NX, NY - 125, 34, "gris", kN, alinear="centro")
        pz.texto(f"{N1['z']:.2f}" if kS[4] > 0 else "Σ", NX, NY, 52, "negro", kN, alinear="centro", negrita=True)
        # la cuenta, escrita como en el pizarrón (debajo de la neurona)
        pa = kS[0] * (1 - kOut)
        if pa > 0:
            filas = [("0.8 × 0.9", "= 0.72", "azul"), ("0.2 × (−0.6)", "= −0.12", "naranja"), ("0.5 × 0.4", "= 0.20", "azul"), ("+ ajuste", "= 0.10", "gris")]
            for i, (a_, b_, col) in enumerate(filas):
                pz.texto(a_, 760, 660 + i * 56, 36, "negro", kS[i], a=pa)
                pz.texto(b_, 1180, 660 + i * 56, 36, col, kS[i], a=pa, alinear="der", negrita=True)
            pz.linea(750, 882, 1190, 884, kS[4], "negro", 3, pa, semilla=4)
            pz.texto("suma = 0.90", 1180, 915, 40, "rojo", kS[4], a=pa, alinear="der", negrita=True)
        if kAct > 0:   # el regulador de luz: la curva sigmoide dibujada a mano
            px, py, pw, ph = 760, 660, 400, 200
            pz.linea(px, py + ph, px + pw, py + ph, kAct, "gris", 3, semilla=5)
            pz.linea(px, py + ph, px, py - 10, kAct, "gris", 3, semilla=6)
            pts = [(px + pw * i / 60, py + ph - sig(lerp(-6, 6, i / 60)) * ph) for i in range(61)]
            pz.trazo(pts, kAct, "naranja", 5)
            pz.texto("regulador de luz", px + pw / 2, py - 40, 36, "naranja", kAct, alinear="centro", negrita=True)
            pz.texto("suma baja", px, py + ph + 36, 28, "gris", kAct)
            pz.texto("suma alta", px + pw, py + ph + 36, 28, "gris", kAct, alinear="der")
            z = lerp(-6, N1["z"], kGlow)
            pz.circulo(px + pw * (z + 6) / 12, py + ph - sig(z) * ph, 12, 1, "rojo", 4, kAct, semilla=7, relleno="rojo", a_relleno=.9)
        if kO > 0:   # el foco, con rayos según cuánto se enciende
            pz.linea(NX + 82, NY, OX - 75, NY, kO, "negro", 4, semilla=8)
            pz.circulo(OX, NY, 70, kO, "negro", 5, semilla=31, relleno="amarillo", a_relleno=.15 + .7 * brillo)
            for r in range(10):
                ang = r / 10 * 2 * math.pi
                largo = 30 + 40 * brillo
                pz.linea(OX + math.cos(ang) * 88, NY + math.sin(ang) * 88, OX + math.cos(ang) * (88 + largo), NY + math.sin(ang) * (88 + largo),
                         clamp(brillo * 1.4), "amarillo", 5, semilla=60 + r)
            pz.texto(f"{round(N1['y'] * kGlow * 100)}%", OX, NY, 48, "negro", kO, alinear="centro", negrita=True)
            pz.texto("cuánto se enciende", OX, NY + 175, 34, "gris", kO, alinear="centro")
    pz.capa(al, dib)


# ───── la red (escenas 4 a 8 y 11) ─────
SIZES = [64, 6, 6, 10]
LX = [640, 980, 1260, 1540]
def nodo_y(l, i):
    return 170 + i * 11.4 if l == 0 else 520 + (i - (SIZES[l] - 1) / 2) * (68 if l == 3 else 112)
GX, GY, CS = 110, 380, 40
import random  # noqa: E402
_r = random.Random(42)
W1 = [[[_r.uniform(-1, 1) for _ in range(SIZES[l + 1])] for _ in range(SIZES[l])] for l in range(3)]
_r2 = random.Random(99)
W2 = [[[clamp(w + (_r2.random() - .5) * 1.1, -1, 1) for w in fila] for fila in capa] for capa in W1]
_r3 = random.Random(5)
HID = [PIX, [_r3.random() for _ in range(6)], [_r3.random() for _ in range(6)]]
OUT_ANTES = [.04, .06, .09, .41, .05, .07, .03, .18, .04, .03]
OUT_DESPUES = [.00, .01, .01, .02, .00, .00, .00, .93, .02, .01]
OBJ = 7
MARCAS = [(1, 0, 1), (1, 2, 4), (1, 5, 0), (2, 0, 0), (2, 2, 7), (2, 5, 9)]


def cuadricula(a):
    for k, on in enumerate(PIX):
        r, c = divmod(k, 8)
        pz.rect(GX + c * CS, GY + r * CS, CS - 4, CS - 4, 1, "gris", 1.5, a, semilla=k, relleno="negro" if on else None, a_relleno=.85)


def red(t, o):
    capas, fwd, back, mix, out = o.get("capas", 4), o.get("fwd", -1), o.get("back", -1), o.get("mix", 0), o.get("out")
    for k in range(64):   # una línea por píxel hacia su neurona de entrada
        r, c = divmod(k, 8)
        if PIX[k]:
            pz.linea(GX + c * CS + CS / 2, GY + r * CS + CS / 2, LX[0] - 8, nodo_y(0, k), clamp(capas), "gris", 1.2, .6, semilla=k)
    for l in range(3):
        ka = clamp(capas - l - 1)
        if ka <= 0:
            continue
        for i in range(SIZES[l]):
            if l == 0 and not PIX[i] and i % 4:    # en la primera capa, sólo algunas conexiones: la pizarra no aguanta 384 líneas
                continue
            for j in range(SIZES[l + 1]):
                w = lerp(W1[l][i][j], W2[l][i][j], mix)
                lit = clamp(fwd - l) * (1 - clamp(fwd - l - 1)) if fwd >= 0 else 0
                bl = clamp(back - (2 - l)) * (1 - clamp(back - (2 - l) - 1)) if back >= 0 else 0
                x1, y1, x2, y2 = LX[l] + (22 if l else 6), nodo_y(l, i), LX[l + 1] - 22, nodo_y(l + 1, j)
                col = "rojo" if bl > 0 else ("azul" if w > 0 else "naranja")
                pz.linea(x1, y1, x2, y2, ka, col, (.8 if l == 0 else 1.2) + abs(w) * 2.5, .25 + .5 * lit + .6 * bl, semilla=l * 1000 + i * 17 + j)
                if 0 < lit < 1 and (l or i % 3 == 0):
                    pz.circulo(lerp(x1, x2, lit), lerp(y1, y2, lit), 5, 1, "negro", 2, 1, semilla=j, relleno="negro", a_relleno=1)
                if 0 < bl < 1 and (l or i % 3 == 0):
                    pz.circulo(lerp(x2, x1, bl), lerp(y2, y1, bl), 6, 1, "rojo", 2, 1, semilla=j, relleno="rojo", a_relleno=1)
    for l in range(4):
        ka = clamp(capas - l)
        if ka <= 0:
            continue
        for i in range(SIZES[l]):
            x, y = LX[l], nodo_y(l, i)
            act = clamp(fwd - l + 1) * HID[l][i] if (l < 3 and fwd >= 0) else (out[i] if (l == 3 and out) else 0)
            if l == 0:
                pz._color("amarillo" if act > .5 else "gris", ka * (1 if act > .5 else .6))
                pz.ctx.arc(x, y, 4.5, 0, 2 * math.pi); pz.ctx.fill(); continue
            pz.circulo(x, y, 22 if l == 3 else 24, ka, "negro", 3, semilla=l * 50 + i, relleno="amarillo" if act > .05 else None, a_relleno=.15 + .7 * act)
            if l == 3:
                pz.texto(str(i), x, y, 26, "negro", ka, alinear="centro", negrita=True)
                if out:
                    best = out.index(max(out))
                    col = ("verde" if i == OBJ else "rojo") if i == best else "gris"
                    pz.rect(x + 34, y - 11, max(3, out[i] * 220), 22, 1, col, 2, 1, semilla=300 + i, relleno=col, a_relleno=.5)
                    if i in (best, OBJ):
                        dx = 236 if (i == OBJ and o.get("objetivo")) else out[i] * 220 + 14
                        pz.texto(f"{round(out[i] * 100)}%", x + 34 + dx, y, 28, "verde" if i == OBJ else col, 1, negrita=True)
    pz.texto("entrada: 64", LX[0], 130, 32, "gris", clamp(capas), alinear="centro")
    pz.texto("capas ocultas", (LX[1] + LX[2]) / 2, 130, 32, "gris", clamp(capas - 1), alinear="centro")
    pz.texto("salida: 10", LX[3], 130, 32, "gris", clamp(capas - 3), alinear="centro")


def escena_red(t):
    al = vis(t, "red", "ajuste")
    def dib():
        cuadricula(1)
        pz.texto("el dibujo", GX + 4 * CS, GY - 34, 32, "gris", 1, alinear="centro")
        capas = lerp(0, 4, P(t, "red", .1, .85))
        fwd = lerp(-.2, 4.2, seg(t, F("intento", .35), F("intento", .8))) if t >= F("intento", .35) else -1
        kOut = P(t, "intento", .78, .9)
        back = lerp(0, 4.2, seg(t, F("retro", .1), F("retro", .8))) if t >= F("retro", .1) else -1
        mix = P(t, "ajuste", .1, .75)
        k7 = P(t, "error", .3, .45) * (1 - P(t, "retro", 0, .12))
        red(t, dict(capas=capas, fwd=fwd, back=back, mix=mix, out=[v * kOut for v in OUT_ANTES] if kOut > 0 else None, objetivo=k7 > .01))
        zonas = [(LX[0] - 40, 150, 80, 760, .02, .3, "recibe el dibujo"), (LX[1] - 60, 170, LX[2] - LX[1] + 120, 700, .3, .55, "buscan patrones"), (LX[3] - 50, 170, 100, 700, .55, .95, "una por dígito")]
        for x, y, w, h, f0, f1, lab in zonas:
            k = min(P(t, "partes", f0, f0 + .06), 1 - P(t, "partes", f1 - .04, f1))
            if k > 0:
                pz.rect(x, y, w, h, P(t, "partes", f0, f0 + .06), "rojo", 4, k, semilla=int(x))
                pz.texto(lab, x + w / 2, y + h + 34, 32, "rojo", 1, k, alinear="centro", negrita=True)
        pz.texto("La red dice: 3", LX[3] + 150, 905, 44, "rojo", P(t, "intento", .88, .96), 1 - P(t, "retro", 0, .1), alinear="centro", negrita=True)
        kE = P(t, "error", .05, .2)
        pz.texto("Era un 7", GX + 4 * CS, GY + 8 * CS + 55, 48, "verde", kE, alinear="centro", negrita=True)
        yo, y3, bx = nodo_y(3, OBJ), nodo_y(3, 3), LX[3] + 34
        off = 1 - P(t, "retro", 0, .12)
        pz.rect(bx - 4, yo - 20, 228, 40, k7, "verde", 3, off, semilla=77)
        pz.texto("debía: 100%", bx + 110, yo + 42, 26, "verde", k7, off, alinear="centro", negrita=True)
        pz.texto("debía: 0%", bx + 110, y3 - 38, 26, "rojo", P(t, "error", .68, .8), off, alinear="centro", negrita=True)
        err = sum((v - (1 if i == OBJ else 0)) ** 2 for i, v in enumerate(OUT_ANTES))
        pz.texto(f"error = {err:.2f}", GX + 4 * CS, GY + 8 * CS + 115, 40, "rojo", P(t, "error", .85, .95), 1 - P(t, "ajuste", .8, 1), alinear="centro", negrita=True)
        kR = min(P(t, "retro", .05, .15), 1 - P(t, "ajuste", 0, .1))
        pz.flecha(LX[3] - 40, 935, LX[0] + 60, 935, kR, "rojo", 5, semilla=12)
        pz.texto("el error viaja hacia atrás", (LX[0] + LX[3]) / 2, 895, 36, "rojo", kR, alinear="centro", negrita=True)
        kM = P(t, "ajuste", .2, .4) * (1 - P(t, "montana", 0, .1))
        for l, i, j in MARCAS:
            d = W2[l][i][j] - W1[l][i][j]
            x, y = lerp(LX[l] + 26, LX[l + 1] - 26, .5), lerp(nodo_y(l, i), nodo_y(l + 1, j), .5)
            pz.circulo(x, y, 20, kM, "azul" if d > 0 else "naranja", 4, semilla=i * 9 + j, relleno="azul" if d > 0 else "naranja", a_relleno=.9)
            pz.texto("+" if d > 0 else "−", x, y - 2, 34, (1, 1, 1), kM, alinear="centro", negrita=True)
        pz.texto("pesos ajustados ✓", (LX[1] + LX[2]) / 2, 905, 40, "verde", P(t, "ajuste", .8, .92), alinear="centro", negrita=True)
    pz.capa(al, dib)


# ───── escena 9: la montaña ─────
Lm = lambda w: 1.1 * (w - .7) ** 2 + .18 + .06 * math.sin(5 * w)
dLm = lambda w: 2.2 * (w - .7) + .3 * math.cos(5 * w)
PASOS = [-1.15]
for _ in range(9):
    PASOS.append(PASOS[-1] - .28 * dLm(PASOS[-1]))


def escena_montana(t):
    al = vis(t, "montana", "montana")
    def dib():
        px, py, pw, ph, w0, w1, lmax = 360, 200, 1200, 580, -1.5, 2.6, 6.2
        X = lambda w: px + (w - w0) / (w1 - w0) * pw
        Y = lambda l: py + ph - l / lmax * ph
        kC = P(t, "montana", 0, .15)
        pz.linea(px, py + ph, px + pw, py + ph, kC, "gris", 3, semilla=1)
        pz.linea(px, py + ph, px, py - 10, kC, "gris", 3, semilla=2)
        pz.trazo([(X(lerp(w0, w1, i / 120)), Y(min(Lm(lerp(w0, w1, i / 120)), lmax))) for i in range(121)], kC, "negro", 6)
        pz.texto("error alto", X(-1.5) + 40, Y(6.2) + 10, 38, "rojo", kC, negrita=True)
        pz.texto("↑ error", px, py - 30, 32, "gris", kC)
        pz.texto("mover un peso →", px + pw, py + ph + 45, 32, "gris", kC, alinear="der")
        pz.texto("tantear y dar un paso hacia donde baja", 1100, 160, 40, "negro", P(t, "montana", .15, .3), alinear="centro")
        pp = seg(t, F("montana", .3), F("montana", .82)) * (len(PASOS) - 1)
        i = min(int(pp), len(PASOS) - 2); f = ease(pp - i)
        w = lerp(PASOS[i], PASOS[i + 1], f)
        sx, sy = X(w), Y(Lm(w)); dx, dy = X(w + .01) - sx, Y(Lm(w + .01)) - sy; n = math.hypot(dx, dy)
        nx, ny = dy / n, -dx / n
        if ny > 0:
            nx, ny = -nx, -ny
        for k in range(i + 1):    # huellas de los pasos anteriores
            pz.circulo(X(PASOS[k]), Y(Lm(PASOS[k])) - 6, 6, 1, "naranja", 3, semilla=k, relleno="naranja", a_relleno=.8)
        R = 22
        kB = P(t, "montana", .25, .32)
        pz.circulo(sx + nx * R, sy + ny * R, R, kB, "negro", 4, semilla=99, relleno="amarillo", a_relleno=.9)
        d = -1 if dLm(w) > 0 else 1
        pz.flecha(sx + nx * R + d * 34, sy + ny * R, sx + nx * R + d * 120, Y(Lm(w + d * .3)) + ny * R, P(t, "montana", .25, .35), "verde", 5, semilla=5)
        pz.texto(f"paso {i + 1}", sx + nx * R, sy + ny * R - 55, 34, "naranja", kB, alinear="centro", negrita=True)
        pz.texto("valle = error mínimo", X(.68), Y(0) + 42, 38, "verde", P(t, "montana", .72, .85), alinear="centro", negrita=True)
    pz.capa(al, dib)


# ───── escena 10: repetir ─────
def escena_repetir(t):
    al = vis(t, "repetir", "repetir")
    def dib():
        k = seg(t, F("repetir", .1), F("repetir", .95))
        pz.texto(f"dibujos vistos: {round(ease(k) * 60000):,}".replace(",", "."), 200, 190, 50, "negro", 1, negrita=True)
        px, py, pw, ph = 200, 260, 1000, 560
        pz.linea(px, py + ph, px + pw, py + ph, P(t, "repetir", 0, .1), "gris", 3, semilla=1)
        pz.linea(px, py + ph, px, py - 10, P(t, "repetir", 0, .1), "gris", 3, semilla=2)
        pz.texto("100%", px - 16, py, 28, "gris", 1, alinear="der")
        pz.texto("0%", px - 16, py + ph, 28, "gris", 1, alinear="der")
        pz.texto("ejemplos →", px + pw, py + ph + 40, 30, "gris", 1, alinear="der")
        acc = lambda x: .1 + .86 * (1 - math.exp(-5 * x))
        pz.trazo([(px + i / 140 * pw, py + ph - acc(i / 140) * ph) for i in range(141)], ease(k), "verde", 6)
        pz.texto(f"aciertos: {round(acc(ease(k)) * 100)}%", px + pw - 20, py + ph - 150, 46, "verde", 1, alinear="der", negrita=True)
        pz.rect(1330, 330, 400, 260, 1, "negro", 5, semilla=3)
        pz.texto("red neuronal", 1530, 440, 46, "azul", 1, alinear="centro", negrita=True)
        pz.texto("ajustando pesos…", 1530, 510, 34, "gris", 1, alinear="centro")
    pz.capa(al, dib)


# ───── escena 11: resultado ─────
def escena_resultado(t):
    al = vis(t, "resultado", "resultado")
    def dib():
        cuadricula(1)
        fwd = lerp(-.2, 4.2, seg(t, F("resultado", .35), F("resultado", .7)))
        kOut = P(t, "resultado", .68, .8)
        red(t, dict(capas=4, fwd=fwd, mix=1, out=[v * kOut for v in OUT_DESPUES] if kOut > 0 else None))
        pz.texto("Ahora dice: 7 ✓", LX[3] + 150, 905, 48, "verde", P(t, "resultado", .8, .9), alinear="centro", negrita=True)
        pz.texto("mismo dibujo, pesos ya entrenados", GX + 4 * CS, GY + 8 * CS + 55, 30, "gris", P(t, "resultado", .1, .3), alinear="centro")
    pz.capa(al, dib)


# ───── cierre: el ciclo ─────
def escena_cierre(t):
    al = vis(t, "cierre", "cierre")
    def dib():
        pasos = ["adivinar", "medir el error", "repartir la culpa", "ajustar un poquito", "repetir"]
        fr = [.08, .2, .36, .52, .64]
        cx, cy, rx, ry = 960, 470, 560, 280
        pos = [(cx + math.cos(-math.pi / 2 + i / 5 * 2 * math.pi) * rx, cy + math.sin(-math.pi / 2 + i / 5 * 2 * math.pi) * ry) for i in range(5)]
        for i, s in enumerate(pasos):
            k = P(t, "cierre", fr[i], fr[i] + .08)
            (x, y), (x2, y2) = pos[i], pos[(i + 1) % 5]
            kA = P(t, "cierre", fr[(i + 1) % 5] - .02, fr[(i + 1) % 5] + .06) * (P(t, "cierre", .74, .82) if i == 4 else 1)
            d = math.hypot(x2 - x, y2 - y); ux, uy = (x2 - x) / d, (y2 - y) / d
            m = min(190 / max(abs(ux), 1e-6), 44 / max(abs(uy), 1e-6)) + 16
            pz.flecha(x + ux * m, y + uy * m, x2 - ux * m, y2 - uy * m, kA, "gris", 4, semilla=i)
            pz.rect(x - 190, y - 44, 380, 88, k, "azul", 4, semilla=10 + i)
            pz.texto(s, x, y, 38, "negro", k, alinear="centro", negrita=True)
        pz.texto("Eso es aprender", cx, cy - 20, 72, "rojo", P(t, "cierre", .8, .92), alinear="centro", negrita=True)
        pz.texto("para una red neuronal", cx, cy + 55, 40, "gris", P(t, "cierre", .84, .95), alinear="centro")
    pz.capa(al, dib)


def escenas(pz_, t):
    escena_titulo(t); escena_idea(t); escena_numeros(t); escena_neurona(t); escena_red(t)
    escena_montana(t); escena_repetir(t); escena_resultado(t); escena_cierre(t)
    titulo(t)


if __name__ == "__main__":
    pz.main(escenas)
