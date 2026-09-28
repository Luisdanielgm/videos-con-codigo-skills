"""Junta capturas en hojas de contacto (3 columnas, 12 por hoja) para revisarlas de un vistazo.

Uso:  .venv/Scripts/python herramientas/hoja.py <prefijo> [t1,t2,...]
      prefijo = nombre de las capturas sin el tiempo, p. ej. 01-html-canvas_visitante-encuentro
Escribe render/capturas/hoja_<prefijo>_<n>.jpg. Cada cuadro lleva su tiempo arriba a la izquierda.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

CAP = Path(__file__).resolve().parent.parent / "render" / "capturas"


def tiempo(f):
    return float(re.search(r"_([\d-]+)\.(jpg|png)$", f.name).group(1).replace("-", "."))


def main(prefijo, lista=None):
    fs = [f for f in CAP.glob(f"{prefijo}_*") if re.search(r"_[\d-]+\.(jpg|png)$", f.name)]
    if lista:
        quiero = {float(x) for x in lista.split(",")}
        fs = [f for f in fs if tiempo(f) in quiero]
    fs.sort(key=tiempo)
    w, h, cols = 640, 360, 3
    for n, i in enumerate(range(0, len(fs), 12)):
        sub = fs[i:i + 12]
        hoja = Image.new("RGB", (cols * w, ((len(sub) + cols - 1) // cols) * h))
        for j, f in enumerate(sub):
            im = Image.open(f).convert("RGB").resize((w, h))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 64, 20], fill="black")
            d.text((4, 4), f"{tiempo(f):g}", fill="yellow")
            hoja.paste(im, ((j % cols) * w, (j // cols) * h))
        out = CAP / f"hoja_{prefijo}_{n}.jpg"
        hoja.save(out, quality=85)
        print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
