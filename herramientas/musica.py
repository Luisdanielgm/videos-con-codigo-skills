"""Música de comercial generada por cálculo, sobre una grilla de pulsos (sin archivos de audio ajenos).

Uso:  .venv/Scripts/python herramientas/musica.py <carpeta-del-video>

Lee <carpeta>/musica.json y escribe:
  - musica.wav : la pista (44,1 kHz, estéreo).
  - pulsos.js  : window.PULSOS = {bpm, inicio, total, compases}: la animación ubica todo en pulsos.

musica.json:
  {"bpm": 120, "compases": 14, "progresion": ["Am", "F", "C", "G"],
   "secciones": [{"desde": 0, "hasta": 4, "partes": ["pad", "arpegio"]},
                 {"desde": 4, "hasta": 12, "partes": ["bombo", "hat", "caja", "bajo", "pad", "arpegio"]},
                 {"desde": 12, "hasta": 14, "partes": ["pad"]}],
   "silencio_antes": [48],                     # pulsos con 0,1 s de silencio total justo antes (el golpe)
   "efectos": [{"tipo": "riser", "pulso": 44, "pulsos": 4}, {"tipo": "impacto", "pulso": 48},
               {"tipo": "whoosh", "pulso": 16}, {"tipo": "clic", "pulso": 20.5}, {"tipo": "pop", "pulso": 22}]}

Efectos (tipo): whoosh, riser, impacto, clic, pop, moneda («trin trin»), escaner (pitido + láser), check
(éxito), tecla, notificacion, burbuja (mensaje), obturador (foto), deslizar, impresora (motores paso a paso
de una impresora 3D; dura "pulsos"). Cada acción que se ve, con su
sonido en el mismo pulso. Para escucharlos sueltos:  musica.py --muestras <carpeta>

Cómo suena (lo explicó @aiehon_aya para los reels de Opus): bombo = tono grave que cae de golpe; caja,
hi-hat y whoosh = ruido con forma; acordes = 7 dientes de sierra desafinados; cada bombo baja los demás
sonidos un instante (efecto «club»); 0,1 s de silencio antes del golpe final. Determinista.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

SR = 44100
NOTAS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
rng = np.random.default_rng(11)


def hz(midi): return 440 * 2 ** ((midi - 69) / 12)


def acorde(nombre, octava=4):
    raiz = nombre[:2] if len(nombre) > 1 and nombre[1] in "#b" else nombre[:1]
    menor = nombre[len(raiz):].startswith("m")
    r = 12 * (octava + 1) + NOTAS[raiz]
    return [r, r + (3 if menor else 4), r + 7]


def filtro(x, fc, tipo="low", orden=2):
    b, a = butter(orden, np.clip(np.asarray(fc) / (SR / 2), 1e-4, .99), btype=tipo)
    return lfilter(b, a, x)


def env(n, ataque, caida):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / max(caida, 1e-4))


def sierra(f, n, fase=0):
    t = np.arange(n) / SR
    return 2 * ((t * f + fase) % 1) - 1


# ── instrumentos (cada uno devuelve un golpe corto) ──
def bombo(n=int(.45 * SR)):
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 1.0


def caja(n=int(.25 * SR)):
    t = np.arange(n) / SR
    ruido = filtro(rng.standard_normal(n), [1200, 6000], "band") * np.exp(-t * 18)
    return (ruido * .9 + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 30) * .5)


def hat(n=int(.06 * SR)):
    return filtro(rng.standard_normal(n), 7000, "high") * env(n, .001, .018) * .35


def pluck(f, n=int(.35 * SR)):
    t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * f * t)) * .3 + np.sin(2 * np.pi * f * t) * .7) * np.exp(-t * 9) * .25


def efecto(tipo, pulsos, s):
    if tipo == "whoosh":
        n = int(.7 * SR); t = np.arange(n) / SR; u = t / t[-1]
        x = rng.standard_normal(n); ag = np.sin(np.pi * u)
        return (filtro(x, [300, 900], "band") * (1 - ag) + filtro(x, [1500, 5000], "band") * ag) * np.sin(np.pi * u) ** 2 * .6
    if tipo == "riser":
        n = int(pulsos * s * SR); t = np.arange(n) / SR; u = t / t[-1]
        f = 200 + 1800 * u ** 2
        return (filtro(rng.standard_normal(n), 3000, "high") * u ** 2 * .4 + np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 3 * .25)
    if tipo == "impacto":
        n = int(2.2 * SR); t = np.arange(n) / SR
        grave = np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-t * 20)) / SR) * np.exp(-t * 2.2)
        platillo = filtro(rng.standard_normal(n), 4000, "high") * np.exp(-t * 1.6) * .35
        return grave * 1.1 + platillo
    if tipo == "clic":
        n = int(.03 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 180) * .5
    if tipo == "pop":
        n = int(.12 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 25) + 300) / SR) * np.exp(-t * 30) * .5
    # ── efectos de interfaz: cada acción que se ve, con su sonido (moneda que cae, escáner, clic…) ──
    if tipo == "moneda":                                  # «trin, trin»: dos campanitas metálicas agudas
        n = int(.9 * SR); t = np.arange(n) / SR; x = np.zeros(n)
        for t0, f in ((0, 1975.5), (.085, 2637.0)):       # si6 → mi7
            i = int(t0 * SR); u = t[:n - i]
            x[i:] += sum(np.sin(2 * np.pi * f * k * u) / k ** 1.4 for k in (1, 2.76, 5.4)) * np.exp(-u * 6)
        return x * .22
    if tipo == "escaner":                                 # pitido de caja + barrido de láser
        n = int(.45 * SR); t = np.arange(n) / SR
        bip = np.sign(np.sin(2 * np.pi * 1850 * t)) * (t < .11) * .18
        barrido = np.sin(2 * np.pi * np.cumsum(600 + 2600 * t / t[-1]) / SR) * np.sin(np.pi * t / t[-1]) * .08
        return filtro(bip, 5000) + barrido
    if tipo == "check":                                   # éxito: dos notas que suben, limpias
        n = int(.6 * SR); t = np.arange(n) / SR; x = np.zeros(n)
        for t0, m in ((0, 76), (.09, 83)):
            i = int(t0 * SR); u = t[:n - i]
            x[i:] += (np.sin(2 * np.pi * hz(m) * u) + .3 * np.sin(4 * np.pi * hz(m) * u)) * np.exp(-u * 7)
        return x * .2
    if tipo == "tecla":                                   # una tecla del teclado
        n = int(.04 * SR); t = np.arange(n) / SR
        return (filtro(rng.standard_normal(n), [2500, 7000], "band") * np.exp(-t * 220) * .5
                + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 120) * .15)
    if tipo == "notificacion":                            # «ding» suave
        n = int(1.0 * SR); t = np.arange(n) / SR
        return sum(np.sin(2 * np.pi * hz(88) * k * t) / k ** 1.6 for k in (1, 2, 3.01)) * np.exp(-t * 4.5) * .16
    if tipo == "burbuja":                                 # mensaje que llega o sale
        n = int(.16 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(500 + 900 * (t / t[-1]) ** .5) / SR) * np.sin(np.pi * t / t[-1]) * .3
    if tipo == "obturador":                               # foto de un recibo
        n = int(.18 * SR); t = np.arange(n) / SR
        ruido = filtro(rng.standard_normal(n), [800, 6000], "band")
        return ruido * (np.exp(-t * 90) + .6 * np.exp(-np.maximum(t - .07, 0) * 70) * (t > .07)) * .35
    if tipo == "deslizar":                                # dedo que desliza una lista
        n = int(.3 * SR); t = np.arange(n) / SR; u = t / t[-1]
        return filtro(rng.standard_normal(n), [2000, 6000], "band") * np.sin(np.pi * u) ** 2 * .18
    if tipo == "impresora":                               # motores paso a paso de una impresora 3D (dura `pulsos`)
        n = int(pulsos * s * SR); x = np.zeros(n); i = 0
        while i < n:                                      # cada movimiento: un tono que cambia de altura
            m = int(rng.uniform(.09, .22) * SR); m = min(m, n - i); u = np.arange(m) / SR
            f = rng.choice([220, 294, 330, 392, 440, 523, 587])
            tono = np.sign(np.sin(2 * np.pi * f * u)) * .5 + np.sin(2 * np.pi * 2 * f * u) * .3
            x[i:i + m] = tono * np.minimum(1, np.minimum(u, u[-1] - u) / .008); i += m
        x = filtro(x, [150, 2500], "band")
        return x * np.minimum(1, np.arange(n) / (.05 * SR)) * np.minimum(1, (n - np.arange(n)) / (.08 * SR)) * .07
    raise ValueError(tipo)


EFECTOS = ["whoosh", "riser", "impacto", "clic", "pop", "moneda", "escaner", "check", "tecla",
           "notificacion", "burbuja", "obturador", "deslizar", "impresora"]


def poner(pista, x, t, vol=1.0):
    i = int(round(t * SR))
    if i >= len(pista) or i + len(x) <= 0: return
    j = min(len(pista), i + len(x)); a = max(0, i)
    pista[a:j] += x[a - i:j - i] * vol


def main(carpeta):
    carpeta = Path(carpeta).resolve()
    cfg = json.loads((carpeta / "musica.json").read_text(encoding="utf-8"))
    bpm, compases = cfg["bpm"], cfg["compases"]
    s = 60 / bpm; inicio = cfg.get("inicio", .2)
    total = inicio + compases * 4 * s + 2.5
    N = int(total * SR)
    ritmo, armonia, fx = np.zeros(N), np.zeros(N), np.zeros(N)
    kick_env = np.zeros(N)
    prog = cfg.get("progresion", ["Am", "F", "C", "G"])
    tb = lambda b: inicio + b * s

    def activa(parte, compas):
        return any(sec["desde"] <= compas < sec["hasta"] and parte in sec["partes"] for sec in cfg["secciones"])

    for c in range(compases):
        ac = acorde(prog[c % len(prog)])
        for b in range(4):
            beat = c * 4 + b
            if activa("bombo", c):
                poner(ritmo, bombo(), tb(beat), .9)
                i = int(tb(beat) * SR); n = int(.35 * SR)
                kick_env[i:i + n] = np.maximum(kick_env[i:i + n], np.exp(-np.arange(min(n, N - i)) / SR / .09))
            if activa("caja", c) and b in (1, 3):
                poner(ritmo, caja(), tb(beat), .55)
            if activa("hat", c):
                poner(ritmo, hat(), tb(beat + .5), .8); poner(ritmo, hat(), tb(beat), .4)
            if activa("bajo", c):
                for m in (0, .5):
                    n = int(s * .48 * SR); t_ = np.arange(n) / SR
                    f = hz(ac[0] - 24)
                    x = filtro(sierra(f, n), 400) * np.minimum(1, t_ / .005) * np.exp(-t_ * 4) * .5
                    poner(armonia, x, tb(beat + m))
            if activa("arpegio", c):
                for k in range(4):
                    nota = (ac + [ac[0] + 12])[(b * 4 + k) % 4] + 12
                    poner(armonia, pluck(hz(nota)), tb(beat + k / 4), .5)
        if activa("pad", c):
            n = int(4 * s * SR) + int(.3 * SR); pad = np.zeros(n)
            for nota in ac:
                for d in np.linspace(-.12, .12, 7):                 # 7 sierras desafinadas por nota
                    pad += sierra(hz(nota) * 2 ** (d / 12), n, rng.uniform())
            e = np.minimum(1, np.arange(n) / SR / .25) * np.minimum(1, (n - np.arange(n)) / SR / .3)
            poner(armonia, filtro(pad, 2200) * e * .045, tb(c * 4))
    for ef in cfg.get("efectos", []):
        x = efecto(ef["tipo"], ef.get("pulsos", 4), s)
        t0 = tb(ef["pulso"]) - (len(x) / SR if ef["tipo"] == "riser" else (.35 if ef["tipo"] == "whoosh" else 0))
        poner(fx, x, t0, ef.get("vol", 1.0))
    # la armonía «respira» con el bombo (sidechain)
    armonia *= 1 - .65 * kick_env
    mezcla = ritmo + armonia + fx
    golpes = cfg.get("silencio_antes", [])                      # 0,1 s de nada justo antes de cada golpe
    for b in (golpes if isinstance(golpes, list) else [golpes]):
        i = int(tb(b) * SR)
        mezcla[i - int(.1 * SR):i] = 0
    mezcla = np.tanh(mezcla * 1.2)
    # volumen de plataforma (≈ −14 LUFS): RMS a −17 dBFS y picos por debajo de −2 dBFS, así el AAC no
    # recorta (a pico −1 dBFS salían −9,5 LUFS y picos de +1,7 dB después de comprimir)
    rms = np.sqrt(np.mean(mezcla ** 2))
    mezcla *= min(10 ** (-17 / 20) / rms, .79 / np.abs(mezcla).max())
    # estéreo leve: la armonía un poco más abierta
    L = mezcla + armonia * .08; R = mezcla - armonia * .08
    sf.write(carpeta / "musica.wav", np.stack([L, R], 1).astype(np.float32), SR)
    (carpeta / "pulsos.js").write_text("window.PULSOS = " + json.dumps(
        {"bpm": bpm, "inicio": inicio, "total": round(total, 3), "compases": compases}) + ";\n", encoding="utf-8")
    print(f"musica.wav: {total:.1f}s, {bpm} BPM, {compases} compases")


def muestras(carpeta):
    """Escribe cada efecto suelto (para escucharlos y elegir): <carpeta>/efecto_<tipo>.wav"""
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
    for tipo in EFECTOS:
        x = efecto(tipo, 4, .5); x = x / max(1e-9, np.abs(x).max()) * .7
        sf.write(carpeta / f"efecto_{tipo}.wav", np.concatenate([np.zeros(int(.1 * SR)), x, np.zeros(int(.2 * SR))]).astype(np.float32), SR)
    print(f"{len(EFECTOS)} efectos en {carpeta}")


def probar():
    """Regla: una guardia nueva se rompe a propósito antes de creerle. Tres pistas cortas en una carpeta temporal: una con todo
    (duración, nivel de plataforma, pulsos.js), una con el silencio antes del golpe y otra con una parte que entra a mitad.
    El azar es de módulo (`rng`): la repetición se prueba con dos procesos aparte."""
    import hashlib
    import subprocess
    import tempfile
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    def pista(carpeta, cfg):
        carpeta.mkdir()
        (carpeta / "musica.json").write_text(json.dumps(cfg), encoding="utf-8")
        main(carpeta)
        x, sr = sf.read(carpeta / "musica.wav")
        return x, sr

    todo = ["bombo", "hat", "caja", "bajo", "pad", "arpegio"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cfg = {"bpm": 120, "compases": 4, "secciones": [{"desde": 0, "hasta": 4, "partes": todo}],
               "efectos": [{"tipo": "clic", "pulso": 4}]}
        x, sr = pista(tmp / "a", cfg)
        caso("44,1 kHz estéreo", (sr, x.shape[1]), (44100, 2))
        caso("duración: inicio + compases + 2,5 s de cola", x.shape[0], int((.2 + 4 * 4 * .5 + 2.5) * SR))
        caso("sin NaN ni infinitos", bool(np.isfinite(x).all()), True)
        mono = x.mean(axis=1)
        pico, rms = float(np.abs(x).max()), 20 * np.log10(np.sqrt(np.mean(mono ** 2)))
        caso("picos por debajo de -2 dBFS (.79)", pico <= .8, True)
        caso("volumen de plataforma: RMS entre -22 y -16,5 dBFS", -22 <= rms <= -16.5, True)
        p = json.loads((tmp / "a" / "pulsos.js").read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))
        caso("pulsos.js: bpm, inicio y compases de la grilla", (p["bpm"], p["inicio"], p["compases"]), (120, .2, 4))
        caso("pulsos.js: el total coincide con la pista", abs(p["total"] * SR - x.shape[0]) < 2, True)

        # un impacto sobre un hi-hat: pico alto con poco volumen medio; el tope de picos manda sobre el volumen de plataforma
        agudo = {"bpm": 120, "compases": 4, "secciones": [{"desde": 0, "hasta": 4, "partes": ["hat"]}],
                 "efectos": [{"tipo": "impacto", "pulso": 4}]}
        x, _ = pista(tmp / "e", agudo)
        caso("con picos altos el tope de -2 dBFS manda (RMS baja de -17)",
             (float(np.abs(x).max()) <= .8, 20 * np.log10(np.sqrt(np.mean(x.mean(axis=1) ** 2))) < -17.5), (True, True))

        golpe = {"bpm": 120, "compases": 4, "silencio_antes": [8], "secciones": [{"desde": 0, "hasta": 4, "partes": ["bombo", "hat"]}]}
        x, _ = pista(tmp / "b", golpe)
        i = int((.2 + 8 * .5) * SR)
        caso("0,1 s de silencio total antes del golpe", float(np.abs(x[i - int(.1 * SR):i]).max()) < 1e-6, True)
        j = int((.2 + 7 * .5) * SR)
        caso("el pulso anterior sí suena", float(np.abs(x[j - int(.1 * SR):j]).max()) > .01, True)

        medio = {"bpm": 120, "compases": 4, "secciones": [{"desde": 2, "hasta": 4, "partes": ["bombo"]}]}
        x, _ = pista(tmp / "c", medio)
        entra = int((.2 + 8 * .5) * SR)
        caso("una parte que entra en el compás 2 no suena antes", float(np.abs(x[int(.25 * SR):entra - int(.01 * SR)]).max()) < 1e-6, True)
        caso("y suena desde ahí", float(np.abs(x[entra:entra + int(.2 * SR)]).max()) > .05, True)

        try:
            efecto("tipo-que-no-existe", 4, .5)
            lanzo = False
        except ValueError:
            lanzo = True
        caso("un efecto desconocido se rechaza (no es silencio)", lanzo, True)

        hashes = []
        for k in ("d1", "d2"):
            (tmp / k).mkdir()
            (tmp / k / "musica.json").write_text(json.dumps(cfg), encoding="utf-8")
            subprocess.run([sys.executable, str(Path(__file__).resolve()), str(tmp / k)], check=True, capture_output=True)
            hashes.append(hashlib.sha256((tmp / k / "musica.wav").read_bytes()).hexdigest())
        caso("dos procesos dan la misma pista (determinista)", hashes[0] == hashes[1], True)
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--muestras"]: muestras(sys.argv[2])
    elif sys.argv[1:] == ["--probar"]: sys.exit(0 if probar() else 1)
    else: main(sys.argv[1] if len(sys.argv) > 1 else ".")
