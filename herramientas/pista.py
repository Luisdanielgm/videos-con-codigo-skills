"""Pasa un video de música calculada (musica.json + musica.py) a una CANCIÓN REAL con efectos REALES, sin tocar
su animación: la grilla de pulsos pasa a ser la de la canción y cada evento de musica.json («whoosh» en el pulso
4, «clic» en el 12…) se vuelve un efecto del banco (recursos/efectos) en ese mismo pulso.

    .venv/Scripts/python herramientas/pista.py <carpeta> <cancion.mp3> [--golpe P] [--compas N] [--energia]

- La canción se analiza con cancion.py (BPM, primer tiempo, energía por compás). El tramo se elige para que la
  mayor SUBIDA de energía de la canción (la energía del compás contra la del anterior) caiga en el pulso del golpe
  del video (`--golpe`; si no, el último «impacto» de musica.json). `--compas N` fija a mano el compás de la
  canción que cae en el pulso 0.
- Escribe pulsos.js (bpm de la canción, mismo inicio), mezcla.json y mezcla.wav (herramientas/mezclar.py). El
  servidor usa mezcla.wav antes que musica.wav al exportar. Los tipos sin equivalente real (la impresora) siguen
  sintetizados con musica.py en <carpeta>/efectos_sinteticos/ (fuera de git); el «riser» se deja: la canción ya sube.
- `--energia`: escribe también energia.js, el espectro REAL del tramo de canción (32 bandas de 60 Hz a 8 kHz, 60
  veces por segundo, cada valor de 0 a 35 en base 36), para dibujar barras de audio que siguen la música de verdad
  (las usa showreel.js).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import cancion  # noqa: E402

# tipo de musica.json → (efecto del banco, dB, alinear por el pico)
REALES = {
    "whoosh": ("transicion/whoosh-rapido.wav", -9, True), "impacto": ("impacto/kenney-soft-heavy-000.wav", -4, False),
    "clic": ("interfaz/kenney-click-001.wav", -7, False), "pop": ("pop/burbuja-pop.wav", -9, False),
    "check": ("exito/kenney-confirmation-001.wav", -9, False), "tecla": ("teclado/tecla-sola.wav", -14, False),
    "notificacion": ("exito/campana-logro.wav", -12, True), "burbuja": ("pop/burbuja-pop.wav", -10, False),
    "obturador": ("camara/obturador.wav", -8, True), "deslizar": ("transicion/swoosh-rapido.wav", -11, True),
    "moneda": ("exito/kenney-glass-001.wav", -10, False), "escaner": ("interfaz/kenney-scroll-002.wav", -12, False),
}
SINTETICOS = {"impresora"}
FUERA = {"riser"}


def analizar(ruta):
    x = cancion.leer(str(ruta))
    env, fps = cancion.envolvente(x)
    bpm = cancion.tempo(env, fps)
    t0 = cancion.fase(env, fps, bpm)
    compas = 4 * 60 / bpm
    acum = np.concatenate([[0], np.cumsum(x.astype(np.float64) ** 2)])
    e = lambda a, b: np.sqrt((acum[int(b * cancion.SR)] - acum[int(a * cancion.SR)]) / max(1, int(b * cancion.SR) - int(a * cancion.SR)))
    n = int((len(x) / cancion.SR - t0) / compas)
    por_compas = np.array([e(t0 + k * compas, t0 + (k + 1) * compas) for k in range(n)])
    return bpm, t0, compas, por_compas, len(x) / cancion.SR


def espectro(ruta, desde, largo, fps=60, bandas=32, sr=22050):
    """Espectro del tramo [desde, desde+largo] de la canción, `fps` veces por segundo, en `bandas` bandas
    logarítmicas; cada banda normalizada por su percentil 95 → texto en base 36 (un carácter por banda y cuadro)."""
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, desde):.3f}", "-t", f"{largo:.3f}", "-i", str(ruta),
                            "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(crudo, np.float32)
    n, cuadros = 2048, int(largo * fps)
    x = np.pad(x, (n, n))
    ventana = np.hanning(n)
    frec = np.fft.rfftfreq(n, 1 / sr)
    bordes = np.geomspace(60, 8000, bandas + 1)
    idx = [(frec >= bordes[k]) & (frec < bordes[k + 1]) for k in range(bandas)]
    m = np.zeros((cuadros, bandas))
    for i in range(cuadros):
        c = n + int(i / fps * sr)
        mag = np.abs(np.fft.rfft(x[c - n // 2:c + n // 2] * ventana))
        m[i] = [mag[j].mean() if j.any() else 0 for j in idx]
    m = np.log1p(m)
    m = np.clip(m / np.maximum(np.percentile(m, 95, axis=0), 1e-6), 0, 1)
    digitos = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(digitos[int(round(v * 35))] for v in m.ravel()), cuadros


def main(a):
    carpeta, ruta = Path(a[0]).resolve(), Path(a[1])
    if not ruta.is_absolute(): ruta = RAIZ / ruta              # sin resolve(): recursos/ puede ser un enlace a otro disco
    m = json.loads((carpeta / "musica.json").read_text(encoding="utf-8"))
    pj = (carpeta / "pulsos.js").read_text(encoding="utf-8")
    inicio = float(json.loads(re.search(r"=\s*(\{.*\})", pj).group(1))["inicio"])
    impactos = [e["pulso"] for e in m["efectos"] if e["tipo"] == "impacto"]
    golpe = float(a[a.index("--golpe") + 1]) if "--golpe" in a else (max(impactos) if impactos else 0)
    bpm, t0, compas, energia, largo_cancion = analizar(ruta)
    largo_video = m["compases"]                                   # en compases
    gc = int(round(golpe / 4))                                    # compás del video donde está el golpe
    if "--compas" in a:
        inicio_c = int(a[a.index("--compas") + 1])
    else:
        subida = energia[1:] / np.maximum(energia[:-1], 1e-6)     # subida[k]: del compás k al k+1
        cands = [k + 1 for k in range(len(subida)) if k + 1 - gc >= 0 and k + 1 - gc + largo_video + 1 <= len(energia)]
        if not cands: sys.exit("la canción es más corta que el video")
        mejor = max(cands, key=lambda k: subida[k - 1])
        inicio_c = mejor - gc
        print(f"subida mayor en el compás {mejor} (×{subida[mejor - 1]:.2f}) → la canción arranca en su compás {inicio_c}")
    T = lambda p: inicio + p * 60 / bpm
    efectos, sint = [], []
    for e in m["efectos"]:
        if e["tipo"] in FUERA: continue
        if e["tipo"] in SINTETICOS or e["tipo"] not in REALES: sint.append(e); continue
        archivo, db, pico = REALES[e["tipo"]]
        db += 20 * np.log10(max(e.get("vol", 1), 1e-3))
        efectos.append({"archivo": archivo, "en": round(T(e["pulso"]), 3), "db": round(float(db), 1), **({"alinear": "pico"} if pico else {})})
    total = T(largo_video * 4) + 1.0
    mezcla = {"cancion": {"archivo": ruta.relative_to(RAIZ).as_posix(), "desde": round(t0 + inicio_c * compas - inicio, 3),
                          "volumen": .9, "entrada": .05, "salida": 1.2},
              "efectos": efectos, "duracion": round(total, 3), "lufs": -14}
    if sint:
        d = carpeta / "efectos_sinteticos"; d.mkdir(exist_ok=True)
        (d / "musica.json").write_text(json.dumps({"bpm": round(bpm, 2), "compases": largo_video, "progresion": ["Am"], "secciones": [],
                                                   "silencio_antes": [], "efectos": sint}, ensure_ascii=False, indent=1), encoding="utf-8")
        subprocess.run([sys.executable, str(AQUI / "musica.py"), str(d)], check=True)
        mezcla["extra"] = [{"archivo": "efectos_sinteticos/musica.wav", "volumen": .42}]
    (carpeta / "pulsos.js").write_text(f'window.PULSOS = {{"bpm": {bpm:.2f}, "inicio": {inicio}, "total": {total:.3f}, '
                                       f'"compases": {largo_video}}};\n', encoding="utf-8")
    (carpeta / "mezcla.json").write_text(json.dumps(mezcla, ensure_ascii=False, indent=1), encoding="utf-8")
    if "--energia" in a:                                           # t = 0 del video = mezcla.cancion.desde de la canción
        datos, cuadros = espectro(ruta, mezcla["cancion"]["desde"], total)
        (carpeta / "energia.js").write_text(f'window.ENERGIA = {{"fps": 60, "bandas": 32, "cuadros": {cuadros}, "datos": "{datos}"}};\n',
                                            encoding="utf-8")
        print(f"energia.js: {cuadros} cuadros × 32 bandas")
    print(f"{ruta.name}: {bpm:.2f} BPM · desde {mezcla['cancion']['desde']:.2f} s · golpe del pulso {golpe:g} en el compás "
          f"{inicio_c + gc} · {len(efectos)} efectos reales" + (f", {len(sint)} sintetizados" if sint else ""))
    subprocess.run([sys.executable, str(AQUI / "mezclar.py"), str(carpeta)], check=True)


if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    main(sys.argv[1:])
