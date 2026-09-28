"""Entrena una red neuronal real con dígitos escritos a mano y deja todo listo para el video.

Uso:  .venv/Scripts/python 03-calculo-real/red-neuronal/entrenar.py

Datos: optdigits (UCI), dígitos de 8×8 con valores 0–16, en datos/optdigits.tra y .tes.
Escribe en esta carpeta:
  - datos.js    : window.DATOS con pesos (antes, después de un paso, al final), el dibujo elegido,
                  la curva de error y de aciertos, el corte del error según un peso, etc.
  - guion.json  : guion_plantilla.json con las cifras reales escritas en palabras.
Todo es determinista (semilla fija): correrlo otra vez da exactamente lo mismo.
"""
import json
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
rng = np.random.default_rng(7)

# ───── datos ─────
def cargar(nombre):
    d = np.loadtxt(RAIZ / "datos" / nombre, delimiter=",")
    return d[:, :64] / 16.0, d[:, 64].astype(int)

Xtr, ytr = cargar("optdigits.tra")
Xte, yte = cargar("optdigits.tes")

# ───── red 64 → 12 → 12 → 10 (sigmoide en las ocultas, softmax a la salida) ─────
SIZES = [64, 12, 12, 10]
sig = lambda z: 1 / (1 + np.exp(-z))

def iniciar():
    return [dict(W=rng.normal(0, 1 / np.sqrt(a), (a, b)), b=np.zeros(b)) for a, b in zip(SIZES[:-1], SIZES[1:])]

def adelante(red, X):
    acts = [X]
    for i, capa in enumerate(red):
        z = acts[-1] @ capa["W"] + capa["b"]
        if i < len(red) - 1:
            acts.append(sig(z))
        else:
            z = z - z.max(axis=-1, keepdims=True)
            e = np.exp(z)
            acts.append(e / e.sum(axis=-1, keepdims=True))
    return acts

def perdida(red, X, y):
    p = adelante(red, X)[-1]
    return float(-np.log(p[np.arange(len(y)), y] + 1e-12).mean())

def gradientes(red, X, y):
    acts = adelante(red, X)
    delta = acts[-1].copy()
    delta[np.arange(len(y)), y] -= 1
    delta /= len(y)
    grads = [None] * len(red)
    for i in reversed(range(len(red))):
        grads[i] = dict(W=acts[i].T @ delta, b=delta.sum(0))
        if i:
            delta = (delta @ red[i]["W"].T) * acts[i] * (1 - acts[i])
    return grads

def paso(red, grads, lr):
    return [dict(W=c["W"] - lr * g["W"], b=c["b"] - lr * g["b"]) for c, g in zip(red, grads)]

def aciertos(red, X, y):
    return float((adelante(red, X)[-1].argmax(1) == y).mean())

def copiar(red):
    return [dict(W=c["W"].copy(), b=c["b"].copy()) for c in red]

# ───── entrenamiento ─────
LR, LOTE, EPOCAS = 0.8, 32, 15
red0 = iniciar()
red = copiar(red0)
curva = []                          # (ejemplos vistos, error en prueba, aciertos en prueba)
vistos = 0
curva.append((0, perdida(red, Xte, yte), aciertos(red, Xte, yte)))
for ep in range(EPOCAS):
    orden = rng.permutation(len(Xtr))
    for k in range(0, len(orden), LOTE):
        idx = orden[k:k + LOTE]
        red = paso(red, gradientes(red, Xtr[idx], ytr[idx]), LR)
        vistos += len(idx)
        if (k // LOTE) % 20 == 0:
            curva.append((vistos, perdida(red, Xte, yte), aciertos(red, Xte, yte)))
curva.append((vistos, perdida(red, Xte, yte), aciertos(red, Xte, yte)))
redF = red

# ───── el siete del video: uno de prueba que al principio falla y al final acierta con seguridad ─────
p0 = adelante(red0, Xte)[-1]
pF = adelante(redF, Xte)[-1]
# seguridad final entre 85 y 98 %: un "cien por ciento" suena irreal y engaña sobre lo que hace una red
cand = [i for i in range(len(yte)) if yte[i] == 7 and p0[i].argmax() != 7 and pF[i].argmax() == 7 and .85 <= pF[i, 7] <= .98]
elegido = max(cand, key=lambda i: pF[i, 7] - p0[i, 7])
x7 = Xte[elegido]

# gradiente real de ese único ejemplo con los pesos iniciales (la "culpa" de cada conexión)
g0 = gradientes(red0, x7[None], np.array([7]))
red1 = paso(red0, g0, LR)           # un paso de ajuste, del mismo tamaño que en el entrenamiento

# Corte del error según UN peso, medido sobre 256 dibujos de entrenamiento (con un solo dibujo la
# curva siempre baja y no tiene valle). Se usa la red a mitad de entrenamiento… no: la inicial,
# que es la que se está ajustando en el video. Peso: el de mayor gradiente entre la última oculta y la salida.
lote = rng.choice(len(Xtr), 256, replace=False)
Xl, yl = Xtr[lote], ytr[lote]
gl = gradientes(red0, Xl, yl)[2]["W"]
j, kk = map(int, np.unravel_index(np.abs(gl).argmax(), gl.shape))
w0 = red0[2]["W"][j, kk]
def perdida_con_peso(w):
    r = copiar(red0); r[2]["W"][j, kk] = w
    return perdida(r, Xl, yl)
busca = np.linspace(w0 - 15, w0 + 15, 601)
wmin = float(busca[np.argmin([perdida_con_peso(w) for w in busca])])
a, b = min(w0, wmin), max(w0, wmin)
xs = np.linspace(a - .6 * (b - a) - 1, b + .6 * (b - a) + 1, 121)
corte = [[float(w), perdida_con_peso(w)] for w in xs]
pasos_w = [float(w0)]
for _ in range(12):
    w = pasos_w[-1]; h = 1e-4
    d = (perdida_con_peso(w + h) - perdida_con_peso(w - h)) / (2 * h)
    pasos_w.append(float(w - 6.0 * d))

# 24 dígitos de prueba al azar con su predicción final: los errores que salgan son representativos
pred = pF.argmax(1)
muestra = sorted(rng.choice(len(Xte), 24, replace=False).tolist())

def redondear(x, n=4):
    return np.round(np.asarray(x, dtype=float), n).tolist()

def exportar(r):
    return [dict(W=redondear(c["W"]), b=redondear(c["b"])) for c in r]

cifras = dict(
    n_train=len(Xtr), n_test=len(Xte), vistos=vistos,
    d0=int(p0[elegido].argmax()), p0=round(float(p0[elegido].max()) * 100),
    p7_ini=round(float(p0[elegido, 7]) * 100), p7_fin=round(float(pF[elegido, 7]) * 100),
    acc_ini=round(curva[0][2] * 100), acc_fin=round(curva[-1][2] * 100),
    err_ini=round(float(-np.log(p0[elegido, 7])), 2), err_fin=round(float(-np.log(pF[elegido, 7])), 2),
)
datos = dict(
    sizes=SIZES, x7=redondear(x7, 3), red0=exportar(red0), red1=exportar(red1), redF=exportar(redF),
    grad0=[redondear(g["W"], 5) for g in g0], curva=[[v, round(l, 4), round(a, 4)] for v, l, a in curva],
    corte=dict(capa=2, j=j, k=kk, w0=float(w0), wmin=wmin, lote=len(lote), puntos=redondear(corte), pasos=redondear(pasos_w)),
    muestra=[dict(x=redondear(Xte[i], 3), y=int(yte[i]), pred=int(pred[i])) for i in muestra],
    cifras=cifras,
)
(AQUI / "datos.js").write_text("window.DATOS = " + json.dumps(datos, separators=(",", ":")) + ";\n", encoding="utf-8")

# ───── guion con las cifras reales en palabras ─────
U = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve".split()
D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
C = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}

def palabras(n):
    n = int(n)
    if n < 30:
        return U[n]
    if n < 100:
        return D[n // 10] + ("" if n % 10 == 0 else " y " + U[n % 10])
    if n < 1000:
        return "cien" if n == 100 else C[n // 100] + ("" if n % 100 == 0 else " " + palabras(n % 100))
    miles, resto = divmod(n, 1000)
    m = "mil" if miles == 1 else palabras(miles).replace("uno", "un") + " mil"
    return m + ("" if resto == 0 else " " + palabras(resto))

guion = json.loads((AQUI / "guion_plantilla.json").read_text(encoding="utf-8"))
valores = {k: palabras(v) for k, v in cifras.items() if isinstance(v, int)}
valores["vistos_redondo"] = palabras(round(vistos, -3))
for s in guion["segmentos"]:
    s["texto"] = s["texto"].format(**valores)
(AQUI / "guion.json").write_text(json.dumps(guion, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(cifras, ensure_ascii=False))
print(f"dibujo elegido: prueba #{elegido}; peso del corte: oculta {j} -> salida {kk} (w0={w0:.3f}, minimo en {wmin:.3f})")
print(f"un paso: 7 pasa de {p0[elegido, 7]:.3f} a {adelante(red1, x7[None])[-1][0, 7]:.3f}; errores en la muestra: {sum(pred[i] != yte[i] for i in muestra)}/24")
