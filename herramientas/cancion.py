"""Analiza una canción real para montar un video sobre su grilla: tempo (BPM), dónde cae el primer tiempo
y la energía por compás (para elegir el tramo con más fuerza y el golpe). Sólo numpy + ffmpeg.

Uso:  .venv/Scripts/python herramientas/cancion.py <cancion.mp3> [segundos-del-video]

Imprime el BPM, la fase de la grilla y el mejor tramo del largo pedido (el de más energía que empieza en un
compás). Con eso: pulsos.js = {bpm, inicio: <inicio del tramo en el video>} y la canción recortada desde ahí.

      .venv/Scripts/python herramientas/cancion.py --probar      (clics a tempos conocidos: ok o FALLA por caso)
"""
import subprocess
import sys

import numpy as np

SR = 22050
ADELANTO = 0.08      # s que la envolvente se adelanta al golpe: lo marca cuando entra en la ventana de 2048 muestras (medido con clics)


def leer(ruta):
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.float32)


def envolvente(x, hop=512, n=2048):
    """Flujo espectral: cuánto sube la energía en cada banda de un cuadro al siguiente (los golpes)."""
    ventana = np.hanning(n)
    cuadros = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * ventana
    mag = np.log1p(np.abs(np.fft.rfft(cuadros, axis=1)))
    flujo = np.maximum(0, np.diff(mag, axis=0)).sum(1)
    flujo -= np.convolve(flujo, np.ones(16) / 16, "same")          # quita la tendencia lenta
    return np.maximum(0, flujo), SR / hop


def pico(a, b, c):
    """Dónde cae el pico verdadero (en cuadros, respecto del central) por una parábola por tres valores vecinos."""
    d = .5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) < 0 else 0.0
    return max(-.5, min(.5, float(d)))   # cae a menos de medio cuadro; en el borde de la ventana la parábola se dispara


def tempo(env, fps, lo=80, hi=160):
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lags = np.arange(len(ac)) / fps
    ok = (lags > 60 / hi) & (lags < 60 / lo)
    # un poco de preferencia por tempos cerca de 115 (evita elegir la mitad o el doble)
    peso = np.exp(-.5 * (np.log2((60 / np.maximum(lags, 1e-6)) / 115) / .9) ** 2)
    i = int(np.flatnonzero(ok)[np.argmax((ac * peso)[ok])])
    # el pico cae en un cuadro entero de la envolvente (≈ 23 ms: a 120 BPM salía 117,45); una parábola por los tres
    # valores vecinos lo ubica entre cuadros, y después se afina contra la grilla entera
    bpm = 60 / ((i + pico(ac[i - 1], ac[i], ac[i + 1])) / fps)
    eje = np.arange(len(env))
    def junta(bp):                       # cuánto golpe junta la mejor grilla de ese tempo
        paso = 60 / bp * fps
        return max(np.interp(np.arange(c0, len(env) - 1, paso), eje, env).mean() for c0 in np.linspace(0, paso, 32, endpoint=False))
    cands = np.clip(np.arange(bpm * .99, bpm * 1.01, .02), lo, hi)
    return float(cands[int(np.argmax([junta(bp) for bp in cands]))])


def fase(env, fps, bpm):
    """Dónde cae el primer tiempo: la fase que junta más golpes sobre la grilla (corregida por ADELANTO)."""
    paso = 60 / bpm * fps
    eje = np.arange(len(env))
    cands = np.linspace(0, paso, 128, endpoint=False)
    puntaje = [np.interp(np.arange(c, len(env) - 1, paso), eje, env).sum() for c in cands]
    return float((cands[int(np.argmax(puntaje))] / fps + ADELANTO) % (60 / bpm))


def main(ruta, largo=22.0):
    x = leer(ruta)
    env, fps = envolvente(x)
    bpm = tempo(env, fps)
    t0 = fase(env, fps, bpm)
    compas = 4 * 60 / bpm
    acum = np.concatenate([[0], np.cumsum(x.astype(np.float64) ** 2)])   # energía de cualquier tramo en O(1)
    energia_de = lambda a, b: np.sqrt((acum[int(b * SR)] - acum[int(a * SR)]) / max(1, int(b * SR) - int(a * SR)))
    inicios = np.arange(t0, len(x) / SR - largo, compas)
    energia = [energia_de(a, a + largo) for a in inicios]
    mejor = inicios[int(np.argmax(energia))] if len(inicios) else t0
    print(f"{ruta}\n  duración {len(x) / SR:.1f} s · {bpm:.1f} BPM · primer tiempo en {t0:.3f} s · compás {compas:.3f} s")
    print(f"  mejor tramo de {largo:.0f} s: desde {mejor:.2f} s (compás {round((mejor - t0) / compas)})")
    por_compas = [energia_de(a, a + compas) for a in np.arange(t0, len(x) / SR - compas, compas)]
    tope = max(por_compas)
    print("  energía por compás: " + "".join(" ▁▂▃▄▅▆▇█"[min(8, int(8 * e / tope))] for e in por_compas))
    return bpm, t0, mejor


def probar():
    """Clics sintéticos a tempos y fases conocidos: cada caso dice ok o FALLA (tempo a ≤ 0,5 BPM, fase a ≤ 20 ms).
    Con la versión anterior daba 0 ok, 5 FALLA (120 BPM → 117,45; fase corrida hasta 251 ms)."""
    def clics(bpm, t0, dur=30.0):
        x = np.zeros(int(dur * SR), np.float32)
        k = np.arange(int(.01 * SR))
        golpe = (np.sin(2 * np.pi * 1000 * k / SR) * np.exp(-k / (.002 * SR))).astype(np.float32)
        t = t0
        while t < dur - .02:
            i = int(round(t * SR)); x[i:i + len(golpe)] += golpe; t += 60 / bpm
        return x
    malos = total = 0
    for bpm, t0 in [(120, .5), (97, .31), (128, .12), (110, .9), (143.5, .2)]:
        env, fps = envolvente(clics(bpm, t0))
        b = tempo(env, fps); f = fase(env, fps, b)
        paso = 60 / bpm
        df = (f - t0 + paso / 2) % paso - paso / 2
        bien = abs(b - bpm) <= .5 and abs(df) <= .02
        malos += not bien; total += 1
        print(f"  {'ok' if bien else 'FALLA'}  {bpm:6.1f} BPM desde {t0:.2f} s -> {b:7.2f} BPM, fase {f:.3f} s ({df * 1000:+.0f} ms)")
    for bpm in (62, 80, 160, 190):       # fuera o en el borde de 80-160: el resultado nunca sale de la ventana
        b = tempo(*envolvente(clics(bpm, .4)))
        bien = 80 <= b <= 160
        malos += not bien; total += 1
        print(f"  {'ok' if bien else 'FALLA'}  {bpm:6.1f} BPM (fuera de ventana) -> {b:7.2f} BPM, dentro de 80-160")
    # la parábola por tres valores: en el borde de la ventana (cresta cayendo, curva hacia abajo) se dispara y se recorta a ±0,5
    for (a, b, c), esperado in [((10, 9, 4), -.5), ((4, 9, 10), .5), ((8, 10, 9), 1 / 6), ((5, 5, 5), 0.0), ((3, 2, 1), 0.0), ((10, 4, 8), 0.0)]:
        p = pico(a, b, c)
        bien = abs(p - esperado) < 1e-6
        malos += not bien; total += 1
        print(f"  {'ok' if bien else 'FALLA'}  pico({a}, {b}, {c}) = {p:+.3f} (esperado {esperado:+.3f})")
    print(f"  {total - malos} ok, {malos} FALLA")
    return malos == 0


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 22.0)
