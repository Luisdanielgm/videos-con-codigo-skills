"""Convierte el guion de un video en narración con una voz local.

Uso:  .venv/Scripts/python herramientas/narrar.py <carpeta-del-video>

Lee <carpeta>/guion.json y escribe en la misma carpeta:
  - narracion.wav : todas las frases seguidas, con pausas.
  - tiempos.js    : window.TIEMPOS con inicio y duración de cada frase, para sincronizar la animación.

Voces: **"supertonic:M5"** (el narrador recomendado; Supertonic-3 corre en un entorno aparte,
externos/voz-env, y este script lo llama allá), Kokoro (ids como "em_alex", "ef_dora") o Piper
(nombre de archivo en modelos/, p. ej. "es_MX-ald-medium"). Cada frase se guarda en caché por su texto,
voz, velocidad y tono: cambiar una frase sólo regenera esa. Para pasar un video viejo a la voz nueva basta
con "voz": "supertonic:M5" en su guion.json.

Historias con varias voces: "personajes": {"nina": {"voz": "ef_dora", "tono": 3}} y en cada
segmento "quien": "nina". "tono" sube o baja la voz en semitonos (ffmpeg rubberband).

ElevenLabs (de pago; sólo con el OK de quien paga la cuenta): "voz": "eleven:<modelo>:<nombre de la voz en su biblioteca>",
p. ej. "eleven:eleven_v4:Mi voz de la biblioteca". Exige VIDEOS_TOPE_ELEVEN=<créditos>: si lo estimado de las
frases que faltan pasa el tope, no llama. La clave sale de ELEVENLABS_API_KEY (entorno o variable de usuario de Windows) y
nunca se imprime. Tarifa: v4 Turbo 0,072 créditos por carácter (medida en la cuenta) y v4 el doble. Cada frase queda
en la caché: se paga una sola vez.
"""
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import sys
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
MOD = RAIZ / "modelos"
CACHE = RAIZ / "render" / "voz_cache"
SR = 24000
INICIO = 0.6  # silencio antes de la primera frase (s)
FINAL = 1.5   # silencio después de la última (s)


def remuestrear(audio, sr):
    if sr == SR:
        return audio
    x = np.linspace(0, len(audio), int(len(audio) * SR / sr), endpoint=False)
    return np.interp(x, np.arange(len(audio)), audio).astype(np.float32)


def cambiar_tono(audio, semitonos):
    tmp_in, tmp_out = CACHE / "_tono_in.wav", CACHE / "_tono_out.wav"
    sf.write(tmp_in, audio, SR)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp_in), "-af",
                    f"rubberband=pitch={2 ** (semitonos / 12):.5f}", str(tmp_out)], check=True)
    return sf.read(tmp_out, dtype="float32")[0]


_voces = {}


def voz(nombre, velocidad):
    if (nombre, velocidad) not in _voces:
        _voces[(nombre, velocidad)] = Voz(nombre, velocidad)
    return _voces[(nombre, velocidad)]


_kokoro = None


# el Python del entorno de Supertonic (en Linux/macOS: externos/voz-env/bin/python); se cambia con VIDEOS_VOZ_PYTHON
VOZ_ENV = Path(os.environ.get("VIDEOS_VOZ_PYTHON", RAIZ / "externos" / "voz-env" / "Scripts" / "python.exe"))


def supertonic_lote(pedidos):
    """Corre DENTRO de externos/voz-env (donde está supertonic): [{texto, estilo, vel, salida}] → WAV a 24 kHz.
    El modelo se carga una sola vez para todas las frases."""
    from supertonic import TTS
    tts = TTS(model="supertonic-3")
    for p in pedidos:
        wav, _ = tts.synthesize(p["texto"], voice_style=tts.get_voice_style(p["estilo"]), lang="es", total_steps=16, speed=p["vel"])
        sf.write(p["salida"], remuestrear(np.squeeze(np.asarray(wav, np.float32)), tts.sample_rate), SR)


# créditos por carácter: Turbo medido en una cuenta (8.144 caracteres ≈ 590 créditos); v4, el doble
ELEVEN_TARIFA = {"eleven_v4": 0.144, "eleven_v4_turbo": 0.072}


def eleven_clave():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
        return winreg.QueryValueEx(env, "ELEVENLABS_API_KEY")[0]


def eleven_pedir(ruta, cuerpo=None, audio=False):
    pedido = urllib.request.Request("https://api.elevenlabs.io" + ruta,
                                    data=json.dumps(cuerpo).encode("utf-8") if cuerpo else None,
                                    headers={"xi-api-key": eleven_clave(), "Content-Type": "application/json",
                                             "Accept": "audio/mpeg" if audio else "application/json"})
    for intento in range(4):   # 429: exceso de pedidos; se espera y se reintenta
        try:
            with urllib.request.urlopen(pedido, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or intento == 3:
                raise RuntimeError(f"ElevenLabs {e.code}: {e.read(300).decode('utf-8', 'replace')}") from None
            time.sleep(2 * (intento + 1))


def eleven_usado():
    d = json.loads(eleven_pedir("/v1/user/subscription"))
    return d["character_count"], d["character_limit"]


def clave_de(nombre, vel, tono, texto):
    # sin tono, la clave queda igual que antes: la caché de los videos viejos sigue valiendo
    extra = f"|{tono}" if tono else ""
    return hashlib.sha1(f"{nombre}|{vel}{extra}|{texto}".encode()).hexdigest()[:16]


class Voz:
    def __init__(self, nombre, velocidad):
        global _kokoro
        self.nombre, self.velocidad = nombre, velocidad
        self.kokoro = self.piper = None
        if nombre.startswith("supertonic:"):
            self.estilo = nombre.split(":", 1)[1]
        elif nombre.startswith("eleven:"):
            _, self.modelo, self.nombre_voz = nombre.split(":", 2)
            buscar = urllib.parse.quote(self.nombre_voz.split()[0])
            voces = json.loads(eleven_pedir(f"/v2/voices?page_size=100&search={buscar}"))["voices"]
            hay = [v["voice_id"] for v in voces if v["name"] == self.nombre_voz]
            if not hay:
                raise SystemExit(f"No encuentro la voz «{self.nombre_voz}» en la biblioteca de ElevenLabs")
            self.voice_id = hay[0]
        elif (MOD / f"{nombre}.onnx").exists():
            from piper import PiperVoice
            self.piper = PiperVoice.load(str(MOD / f"{nombre}.onnx"))
            self.kokoro = None
        else:
            if _kokoro is None:
                from kokoro_onnx import Kokoro
                _kokoro = Kokoro(str(MOD / "kokoro-v1.0.int8.onnx"), str(MOD / "voices-v1.0.bin"))
            self.kokoro = _kokoro

    def decir(self, texto):
        if self.nombre.startswith("supertonic:"):
            tmp = CACHE / "_supertonic.wav"
            pedido = [{"texto": texto, "estilo": self.estilo, "vel": self.velocidad, "salida": str(tmp)}]
            subprocess.run([str(VOZ_ENV), __file__, "--supertonic"], input=json.dumps(pedido).encode("utf-8"), check=True)
            return sf.read(tmp, dtype="float32")[0]
        if self.nombre.startswith("eleven:"):
            # un nombre por proceso: con varios agentes narrando a la vez, el nombre único pisaba el audio de uno con el
            # de otro (3 frases de dos videos quedaron con voz ajena)
            mp3, wav = CACHE / f"_eleven_{os.getpid()}.mp3", CACHE / f"_eleven_{os.getpid()}.wav"
            mp3.write_bytes(eleven_pedir(f"/v1/text-to-speech/{self.voice_id}?output_format=mp3_44100_128",
                                         {"text": texto, "model_id": self.modelo, "language_code": "es"}, audio=True))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
            audio = sf.read(wav, dtype="float32")[0]
            mp3.unlink(missing_ok=True)
            wav.unlink(missing_ok=True)
            return audio
        if self.kokoro:
            audio, sr = self.kokoro.create(texto, voice=self.nombre, speed=self.velocidad, lang="es")
            return remuestrear(np.asarray(audio, dtype=np.float32), sr)
        tmp = CACHE / "_piper.wav"
        with wave.open(str(tmp), "wb") as wf:
            self.piper.synthesize_wav(texto, wf)
        audio, sr = sf.read(tmp, dtype="float32")
        return remuestrear(audio, sr)


def main(carpeta):
    carpeta = Path(carpeta).resolve()
    g = json.loads((carpeta / "guion.json").read_text(encoding="utf-8"))
    base = {"voz": g.get("voz", "em_alex"), "velocidad": g.get("velocidad", 1.0), "tono": 0}
    personajes, pausa = g.get("personajes", {}), g.get("pausa", 0.7)
    CACHE.mkdir(parents=True, exist_ok=True)
    # las frases de Supertonic que faltan se generan todas juntas (el modelo se carga una vez)
    lote = []
    for s in g["segmentos"]:
        c = {**base, **personajes.get(s.get("quien"), {})}
        if c["voz"].startswith("supertonic:") and not c["tono"]:
            arch = CACHE / f"{clave_de(c['voz'], c['velocidad'], 0, s['texto'])}.wav"
            if not arch.exists():
                lote.append({"texto": s["texto"], "estilo": c["voz"].split(":", 1)[1], "vel": c["velocidad"], "salida": str(arch)})
    if lote:
        print(f"supertonic: {len(lote)} frases nuevas")
        subprocess.run([str(VOZ_ENV), __file__, "--supertonic"], input=json.dumps(lote).encode("utf-8"), check=True)
    # ElevenLabs es de pago: se estima lo que falta y no se llama si pasa el tope
    gasto = 0.0
    for s in g["segmentos"]:
        c = {**base, **personajes.get(s.get("quien"), {})}
        if c["voz"].startswith("eleven:") and not (CACHE / f"{clave_de(c['voz'], c['velocidad'], c['tono'], s['texto'])}.wav").exists():
            gasto += len(s["texto"]) * ELEVEN_TARIFA.get(c["voz"].split(":")[1], 0.11)
    if gasto:
        tope = float(os.environ.get("VIDEOS_TOPE_ELEVEN", "0"))
        if gasto > tope:
            raise SystemExit(f"ElevenLabs: lo que falta cuesta ~{gasto:.0f} créditos y el tope es {tope:.0f} "
                             f"(VIDEOS_TOPE_ELEVEN); no se llamó")
        usado_antes = eleven_usado()[0]
        print(f"ElevenLabs: ~{gasto:.0f} créditos estimados (tope {tope:.0f}); la cuenta llevaba {usado_antes}")
    pistas, tiempos, t = [np.zeros(int(INICIO * SR), np.float32)], {}, INICIO
    for s in g["segmentos"]:
        c = {**base, **personajes.get(s.get("quien"), {})}
        nombre, vel, tono = c["voz"], c["velocidad"], c["tono"]
        archivo = CACHE / f"{clave_de(nombre, vel, tono, s['texto'])}.wav"
        if archivo.exists():
            audio, _ = sf.read(archivo, dtype="float32")
        else:
            audio = voz(nombre, vel).decir(s["texto"])
            if tono:
                audio = cambiar_tono(audio, tono)
            sf.write(archivo, audio, SR)
        dur = len(audio) / SR
        tiempos[s["id"]] = {"inicio": round(t, 3), "dur": round(dur, 3), "texto": s["texto"]}
        if "quien" in s:
            tiempos[s["id"]]["quien"] = s["quien"]
        pistas.append(audio)
        hueco = s.get("pausa", pausa)
        pistas.append(np.zeros(int(hueco * SR), np.float32))
        t += dur + hueco
        print(f"{s['id']:<12} {tiempos[s['id']]['inicio']:7.2f}s  {dur:5.2f}s")
    pistas.append(np.zeros(int(FINAL * SR), np.float32))
    total = round(t + FINAL, 3)
    sf.write(carpeta / "narracion.wav", np.concatenate(pistas), SR)
    orden = [s["id"] for s in g["segmentos"]]
    js = "window.TIEMPOS = " + json.dumps({"total": total, "orden": orden, "seg": tiempos},
                                          ensure_ascii=False, indent=1) + ";\n"
    (carpeta / "tiempos.js").write_text(js, encoding="utf-8")
    print(f"total {total:.1f}s -> narracion.wav, tiempos.js")
    if gasto:
        usado, limite = eleven_usado()   # el contador de la cuenta puede tardar en ponerse al día
        print(f"ElevenLabs: la cuenta marca {usado - usado_antes} créditos usados en esta corrida; quedan {limite - usado}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--supertonic"]:                 # llamado desde main()/decir(), ya dentro de voz-env
        supertonic_lote(json.loads(sys.stdin.buffer.read().decode("utf-8")))
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else ".")
