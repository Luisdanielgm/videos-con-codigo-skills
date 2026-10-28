"""Recorta a la persona de un clip, cuadro a cuadro (técnica 27: alguien hablando sobre mundos que cambian).

    <venv-vision>/Scripts/python herramientas/recortar_persona.py <entrada.mp4> <salida-sin-extension> [--desde s] [--dura s]
    <venv-vision>/Scripts/python herramientas/recortar_persona.py --probar

Escribe dos clips **todo intra** a 30 fps y del mismo largo: `<salida>.mp4` (el color) y `<salida>_mascara.mp4` (blanco
donde está la persona). La página dibuja la máscara y encima el color con `source-in` (`Clips` los lleva al mismo
cuadro), así el recorte salta al cuadro exacto como cualquier clip; un WebM con alfa no se deja buscar igual de bien.

Modelo: MediaPipe «selfie multiclass 256×256» (Apache 2.0, en modelos/vision): la persona es
todo lo que no es fondo (pelo, cuerpo, ropa, cara). La máscara se suaviza en el tiempo (media móvil con el cuadro
anterior: sin parpadeo del borde) y con un desenfoque chico (borde sin escalones).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

MODELO = Path("modelos/vision/selfie_multiclass_256x256.tflite")
FPS = 30
SUAVE_T = 0.55        # peso del cuadro actual en la media móvil de la máscara
UMBRAL = (0.35, 0.65)  # confianza → alfa: debajo de 0,35 es fondo, encima de 0,65 es persona


def sonda(ruta):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(ruta)], capture_output=True, text=True, check=True)
    w, h = map(int, r.stdout.strip().split(",")[:2])
    return w, h


def cuadros(ruta, w, h, desde, dura):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(desde)] + (["-t", str(dura)] if dura else []) + \
          ["-i", str(ruta), "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.wait()


def escritor(salida, w, h, gris):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray" if gris else "rgb24",
                             "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-g", "1", "-crf", "14" if gris else "16",
                             "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)


def recortar(entrada, salida, desde=0.0, dura=None, segmentar=None):
    import cv2
    w, h = sonda(entrada)
    if segmentar is None:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
        seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=str(MODELO)), output_confidence_masks=True))
        def segmentar(rgb):
            r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
            return 1.0 - r.confidence_masks[0].numpy_view()           # 0 = fondo
    color, masc = escritor(f"{salida}.mp4", w, h, False), escritor(f"{salida}_mascara.mp4", w, h, True)
    previa, n = None, 0
    for rgb in cuadros(entrada, w, h, desde, dura):
        m = cv2.resize(np.asarray(segmentar(rgb), np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        previa = m if previa is None else SUAVE_T * m + (1 - SUAVE_T) * previa
        a = np.clip((previa - UMBRAL[0]) / (UMBRAL[1] - UMBRAL[0]), 0, 1)
        a = cv2.GaussianBlur(a, (0, 0), 1.6)
        color.stdin.write(rgb.tobytes()); masc.stdin.write((a * 255).astype(np.uint8).tobytes()); n += 1
    for p in (color, masc):
        p.stdin.close(); p.wait()
    return n


def probar():
    """Sin modelo: un clip sintético con un círculo que se mueve y un «segmentador» que lo encuentra por color."""
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        # overlay sí mueve el cuadrado con t (drawbox no lo dibujaba con x en función de t)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1:r=25",
                        "-f", "lavfi", "-i", "color=c=red:s=80x80:d=1:r=25", "-filter_complex",
                        "[0][1]overlay=x='40+t*120':y=80", str(d / "e.mp4")], check=True)
        rojo = lambda rgb: (rgb[..., 0] > 150) & (rgb[..., 2] < 100)
        n = recortar(d / "e.mp4", d / "s", segmentar=lambda rgb: rojo(rgb).astype(np.float32))
        w, h = sonda(d / "s_mascara.mp4")
        cuenta = lambda f: int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                                               "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(f)],
                                              capture_output=True, text=True).stdout.strip())
        m = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(d / "s_mascara.mp4"), "-frames:v", "1",
                                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout, np.uint8).reshape(h, w)
        casos = [("30 cuadros de 1 s a 30 fps", n == 30),
                 ("color y máscara con los mismos cuadros", cuenta(d / "s.mp4") == cuenta(d / "s_mascara.mp4") == 30),
                 ("la máscara es blanca en la persona", m[120, int(40 + .5 * 120 + 40)] > 200),
                 ("la máscara es negra en el fondo", m[20, 20] < 30 and m[220, 300] < 30)]
        for nombre, paso in casos:
            print(("ok    " if paso else "FALLA ") + nombre)
            ok &= paso
    print("recortar_persona:", "todo ok" if ok else "HAY FALLAS")
    return ok


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    a = sys.argv[1:]
    opc = {k: float(a[a.index(k) + 1]) for k in ("--desde", "--dura") if k in a}
    n = recortar(Path(a[0]), a[1], opc.get("--desde", 0.0), opc.get("--dura"))
    print(f"{n} cuadros → {a[1]}.mp4 y {a[1]}_mascara.mp4")
