"""Crítico ciego: mide un MP4 TERMINADO contra la barra de calidad y arma las hojas para que lo mire un crítico que no
vio la construcción. Decodifica el archivo final (no capturas del navegador) UNA vez, a 320×180 y 160×90 en gris.

    .venv/Scripts/python herramientas/critico.py render/<video>.mp4 [--salida carpeta] [--paso 0.2] [--sin-hojas]
                         [--quietos 12.0-12.6,30-31 | --quietos <carpeta>/tiempos.json | --quietos quietos.json]
                         [--textos cajas.json]
    .venv/Scripts/python herramientas/critico.py --probar      # se rompe a propósito: cada «ok» tiene su «FALLA»

Qué mide (meta entre paréntesis):
  congelado      segundos sin cambio visible por cada 30 s (≤ 1) y tramo quieto más largo (≤ 0,5). Sin cambio
                 visible = menos de 3 píxeles (de 320×180) cambian más de 8/255. Tramos de menos de 0,15 s no cuentan
                 (cuadros dobles de 60 fps). `--quietos` marca tramos quietos a propósito: «a-b,c-d», un JSON
                 [[a,b],…], o tiempos.json/tiempos.js (toma las pausas de voz de ≥ 400 ms entre frases).
  primer cuadro  terminado: no vacío ni negro (desvío del brillo ≥ 0,02) y detalle (bordes) ≥ 50 % de la mediana.
  sonoridad      integrada −14 ± 2 LUFS y pico verdadero ≤ −1 dBTP (sin recorte), con ffmpeg ebur128.
  contraste      `--textos cajas.json` = [{"x":…,"y":…,"w":…,"h":…,"t":…}] en píxeles del video: separa texto y
                 fondo dentro de cada caja (umbral de Otsu) y mide el contraste WCAG (≥ 4,5:1). Aproximado sobre fotos.
  sobresalto     el audio no se dispara en los cortes: nivel máximo de los 0,3 s que siguen al corte menos la mediana de
                 los 4 s anteriores (ventanas de 100 ms con sonido) ≤ +8 dB. En 12 MP4 buenos el peor corte fue de −5 a +9
                 dB y los showreels con golpes a propósito rondan +5…+7: el +6 de iart-ai/sync-check se quedó corto para
                 ellos; arriba de +8 es un susto que hay que oír antes de aceptar. No cuentan el primer segundo ni los
                 cortes sin 5 ventanas con sonido antes.
  cortes         (info) los de herramientas/saltos.py, con una hoja densa (18 cuadros/s durante 1 s) en cada uno.
  hojas          una cada `--paso` s (0,2) con herramientas/hoja.py → render/critica/<video>/ (o `--salida`).
Escribe también medidas.json (para el registro de rondas, critica.md). Sale con código 1 si algo dice FALLA.
"""
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hoja  # noqa: E402
import saltos  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
W, H = saltos.W, saltos.H
PX, N_PX, TRAMO_MIN = 8, 3, 0.15          # cambio visible: ≥ 3 píxeles cambian > 8/255; tramos < 0,15 s no cuentan
META = {"congelado_30": 1.0, "quieto_max": 0.5, "lufs": -14.0, "lufs_tol": 2.0, "pico": -1.0, "primer": 0.5,
        "contraste": 4.5, "sobresalto": 8.0}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, check=True, **kw)


def sonda(ruta):
    j = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,r_frame_rate,width,height:"
                        "format=duration", "-of", "json", ruta]).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a, b = (v["r_frame_rate"].split("/") + ["1"])[:2]
    return (float(a) / float(b), float(j["format"]["duration"]), v["width"], v["height"],
            any(s["codec_type"] == "audio" for s in j["streams"]))


def decodificar(ruta, fps, carpeta=None, paso=0.2):
    """Una sola pasada por el MP4: cuántos píxeles cambian entre cuadros (a 2·W×2·H), los cuadros a W×H para lo
    demás y, si hay `carpeta`, los cuadros de la hoja general (cada `paso` s, 640×360)."""
    f = fps if fps <= 30.5 else 30.0       # 60 fps → 30: alcanza para medir y gasta la mitad
    pre = f"fps={f}," if f != fps else ""
    if carpeta:
        fc = (f"[0:v]{pre}split=2[a][b];[a]scale={2 * W}:{2 * H},format=gray[m];"
              f"[b]fps={1 / paso},scale=640:360:force_original_aspect_ratio=decrease[g]")
        fin = ["-map", "[g]", "-q:v", "4", str(Path(carpeta) / "g_%05d.jpg")]
    else:
        fc, fin = f"[0:v]{pre}scale={2 * W}:{2 * H},format=gray[m]", []
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-i", ruta, "-filter_complex", fc, "-map", "[m]", "-f",
                          "rawvideo", "pipe:1", *fin], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    chicos, cambio, antes, n = [], [], None, 4 * W * H
    while len(b := p.stdout.read(n)) == n:
        x = np.frombuffer(b, np.uint8).reshape(2 * H, 2 * W).astype(np.int16)
        if antes is not None: cambio.append(int((np.abs(x - antes) > PX).sum()))
        antes = x
        chicos.append(x.reshape(H, 2, W, 2).mean(axis=(1, 3)).astype(np.uint8))
    if p.wait(): raise RuntimeError(f"ffmpeg no pudo leer {ruta}")
    return np.stack(chicos), np.array(cambio), f


def leer_quietos(arg):
    """Tramos quietos a propósito → [(a, b)]."""
    if not arg: return []
    p = Path(arg)
    if not p.exists():
        return [tuple(float(x) for x in par.split("-")) for par in arg.split(",")]
    txt = p.read_text(encoding="utf-8")
    if p.suffix == ".js" or '"seg"' in txt:              # tiempos.js / tiempos.json: pausas de voz ≥ 400 ms
        t = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        seg = sorted((s["inicio"], s["inicio"] + s["dur"]) for s in t["seg"].values())
        pausas = [(0.0, seg[0][0])] + [(a[1], b[0]) for a, b in zip(seg, seg[1:])] + [(seg[-1][1], t.get("total", 1e9))]
        return [(a, b) for a, b in pausas if b - a >= 0.4]
    return [tuple(map(float, x)) for x in json.loads(txt)]


def congelado(cambio, f, dur, quietos):
    quieto = cambio < N_PX
    t = (np.arange(len(quieto)) + 0.5) / f               # mitad de cada paso entre cuadros
    for a, b in quietos: quieto &= ~((t >= a) & (t <= b))
    tramos, i = [], 0
    while i < len(quieto):
        if quieto[i]:
            j = i
            while j < len(quieto) and quieto[j]: j += 1
            if (j - i) / f >= TRAMO_MIN: tramos.append((i / f, j / f))
            i = j
        else: i += 1
    total = sum(b - a for a, b in tramos)
    largo = max(tramos, key=lambda x: x[1] - x[0], default=(0.0, 0.0))
    return total * 30 / dur, largo, total, sorted(tramos, key=lambda x: x[0] - x[1])[:5]


def detalle(x):
    x = x.astype(np.float32) / 255
    return float(np.abs(np.diff(x, axis=0)).mean() + np.abs(np.diff(x, axis=1)).mean())


def primer_cuadro(v, f):
    med = float(np.median([detalle(v[i]) for i in range(0, len(v), max(1, round(f * 0.2)))]))
    d0, s0 = detalle(v[0]), float(v[0].std()) / 255
    return d0, med, s0


def sonoridad(ruta):
    err = run(["ffmpeg", "-nostats", "-hide_banner", "-i", ruta, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
              ).stderr.decode("utf-8", "replace")
    resumen = err[err.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", resumen)
    p = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", resumen)
    return float(i.group(1)), float(p.group(1))


def energia(ruta):
    """Nivel del audio (dB) en ventanas de 100 ms, mono a 16 kHz. Vacío si no hay audio."""
    raw = run(["ffmpeg", "-v", "error", "-i", ruta, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    n = len(x) // 1600
    if n == 0:
        return np.array([])
    rms = np.sqrt((x[:n * 1600].reshape(n, 1600) ** 2).mean(axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-5))


def sobresaltos(db, cortes_t, ref=4.0, despues=0.3, piso=-45.0):
    """Por cada corte: el nivel máximo de los 0,3 s siguientes menos la mediana de las ventanas con sonido (> −45 dB) de los
    4 s anteriores. Un corte que entra +7 a +10 dB más fuerte se oye como susto (sync-check de iart-ai/javascript-animation:
    límite +6 dB). No cuentan el primer segundo ni los cortes sin 5 ventanas con sonido antes (música que vuelve tras un silencio)."""
    out = []
    for t in cortes_t:
        i = int(round(t * 10))
        a = db[i:i + int(despues * 10)]
        b = db[max(0, i - int(ref * 10)):max(0, i - 1)]
        b = b[b > piso]
        if t >= 1.0 and len(a) and len(b) >= 5:
            out.append((t, float(a.max() - np.median(b))))
    return out


def cortes(v, f, ruta):
    vf = v.astype(np.float16) / np.float16(255)
    original = saltos.cuadros
    saltos.cuadros = lambda _r: (vf, f)                   # reusar el detector sin decodificar otra vez
    try:
        h, _, _ = saltos.analizar(ruta)
    finally:
        saltos.cuadros = original
    ep = saltos.episodios(h, f)
    return [e[0] for e in ep if e[2] in ("salto", "transición rápida")], [e[0] for e in ep if e[2] == "tirón"]


def luminancia(rgb):
    c = rgb.astype(np.float64) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ [0.2126, 0.7152, 0.0722]


def contraste(ruta, cajas, w, h):
    out = []
    for c in cajas:
        raw = run(["ffmpeg", "-v", "error", "-ss", str(c["t"]), "-i", ruta, "-frames:v", "1", "-f", "rawvideo",
                   "-pix_fmt", "rgb24", "-"]).stdout
        im = np.frombuffer(raw, np.uint8).reshape(h, w, 3)[int(c["y"]):int(c["y"] + c["h"]), int(c["x"]):int(c["x"] + c["w"])]
        L = luminancia(im.reshape(-1, 3))
        hist, bordes = np.histogram(L, 256, (0, 1))       # Otsu: el umbral que mejor separa texto y fondo
        p = hist / hist.sum(); m = np.cumsum(p * (bordes[:-1] + bordes[1:]) / 2); w0 = np.cumsum(p)
        with np.errstate(divide="ignore", invalid="ignore"):
            var = (m[-1] * w0 - m) ** 2 / (w0 * (1 - w0))
        u = bordes[int(np.nanargmax(var)) + 1]
        a, b = L[L < u], L[L >= u]
        if min(len(a), len(b)) < 0.01 * len(L): out.append((c, 1.0)); continue   # caja pareja: no hay texto
        l1, l2 = float(np.median(b)), float(np.median(a))
        out.append((c, (l1 + 0.05) / (l2 + 0.05)))
    return out


def hojas(ruta, salida, cortes_t, paso, dur):
    """Los cuadros generales (g_*.jpg) ya los dejó decodificar(); aquí van los densos y se arman las hojas."""
    nombre = lambda t: f"{t:.3f}".rstrip("0").rstrip(".").replace(".", "-") + ".jpg"
    for k, g in enumerate(sorted(salida.glob("g_*.jpg"))): g.rename(salida / f"general_{nombre(k * paso)}")
    for n, t in enumerate(cortes_t[:40]):
        t0 = max(0.0, min(t - 0.5, dur - 1))
        run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", "1", "-i", ruta, "-vf", "fps=18,scale=640:360:force_original_aspect_ratio=decrease",
             "-q:v", "4", str(salida / "c_%03d.jpg")])
        for k, g in enumerate(sorted(salida.glob("c_*.jpg"))): g.rename(salida / f"corte{n:02d}_{nombre(t0 + k / 18)}")
    hoja.CAP = salida                                      # hoja.py lee y escribe en su carpeta CAP
    with contextlib.redirect_stdout(io.StringIO()):
        hoja.main("general")
        for n in range(min(len(cortes_t), 40)): hoja.main(f"corte{n:02d}")
    for g in salida.glob("*.jpg"):
        if not g.name.startswith("hoja_"): g.unlink()      # quedan sólo las hojas
    return len(list(salida.glob("hoja_general_*"))), len(list(salida.glob("hoja_corte*")))


def criticar(ruta, salida=None, quietos=(), textos=None, paso=0.2, con_hojas=True, mostrar=True):
    ruta = str(ruta)
    fps, dur, w, h, con_audio = sonda(ruta)
    salida = Path(salida) if salida else RAIZ / "render" / "critica" / Path(ruta).stem
    if con_hojas:
        salida.mkdir(parents=True, exist_ok=True)
        for viejo in salida.glob("*.jpg"): viejo.unlink()
    v, cambio, f = decodificar(ruta, fps, salida if con_hojas else None, paso)
    dur = len(v) / f
    r = []                                                 # (clave, ok | None, texto)
    c30, largo, total, peores = congelado(cambio, f, dur, quietos)
    r.append(("congelado", c30 <= META["congelado_30"],
              f"congelado: {c30:.2f} s cada 30 s ({total:.2f} s en total; meta ≤ {META['congelado_30']:g})"))
    r.append(("quieto_max", largo[1] - largo[0] <= META["quieto_max"],
              f"tramo quieto más largo: {largo[1] - largo[0]:.2f} s en {largo[0]:.2f}–{largo[1]:.2f} "
              f"(meta ≤ {META['quieto_max']:g})" + (f"; otros: {', '.join(f'{a:.1f}–{b:.1f}' for a, b in peores[1:])}"
                                                     if len(peores) > 1 else "")))
    d0, med, s0 = primer_cuadro(v, f)
    rel = d0 / med if med else 0
    r.append(("primer", s0 >= 0.02 and rel >= META["primer"],
              f"primer cuadro: detalle {rel * 100:.0f} % de la mediana, desvío del brillo {s0:.3f}"
              + (" (vacío o negro)" if s0 < 0.02 else " (a medio entrar)" if rel < META["primer"] else "")))
    if con_audio:
        lufs, pico = sonoridad(ruta)
        r.append(("lufs", abs(lufs - META["lufs"]) <= META["lufs_tol"],
                  f"sonoridad: {lufs:.1f} LUFS (meta {META['lufs']:g} ± {META['lufs_tol']:g})"))
        r.append(("pico", pico <= META["pico"], f"pico verdadero: {pico:.1f} dBTP (meta ≤ {META['pico']:g}, sin recorte)"))
    else:
        lufs = pico = None
        r.append(("lufs", False, "sonoridad: el MP4 no tiene audio"))
    for n, (c, k) in enumerate(contraste(ruta, textos, w, h) if textos else []):
        r.append((f"contraste{n}", k >= META["contraste"],
                  f"contraste en {c['t']} s ({c['x']},{c['y']},{c['w']}×{c['h']}): {k:.1f}:1 (meta ≥ 4.5:1)"))
    ct, tirones = cortes(v, f, ruta)
    r.append(("cortes", None, f"cortes: {len(ct)} ({len(ct) * 30 / dur:.1f} cada 30 s)"
              + (f" en {', '.join(f'{t:.2f}' for t in ct[:30])}" if ct else "")
              + (f"; tirones (ver saltos.py): {', '.join(f'{t:.2f}' for t in tirones)}" if tirones else "")))
    sb = sobresaltos(energia(ruta), ct) if con_audio else []
    peor_sb = max(sb, key=lambda x: x[1]) if sb else None
    if con_audio:
        r.append(("sobresalto", peor_sb is None or peor_sb[1] <= META["sobresalto"],
                  "sobresalto del audio en los cortes: "
                  + (f"peor +{peor_sb[1]:.1f} dB en {peor_sb[0]:.2f} s ({len(sb)} cortes medidos; meta ≤ +{META['sobresalto']:g})"
                     if peor_sb else "sin cortes medibles")))
    if con_hojas:
        ng, nc = hojas(ruta, salida, ct, paso, dur)
        r.append(("hojas", None, f"hojas: {ng} generales (cada {paso:g} s) + {nc} densas de cortes en {salida}"))
    malos = [x for x in r if x[1] is False]
    if mostrar:
        print(f"{ruta} · {dur:.1f} s · {w}×{h} a {fps:g} fps (medido a {2 * W}×{2 * H} y {W}×{H}, {f:g} fps)")
        for _, ok, txt in r: print(f"  {'info ' if ok is None else 'ok   ' if ok else 'FALLA'}  {txt}")
        n_ok = sum(1 for x in r if x[1])
        print(f"TOTAL: {n_ok} ok · {len(malos)} FALLA → "
              + ("otra pasada" if malos else "pasa la barra medida (falta lo que tiene que ver u oír una persona)"))
    medidas = {"video": ruta, "duracion": round(dur, 2), "congelado_cada_30s": round(c30, 3),
               "quieto_max": round(largo[1] - largo[0], 3), "quieto_max_en": round(largo[0], 2),
               "primer_detalle_rel": round(rel, 3), "lufs": lufs, "pico_dbtp": pico, "cortes": [round(t, 2) for t in ct],
               "sobresalto_db": round(peor_sb[1], 1) if peor_sb else None,
               "falla": [k for k, ok, _ in r if ok is False]}
    if con_hojas: (salida / "medidas.json").write_text(json.dumps(medidas, ensure_ascii=False, indent=1), encoding="utf-8")
    return {k: ok for k, ok, _ in r}, medidas


def probar():
    """Regla: una guardia que nunca falló no se cree. Clips de 9 s (640×360) con defectos puestos a mano; cada
    medida tiene que decir «ok» en el sano y «FALLA» en el roto."""
    tmp = Path(tempfile.mkdtemp())
    seg = "testsrc2=s=640x360:r=30:d=3"
    # sano: tres tomas (cortes en 3 y 6 s), dos «textos» (A blanco sobre negro, B gris sobre gris), audio a ≈ −14 LUFS
    texto = ("drawbox=x=20:y=250:w=200:h=60:color=black:t=fill,"
             + ",".join(f"drawbox=x={30 + 45 * k}:y=262:w=30:h=36:color=white:t=fill" for k in range(4)) + ","
             "drawbox=x=400:y=250:w=200:h=60:color=0x666666:t=fill,"
             + ",".join(f"drawbox=x={410 + 45 * k}:y=262:w=30:h=36:color=0x777777:t=fill" for k in range(4)))
    base = f"{seg}[a];{seg},hflip,negate[b];{seg},vflip[c];[a][b][c]concat=n=3:v=1:a=0,{texto}"

    def clip(nombre, extra_v="", vol="7dB"):
        out = tmp / f"{nombre}.mp4"
        g = f"{base}{extra_v}[v];sine=f=997:d=9,volume={vol}[s]"
        run(["ffmpeg", "-v", "error", "-y", "-filter_complex", g, "-map", "[v]",
             "-map", "[s]", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", str(out)])
        return out

    cajas = [{"x": 20, "y": 250, "w": 200, "h": 60, "t": 1.0}, {"x": 400, "y": 250, "w": 200, "h": 60, "t": 1.0}]
    congelar = ",split[x][y];[x][y]freezeframes=first=120:last=180:replace=120"
    casos = [  # (nombre, clip, opciones, lo esperado)
        ("sano", clip("sano"), {"textos": cajas},
         {"congelado": True, "quieto_max": True, "primer": True, "lufs": True, "pico": True,
          "contraste0": True, "contraste1": False, "sobresalto": True}),
        ("2 s congelados", clip("congelado", congelar), {}, {"congelado": False, "quieto_max": False}),
        ("los mismos 2 s marcados a propósito", tmp / "congelado.mp4", {"quietos": [(3.9, 6.1)]},
         {"congelado": True, "quieto_max": True}),
        ("empieza en negro", clip("negro", ",drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='lt(t,0.2)'"), {},
         {"primer": False}),
        ("primer cuadro a medio entrar", clip("medio", ",drawbox=x=0:y=0:w=iw:h=ih*0.85:color=0x404040:t=fill:"
                                                       "enable='lt(t,0.1)'"), {}, {"primer": False}),
        ("audio a −5 LUFS", clip("fuerte", vol="16dB"), {}, {"lufs": False}),
        ("audio recortado", clip("recorte", vol="26dB"), {}, {"pico": False}),
        ("audio que salta +16 dB en el corte de 6 s", clip("golpe", vol="'if(lt(t,6),0.25,1.6)':eval=frame"), {},
         {"sobresalto": False}),
    ]
    bien = True
    for nombre, ruta, op, esperado in casos:
        res, med = criticar(ruta, tmp / "hojas", op.get("quietos", ()), op.get("textos"), con_hojas=nombre == "sano",
                            mostrar=False)
        dice = [f"{k}={'ok' if res.get(k) else 'FALLA'}" for k in esperado]
        malos = [k for k, e in esperado.items() if res.get(k) != e]
        if nombre == "sano":                               # contraste0: blanco sobre negro; contraste1: gris sobre gris
            ca = contraste(ruta, cajas, 640, 360)
            dice.append(f"(texto A {ca[0][1]:.1f}:1, texto B {ca[1][1]:.1f}:1)")
            nc = len(med["cortes"])
            dice.append(f"cortes {med['cortes']} (esperados 3 y 6)")
            if nc != 2 or not all(any(abs(t - e) < 0.1 for t in med["cortes"]) for e in (3, 6)): malos.append("cortes")
            hg, hc = len(list((tmp / "hojas").glob("hoja_general_*"))), len(list((tmp / "hojas").glob("hoja_corte*")))
            dice.append(f"hojas {hg} generales + {hc} densas")
            if hg != 4 or hc != 4: malos.append("hojas")
        dice.append(f"(congelado {med['congelado_cada_30s']:.2f} s/30 s, quieto máx. {med['quieto_max']:.2f} s, "
                    f"primer {med['primer_detalle_rel'] * 100:.0f} %, {med['lufs']} LUFS, pico {med['pico_dbtp']})")
        print(f"{'bien' if not malos else 'MAL '}  {nombre}: " + " · ".join(dice))
        bien &= not malos
    print("PRUEBA", "PASA" if bien else "FALLA")
    return bien


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a[:1] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    op = lambda k: a[a.index(k) + 1] if k in a else None
    textos = json.loads(Path(op("--textos")).read_text(encoding="utf-8")) if op("--textos") else None
    res, _ = criticar(a[0], op("--salida"), leer_quietos(op("--quietos")), textos, float(op("--paso") or 0.2),
                      "--sin-hojas" not in a)
    sys.exit(1 if any(v is False for v in res.values()) else 0)
