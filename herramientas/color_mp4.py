"""Banderas de color de todo MP4 final del proyecto: BT.709 en rango tv, etiquetado.

Sin ellas, la exportación del navegador salía en yuvj420p de rango completo con matriz BT.601, y las de cairo o
recodificadas, sin etiqueta. Chromium (y los teléfonos) leen un video HD sin etiqueta como BT.709: medido,
el rojo y el verde se corrían hasta 25 niveles y el negro #0a0a0a hasta 10. Con estas banderas, ≤ 2 niveles.
`accurate_rnd+full_chroma_int` deja exactos los grises que venían de JPEG (antes, 3–4 niveles corridos).
Con ffmpeg ≥ 7 basta ponerlas antes del archivo de salida: la conversión la arma solo, sin `-vf`, y una entrada
sin etiqueta se toma como BT.601 y se convierte bien. `verificar_export.py` revisa que el MP4 las lleve.

Arreglar los MP4 que ya estaban hechos:

    .venv/Scripts/python herramientas/color_mp4.py arreglar <mp4> [<mp4> …]     # o --todos (todo render/*.mp4)
    .venv/Scripts/python herramientas/color_mp4.py arreglar --todos --lote 40    # sólo 40 archivos y se detiene
    .venv/Scripts/python herramientas/color_mp4.py arreglar --todos --max-seg 120   # a lo sumo ~2 min de reloj
    .venv/Scripts/python herramientas/color_mp4.py --probar                      # cada caso, roto a propósito

`--max-seg N` limita el tiempo de reloj: no empieza un archivo que, a RITMO_MIN (0,5 min de video por minuto de reloj),
no cabe en lo que queda; ese archivo se salta, dice «largo» y cuánto necesita, y queda para una corrida aparte.
No se pasa del tope más que por el error de esa estimación; los que sólo se etiquetan casi no gastan tiempo.

`--lote N` cuenta los archivos que de verdad se arreglan (los «ya está» no cuentan) y se detiene al llegar a N; volver a
correr el mismo comando sigue donde quedó. Un archivo `render/parar-color` detiene el lote entre un archivo
y el siguiente (sin perder el que está en curso); se borra solo al detenerse.

- yuv420p sin etiqueta (cairo, Manim, Blender vía componer.py, ffmpeg): se etiqueta BT.601 SIN recodificar (los
  cuadros decodificados salen idénticos). Todo ffmpeg del repo escribía BT.601 al pasar de RGB a YUV sin etiqueta.
- yuvj420p o rango pc (exportación del navegador): se recodifica una vez a BT.709 en rango tv, con la misma
  resolución, fps y audio (copiado), CRF 16 y el bitrate topado a 1,1 veces el del original (no crece el archivo).
- En los dos casos el original se MUEVE a render/antes-color/ (no se borra ni se pisa).
- Ya etiquetado en rango tv: no se toca. Otro formato: se avisa y no se toca.
Antes de reemplazar comprueba la etiqueta nueva y que la cantidad de cuadros y la duración sean las mismas.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

COLOR_709 = ["-sws_flags", "accurate_rnd+full_chroma_int", "-colorspace", "bt709", "-color_primaries", "bt709",
             "-color_trc", "bt709", "-color_range", "tv"]

# Manim (CE 0.21) escribe BT.601 en rango tv sin etiqueta (medido con un render de colores conocidos).
# Al copiar su video sin recodificar (`-c:v copy`), esto le pone la etiqueta verdadera; Chromium la respeta (≤ 1 nivel).
ETIQUETA_601 = ["-bsf:v", "h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1"
                ":matrix_coefficients=6"]

RAIZ = Path(__file__).resolve().parent.parent
ANTES = Path(os.environ.get("VIDEOS_ANTES_COLOR", "render/antes-color"))
PARAR = Path(os.environ.get("VIDEOS_PARAR_COLOR", "render/parar-color"))   # (las dos se cambian en --probar)
CUADROS_POR_SEG = 6   # cuadros por segundo de reloj que se supone como mínimo al recodificar 1080p con preset medium. Medido
#  con la PC cargada: ~8 (7,9 en un archivo de 60 fps: 1651 cuadros en ~210 s) a ~11. Se calcula con CUADROS, no con
#  segundos de video: un archivo de 60 fps cuesta el doble que uno de 30 de la misma duración.
HECHO = Path(os.environ.get("VIDEOS_HECHO_COLOR", "render/color-hecho.txt"))   # «nombre|tamaño» ya arreglados


def sonda(ruta, contar=True):
    """pix_fmt, rango, matriz, cuadros, duración, fps y bitrate de video. `contar=False` no lee los paquetes (cuadros = 0):
    sirve para decidir qué hacer con un archivo ya arreglado sin pagar el conteo."""
    s = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", *(["-count_packets"] if contar else []),
                        "-show_entries", "stream=pix_fmt,color_range,color_space,nb_read_packets,bit_rate,r_frame_rate"
                        ":format=duration", "-of", "default=nw=1", str(ruta)], capture_output=True, text=True).stdout
    d = dict(l.split("=", 1) for l in s.split() if "=" in l)
    num = lambda k: float(d[k]) if d.get(k, "N/A") not in ("N/A", "") else 0.0
    a, b = (d.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {"pix": d.get("pix_fmt"), "rango": d.get("color_range"), "matriz": d.get("color_space"),
            "cuadros": int(num("nb_read_packets")), "dur": num("duration"), "bitrate": num("bit_rate"),
            "fps": float(a) / float(b or 1)}


def bien(s):
    return s["pix"] == "yuv420p" and s["rango"] == "tv" and s["matriz"] in ("bt709", "smpte170m")


def que_hacer(s):
    if bien(s):
        return "ya está"
    if s["pix"] == "yuv420p" and s["rango"] in ("unknown", None) and s["matriz"] in ("unknown", None):
        return "etiquetar"
    if s["pix"] == "yuvj420p" or s["rango"] == "pc":
        return "recodificar"
    return "no sé"


def arreglar(ruta, antes=ANTES):
    """Devuelve (acción, detalle). Escribe a un temporal y sólo reemplaza si la comprobación pasa."""
    ruta = Path(ruta)
    s = sonda(ruta, contar=False)
    accion = que_hacer(s)
    if accion in ("ya está", "no sé"):
        return accion, f"{s['pix']}, rango {s['rango']}, matriz {s['matriz']}"
    s = sonda(ruta)                                     # el conteo de cuadros sólo se paga si hay que arreglarlo
    tmp = ruta.with_name(ruta.stem + ".color-tmp.mp4")
    if accion == "etiquetar":
        cmd = ["-map", "0", "-c", "copy", *ETIQUETA_601]
    else:
        tope = max(s["bitrate"], 500_000) * 1.1
        cmd = ["-map", "0", "-c:a", "copy", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
               "-maxrate", f"{tope:.0f}", "-bufsize", f"{2 * tope:.0f}", "-pix_fmt", "yuv420p", *COLOR_709]
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ruta), *cmd, "-movflags", "+faststart", str(tmp)],
                       capture_output=True, text=True)
    n = sonda(tmp) if tmp.exists() else None
    if r.returncode or not n or not bien(n) or n["cuadros"] != s["cuadros"] or abs(n["dur"] - s["dur"]) > 0.1:
        tmp.unlink(missing_ok=True)
        return "FALLA", (r.stderr.strip()[-200:] or f"salió {n}") + f" (original: {s['cuadros']} cuadros, {s['dur']:.2f} s)"
    antes.mkdir(parents=True, exist_ok=True)            # el original no se pisa: se mueve aparte
    shutil.move(str(ruta), str(antes / ruta.name))
    tmp.replace(ruta)
    peso = f", {s['bitrate'] / 1e6:.1f} → {n['bitrate'] / 1e6:.1f} Mb/s" if accion == "recodificar" else ""
    return accion, f"{n['cuadros']} cuadros, {n['dur']:.2f} s{peso}"


def revisar_salida(ruta, cuadros=None, con_audio=None):
    """[(caso, ok, detalle)] de un MP4 que sale de una herramienta: etiqueta de color, cantidad de cuadros y audio."""
    s = sonda(ruta)
    casos = [("color", bien(s), f"{s['pix']}, rango {s['rango']}, matriz {s['matriz']}")]
    if cuadros is not None:
        casos.append(("cuadros", s["cuadros"] == cuadros, f"{s['cuadros']} de {cuadros}"))
    if con_audio is not None:
        hay = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                   "-of", "csv=p=0", str(ruta)], capture_output=True, text=True).stdout.strip())
        casos.append(("audio", hay == con_audio, "tiene audio" if hay else "sin audio"))
    return casos


def probar_salida(nombre, hacer, cuadros, con_audio=True):
    """Autoprueba común de las herramientas que escriben un MP4 final (servidor, pizarra, componer, estilo, ascii).
    `hacer(entrada, salida, tmp)` corre la herramienta sobre `entrada`: 1 s de 320×240 a 30 fps con un tono (30
    cuadros), o la ignora si arma su propia entrada. La salida tiene que pasar `revisar_salida` entera, y la misma salida
    rota a propósito (un cuadro menos y sin etiqueta de color) tiene que dar FALLA."""
    sys.stdout.reconfigure(encoding="utf-8")         # al redirigir, Windows imprime en cp1252
    ok = True
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        entrada, salida, roto = t / "entrada.mp4", t / "salida.mp4", t / "roto.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=1", "-f", "lavfi",
                        "-i", "sine=frequency=440:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-shortest", str(entrada)], check=True)
        hacer(entrada, salida, t)
        if not salida.exists():
            print(f"  FALLA {nombre}: no salió el MP4")
            print("PRUEBA FALLA")
            return False
        for caso, paso, det in revisar_salida(salida, cuadros, con_audio):
            ok &= paso
            print(f"  {'ok   ' if paso else 'FALLA'} {nombre}, {caso}: {det}")
        # una recodificación conserva la etiqueta: se borra a propósito con setparams
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(salida), "-frames:v", str(cuadros - 1), "-vf",
                        "setparams=range=unknown:color_primaries=unknown:color_trc=unknown:colorspace=unknown",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", str(roto)], check=True)
        caidos = [c for c, paso, _ in revisar_salida(roto, cuadros, con_audio) if not paso]
        atrapa = {"color", "cuadros"} <= set(caidos)
        ok &= atrapa
        print(f"  {'ok   ' if atrapa else 'FALLA'} salida rota a propósito (un cuadro menos, sin etiqueta): falla "
              f"{', '.join(caidos) or 'nada'} (esperado: color y cuadros)")
    print("PRUEBA", "PASA" if ok else "FALLA")
    return ok


def decodificar(ruta, w, h):
    """El primer cuadro como lo lee Chromium: según su etiqueta, y BT.709 si no la tiene."""
    s = sonda(ruta)
    m = "bt601" if s["matriz"] in ("smpte170m", "bt470bg") else "bt709"
    rng = "pc" if s["rango"] == "pc" else "tv"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-frames:v", "1", "-vf",
                          f"scale=in_color_matrix={m}:in_range={rng},format=rgb24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return raw, w * h * 3


def probar():
    """Con cuadros de colores conocidos: el MP4 del navegador (yuvj) y el de cairo (sin etiqueta) se arreglan y quedan
    a ≤ 3 niveles del color original leídos como Chromium; antes de arreglar, el error pasa de 10 (la prueba ve el daño);
    lo ya etiquetado no se toca; un yuv444p no se toca; y si la salida pierde cuadros, el original queda intacto."""
    import numpy as np
    W, H = 320, 180
    cols = [(10, 10, 10), (230, 57, 70), (42, 157, 143), (40, 200, 60)]
    img = np.zeros((H, W, 3), np.uint8)
    for i, c in enumerate(cols):
        img[:, i * 80:(i + 1) * 80] = c
    rgb = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-"]

    def error(ruta):
        raw, n = decodificar(ruta, W, H)
        d = np.frombuffer(raw[:n], np.uint8).reshape(H, W, 3).astype(int)
        return max(int(np.abs(d[60:120, i * 80 + 20:i * 80 + 60].reshape(-1, 3).mean(0) - c).max().round())
                   for i, c in enumerate(cols))

    ok = True
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        hacer = lambda nombre, extra: subprocess.run(["ffmpeg", "-v", "error", "-y", *rgb, *extra, "-c:v", "libx264",
                                                      "-crf", "18", str(t / nombre)], input=img.tobytes() * 30, check=True)
        hacer("navegador.mp4", ["-pix_fmt", "yuvj420p"])
        hacer("cairo.mp4", ["-pix_fmt", "yuv420p"])
        hacer("bueno.mp4", ["-pix_fmt", "yuv420p", *COLOR_709])
        hacer("raro.mp4", ["-pix_fmt", "yuv444p"])
        shutil.copy(t / "cairo.mp4", t / "corto.mp4")
        casos = []
        for nombre, accion in (("navegador.mp4", "recodificar"), ("cairo.mp4", "etiquetar")):
            e0 = error(t / nombre)
            hecho, det = arreglar(t / nombre, antes=t / "antes")
            e1 = error(t / nombre)
            casos += [(f"{nombre}: el daño se ve antes de arreglar (error {e0} > 10)", e0 > 10),
                      (f"{nombre}: {hecho} ({det}), error {e1} ≤ 3", hecho == accion and e1 <= 3)]
        casos.append(("los dos originales quedaron en antes/",
                      (t / "antes" / "navegador.mp4").exists() and (t / "antes" / "cairo.mp4").exists()))
        casos.append(("lo ya etiquetado no se toca", arreglar(t / "bueno.mp4", antes=t / "antes")[0] == "ya está"))
        casos.append(("un yuv444p no se toca", arreglar(t / "raro.mp4", antes=t / "antes")[0] == "no sé"))
        # rota a propósito: la etiqueta sale bien pero con un cuadro menos → FALLA y el original sigue igual
        global ETIQUETA_601
        guardada, ETIQUETA_601 = ETIQUETA_601, ETIQUETA_601 + ["-frames:v", "29"]
        antes_bytes = (t / "corto.mp4").read_bytes()
        hecho = arreglar(t / "corto.mp4", antes=t / "antes")[0]
        ETIQUETA_601 = guardada
        casos.append(("si pierde un cuadro: FALLA y el original intacto",
                      hecho == "FALLA" and (t / "corto.mp4").read_bytes() == antes_bytes))
        # por lotes: --lote 2 arregla 2 de 3 y deja el tercero intacto; el archivo parar-color corta antes del primero
        entorno = dict(os.environ, VIDEOS_ANTES_COLOR=str(t / "antes-lote"), VIDEOS_PARAR_COLOR=str(t / "parar"),
                       VIDEOS_HECHO_COLOR=str(t / "hecho.txt"))
        tres = [t / f"lote{i}.mp4" for i in range(3)]
        for p in tres:
            shutil.copy(t / "corto.mp4", p)
        corre = lambda *extra: subprocess.run([sys.executable, __file__, "arreglar", *map(str, tres), *extra], env=entorno,
                                              capture_output=True, text=True)
        r = corre("--lote", "2")
        etiquetados = [sonda(p)["matriz"] == "smpte170m" for p in tres]
        casos.append(("--lote 2: arregla 2 y deja el tercero intacto", r.returncode == 0 and etiquetados == [True, True, False]))
        (t / "parar").write_text("")
        corre()
        casos.append(("parar-color: corta antes de arreglar el tercero y se borra solo",
                      not sonda(tres[2])["matriz"] == "smpte170m" and not (t / "parar").exists()))
        corre()
        casos.append(("seguir sin lote termina el tercero", sonda(tres[2])["matriz"] == "smpte170m"))
        # tope por tiempo: un archivo que necesita más de lo que queda se salta (dice «largo») y queda intacto
        hacer("largo.mp4", ["-pix_fmt", "yuvj420p"])
        antes_largo = (t / "largo.mp4").read_bytes()
        r = subprocess.run([sys.executable, __file__, "arreglar", str(t / "largo.mp4"), "--max-seg", "1"], env=entorno,
                           capture_output=True, text=True, encoding="utf-8")
        casos.append(("--max-seg 1: el archivo que no cabe se salta, dice «largo» y queda intacto",
                      "largo" in r.stdout and (t / "largo.mp4").read_bytes() == antes_largo))
        subprocess.run([sys.executable, __file__, "arreglar", str(t / "largo.mp4"), "--max-seg", "600"], env=entorno,
                       capture_output=True, text=True)
        casos.append(("--max-seg 600: ahora sí lo arregla", bien(sonda(t / "largo.mp4"))))
        # lo ya arreglado queda en la lista y no se vuelve a revisar
        r = subprocess.run([sys.executable, __file__, "arreglar", *map(str, tres), str(t / "largo.mp4")], env=entorno,
                           capture_output=True, text=True, encoding="utf-8")
        casos.append(("lo ya arreglado se omite sin revisarlo (omitido 4)", "omitido 4" in r.stdout))
        for nombre, paso in casos:
            ok &= paso
            print(f"  {'ok   ' if paso else 'FALLA'} {nombre}")
    print("PRUEBA", "PASA" if ok else "FALLA")
    return ok


def main():
    for f in (sys.stdout, sys.stderr):
        f.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if "--probar" in a:
        sys.exit(0 if probar() else 1)
    if not a or a[0] != "arreglar":
        sys.exit(__doc__)
    lote = int(a[a.index("--lote") + 1]) if "--lote" in a else None
    tope = float(a[a.index("--max-seg") + 1]) if "--max-seg" in a else None
    rutas = sorted((RAIZ / "render").glob("*.mp4")) if "--todos" in a else \
        [Path(x) for x in a[1:] if not x.startswith("--") and not x.replace(".", "").isdigit()]
    cuenta, hechos, inicio = {}, 0, time.monotonic()
    hecho_antes = set(HECHO.read_text(encoding="utf-8").split("\n")) if HECHO.exists() else set()
    clave = lambda r: f"{r.name}|{r.stat().st_size}"
    for ruta in rutas:
        if ruta.exists() and clave(ruta) in hecho_antes:      # ya arreglado en una corrida anterior: ni se revisa
            cuenta["omitido"] = cuenta.get("omitido", 0) + 1
            continue
        if PARAR.exists():
            PARAR.unlink()
            print("parado por el archivo parar-color", flush=True)
            break
        if lote is not None and hechos >= lote:
            print(f"lote de {lote} completo", flush=True)
            break
        if tope is not None:
            gastado = time.monotonic() - inicio
            if gastado >= tope:
                print(f"tope de {tope:g} s alcanzado ({gastado:.0f} s)", flush=True)
                break
        if ruta.stat().st_size == 0:
            accion, det = "vacío", "0 bytes"
        elif tope is not None and que_hacer(s := sonda(ruta, contar=False)) == "recodificar" \
                and time.monotonic() - inicio + (est := s["dur"] * s["fps"] / CUADROS_POR_SEG) > tope:
            # recodificar tarda ~cuadros / CUADROS_POR_SEG como mucho: si no cabe en lo que queda del tope, se salta y se avisa
            accion, det = "largo", (f"{s['dur']:.0f} s de video a {s['fps']:g} fps: necesita unos {est / 60:.1f} min; "
                                    f"no cabe en lo que queda del tope de {tope:g} s")
        else:
            accion, det = arreglar(ruta)
            if accion in ("ya está", "etiquetar", "recodificar"):        # queda anotado con su tamaño final
                HECHO.parent.mkdir(parents=True, exist_ok=True)
                with HECHO.open("a", encoding="utf-8") as h:
                    h.write(clave(ruta) + "\n")
        hechos += accion in ("etiquetar", "recodificar")
        cuenta[accion] = cuenta.get(accion, 0) + 1
        print(f"{accion:12s} {ruta.name}: {det}", flush=True)
    print("TOTAL:", ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items())))
    sys.exit(1 if cuenta.get("FALLA") else 0)


if __name__ == "__main__":
    main()
