"""Recorta una imagen generada sobre verde croma y la vuelve sticker (técnica 16, collage).

Uso:  .venv/Scripts/python herramientas/recortar.py <entrada.png> <salida.png> [--borde 14]

- Quita el verde (#00FF00) con un borde suave y le saca el reflejo verde a los bordes del recorte.
- Borra las motas sueltas que deja el generador: sólo quedan las piezas grandes.
- Agrega el borde blanco de sticker (--borde px, 0 = sin borde) y recorta al contenido.
La sombra y el papel no van acá: los pone la animación, para poder moverlos.
"""
import argparse

import numpy as np
from PIL import Image
from scipy import ndimage


def recortar(entrada, salida, borde=14):
    x = np.asarray(Image.open(entrada).convert("RGB")).astype(np.float32) / 255
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    verde = g - np.maximum(r, b)                                    # cuánto más verde que lo demás
    alfa = np.clip((.32 - verde) / (.32 - .12), 0, 1)
    # motas: se quedan las piezas de al menos 2 % de la más grande
    etiquetas, n = ndimage.label(alfa > .5)
    if n:
        tam = ndimage.sum(np.ones_like(alfa), etiquetas, range(1, n + 1))
        grandes = np.isin(etiquetas, 1 + np.flatnonzero(tam >= .02 * tam.max()))
        grandes = ndimage.binary_fill_holes(ndimage.binary_dilation(grandes, iterations=2))
        alfa *= grandes
    # reflejo verde en el borde: el verde no pasa del mayor de rojo y azul
    g2 = np.where(alfa < 1, np.minimum(g, np.maximum(r, b) + .03), g)
    rgb = np.stack([r, g2, b], -1)
    if borde:
        dist = ndimage.distance_transform_edt(alfa < .5)            # distancia al recorte
        blanco = np.clip(borde + .5 - dist, 0, 1)                    # anillo blanco con borde suave
        fondo = np.array([.99, .98, .95], np.float32)                # blanco de papel, no blanco puro
        rgb = rgb * alfa[..., None] + fondo * (1 - alfa[..., None])
        alfa = np.maximum(alfa, blanco)
    ys, xs = np.nonzero(alfa > .02)
    m = borde + 4
    y0, y1, x0, x1 = max(0, ys.min() - m), ys.max() + m, max(0, xs.min() - m), xs.max() + m
    out = np.dstack([rgb, alfa])[y0:y1, x0:x1]
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA").save(salida)
    print("listo", salida, f"{out.shape[1]}x{out.shape[0]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("salida"); ap.add_argument("--borde", type=int, default=14)
    a = ap.parse_args()
    recortar(a.entrada, a.salida, a.borde)
