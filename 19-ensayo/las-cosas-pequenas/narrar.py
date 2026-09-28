"""Narración del ensayo con Supertonic-3, voz M5 (la voz fija del narrador del proyecto; en el procesador).
Escribe narracion.wav + tiempos.js (una frase por toma, con silencios para que la imagen respire).

    externos/voz-env/Scripts/python 19-ensayo/las-cosas-pequenas/narrar.py
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from supertonic import TTS

AQUI = Path(__file__).resolve().parent
SR = 24000
ENTRADA = 2.5                       # la primera imagen sola, antes de la primera palabra
# (id, texto, silencio después): una frase por toma
FRASES = [
    ("ventana", "Casi nada importante pasa de golpe.", 1.6),
    ("manos", "Pasa de a poco. Una línea, una página, un día.", 1.8),
    ("cafe", "Y mientras esperamos el momento grande, se nos van los pequeños.", 1.8),
    ("gorrion", "Pero los pequeños son casi todo lo que hay.", 2.0),
    ("atardecer", "Así que mira despacio.", 2.4),
    ("noche", "Lo que haces hoy, aunque parezca poco, también es tu historia.", 4.5),
]

tts = TTS(model="supertonic-3")
voz = tts.get_voice_style("M5")
piezas, seg, t = [np.zeros(int(ENTRADA * SR), np.float32)], {}, ENTRADA
for i, texto, pausa in FRASES:
    wav, _ = tts.synthesize(texto, voice_style=voz, lang="es", total_steps=16, speed=.9)
    x = np.squeeze(np.asarray(wav, np.float32))
    if tts.sample_rate != SR:
        import torch, torchaudio
        x = torchaudio.functional.resample(torch.from_numpy(x), tts.sample_rate, SR).numpy()
    seg[i] = {"inicio": round(t, 3), "dur": round(len(x) / SR, 3), "texto": texto, "quien": "narrador"}
    piezas += [x, np.zeros(int(pausa * SR), np.float32)]; t += len(x) / SR + pausa
y = np.concatenate(piezas); y = y / np.abs(y).max() * .9
sf.write(AQUI / "narracion.wav", y, SR)
datos = {"total": round(len(y) / SR, 3), "orden": [f[0] for f in FRASES], "seg": seg}
(AQUI / "tiempos.js").write_text("window.TIEMPOS = " + json.dumps(datos, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print(f"narracion.wav {datos['total']} s")
for i in datos["orden"]: print(f"  {i:9s} {seg[i]['inicio']:6.2f} +{seg[i]['dur']:.2f}")
