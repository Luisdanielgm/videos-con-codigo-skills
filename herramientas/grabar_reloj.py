"""Graba a cuadros exactos una página AJENA que anima con el reloj real (requestAnimationFrame, setTimeout y animaciones
CSS), p. ej. los ejemplos de Anatomy: el reloj del navegador se congela y se adelanta cuadro por cuadro. Las páginas
propias no lo necesitan (cada cuadro es render(t): navegador.py).

Uso:  .venv/Scripts/python herramientas/grabar_reloj.py <url> <salida.mp4> [--seg 13.2] [--fps 30] [--selector .iso-figure]
                                                         [--escala 2] [--ancho 1280] [--alto 900]
      .venv/Scripts/python herramientas/grabar_reloj.py --probar     (ok o FALLA por caso)

La URL va por http (python -m http.server) si la página carga módulos. Sale sin audio. Límites: la página tiene que
animar sola (si sólo se mueve con el mouse, no hay qué grabar), y el origen fijo (49 ms) sólo lo protege la comprobación
en la corrida (`ahora > 48` aborta), que `--probar` no ejerce (mutarla da ok). Un rAF que use el tiempo real por otra vía (Date de
un worker, audio) se escapa del reloj congelado.
"""
import argparse
import subprocess
import sys
import tempfile
import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

from color_mp4 import COLOR_709

CUENTA_PEDIDOS = ("{const o = window.requestAnimationFrame; window.__pedidos = 0;"
                  " window.requestAnimationFrame = cb => { window.__pedidos++; return o(cb); };}")
CSS = "t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })"


def cuadros(url, seg, fps, selector="body", escala=2.0, ancho=1280, alto=900, al_cuadro=None):
    """Devuelve los cuadros (PNG en bytes) de seg segundos a fps. al_cuadro(pagina, i, ms) corre antes de cada captura."""
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        pag = nav.new_page(viewport={"width": ancho, "height": alto}, device_scale_factor=escala)
        pag.clock.install(time=0)
        pag.clock.pause_at(1000)  # install solo no basta: el reloj falso sigue corriendo a tiempo real hasta pausarlo
        pag.add_init_script(CUENTA_PEDIDOS)
        pag.goto(url)
        pag.wait_for_load_state("load")
        for _ in range(200):          # tiempo real: el IntersectionObserver (o lo que arranque la animación) llega cuando quiere
            if pag.evaluate("window.__pedidos"):
                break
            time.sleep(0.05)
        else:
            nav.close()
            raise SystemExit("la página no pidió ningún cuadro en 10 s: no anima con requestAnimationFrame")
        # el rAF falso dispara en múltiplos de 16 ms del performance.now de la página, y ese reloj arranca con 5-20 ms de
        # tiempo real colado antes de pausar: el origen es una marca fija (49 = 3·16 + 1), igual en cada corrida; si el
        # colado la pasó, esa corrida no sirve (se avisa, no se graba corrida)
        ahora = int(pag.evaluate("performance.now()"))
        origen = 49
        if ahora > 48:
            nav.close()
            raise SystemExit(f"el reloj ya iba en {ahora} ms al pausar (máx. 48): vuelve a correr")
        caja = pag.locator(selector).first
        salida = []
        for i in range(round(seg * fps)):
            ms = round(i * 1000 / fps)
            if origen + ms > ahora:
                pag.clock.run_for(origen + ms - ahora)
                ahora = origen + ms
            pag.evaluate(CSS, ms)
            if al_cuadro:
                al_cuadro(pag, i, ms)
            salida.append(caja.screenshot())
        nav.close()
    return salida


def a_mp4(pngs, fps, destino):
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
                           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16",
                           *COLOR_709, str(destino)], stdin=subprocess.PIPE)
    for png in pngs:
        ff.stdin.write(png)
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg falló")


PAGINA_PRUEBA = """<!doctype html><meta charset=utf-8>
<style>body{margin:0;background:#111}@keyframes mv{to{transform:translateX(500px)}}
#a{width:60px;height:60px;background:#fff;animation:mv 1000ms linear infinite}#b{width:60px;height:60px;background:#f80}</style>
<div id=a></div><div id=b></div><div id=t style="color:#fff"></div>
<script>
// como Anatomy: arranca cuando el IntersectionObserver avisa (tiempo real) e integra con el dt de cada rAF
let reloj = 0, last = 0, x = 0;
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60; last = now; reloj += dt;
  x += ((Math.floor(reloj / .7) % 2 ? 400 : 0) - x) *(1 - Math.exp(-dt / .2));   // salta cada 0,7 s con un resorte
  document.getElementById("b").style.transform = `translateX(${x}px)`;
  document.getElementById("t").textContent = now;
  requestAnimationFrame(tick);
}
new IntersectionObserver(e => { if (e[0].isIntersecting && !last) requestAnimationFrame(tick); }).observe(document.body);
</script>"""


def probar():
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "prueba.html"
        html.write_text(PAGINA_PRUEBA, encoding="utf-8")
        url = html.as_uri()
        datos = []
        def anota(pag, i, ms):
            datos.append((ms, pag.evaluate("performance.now()"), pag.evaluate("document.getElementById('t').textContent"),
                          pag.evaluate("new DOMMatrix(getComputedStyle(document.getElementById('a')).transform).m41")))
        a = cuadros(url, 3, 30, escala=1, ancho=640, alto=240, al_cuadro=anota)
        b = cuadros(url, 3, 30, escala=1, ancho=640, alto=240)
    arr = lambda png: np.asarray(Image.open(BytesIO(png)).convert("RGB"), np.int16)
    peor = max(int(np.abs(arr(x) - arr(y)).max()) for x, y in zip(a, b))
    distintos = len({hash(x) for x in a})
    t0 = datos[0][1]
    corridos = [ms for ms, now, _, _ in datos if now - t0 != ms]
    al_dia = all(0 <= now - int(tx) < 16 for _, now, tx, _ in datos)    # la página ya dibujó el último rAF antes de la captura
    css_mal = [ms for ms, _, _, mx in datos if abs(mx - (ms % 1000) / 1000 * 500) > .5]
    casos = [
        (peor <= 2 and distintos > 10, f"dos grabaciones iguales (peor diferencia {peor} niveles de 255) y la página se mueve ({distintos} cuadros distintos de {len(a)})"),
        (not corridos and al_dia, f"cada cuadro está a i·1000/fps ms del primero y muestra el último rAF (corridos: {corridos[:3]})"),
        (not css_mal, f"las animaciones CSS van con el mismo reloj (fuera de lugar: {css_mal[:3]})"),
    ]
    for bien, texto in casos:
        print(f"  {'ok' if bien else 'FALLA'}  {texto}")
    malos = sum(not b for b, _ in casos)
    print(f"  {len(casos) - malos} ok, {malos} FALLA")
    return malos == 0


def main():
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("salida")
    ap.add_argument("--seg", type=float, default=13.2); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--selector", default="body"); ap.add_argument("--escala", type=float, default=2.0)
    ap.add_argument("--ancho", type=int, default=1280); ap.add_argument("--alto", type=int, default=900)
    o = ap.parse_args()
    pngs = cuadros(o.url, o.seg, o.fps, o.selector, o.escala, o.ancho, o.alto)
    a_mp4(pngs, o.fps, o.salida)
    print(f"{len(pngs)} cuadros -> {o.salida}")


if __name__ == "__main__":
    main()
