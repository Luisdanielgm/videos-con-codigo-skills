"""Prueba de los efectos de herramientas/efectos/: determinismo, errores de consola y tiempo por cuadro a 1920×1080.

Uso:  .venv/Scripts/python herramientas/efectos/probar.py [efecto ...]

Por cada efecto, en el instante T de la tabla de abajo:
  1. página nueva → huella (SHA-256 de los píxeles) A, tiempo del primer cuadro (frío: las simulaciones calculan
     todos los pasos desde 0) y de 5 cuadros siguientes (caliente: lo normal al exportar); luego vuelve a T
     (para las simulaciones es un salto hacia atrás: sale de un cuadro clave) → huella A2;
  2. otra página nueva → huella B;
  3. otra página que dibuja primero t = 1 y después salta a T → huella C.
  Determinista = A, A2, B y C iguales. Guarda una captura PNG por efecto en herramientas/efectos/capturas/.
Levanta herramientas/servidor.py en el puerto 8791 (o VIDEOS_PUERTO) y usa el Chrome instalado (Playwright).
Sale con código 1 si algún efecto no es determinista o dejó errores en la consola.
"""
import base64
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
CAPTURAS = Path(__file__).resolve().parent / "capturas"
PUERTO = int(os.environ.get("VIDEOS_PUERTO", "8791"))
BASE = f"http://localhost:{PUERTO}/herramientas/efectos/demo.html"
INSTANTES = {"disolver": 2.0, "armar": 2.0, "velocidad": 1.3, "velocidad3d": 1.3, "vidrio": 2.5,
             "physarum": 8.0, "grayscott": 8.0, "marmoleado": 9.5, "causticas": 3.0}
EXTRA = {"disolver": [1.2], "physarum": [3.0], "grayscott": [3.0], "marmoleado": [6.0, 14.4]}   # sólo capturas


def arriba():
    try:
        urllib.request.urlopen(f"http://localhost:{PUERTO}/AGENTS.md", timeout=2)
        return True
    except Exception:
        return False


def main():
    nombres = sys.argv[1:] or list(INSTANTES)
    CAPTURAS.mkdir(exist_ok=True)
    srv = None
    if not arriba():
        srv = subprocess.Popen([sys.executable, str(RAIZ / "herramientas" / "servidor.py"), str(PUERTO)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            if arriba():
                break
            time.sleep(.2)
    errores, filas, ok = [], [], True
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", args=["--enable-unsafe-swiftshader", "--hide-scrollbars"])
        ctx = nav.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)

        def pagina(url):
            pg = ctx.new_page()
            pg.on("console", lambda m: m.type == "error" and errores.append(f"{url}: {m.text}"))
            pg.on("pageerror", lambda e: errores.append(f"{url}: {e}"))
            pg.add_init_script("addEventListener('error', () => window.__ERR = true); addEventListener('unhandledrejection', () => window.__ERR = true);")
            pg.goto(url, wait_until="load", timeout=120000)
            pg.wait_for_function("window.LISTO === true || window.__ERR === true", timeout=600000, polling=200)
            if not pg.evaluate("window.LISTO === true"):
                time.sleep(.3)
                raise SystemExit(f"la página falló: {url}\n" + "\n".join(errores))
            return pg

        for n in nombres:
            T = INSTANTES[n]
            url = f"{BASE}?efecto={n}&t={T}"
            a = pagina(url)
            if n == nombres[0]:
                gpu = a.evaluate("""(() => { const g = document.createElement('canvas').getContext('webgl2');
                    const e = g && g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'sin dato'; })()""")
                print("WebGL:", gpu)
            h_a = a.evaluate("DEMO.huella()")
            frio = a.evaluate("window.MS_PRIMER_CUADRO")
            (CAPTURAS / f"{n}_{T}.png").write_bytes(base64.b64decode(a.evaluate("DEMO.png()").split(",")[1]))
            calientes = sorted(a.evaluate(f"[1,2,3,4,5].map(k => DEMO.medir({T} + k / 30))"))
            a.evaluate(f"DEMO.render({T})")
            h_a2 = a.evaluate("DEMO.huella()")
            for te in EXTRA.get(n, []):
                a.evaluate(f"DEMO.render({te})")
                (CAPTURAS / f"{n}_{te}.png").write_bytes(base64.b64decode(a.evaluate("DEMO.png()").split(",")[1]))
            a.close()
            b = pagina(url)
            h_b = b.evaluate("DEMO.huella()")
            b.close()
            c = pagina(f"{BASE}?efecto={n}&t=1")
            c.evaluate(f"DEMO.render({T})")
            h_c = c.evaluate("DEMO.huella()")
            c.close()
            igual = h_a == h_a2 == h_b == h_c
            ok &= igual
            filas.append((n, T, "ok" if igual else "FALLA", frio, calientes[2], h_a[:12]))
            print(f"{n:12s} t={T:<5} {'ok' if igual else 'FALLA'}  frío {frio:8.1f} ms  caliente {calientes[2]:7.1f} ms  {h_a[:12]}"
                  + ("" if igual else f"  (A2 {h_a2[:12]}, B {h_b[:12]}, C {h_c[:12]})"), flush=True)
        # el modo que recorre todos
        pg = pagina(f"{BASE}?t=20")
        print("todos: total", pg.evaluate("DEMO.total"), "s, lista", pg.evaluate("DEMO.lista.join(', ')"))
        pg.close()
        nav.close()
    if srv:
        srv.kill()
    for e in errores:
        print("error de consola:", e)
    print(f"{sum(f[2] == 'ok' for f in filas)}/{len(filas)} deterministas, {len(errores)} errores de consola")
    sys.exit(0 if ok and not errores else 1)


if __name__ == "__main__":
    main()
