"""Guardias y utilidades de la técnica 26 (máquina isométrica), sobre lo que la escena dibuja de verdad.

La página de la escena, con ?auditar=1, expone ISO_AUDITAR(t) → el registro de herramientas/iso.js (sólidos con su caja
3D, silueta y bordes en pantalla y orden de dibujo; líneas con sus extremos; terminales; textos; encendidos; ciclos).
Este script lo abre con Playwright (el Chrome instalado, sin bajar navegadores) y juzga en Python.

    .venv/Scripts/python herramientas/maquina_iso.py auditar <carpeta> [--instantes 3,21.5] [--params "tema=claro"]
    .venv/Scripts/python herramientas/maquina_iso.py cerca <carpeta> --t 25 [--zoom 4] [--puntos "800,400;920,515"]
    .venv/Scripts/python herramientas/maquina_iso.py efectos <carpeta>        # → <carpeta>/efectos.json (mezclar.py)
    .venv/Scripts/python herramientas/maquina_iso.py paquete <carpeta>        # → render/paquetes/<técnica>_<video>/
    .venv/Scripts/python herramientas/maquina_iso.py --probar                 # cada guardia, rota a propósito

Guardias (adaptadas de Anatomy, wheresryan22/anatomy, MIT: su audit.mjs y lines.mjs, reescritas para Canvas 2D):
  lineas    ninguna línea termina en el aire: cada extremo cae en un borde, un punto, otra línea o una pieza que toca
            (o queda tapado por una pieza dibujada después). Libres sólo las marcadas: rótulos, puntas de aguja.
  orden     orden del pintor: donde dos siluetas se pisan y una cara de separación dice cuál está detrás, ésa se dibujó antes
  cruces    ninguna pieza ni cable atraviesa otra (cajas 3D que se meten > 0,5 unidades) y el orden no tiene ciclos
  acento    un solo grupo encendido por cuadro
  texto90   todo texto dentro del 90 % central del cuadro
  encimados ningún texto pisa otro texto (el subtítulo cuenta)
  sobre     ningún texto pisa el dibujo, salvo el grabado en su propia placa
  piezas    la máquina tiene ≥ 40 piezas (nombres distintos; un cable cuenta una vez)
Sale con código 1 si algún instante dice FALLA. Instantes por omisión: uno por frase de tiempos.js, al 70 %.
Los primeros planos a 4× (cerca) no se juzgan solos: la hoja se mira entera, junta por junta.
"""
import base64
import io
import json
import re
import shutil
import sys
from pathlib import Path

for _f in (sys.stdout, sys.stderr):
    _f.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
RENDER = RAIZ / "render"
W, H = 1920, 1080
TOL = 2.0              # px: un extremo «cae» en algo si queda a esta distancia
SOLAPE = 0.75          # px: dos siluetas se pisan si se meten más que esto
METIDO = 0.5           # unidades del mundo: dos cajas 3D se cruzan si se meten más que esto en los tres ejes
MIN_PIEZAS = 40


# ───────── geometría 2D ─────────
def dist_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    k = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - k * dx) ** 2 + (py - ay - k * dy) ** 2) ** .5


def en_poligono(poli, p):
    x, y = p; dentro = False; j = len(poli) - 1
    for i in range(len(poli)):
        xi, yi = poli[i]; xj, yj = poli[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def solapan(A, B, margen=SOLAPE):
    """Dos polígonos convexos se pisan más que `margen` (ejes separadores)."""
    for P in (A, B):
        for i in range(len(P)):
            x1, y1 = P[i]; x2, y2 = P[(i + 1) % len(P)]
            nx, ny = y1 - y2, x2 - x1
            n = (nx * nx + ny * ny) ** .5
            if n < 1e-9:
                continue
            nx, ny = nx / n, ny / n
            pa = [x * nx + y * ny for x, y in A]; pb = [x * nx + y * ny for x, y in B]
            if min(max(pa), max(pb)) - max(min(pa), min(pb)) <= margen:
                return False
    return True


def rect_poli(c):
    x, y, w, h = c
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


# ───────── 3D: ¿quién está detrás? (la misma regla que iso.js) ─────────
def detras(A, B, v, eps=0.01):
    r = 0
    for k in range(3):
        vk = v[k]
        if abs(vk) < 1e-6:
            continue
        a_det = A[k + 3] <= B[k] + eps if vk > 0 else A[k] >= B[k + 3] - eps
        b_det = B[k + 3] <= A[k] + eps if vk > 0 else B[k] >= A[k + 3] - eps
        if a_det and not b_det:
            if r == -1:
                return 0
            r = 1
        elif b_det and not a_det:
            if r == 1:
                return 0
            r = -1
    return r


def metidos(A, B):
    return all(min(A[k + 3], B[k + 3]) - max(A[k], B[k]) > METIDO for k in range(3))


def parientes(a, b):
    """Pares que se tocan a propósito: el mismo cable, una pieza adentro de otra, un cable con lo que toca."""
    if a.get("cable") and a.get("cable") == b.get("cable"):
        return True
    for x, y in ((a, b), (b, a)):
        if x.get("dentro") and x["dentro"] in (y["nombre"], y.get("grupo")):
            return True
        if x.get("cable") and (y["nombre"] in x.get("toca", []) or y.get("grupo") in x.get("toca", [])):
            return True
    return False


# ───────── las guardias (cada una devuelve la lista de problemas) ─────────
def g_lineas(reg):
    malos = []
    sol, ter, lin = reg["solidos"], reg["terminales"], reg["lineas"]
    for i, l in enumerate(lin):
        if l.get("libre") is True or l.get("cerrada"):
            continue
        extremos = [l["pts"][0]] if l.get("libre") == "fin" else [l["pts"][0], l["pts"][-1]]
        for p in extremos:
            if any(dist_seg(p, (t["x"], t["y"]), (t["x"], t["y"])) <= t["r"] + TOL for t in ter):
                continue
            if any(dist_seg(p, b[:2], b[2:]) <= TOL for s in sol for b in s["bordes"]):
                continue
            if any(j != i and any(dist_seg(p, o["pts"][k], o["pts"][k + 1]) <= TOL for k in range(len(o["pts"]) - 1))
                   for j, o in enumerate(lin)):
                continue
            toca = l.get("toca") or []
            if any((s["nombre"] in toca or s.get("grupo") in toca) and en_poligono(s["sil"], p) for s in sol):
                continue
            if any(s["orden"] > l["orden"] and en_poligono(s["sil"], p) for s in sol):
                continue          # tapado por algo que se dibuja después
            malos.append(f"«{l['nombre']}» termina en el aire en ({p[0]:.0f}, {p[1]:.0f})")
    return malos


def g_orden(reg):
    malos, v, S = [], reg["camara"]["v"], reg["solidos"]
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            a, b = S[i], S[j]
            if parientes(a, b) or not solapan(a["sil"], b["sil"]):
                continue
            d = detras(a["aabb"], b["aabb"], v)
            atras, adelante = (a, b) if d == 1 else (b, a) if d == -1 else (None, None)
            if atras and atras["orden"] > adelante["orden"]:
                malos.append(f"«{atras['nombre']}» está detrás de «{adelante['nombre']}» y se dibujó después")
    return malos


def g_cruces(reg):
    malos, S = [], reg["solidos"]
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            a, b = S[i], S[j]
            if not parientes(a, b) and metidos(a["aabb"], b["aabb"]):
                malos.append(f"«{a['nombre']}» y «{b['nombre']}» se atraviesan")
    for n in reg.get("ciclos", []):
        malos.append(f"el orden del pintor tiene un ciclo (roto en «{n}»)")
    return malos


def g_acento(reg):
    e = reg.get("encendidos", [])
    return [f"{len(e)} acentos encendidos a la vez: {', '.join(e)}"] if len(e) > 1 else []


def g_texto90(reg):
    x0, y0, x1, y1 = .05 * W, .05 * H, .95 * W, .95 * H
    return [f"«{t['texto']}» sale del 90 % central" for t in reg["textos"]
            if t["caja"][0] < x0 or t["caja"][1] < y0 or t["caja"][0] + t["caja"][2] > x1 or t["caja"][1] + t["caja"][3] > y1]


def g_encimados(reg):
    T, malos = reg["textos"], []
    for i in range(len(T)):
        for j in range(i + 1, len(T)):
            a, b = T[i], T[j]
            if a.get("grupo") and a.get("grupo") == b.get("grupo"):
                continue
            if solapan(rect_poli(a["caja"]), rect_poli(b["caja"]), 0):
                malos.append(f"«{a['texto']}» pisa «{b['texto']}»")
    return malos


def g_sobre(reg):
    """Un texto de pantalla no pisa ninguna pieza. Uno grabado (sobre=pieza) cabe entero en su pieza y nada que se
    dibuje después lo tapa."""
    malos = []
    for t in reg["textos"]:
        R = t.get("poli") or rect_poli(t["caja"])
        if t.get("sobre"):
            casa = [s for s in reg["solidos"] if s["nombre"] == t["sobre"]]
            if not casa or not all(en_poligono(casa[0]["sil"], p) for p in R):
                malos.append(f"«{t['texto']}» no cabe en su placa «{t['sobre']}»")
            otros = [s for s in reg["solidos"] if s["orden"] > t["orden"]]
        else:
            otros = reg["solidos"]
        for s in otros:
            if solapan(R, s["sil"], SOLAPE):
                malos.append(f"«{t['texto']}» pisa la pieza «{s['nombre']}»")
                break
    return malos


def g_piezas(reg):
    n = len({s.get("cable") or s["nombre"] for s in reg["solidos"]})
    return [] if n >= MIN_PIEZAS else [f"sólo {n} piezas (mínimo {MIN_PIEZAS})"]


GUARDIAS = [("lineas", g_lineas), ("orden", g_orden), ("cruces", g_cruces), ("acento", g_acento),
            ("texto90", g_texto90), ("encimados", g_encimados), ("sobre", g_sobre), ("piezas", g_piezas)]


def juzgar(reg):
    return [(n, f(reg)) for n, f in GUARDIAS]


# ───────── la página ─────────
class Pagina:
    def __init__(self, carpeta, params=""):
        from playwright.sync_api import sync_playwright
        self.carpeta = carpeta.replace("\\", "/").strip("/")
        url = (RAIZ / self.carpeta / "index.html").as_uri() + "?auditar=1" + ("&" + params if params else "")
        self.errores = []
        self._p = sync_playwright().start()
        self.nav = self._p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        self.pag = self.nav.new_page(viewport={"width": W, "height": H})
        self.pag.on("console", lambda m: m.type == "error" and self.errores.append(m.text))
        self.pag.on("pageerror", lambda e: self.errores.append(str(e)))
        self.pag.goto(url)
        self.pag.wait_for_function("window.ISO_LISTA === true", timeout=30000)

    def __call__(self, expr, *args):
        if not args:
            return self.pag.evaluate(expr)
        return self.pag.evaluate(expr, args[0] if len(args) == 1 else list(args))

    def cerrar(self):
        self.nav.close(); self._p.stop()


def tiempos_de(carpeta):
    txt = (RAIZ / carpeta / "tiempos.js").read_text(encoding="utf-8")
    return json.loads(re.search(r"=\s*(\{.*\})\s*;", txt, re.S).group(1))


def auditar(carpeta, instantes=None, params=""):
    if not instantes:
        T = tiempos_de(carpeta)
        instantes = [round(T["seg"][i]["inicio"] + .7 * T["seg"][i]["dur"], 2) for i in T["orden"]]
    pag = Pagina(carpeta, params)
    malos_total, n = 0, 0
    try:
        for t in instantes:
            reg = pag("t => ISO_AUDITAR(t)", t)
            res = juzgar(reg)
            piezas = len({s.get("cable") or s["nombre"] for s in reg["solidos"]})
            print(f"t = {t:6.2f} s · {piezas} piezas, {len(reg['solidos'])} sólidos, {len(reg['lineas'])} líneas, {len(reg['textos'])} textos")
            for nombre, malos in res:
                n += 1
                print(f"  {'ok' if not malos else 'FALLA':5s} {nombre:9s}" + (f" {len(malos)}: " + " · ".join(malos[:3]) if malos else ""))
                malos_total += bool(malos)
    finally:
        errores = pag.errores
        pag.cerrar()
    for e in errores:
        print("error de consola:", e)
    print(f"TOTAL: {n - malos_total} ok, {malos_total} FALLA" + (" · FALLA: errores de consola" if errores else ""))
    return 1 if malos_total or errores else 0


def cerca(carpeta, t, zoom=4, puntos=None, params=""):
    from PIL import Image, ImageDraw
    pag = Pagina(carpeta, params)
    try:
        if not puntos:
            reg = pag("t => ISO_AUDITAR(t)", t)
            cand = []
            for l in reg["lineas"]:
                if l.get("cable") or l["nombre"] == "brazo":
                    cand += [l["pts"][0], l["pts"][-1]]
            cand += [[x["x"], x["y"]] for x in reg["terminales"] if "@" in x["nombre"]]
            for s in reg["solidos"]:
                if s.get("lit"):
                    xs = [p[0] for p in s["sil"]]; ys = [p[1] for p in s["sil"]]
                    cand.append([(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2])
            puntos = []
            for p in cand:                                     # sin repetir lo que ya entra en otra toma
                if all(abs(p[0] - q[0]) > W / zoom / 3 or abs(p[1] - q[1]) > H / zoom / 3 for q in puntos):
                    puntos.append(p)
            puntos = puntos[:12]
        tomas = []
        for x, y in puntos:
            url = pag("a => ISO_CERCA(a[0], a[1], a[2], a[3])", t, x, y, zoom)
            tomas.append(((x, y), Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGB")))
    finally:
        errores = pag.errores
        pag.cerrar()
    cw, ch, cols = 640, 360, 4
    filas = (len(tomas) + cols - 1) // cols
    hoja = Image.new("RGB", (cw * cols, ch * filas), (20, 20, 20))
    d = ImageDraw.Draw(hoja)
    for i, ((x, y), im) in enumerate(tomas):
        hoja.paste(im.resize((cw, ch)), ((i % cols) * cw, (i // cols) * ch))
        d.text(((i % cols) * cw + 8, (i // cols) * ch + 6), f"{zoom:g}x en ({x:.0f}, {y:.0f})", fill=(255, 220, 120))
    nombre = carpeta.replace("\\", "/").strip("/").replace("/", "_")
    salida = RENDER / "capturas" / f"hoja_cerca_{nombre}_{str(t).replace('.', '-')}.jpg"
    salida.parent.mkdir(parents=True, exist_ok=True)
    hoja.save(salida, quality=90)
    print(f"{len(tomas)} primeros planos a {zoom}× → {salida}")
    for e in errores:
        print("error de consola:", e)
    return 1 if errores else 0


def efectos(carpeta):
    pag = Pagina(carpeta)
    try:
        ef = pag("() => ISO_EFECTOS")
    finally:
        pag.cerrar()
    (RAIZ / carpeta / "efectos.json").write_text(json.dumps(ef, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ef)} efectos → {carpeta}/efectos.json")
    return 0


def vtt(T):
    def ts(s):
        h, r = divmod(s, 3600); m, r = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{r:06.3f}"
    out = ["WEBVTT", ""]
    for i, k in enumerate(T["orden"], 1):
        s = T["seg"][k]
        out += [str(i), f"{ts(s['inicio'])} --> {ts(s['inicio'] + s['dur'])}", s["texto"], ""]
    return "\n".join(out)


def paquete(carpeta):
    """La escena como paquete de código para una pizarra interactiva: sin video renderizado."""
    carpeta = carpeta.replace("\\", "/").strip("/")
    src = RAIZ / carpeta
    dst = RENDER / "paquetes" / carpeta.replace("/", "_")
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "lib").mkdir(parents=True)
    T = tiempos_de(carpeta)
    shutil.copy2(RAIZ / "herramientas" / "iso.js", dst / "lib" / "iso.js")
    for n in ("escena.js", "tiempos.js", "guion.json", "hechos.md", "narracion.wav", "efectos.json", "mezcla.wav"):
        if (src / n).exists():
            shutil.copy2(src / n, dst / n)
    (dst / "subtitulos.vtt").write_text(vtt(T), encoding="utf-8")
    ficha = {
        "tecnica": "26 máquina isométrica", "skill": ".claude/skills/video-maquina-isometrica/SKILL.md",
        "escena": "escena.js", "global": "Escenas." + carpeta.split("/")[-1], "dependencias": ["lib/iso.js"],
        "lienzo": [W, H], "duracion": T["total"], "audio": "mezcla.wav" if (src / "mezcla.wav").exists() else "narracion.wav",
        "voz_sola": "narracion.wav", "tiempos": "tiempos.js", "subtitulos": "subtitulos.vtt", "fuentes": "hechos.md",
        "contrato": {"crear": "Escenas.<nombre>.crear(canvas, { tema, tiempos }) → escena",
                     "video": "escena.render(t): cuadro puro de t, sin subtítulos",
                     "interactivo": "escena.explorar() → detener()",
                     "guardias": "escena.registro(t) → herramientas/maquina_iso.py"},
        "temas": ["oscuro", "claro"], "leyenda": {"acento": "la pieza encendida es la que hay que mirar (una sola)",
                                                  "1": "cliente", "2": "servidor", "3": "caché", "4": "base de datos"},
        "frases": [{"id": k, **T["seg"][k]} for k in T["orden"]],
    }
    (dst / "manifiesto.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"paquete → {dst} ({len(list(dst.rglob('*')))} archivos)")
    return 0


# ───────── se rompe a propósito ─────────
def _cam(p):
    c30 = 3 ** .5 / 2
    return [960 + (p[0] - p[1]) * c30, 540 + (p[0] + p[1]) * .5 - p[2]]


def _caja(nombre, x, y, z, w, d, h, orden, **extra):
    P = lambda a, b, c: _cam([a, b, c])
    caras = [[P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)],
             [P(x + w, y + d, z), P(x, y + d, z), P(x, y + d, z + h), P(x + w, y + d, z + h)],
             [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]]
    pts = sorted({tuple(p) for c in caras for p in c})

    def casco(P):
        cruz = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lo, hi = [], []
        for p in P:
            while len(lo) >= 2 and cruz(lo[-2], lo[-1], p) <= 0: lo.pop()
            lo.append(p)
        for p in reversed(P):
            while len(hi) >= 2 and cruz(hi[-2], hi[-1], p) <= 0: hi.pop()
            hi.append(p)
        return [list(p) for p in lo[:-1] + hi[:-1]]
    s = {"nombre": nombre, "grupo": nombre, "tipo": "caja", "aabb": [x, y, z, x + w, y + d, z + h], "sil": casco(pts),
         "bordes": [c[i] + c[(i + 1) % 4] for c in caras for i in range(4)], "orden": orden, "lit": False}
    s.update(extra)
    return s


def _reg(**k):
    r = {"camara": {"v": [1, 1, 1], "giro": 0}, "solidos": [], "lineas": [], "terminales": [], "textos": [], "encendidos": [], "ciclos": []}
    r.update(k)
    return r


_JS_PIEZA = r"""
const vm = require('vm'), fs = require('fs');
const sandbox = { window: {}, Math };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), sandbox);
const Iso = sandbox.window.Iso;
const ctx = new Proxy({}, { get: (_, k) => k === 'measureText' ? () => ({ width: 10 }) : () => ctx, set: () => true });
const cam = Iso.camara({ escala: 1, cx: 960, cy: 540 });
const E = Iso.escena(cam, Iso.TEMAS.oscuro);
E.caja({ x: 0, y: 0, z: 0, w: 40, d: 40, h: 10 }, { nombre: 'base' });
E.pieza([0, 0, 10, 10, 10, 50], { nombre: 'aguja' }, () => {});
Iso.grabar(cam); E.pintar(ctx);
process.stdout.write(JSON.stringify(Iso.terminar()));
"""


def _registro_iso_real(node="node"):
    """Lo que iso.js registra de verdad (corrido en Node con un lienzo falso): una caja y una pieza a medida.
    Si Node falta, tarda de más o contesta algo que no es JSON, devuelve un registro vacío con el motivo en «error»
    (el caso dice FALLA con la razón, en vez de romper la prueba entera)."""
    import subprocess
    try:
        sal = subprocess.run([node, "-e", _JS_PIEZA, str(RAIZ / "herramientas" / "iso.js")], capture_output=True, text=True,
                             encoding="utf-8", timeout=60)
        if sal.returncode == 0 and sal.stdout:
            return json.loads(sal.stdout)
        return {"solidos": [], "error": sal.stderr[-300:] or "node no devolvió nada"}
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:      # FileNotFoundError, tiempo agotado, JSON malo
        return {"solidos": [], "error": f"{type(e).__name__}: {e}"[:300]}


def g_pieza_registrada(reg):
    """E.pieza (brazo, aguja) también entra al registro: sin eso las guardias de orden y cruces no la ven."""
    return [] if any(s.get("tipo") == "pieza" for s in reg.get("solidos", [])) else [f"E.pieza no se registró ({reg.get('error', '')})"]


def probar():
    A = _caja("atras", 0, 0, 0, 40, 40, 40, 0)
    B = _caja("adelante", 45, 0, 0, 40, 40, 30, 1)               # a la derecha en x: queda adelante y se pisan en pantalla
    B_mal = dict(B, orden=-1)
    C_metida = _caja("metida", 20, 20, 10, 40, 40, 40, 2)
    tocando = _caja("encima", 0, 0, 40, 40, 40, 10, 2)
    muchas = [_caja(f"p{i}", 100 * i, 0, 0, 10, 10, 10, i) for i in range(45)]
    pocas = muchas[:12]
    e1, e2 = _cam([0, 0, 40]), _cam([40, 0, 40])                # arista de la tapa de A
    aire = _cam([20, 20, 90])
    cable = lambda pts, orden=5: {"nombre": "cable", "pts": [_cam(p) for p in pts], "libre": False, "cerrada": False, "toca": [], "orden": orden}
    tubo_por = _caja("cable#0", -20, 18, 18, 80, 4, 4, 3, cable="cable")
    tubo_al_lado = _caja("cable#0", -20, 48, 18, 10, 4, 4, 3, cable="cable")
    txt = lambda s, x, y, w=200, h=40, **k: {"texto": s, "caja": [x, y, w, h], "orden": 9, **k}
    casos = [
        ("lineas: borde a borde", g_lineas, _reg(solidos=[A], lineas=[cable([[0, 0, 40], [40, 0, 40]])]), "ok"),
        ("lineas: termina en el aire", g_lineas, _reg(solidos=[A], lineas=[{"nombre": "suelta", "pts": [e1, aire], "libre": False, "orden": 5}]), "FALLA"),
        ("lineas: punta libre marcada", g_lineas, _reg(solidos=[A], lineas=[{"nombre": "aguja", "pts": [e1, aire], "libre": "fin", "orden": 5}]), "ok"),
        ("lineas: cae en un terminal", g_lineas, _reg(solidos=[A], terminales=[{"x": aire[0], "y": aire[1], "r": 3, "nombre": "t"}],
                                                     lineas=[{"nombre": "cable", "pts": [e2, aire], "libre": False, "orden": 5}]), "ok"),
        ("orden: lo de atrás antes", g_orden, _reg(solidos=[A, B]), "ok"),
        ("orden: lo de atrás después", g_orden, _reg(solidos=[A, B_mal]), "FALLA"),
        ("cruces: apoyada encima", g_cruces, _reg(solidos=[A, tocando]), "ok"),
        ("cruces: metida en otra", g_cruces, _reg(solidos=[A, C_metida]), "FALLA"),
        ("cruces: cable al lado", g_cruces, _reg(solidos=[A, tubo_al_lado]), "ok"),
        ("cruces: cable que atraviesa", g_cruces, _reg(solidos=[A, tubo_por]), "FALLA"),
        ("cruces: ciclo en el orden", g_cruces, _reg(solidos=[A], ciclos=["atras"]), "FALLA"),
        ("acento: uno", g_acento, _reg(encendidos=["capsula"]), "ok"),
        ("acento: dos", g_acento, _reg(encendidos=["capsula", "reloj"]), "FALLA"),
        ("texto90: adentro", g_texto90, _reg(textos=[txt("a", 100, 100)]), "ok"),
        ("texto90: afuera", g_texto90, _reg(textos=[txt("a", 1800, 100)]), "FALLA"),
        ("encimados: separados", g_encimados, _reg(textos=[txt("a", 100, 100), txt("b", 100, 200)]), "ok"),
        ("encimados: uno sobre otro", g_encimados, _reg(textos=[txt("a", 100, 100), txt("b", 150, 120)]), "FALLA"),
        ("sobre: lejos del dibujo", g_sobre, _reg(solidos=[A], textos=[txt("a", 100, 100)]), "ok"),
        ("sobre: encima de una pieza", g_sobre, _reg(solidos=[A], textos=[txt("a", 900, 500, 80, 30)]), "FALLA"),
        ("sobre: grabado en su placa", g_sobre, _reg(solidos=[A], textos=[txt("a", 945, 512, 30, 16, sobre="atras")]), "ok"),
        ("sobre: grabado que se sale", g_sobre, _reg(solidos=[A], textos=[txt("a", 900, 500, 80, 30, sobre="atras")]), "FALLA"),
        ("piezas: 45", g_piezas, _reg(solidos=muchas), "ok"),
        ("piezas: 12", g_piezas, _reg(solidos=pocas), "FALLA"),
        ("pieza a medida: iso.js la registra", g_pieza_registrada, _registro_iso_real(), "ok"),
        ("pieza a medida: sin registrar", g_pieza_registrada, _reg(solidos=[A]), "FALLA"),
        ("pieza a medida: sin node", g_pieza_registrada, _registro_iso_real("node-que-no-existe"), "FALLA"),
    ]
    bien = 0
    for nombre, f, reg, esperado in casos:
        dicho = "FALLA" if f(reg) else "ok"
        paso = dicho == esperado
        bien += paso
        print(f"  {dicho:5s} {nombre:32s} (esperado {esperado}) {'PASA' if paso else 'NO PASA'}")
    print(f"PRUEBA: {bien}/{len(casos)} casos como se esperaba → {'PASA' if bien == len(casos) else 'FALLA'}")
    return 0 if bien == len(casos) else 1


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if "--probar" in a:
        sys.exit(probar())
    if len(a) < 2 or a[0] not in ("auditar", "cerca", "efectos", "paquete"):
        sys.exit(__doc__)
    modo, carpeta = a[0], a[1].replace("\\", "/").strip("/")
    if modo == "auditar":
        ins = [float(x) for x in opt("--instantes").split(",")] if opt("--instantes") else None
        sys.exit(auditar(carpeta, ins, opt("--params", "")))
    if modo == "cerca":
        pts = [[float(v) for v in p.split(",")] for p in opt("--puntos").split(";")] if opt("--puntos") else None
        sys.exit(cerca(carpeta, float(opt("--t", "10")), float(opt("--zoom", "4")), pts, opt("--params", "")))
    if modo == "efectos":
        sys.exit(efectos(carpeta))
    sys.exit(paquete(carpeta))


if __name__ == "__main__":
    main()
