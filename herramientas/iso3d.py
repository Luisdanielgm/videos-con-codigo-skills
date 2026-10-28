"""Guardias de la técnica 26 en 3D (variante ISO-GLOW 3D): lector y limpieza de .glb, un solo acento, encuadre, vista
isométrica verdadera, resplandor real y determinismo. Sobre herramientas/iso3d.js y sus dos páginas
(26-maquina-isometrica/glow-indice y glow-glb), abiertas con Playwright (el Chrome instalado).

    .venv/Scripts/python herramientas/iso3d.py --probar        (cada caso: ok o FALLA; sale con 1 si alguno falla)
    .venv/Scripts/python herramientas/iso3d.py glb <archivo.glb> [--acentos "luz|lamp"] [--objetivo 4]
                                                  # restiliza un .glb de verdad y dice qué quitó, qué quedó y dónde cae en el cuadro
Casos de --probar (cada uno se rompe a propósito con mutar.py antes de creerle):
  lector      un .glb armado aquí (nodos con traslación, giro y escala, hijo de un nodo girado, índices de 16 y de 32 bits)
              sale con la misma caja que calcula numpy con las mismas matrices
  limpieza    vértices repetidos soldados (24 → 8 por cubo), triángulos degenerados fuera, texturas y materiales tirados
              (quedan ≤ 2 materiales y ninguno con textura), centrado, base en y = 0, lado mayor = objetivo
  comprimido  un .glb con Draco/meshopt se rechaza con un mensaje que dice qué hacer, no con un cuadro negro
  acentos     sólo las mallas cuyo nombre coincide con la expresión quedan encendidas
  un-acento   en el ejemplo, exactamente una pieza encendida en cada instante (cada 0,25 s)
  encuadre    ninguna pieza visible sale del cuadro (el ejemplo, y el .glb dando la vuelta entera)
  isometrica  la vista termina en 45° / 35,264° exactos y la guardia ve la diferencia cuando no lo es
  resplandor  alrededor de lo encendido hay más luz con el resplandor que sin él
  efectos     cada sonido por contacto cae 1 cuadro (1/30 s ±1 ms) después de que la imagen cambia (un cajón empieza a abrirse,
              se enciende la pestaña, la punta o la luz del cajón buscado), comprobado con ISO3D_REGISTRO y ISO3D_TIEMPOS
  explorable  los botones y el selector accionan la búsqueda y la sonda cae en el cajón buscado (cajones abiertos y pestaña)
  consola     ninguna página (visor, ejemplo, vertical, explorable) da errores de consola; una página que no queda lista es FALLA
  determinismo el cuadro no depende del orden en que se piden (herramientas/determinismo.py): las cinco fases en horizontal
              y las de «sin», «con» y «cierre» en vertical
"""
import base64
import json
import struct
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
INDICE = "26-maquina-isometrica/glow-indice"
VISOR = "26-maquina-isometrica/glow-glb"
W, H = 1920, 1080


class Pagina:
    _pw = None      # un solo Playwright para todas las páginas (con dos abiertos a la vez, el segundo falla)

    def __init__(self, carpeta, params="auditar=1"):
        from playwright.sync_api import sync_playwright
        self.errores = []
        if Pagina._pw is None:
            Pagina._pw = sync_playwright().start()
        self._p = Pagina._pw
        self.nav = self._p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files", "--enable-unsafe-swiftshader"])
        self.pag = self.nav.new_page(viewport={"width": W, "height": H})
        self.pag.on("console", lambda m: m.type == "error" and self.errores.append(m.text))
        self.pag.on("pageerror", lambda e: self.errores.append(str(e)))
        try:
            self.pag.goto((RAIZ / carpeta / "index.html").as_uri() + "?" + params)
            self.pag.wait_for_function("window.ISO_LISTA === true", timeout=30000)
        except Exception:
            self.nav.close()        # que el navegador no quede abierto si la página no llega a estar lista
            raise

    def __call__(self, expr, *args):
        return self.pag.evaluate(expr, args[0] if len(args) == 1 else list(args)) if args else self.pag.evaluate(expr)

    def cerrar(self):
        self.nav.close()


# ───────── un .glb armado aquí (con respuesta conocida) ─────────
def cubo_suelto():
    """Cubo de lado 1 con 24 vértices (4 por cara, como lo exportan muchos programas) y 12 triángulos + 1 degenerado."""
    caras = [((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
             ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
             ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1))]
    v = np.array([p for c in caras for p in c], np.float32)
    i = [k * 4 + o for k in range(6) for o in (0, 1, 2, 0, 2, 3)] + [0, 0, 1]
    return v, i


def trs(t=(0, 0, 0), q=(0, 0, 0, 1), s=(1, 1, 1)):
    x, y, z, w = q
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R @ np.diag(s); M[:3, 3] = t
    return M


NODOS = [dict(name="cuerpo", mesh=0, translation=[10, 0, 0], scale=[2, 1, 1]),
         dict(name="giro", rotation=[0, float(np.sin(np.pi / 4)), 0, float(np.cos(np.pi / 4))], children=[2]),
         dict(name="luz", mesh=1, translation=[1, 0, 0], scale=[.5, .5, .5])]


def armar(u32=False, comprimido=False):
    v, ind = cubo_suelto()
    pos = v.tobytes()
    idx = np.array(ind, np.uint32 if u32 else np.uint16).tobytes()
    idx += b"\0" * (-len(idx) % 4)
    j = dict(asset=dict(version="2.0"), scene=0, scenes=[dict(nodes=[0, 1])], nodes=NODOS,
             meshes=[dict(name="cuerpo", primitives=[dict(attributes=dict(POSITION=0), indices=1, material=0)]),
                     dict(name="luz", primitives=[dict(attributes=dict(POSITION=0), indices=1, material=0)])],
             materials=[dict(name="pintura", pbrMetallicRoughness=dict(baseColorTexture=dict(index=0)))],
             images=[dict(uri="textura.png")], textures=[dict(source=0)],
             accessors=[dict(bufferView=0, componentType=5126, count=24, type="VEC3"),
                        dict(bufferView=1, componentType=5125 if u32 else 5123, count=len(ind), type="SCALAR")],
             bufferViews=[dict(buffer=0, byteOffset=0, byteLength=len(pos)), dict(buffer=0, byteOffset=len(pos), byteLength=len(idx))],
             buffers=[dict(byteLength=len(pos) + len(idx))])
    if comprimido:
        j["extensionsRequired"] = ["KHR_draco_mesh_compression"]
    js = json.dumps(j).encode(); js += b" " * (-len(js) % 4)
    binario = pos + idx
    cuerpo = struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binario), 0x004E4942) + binario
    return struct.pack("<III", 0x46546C67, 2, 12 + len(cuerpo)) + cuerpo


def esperado(objetivo):
    """Caja del fixture con las mismas matrices en numpy: (tamaño ya escalado, vértices soldados, triángulos útiles)."""
    v, _ = cubo_suelto()
    h = np.c_[v, np.ones(len(v))]
    M0 = trs(t=(10, 0, 0), s=(2, 1, 1))
    Mg = trs(q=NODOS[1]["rotation"]); M2 = Mg @ trs(t=(1, 0, 0), s=(.5, .5, .5))
    todo = np.vstack([(M0 @ h.T).T[:, :3], (M2 @ h.T).T[:, :3]])
    tam = todo.max(0) - todo.min(0)
    return tam * objetivo / tam.max(), todo


def b64(b):
    return base64.b64encode(b).decode()


# ───────── los casos ─────────
D_EFECTO = 1 / 30      # el sonido cae un cuadro (a 30 fps) después del instante en que la imagen cambia
PX_MOVIDO = 3          # un cajón «se movió» si cambia más de esto (px) respecto de la base entre dos instantes (la cámara deriva < 1 px)


def probar():
    casos = []
    def caso(bien, texto):
        casos.append(bool(bien))
        print(f"  {'ok' if bien else 'FALLA'}  {texto}")

    def con_pagina(nombre, carpeta, params, f):
        """Abre la página, corre f(página) y la cierra pase lo que pase; una excepción (p. ej. la página que nunca queda lista)
        es un FALLA con su causa, no un traceback, y los errores de consola de la página también son un FALLA."""
        p = None
        try:
            p = Pagina(carpeta, params)
            f(p)
            caso(not p.errores, f"errores de consola ({nombre}): {len(p.errores)} {[x[:90] for x in p.errores[:2]]}")
        except Exception as ex:
            caso(False, f"{nombre}: excepción {type(ex).__name__}: {(str(ex).strip().splitlines() or [''])[0][:140]}")
        finally:
            if p is not None:
                p.cerrar()

    objetivo = 4
    tam_esp, _ = esperado(objetivo)

    def visor(p):
        r16 = p.pag.evaluate("([b, o]) => ISO3D_RESTILIZAR(b, o)", [b64(armar()), {"acentos": "luz", "objetivo": objetivo}])
        mat = p("ISO3D_MATERIALES")
        r32 = p.pag.evaluate("([b, o]) => ISO3D_RESTILIZAR(b, o)", [b64(armar(u32=True)), {"objetivo": objetivo}])
        def num(x):
            try:
                a = np.array(x, float)
                return a if np.isfinite(a).all() else None
            except (TypeError, ValueError):
                return None
        tam16, tam32 = num(r16["tam"]), num(r32["tam"])
        min_esp = np.array([-tam_esp[0] / 2, 0, -tam_esp[2] / 2]); max_esp = np.array([tam_esp[0] / 2, tam_esp[1], tam_esp[2] / 2])
        def igual(r, t):
            mn, mx = num(r["caja"]["min"]), num(r["caja"]["max"])
            return t is not None and mn is not None and mx is not None and np.allclose(mn, min_esp, atol=2e-3) and np.allclose(mx, max_esp, atol=2e-3)
        caso(igual(r16, tam16) and igual(r32, tam32),
             f"lector: caja {r16['caja']['min']}..{r16['caja']['max']} (numpy {np.round(min_esp, 3).tolist()}..{np.round(max_esp, 3).tolist()}), índices de 16 y de 32 bits iguales")
        tam16 = tam16 if tam16 is not None else np.zeros(3)
        caso(r16["antes"]["vertices"] == 48 and r16["despues"]["vertices"] == 16 and r16["antes"]["triangulos"] == 26 and r16["despues"]["triangulos"] == 24,
             f"limpieza: vértices {r16['antes']['vertices']} → {r16['despues']['vertices']}, triángulos {r16['antes']['triangulos']} → {r16['despues']['triangulos']} (esperado 48 → 16 y 26 → 24)")
        caso(r16["texturas"] == 1 and r16["materiales"] == 1 and mat["conMapa"] == 0 and mat["distintos"] <= 4,
             f"limpieza: {r16['texturas']} textura y {r16['materiales']} material tirados; quedan {mat['distintos']} materiales, {mat['conMapa']} con textura")
        c = r16["caja"]
        caso(abs(max(tam16) - objetivo) < 2e-3 and r16["piezas"] == 2 and abs(c["min"][1]) < 1e-4 and abs(c["min"][0] + c["max"][0]) < 1e-3 and abs(c["min"][2] + c["max"][2]) < 1e-3,
             f"limpieza: lado mayor {max(tam16):.3f} (objetivo {objetivo}), base en y = {c['min'][1]:.4f}, centrado en x y z ({(c['min'][0] + c['max'][0]) / 2:.4f}, {(c['min'][2] + c['max'][2]) / 2:.4f}), {r16['piezas']} piezas")
        caso(r16["acentos"] == ["luz/luz"], f"acentos: encendidas {r16['acentos']} (esperado ['luz/luz']: nodo/malla)")
        try:
            p("ISO3D_RESTILIZAR", b64(armar(comprimido=True)))
            caso(False, "comprimido: se aceptó un .glb con Draco")
        except Exception as e:
            caso("comprimido" in str(e), f"comprimido: rechazado con «{str(e).splitlines()[0][-110:]}»")
    con_pagina("visor", VISOR, "auditar=1", visor)

    def giro(pg):          # encuadre del .glb dando la vuelta entera
        pg.pag.evaluate("([b, o]) => ISO3D_RESTILIZAR(b, o)", [b64(armar()), {"objetivo": objetivo}])
        fuera = []
        for t in np.linspace(0, 12, 13):
            for x in pg("ISO3D_REGISTRO", float(t)):
                if x["visible"] and (x["x0"] < 0 or x["x1"] > W or x["y0"] < 0 or x["y1"] > H):
                    fuera.append((round(float(t), 1), x["nombre"]))
        caso(not fuera, f"encuadre (.glb girando): {len(fuera)} piezas fuera del cuadro {fuera[:2]}")
    con_pagina("visor girando", VISOR, "auditar=1&giro=1", giro)

    dur = 14.0             # lo reemplaza la duración que dice la página del ejemplo

    def ejemplo(e):
        nonlocal dur
        dur = float(e("() => ISO3D_DURACION"))
        ts = np.arange(0, dur, .25)
        cuentas = [sum(1 for x in e("ISO3D_REGISTRO", float(t)) if x["visible"] and x["acento"]) for t in ts]
        mal = [(float(t), n) for t, n in zip(ts, cuentas) if n != 1]
        caso(not mal, f"un-acento: exactamente 1 pieza encendida en los {len(ts)} instantes (fuera de regla: {mal[:3]})")
        fuera = []
        for t in ts:
            for x in e("ISO3D_REGISTRO", float(t)):
                if x["visible"] and (x["x0"] < 0 or x["x1"] > W or x["y0"] < 0 or x["y1"] > H):
                    fuera.append((float(t), x["nombre"]))
        caso(not fuera, f"encuadre (ejemplo): {len(fuera)} piezas fuera del cuadro {fuera[:2]}")
        d_fin = [e("ISO3D_DESVIO", t) for t in (dur - 1.5, dur - .2)]
        d_ini = e("ISO3D_DESVIO", 0)
        caso(max(d_fin) < .01 and d_ini > 5, f"isométrica: desvío {max(d_fin):.4f}° al final y {d_ini:.1f}° al principio (la guardia los distingue)")
        # el resplandor: más luz en un anillo alrededor de lo encendido
        t = 9.3
        luz = [x for x in e("ISO3D_REGISTRO", t) if x["visible"] and x["acento"]][0]
        sin, con = (np.asarray(Image.open(BytesIO(base64.b64decode(e("ISO3D_BRILLO", t, b).split(",")[1]))).convert("L"), np.float32) for b in (0, .5))
        x0, x1, y0, y1 = (int(luz[k]) for k in ("x0", "x1", "y0", "y1"))
        m = 30
        anillo = np.zeros((H, W), bool); anillo[max(0, y0 - m):y1 + m, max(0, x0 - m):x1 + m] = True; anillo[y0:y1, x0:x1] = False
        mas = float((con - sin)[anillo].mean())
        caso(mas > 2, f"resplandor: el anillo de {m} px alrededor de «{luz['nombre']}» gana {mas:.1f} niveles de gris con el resplandor")
        efectos_con_imagen(e, caso, dur)
    con_pagina("ejemplo", INDICE, "auditar=1", ejemplo)

    # vertical (1080×1920): nada visible sale del cuadro, en todo el video
    def vertical(v):
        fuera_v = [(float(t), x["nombre"]) for t in np.arange(0, dur, .5) for x in v("ISO3D_REGISTRO", float(t))
                   if x["visible"] and (x["x0"] < 0 or x["x1"] > 1080 or x["y0"] < 0 or x["y1"] > 1920)]
        caso(not fuera_v, f"encuadre (vertical 1080×1920): {len(fuera_v)} piezas fuera del cuadro {fuera_v[:2]}")
    con_pagina("vertical", INDICE, "auditar=1&formato=vertical", vertical)

    # explorable: los botones accionan la búsqueda (sin índice abre hasta el cajón buscado; con índice, uno) y el selector cambia el cajón;
    # además la sonda cae donde se busca: qué cajones se abrieron y qué pestaña se encendió en cada búsqueda
    def explorable(x):
        def buscar(accion):
            x.pag.click(f"[data-accion={accion}]")
            n = 1 if accion == "sin" else 2
            x.pag.wait_for_function(f"window.ISO3D_EXPLORAR() && window.ISO3D_EXPLORAR().res[{n}] != null", timeout=15000)
            return x("() => ISO3D_EXPLORAR()")
        a1 = buscar("sin"); a2 = buscar("con")
        x.pag.select_option("select", index=1)          # el cajón 2 (por valor, Playwright calzaba «1» con el texto del cajón 1)
        b1 = buscar("sin"); b2 = buscar("con")
        r1, r2, s1, s2 = a1["res"]["1"], a2["res"]["2"], b1["res"]["1"], b2["res"]["2"]
        caso((r1, r2, s1, s2) == (5, 1, 2, 1), f"explorable: sin índice abre {r1} (cajón 5) y {s1} (cajón 2); con índice abre {r2} y {s2} (esperado 5, 1, 2, 1)")
        # sin índice: se abren, en orden, todos los cajones hasta el buscado; con índice: sólo el buscado y su pestaña
        esp = [(a1, 4, [0, 1, 2, 3, 4], []), (a2, 4, [4], [4]), (b1, 1, [0, 1], []), (b2, 1, [1], [1])]
        caso(all(r["buscado"] == bu and r["abiertos"] == ab and r["pestanas"] == pe for r, bu, ab, pe in esp),
             f"explorable: cajones abiertos {a1['abiertos']} y {a2['abiertos']} (pestaña {a2['pestanas']}) buscando el 5; {b1['abiertos']} y {b2['abiertos']} (pestaña {b2['pestanas']}) buscando el 2")
    con_pagina("explorable", INDICE, "explorar=1", explorable)

    # el cuadro no depende del orden: instantes de las cinco fases (gancho, sin, cuenta, con, cierre) y también el vertical
    for etiqueta, params, ts in (("horizontal", [], "1,4.3,9.5,12,22,28"), ("vertical", ["--params", "formato=vertical"], "6,13,22,28")):
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "herramientas" / "determinismo.py"), INDICE, "--instantes", ts, *params],
                               capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, timeout=900)
            caso(r.returncode == 0, f"determinismo ({etiqueta}, {ts}): " + (r.stdout.strip().splitlines() or ["sin salida"])[-1])
        except Exception as ex:
            caso(False, f"determinismo ({etiqueta}): excepción {type(ex).__name__}: {str(ex)[:140]}")
    print(f"  {sum(casos)} ok, {len(casos) - sum(casos)} FALLA")
    return all(casos)


def efectos_con_imagen(e, caso, dur):
    """Los sonidos por contacto contra la imagen que de verdad dibuja la página: cada sonido cae D_EFECTO (1 cuadro) después del
    instante en que la imagen cambia (un cajón empieza a abrirse, o se enciende la pestaña, la punta o la luz del cajón buscado).
    Los instantes salen de los tiempos de la escena (ISO3D_TIEMPOS) y se comprueban con ISO3D_REGISTRO: la imagen sigue cerrada
    en ese instante y ya cambió un cuadro después. Un efecto que falta, que sobra o que cae en otro cuadro es FALLA."""
    ef = e("() => ISO3D_EFECTOS")
    ti = e("() => ISO3D_TIEMPOS")
    def rel(t, nombre):          # la pieza respecto de la base (así la deriva lenta de la cámara casi no cuenta)
        reg = e("ISO3D_REGISTRO", float(t))
        base = next(x for x in reg if x["nombre"] == "base")
        for x in reg:
            if x["nombre"] == nombre:
                return x["x0"] - base["x0"], x["y0"] - base["y0"], x["visible"]
        raise RuntimeError(f"la pieza «{nombre}» no está en el registro")
    def movido(t, nombre, ref):  # ¿cuántos px se movió respecto del instante ref (con el cajón cerrado)?
        a, b = rel(t, nombre), rel(ref, nombre)
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    def visible(t, nombre):
        return rel(t, nombre)[2]
    esperados, malos = [], []    # instantes en que la imagen cambia; y lo que no coincide con los tiempos de la escena
    for i in range(ti["hasta"]):                       # cada cajón que se abre antes de la fase «con índice»
        ini = ti["tA"] + i * ti["paso"] + .3
        nombre = f"cajón {i + 1}"
        if movido(ini + D_EFECTO, nombre, ini - .05) > PX_MOVIDO:
            if movido(ini, nombre, ini - .05) > PX_MOVIDO:
                malos.append(f"{nombre} ya está abierto en {ini:.2f} s")
            esperados.append(ini)
    tB, b = ti["tB"], ti["buscado"] + 1
    for ini, nombre in ((tB + .1, f"pestaña luz {b}"), (tB + 1.0, "punta luz"), (tB + 1.8, f"luz {b}")):
        if visible(ini - .001, nombre) or not visible(ini, nombre):
            malos.append(f"«{nombre}» no se enciende en {ini:.2f} s")
        esperados.append(ini)
    en = sorted(x["en"] for x in ef)
    esp = sorted(i + D_EFECTO for i in esperados)
    parejos = len(en) == len(esp) and all(abs(a - c) <= .001 for a, c in zip(en, esp))
    caso(ef and not malos and parejos and all(0 < x < dur for x in en),
         f"efectos: {len(ef)} sonidos (esperados {len(esp)} por la imagen), cada uno 1 cuadro (1/30 s ±1 ms) después de que la imagen cambia"
         + (f"; la imagen no coincide con los tiempos: {malos[:2]}" if malos else "")
         + (f"; sonidos en {[round(x, 3) for x in en]} contra {[round(x, 3) for x in esp]}" if not parejos else ""))


def glb(ruta, acentos=None, objetivo=4.0):
    p = Pagina(VISOR)
    r = p.pag.evaluate("([b, o]) => ISO3D_RESTILIZAR(b, o)", [b64(Path(ruta).read_bytes()), {"acentos": acentos, "objetivo": objetivo}])
    print(f"{ruta}\n  vértices {r['antes']['vertices']} → {r['despues']['vertices']} · triángulos {r['antes']['triangulos']:.0f} → {r['despues']['triangulos']:.0f}"
          f" · tiradas {r['texturas']} texturas y {r['materiales']} materiales · {r['piezas']} piezas · caja {np.round(r['tam'], 2).tolist()} · encendidas {r['acentos'] or 'ninguna'}")
    fuera = [x["nombre"] for t in (0,) for x in p("ISO3D_REGISTRO", t) if x["visible"] and (x["x0"] < 0 or x["x1"] > W or x["y0"] < 0 or x["y1"] > H)]
    print(f"  piezas fuera del cuadro: {len(fuera)}" + (f" {fuera[:3]}" if fuera else ""))
    if p.errores:
        print("  errores de consola:", p.errores[:3])
    p.cerrar()
    return not fuera and not p.errores


def efectos(carpeta):
    """Los sonidos por contacto de la escena (ISO3D_EFECTOS, 1 cuadro después de la imagen) → <carpeta>/efectos.json para mezclar.py."""
    p = Pagina(carpeta)
    try:
        ef = p("() => ISO3D_EFECTOS")
    finally:
        p.cerrar()
    (RAIZ / carpeta / "efectos.json").write_text(json.dumps(ef, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ef)} efectos → {carpeta}/efectos.json")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")        # con la salida redirigida Windows usa cp1252 y «→» tumbaba el caso del visor
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    if len(sys.argv) > 2 and sys.argv[1] == "efectos":
        sys.exit(efectos(sys.argv[2]))
    if len(sys.argv) > 2 and sys.argv[1] == "glb":
        a = sys.argv
        sys.exit(0 if glb(a[2], a[a.index("--acentos") + 1] if "--acentos" in a else None,
                          float(a[a.index("--objetivo") + 1]) if "--objetivo" in a else 4.0) else 1)
    print(__doc__)
