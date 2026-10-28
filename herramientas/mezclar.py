"""Mezcla compartida: canción + efectos reales en su momento + voz (la música baja sola cuando alguien habla)
→ <carpeta>/mezcla.wav a −14 LUFS. Reemplaza los mezclar.py de cada video (ensayo, épica, comerciales), que
hacían lo mismo cada uno a su manera.

    .venv/Scripts/python herramientas/mezclar.py <carpeta-del-video>        # lee <carpeta>/mezcla.json

mezcla.json (todo opcional salvo lo que haya):
{
  "cancion": {"archivo": "recursos/musica/mixkit-759-vastness.mp3",
              "desde": 0.37,                                   # o bien "bpm", "primer_tiempo", "compas" (desde = ese compás)
              "volumen": 0.55, "entrada": 2, "salida": 4,      # volumen lineal; fundidos en segundos
              "bucle": true, "cruce": 4},                      # si el video es más largo: la canción se repite, con cruce de 4 s
  "voz": "narracion.wav",                                      # relativo a la carpeta; si está, la canción se agacha
  "agachar": {"umbral": 0.02, "ratio": 6, "ataque": 40, "suelta": 600},
  "efectos": [{"archivo": "impacto/bum-grave.wav", "en": 3.2, "db": -3, "alinear": "pico"}],
                                                               # archivo relativo a recursos/efectos/listos (o al repo);
                                                               # "pico": el golpe del efecto cae justo en "en" (indice.json)
  "efectos_de": "efectos.json",                                # más efectos, de un archivo (los escribe la escena de Manim)
  "extra": [{"archivo": "efectos/musica.wav", "volumen": 0.35}],   # pistas ya armadas (p. ej. las de musica.py)
  "duracion": 41.5,                                            # si no: la de tiempos.js/tiempos.json, la voz o la canción
  "lufs": -14,
  "realce": 6                                                  # opcional: sube y limita antes de normalizar (efectos sueltos)
}
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EFECTOS = RAIZ / "recursos" / "efectos"


def duracion_de(carpeta, m):
    if "duracion" in m: return float(m["duracion"])
    for nombre in ("tiempos.json", "tiempos.js"):
        f = carpeta / nombre
        if f.exists():
            txt = f.read_text(encoding="utf-8")
            if nombre.endswith(".js"): txt = re.search(r"=\s*(\{.*\})\s*;", txt, re.S).group(1)
            return float(json.loads(txt)["total"])
    return duracion_archivo(carpeta / m["voz"] if "voz" in m else RAIZ / m["cancion"]["archivo"])


def duracion_archivo(ruta):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                                capture_output=True, text=True, check=True).stdout)


def picos():
    f = EFECTOS / "indice.json"
    if not f.exists(): return {}
    return {Path(e["archivo"]).as_posix(): float(e.get("pico_s", 0)) for e in json.loads(f.read_text(encoding="utf-8"))}


def ruta_efecto(a):
    for base in (EFECTOS / "listos", EFECTOS, RAIZ):
        if (base / a).exists(): return base / a
    raise FileNotFoundError(f"efecto no encontrado: {a}")


def mezclar(carpeta):
    carpeta = Path(carpeta).resolve()
    m = json.loads((carpeta / "mezcla.json").read_text(encoding="utf-8"))
    total = duracion_de(carpeta, m)
    entradas, filtros, pistas = [], [], []
    def entrada(args):
        entradas.extend(args); return len([a for a in entradas if a == "-i"]) - 1
    voz = None
    if "voz" in m:
        i = entrada(["-i", str(carpeta / m["voz"])])
        filtros.append(f"[{i}:a]aresample=44100,apad,atrim=0:{total:.3f},asplit=2[voz][llave]"); voz = "voz"
    if "cancion" in m:
        c = m["cancion"]
        desde = c.get("desde")
        if desde is None and "bpm" in c: desde = c.get("primer_tiempo", 0) + c.get("compas", 0) * 4 * 60 / c["bpm"]
        desde = desde or 0
        if c.get("bucle"):
            largo, cruce = duracion_archivo(RAIZ / c["archivo"]), c.get("cruce", 4)
            n = max(1, math.ceil((desde + total - cruce) / (largo - cruce)))
            i = entrada(["-i", str(RAIZ / c["archivo"])])
            filtros.append(f"[{i}:a]aresample=44100,asplit={n}" + "".join(f"[c{k}]" for k in range(n)))
            previa = "c0"
            for k in range(1, n):
                filtros.append(f"[{previa}][c{k}]acrossfade=d={cruce}[b{k}]"); previa = f"b{k}"
            filtros.append(f"[{previa}]atrim={desde:.3f}:{desde + total:.3f},asetpts=PTS-STARTPTS[cancion]")
            fuente = "[cancion]"
        else:
            i = entrada(["-ss", f"{desde:.3f}", "-t", f"{total:.3f}", "-i", str(RAIZ / c["archivo"])])
            fuente = f"[{i}:a]aresample=44100,"
        filtros.append(f"{fuente}afade=t=in:d={c.get('entrada', 1)},"
                       f"afade=t=out:st={max(0, total - c.get('salida', 3)):.2f}:d={c.get('salida', 3)},volume={c.get('volumen', .6)}[mus]")
        if voz:
            a = {"umbral": .02, "ratio": 6, "ataque": 40, "suelta": 600, **m.get("agachar", {})}
            filtros.append(f"[mus][llave]sidechaincompress=threshold={a['umbral']}:ratio={a['ratio']}:attack={a['ataque']}:release={a['suelta']}[fondo]")
            pistas.append("[fondo]")
        else:
            pistas.append("[mus]")
    elif voz:
        filtros.append("[llave]anullsink")
    if voz: pistas.append("[voz]")
    pk = picos()
    efectos = m.get("efectos", []) + (json.loads((carpeta / m["efectos_de"]).read_text(encoding="utf-8")) if "efectos_de" in m else [])
    por_archivo = {}                                  # cada efecto distinto se abre una sola vez y se copia (asplit)
    for e in efectos: por_archivo.setdefault(e["archivo"], []).append(e)
    k = 0
    for a, usos in por_archivo.items():
        ruta = ruta_efecto(a)
        rel = ruta.relative_to(EFECTOS).as_posix() if EFECTOS in ruta.parents else ""
        i = entrada(["-i", str(ruta)])
        copias = [f"s{k + j}" for j in range(len(usos))]
        filtros.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,asplit={len(usos)}" + "".join(f"[{c}]" for c in copias))
        for c, e in zip(copias, usos):
            t0 = float(e["en"]) - (pk.get(rel, 0) if e.get("alinear") == "pico" else 0)
            ms = max(0, int(round(t0 * 1000)))
            filtros.append(f"[{c}]volume={e.get('db', 0)}dB,adelay={ms}|{ms}[e{k}]")
            pistas.append(f"[e{k}]"); k += 1
    for k, x in enumerate(m.get("extra", [])):
        i = entrada(["-i", str(carpeta / x["archivo"])])
        filtros.append(f"[{i}:a]aresample=44100,volume={x.get('volumen', 1)}[x{k}]"); pistas.append(f"[x{k}]")
    lufs = m.get("lufs", -14)
    # "realce": dB que se suben con un limitador ANTES de normalizar. Con efectos sueltos sin cama, los picos de los clics no
    # dejan que loudnorm llegue a −14 (quedaban en −18…−21); el limitador recorta esos picos y le deja lugar.
    realce = m.get("realce", 0)
    previo = f"volume={realce}dB,alimiter=limit=0.5:level=0:attack=1:release=50," if realce else ""
    # una pista de silencio de `total` segundos: con sólo efectos (sin voz ni canción) la mezcla terminaba con el último efecto
    # y el MP4 salía corto. `apad` después de amix no alcanzó: con efectos copiados por asplit se
    # quedaba esperando para siempre o no rellenaba.
    i = entrada(["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"])
    pistas.append(f"[{i}:a]")
    filtros.append(f"{''.join(pistas)}amix=inputs={len(pistas)}:normalize=0:duration=longest,atrim=0:{total:.3f},"
                   f"{previo}loudnorm=I={lufs}:TP=-2:LRA=11[out]")
    salida = carpeta / "mezcla.wav"
    grafo = carpeta / "mezcla_filtro.txt"             # en un archivo: con cientos de efectos no entra en la línea de comandos
    grafo.write_text(";\n".join(filtros), encoding="utf-8")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-/filter_complex", str(grafo), "-map", "[out]",
                        "-ar", "44100", "-ac", "2", str(salida)], check=True)
    finally:
        grafo.unlink(missing_ok=True)
    print(f"mezcla.wav {total:.1f} s · {len(pistas)} pistas ({len(efectos)} efectos) · {lufs} LUFS")


def probar():
    """Regla: una guardia nueva se rompe a propósito antes de creerle. Una mezcla de 4 s con sonidos sintéticos en una carpeta temporal:
    voz de 440 Hz entre 1 y 2,5 s, canción de 220 Hz todo el rato y dos clics de ruido (uno por `efectos`, otro por `efectos_de`).
    Se mide la salida de verdad: el volumen en LUFS, cuánto baja la canción cuando habla la voz y en qué instante cae cada clic."""
    import tempfile
    import numpy as np
    import soundfile as sf
    SR = 44100
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    t = np.arange(int(6 * SR)) / SR
    rng = np.random.default_rng(3)
    clic = rng.standard_normal(int(.06 * SR)) * np.exp(-np.arange(int(.06 * SR)) / SR / .015) * .8

    def amplitud(x, hz, a, b):                       # amplitud de una frecuencia en [a, b) s
        s = x[int(a * SR):int(b * SR)]
        return float(np.abs(np.fft.rfft(s * np.hanning(len(s))))[int(round(hz * len(s) / SR))])

    def agudos(x, a, b):                             # energía por encima de 3 kHz en [a, b) s (donde sólo hay clics)
        s = x[int(a * SR):int(b * SR)]
        return float(np.sum(np.abs(np.fft.rfft(s))[np.fft.rfftfreq(len(s), 1 / SR) > 3000] ** 2))

    def lufs(ruta):
        r = subprocess.run(["ffmpeg", "-nostats", "-i", str(ruta), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
        return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        voz = np.where((t >= 1) & (t < 2.5), .5 * np.sin(2 * np.pi * 440 * t), 0)[:int(4 * SR)]
        sf.write(tmp / "voz.wav", voz, SR)
        sf.write(tmp / "cancion.wav", .5 * np.sin(2 * np.pi * 220 * t), SR)
        sf.write(tmp / "clic.wav", clic, SR)
        (tmp / "efectos.json").write_text(json.dumps([{"archivo": str(tmp / "clic.wav"), "en": .5}]), encoding="utf-8")
        cfg = {"cancion": {"archivo": str(tmp / "cancion.wav"), "desde": 0, "volumen": .6, "entrada": .1, "salida": .1},
               "voz": "voz.wav", "efectos": [{"archivo": str(tmp / "clic.wav"), "en": 3.2, "db": -3}],
               "efectos_de": "efectos.json", "duracion": 4.0, "lufs": -14}
        (tmp / "mezcla.json").write_text(json.dumps(cfg), encoding="utf-8")
        mezclar(tmp)
        x, sr = sf.read(tmp / "mezcla.wav")
        caso("44,1 kHz estéreo", (sr, x.shape[1]), (44100, 2))
        caso("dura lo que dice `duracion` (±50 ms)", abs(x.shape[0] / sr - 4.0) < .05, True)
        caso("volumen de plataforma: -14 LUFS (±1,5)", abs(lufs(tmp / "mezcla.wav") + 14) < 1.5, True)
        m = x.mean(axis=1)
        sola, con_voz = amplitud(m, 220, .15, .95), amplitud(m, 220, 1.2, 2.3)
        caso("la canción baja sola cuando habla la voz (a menos de la mitad)", con_voz < .5 * sola, True)
        pico_voz = amplitud(m, 440, 1.2, 2.3)
        caso("y la voz se oye (más que la canción en ese tramo)", pico_voz > con_voz, True)
        for en, nombre in ((3.2, "`efectos`"), (.5, "`efectos_de`")):
            ventana = np.array([agudos(m, a, a + .05) for a in np.arange(en - .3, en + .3, .05)])
            instante = float(np.arange(en - .3, en + .3, .05)[ventana.argmax()])
            caso(f"el clic de {nombre} cae en {en} s (±50 ms)", abs(instante - en) <= .05, True)
        caso("el archivo de trabajo (mezcla_filtro.txt) no queda", (tmp / "mezcla_filtro.txt").exists(), False)

        solo = dict(cfg); solo.pop("voz"); solo.pop("efectos"); solo.pop("efectos_de")
        (tmp / "mezcla.json").write_text(json.dumps(solo), encoding="utf-8")
        mezclar(tmp)
        y, _ = sf.read(tmp / "mezcla.wav")
        caso("sin voz la canción no se agacha (misma amplitud en todo)", amplitud(y.mean(axis=1), 220, 1.2, 2.3) > .8 * amplitud(y.mean(axis=1), 220, .15, .95), True)

        (tmp / "tiempos.json").write_text(json.dumps({"total": 2.5}), encoding="utf-8")
        solo.pop("duracion")
        (tmp / "mezcla.json").write_text(json.dumps(solo), encoding="utf-8")
        mezclar(tmp)
        z, _ = sf.read(tmp / "mezcla.wav")
        caso("sin `duracion`, la toma de tiempos.json (2,5 s)", abs(z.shape[0] / SR - 2.5) < .05, True)

        sueltos = {"efectos": [{"archivo": str(tmp / "clic.wav"), "en": .5}], "duracion": 3.0, "lufs": -14}
        (tmp / "mezcla.json").write_text(json.dumps(sueltos), encoding="utf-8")
        mezclar(tmp)
        e, _ = sf.read(tmp / "mezcla.wav")
        caso("sólo efectos (sin voz ni canción): igual dura `duracion` (3 s)", abs(e.shape[0] / SR - 3.0) < .05, True)

        malo = dict(cfg); malo["efectos"] = [{"archivo": str(tmp / "no-existe.wav"), "en": 1}]
        (tmp / "mezcla.json").write_text(json.dumps(malo), encoding="utf-8")
        try:
            mezclar(tmp)
            detalle = "no falló"
        except FileNotFoundError:
            detalle = "FileNotFoundError"
        except Exception as e:                       # noqa: BLE001
            detalle = type(e).__name__
        caso("un efecto que no existe se rechaza con su nombre, no con un fallo de ffmpeg", detalle, "FileNotFoundError")
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    if sys.argv[1:] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    mezclar(sys.argv[1] if len(sys.argv) > 1 else ".")
    from sonido_repetido import avisar                # avisa si repite la canción o los efectos de las recientes; no corta
    avisar(sys.argv[1] if len(sys.argv) > 1 else ".")
