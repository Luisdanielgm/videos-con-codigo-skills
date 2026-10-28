"""Kit de efectos propio de cada pieza: síntesis con numpy y semilla, afinado a la tónica de su canción, con variantes.

    .venv/Scripts/python herramientas/kit_efectos.py <carpeta> [--cancion <ruta> --desde <s>] [--semilla <n>]
    .venv/Scripts/python herramientas/kit_efectos.py --probar

Por qué: la música y los efectos de todos los videos sonaban siempre iguales (en el banco compartido, burbuja-pop y
kenney-click-001 suenan miles de veces). Generaliza el primer kit propio, hecho a mano para una sola pieza.

Escribe <carpeta>/sfx/<tipo>_<n>.wav (48 kHz, estéreo) y sfx/kit.json (semilla, tónica, paleta y el pico de cada efecto).
- La semilla sale de la ruta de la carpeta (otra pieza, otro kit) y elige la PALETA: timbre de las claves (madera, marimba,
  vidrio o pulsada), bandas del whoosh, caída del sub, brillo de la subida, cuerpo de la tarjeta, del pop y del clic.
- Lo tonal (clave, pop, clic, swell al revés, brillo) va en la tónica de la canción, estimada por croma con los perfiles de
  Krumhansl (mayor y menor); sin `--cancion` la toma de la `cancion` de <carpeta>/mezcla.json, y sin canción la elige la
  semilla. Sólo tónica, cuarta, quinta y octavas: calzan en mayor y en menor.
- Cada tipo trae variantes (_1, _2, …) con altura, duración y filtro corridos: dos golpes seguidos no suenan idénticos.

Tipos: subida (antes del corte), reves (swell al revés), whoosh (cruza el estéreo), sub (golpe grave), clave, brillo (cierre),
tarjeta (algo que cae), trazo (marcador áspero), pop (aparece algo), clic (interfaz).

En el efectos.py de la pieza:
    sys.path.insert(0, str(RAIZ / "herramientas")); from kit_efectos import Kit
    k = Kit(AQUI)                                         # lee sfx/kit.json
    E = [k("whoosh", 2.4, -17), k("clave", 3.1, -19), k("clave_3", 3.4, -19)]
Por tipo rota entre sus variantes (nunca la misma dos veces seguidas); con nombre exacto usa esa. Devuelve la entrada de
mezcla.json ya corrida para que el PICO caiga en t: el "alinear": "pico" de mezclar.py sólo conoce los picos del banco.
"""
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

RAIZ = Path(__file__).resolve().parent.parent
SR = 48000
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# Krumhansl-Kessler: con C G Am F da C (la tríada más cargada daba F)
MAYOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MENOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PERMITIDAS = (0, 5, 7)               # clases de altura sobre la tónica: sin terceras, sirven en mayor y en menor
TIPOS = {"subida": 3, "reves": 2, "whoosh": 3, "sub": 2, "clave": 5, "brillo": 1, "tarjeta": 4, "trazo": 2, "pop": 4, "clic": 4}
GRADOS = {"clave": (0, 7, 12, 5, 19), "pop": (0, 7, 12, 5), "reves": (0, 7)}
TIMBRES = {  # clave: (múltiplo, amplitud, caída por segundo) de cada parcial
    "madera": ((1, 1, 38), (2.76, .35, 60)),
    "marimba": ((1, 1, 14), (4.0, .25, 40), (10.0, .06, 90)),
    "vidrio": ((1, 1, 9), (2.32, .5, 14), (4.25, .3, 20), (6.63, .15, 28)),
    "pulsada": tuple((m, 1 / m, 12 + 9 * m) for m in range(1, 7)),
}


def tonica(ruta, desde=0.0, dura=45.0):
    """(clase de altura 0–11, 'mayor' | 'menor') de la canción, por croma y perfiles de Krumhansl."""
    x, sr = sf.read(str(ruta), always_2d=True)
    x = x.mean(1)[int(desde * sr):int((desde + dura) * sr)]
    n = 8192
    fr = np.fft.rfftfreq(n, 1 / sr)
    ok = (fr > 60) & (fr < 2000)
    clase = np.round(12 * np.log2(fr[ok] / 261.63)).astype(int) % 12
    croma = np.zeros(12)
    for i in range(0, len(x) - n, n // 2):
        np.add.at(croma, clase, np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n)))[ok])
    r, k, modo = max((np.corrcoef(croma, np.roll(p, k))[0, 1], k, m) for p, m in ((MAYOR, "mayor"), (MENOR, "menor")) for k in range(12))
    return k, modo


def afinacion(x, f_tonica):
    """Cents entre la altura dominante de x y la clase permitida más cercana (tónica, cuarta o quinta, en cualquier octava)."""
    m = x.mean(1) if x.ndim > 1 else x
    a = int(np.argmax(np.abs(m))) + int(.004 * SR)                # después del ataque (el pop baja de altura al empezar)
    s = m[a:a + int(.08 * SR)]
    n = 1 << 18
    esp = np.abs(np.fft.rfft(s * np.hanning(len(s)), n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    esp[(fr < 80) | (fr > 5000)] = 0
    i = int(np.argmax(esp))
    y0, y1, y2 = np.log(esp[i - 1:i + 2] + 1e-12)
    f = fr[i] + (y0 - y2) / (2 * (y0 - 2 * y1 + y2)) * (fr[1] - fr[0])   # interpolación parabólica
    c = 1200 * np.log2(f / f_tonica) % 1200
    return float(min(min(abs(c - 100 * p), 1200 - abs(c - 100 * p)) for p in PERMITIDAS))


def t(dur):
    return np.arange(int(dur * SR)) / SR


def banda(x, lo, hi):
    return sosfilt(butter(2, [lo, min(hi, SR / 2 - 100)], "band", fs=SR, output="sos"), x)  # idioma:ok


def pasa(x, fc, tipo):
    return sosfilt(butter(2, fc, tipo, fs=SR, output="sos"), x)  # idioma:ok


def barrido(ruido, f0, f1, ancho=0.6, trozos=48):
    """Ruido por una banda que se mueve de f0 a f1 (trozos solapados con ventana)."""
    n, sal = len(ruido), np.zeros(len(ruido))
    paso = n // trozos
    for k in range(trozos):
        fc = f0 * (f1 / f0) ** (k / (trozos - 1))
        a, b = max(0, k * paso - paso), min(n, (k + 2) * paso)
        seg = banda(ruido[a:b], fc * (1 - ancho / 2), fc * (1 + ancho / 2))
        sal[a:b] += seg * np.hanning(len(seg))
    return sal


def estereo(x, pan=None):
    """pan: arreglo de -1 (izquierda) a 1 (derecha), o None = centro con un poco de ancho."""
    if pan is None:
        d = int(0.011 * SR)
        return np.stack([x, np.concatenate([np.zeros(d), x[:-d]]) * 0.1 + x * 0.9], 1)
    ang = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(ang), x * np.sin(ang)], 1)


def norm(x, pico=0.89):
    return x / (np.abs(x).max() + 1e-9) * pico


def paleta(rng):
    return {"timbre": str(rng.choice(list(TIMBRES))), "whoosh": [float(rng.uniform(200, 500)), float(rng.uniform(2500, 6000)),
            float(rng.uniform(.4, .9))], "sub": [float(rng.uniform(70, 110)), float(rng.uniform(30, 45)), float(rng.uniform(4, 7))],
            "subida": [float(rng.uniform(6000, 11000)), bool(rng.random() < .6)],
            "tarjeta": [float(rng.uniform(600, 1200)), float(rng.uniform(4000, 8000)), float(rng.uniform(110, 180))],
            "pop": [float(rng.uniform(1.3, 2.0)), float(rng.uniform(18, 35))], "clic": [float(rng.uniform(1500, 3500)), float(rng.uniform(.012, .03))],
            "campana": bool(rng.random() < .5)}


# Cada síntesis recibe (rng, p = paleta, f = altura en Hz, j = corrimiento de la variante, cerca de 1)
def subida(rng, p, f, j):
    dur = .7 * j
    tt = t(dur)
    x = barrido(rng.standard_normal(len(tt)), 400, p["subida"][0] * j, .6) * (tt / dur) ** 2.2
    if p["subida"][1]:
        x += .25 * np.sin(2 * np.pi * (180 * tt + 500 * tt ** 2 / dur)) * (tt / dur) ** 3
    x[-int(.004 * SR):] *= np.linspace(1, 0, int(.004 * SR))
    return estereo(norm(x))


def reves(rng, p, f, j):
    tt = t(.9 * j)
    nota = sum(np.sin(2 * np.pi * f / 2 * m * tt) / m ** 1.4 for m in (1, 2, 3, 4))
    x = (nota + pasa(rng.standard_normal(len(tt)), 3000, "low") * .3) * np.exp(-tt * 4.5)
    return estereo(norm(x[::-1]))


def whoosh(rng, p, f, j):
    dur = .5 * j
    tt = t(dur)
    lo, hi, ancho = p["whoosh"]
    env = np.sin(np.pi * tt / dur) ** 1.5
    x = barrido(rng.standard_normal(len(tt)), lo * j, hi * j, ancho) * env
    x = x + barrido(rng.standard_normal(len(tt)), hi * j, lo * 2, ancho * .6) * env * .4
    sentido = 1 if rng.random() < .5 else -1
    return estereo(norm(x), np.linspace(-.9, .9, len(tt)) * sentido)


def sub(rng, p, f, j):
    f0, f1, caida = p["sub"]
    tt = t(.6 * j)
    x = np.sin(2 * np.pi * np.cumsum(f1 * j + (f0 * j - f1 * j) * np.exp(-tt * 9)) / SR) * np.exp(-tt * caida / j)
    x += pasa(rng.standard_normal(len(tt)), 2500, "low") * np.exp(-tt * 70) * .5
    return estereo(norm(np.tanh(x * 1.6)))


def clave(rng, p, f, j):
    tt = t(.35)
    x = sum(a * np.sin(2 * np.pi * f * m * tt + rng.uniform(0, 6)) * np.exp(-tt * c * j) for m, a, c in TIMBRES[p["timbre"]])
    x *= np.minimum(1, tt / .002)
    x[:int(.0015 * SR)] += rng.standard_normal(int(.0015 * SR)) * .3
    return estereo(norm(x, .8))


def brillo(rng, p, f, j):
    tt = t(2.2)
    parciales = ((1, 1, 1.6), (2, .5, 2.4), (3, .28, 3.1), (4.2, .18, 4.4), (5.4, .1, 6)) if p["campana"] else \
                ((1, 1, 1.4), (2, .45, 2.2), (3, .3, 3), (4, .15, 4), (5, .08, 5))
    x = sum(a * np.sin(2 * np.pi * f * m * tt + rng.uniform(0, 6)) * np.exp(-tt * c) for m, a, c in parciales)
    x *= np.minimum(1, tt / .006)
    d = int(.017 * SR)
    return np.stack([norm(x), norm(np.concatenate([np.zeros(d), x[:-d]])) * .95], 1)


def tarjeta(rng, p, f, j):
    lo, hi, golpe = p["tarjeta"]
    tt = t(.25 * j)
    x = banda(rng.standard_normal(len(tt)), lo * j, hi * j) * np.exp(-tt * 30) * .6 + np.sin(2 * np.pi * golpe * j * tt) * np.exp(-tt * 35)
    return estereo(norm(x, .8))


def trazo(rng, p, f, j):
    dur = .4 * j
    tt = t(dur)
    x = barrido(rng.standard_normal(len(tt)), 4000 * j, 900, .4) * np.sin(np.pi * tt / dur) ** .6
    x *= 1 + .5 * np.sign(np.sin(2 * np.pi * 34 * j * tt))            # rugosidad del marcador
    return estereo(norm(x, .8))


def pop(rng, p, f, j):
    sube, caida = p["pop"]
    tt = t(.18)
    altura = f * (1 + (sube - 1) * np.exp(-tt * 400))                  # arranca más alto y cae a f en ~10 ms
    x = np.sin(2 * np.pi * np.cumsum(altura) / SR) * np.exp(-tt * caida * j)
    x[:int(.001 * SR)] += rng.standard_normal(int(.001 * SR)) * .2
    return estereo(norm(x, .8))


def clic(rng, p, f, j):
    centro, dur = p["clic"]
    tt = t(.06)
    x = banda(rng.standard_normal(len(tt)), centro * j * .7, centro * j * 1.4) * np.exp(-tt / (dur * j))
    x += .3 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 120)
    return estereo(norm(x, .7))


SINTESIS = {"subida": subida, "reves": reves, "whoosh": whoosh, "sub": sub, "clave": clave, "brillo": brillo,
            "tarjeta": tarjeta, "trazo": trazo, "pop": pop, "clic": clic}


def pico_s(x):
    """Instante del pico de energía (ventanas de 10 ms), como preparar_efectos.py."""
    n = int(SR * .01)
    k = len(x) // n
    e = (x[:k * n] ** 2).sum(axis=1).reshape(k, n).sum(axis=1)
    return (int(np.argmax(e)) + .5) * n / SR


def semilla_de(carpeta):
    try:
        rel = Path(carpeta).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        rel = Path(carpeta).resolve().as_posix()
    return zlib.crc32(rel.encode()) % 100000


def generar(carpeta, cancion=None, desde=0.0, semilla=None):
    carpeta = Path(carpeta).resolve()
    semilla = semilla_de(carpeta) if semilla is None else semilla
    if cancion is None and (carpeta / "mezcla.json").exists():
        c = json.loads((carpeta / "mezcla.json").read_text(encoding="utf-8")).get("cancion")
        if c:
            cancion, desde = RAIZ / c["archivo"], c.get("desde", 0) or 0
    rng = np.random.default_rng(semilla)
    pal = paleta(rng)
    if cancion is not None:
        k, modo = tonica(cancion, desde)
    else:
        k, modo = int(rng.integers(12)), "sin canción"
    f = 261.63 * 2 ** (k / 12) * 2                    # tónica en la octava 5
    sal = carpeta / "sfx"
    sal.mkdir(parents=True, exist_ok=True)
    info = {"semilla": semilla, "tonica": NOTAS[k], "modo": modo, "hz": round(f, 2),
            "cancion": None if cancion is None else Path(cancion).as_posix(), "desde": desde, "paleta": pal, "efectos": {}}
    for ti, (tipo, n) in enumerate(TIPOS.items()):
        for i in range(n):
            r = np.random.default_rng([semilla, ti, i])
            j = float(r.uniform(.82, 1.22)) if i else 1.0
            st = GRADOS.get(tipo, (0,))[i % len(GRADOS.get(tipo, (0,)))]
            x = SINTESIS[tipo](r, pal, f * 2 ** (st / 12), j).astype(np.float32)
            nombre = f"{tipo}_{i + 1}"
            sf.write(sal / f"{nombre}.wav", x, SR, subtype="PCM_16")
            info["efectos"][nombre] = {"tipo": tipo, "semitonos": st, "dur": round(len(x) / SR, 3), "pico_s": round(pico_s(x), 3)}
    (sal / "kit.json").write_text(json.dumps(info, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return info


class Kit:
    """Entradas de mezcla.json desde el kit de una carpeta, rotando variantes y con el pico en el instante pedido."""

    def __init__(self, carpeta):
        self.carpeta = Path(carpeta).resolve()
        self.info = json.loads((self.carpeta / "sfx" / "kit.json").read_text(encoding="utf-8"))
        try:
            self.base = self.carpeta.relative_to(RAIZ).as_posix() + "/sfx/"
        except ValueError:
            self.base = (self.carpeta / "sfx").as_posix() + "/"
        self.vueltas = Counter()

    def __call__(self, nombre, t, db=-18):
        ef = self.info["efectos"]
        if nombre not in ef:
            vs = [n for n, v in ef.items() if v["tipo"] == nombre]
            if not vs:
                raise KeyError(f"el kit no tiene «{nombre}»: tipos {sorted({v['tipo'] for v in ef.values()})}")
            self.vueltas[nombre] += 1
            nombre = vs[(self.vueltas[nombre] - 1) % len(vs)]
        return {"archivo": self.base + nombre + ".wav", "en": round(t - ef[nombre]["pico_s"], 3), "db": db}


def probar():
    """Canciones sintéticas de tónica conocida, kits en carpetas temporales y una mezcla real con mezclar.py."""
    import tempfile
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    def roto(nombre, atrapado):
        casos.append(atrapado)
        print(f"  (rota a propósito) {'FALLA' if atrapado else 'ok'}: {nombre} -> {'como se esperaba' if atrapado else 'MAL: la guardia no lo vio'}")

    def cancion(ruta, acordes):                        # tríadas de 1,5 s con su bajo, en clases de altura
        x = []
        for raiz_, terc, quin in acordes:
            tt = t(1.5)
            notas = [261.63 * 2 ** (raiz_ / 12) / 2] + [261.63 * 2 ** (s / 12) for s in (raiz_, raiz_ + terc, raiz_ + quin)]
            x.append(sum(np.sin(2 * np.pi * h * tt) for h in notas) * np.exp(-tt * .8))
        sf.write(ruta, np.concatenate(x) * .2, SR)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cancion(tmp / "do.wav", [(0, 4, 7), (7, 4, 7), (9, 3, 7), (5, 4, 7)] * 3)       # C G Am F
        cancion(tmp / "la.wav", [(9, 3, 7), (2, 3, 7), (4, 4, 7), (9, 3, 7)] * 3)       # Am Dm E Am
        caso("tónica de C G Am F", tonica(tmp / "do.wav"), (0, "mayor"))
        caso("tónica de Am Dm E Am", tonica(tmp / "la.wav"), (9, "menor"))

        info = generar(tmp / "a", cancion=tmp / "la.wav", semilla=7)
        kit = tmp / "a" / "sfx"
        caso("el kit va en La", info["tonica"], "A")
        n = sum(TIPOS.values())
        caso(f"{n} efectos en sfx/ y en kit.json", (len(list(kit.glob("*.wav"))), len(info["efectos"])), (n, n))
        malos = []
        for nombre, e in info["efectos"].items():
            x, sr = sf.read(kit / f"{nombre}.wav", always_2d=True)
            rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
            if sr != SR or x.shape[1] != 2 or np.abs(x).max() > .9 or rms < -45 or not 0 <= e["pico_s"] <= e["dur"]:
                malos.append(f"{nombre} (sr {sr}, pico {np.abs(x).max():.2f}, RMS {rms:.0f} dB, pico_s {e['pico_s']})")
        caso("todos 48 kHz estéreo, sin saturar, audibles y con su pico adentro", malos, [])
        desafinados = {}
        for nombre, e in info["efectos"].items():
            if e["tipo"] in ("clave", "pop"):
                c = afinacion(sf.read(kit / f"{nombre}.wav")[0], info["hz"])
                if c > 15:
                    desafinados[nombre] = round(c)
        caso("claves y pops en tónica, cuarta o quinta (a menos de 15 cents)", desafinados, {})
        pal = paleta(np.random.default_rng(7))
        roto("una clave 50 cents arriba se ve desafinada", afinacion(clave(np.random.default_rng(1), pal, info["hz"] * 2 ** (50 / 1200), 1), info["hz"]) > 15)
        roto("una clave un semitono arriba se ve desafinada", afinacion(clave(np.random.default_rng(1), pal, info["hz"] * 2 ** (1 / 12), 1), info["hz"]) > 15)

        generar(tmp / "a2", cancion=tmp / "la.wav", semilla=7)
        iguales = [p.name for p in kit.glob("*.wav") if p.read_bytes() == (tmp / "a2" / "sfx" / p.name).read_bytes()]
        caso("misma semilla, mismo kit byte por byte", len(iguales), n)
        info_b = generar(tmp / "b", cancion=tmp / "la.wav", semilla=8)
        repetidos = [p.name for p in kit.glob("*.wav") if p.read_bytes() == (tmp / "b" / "sfx" / p.name).read_bytes()]
        caso("otra semilla: ningún archivo igual y otra paleta", (repetidos, info_b["paleta"] == info["paleta"]), ([], False))
        roto("con la misma semilla los dos kits son iguales (la comparación lo ve)", len(iguales) == n)
        clones = []
        for tipo, k in TIPOS.items():
            for i in range(1, k):
                x1, x2 = (sf.read(kit / f"{tipo}_{v}.wav")[0] for v in (i, i + 1))
                if len(x1) == len(x2) and np.abs(x1 - x2).max() < .01:
                    clones.append(f"{tipo}_{i}")
        caso("cada variante suena distinta de la siguiente", clones, [])
        caso("sin canción, la tónica la pone la semilla", generar(tmp / "c", semilla=3)["modo"], "sin canción")

        k = Kit(tmp / "a")
        w = [k("whoosh", 1, -17)["archivo"] for _ in range(4)]
        caso("por tipo rota las variantes (1, 2, 3, 1)", [Path(a).stem for a in w], ["whoosh_1", "whoosh_2", "whoosh_3", "whoosh_1"])
        caso("con nombre exacto usa esa", Path(k("clave_3", 1)["archivo"]).stem, "clave_3")
        e = k("sub_1", 1.0, -6)
        caso("la entrada va corrida por el pico", round(e["en"] + info["efectos"]["sub_1"]["pico_s"], 3), 1.0)
        try:
            k("campana", 1)
            detalle = "no falló"
        except KeyError as err:
            detalle = "nombra los tipos" if "whoosh" in str(err) else str(err)
        caso("un tipo que no existe falla diciendo cuáles hay", detalle, "nombra los tipos")

        sys.path.insert(0, str(Path(__file__).parent))
        from mezclar import mezclar
        (tmp / "a" / "mezcla.json").write_text(json.dumps({"efectos": [k("sub_2", 1.5, -3)], "duracion": 3, "lufs": -14}), encoding="utf-8")
        mezclar(tmp / "a")
        x, sr = sf.read(tmp / "a" / "mezcla.wav", always_2d=True)
        n10 = int(sr * .01)
        en = (x[:len(x) // n10 * n10] ** 2).sum(1).reshape(-1, n10).sum(1)
        caso("mezclado con mezclar.py, el pico del sub cae en 1,5 s (±30 ms)", bool(abs((np.argmax(en) + .5) * .01 - 1.5) <= .03), True)
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--probar"]:
        sys.exit(0 if probar() else 1)
    if not args:
        sys.exit(__doc__)
    opcion = lambda o, tipo, defecto=None: tipo(args[args.index(o) + 1]) if o in args else defecto
    info = generar(args[0], cancion=opcion("--cancion", Path), desde=opcion("--desde", float, 0.0), semilla=opcion("--semilla", int))
    print(f"semilla {info['semilla']} · tónica {info['tonica']} ({info['modo']}) · claves {info['paleta']['timbre']} · "
          f"{len(info['efectos'])} efectos en {Path(args[0]) / 'sfx'}")
