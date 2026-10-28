"""Junta capturas en hojas de contacto (3 columnas, 12 por hoja; las verticales en 6 columnas) para revisarlas de un vistazo.

Uso:  .venv/Scripts/python herramientas/hoja.py <prefijo> [t1,t2,...]
      prefijo = nombre de las capturas sin el tiempo, p. ej. 01-html-canvas_visitante-encuentro
Escribe render/capturas/hoja_<prefijo>_<n>.jpg. Cada cuadro lleva su tiempo arriba a la izquierda.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

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
    if fs and (lambda s: s[1] > s[0])(Image.open(fs[0]).size):
        w, h, cols = 360, 640, 6          # vertical (reels): celdas de 360×640 en 2 filas de 6, no achicadas a 202×360
    for n, i in enumerate(range(0, len(fs), 12)):
        sub = fs[i:i + 12]
        hoja = Image.new("RGB", (cols * w, ((len(sub) + cols - 1) // cols) * h))
        for j, f in enumerate(sub):
            # conserva la proporción (un video vertical no se estira a 16:9); los 16:9 quedan igual
            im = Image.new("RGB", (w, h), (24, 24, 24))
            c = ImageOps.contain(Image.open(f).convert("RGB"), (w, h))
            im.paste(c, ((w - c.width) // 2, (h - c.height) // 2))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 64, 20], fill="black")
            d.text((4, 4), f"{tiempo(f):g}", fill="yellow")
            hoja.paste(im, ((j % cols) * w, (j // cols) * h))
        out = CAP / f"hoja_{prefijo}_{n}.jpg"
        hoja.save(out, quality=85)
        print(out)


def probar():
    """Regla: una guardia nueva se rompe a propósito antes de creerle. Capturas falsas de un color liso cada una, en una carpeta
    temporal: se mira de qué color es cada celda de la hoja (orden por tiempo), cuántas hojas salen, su tamaño y el filtro."""
    import tempfile
    global CAP
    guardado = CAP
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    def color(hoja, col, fila, w, h):
        return hoja.getpixel((col * w + w // 2, fila * h + h // 2))

    try:
        with tempfile.TemporaryDirectory() as tmp:
            CAP = Path(tmp)
            # nombres con tiempos que ordenados como texto saldrían mal: «_10» antes que «_2»
            for nombre, rgb in {"h_2": (200, 0, 0), "h_10": (0, 200, 0), "h_1-5": (0, 0, 200), "otro_3": (200, 200, 0)}.items():
                Image.new("RGB", (320, 180), rgb).save(CAP / f"{nombre}.png")
            main("h")
            hoja = Image.open(CAP / "hoja_h_0.jpg")
            caso("tamaño de la hoja horizontal: 3 columnas, 1 fila", hoja.size, (3 * 640, 360))
            caso("orden por tiempo (1,5 · 2 · 10), no por texto", [color(hoja, c, 0, 640, 360)[i] > 150 for c, i in ((0, 2), (1, 0), (2, 1))], [True] * 3)
            caso("las capturas de otro prefijo no entran", color(hoja, 2, 0, 640, 360)[0] < 100, True)
            for f in CAP.glob("hoja_*"):
                f.unlink()
            main("h", "2,10")
            caso("la lista de tiempos deja sólo esos", Image.open(CAP / "hoja_h_0.jpg").size, (3 * 640, 360))
            hoja = Image.open(CAP / "hoja_h_0.jpg")
            caso("con la lista, la primera celda es la de 2 s", color(hoja, 0, 0, 640, 360)[0] > 150, True)
            for f in CAP.glob("*"):
                f.unlink()
            for i in range(13):                                   # 13 capturas: 12 en la primera hoja y 1 en la segunda
                Image.new("RGB", (320, 180), (10 * i, 50, 50)).save(CAP / f"m_{i + 1}.png")
            main("m")
            caso("13 capturas: dos hojas", sorted(f.name for f in CAP.glob("hoja_m_*")), ["hoja_m_0.jpg", "hoja_m_1.jpg"])
            caso("la hoja llena trae 4 filas de 3", Image.open(CAP / "hoja_m_0.jpg").size, (3 * 640, 4 * 360))
            for f in CAP.glob("*"):
                f.unlink()
            for f in CAP.glob("*"):
                f.unlink()
            Image.new("RGB", (320, 180), (120, 120, 120)).save(CAP / "a_1.png")        # una vertical dentro de una hoja horizontal:
            Image.new("RGB", (90, 160), (0, 0, 255)).save(CAP / "a_2.png")             # conserva su proporción y deja franjas, no se recorta
            main("a")
            hoja = Image.open(CAP / "hoja_a_0.jpg")
            caso("una captura de otra proporción deja franjas (no se recorta)", max(hoja.getpixel((640 + 5, 180))) < 60, True)
            for f in CAP.glob("*"):
                f.unlink()
            for i in range(3):                                    # verticales (reels): 6 columnas de 360×640, sin estirarse
                Image.new("RGB", (180, 320), (0, 40, 200)).save(CAP / f"v_{i + 1}.png")
            main("v")
            hoja = Image.open(CAP / "hoja_v_0.jpg")
            caso("verticales: 6 columnas de 360×640", hoja.size, (6 * 360, 640))
            caso("la vertical llena su celda (no se estira a 16:9)", color(hoja, 0, 0, 360, 640)[2] > 150 and hoja.getpixel((5, 320))[2] > 150, True)
    finally:
        CAP = guardado
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    if sys.argv[1:] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
