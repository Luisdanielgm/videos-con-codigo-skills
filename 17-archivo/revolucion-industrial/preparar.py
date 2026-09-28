"""Prepara el documental a partir del archivo ya bajado (bajar.py):

- Recorta los tramos de las películas de los Lumière y los recodifica **todo intra** (`-g 1`, cada cuadro
  es clave): así el navegador salta al cuadro exacto y la página espera `seeked` antes de dibujarlo
  (método de @twoclipping). Van a recursos/.../clips/ (fuera de git).
- Saca de la tabla de Our World in Data la población del Reino Unido de 1750 a 1900 → datos.js (en git).

    .venv/Scripts/python 17-archivo/revolucion-industrial/preparar.py
    .venv/Scripts/python herramientas/musica.py 17-archivo/revolucion-industrial
"""
import csv
import json
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ARCH = AQUI.parents[1] / "recursos" / "archivo" / "revolucion-industrial"
CLIPS = ARCH / "clips"
# nombre → (película, desde s, dura s)
TRAMOS = {
    "tren": ("train-ciotat-1897.webm", 7.8, 6.0),        # el tren llega y pasa frente a la cámara (desde 5,5 no alcanzaba a llegar)
    "fabrica": ("sortie-usine-1895.webm", 0.0, 6.5),     # se abren las puertas y salen los obreros
}

CLIPS.mkdir(exist_ok=True)
for nombre, (peli, desde, dura) in TRAMOS.items():
    salida = CLIPS / f"{nombre}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(desde), "-t", str(dura), "-i", str(ARCH / peli),
                    "-vf", "scale=1440:-2", "-an", "-c:v", "libx264", "-g", "1", "-crf", "18", "-preset", "fast",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(salida)], check=True)
    print("clip", salida.name, f"{salida.stat().st_size / 2**20:.1f} MB")

# Desde 1820: antes la serie empalma fuentes (sólo Gran Bretaña hasta ~1810, con Irlanda desde ~1816) y
# pega un salto falso de 12 a 17 millones. De 1820 a 1900 es una sola serie (Reino Unido con Irlanda).
with open(ARCH / "poblacion-reino-unido.csv", encoding="utf-8") as f:
    serie = [(int(r["year"]), int(float(r["population_historical"]))) for r in csv.DictReader(f) if 1820 <= int(r["year"]) <= 1900]
datos = {"poblacion": {"fuente": "Our World in Data (Gapminder, HYDE, ONU), CC BY 4.0", "pais": "Reino Unido (con Irlanda)", "serie": serie}}
(AQUI / "datos.js").write_text("window.DATOS = " + json.dumps(datos, ensure_ascii=False) + ";\n", encoding="utf-8")
print("datos.js:", len(serie), "años", serie[0], serie[-1])
