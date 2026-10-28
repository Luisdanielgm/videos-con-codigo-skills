"""Métricas de dinamismo de un MP4 terminado, sin modelos ni tokens: qué tanto se mueve, cada cuánto cambia la imagen, cuánto
tiempo está quieto, qué tan variado es el ritmo y cómo suena. Sirven para cruzarlas con lo que una persona califica a ojo
y ver qué mide lo que ella llama «un video con dinamismo».

    .venv/Scripts/python herramientas/metricas_video.py render/<video>.mp4        # imprime las métricas de un MP4
    .venv/Scripts/python herramientas/metricas_video.py fichas [--solo id,id]     # todos los de clasificatorio/fichas.json → clasificatorio/metricas.json
                                                         # (fichas.json: {"videos": [{"id": ..., "archivo": "<mp4 en render/>"}]})
    .venv/Scripts/python herramientas/metricas_video.py --probar                  # se rompe a propósito: cada «ok» tiene su «FALLA»

Usa la decodificación de `critico.py` (una sola pasada, 320×180 a ≤ 30 fps; ~1 min por minuto de video). Reanudable: lo ya medido
(mismo tamaño y fecha del MP4) se salta.

  activo_pct      % del tiempo en que la imagen cambia de verdad (más de N_PX píxeles entre cuadros; es el contrario de «congelado»)
  mov_medio       % de píxeles que cambian entre cuadros, en promedio (cuánto se mueve)
  mov_p90         lo mismo en el 10 % de los cuadros que más se mueven (los golpes de movimiento)
  quieto_max_s    el tramo quieto más largo
  ritmo_var       variación del movimiento segundo a segundo (0 = parejo todo el video; alto = pausas y golpes alternados)
  cortes_min      cortes y saltos por minuto (`saltos.py`)
  cambios_min     cambios de composición por minuto (la distribución de grises cambia mucho: cortes, transiciones, escenas nuevas)
  detalle_medio   riqueza de bordes (poca = fondo liso con poco; mucha = imagen cargada)
  sonido_pct      % del tiempo con sonido (> −45 dB)    sonido_var  cuánto cambia el nivel del audio (dinámica)
  lufs, pico_db   sonoridad integrada y pico
  efectos_min     ataques de sonido por minuto (clics, golpes, whoosh: el nivel sube ≥ 6 dB de golpe)
  sync_cortes_pct de los cortes, cuántos tienen un ataque de sonido a ±0,2 s (el sonido cae con la imagen); sólo si hay cortes
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import critico  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FICHAS = RAIZ / "clasificatorio" / "fichas.json"
SALIDA = RAIZ / "clasificatorio" / "metricas.json"
VIDEOS = RAIZ / "render"
UMBRAL_CAMBIO = 0.35        # distancia entre distribuciones de gris (0 a 1) que cuenta como cambio de composición


def histograma(x):
    h = np.bincount((x.ravel() // 16).astype(np.int64), minlength=16).astype(np.float64)
    return h / h.sum()


def ataques(db, salto=6.0, piso=-45.0, refractario=2):
    """Instantes (s) en que el sonido arranca de golpe: el nivel sube ≥ `salto` dB de una ventana de 100 ms a la siguiente y queda sobre `piso`.
    Es lo que se oye como un efecto (clic, golpe, whoosh) o como una nota que entra. Entre dos ataques pasan al menos `refractario` ventanas."""
    if len(db) < 2:
        return []
    out, ultimo = [], -10 ** 9
    for i in np.flatnonzero((np.diff(db) >= salto) & (db[1:] > piso)) + 1:
        if i - ultimo >= refractario:
            out.append(round(float(i) / 10, 1))
            ultimo = int(i)
    return out


def sincronia(cortes_t, ataques_t, tol=0.2):
    """Qué parte de los cortes tiene un efecto de sonido a ±`tol` s (None si no hay cortes): el sonido «cae» con la imagen."""
    if not len(cortes_t):
        return None
    return sum(1 for c in cortes_t if any(abs(c - a) <= tol for a in ataques_t)) / len(cortes_t)


def metricas(ruta):
    fps, dur, _w, _h, hay_audio = critico.sonda(str(ruta))
    v, cambio, f = critico.decodificar(str(ruta), fps)
    pct = cambio / (4 * critico.W * critico.H) * 100
    out = {"duracion_s": round(dur, 1), "fps_medido": f}
    out["activo_pct"] = round(float((cambio >= critico.N_PX).mean() * 100), 1)
    out["mov_medio"] = round(float(pct.mean()), 2)
    out["mov_p90"] = round(float(np.percentile(pct, 90)), 2)
    largo = critico.congelado(cambio, f, dur, [])[1]
    out["quieto_max_s"] = round(float(largo[1] - largo[0]), 2)
    por_seg = [pct[i:i + int(round(f))].mean() for i in range(0, len(pct) - int(round(f)) + 1, int(round(f)))] or [0.0]
    m = float(np.mean(por_seg))
    out["ritmo_var"] = round(float(np.std(por_seg) / m), 2) if m > 0 else 0.0
    cortes_t, _tirones = critico.cortes(v, f, str(ruta))
    out["cortes_min"] = round(len(cortes_t) / dur * 60, 1)
    paso = max(1, int(round(f / 2)))
    muestra = v[::paso]
    hs = [histograma(x) for x in muestra]
    cambios = sum(1 for a, b in zip(hs, hs[1:]) if 0.5 * np.abs(a - b).sum() > UMBRAL_CAMBIO)
    out["cambios_min"] = round(cambios / dur * 60, 1)
    out["detalle_medio"] = round(float(np.mean([critico.detalle(x) for x in muestra])), 3)
    if hay_audio:
        db = critico.energia(str(ruta))
        con = db[db > -45] if len(db) else db
        out["sonido_pct"] = round(float(len(con) / len(db) * 100), 1) if len(db) else 0.0
        out["sonido_var"] = round(float(np.std(con)), 2) if len(con) > 1 else 0.0
        out["lufs"], out["pico_db"] = critico.sonoridad(str(ruta))
        at = ataques(db)
        out["efectos_min"] = round(len(at) / dur * 60, 1)
        s = sincronia(cortes_t, at)
        if s is not None:
            out["sync_cortes_pct"] = round(s * 100, 1)
    return out


def medir_fichas(solo=None):
    fichas = json.loads(FICHAS.read_text(encoding="utf-8"))["videos"]
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.is_file() else {}
    for i, v in enumerate(fichas, 1):
        if solo and v["id"] not in solo:
            continue
        p = VIDEOS / v["archivo"]
        if not p.is_file():
            print(f"[{i}/{len(fichas)}] {v['id']}: no existe {v['archivo']}")
            continue
        sello = {"tam": p.stat().st_size, "mtime": int(p.stat().st_mtime)}
        if previo.get(v["id"], {}).get("sello") == sello:
            print(f"[{i}/{len(fichas)}] {v['id']}: ya medido")
            continue
        print(f"[{i}/{len(fichas)}] {v['id']} …", flush=True)
        previo[v["id"]] = {"sello": sello, "archivo": v["archivo"], **metricas(p)}
        tmp = SALIDA.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(previo, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(SALIDA)
    print("listo")


# ───────────── pruebas ─────────────
def _ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def _clip(ruta, video, audio, d=4):
    _ff("-f", "lavfi", "-i", f"{video}:d={d}", "-f", "lavfi", "-i", audio, "-t", str(d), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(ruta))


def probar():
    ok = fallas = 0

    def caso(nombre, cond):
        nonlocal ok, fallas
        print(f"  {'ok  ' if cond else 'FALLA'}  {nombre}")
        ok += bool(cond)
        fallas += not cond

    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        seno, mudo = "sine=frequency=440:sample_rate=44100", "anullsrc=r=44100:cl=mono"
        _clip(t / "quieto.mp4", "color=c=red:s=320x180:r=30", mudo)
        _clip(t / "mueve.mp4", "testsrc2=s=320x180:r=30", seno)
        # cuatro colores muy distintos, uno por segundo: tres cortes
        for i, c in enumerate(["red", "blue", "green", "white"]):
            _clip(t / f"c{i}.mp4", f"color=c={c}:s=320x180:r=30", seno, d=1)
        (t / "lista.txt").write_text("".join(f"file 'c{i}.mp4'\n" for i in range(4)), encoding="utf-8")
        _ff("-f", "concat", "-safe", "0", "-i", str(t / "lista.txt"), "-c", "copy", str(t / "cortes.mp4"))
        # mitad quieta y mitad en movimiento
        (t / "mixto.txt").write_text("file 'quieto.mp4'\nfile 'mueve.mp4'\n", encoding="utf-8")
        _ff("-f", "concat", "-safe", "0", "-i", str(t / "mixto.txt"), "-c", "copy", str(t / "mixto.mp4"))

        q, m, c, x = (metricas(t / n) for n in ("quieto.mp4", "mueve.mp4", "cortes.mp4", "mixto.mp4"))
        caso(f"quieto: nada activo ({q['activo_pct']} %) y el tramo quieto es todo el video ({q['quieto_max_s']} s)", q["activo_pct"] == 0 and q["quieto_max_s"] >= 3.5)
        caso(f"quieto: sin cortes ni cambios ({q['cortes_min']}, {q['cambios_min']})", q["cortes_min"] == 0 and q["cambios_min"] == 0)
        caso(f"movimiento: casi siempre activo ({m['activo_pct']} %) y sin tramo quieto ({m['quieto_max_s']} s)", m["activo_pct"] > 90 and m["quieto_max_s"] == 0)
        caso(f"movimiento: mueve más que lo quieto ({m['mov_medio']} contra {q['mov_medio']})", m["mov_medio"] > q["mov_medio"] + 1)
        caso(f"cortes: cuenta los tres cortes de 4 s (≈ 45 por minuto; salió {c['cortes_min']})", 30 <= c["cortes_min"] <= 60)
        caso(f"cambios de composición: también los ve ({c['cambios_min']} por minuto)", 30 <= c["cambios_min"] <= 60)
        caso(f"ritmo: mitad quieto y mitad movimiento varía más ({x['ritmo_var']}) que lo parejo ({m['ritmo_var']})", x["ritmo_var"] > m["ritmo_var"] + 0.3)
        caso(f"detalle: la carta de ajuste tiene más bordes que un color liso ({m['detalle_medio']} contra {q['detalle_medio']})", m["detalle_medio"] > q["detalle_medio"] + 0.02)
        caso(f"audio: con seno suena todo el tiempo ({m['sonido_pct']} %), mudo no ({q['sonido_pct']} %)", m["sonido_pct"] > 95 and q["sonido_pct"] < 5)
        caso("audio: sonoridad medida en el que suena", "lufs" in m and m["lufs"] > -40)
        # golpes de sonido justo en los cortes (0 s, 1 s, 2 s, 3 s) contra un seno parejo
        golpes = "aevalsrc=sin(2*PI*440*t)*lt(mod(t\\,1)\\,0.15):s=44100"
        for i, col in enumerate(["red", "blue", "green", "white"]):
            _clip(t / f"g{i}.mp4", f"color=c={col}:s=320x180:r=30", golpes, d=1)
        (t / "g.txt").write_text("".join(f"file 'g{i}.mp4'\n" for i in range(4)), encoding="utf-8")
        _ff("-f", "concat", "-safe", "0", "-i", str(t / "g.txt"), "-c", "copy", str(t / "golpes.mp4"))
        g = metricas(t / "golpes.mp4")
        caso(f"efectos: ve los golpes de sonido (≈ 45 por minuto; salió {g['efectos_min']}) y no en un seno parejo ({c['efectos_min']})", 30 <= g["efectos_min"] <= 60 and c["efectos_min"] == 0)
        caso(f"sincronía: los cortes con golpe encima ({g.get('sync_cortes_pct')} %) contra los de seno parejo ({c.get('sync_cortes_pct')} %)", g.get("sync_cortes_pct") == 100.0 and c.get("sync_cortes_pct") == 0.0)
        caso("sincronía: sin cortes no hay porcentaje", "sync_cortes_pct" not in q)
        caso("ataques: sube de golpe, respeta el refractario y el piso", ataques(np.array([-60.0, -20, -10, -60, -20])) == [0.1, 0.4]
             and ataques(np.array([-70.0, -60, -55])) == [] and ataques(np.array([-30.0, -30])) == [])
        caso("sincronía: tolerancia ±0,2 s y sin cortes da None", sincronia([1.0, 2.0], [1.15]) == 0.5 and sincronia([1.0], [1.3]) == 0.0 and sincronia([], [1.0]) is None)

        # reanudable: lo ya medido (mismo sello) no se vuelve a medir
        global FICHAS, SALIDA, VIDEOS
        guardado = (FICHAS, SALIDA, VIDEOS)
        try:
            FICHAS, SALIDA, VIDEOS = t / "fichas.json", t / "metricas.json", t
            FICHAS.write_text(json.dumps({"videos": [{"id": "q", "archivo": "quieto.mp4"}, {"id": "falta", "archivo": "nada.mp4"}]}), encoding="utf-8")
            medir_fichas()
            primero = json.loads(SALIDA.read_text(encoding="utf-8"))
            caso("fichas: mide lo que existe y se salta lo que no", list(primero) == ["q"] and primero["q"]["activo_pct"] == 0)
            primero["q"]["activo_pct"] = 123.0                     # si lo volviera a medir, esto se pisaría
            SALIDA.write_text(json.dumps(primero), encoding="utf-8")
            medir_fichas()
            caso("fichas: lo ya medido con el mismo sello no se vuelve a medir", json.loads(SALIDA.read_text(encoding="utf-8"))["q"]["activo_pct"] == 123.0)
            medir_fichas(solo={"no-existe"})
            caso("fichas: --solo con un id desconocido no toca nada", json.loads(SALIDA.read_text(encoding="utf-8"))["q"]["activo_pct"] == 123.0)
        finally:
            FICHAS, SALIDA, VIDEOS = guardado

    print(f"\n  {ok} ok, {fallas} FALLA")
    return fallas == 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a[:1] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    if a[:1] == ["fichas"]:
        medir_fichas(set(a[a.index("--solo") + 1].split(",")) if "--solo" in a else None)
    elif a and Path(a[0]).is_file():
        print(json.dumps(metricas(a[0]), ensure_ascii=False, indent=1))
    else:
        print(__doc__)
