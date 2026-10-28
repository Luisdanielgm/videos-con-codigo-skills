"""Audita la voz de un video: transcribe CADA frase de narracion.wav (ElevenLabs Scribe) y la compara con su texto del guion.

    .venv/Scripts/python herramientas/auditar_voz.py <carpeta del video> [id id ...]     (sin ids: todas las frases)

Por qué existe: la voz generada a veces dice otra cosa (p. ej. «Ahora, la preeclampsia cefalosporinas» en vez de «severa»;
la caché compartida dejó voz ajena en 3 frases). Medir la duración por letra no lo ve; oírlo sí. Aquí lo «oye» un
transcriptor. Es una llamada de pago de ElevenLabs (por duración del audio): se imprime lo estimado antes de llamar y no
corre si pasa de VIDEOS_TOPE_STT minutos (6 por omisión). Clave: variable de entorno ELEVENLABS_API_KEY.

Salida: por frase, la similitud (0–1) entre lo transcrito y lo escrito, tras normalizar (minúsculas, sin acentos ni
puntuación, números en cifras y en palabras se parecen poco: por eso 0,75 es el umbral, no 0,95). Las que quedan por
debajo se imprimen con las dos versiones; sale con código 1 si hay alguna. Guarda auditoria_voz.json en la carpeta.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import soundfile as sf

UMBRAL = 0.75
SR_STT = 16000


def normal(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def transcribir(wav):
    r = subprocess.run(["curl", "-s", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text",
                        "-H", f"xi-api-key: {os.environ['ELEVENLABS_API_KEY']}", "-F", "model_id=scribe_v1",
                        "-F", "language_code=es", "-F", f"file=@{wav}"], capture_output=True, check=True)
    d = json.loads(r.stdout.decode("utf-8"))
    if "text" not in d:
        raise SystemExit(f"Scribe respondió: {d}")
    return d["text"]


def main(carpeta, ids):
    carpeta = Path(carpeta).resolve()
    T = json.loads((carpeta / "tiempos.json").read_text(encoding="utf-8"))
    x, sr = sf.read(carpeta / "narracion.wav", dtype="float32")
    orden = ids or T["orden"]
    minutos = sum(T["seg"][i]["dur"] for i in orden) / 60
    tope = float(os.environ.get("VIDEOS_TOPE_STT", "6"))
    print(f"{carpeta.name}: {len(orden)} frases, {minutos:.1f} min de audio a transcribir (tope {tope:g} min)")
    if minutos > tope:
        raise SystemExit("pasa del tope; súbelo con VIDEOS_TOPE_STT si de verdad hace falta")
    tmp = Path(tempfile.mkdtemp(prefix="auditar_voz_"))

    def una(i):
        s = T["seg"][i]
        a, b = max(0, int((s["inicio"] - 0.15) * sr)), min(len(x), int((s["inicio"] + s["dur"] + 0.15) * sr))
        wav = tmp / f"{i}.wav"
        sf.write(wav, x[a:b], sr)
        out = tmp / f"{i}_16k.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR_STT), str(out)], check=True)
        oido = transcribir(out)
        sim = difflib.SequenceMatcher(None, normal(oido), normal(s["texto"])).ratio()
        return i, round(sim, 2), oido, s["texto"]

    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(una, orden))
    malas = [r for r in res if r[1] < UMBRAL]
    for i, sim, oido, texto in res:
        print(f"{'FALLA' if sim < UMBRAL else 'ok   '} {sim:4.2f} {i}")
    for i, sim, oido, texto in malas:
        print(f"\n  {i}\n    escrito: {texto}\n    se oye:  {oido}")
    print(f"\nTOTAL: {len(res)} frases · {len(malas)} FALLA")
    if not ids:         # el informe completo sólo se guarda cuando se auditó todo el video
        (carpeta / "auditoria_voz.json").write_text(json.dumps(
            [{"id": i, "similitud": s, "oido": o, "texto": t} for i, s, o, t in res], ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if malas else 0)


def probar():
    """Regla: una guardia nueva se rompe a propósito antes de creerle. NO llama a ElevenLabs: `transcribir` se cambia por un transcriptor
    falso que responde según la frase (a: igual con otra puntuación y sin acentos; b: otra cosa, como el «cefalosporinas» de arriba;
    c: igual), y se cuenta cuántas veces se le llama. Se miran el código de salida, lo impreso, el tope y el informe guardado."""
    import contextlib
    import io
    import numpy as np
    g = globals()
    guardado, tope_antes = g["transcribir"], os.environ.pop("VIDEOS_TOPE_STT", None)
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    textos = {"a": "Ahora, la preeclampsia severa.", "b": "Se indica un antibiótico.", "c": "La presión sube."}
    oido = {"a": "ahora la preeclampsia severa", "b": "se indica una cefalosporinas", "c": "La presión sube."}
    llamadas = []

    def falso(wav):
        llamadas.append(Path(wav).name)
        return oido[Path(wav).name.split("_")[0]]

    def correr(carpeta, ids=()):
        llamadas.clear()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                main(carpeta, list(ids)); codigo = 0
            except SystemExit as e:
                codigo = e.code if isinstance(e.code, int) else str(e.code)
        return codigo, buf.getvalue()

    try:
        g["transcribir"] = falso
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            sf.write(tmp / "narracion.wav", np.zeros(24000 * 9, np.float32), 24000)
            seg = {i: {"inicio": 1 + 3 * k, "dur": 2.0, "texto": textos[i]} for k, i in enumerate("abc")}
            (tmp / "tiempos.json").write_text(json.dumps({"orden": list("abc"), "seg": seg}), encoding="utf-8")
            caso("normal(): sin mayúsculas, acentos ni signos", normal("¡Ácido, ÁCIDO!  Dos."), "acido acido dos")
            codigo, salida = correr(tmp)
            caso("una frase con otra cosa: código 1", codigo, 1)
            caso("la lista marca FALLA sólo en esa (b)", [l.split()[0] + " " + l.split()[-1] for l in salida.splitlines() if l[:5] in ("FALLA", "ok   ")],
                 ["ok a", "FALLA b", "ok c"])
            caso("imprime lo escrito y lo que se oye de la mala", ("escrito: Se indica un antibiótico." in salida, "se oye:  se indica una cefalosporinas" in salida), (True, True))
            caso("sin ids transcribe las tres y guarda auditoria_voz.json", (len(llamadas), len(json.loads((tmp / "auditoria_voz.json").read_text(encoding="utf-8")))), (3, 3))
            (tmp / "auditoria_voz.json").unlink()
            codigo, _ = correr(tmp, ["a", "c"])
            caso("con ids sólo transcribe esas, sale 0 y no guarda informe", (sorted(n.split("_")[0] for n in llamadas), codigo, (tmp / "auditoria_voz.json").exists()), (["a", "c"], 0, False))
            os.environ["VIDEOS_TOPE_STT"] = "0.05"          # 3 s de tope; las 3 frases suman 6 s
            codigo, _ = correr(tmp)
            caso("pasar del tope de minutos corta antes de llamar al transcriptor", (llamadas, "tope" in str(codigo)), ([], True))
            os.environ["VIDEOS_TOPE_STT"] = "0.05"
            codigo, _ = correr(tmp, ["a"])
            caso("una sola frase (2 s) cabe en ese tope", (codigo, len(llamadas)), (0, 1))
    finally:
        g["transcribir"] = guardado
        os.environ.pop("VIDEOS_TOPE_STT", None)
        if tope_antes is not None:
            os.environ["VIDEOS_TOPE_STT"] = tope_antes
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    if sys.argv[1:] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    main(sys.argv[1], sys.argv[2:])
