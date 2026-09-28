"""Baja el material de archivo del documental desde Wikimedia Commons (y la población de Our World in Data)
a recursos/archivo/revolucion-industrial/ — `recursos/` está fuera de git (puede ser un enlace a otro disco).
Guarda también creditos.json (autor y licencia de cada archivo) para los créditos del final.

    .venv/Scripts/python 17-archivo/revolucion-industrial/bajar.py
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DEST = RAIZ / "recursos" / "archivo" / "revolucion-industrial"
UA = {"User-Agent": "videos-con-codigo/1.0 (uso personal)"}

# nombre local → título en Commons
ARCHIVOS = {
    "sortie-usine-1895.webm": "La Sortie de l'Usine Lumière à Lyon I 1895.webm",
    "train-ciotat-1897.webm": "L'Arrivée d'un train en gare de La Ciotat (1897).webm",
    "coalbrookdale-1801.jpg": "Philipp Jakob Loutherbourg d. J. 002.jpg",
    "telares-1835.jpg": "Powerloom weaving in 1835.jpg",
    "manchester-1852.jpg": "Wyld, William - Manchester from Kersal Moor, with rustic figures and goats - Google Art Project.jpg",
    "trenes-1830.png": "Trains upon the Liverpool and Manchester Railway about the year 1830.png",
    "hilandera-1909.jpg": "Lewis Hine, Spinner in Globe Cotton Mill, Augusta, Georgia, 1909.jpg",
    "breaker-boys.jpg": "Breaker Boys 1.jpg",
    "crystal-palace-1851.jpg": "Crystal Palace - interior.jpg",
}   # (se bajó también una foto moderna de la máquina de Watt en un museo; no quedó: se veía de hoy)
OWID = "https://ourworldindata.org/grapher/population.csv?v=1&csvType=filtered&useColumnShortNames=true&country=~GBR"


def api(titulo):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": "File:" + titulo, "prop": "imageinfo",
                                "iiprop": "url|size|extmetadata", "iiextmetadatafilter": "LicenseShortName|Artist|DateTimeOriginal"})
    with urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers=UA)) as r:
        pagina = next(iter(json.load(r)["query"]["pages"].values()))
    if "imageinfo" not in pagina: raise SystemExit(f"no está en Commons: {titulo}")
    return pagina["imageinfo"][0]


def bajar(url, destino):
    if destino.exists(): print("ya está", destino.name); return
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(destino, "wb") as f:
        while b := r.read(1 << 20): f.write(b)
    print("bajado", destino.name, f"{destino.stat().st_size / 2**20:.1f} MB")


DEST.mkdir(parents=True, exist_ok=True)
creditos = {}
for local, titulo in ARCHIVOS.items():
    ii = api(titulo); m = ii["extmetadata"]
    limpio = lambda k: re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", "")).strip()
    creditos[local] = {"titulo": titulo, "autor": limpio("Artist"), "fecha": limpio("DateTimeOriginal"),
                       "licencia": limpio("LicenseShortName"), "pagina": "https://commons.wikimedia.org/wiki/File:" + titulo.replace(" ", "_")}
    bajar(ii["url"], DEST / local)
bajar(OWID, DEST / "poblacion-reino-unido.csv")
creditos["poblacion-reino-unido.csv"] = {"titulo": "Population (Gapminder, HYDE y UN)", "autor": "Our World in Data", "licencia": "CC BY 4.0", "pagina": OWID}
(DEST / "creditos.json").write_text(json.dumps(creditos, ensure_ascii=False, indent=1), encoding="utf-8")
print("creditos.json listo")
