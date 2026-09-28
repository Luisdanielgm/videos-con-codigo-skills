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
  "lufs": -14
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
    filtros.append(f"{''.join(pistas)}amix=inputs={len(pistas)}:normalize=0:duration=longest,atrim=0:{total:.3f},"
                   f"loudnorm=I={lufs}:TP=-2:LRA=11[out]")
    salida = carpeta / "mezcla.wav"
    grafo = carpeta / "mezcla_filtro.txt"             # en un archivo: con cientos de efectos no entra en la línea de comandos
    grafo.write_text(";\n".join(filtros), encoding="utf-8")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-/filter_complex", str(grafo), "-map", "[out]",
                        "-ar", "44100", "-ac", "2", str(salida)], check=True)
    finally:
        grafo.unlink(missing_ok=True)
    print(f"mezcla.wav {total:.1f} s · {len(pistas)} pistas ({len(efectos)} efectos) · {lufs} LUFS")


if __name__ == "__main__":
    mezclar(sys.argv[1] if len(sys.argv) > 1 else ".")
