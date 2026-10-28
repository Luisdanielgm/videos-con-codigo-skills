"""Pone ambiente, música y efectos debajo de la narración de un video.

Uso:  .venv/Scripts/python herramientas/sonido.py <carpeta-del-video>

Lee <carpeta>/sonido.json, tiempos.js y narracion.wav, y escribe <carpeta>/mezcla.wav.
Todo se sintetiza aquí con numpy: sin archivos de audio ajenos. La música y el ambiente bajan
solos cuando alguien habla. Si existe mezcla.wav, la exportación la usa en vez de narracion.wav.

sonido.json:
  {"pistas": [
     {"tipo": "mar",      "desde": "titulo", "hasta": "fin", "vol": 0.5},
     {"tipo": "musica",   "desde": "titulo", "hasta": "caida", "animo": "calma", "vol": 0.4},
     {"tipo": "descenso", "en": "luz", "f": 0.05, "dur": 9},
     ...]}
  Posiciones: "desde"/"hasta" = id de frase (hasta = final de esa frase; "fin" = final del video);
  "en" + "f" = id de frase y fracción de su duración (0 = cuando empieza), "t" = segundos extra.
  Tipos: mar, viento, musica (animo calma | misterio | magia), descenso, silencio, brillo,
  nado, whoosh, latido.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

SR = 24000
rng = np.random.default_rng(7)


def leer_tiempos(carpeta):
    txt = (carpeta / "tiempos.js").read_text(encoding="utf-8")
    return json.loads(re.search(r"=\s*(\{.*\})\s*;", txt, re.S).group(1))


def filtro(x, fc, tipo="low", orden=2):
    b, a = butter(orden, np.clip(np.asarray(fc) / (SR / 2), 1e-4, 0.99), btype=tipo)
    return lfilter(b, a, x)


def env(n, ataque, caida):
    """Envolvente 0→1→0 con subida y bajada suaves (en segundos)."""
    e = np.ones(n)
    a, c = min(int(ataque * SR), n // 2), min(int(caida * SR), n // 2)
    if a:
        e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if c:
        e[-c:] = np.cos(np.linspace(0, np.pi / 2, c)) ** 2
    return e


def ruido(n, color="rosa"):
    x = rng.standard_normal(n)
    if color == "marron":
        x = np.cumsum(x); x = filtro(x, 20, "high")
    elif color == "rosa":
        x = filtro(x, 800)
    return x / (np.abs(x).max() + 1e-9)


# ---- sonidos -----------------------------------------------------------------------------------

def mar(n):
    """Olas: ruido filtrado que respira con ciclos lentos e irregulares, más resaca aguda."""
    t = np.arange(n) / SR
    ola = np.zeros(n); pos = 0.0
    while pos < t[-1]:
        per = rng.uniform(5.5, 8.5)
        fase = np.clip((t - pos) / per, 0, 1)
        ola += np.where((t >= pos) & (t < pos + per), np.sin(np.pi * fase) ** 3 * (1 - fase) ** 0.5, 0) * rng.uniform(0.6, 1)
        pos += per * rng.uniform(0.55, 0.8)
    grave = filtro(ruido(n, "marron"), 400) * (0.35 + 0.65 * ola)
    espuma = filtro(ruido(n, "blanco"), [1500, 6000], "band") * ola ** 2 * 0.35
    return grave + espuma


def viento(n):
    t = np.arange(n) / SR
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + 1.3) * np.sin(2 * np.pi * 0.023 * t)
    return filtro(ruido(n, "blanco"), [300, 1200], "band") * mod


ANIMOS = {
    # acordes en semitonos respecto de la tónica (La = 220 Hz), 4 compases que se repiten
    "calma": ([0, 4, 7, 11], [-3, 0, 4, 7], [5, 9, 12, 16], [2, 7, 11, 14]),
    "misterio": ([0, 3, 7, 10], [-4, 0, 3, 7], [-2, 2, 5, 9], [-5, -1, 2, 7]),
    "magia": ([5, 9, 12, 16], [7, 11, 14, 19], [4, 7, 11, 16], [0, 4, 7, 14]),
}


def musica(n, animo="calma", compas=4.0):
    """Colchón de acordes suaves (senos desafinados) y, en 'magia', una cajita musical arriba."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    acordes = ANIMOS[animo]
    lc = int(compas * SR)
    for i in range(0, n, lc):
        ac = acordes[(i // lc) % len(acordes)]
        m = min(lc + int(1.5 * SR), n - i)  # se solapa un poco con el siguiente
        tt = t[:m]
        e = env(m, 1.2, 1.8)
        for s in ac:
            f = 220 * 2 ** (s / 12) / 2
            for d in (-0.15, 0.15):
                out[i:i + m] += np.sin(2 * np.pi * (f + d) * tt + rng.uniform(0, 6)) * e * 0.12
        if animo == "magia":
            for k in range(8):  # arpegio de cajita musical
                ini = i + int(k * compas / 8 * SR)
                if ini >= n:
                    break
                f = 220 * 2 ** ((ac[k % 4] + 24) / 12)
                ln = min(int(1.2 * SR), n - ini)
                tt2 = np.arange(ln) / SR
                out[ini:ini + ln] += np.sin(2 * np.pi * f * tt2) * np.exp(-tt2 * 4) * 0.06
    return filtro(out, 2500)


def descenso(n):
    """La luz que baja: zumbido que sube de tono, con chisporroteo."""
    t = np.arange(n) / SR; u = t / t[-1]
    f = 90 + 260 * u ** 1.5
    fase = 2 * np.pi * np.cumsum(f) / SR
    zumb = (np.sin(fase) + 0.4 * np.sin(2.01 * fase) + 0.2 * np.sin(3.02 * fase)) * (0.3 + 0.7 * u)
    chisp = np.zeros(n)
    for _ in range(int(40 * t[-1] / 9)):
        p = int(rng.uniform(0, n - 2000)); ln = int(rng.uniform(200, 900))
        chisp[p:p + ln] += rng.standard_normal(ln) * np.exp(-np.arange(ln) / 150) * rng.uniform(0.2, 0.7)
    chisp = filtro(chisp, 2500, "high")
    return (zumb * 0.5 + chisp * 0.5) * env(n, 2.0, 0.08)


def brillo(n):
    """Campanitas agudas que suben (ojos, estrellas)."""
    out = np.zeros(n)
    notas = [0, 4, 7, 12, 16, 19, 24]
    for k, s in enumerate(notas):
        ini = int(k * 0.11 * SR)
        if ini >= n:
            break
        ln = n - ini; tt = np.arange(ln) / SR
        f = 880 * 2 ** (s / 12)
        out[ini:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.76 * f * tt)) * np.exp(-tt * 3.5) * 0.3
    return out


def nado(n):
    """Brazadas: chapoteos cortos a ritmo."""
    out = np.zeros(n); p = 0
    while p < n - 4000:
        ln = int(0.25 * SR)
        s = filtro(rng.standard_normal(ln), [600, 3500], "band") * np.exp(-np.arange(ln) / (0.06 * SR))
        out[p:p + ln] += s[: n - p] * rng.uniform(0.5, 1)
        p += int(rng.uniform(0.42, 0.55) * SR)
    return out * 0.8


def whoosh(n):
    t = np.arange(n) / SR; u = t / t[-1]
    x = ruido(n, "blanco")
    agudo = np.sin(np.pi * u)  # pasa de grave a agudo y vuelve
    out = filtro(x, [250, 700], "band") * (1 - agudo) + filtro(x, [1000, 3000], "band") * agudo
    return out * np.sin(np.pi * u) ** 2


def latido(n):
    out = np.zeros(n); p = 0
    while p < n - 4000:
        for d, a in ((0, 1), (0.22, 0.7)):
            ini = p + int(d * SR); ln = int(0.15 * SR)
            if ini + ln >= n:
                break
            tt = np.arange(ln) / SR
            out[ini:ini + ln] += np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 25) * a
        p += int(0.8 * SR)
    return out


# ---- mezcla --------------------------------------------------------------------------------------

def main(carpeta):
    carpeta = Path(carpeta).resolve()
    T = leer_tiempos(carpeta)
    voz, sr = sf.read(carpeta / "narracion.wav", dtype="float32")
    assert sr == SR
    N = len(voz)
    cfg = json.loads((carpeta / "sonido.json").read_text(encoding="utf-8"))

    def pos(p, clave_id, fin=False):
        i = p[clave_id]
        if i == "fin":
            return N
        s = T["seg"][i]
        base = s["inicio"] + (s["dur"] if fin else s["dur"] * p.get("f", 0))
        return int((base + p.get("t", 0)) * SR)

    fondo, efectos = np.zeros(N), np.zeros(N)
    silencio = np.ones(N)
    for p in cfg["pistas"]:
        tipo, vol = p["tipo"], p.get("vol", 0.5)
        if "desde" in p:
            a, b = pos(p, "desde"), pos(p, "hasta", fin=True)
        else:
            a = pos(p, "en"); b = min(N, a + int(p.get("dur", 2) * SR))
        a, b = max(0, a), min(N, b)
        n = b - a
        if n <= 0:
            continue
        if tipo == "silencio":  # baja el fondo (el ruido que no hizo la nave)
            silencio[a:b] = np.minimum(silencio[a:b], 1 - (1 - vol) * env(n, 0.4, p.get("caida", 2.5)))
            continue
        gen = {"mar": mar, "viento": viento, "descenso": descenso, "brillo": brillo,
               "nado": nado, "whoosh": whoosh, "latido": latido}.get(tipo)
        x = musica(n, p.get("animo", "calma")) if tipo == "musica" else gen(n)
        x = x / (np.abs(x).max() + 1e-9) * env(n, p.get("entrada", 1.5), p.get("salida", 1.5))
        (fondo if tipo in ("mar", "viento", "musica") else efectos)[a:b] += x * vol

    # la voz baja el fondo: envolvente suavizada de la voz
    nivel = np.abs(voz).astype(np.float64)
    nivel = filtro(nivel, 3)
    nivel = np.clip(nivel / (np.percentile(nivel, 95) + 1e-9), 0, 1)
    bajar = 1 - 0.7 * nivel
    # efectos también bajan un poco con la voz: nunca deben taparla
    mezcla = voz + fondo * bajar * silencio * 0.22 + efectos * (1 - 0.4 * nivel) * 0.25
    mezcla = mezcla / max(1.0, np.abs(mezcla).max() / 0.95)
    sf.write(carpeta / "mezcla.wav", mezcla.astype(np.float32), SR)
    print(f"mezcla.wav: {N / SR:.1f}s, {len(cfg['pistas'])} pistas")


def probar():
    """Regla: una guardia nueva se rompe a propósito antes de creerle. Voz de 6 s (un tono de 440 Hz entre 1 y 3 s) y dos frases
    en tiempos.js. Los generadores `viento` y `whoosh` se cambian por una constante (1.0) para que lo que la mezcla le hace al
    fondo y a los efectos se lea exacto en `mezcla − voz`: fondo × 0,22 y efectos × 0,25, bajados por la voz."""
    import tempfile
    g = globals()
    guardado = {k: g[k] for k in ("viento", "whoosh")}
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    def nivel(r, a, b):
        return float(np.mean(np.abs(r[int(a * SR):int(b * SR)])))

    try:
        g["viento"] = g["whoosh"] = lambda n: np.ones(n)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            t = np.arange(6 * SR) / SR
            voz = np.where((t >= 1) & (t < 3), .4 * np.sin(2 * np.pi * 440 * t), 0).astype(np.float32)
            sf.write(tmp / "narracion.wav", voz, SR)
            (tmp / "tiempos.js").write_text('window.TIEMPOS = {"seg": {"a": {"inicio": 1, "dur": 2}, "b": {"inicio": 3.5, "dur": 2}}};', encoding="utf-8")

            def correr(pistas, v=None):
                if v is not None:
                    sf.write(tmp / "narracion.wav", v.astype(np.float32), SR)
                (tmp / "sonido.json").write_text(json.dumps({"pistas": pistas}), encoding="utf-8")
                main(tmp)
                m, sr = sf.read(tmp / "mezcla.wav", dtype="float32")
                v0, _ = sf.read(tmp / "narracion.wav", dtype="float32")
                return m, v0, sr

            fondo = {"tipo": "viento", "desde": "a", "hasta": "fin", "vol": .5, "entrada": 0, "salida": 0}
            m, v0, sr = correr([fondo])
            r = m - v0
            caso("mezcla.wav mono a 24 kHz y del largo de la voz", (sr, m.shape), (24000, v0.shape))
            caso("el fondo entra a 0,22 de su volumen donde nadie habla (0,5 × 0,22)", abs(nivel(r, 4.0, 5.9) - .11) < .005, True)
            caso("la voz baja el fondo (con voz, menos de la mitad que sin ella)", nivel(r, 2.0, 2.8) < .5 * nivel(r, 4.0, 5.9), True)
            caso("antes de que empiece la pista no hay fondo", nivel(r, .1, .9) < .001, True)
            caso("`hasta: fin` llega al final de la voz", abs(nivel(r, 5.85, 5.99) - .11) < .01, True)

            m, v0, _ = correr([fondo, {"tipo": "silencio", "desde": "b", "hasta": "b", "vol": 0, "caida": .1}])
            r = m - v0
            caso("la pista `silencio` apaga el fondo en su frase", nivel(r, 4.3, 5.2) < .003, True)
            caso("y el fondo vuelve después", abs(nivel(r, 5.7, 5.95) - .11) < .01, True)

            efecto = {"tipo": "whoosh", "en": "b", "f": .5, "t": .25, "dur": 1, "vol": 1, "entrada": 0, "salida": 0}
            m, v0, _ = correr([efecto])
            r = np.abs(m - v0)
            primero = int(np.argmax(r > .01)) / SR
            caso("`en` + `f` + `t` ubican el efecto (3,5 + 2 × 0,5 + 0,25 = 4,75 s, ±20 ms)", abs(primero - 4.75) < .02, True)
            caso("el efecto entra a 0,25 de su volumen (voz callada)", abs(nivel(r, 4.8, 5.7) - .25) < .01, True)

            fuerte = (.9 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
            m, _, _ = correr([{**efecto, "vol": 3}, {**fondo, "vol": 3}], fuerte)
            caso("el pico nunca pasa de 0,95 (se baja, no se recorta)", float(np.abs(m).max()) <= .951, True)

            sf.write(tmp / "narracion.wav", voz[::2], SR // 2)
            try:
                main(tmp)
                detalle = "no falló"
            except AssertionError:
                detalle = "AssertionError"
            caso("una narración a otra frecuencia de muestreo se rechaza", detalle, "AssertionError")
    finally:
        g.update(guardado)
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    if sys.argv[1:] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
