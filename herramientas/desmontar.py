"""Desmonta un video (uno de referencia o uno nuestro) en un mapa que se puede leer antes de escribir código: dónde corta,
a qué pulso va, cuánto dura cada toma y qué se mueve adentro de cada una.

    .venv/Scripts/python herramientas/desmontar.py <video.mp4> [--salida carpeta] [--umbral 8] [--antirrebote 0.3]
    .venv/Scripts/python herramientas/desmontar.py --probar     # video sintético con cortes y pulso conocidos

Deja en `render/desmontar/<video>/` (o `--salida`):
  hoja_NN.jpg          hoja de cuadros: 4 por segundo (menos si el video pasa de 60 s), 30 por hoja, con su tiempo
  diferencias.png      diferencia media en gris entre cada cuadro y el anterior (0–255, a 192 px de lado largo), con
                       el umbral, los cortes en rojo y la grilla de pulsos abajo si hay audio
  calor.png            un mapa de calor por toma: en rojo, el máximo cambio de cada píxel dentro de la toma, sobre su
                       primer cuadro en gris; con el % de la imagen que se mueve (cambia > 25/255 en algún momento)
  calor/toma_NN.png    el mismo mapa, uno por toma
  resumen.txt          lo mismo en texto (y en pantalla); desmontar.json para otro programa
Cómo decide:
  corte       la diferencia pasa el umbral viniendo de abajo, o es 3 veces la mediana de sus vecinos (±6 cuadros);
              no dos cortes a menos de `--antirrebote` s. Una transición de varios cuadros cuenta una vez, al empezar.
              Con mucho movimiento continuo, subir el umbral; con fundidos suaves, bajarlo.
  grilla      si hay audio con golpes: BPM y fase con `cancion.py` (flujo espectral); cuadros por pulso = fps·60/BPM
              y cuántos cortes caen a ±1,5 cuadros de un pulso. El BPM puede salir al doble o a la mitad.
  calor       cada toma sin sus primeros 0,35 s (la estela del corte) ni sus 2 últimos cuadros.
Guarda en memoria cada cuadro en gris a 192×108 (≈ 21 KB): un video de 3 min a 60 fps usa ≈ 220 MB. Sólo numpy, pillow
y ffmpeg.

Método y la idea del mapa de calor: huashu-art-motion (alchaincyf, MIT), `references/01-拆解.md` y
`scripts/analyze/breakdown.py`. Este es nuestro, escrito de nuevo: lee el video de a un cuadro (no todo de una vez), usa
el detector de golpes de `cancion.py` y deja el resumen en español.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cancion  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
LADO = 384                      # lado largo de la decodificación; el gris del análisis va a la mitad (192)
MOVIDO = 25                     # un píxel «se mueve» si cambia más que esto (0–255) en algún momento de la toma
ESTELA = 0.35                   # s que se saltan al empezar cada toma (lo que queda del corte)
ADELANTO = cancion.ADELANTO     # s que la envolvente de cancion.py se adelanta al golpe (medido con clics, ver refinar)


def coma(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def letra(n=14):
    try:
        return ImageFont.load_default(size=n)
    except TypeError:
        return ImageFont.load_default()


def sonda(ruta):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,r_frame_rate,width,height:"
                                   "format=duration", "-of", "json", str(ruta)], capture_output=True, check=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a, b = (v["r_frame_rate"].split("/") + ["1"])[:2]
    return (float(a) / float(b), float(j["format"]["duration"]), v["width"], v["height"],
            any(s["codec_type"] == "audio" for s in j["streams"]))


def tamanos(w, h):
    if w >= h:
        sw, sh = LADO, max(4, round(LADO * h / w / 4) * 4)
    else:
        sw, sh = max(4, round(LADO * w / h / 4) * 4), LADO
    return sw, sh


def decodificar(ruta, fps, dur, sw, sh):
    """Un paso por el video: gris chico de cada cuadro, diferencia con el anterior y los cuadros de la hoja."""
    cps = min(4.0, 240.0 / max(dur, 1e-6))
    quiero = {int(round(k * fps / cps)) for k in range(int(dur * cps) + 1)}
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(ruta), "-vf", f"scale={sw}:{sh}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n_bytes, grises, difs, hoja, i, prev = sw * sh * 3, [], [], [], 0, None
    while True:
        b = p.stdout.read(n_bytes)
        if len(b) < n_bytes:
            break
        rgb = np.frombuffer(b, np.uint8).reshape(sh, sw, 3)
        g = rgb.astype(np.float32) @ np.array([.299, .587, .114], np.float32)
        g = g.reshape(sh // 2, 2, sw // 2, 2).mean(axis=(1, 3))
        if prev is not None:
            difs.append(float(np.abs(g - prev).mean()))
        prev = g
        grises.append(np.round(g).astype(np.uint8))
        if i in quiero:
            hoja.append((i / fps, Image.fromarray(rgb.copy())))
        i += 1
    p.wait()
    return grises, np.array(difs, np.float32), hoja


def detectar_cortes(d, fps, umbral, antirrebote):
    """Cuadro donde empieza cada corte o transición (d[i] es el cambio del cuadro i al i+1: el corte es el i+1)."""
    cortes, separa = [], max(1, int(round(antirrebote * fps)))
    for i in range(len(d)):
        vec = np.concatenate([d[max(0, i - 6):i], d[i + 1:i + 7]])
        med = float(np.median(vec)) if len(vec) else 0.0
        antes = d[i - 1] if i else 0.0
        sube = d[i] >= umbral and (antes < umbral or d[i] >= 3 * max(med, .5))
        if sube and i + 1 - (cortes[-1] if cortes else 0) > separa:      # el cuadro 0 cuenta como corte
            cortes.append(i + 1)
    return cortes


def refinar(env, fa, bpm):
    """`cancion.tempo` mide el período en cuadros enteros de la envolvente (≈ 23 ms): a 120 BPM sale 117 o 123. Se afina
    buscando, cerca de ese valor, el BPM y la fase cuya grilla cae en promedio sobre más golpes."""
    eje, mejor = np.arange(len(env)), (-1.0, bpm, 0.0)
    for b in np.arange(bpm * .96, bpm * 1.04, .05):
        paso = 60 / b * fa
        for c in np.linspace(0, paso, 48, endpoint=False):
            s = float(np.interp(np.arange(c, len(env) - 1, paso), eje, env).mean())
            if s > mejor[0]:
                mejor = (s, float(b), float(c / fa))
    # La envolvente marca el golpe cuando entra en la ventana de 2048 muestras, antes de que suene: con clics
    # sintéticos sale ADELANTADA ≈ 0,08 s. Se corrige para que la grilla caiga en el golpe (y en el corte).
    return mejor[1], (mejor[2] + ADELANTO) % (60 / mejor[1])


def grilla(ruta, dur, con_audio):
    if not con_audio:
        return None
    try:
        x = cancion.leer(str(ruta))
    except subprocess.CalledProcessError:
        return None
    if len(x) < cancion.SR * 2 or float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) < 1e-4:
        return None
    env, fa = cancion.envolvente(x)
    if env.max() <= 0:
        return None
    bpm, t0 = refinar(env, fa, float(cancion.tempo(env, fa)))
    paso = 60 / bpm
    return {"bpm": round(bpm, 2), "inicio": round(t0, 3),
            "pulsos": [round(t0 + k * paso, 4) for k in range(int((dur - t0) / paso) + 1)]}


def calor(grises, a, b, fps):
    """Máximo cambio por píxel entre a y b (cuadros), y la fracción de la imagen que se mueve."""
    a0 = a + (int(round(ESTELA * fps)) if a else 0)
    b0 = b - 2
    if b0 - a0 < 3:
        return None, None, a0
    m = np.zeros(grises[0].shape, np.int16)
    for k in range(a0, b0):
        np.maximum(m, np.abs(grises[k + 1].astype(np.int16) - grises[k]), out=m)
    return m, float((m > MOVIDO).mean()), a0


def dibujar_diferencias(d, fps, cortes, umbral, red, ruta):
    W, H, mx = 1600, 380, 40
    top = max(float(np.percentile(d, 99.5)) * 1.15 if len(d) else 1, umbral * 2)
    im = Image.new("RGB", (W, H), (250, 248, 242))
    dr, f = ImageDraw.Draw(im), letra(13)
    dur = (len(d) + 1) / fps
    X = lambda t: mx + (W - 2 * mx) * t / max(dur, 1e-6)
    Y = lambda v: H - 40 - (H - 70) * min(v, top) / top
    if red:
        for k, t in enumerate(red["pulsos"]):
            dr.line([(X(t), H - 40), (X(t), H - 30 if k % 4 else H - 22)], fill=(150, 150, 150))
    for c in cortes:
        dr.line([(X(c / fps), 20), (X(c / fps), H - 40)], fill=(214, 60, 50), width=2)
    for x0 in range(int(mx), W - mx, 12):
        dr.line([(x0, Y(umbral)), (x0 + 6, Y(umbral))], fill=(90, 120, 200))
    pts = [(X((i + 1) / fps), Y(v)) for i, v in enumerate(d)]
    if len(pts) > 1:
        dr.line(pts, fill=(30, 30, 30), width=1)
    paso = 1 if dur <= 20 else 5 if dur <= 120 else 15
    for s in range(0, int(dur) + 1, paso):
        dr.text((X(s) - 4, H - 18), f"{s}", fill=(60, 60, 60), font=f)
    titulo = f"diferencia en gris entre cuadros (0-255, techo {coma(top, 1)}) · umbral {coma(umbral, 1)} · cortes en rojo"
    dr.text((mx, 4), titulo + (f" · pulsos abajo ({coma(red['bpm'], 1)} BPM)" if red else ""), fill=(0, 0, 0), font=f)
    im.save(ruta)


def mosaico(imgs, cols, ruta):
    w, h = imgs[0].size
    filas = (len(imgs) + cols - 1) // cols
    S = Image.new("RGB", (cols * w, filas * h), (20, 20, 20))
    for k, im in enumerate(imgs):
        S.paste(im, ((k % cols) * w, (k // cols) * h))
    S.save(ruta, quality=85) if str(ruta).endswith(".jpg") else S.save(ruta)


def desmontar(ruta, salida=None, umbral=8.0, antirrebote=0.3, mostrar=True):
    ruta = Path(ruta)
    salida = Path(salida) if salida else RAIZ / "render" / "desmontar" / ruta.stem
    (salida / "calor").mkdir(parents=True, exist_ok=True)
    for viejo in list(salida.glob("hoja_*.jpg")) + list((salida / "calor").glob("toma_*.png")):
        viejo.unlink()
    fps, dur, w, h, con_audio = sonda(ruta)
    sw, sh = tamanos(w, h)
    grises, d, hoja = decodificar(ruta, fps, dur, sw, sh)
    n = len(grises)
    cortes = detectar_cortes(d, fps, umbral, antirrebote)
    red = grilla(ruta, n / fps, con_audio)
    f = letra(14)
    # hoja de cuadros
    for k in range(0, len(hoja), 30):
        celdas = []
        for t, im in hoja[k:k + 30]:
            c = im.copy()
            dd = ImageDraw.Draw(c)
            dd.rectangle([0, 0, 70, 20], fill="black")
            dd.text((4, 2), f"{coma(t)} s", fill="yellow", font=f)
            celdas.append(c)
        mosaico(celdas, 6 if sw >= sh else 10, salida / f"hoja_{k // 30 + 1:02d}.jpg")
    dibujar_diferencias(d, fps, cortes, umbral, red, salida / "diferencias.png")
    # tomas y calor
    bordes = [0] + cortes + [n]
    tomas, tiles = [], []
    for k in range(len(bordes) - 1):
        a, b = bordes[k], bordes[k + 1]
        m, frac, a0 = calor(grises, a, b, fps)
        toma = {"n": k + 1, "desde": round(a / fps, 3), "hasta": round(b / fps, 3), "movimiento": None}
        if m is not None:
            toma["movimiento"] = round(frac * 100, 2)
            base = Image.fromarray(grises[a0]).resize((sw, sh)).convert("RGB")
            roja = np.zeros((m.shape[0], m.shape[1], 3), np.uint8)
            roja[..., 0] = np.clip(m.astype(np.int32) * 4, 0, 255)
            im = Image.blend(base, Image.fromarray(roja).resize((sw, sh)), 0.6)
            dd = ImageDraw.Draw(im)
            dd.rectangle([0, 0, sw, 38], fill="black")          # la letra de pillow no trae «–»: va «-»
            dd.text((4, 2), f"toma {k + 1} · {coma(a / fps)}-{coma(b / fps)} s", fill="yellow", font=f)
            dd.text((4, 20), f"se mueve {coma(frac * 100, 1)} %", fill="yellow", font=f)
            im.save(salida / "calor" / f"toma_{k + 1:02d}.png")
            tiles.append(im)
        tomas.append(toma)
    if tiles:
        mosaico(tiles, 4 if sw >= sh else 6, salida / "calor.png")
    # resumen
    cortes_t = [round(c / fps, 3) for c in cortes]
    largos = [t["hasta"] - t["desde"] for t in tomas]
    en_pulso = None
    if red and cortes_t:
        P = np.array(red["pulsos"])
        en_pulso = sum(bool(len(P)) and float(np.min(np.abs(P - t))) <= 1.5 / fps for t in cortes_t)
    lin = [f"Desmontaje de {ruta}",
           f"{w}×{h} · {coma(fps, 3).rstrip('0').rstrip(',')} fps · {coma(n / fps)} s · {n} cuadros · audio {'sí' if con_audio else 'no'}",
           f"Diferencia media entre cuadros: {coma(float(d.mean()) if len(d) else 0)} (de 255); "
           f"cuadros casi quietos (< 0,5): {coma(100 * float((d < .5).mean()) if len(d) else 0, 1)} %",
           f"Cortes y transiciones ({len(cortes_t)}): " + (" · ".join(coma(t) for t in cortes_t) or "ninguno"),
           f"Tomas: {len(tomas)} · duración mediana {coma(float(np.median(largos)))} s "
           f"(mín {coma(min(largos))} · máx {coma(max(largos))})"]
    if red:
        lin.append(f"Grilla: {coma(red['bpm'], 1)} BPM, primer pulso en {coma(red['inicio'])} s, "
                   f"{coma(fps * 60 / red['bpm'])} cuadros por pulso (cada pulso se calcula desde el tiempo y se redondea; "
                   f"no se suma el redondeo)")
        if en_pulso is not None:
            lin.append(f"Cortes en el pulso (± 1,5 cuadros): {en_pulso} de {len(cortes_t)}")
    else:
        lin.append("Grilla: sin audio con golpes, no hay grilla de pulsos")
    lin.append(f"Movimiento por toma (% de la imagen que cambia > {MOVIDO}/255 en algún momento):")
    for t in tomas:
        mv = "muy corta para medir" if t["movimiento"] is None else f"{coma(t['movimiento'], 1)} %"
        lin.append(f"  toma {t['n']:>2}  {coma(t['desde'])}–{coma(t['hasta'])} s  {mv}")
    medidas = [t for t in tomas if t["movimiento"] is not None]
    if len(medidas) > 1:
        q = min(medidas, key=lambda t: t["movimiento"])
        mm = max(medidas, key=lambda t: t["movimiento"])
        lin.append(f"Más quieta: toma {q['n']} ({coma(q['movimiento'], 1)} %); más movida: toma {mm['n']} "
                   f"({coma(mm['movimiento'], 1)} %)")
    lin.append(f"Archivos en {salida}: hoja_NN.jpg, diferencias.png, calor.png, calor/toma_NN.png, desmontar.json")
    texto = "\n".join(lin)
    (salida / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
    datos = {"video": str(ruta), "fps": fps, "tamano": [w, h], "cuadros": n, "cortes": cortes_t,
             "grilla": ({k: v for k, v in red.items() if k != "pulsos"} if red else None),
             "cortes_en_pulso": en_pulso, "tomas": tomas, "umbral": umbral, "antirrebote": antirrebote}
    (salida / "desmontar.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    if mostrar:
        print(texto)
    datos["salida"] = salida
    return datos


def probar():
    """Video sintético: 2 s que se mueven, 2 s quietos, 2 s que se mueven, cortes secos en 2 y 4 s, clics a 120 BPM.
    Cada caso dice ok o FALLA; también se rompe el video a propósito (sin audio, sin cortes)."""
    tmp = Path(tempfile.mkdtemp(prefix="ideas_desmontar_"))
    ff = lambda *a: subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
    sint = tmp / "sintetico.mp4"
    ff("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=2",
       "-f", "lavfi", "-i", "color=c=0x305070:size=640x360:rate=30:duration=2",
       "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30:duration=2",
       "-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t,0.5),0.03),0.8*sin(2*PI*900*t),0)':s=44100:d=6",
       "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3:a",
       "-pix_fmt", "yuv420p", "-c:a", "aac", str(sint))
    mudo = tmp / "mudo.mp4"
    ff("-i", str(sint), "-an", "-c:v", "copy", str(mudo))
    plano = tmp / "plano.mp4"
    ff("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=6",       # clics a 100 BPM desde 0,2 s
       "-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t+0.4,0.6),0.03),0.8*sin(2*PI*900*t),0)':s=44100:d=6",
       "-pix_fmt", "yuv420p", "-c:a", "aac", str(plano))
    r = desmontar(sint, tmp / "sint", mostrar=False)
    casos = []
    c = r["cortes"]
    casos.append(("cortes en 2 y 4 s, y nada más", len(c) == 2 and all(abs(a - b) <= 2 / 30 for a, b in zip(c, [2, 4])),
                  f"encontró {c}"))
    g = r["grilla"]
    casos.append(("grilla de 120 BPM (± 2)", bool(g) and abs(g["bpm"] - 120) <= 2, f"{g}"))
    casos.append(("cortes en el pulso: 2 de 2", r["cortes_en_pulso"] == 2, f"{r['cortes_en_pulso']}"))
    mv = [t["movimiento"] for t in r["tomas"]]
    casos.append(("toma quieta < 0,5 % y la movida > 2 %",
                  len(mv) == 3 and mv[1] is not None and mv[1] < .5 and (mv[0] or 0) > 2, f"movimiento {mv}"))
    hechos = all((r["salida"] / x).is_file() for x in ("hoja_01.jpg", "diferencias.png", "calor.png", "resumen.txt",
                                                        "calor/toma_02.png", "desmontar.json"))
    casos.append(("escribe hoja, diferencias, calor y resumen", hechos, str(r["salida"])))
    r2 = desmontar(mudo, tmp / "mudo", mostrar=False)
    casos.append(("roto: sin audio → sin grilla", r2["grilla"] is None and len(r2["cortes"]) == 2, f"{r2['grilla']}"))
    r3 = desmontar(plano, tmp / "plano", mostrar=False)
    casos.append(("roto: una sola toma → ningún corte", r3["cortes"] == [] and len(r3["tomas"]) == 1, f"{r3['cortes']}"))
    g3 = r3["grilla"]
    casos.append(("otra grilla: 100 BPM con el primer pulso en 0,2 s",
                  bool(g3) and abs(g3["bpm"] - 100) <= 2 and abs(g3["inicio"] - .2) <= 1.5 / 30, f"{g3}"))
    for nombre, ok, det in casos:
        print(f"{'ok   ' if ok else 'FALLA'}  {nombre}" + ("" if ok else f" ({det})"))
    nf = sum(not ok for _, ok, _ in casos)
    print(f"Total: {len(casos) - nf} ok, {nf} FALLA · archivos en {tmp}")
    return nf == 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a[:1] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    if not a or a[0].startswith("-"):
        print(__doc__)
        sys.exit(2)
    op = lambda k, d: type(d)(a[a.index(k) + 1].replace(",", ".")) if k in a else d
    salida = a[a.index("--salida") + 1] if "--salida" in a else None
    if not Path(a[0]).is_file():
        print(f"no existe {a[0]}")
        sys.exit(2)
    desmontar(a[0], salida, op("--umbral", 8.0), op("--antirrebote", 0.3))
