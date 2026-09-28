"""Detector de saltos en un MP4: cuadros donde la imagen cambia de golpe (un salto, un cuadro que falta) o se
queda quieta en medio del movimiento (un cuadro repetido). Revisa el video terminado, no el código.

    .venv/Scripts/python herramientas/saltos.py render/<video>.mp4 [--cortes 12.5,40] [--umbral 3]
    .venv/Scripts/python herramientas/saltos.py --probar        # se rompe a propósito: debe encontrar los dos defectos

Cómo mide: baja el video a 160×90 en gris y calcula la diferencia media entre cada cuadro y el anterior.
- salto: la diferencia es `umbral` veces mayor que la mediana de sus vecinos (±6 cuadros) y visible (> 2 %).
- falta: en un movimiento parejo (vecinos casi iguales), de golpe cambia 1,7 veces o más (se saltó un cuadro:
  la primera versión pedía 3 veces y la prueba con un cuadro quitado no lo encontró).
- repetido: la diferencia es casi cero mientras los vecinos se mueven (mediana > 0,6 %).
Los cortes a propósito (`--cortes`, en segundos) no cuentan. Sale con código 1 si encuentra algo.
"""
import subprocess
import sys

import numpy as np

W, H = 160, 90


def cuadros(ruta):
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", ruta], capture_output=True, text=True, check=True).stdout.strip().split(",")[0]
    a, b = (fps.split("/") + ["1"])[:2]; fps = float(a) / float(b)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32) / 255, fps


def analizar(ruta, cortes=(), umbral=3.0):
    v, fps = cuadros(ruta)
    d = np.abs(np.diff(v, axis=0)).mean(axis=(1, 2))              # d[i]: cambio del cuadro i al i+1
    hallazgos = []
    for i in range(len(d)):
        t = (i + 1) / fps
        if any(abs(t - c) < 1.5 / fps for c in cortes): continue
        vec = np.concatenate([d[max(0, i - 6):i], d[i + 1:i + 7]])
        if len(vec) < 4: continue
        med = float(np.median(vec))
        if d[i] > .02 and d[i] > umbral * max(med, .002):
            hallazgos.append((t, "salto", float(d[i]), med))
        elif d[i] > 1.7 * med and med > .004 and np.std(vec) < .2 * med:
            hallazgos.append((t, "falta", float(d[i]), med))           # movimiento parejo y de golpe el doble
        elif d[i] < .12 * med and med > .006:
            hallazgos.append((t, "repetido", float(d[i]), med))
    return hallazgos, fps, len(v)


def episodios(hallazgos, fps):
    """Junta hallazgos seguidos. Tres o más saltos en fila = una transición rápida (puede ser a propósito:
    se informa, no es error). Un repetido pegado a un salto = tirón (se congeló y después alcanzó): defecto."""
    grupos = []
    for h in hallazgos:
        if grupos and h[0] - grupos[-1][-1][0] <= 1.5 / fps: grupos[-1].append(h)
        else: grupos.append([h])
    out = []
    for g in grupos:
        tipos = [k for _, k, _, _ in g]
        if "repetido" in tipos and ("salto" in tipos or "falta" in tipos): clase, defecto = "tirón", True
        elif tipos.count("salto") >= 3: clase, defecto = "transición rápida", False
        else: clase, defecto = tipos[0], True
        out.append((g[0][0], g[-1][0], clase, defecto, max(dv for _, _, dv, _ in g)))
    return out


def probar():
    """Regla: un guardián que nunca falló no se cree. Video de prueba que se mueve parejo, con un cuadro
    quitado (salto) y uno repetido; el detector tiene que encontrar los dos y nada más."""
    import tempfile, os
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "base.mp4"); roto = os.path.join(tmp, "roto.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=6",
                    "-pix_fmt", "yuv420p", base], check=True)
    # quitar el cuadro 60 (salto a los 2 s) y repetir el 120 (a los 4 s)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-vf",
                    "select='not(eq(n\\,60))',setpts=N/30/TB,loop=loop=1:size=1:start=118,setpts=N/30/TB",
                    "-r", "30", "-pix_fmt", "yuv420p", roto], check=True)
    h0, _, _ = analizar(base); h1, fps, n = analizar(roto)
    print(f"sano: {len(h0)} hallazgos · roto: {h1}")
    tipos = {k for _, k, _, _ in h1}
    ok = not h0 and ("salto" in tipos or "falta" in tipos) and "repetido" in tipos
    print("PRUEBA", "PASA" if ok else "FALLA")
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    cortes = [float(x) for x in a[a.index("--cortes") + 1].split(",")] if "--cortes" in a else []
    umbral = float(a[a.index("--umbral") + 1]) if "--umbral" in a else 3.0
    h, fps, n = analizar(a[0], cortes, umbral)
    ep = episodios(h, fps)
    malos = [e for e in ep if e[3]]
    print(f"{a[0]}: {n} cuadros a {fps:g} fps · {len(malos)} defectos · {len(ep) - len(malos)} transiciones rápidas")
    for t0, t1, clase, defecto, dv in ep:
        print(f"  {'DEFECTO' if defecto else 'info   '} {t0:7.2f}–{t1:.2f} s  {clase} (cambio máx. {dv * 100:.1f} %)")
    sys.exit(1 if malos else 0)
