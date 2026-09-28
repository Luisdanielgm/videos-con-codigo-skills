"""Genera la misma frase con cada voz local para compararlas de oído."""
import wave
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro
from piper import PiperVoice

RAIZ = Path(__file__).resolve().parent.parent
MOD = RAIZ / "modelos"
OUT = RAIZ / "render" / "muestras"
OUT.mkdir(parents=True, exist_ok=True)

FRASE = ("Una red neuronal es un programa que aprende con ejemplos. "
         "Cada peso es como una perilla de volumen: dice cuánto importa cada entrada. "
         "Aquí la neurona se enciende un setenta y uno por ciento.")

kokoro = Kokoro(str(MOD / "kokoro-v1.0.int8.onnx"), str(MOD / "voices-v1.0.bin"))
for voz in ["ef_dora", "em_alex", "em_santa"]:
    audio, sr = kokoro.create(FRASE, voice=voz, speed=1.0, lang="es")
    sf.write(OUT / f"kokoro_{voz}.wav", audio, sr)
    print("ok kokoro", voz)

for nombre in ["es_MX-ald-medium", "es_MX-claude-high"]:
    voz = PiperVoice.load(str(MOD / f"{nombre}.onnx"))
    with wave.open(str(OUT / f"piper_{nombre}.wav"), "wb") as wf:
        voz.synthesize_wav(FRASE, wf)
    print("ok piper", nombre)
