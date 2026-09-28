"""Normaliza el banco de efectos a WAV 48 kHz, arma indice.json y verifica cada archivo.

Uso: python herramientas/preparar_efectos.py            -> procesa y verifica el banco
     python herramientas/preparar_efectos.py --romper   -> prueba la guardia con casos malos a propósito

Antes hay que bajar los originales (no vienen en el repositorio: su licencia no deja redistribuirlos sueltos):
  - Mixkit: cada fila de herramientas/seleccion.tsv (id, categoría, nombre, página) se baja de
    https://assets.mixkit.co/active_storage/sfx/<id>/<id>.wav a recursos/efectos/mixkit/<categoría>/<nombre>.wav
  - Kenney (CC0): los zip de KENNEY_ZIP, descomprimidos en recursos/efectos/kenney/<paquete>/ (con su carpeta Audio/).
El resultado queda en recursos/efectos/listos/<categoría>/<nombre>.wav + recursos/efectos/indice.json, que
usan mezclar.py, pista.py y motor_manim.py.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent / "recursos" / "efectos"
SR = 48000
FORMATO = "pcm_s24le"
FILTRO = "silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.01:detection=peak,aresample=48000"

LIC_MIXKIT = "Mixkit Sound Effects Free License (https://mixkit.co/license/#sfxFree)"
LIC_KENNEY = "CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/)"

KENNEY_PAG = {
    "interface-sounds": "https://kenney.nl/assets/interface-sounds",
    "ui-audio": "https://kenney.nl/assets/ui-audio",
    "impact-sounds": "https://kenney.nl/assets/impact-sounds",
}
KENNEY_ZIP = {
    "interface-sounds": "https://kenney.nl/media/pages/assets/interface-sounds/fa43c1dd4d-1677589452/kenney_interface-sounds.zip",
    "ui-audio": "https://kenney.nl/media/pages/assets/ui-audio/490d233f68-1677590494/kenney_ui-audio.zip",
    "impact-sounds": "https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip",
}
# (paquete, archivo original, categoria, nombre)
KENNEY = [
    ("interface-sounds", "click_001.ogg", "interfaz", "kenney-click-001"),
    ("interface-sounds", "switch_002.ogg", "interfaz", "kenney-switch-002"),
    ("interface-sounds", "select_003.ogg", "interfaz", "kenney-select-003"),
    ("interface-sounds", "toggle_001.ogg", "interfaz", "kenney-toggle-001"),
    ("interface-sounds", "open_001.ogg", "interfaz", "kenney-open-001"),
    ("interface-sounds", "scroll_002.ogg", "interfaz", "kenney-scroll-002"),
    ("ui-audio", "click1.ogg", "interfaz", "kenney-ui-click1"),
    ("ui-audio", "rollover2.ogg", "interfaz", "kenney-ui-rollover2"),
    ("ui-audio", "switch7.ogg", "interfaz", "kenney-ui-switch7"),
    ("interface-sounds", "maximize_001.ogg", "transicion", "kenney-maximize-001"),
    ("interface-sounds", "minimize_001.ogg", "transicion", "kenney-minimize-001"),
    ("interface-sounds", "confirmation_001.ogg", "exito", "kenney-confirmation-001"),
    ("interface-sounds", "confirmation_002.ogg", "exito", "kenney-confirmation-002"),
    ("interface-sounds", "glass_001.ogg", "exito", "kenney-glass-001"),
    ("interface-sounds", "error_008.ogg", "error", "kenney-error-008"),
    ("interface-sounds", "error_004.ogg", "error", "kenney-error-004"),
    ("interface-sounds", "error_006.ogg", "error", "kenney-error-006"),
    ("interface-sounds", "drop_001.ogg", "pop", "kenney-drop-001"),
    ("interface-sounds", "drop_002.ogg", "pop", "kenney-drop-002"),
    ("impact-sounds", "impactPunch_heavy_000.ogg", "impacto", "kenney-punch-heavy-000"),
    ("impact-sounds", "impactSoft_heavy_000.ogg", "impacto", "kenney-soft-heavy-000"),
    ("impact-sounds", "impactWood_heavy_000.ogg", "impacto", "kenney-wood-heavy-000"),
    ("impact-sounds", "impactMetal_heavy_000.ogg", "impacto", "kenney-metal-heavy-000"),
    ("impact-sounds", "impactBell_heavy_000.ogg", "impacto", "kenney-bell-heavy-000"),
    ("impact-sounds", "impactPlank_medium_000.ogg", "impacto", "kenney-plank-medium-000"),
]


def entradas():
    lista = []
    for linea in (AQUI / "seleccion.tsv").read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        ide, cat, nombre, pagina = linea.split("\t")
        lista.append({
            "nombre": nombre, "categoria": cat, "fuente": "mixkit",
            "src": BASE / "mixkit" / cat / f"{nombre}.wav",
            "original": f"mixkit/{cat}/{nombre}.wav",
            "url": f"https://mixkit.co/free-sound-effects/{pagina}/",
            "url_audio": f"https://assets.mixkit.co/active_storage/sfx/{ide}/{ide}.wav",
            "licencia": LIC_MIXKIT,
        })
    for paq, arch, cat, nombre in KENNEY:
        lista.append({
            "nombre": nombre, "categoria": cat, "fuente": "kenney",
            "src": BASE / "kenney" / paq / "Audio" / arch,
            "original": f"kenney/{paq}/Audio/{arch}",
            "url": KENNEY_PAG[paq], "url_audio": KENNEY_ZIP[paq],
            "licencia": LIC_KENNEY,
        })
    return lista


def convertir(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-threads", "1", "-y",
                    "-i", str(src), "-af", FILTRO, "-c:a", FORMATO, str(dst)], check=True)


def medir(ruta):
    x, sr = sf.read(str(ruta), dtype="float64", always_2d=True)
    dur = len(x) / sr
    rms = float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0
    rms_db = 20 * np.log10(rms) if rms > 0 else -999.0
    pico = float(np.max(np.abs(x))) if len(x) else 0.0
    pico_db = 20 * np.log10(pico) if pico > 0 else -999.0
    # saturación: cualquier muestra en el tope (>= -0,01 dBFS); el remuestreo recorta muestras sueltas, no rachas
    en_tope = int(np.sum(np.abs(x) >= 10 ** (-0.01 / 20)))
    # pico de energía en ventanas de 10 ms (centro de la ventana)
    n = int(round(sr * 0.010))
    k = len(x) // n
    if k:
        e = (x[:k * n] ** 2).sum(axis=1).reshape(k, n).sum(axis=1)
        pico_s = (int(np.argmax(e)) + 0.5) * n / sr
    else:
        pico_s = 0.0
    return {"sr": sr, "dur": dur, "rms_db": rms_db, "pico_db": pico_db, "en_tope": en_tope, "pico_s": pico_s}


def juzgar(m):
    fallas = []
    if m["sr"] != SR:
        fallas.append(f"sr={m['sr']}")
    if m["dur"] <= 0.05:
        fallas.append(f"dura {m['dur']:.3f} s")
    if m["rms_db"] <= -50:
        fallas.append(f"RMS {m['rms_db']:.1f} dBFS")
    if m["pico_db"] > 0 or m["en_tope"]:
        fallas.append(f"satura (pico {m['pico_db']:.2f} dBFS, {m['en_tope']} muestras en el tope)")
    return fallas


def romper():
    """Casos malos a propósito: cada uno tiene que dar FALLA; el bueno, ok."""
    d = AQUI / "romper"
    d.mkdir(exist_ok=True)
    t = np.arange(int(SR * 0.5)) / SR
    casos = {
        "bueno": 0.5 * np.sin(2 * np.pi * 440 * t),
        "corto": 0.5 * np.sin(2 * np.pi * 440 * t[: int(SR * 0.03)]),
        "silencio": 0.001 * np.sin(2 * np.pi * 440 * t),  # -63 dBFS RMS
        "satura": np.clip(2.0 * np.sin(2 * np.pi * 440 * t), -1, 1),
        "recorte_suelto": 0.5 * np.sin(2 * np.pi * 440 * t),
    }
    casos["recorte_suelto"][[1000, 5000]] = 1.0  # dos muestras sueltas en el tope, como las del remuestreo
    for nombre, y in casos.items():
        sf.write(str(d / f"{nombre}.wav"), y, SR, subtype="PCM_24")
    sf.write(str(d / "sr44.wav"), casos["bueno"], 44100, subtype="PCM_24")
    esperado = {"bueno": True, "corto": False, "silencio": False, "satura": False, "recorte_suelto": False,
                "sr44": False}
    bien = 0
    for nombre, ok_esperado in esperado.items():
        f = juzgar(medir(d / f"{nombre}.wav"))
        dio_ok = not f
        acierto = dio_ok == ok_esperado
        bien += acierto
        print(f"{'ok' if dio_ok else 'FALLA'}  {nombre}  {'; '.join(f)}  -> {'como se esperaba' if acierto else 'MAL'}")
    print(f"guardia: {bien}/{len(esperado)} casos como se esperaba")
    return bien == len(esperado)


def main():
    if "--romper" in sys.argv:
        sys.exit(0 if romper() else 1)
    indice, malos = [], 0
    for e in entradas():
        dst = BASE / "listos" / e["categoria"] / f"{e['nombre']}.wav"
        convertir(e["src"], dst)
        m = medir(dst)
        f = juzgar(m)
        malos += bool(f)
        print(f"{'ok' if not f else 'FALLA'}  {e['categoria']}/{e['nombre']}  {m['dur']:.3f} s  RMS {m['rms_db']:.1f}  "
              f"pico {m['pico_db']:.2f} dBFS @ {m['pico_s']:.3f} s  {'; '.join(f)}")
        indice.append({
            "nombre": e["nombre"], "categoria": e["categoria"],
            "archivo": dst.relative_to(BASE).as_posix(),
            "duracion_s": round(m["dur"], 3), "pico_s": round(m["pico_s"], 3),
            "fuente": e["fuente"], "url": e["url"], "url_audio": e["url_audio"],
            "original": e["original"], "licencia": e["licencia"],
        })
    indice.sort(key=lambda r: (r["categoria"], r["fuente"], r["nombre"]))
    (BASE / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"total: {len(indice)} efectos, {len(indice) - malos} ok, {malos} FALLA")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
