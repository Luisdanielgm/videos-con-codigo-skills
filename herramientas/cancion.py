"""Analiza una canción real para montar un video sobre su grilla: tempo (BPM), dónde cae el primer tiempo
y la energía por compás (para elegir el tramo con más fuerza y el golpe). Sólo numpy + ffmpeg.

Uso:  .venv/Scripts/python herramientas/cancion.py <cancion.mp3> [segundos-del-video]

Imprime el BPM, la fase de la grilla y el mejor tramo del largo pedido (el de más energía que empieza en un
compás). Con eso: pulsos.js = {bpm, inicio: <inicio del tramo en el video>} y la canción recortada desde ahí.
"""
import subprocess
import sys

import numpy as np

SR = 22050


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


def tempo(env, fps, lo=80, hi=160):
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lags = np.arange(len(ac)) / fps
    ok = (lags > 60 / hi) & (lags < 60 / lo)
    # un poco de preferencia por tempos cerca de 115 (evita elegir la mitad o el doble)
    peso = np.exp(-.5 * (np.log2((60 / np.maximum(lags, 1e-6)) / 115) / .9) ** 2)
    lag = lags[ok][np.argmax((ac * peso)[ok])]
    return 60 / lag


def fase(env, fps, bpm):
    """Dónde cae el primer tiempo: la fase que junta más golpes sobre la grilla."""
    paso = 60 / bpm * fps
    cands = np.linspace(0, paso, 64, endpoint=False)
    puntaje = [env[np.round(np.arange(c, len(env), paso)).astype(int).clip(0, len(env) - 1)].sum() for c in cands]
    return cands[int(np.argmax(puntaje))] / fps


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


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 22.0)
