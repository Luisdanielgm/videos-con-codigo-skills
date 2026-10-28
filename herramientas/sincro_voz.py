"""Sincronía fina con la voz: cuándo se dice de verdad una parte de una frase.

`tiempos.json` sólo trae el inicio y la duración de cada frase. Para animar algo a mitad de frase, las escenas estimaban la
hora por la posición en el texto (si «Rojo» está al 40 % del texto, al 40 % del tiempo). En frases largas con puntos y comas,
la voz hace pausas que esa cuenta no ve, y la animación llega hasta 3 s tarde o temprano (medido en un video
de una guía de colores: 2,7 s).

Este módulo busca las pausas reales de la frase en `narracion.wav` y las casa con la puntuación del texto: cada trozo entre
signos de puntuación empieza después de su pausa. Dentro de un trozo sigue siendo proporcional (ahí no hay pausas).

    from sincro_voz import Voz
    v = Voz(carpeta)                      # lee narracion.wav y tiempos.json una vez
    t = v.momento("leyenda", 0.4)          # hora real del 40 % del texto de la frase «leyenda»

Si una frontera no tiene una pausa cerca (±3 s de lo esperado), se queda con la cuenta proporcional: nunca empeora más que eso.
`python herramientas/sincro_voz.py <carpeta>` imprime, por frase, cuánto se corrige cada frontera.
"""
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf

VENT = 0.02          # ventana de energía (s)
UMBRAL_DB = -40      # por debajo es silencio
PAUSA_MIN = 0.12     # un silencio más corto no es pausa (oclusivas, respiraciones)
VENTANA = 3.0        # una frontera busca su pausa a ±3 s de la hora proporcional
CORTE = re.compile(r"[.,:;?!…]\s")


class Voz:
    def __init__(self, carpeta):
        carpeta = Path(carpeta)
        self.T = json.loads((carpeta / "tiempos.json").read_text(encoding="utf-8"))
        self.x, self.sr = sf.read(carpeta / "narracion.wav", dtype="float32")
        if self.x.ndim > 1:
            self.x = self.x.mean(axis=1)

    def _huecos(self, a, b):
        """Pausas (ini, fin) dentro de [a, b] y el tramo con voz (primera y última ventana con sonido)."""
        y = self.x[int(a * self.sr): int(b * self.sr)]
        n = int(VENT * self.sr)
        if len(y) < 2 * n:
            return a, b, []
        e = np.sqrt(np.mean(y[: len(y) // n * n].reshape(-1, n) ** 2, axis=1) + 1e-12)
        voz = 20 * np.log10(e) > UMBRAL_DB
        hay = np.flatnonzero(voz)
        if not len(hay):
            return a, b, []
        huecos, i = [], hay[0]
        while i <= hay[-1]:
            if not voz[i]:
                j = i
                while not voz[j]:
                    j += 1
                if (j - i) * VENT >= PAUSA_MIN:
                    huecos.append((a + i * VENT, a + j * VENT))
                i = j
            else:
                i += 1
        return a + hay[0] * VENT, a + (hay[-1] + 1) * VENT, huecos

    @lru_cache(maxsize=None)
    def anclas(self, i):
        """Trozos de la frase i: (posición en el texto 0–1 donde empieza, hora en que empieza a decirse, hora en que
        termina de decirse, sin la pausa que lo sigue). Ordenados; el último termina en 1.0."""
        s = self.T["seg"][i]
        texto, a, d = s["texto"], s["inicio"], s["dur"]
        ini, fin, huecos = self._huecos(a, a + d)
        n = len(texto)
        ps = [m.end() / n for m in CORTE.finditer(texto)]
        # casar fronteras (en orden) con pausas (en orden) de una vez, por programación dinámica: casar cuesta
        # −largo de la pausa + 0,1 por segundo de distancia a la hora esperada; dejar una pausa sin casar no cuesta y
        # dejar una frontera sin casar cuesta 0,2. Así una estimación corrida no arrastra a las siguientes.
        # Hora esperada de la frontera k: el habla (sin pausas) repartida por el texto + una pausa media por cada
        # frontera anterior (si no, la cuenta llega tarde a mitad de frase: 2,7 s en la guía de colores).
        K, G = len(ps), len(huecos)
        P = sum(h[1] - h[0] for h in huecos)
        media = P / K if K else 0.0
        esp = [ini + (fin - ini - P) * p + media * (k + 1) for k, p in enumerate(ps)]
        INF = float("inf")
        dp = [[INF] * (G + 1) for _ in range(K + 1)]
        de = [[None] * (G + 1) for _ in range(K + 1)]
        dp[0] = [0.0] * (G + 1)
        for k in range(K + 1):
            for g in range(G + 1):
                c = dp[k][g]
                if c == INF:
                    continue
                if g < G and c < dp[k][g + 1]:
                    dp[k][g + 1], de[k][g + 1] = c, (k, g, False)
                if k < K and c + 0.2 < dp[k + 1][g]:
                    dp[k + 1][g], de[k + 1][g] = c + 0.2, (k, g, False)
                if k < K and g < G and abs(huecos[g][1] - esp[k]) <= VENTANA:
                    cc = c - (huecos[g][1] - huecos[g][0]) + 0.1 * abs(huecos[g][1] - esp[k])
                    if cc < dp[k + 1][g + 1]:
                        dp[k + 1][g + 1], de[k + 1][g + 1] = cc, (k, g, True)
        casado, k, g = {}, K, G
        while de[k][g] is not None:
            pk, pg, m = de[k][g]
            if m:
                casado[pk] = huecos[pg]
            k, g = pk, pg
        trozos, p_ant, t_ant = [], 0.0, ini
        for k in sorted(casado):
            h = casado[k]
            trozos.append((p_ant, t_ant, h[0]))
            p_ant, t_ant = ps[k], h[1]
        trozos.append((p_ant, t_ant, fin))
        return tuple(trozos)

    def momento(self, i, frac):
        """Hora real a la que la voz llega al `frac` (0–1, por posición en el texto) de la frase i. Si algún trozo de la
        frase sale a una velocidad imposible (frontera mal casada), vuelve a la cuenta proporcional de siempre."""
        frac = min(max(frac, 0.0), 1.0)
        if raros(self, i):
            s = self.T["seg"][i]
            return s["inicio"] + s["dur"] * frac
        tr = self.anclas(i)
        fines = [p for p, _, _ in tr[1:]] + [1.0]
        for (p0, t0, t1), p1 in zip(tr, fines):
            if p0 <= frac < p1 or p1 == 1.0:
                return t0 + (t1 - t0) * (frac - p0) / max(p1 - p0, 1e-9)
        return tr[-1][2]


def raros(v, i):
    """Trozos (de ≥ 8 letras) leídos a una velocidad imposible para su frase: señal de una frontera mal casada."""
    texto, tr = v.T["seg"][i]["texto"], v.anclas(i)
    fines = [p for p, _, _ in tr[1:]] + [1.0]
    vel = [((p1 - p0) * len(texto), (p1 - p0) * len(texto) / max(t1 - t0, 1e-3)) for (p0, t0, t1), p1 in zip(tr, fines)]
    medios = sorted(r for n, r in vel if n >= 8)
    if not medios:
        return []
    med = medios[len(medios) // 2]
    return [(round(n), round(r / med, 2)) for n, r in vel if n >= 8 and not 0.55 <= r / med <= 1.8]


def _hms(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _seg(txt):
    h, m, s = txt.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def resincronizar_srt(carpeta):
    """Mueve cada subtítulo de subtitulos.srt a la hora real en que la voz dice ese pedazo de la frase (los subtítulos
    se repartían igual que las animaciones: proporcional al texto). Si un subtítulo no se encuentra en su frase, se
    queda donde estaba. Devuelve (movidos, total)."""
    carpeta = Path(carpeta)
    v = Voz(carpeta)
    bloques = [b for b in (carpeta / "subtitulos.srt").read_text(encoding="utf-8").strip().split("\n\n") if b.strip()]
    cues = []
    for b in bloques:
        lin = b.strip().splitlines()
        a, z = [_seg(x.strip()) for x in lin[1].split("-->")]
        cues.append([a, z, lin[2:]])
    orden = sorted(v.T["seg"], key=lambda i: v.T["seg"][i]["inicio"])
    pos, movidos = {}, 0
    for c in cues:
        a = c[0]
        i = next((i for i in reversed(orden) if v.T["seg"][i]["inicio"] - 0.05 <= a), None)
        if i is None:
            continue
        texto = v.T["seg"][i]["texto"]
        frag = " ".join(l.strip() for l in c[2])
        k0 = texto.find(frag, pos.get(i, 0))
        if k0 < 0:
            continue
        k1 = k0 + len(frag)
        pos[i] = k1
        nuevo_a = v.momento(i, k0 / len(texto))
        nuevo_z = v.momento(i, k1 / len(texto)) if k1 < len(texto) else c[1]
        if nuevo_z - nuevo_a >= 0.3:
            movidos += abs(nuevo_a - c[0]) > 0.05
            c[0], c[1] = nuevo_a, nuevo_z
    # un subtítulo termina cuando empieza el siguiente si se tocan (sin encimarse)
    for c, d in zip(cues, cues[1:]):
        if c[1] > d[0]:
            c[1] = d[0]
    out = "\n\n".join(f"{n}\n{_hms(a)} --> {_hms(z)}\n" + "\n".join(t) for n, (a, z, t) in enumerate(cues, 1)) + "\n"
    (carpeta / "subtitulos.srt").write_text(out, encoding="utf-8")
    return movidos, len(cues)


if __name__ == "__main__":
    if sys.argv[1] == "--srt":
        for c in sys.argv[2:]:
            print(c, "subtítulos movidos / total:", resincronizar_srt(c))
        sys.exit()
    v = Voz(sys.argv[1])
    total = malas = 0
    for i, s in v.T["seg"].items():
        tr = v.anclas(i)
        corr = [round(t - (s["inicio"] + s["dur"] * p), 2) for p, t, _ in tr[1:]]
        mal = raros(v, i)
        total += 1
        malas += bool(mal)
        if mal:
            print(f"FALLA  {i:14s} trozos a velocidad imposible (letras, velocidad/mediana): {mal}")
        elif corr and max(abs(c) for c in corr) > 0.5:
            print(f"ok     {i:14s} {len(tr) - 1} fronteras, corrección máx {max(corr, key=abs):+.2f} s")
    print(f"TOTAL: {total} frases · {malas} FALLA")
