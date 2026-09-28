"""Mezcla del ensayo: narración (Supertonic M5) + «Vastness» (Andrew Ev, Mixkit; licencia gratuita de música de
Mixkit) que baja sola cuando habla el narrador + ambiente real bajo en cada toma (banco recursos/efectos: Mixkit
y Kenney), con la mezcla compartida → mezcla.json + mezcla.wav.

    .venv/Scripts/python 19-ensayo/las-cosas-pequenas/mezclar.py

Falta en el banco: un pájaro para la toma del gorrión (va la brisa de los árboles mientras tanto).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
TI = json.loads(re.search(r"=\s*(\{.*\})\s*;", (AQUI / "tiempos.js").read_text(encoding="utf-8"), re.S).group(1))
ini = lambda i: 0 if i == "ventana" else TI["seg"][i]["inicio"] - .9        # como index.html: la toma empieza antes de su frase

ef = []
def e(archivo, en, db): ef.append({"archivo": archivo, "en": round(max(0, en), 3), "db": db})
e("viento/brisa-arboles.wav", ini("ventana"), -30)                    # ventana: el aire de afuera
for k in range(3): e("escritura/pluma-papel.wav", ini("manos") + .6 + k * 1.5, -22)   # manos que escriben
e("papel/hoja-pasar.wav", ini("cafe") + 1.2, -20)                      # el escritorio
e("viento/brisa-arboles.wav", ini("gorrion"), -28)                     # afuera (sin pájaro en el banco)
e("viento/brisa-arboles.wav", ini("atardecer"), -31)

mezcla = {
    "cancion": {"archivo": "recursos/musica/mixkit-759-vastness.mp3", "desde": .37, "volumen": .55, "entrada": 2, "salida": 4},
    "voz": "narracion.wav", "efectos": ef, "lufs": -14,
}
(AQUI / "mezcla.json").write_text(json.dumps(mezcla, ensure_ascii=False, indent=1), encoding="utf-8")
subprocess.run([sys.executable, str(RAIZ / "herramientas" / "mezclar.py"), str(AQUI)], check=True)
