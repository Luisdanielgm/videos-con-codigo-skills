"""Pista de la épica: «Drawing the Sky» (Eugenio Mininni, Mixkit; licencia gratuita de música de Mixkit) + efectos
REALES del banco (recursos/efectos: Kenney CC0 y Mixkit) en cada evento del dibujo, con la mezcla compartida.
(En la primera versión los efectos eran sintetizados con musica.py: efectos/musica.json.)

herramientas/cancion.py: 99,4 BPM, primer tiempo a 0,226 s; se recorta desde el compás 10: la entrada al espacio
(pulso 60 = compás 15 del video) cae en el compás 25 de la canción, su parte más fuerte.

    .venv/Scripts/python 18-epica-lineal/historia-del-vuelo/mezclar.py        # → mezcla.json + mezcla.wav + pulsos.js
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
BPM, PRIMER_TIEMPO, COMPAS_INICIO = 99.4, .226, 10
T = lambda p: .2 + p * 60 / BPM                               # el pulso p del video, en segundos (igual que index.html)
LARGO = T(98) + 1.5

ef = []
def e(archivo, en, db, alinear=False): ef.append({"archivo": archivo, "en": round(en, 3), "db": db, **({"alinear": "pico"} if alinear else {})})

# pluma sobre el papel mientras se traza cada dibujo (más al principio, cuando la línea corre)
trazos = [(T(.6), T(9)), *[(T(12 * i - .6), T(12 * i + 8.5)) for i in range(1, 4)], (T(46.8), T(56))]
for a, b in trazos:
    t, k = a, 0
    while t < a + (b - a) * .7:
        e("escritura/pluma-papel.wav" if k % 2 == 0 else "escritura/lapiz-corto.wav", t, -15 - k * .6); t += 1.35; k += 1
for i in range(1, 5): e("papel/hoja-pasar.wav", T(12 * i - 1.6), -12)           # la cámara pasa al dibujo siguiente
e("transicion/whoosh-rapido.wav", T(43.8), -10, True)                            # el Flyer despega
e("impacto/impacto-epico.wav", T(59.9), -5, True)                                # la tinta inunda: el espacio
e("impacto/latido-grave.wav", T(65), -7)                                         # enciende el Saturno V
e("transicion/whoosh-cine-rapido.wav", T(66.4), -9, True)                        # despega
for i in range(18): e("exito/kenney-glass-001.wav", T(75 + i * .22) + .15, -20)   # cada espejo del Webb se enciende
e("exito/campana-logro.wav", T(85.2), -13, True)                                  # las estrellas dibujan a Ícaro
e("transicion/whoosh-rapido.wav", T(90.3), -9, True)                             # la noche se abre al papel
e("impacto/kenney-soft-heavy-000.wav", T(90.9), -12)                             # entra el título final

mezcla = {
    "cancion": {"archivo": "recursos/musica/mixkit-272-drawing-the-sky.mp3",
                "desde": round(PRIMER_TIEMPO + COMPAS_INICIO * 4 * 60 / BPM - .2, 3), "volumen": .9, "entrada": 1.2, "salida": 3},
    "efectos": ef, "duracion": round(LARGO, 3), "lufs": -14,
}
(AQUI / "mezcla.json").write_text(json.dumps(mezcla, ensure_ascii=False, indent=1), encoding="utf-8")
shutil.copy(AQUI / "efectos" / "pulsos.js", AQUI / "pulsos.js")
subprocess.run([sys.executable, str(RAIZ / "herramientas" / "mezclar.py"), str(AQUI)], check=True)
