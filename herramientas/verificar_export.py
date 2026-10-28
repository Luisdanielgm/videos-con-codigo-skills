"""Guardia de exportes: comprueba que un MP4 exportado es el MISMO video que dibuja la página, no uno corrupto.
Con la máquina saturada Chrome puede perder el contexto de GPU a mitad del exporte: faltan fondos
prerrenderizados, salen manchas negras y franjas oscuras, y las capturas del mismo código salen perfectas. Un exporte
así sale «bien» (sin errores, con todos sus cuadros) y un crítico lo juzga como si fuera el diseño. Esta guardia lo
atrapa: saca capturas de la PÁGINA en unos instantes, decodifica del MP4 el cuadro de esos mismos instantes y los compara.

    .venv/Scripts/python herramientas/verificar_export.py <carpeta-del-video> [--mp4 ruta]
                         [--instantes 0.3,12,30] [--params "fps=60&sub=4"]
    .venv/Scripts/python herramientas/verificar_export.py --probar [<carpeta-del-video>]
                         # se rompe a propósito: cada «ok» tiene su caso que dice «FALLA»
                         # (pide render/<carpeta>.mp4: por omisión, copiar ahí ejemplos/18-epica-lineal_historia-del-vuelo.mp4)

- Instantes por omisión (6): 0,3 s, 25 %, 40 %, 50 %, 75 % y duración − 1 s (la duración sale del MP4). Cada instante se
  ajusta a la cuadrícula de cuadros del MP4 (así la captura y el cuadro son exactamente el mismo instante).
- Las capturas salen con `navegador.py capturas` (su propio servidor y puerto) y con los MISMOS parámetros del exporte:
  `--params` o, si no se da, la variable VIDEOS_PARAMS. Dejan render/capturas/<tecnica>_<video>_<t>.jpg.
- El MP4 es render/<tecnica>_<video>.mp4 salvo que se dé `--mp4`.
- Compara a la resolución del MP4 (cada diferencia se promedia en los tres canales): diferencia media (0–255) y fracción
  de píxeles cuya diferencia pasa de 48/255 y diferencia media del peor bloque (rejilla 16×9). FALLA si pasa de MEDIA_MAX,
  FRAC_MAX o BLOQUE_MAX (umbrales calibrados abajo con exportes buenos; la compresión y el desenfoque por subcuadros dan
  poco, un cuadro corrupto da mucho). Medido a 60 fps con sub=4; en cuadros muy oscuros sólo el bloque ve lo local.
- Revisa también la etiqueta de color del MP4 (yuv420p, rango tv, matriz bt709 o smpte170m): sin ella el navegador y el
  teléfono muestran otros colores que los que ve esta comparación (ver color_mp4.py).
Sale con código 1 si algún instante o el color dicen FALLA (o si la página dio error de consola).

Límite: si Chrome pierde el contexto también en las capturas, la guardia lo verá como diferencia (falso positivo, no
falso negativo): se repite. Un MP4 más viejo que el código de su carpeta también da FALLA, y es una discrepancia real.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

for _f in (sys.stdout, sys.stderr):
    _f.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
RENDER = RAIZ / "render"
GRANDE = 48                  # una diferencia de más de 48/255 en un píxel es «grande»
# Umbrales calibrados con 7 exportes buenos a 60 fps y sub=4 (comerciales de las técnicas 8, 10 y 13, y los instantes
# sanos de dos de las técnicas 9 y 11; 40 instantes): diferencia media 0,4–2,8 y fracción grande
# 0–0,07 %. Los umbrales dejan ~2 veces de margen en la media y ~14 veces en la fracción.
# El peor bloque (rejilla 16×9) dio 0,7–7,1 en los sanos y 25–93 en los discrepantes.
MEDIA_MAX, FRAC_MAX, BLOQUE_MAX = 5.0, 0.01, 14.0


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, check=True, **kw)


def sonda(ruta):
    s = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate:format=duration", "-of", "default=nw=1", str(ruta)]).stdout.decode()
    d = dict(l.split("=", 1) for l in s.split() if "=" in l)
    a, b = (d["r_frame_rate"].split("/") + ["1"])[:2]
    return float(a) / float(b), float(d["duration"]), int(d["width"]), int(d["height"])


def color(ruta):
    """(«ok» o «FALLA», detalle). Exige la etiqueta de color en rango tv: sin ella Chromium y los teléfonos leen el HD como
    BT.709, y ffmpeg (con el que esta guardia compara) como BT.601; eso corría el color hasta 25 niveles sin que
    la comparación lo viera. Ver color_mp4.py."""
    s = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=pix_fmt,color_range,color_space",
             "-of", "default=nw=1", str(ruta)]).stdout.decode()
    d = dict(l.split("=", 1) for l in s.split() if "=" in l)
    bien = d.get("pix_fmt") == "yuv420p" and d.get("color_range") == "tv" and d.get("color_space") in ("bt709", "smpte170m")
    return ("ok" if bien else "FALLA"), f"{d.get('pix_fmt')}, rango {d.get('color_range')}, matriz {d.get('color_space')}"


def nombre_t(t):
    """Igual que reproductor.js: String(Number(t)) con el punto pasado a guion."""
    return (("%.4f" % t).rstrip("0").rstrip(".") or "0").replace(".", "-")


def instantes_por_omision(dur):
    fr = [.25, .4, .5, .75]
    return sorted({0.3, *(round(dur * f, 3) for f in fr), max(0.3, dur - 1)})


def ajustar(ts, fps, dur):
    """Al cuadro más cercano del MP4 (el exporte dibuja el cuadro f en t = f/fps)."""
    n = int(round(dur * fps)) - 1
    return [min(max(0, round(t * fps)), n) / fps for t in ts]


def capturar(carpeta, ts, params):
    """Capturas de la página con navegador.py (su servidor y puerto propios). Devuelve {t: ruta}."""
    env = dict(os.environ)
    if params is not None:
        env["VIDEOS_PARAMS"] = params
    env.pop("VIDEOS_PARTE", None)
    env.pop("VIDEOS_TRAMO", None)
    lista = ",".join(("%.4f" % t).rstrip("0").rstrip(".") or "0" for t in ts)
    r = subprocess.run([sys.executable, str(RAIZ / "herramientas" / "navegador.py"), "capturas", carpeta, lista],
                       env=env, capture_output=True, text=True)
    nombre = carpeta.replace("\\", "/").strip("/").replace("/", "_")
    rutas = {t: RENDER / "capturas" / f"{nombre}_{nombre_t(t)}.jpg" for t in ts}
    # el log de navegador.py es uno solo para todas las corridas de capturas: sólo cuentan los errores de ESTA página
    errores = [l for l in r.stdout.splitlines() if l.startswith("error de consola") and f"/{carpeta}/" in l]
    return rutas, errores


def cuadro_mp4(mp4, t, fps, w, h):
    """El cuadro de índice round(t·fps) del MP4 como RGB (h, w, 3), con seek exacto (-ss antes de -i descarta lo anterior)."""
    i = int(round(t * fps))
    ss = max(0.0, (i - .5) / fps)
    raw = run(["ffmpeg", "-v", "error", "-ss", f"{ss:.6f}", "-i", str(mp4), "-frames:v", "1", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-"]).stdout
    if len(raw) != w * h * 3:
        raise RuntimeError(f"no pude decodificar el cuadro de {t:.3f} s del MP4")
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def cargar(ruta, w, h):
    im = Image.open(ruta).convert("RGB")
    if im.size != (w, h):
        im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im)


def comparar(a, b):
    """(diferencia media, fracción de píxeles con diferencia > 48/255, diferencia media del peor bloque de una rejilla
    de 16×9); la diferencia de un píxel es la media de sus 3 canales. El bloque atrapa lo local (franjas, una ficha que
    falta) en cuadros oscuros, donde la media y la fracción casi no se mueven."""
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).mean(axis=2)
    h, w = d.shape[0] // 9 * 9, d.shape[1] // 16 * 16
    bloque = d[:h, :w].reshape(9, h // 9, 16, w // 16).mean(axis=(1, 3)).max()
    return float(d.mean()), float((d > GRANDE).mean()), float(bloque)


def veredicto(media, frac, bloque):
    return "ok" if media <= MEDIA_MAX and frac <= FRAC_MAX and bloque <= BLOQUE_MAX else "FALLA"


def verificar(carpeta, mp4=None, instantes=None, params=None):
    """Devuelve (resultados, consola_ok): resultados = [(t, media, frac, veredicto)]."""
    carpeta = carpeta.replace("\\", "/").strip("/")
    mp4 = Path(mp4) if mp4 else RENDER / f"{carpeta.replace('/', '_')}.mp4"
    if not mp4.exists():
        sys.exit(f"No existe {mp4}")
    fps, dur, w, h = sonda(mp4)
    ts = ajustar(instantes or instantes_por_omision(dur), fps, dur)
    rutas, errores = capturar(carpeta, ts, params)
    faltan = [t for t in ts if not rutas[t].exists()]
    for e in errores:
        print(e)
    if faltan:
        sys.exit(f"No salieron las capturas de {faltan} (¿falló la página?).")
    out = []
    for t in ts:
        m, f, b = comparar(cuadro_mp4(mp4, t, fps, w, h), cargar(rutas[t], w, h))
        out.append((t, m, f, b, veredicto(m, f, b)))
    return out, not errores, (mp4, fps, dur, w, h)


def imprimir(carpeta, res, info):
    mp4, fps, dur, w, h = info
    print(f"{carpeta}: {mp4.name} · {w}×{h} a {fps:g} fps · {dur:.2f} s · umbrales: media ≤ {MEDIA_MAX:g}, fracción(>{GRANDE}) ≤ {FRAC_MAX * 100:g} %, peor bloque ≤ {BLOQUE_MAX:g}")
    for t, m, f, b, v in res:
        print(f"  {v:5s} t={t:7.3f} s  diferencia media {m:6.2f}  fracción grande {f * 100:6.2f} %  peor bloque {b:6.2f}")
    vc, detalle = color(mp4)
    print(f"  {vc:5s} color: {detalle} (pide yuv420p, rango tv y matriz bt709 o smpte170m; ver color_mp4.py)")
    malos = sum(v == "FALLA" for *_, v in res) + (vc == "FALLA")
    print(f"TOTAL: {len(res) + 1 - malos} ok, {malos} FALLA")
    return malos


def probar(carpeta):
    """Un guardián que nunca falló no se cree. Con un MP4 bueno: (1) cuadro vs captura del mismo instante → ok;
    (2) cuadro vs captura 2 s después → FALLA; (3) cuadro con franjas negras encima vs su captura → FALLA."""
    carpeta = carpeta.replace("\\", "/").strip("/")
    mp4 = RENDER / f"{carpeta.replace('/', '_')}.mp4"
    fps, dur, w, h = sonda(mp4)
    base = ajustar([dur * .3, dur * .6], fps, dur)
    desp = ajustar([t + 2 for t in base], fps, dur)
    rutas, _errores = capturar(carpeta, base + desp, os.environ.get("VIDEOS_PARAMS", ""))
    casos, ok = [], True
    for t, t2 in zip(base, desp):
        v = cuadro_mp4(mp4, t, fps, w, h)
        cap, cap2 = cargar(rutas[t], w, h), cargar(rutas[t2], w, h)
        rayas = v.copy()
        for k in range(3):                       # tres franjas negras horizontales (un cuarto del cuadro)
            y = int(h * (.12 + .3 * k)); rayas[y:y + int(h * .08)] = 0
        casos += [(f"t={t:.2f} bueno (mismo instante)", cap, v, "ok"),
                  (f"t={t:.2f} captura de +2 s", cap2, v, "FALLA"),
                  (f"t={t:.2f} franjas negras encima", cap, rayas, "FALLA")]
    for nombre, a, b, esperado in casos:
        m, f, bl = comparar(a, b)
        dicho = veredicto(m, f, bl)
        paso = dicho == esperado
        ok &= paso
        print(f"  {dicho:5s} {nombre:36s} media {m:6.2f}  fracción {f * 100:6.2f} %  bloque {bl:6.2f}  (esperado {esperado}) {'PASA' if paso else 'NO PASA'}")
    # color: el mismo cuadro RGB codificado con las banderas de color_mp4.py (ok), como lo hacía servidor.py antes
    # (JPEG → yuvj420p de rango completo: FALLA) y como cairo antes (sin etiqueta: FALLA)
    from color_mp4 import COLOR_709
    with tempfile.TemporaryDirectory() as tmp:
        prueba = [("con color_mp4", "rgb24", COLOR_709, "ok"), ("JPEG sin banderas", "mjpeg", [], "FALLA"),
                  ("RGB sin banderas", "rgb24", [], "FALLA")]
        jpg = Path(tmp) / "c.mjpeg"              # como servidor.py: los cuadros llegan como JPEG
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=0.2", "-c:v", "mjpeg",
             "-pix_fmt", "yuvj420p", "-f", "mjpeg", str(jpg)])
        for nombre, ent, banderas, esperado in prueba:
            ruta = Path(tmp) / f"{ent}_{len(banderas)}.mp4"
            fuente = (["-f", "image2pipe", "-c:v", "mjpeg", "-i", str(jpg)] if ent == "mjpeg"
                      else ["-f", "lavfi", "-i", "testsrc2=s=320x180:d=0.2,format=rgb24"])
            run(["ffmpeg", "-v", "error", "-y", *fuente, "-c:v", "libx264", "-pix_fmt", "yuv420p", *banderas, str(ruta)])
            dicho, detalle = color(ruta)
            paso = dicho == esperado
            ok &= paso
            print(f"  {dicho:5s} color {nombre:30s} {detalle:40s} (esperado {esperado}) {'PASA' if paso else 'NO PASA'}")
    print("PRUEBA", "PASA" if ok else "FALLA")
    return ok


def main():
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    if "--probar" in a:
        resto = [x for x in a if x != "--probar"]
        sys.exit(0 if probar(resto[0] if resto else "18-epica-lineal/historia-del-vuelo") else 1)
    if not a or a[0].startswith("--"):
        sys.exit(__doc__)
    inst = [float(x) for x in opt("--instantes").split(",")] if opt("--instantes") else None
    res, consola_ok, info = verificar(a[0], opt("--mp4"), inst, opt("--params"))
    malos = imprimir(a[0], res, info)
    if not consola_ok:
        print("FALLA: la página dio errores de consola al sacar las capturas (ver render/navegador-capturas-<puerto>.log)")
    sys.exit(1 if malos or not consola_ok else 0)


if __name__ == "__main__":
    main()
