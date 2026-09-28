"""Saca capturas reales de una web (página entera) para usarlas dentro de un video.

Uso:  .venv/Scripts/python herramientas/capturar_web.py <carpeta-del-video> <url> <nombre> [--ancho 1440] [--alto 900]
                                                    [--movil] [--oscuro] [--espera 2500] [--pantalla] [--secciones 6]

Guarda <carpeta>/capturas/<nombre>.png con la página ENTERA (o sólo lo visible con --pantalla).
--secciones N: para páginas que desplazan un contenedor interno (no la ventana): recorre el elemento con
más contenido desplazable y guarda N capturas de pantalla <nombre>_1.png … <nombre>_N.png.
--movil: 390×844 a escala 3 (como un teléfono). --oscuro: pide el tema oscuro (prefers-color-scheme).
Usa el Chrome instalado (Playwright, canal "chrome"), sin cuentas ni cookies: sólo páginas públicas
o servidores locales. Nunca iniciar sesión en producción para un video.
"""
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta"); ap.add_argument("url"); ap.add_argument("nombre")
    ap.add_argument("--ancho", type=int, default=1440); ap.add_argument("--alto", type=int, default=900)
    ap.add_argument("--movil", action="store_true"); ap.add_argument("--oscuro", action="store_true")
    ap.add_argument("--espera", type=int, default=2500); ap.add_argument("--pantalla", action="store_true")
    ap.add_argument("--secciones", type=int, default=0)
    a = ap.parse_args()
    salida = Path(a.carpeta) / "capturas" / f"{a.nombre}.png"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        opciones = dict(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True) if a.movil \
            else dict(viewport={"width": a.ancho, "height": a.alto}, device_scale_factor=1)
        ctx = nav.new_context(color_scheme="dark" if a.oscuro else "light", locale="es", **opciones)
        pag = ctx.new_page()
        pag.goto(a.url, wait_until="networkidle", timeout=60000)
        pag.wait_for_timeout(a.espera)
        if a.secciones:
            js = """(() => { let m = null, h = 0; for (const e of document.querySelectorAll('*')) { const s = getComputedStyle(e).overflowY;
                 if ((s === 'auto' || s === 'scroll') && e.scrollHeight - e.clientHeight > h) { h = e.scrollHeight - e.clientHeight; m = e; } }
                 window.__cont = m; return m ? [m.scrollHeight, m.clientHeight] : null; })()"""
            dims = pag.evaluate(js)
            total, vista = dims if dims else (pag.evaluate("document.documentElement.scrollHeight"), a.alto)
            for i in range(a.secciones):
                y = round(i * (total - vista) / max(1, a.secciones - 1))
                pag.evaluate(f"(window.__cont || document.scrollingElement).scrollTo(0, {y})"); pag.wait_for_timeout(1200)
                pag.screenshot(path=str(salida.with_name(f"{a.nombre}_{i + 1}.png")))
            print(salida.parent, a.secciones, "secciones de", total, pag.title()); nav.close(); return
        if not a.pantalla:                      # recorrer la página para que carguen las imágenes perezosas y animaciones
            alto = pag.evaluate("document.documentElement.scrollHeight")
            for y in range(0, alto, 600):
                pag.evaluate(f"window.scrollTo(0, {y})"); pag.wait_for_timeout(120)
            pag.evaluate("window.scrollTo(0, 0)"); pag.wait_for_timeout(600)
        pag.screenshot(path=str(salida), full_page=not a.pantalla)
        print(salida, pag.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]"), pag.title())
        nav.close()


if __name__ == "__main__":
    main()
