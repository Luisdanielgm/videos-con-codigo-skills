"""Baja clips de captura de movimiento (BVH) de la base pública de CMU a externos/mocap/.

Uso:  python herramientas/bajar_mocap.py

Fuente: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), libre para cualquier uso,
en la conversión a BVH de Bruce Hahne (cgspeed), publicada en github.com/una-dinosauria/cmu-mocap.
El índice de todos los clips está en cmu-mocap-index-text.txt de ese repositorio.
Los archivos no van a git (externos/ está en .gitignore): se vuelven a bajar con este script.
"""
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "externos" / "mocap"
BASE = "https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{sujeto:03d}/{clip}.bvh"

CLIPS = {
    "01_06": "trepa, se sienta con las piernas colgando, baja",
    "13_33": "trepa una escalera",
    "13_27": "dirige el tránsito, saluda, señala",
    "09_01": "corre",
    "13_11": "salto hacia adelante",
    "132_01": "camina con los brazos abiertos (equilibrio)",
    "125_06": "nada estilo libre",
    "104_14": "empieza a caminar, contento",
    "07_01": "camina",
    "79_73": "asustado",
    "13_29": "saltos de tijera, estiramientos",
    "14_29": "sentado en un banquito, balancea las piernas",
    "82_08": "quieto de pie; camina tranquilo",
    "40_10": "espera el autobús (de pie, quieto)",
}


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for clip, desc in CLIPS.items():
        out = DESTINO / f"{clip}.bvh"
        if out.exists():
            continue
        url = BASE.format(sujeto=int(clip.split("_")[0]), clip=clip)
        print(f"{clip:8} {desc}")
        urllib.request.urlretrieve(url, out)
        if not out.read_text(errors="ignore").startswith("HIERARCHY"):
            out.unlink()
            sys.exit(f"{clip}: lo bajado no es un BVH ({url})")
    print(f"listo: {len(CLIPS)} clips en {DESTINO}")


if __name__ == "__main__":
    main()
