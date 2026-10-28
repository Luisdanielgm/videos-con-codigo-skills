"""Instante de cada palabra de una voz (técnica 27: subtítulos palabra por palabra y palabras grandes en su sílaba).

    <venv-vision>/Scripts/python herramientas/palabras.py <carpeta> [audio]
    <venv-vision>/Scripts/python herramientas/palabras.py --probar

Transcribe `<carpeta>/narracion.wav` (u otro audio, p. ej. el de un clip de alguien hablando) con faster-whisper
(modelo «small», local, MIT; en externos/hf-cache) y escribe `<carpeta>/palabras.js`:
`window.PALABRAS = [{t, f, p, seg}]` (inicio y fin en s, la palabra y el id del segmento del guion).

Si hay `guion.json`, el texto manda: whisper confunde nombres propios («Uffy» por *Up*, «casa de cd» por «tasa fija»,
medido), así que las palabras del guion se alinean con las oídas (difflib) y toman su tiempo; las que no
calzan se reparten entre sus vecinas. Sin guion, quedan las palabras oídas.

Corre en `venv-vision` (faster-whisper, fuera del `.venv`). El audio se decodifica con ffmpeg: el PyAV de faster-whisper
1.2.1 no acepta `metadata_errors` con el av instalado.
"""
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

SR = 16000


def plano(p):
    return "".join(c for c in unicodedata.normalize("NFD", p.lower()) if unicodedata.category(c) != "Mn" and c.isalnum())


def oir(audio):
    import numpy as np
    from faster_whisper import WhisperModel
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    m = WhisperModel("small", device="cpu", compute_type="int8")
    # sin vad_filter: con él, la alineación de palabras se cae en una voz con pausas cortas (IndexError en
    # find_alignment, con la narración de un reel)
    segs, _ = m.transcribe(np.frombuffer(crudo, np.float32), language="es", word_timestamps=True)
    return [{"t": round(w.start, 3), "f": round(w.end, 3), "p": w.word.strip()} for s in segs for w in s.words]


def alinear(oidas, guion):
    """Palabras del guion con el tiempo de la oída que les corresponde; las sueltas se interpolan."""
    dichas = [(w, s["id"]) for s in guion["segmentos"] for w in s["texto"].split()]
    a, b = [plano(w) for w, _ in dichas], [plano(o["p"]) for o in oidas]
    tiempo = [None] * len(dichas)
    for blq in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(blq.size):
            o = oidas[blq.b + k]
            tiempo[blq.a + k] = (o["t"], o["f"])
    salida = []
    for i, (w, seg) in enumerate(dichas):
        if tiempo[i] is None:   # entre la anterior con tiempo y la siguiente con tiempo
            ant = next((tiempo[j][1] for j in range(i - 1, -1, -1) if tiempo[j]), 0.0)
            j = next((j for j in range(i + 1, len(dichas)) if tiempo[j]), None)
            sig = tiempo[j][0] if j is not None else ant + 0.4 * (len(dichas) - i)
            huecos = (j if j is not None else len(dichas)) - next((k for k in range(i - 1, -1, -1) if tiempo[k]), -1) - 1
            pos = i - next((k for k in range(i - 1, -1, -1) if tiempo[k]), -1) - 1
            paso = (sig - ant) / max(1, huecos)
            tiempo[i] = (round(ant + pos * paso, 3), round(ant + (pos + 1) * paso, 3))
        salida.append({"t": tiempo[i][0], "f": tiempo[i][1], "p": w, "seg": seg})
    return salida


def acotar(palabras, tiempos):
    """Ninguna palabra empieza antes que su segmento (narrar.py sabe dónde empieza cada frase; whisper adelanta la
    primera palabra hasta 0,6 s, medido). Las que quedan pisadas se corren en fila."""
    ini = {k: v["inicio"] for k, v in tiempos["seg"].items()}
    previo = 0.0
    for w in palabras:
        t = max(w["t"], ini.get(w.get("seg"), 0.0), previo)
        w["f"] = round(max(w["f"], t + 0.08), 3)
        w["t"] = round(t, 3)
        previo = t
    return palabras


def escribir(carpeta, palabras):
    (Path(carpeta) / "palabras.js").write_text("window.PALABRAS = " + json.dumps(palabras, ensure_ascii=False) + ";\n",
                                               encoding="utf-8")


def probar():
    """La alineación sin modelo: palabras oídas con errores, una de más y una que falta."""
    guion = {"segmentos": [{"id": "a", "texto": "Portallaveros de Up"}, {"id": "b", "texto": "doce dólares a tasa fija"}]}
    oidas = [{"t": 0.0, "f": 0.5, "p": "Portallaveros"}, {"t": 0.5, "f": 0.6, "p": "de"}, {"t": 0.6, "f": 0.9, "p": "Uffy"},
             {"t": 1.0, "f": 1.3, "p": "doce"}, {"t": 1.3, "f": 1.7, "p": "dólares"}, {"t": 1.7, "f": 1.8, "p": "a"},
             {"t": 1.8, "f": 2.1, "p": "casa"}, {"t": 2.1, "f": 2.4, "p": "de"}, {"t": 2.4, "f": 2.6, "p": "cd"}]
    r = alinear(oidas, guion)
    casos = [
        ("las palabras son las del guion", [w["p"] for w in r] == "Portallaveros de Up doce dólares a tasa fija".split()),
        ("una palabra que calza toma su tiempo", r[3]["t"] == 1.0 and r[4]["f"] == 1.7),
        ("la mal oída queda entre sus vecinas", 0.6 <= r[2]["t"] < r[2]["f"] <= 1.0),
        ("los tiempos no retroceden", all(r[i]["t"] <= r[i + 1]["t"] for i in range(len(r) - 1))),
        ("cada palabra lleva su segmento", [w["seg"] for w in r] == ["a"] * 3 + ["b"] * 5),
    ]
    c = acotar([dict(w) for w in r], {"seg": {"a": {"inicio": 0.3}, "b": {"inicio": 1.2}}})
    casos += [("ninguna palabra antes que su segmento", c[0]["t"] == 0.3 and c[3]["t"] == 1.2),
              ("acotar no desordena", all(c[i]["t"] <= c[i + 1]["t"] for i in range(len(c) - 1)))]
    ok = True
    for nombre, paso in casos:
        print(("ok    " if paso else "FALLA ") + nombre)
        ok &= paso
    print("palabras:", "todo ok" if ok else "HAY FALLAS")
    return ok


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    carpeta = Path(sys.argv[1])
    audio = Path(sys.argv[2]) if len(sys.argv) > 2 else carpeta / "narracion.wav"
    oidas = oir(audio)
    g = carpeta / "guion.json"
    palabras = alinear(oidas, json.loads(g.read_text(encoding="utf-8"))) if g.exists() else oidas
    tj = carpeta / "tiempos.js"
    if g.exists() and tj.exists() and audio == carpeta / "narracion.wav":
        texto = tj.read_text(encoding="utf-8")
        palabras = acotar(palabras, json.loads(texto[texto.index("{"):texto.rindex("}") + 1]))
    escribir(carpeta, palabras)
    calzan = sum(1 for o in oidas if plano(o["p"]) in {plano(w["p"]) for w in palabras})
    print(f"{len(oidas)} palabras oídas, {len(palabras)} escritas en palabras.js ({calzan} calzan con el guion)")
    print(" ".join(f"{w['p']}@{w['t']:g}" for w in palabras))
