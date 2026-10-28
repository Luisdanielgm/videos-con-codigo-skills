"""Guardia de determinismo: comprueba que el cuadro de un instante NO depende de qué instantes se dibujaron antes.
El exporte dibuja los cuadros en orden, pero la revisión (capturas, hojas de contacto, un tramo reanudado) los pide en
cualquier orden. Si el video guarda estado entre cuadros (un contador que sube, hilos simulados que se acumulan, un
Math.random sin semilla, Date.now()), el mismo t da cuadros distintos según el camino: el MP4 y lo que revisaste no
son el mismo video (pasó con unos hilos de sutura simulados y con Math.sin() de hash en el faro).

    .venv/Scripts/python herramientas/determinismo.py <carpeta-del-video> [--instantes 2,10,25,40]
                         [--params "fps=60&sub=4"] [--mp4 ruta]
    .venv/Scripts/python herramientas/determinismo.py --probar
                         # se rompe a propósito: una página pura debe dar ok y tres impuras (contador, azar,
                         # reloj) deben dar FALLA

- Saca las capturas de la PÁGINA dos veces, cada una en una página nueva: una en el orden dado y otra en el orden
  inverso (con 4 instantes: 2,10,25,40 y luego 40,25,10,2), y compara cada instante consigo mismo.
- Instantes por omisión: los 6 de verificar_export.py si hay MP4 en render/ (o `--mp4`); si no, 1,3,6,10,15 s.
  Hacen falta al menos 3 instantes para que el orden importe.
- Mismas reglas de umbral que verificar_export.py pero mucho más estrictas: dos dibujos del mismo código en el mismo
  navegador deben ser idénticos (diferencia media ≤ 0,5, fracción grande ≤ 0,1 %, peor bloque ≤ 2).
- Sale con código 1 si algún instante dice FALLA o si la página dio error de consola.

Medido (6 videos, instantes por omisión, fps=60&sub=2): 5 ok con diferencia 0,00; El faro (23) dio FALLA sólo en
t = 0,3 s (peor bloque 2,98): el grano de la acuarela de la luna cambia hasta 20/255 según el orden (mismo orden: 0,00), sin
efecto visible. Es una dependencia real del orden y se deja como está: no justifica relajar el umbral.

Límite: un estado que sólo se nota entre cuadros contiguos (una física que integra paso a paso con el mismo t) no
aparece si los instantes están lejos entre sí: ahí el estado se reconstruye desde cero. Eso se arregla escribiendo el
cuadro como función pura de t (ver la skill exportar-video, «el cuadro es una función de t»).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verificar_export as ve

for _f in (sys.stdout, sys.stderr):
    _f.reconfigure(encoding="utf-8")

RAIZ, RENDER = ve.RAIZ, ve.RENDER
MEDIA_MAX, FRAC_MAX, BLOQUE_MAX = 0.5, 0.001, 2.0
POR_OMISION = [1, 3, 6, 10, 15]


def instantes(carpeta, mp4, dados):
    if dados:
        return dados
    mp4 = Path(mp4) if mp4 else RENDER / f"{carpeta.replace('/', '_')}.mp4"
    if mp4.exists():
        fps, dur, _w, _h = ve.sonda(mp4)
        return ve.ajustar(ve.instantes_por_omision(dur), fps, dur)
    return POR_OMISION


def imagenes(carpeta, ts, params):
    """Una corrida de capturas en el orden dado → ({t: matriz RGB}, errores). Se leen en seguida: la segunda corrida
    escribe sobre los mismos archivos."""
    rutas, errores = ve.capturar(carpeta, ts, params)
    faltan = [t for t in ts if not rutas[t].exists()]
    if faltan:
        sys.exit(f"No salieron las capturas de {faltan} (¿falló la página?).")
    out = {}
    for t in ts:
        with ve.Image.open(rutas[t]) as im:
            out[t] = np.asarray(im.convert("RGB")).copy()
    return out, errores


def veredicto(m, f, b):
    return "ok" if m <= MEDIA_MAX and f <= FRAC_MAX and b <= BLOQUE_MAX else "FALLA"


def medir(carpeta, ts, params):
    """[(t, media, fracción, bloque, veredicto)] y los errores de consola de las dos corridas."""
    if len(ts) < 3:
        sys.exit("Hacen falta al menos 3 instantes para que el orden importe.")
    ida, e1 = imagenes(carpeta, ts, params)
    vuelta, e2 = imagenes(carpeta, ts[::-1], params)
    out = []
    for t in ts:
        m, f, b = ve.comparar(ida[t], vuelta[t])
        out.append((t, m, f, b, veredicto(m, f, b)))
    return out, sorted(set(e1 + e2))


def imprimir(carpeta, ts, res):
    print(f"{carpeta}: orden {','.join('%g' % t for t in ts)} contra el inverso · umbrales: media ≤ {MEDIA_MAX:g}, "
          f"fracción(>{ve.GRANDE}) ≤ {FRAC_MAX * 100:g} %, peor bloque ≤ {BLOQUE_MAX:g}")
    for t, m, f, b, v in res:
        print(f"  {v:5s} t={t:7.3f} s  diferencia media {m:6.2f}  fracción grande {f * 100:6.2f} %  peor bloque {b:6.2f}")
    malos = sum(v == "FALLA" for *_, v in res)
    print(f"TOTAL: {len(res) - malos} ok, {malos} FALLA")
    return malos


PAGINA = """<!doctype html><meta charset="utf-8"><body style="margin:0;background:#000">
<canvas id="c" width="1920" height="1080"></canvas>
<script src="../../../herramientas/reproductor.js"></script>
<script>
// Página de prueba de determinismo (herramientas/determinismo.py --probar). Modo: %(modo)s
const c = document.getElementById('c'), x = c.getContext('2d', { willReadFrequently: true });
let llamadas = 0;
function render(t) {
  llamadas++;
  const px = %(posicion)s;
  x.fillStyle = '#103050'; x.fillRect(0, 0, 1920, 1080);
  x.fillStyle = '#ffcc33'; x.fillRect(px, 380, 360, 320);
  x.fillStyle = '#ffffff'; x.font = '64px sans-serif'; x.fillText('t = ' + t.toFixed(2), 80, 120);
}
Reproductor.iniciar({ canvas: c, render, duracion: 20 });
</script>
"""

CASOS = [  # (nombre, expresión de la posición x del cuadro, veredicto esperado)
    ("pura (x = 100 + 80·t)", "100 + 80 * t", "ok"),
    ("contador (x sube con cada llamada)", "100 + 90 * llamadas", "FALLA"),
    ("azar sin semilla (Math.random)", "100 + 1400 * Math.random()", "FALLA"),
    ("reloj (Date.now)", "100 + (Date.now() % 1400)", "FALLA"),
]


def probar():
    """Un guardián que nunca falló no se cree: una página pura debe dar ok y las tres impuras, FALLA."""
    base = RENDER / "_prueba-determinismo"
    ok = True
    for i, (nombre, pos, esperado) in enumerate(CASOS):
        d = base / f"caso{i}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(PAGINA % {"modo": nombre, "posicion": pos}, encoding="utf-8")
        carpeta = f"render/_prueba-determinismo/caso{i}"
        res, errores = medir(carpeta, [2, 6, 10, 14], "")
        malos = sum(v == "FALLA" for *_, v in res)
        dicho = "FALLA" if malos or errores else "ok"
        paso = dicho == esperado
        ok &= paso
        print(f"  {dicho:5s} {nombre:36s} {len(res) - malos}/{len(res)} instantes ok  (esperado {esperado}) "
              f"{'PASA' if paso else 'NO PASA'}")
    print("PRUEBA", "PASA" if ok else "FALLA")
    return ok


def main():
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    if "--probar" in a:
        sys.exit(0 if probar() else 1)
    if not a or a[0].startswith("--"):
        sys.exit(__doc__)
    carpeta = a[0].replace("\\", "/").strip("/")
    dados = [float(x) for x in opt("--instantes").split(",")] if opt("--instantes") else None
    ts = instantes(carpeta, opt("--mp4"), dados)
    res, errores = medir(carpeta, ts, opt("--params"))
    malos = imprimir(carpeta, ts, res)
    for e in errores:
        print(e)
    if errores:
        print("FALLA: la página dio errores de consola (ver render/navegador-capturas-<puerto>.log)")
    sys.exit(1 if malos or errores else 0)


if __name__ == "__main__":
    main()
