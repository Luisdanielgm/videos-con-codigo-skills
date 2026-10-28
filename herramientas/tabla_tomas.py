"""Revisa una tabla de tomas ANTES de escribir código: si no pasa, no se anima nada.

    .venv/Scripts/python herramientas/tabla_tomas.py <carpeta>/tomas.md [--total 24] [--estricto]
    .venv/Scripts/python herramientas/tabla_tomas.py --probar     # cada regla tiene su caso que dice «FALLA»

La tabla (plantilla en la skill `director-de-video`, «Tabla de tomas») es Markdown: una línea `Duración: 24 s` antes de la
tabla y una fila por toma con las columnas Tiempo · Héroe · Qué hace · Cámara · Texto en pantalla · Técnica.

Qué revisa, por toma (una línea «ok» o «FALLA» por toma, con lo que falla):
  tiempo      «a–b» legible (0–3, 3–7,5, 0:03–0:07,5) y empieza donde terminó la anterior (la primera en 0)
  duración    entre 0,5 s y 12 s; con --estricto (carril de modelos débiles) a lo sumo 8 s
  un tema     el héroe es UNA cosa que se puede señalar: no vacío, no una palabra de maqueta (título, texto, fondo,
              lista, tarjeta…) y sin enumerar dos (« y », comas, «+», «/»)
  acción      el héroe hace algo: no vacío ni sólo «aparece», «se muestra», «entra», «fundido»…
  texto       cabe en el tiempo de la toma: 0,3 s por palabra + 0,5 s (Motion Lab, @flxrnc), o sea
              palabras ≤ (duración − 0,5) / 0,3
  receta      la composición de la toma, UNA palabra de RECETAS (tarjeta, mecanismo, construccion, transformacion,
              comparacion, acercamiento, escala, dato, real)
Y para toda la tabla: la suma de las tomas es igual a la duración total (± 0,05 s); la columna Receta existe; las
tomas «tarjeta» (texto, cajas o íconos quietos) no pasan de TARJETA_MAX del tiempo ni de RACHA_TARJETA segundos
seguidos; y con MIN_TOMAS_VARIEDAD tomas o más hay al menos MIN_RECETAS recetas distintas. Es la guardia contra «puro cuadritos y texto» (idea de la skill
`vox-explainer` del repo comunitario de HyperFrames; calibrada con dos videos marcados «visual fuerte» contra dos
marcados «visual flojo»).
Sale con 1 si algo dice FALLA, con 2 si no encuentra la tabla o la duración.

Idea tomada de huashu-art-motion (alchaincyf, MIT): «镜头表» + `storyboard_lint.py` (tabla de tomas con lint antes del
código, y su carril para modelos que no son el más fuerte). Escrito de nuevo para este proyecto; sólo biblioteca estándar.
"""
import re
import sys
import unicodedata
from pathlib import Path

MIN_TOMA, MAX_TOMA, MAX_ESTRICTO = 0.5, 12.0, 8.0
SEG_PALABRA, SEG_FIJO = 0.3, 0.5
TOLERANCIA = 0.05
RECETAS = {
    "tarjeta": "texto, cajas, íconos o listas que aparecen y quedan quietos (lo narrado, escrito)",
    "mecanismo": "la cosa funcionando: proceso o máquina en marcha, con causa y efecto a la vista",
    "construccion": "algo se arma o se dibuja pieza por pieza frente a la cámara",
    "transformacion": "una forma se vuelve otra (se deforma, se despieza, se corta, cambia de estado)",
    "comparacion": "dos cosas a la misma escala, o antes y después",
    "acercamiento": "la cámara entra a una imagen u objeto y aísla una parte",
    "escala": "travesía de escala (de lo grande a lo chico o al revés)",
    "dato": "una cifra o gráfico que se calcula o crece en pantalla",
    "real": "material real recorrido (pantalla grabada, foto, archivo, modelo 3D de algo real)",
}
# Calibrado con tablas escritas a posteriori (sin saber la etiqueta) de 4 videos ya calificados: un explicativo médico
# en 3D («visual fuerte») tarjeta 27 % y racha 32 s; dos clases con diapositivas («flojo») 49 % / 48 s y 76 % / 132 s. Una
# pizarra de marketing («fuerte») da 54 % / 50 s y FALLA: su fuerza está en la pantalla real y los cortes, no en la
# composición (desacuerdo abierto). «No repetir receta seguida» se probó y se sacó: el explicativo médico la rompe
# 12 veces.
TARJETA_MAX, RACHA_TARJETA, MIN_RECETAS, MIN_TOMAS_VARIEDAD = 1 / 3, 40.0, 3, 5

MAQUETA = {"titulo", "subtitulo", "texto", "textos", "fondo", "lista", "vinetas", "vineta", "tarjeta", "tarjetas",
           "pantalla", "rotulo", "rotulos", "subtitulos", "diapositiva", "degradado", "icono", "iconos", "cartel",
           "plantilla", "contenido", "elementos", "efecto", "animacion", "nada", "negro", "vacio"}
DEBILES = {"aparece", "aparecen", "se", "muestra", "muestran", "mostrar", "ve", "ven", "entra", "entran", "sale",
           "salen", "esta", "estan", "queda", "quedan", "fundido", "fundidos", "con", "de", "en", "a", "y", "el",
           "la", "los", "las", "un", "una", "despacio", "poco", "luego", "aparecer", "presenta", "presentan"}


def plano(s):
    """minúsculas sin tildes (para comparar palabras)."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def segundos(s):
    s = s.strip().replace(",", ".")
    if ":" in s:
        m, x = s.split(":", 1)
        return int(m) * 60 + float(x)
    return float(s)


def tramo(celda):
    m = re.fullmatch(r"\s*([\d:.,]+)\s*[–—-]\s*([\d:.,]+)\s*(s|seg)?\s*", celda)
    if not m:
        return None
    try:
        return segundos(m.group(1)), segundos(m.group(2))
    except ValueError:
        return None


def celdas(linea):
    s = linea.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") else s
    return [c.strip() for c in s.split("|")]


def leer(texto):
    """Devuelve (total o None, encabezado, filas[(n_linea, celdas)]) de la primera tabla con columna de tiempo y héroe."""
    total, lineas, fuera = None, texto.splitlines(), False
    for ln in lineas:
        if ln.strip().startswith("```"):
            fuera = not fuera
            continue
        m = None if fuera else re.search(r"duraci[oó]n\s*(?:total)?\s*[:=]\s*([\d:.,]+)\s*s?\b", ln, re.I)
        if m and total is None:
            total = segundos(m.group(1))
    fuera, i = False, 0
    while i < len(lineas):
        ln = lineas[i]
        if ln.strip().startswith("```"):
            fuera = not fuera
            i += 1
            continue
        if not fuera and ln.strip().startswith("|") and i + 1 < len(lineas) and re.match(r"^\s*\|?\s*:?-{3,}", lineas[i + 1]):
            cab = [plano(c) for c in celdas(ln)]
            filas, j = [], i + 2
            while j < len(lineas) and lineas[j].strip().startswith("|"):
                filas.append((j + 1, celdas(lineas[j])))
                j += 1
            if any("tiempo" in c for c in cab) and any(("heroe" in c or "se ve" in c) for c in cab):
                return total, cab, filas
            i = j
            continue
        i += 1
    return total, None, []


def columna(cab, *claves):
    for k, c in enumerate(cab):
        if any(x in c for x in claves):
            return k
    return None


def palabras(s):
    return [p for p in re.split(r"\s+", s.strip()) if re.search(r"\w", p)]


def revisar(texto, total=None, estricto=False):
    """Lista de (caso, ok, detalle) y un error (str) si no se puede revisar."""
    t_doc, cab, filas = leer(texto)
    total = total if total is not None else t_doc
    if cab is None:
        return [], "no encuentro la tabla (hace falta un encabezado con «Tiempo» y «Héroe» o «Qué se ve»)"
    if total is None:
        return [], "falta la duración total (una línea «Duración: 24 s» antes de la tabla, o --total)"
    c_t, c_h = columna(cab, "tiempo"), columna(cab, "heroe", "se ve")
    c_a, c_x, c_r = columna(cab, "hace", "accion"), columna(cab, "texto"), columna(cab, "receta")
    tope = MAX_ESTRICTO if estricto else MAX_TOMA
    casos, fin_ant, suma = [], 0.0, 0.0
    por_receta, racha, racha_max = {}, 0.0, 0.0
    for n, (linea, c) in enumerate(filas, 1):
        c = c + [""] * (len(cab) - len(c))
        mal = []
        tr = tramo(c[c_t])
        if tr is None:
            casos.append((f"toma {n} (línea {linea})", False, f"tiempo ilegible «{c[c_t]}»"))
            continue
        a, b = tr
        dur = b - a
        suma += dur
        if abs(a - fin_ant) > TOLERANCIA:
            mal.append(f"empieza en {a:g} s y la anterior terminó en {fin_ant:g} s")
        fin_ant = b
        if dur < MIN_TOMA:
            mal.append(f"dura {dur:g} s (< {MIN_TOMA:g} s)")
        elif dur > tope:
            mal.append(f"dura {dur:g} s (> {tope:g} s{', carril estricto' if estricto else ''})")
        heroe = c[c_h]
        hp = [w for w in re.findall(r"\w+", plano(heroe))]
        if not hp:
            mal.append("sin héroe")
        elif all(w in MAQUETA or w in DEBILES for w in hp):
            mal.append(f"el héroe «{heroe}» es maqueta, no un objeto")
        elif re.search(r"\s(y|e)\s|[,;+/]", plano(heroe)):
            mal.append(f"dos temas en «{heroe}» (un solo héroe por toma)")
        if c_a is not None:
            ap = re.findall(r"\w+", plano(c[c_a]))
            if not ap or all(w in DEBILES for w in ap):
                mal.append(f"acción vacía o débil «{c[c_a]}» (¿qué hace el héroe?)")
        if c_x is not None:
            np_ = len(palabras(c[c_x]))
            cabe = max(0, int((dur - SEG_FIJO) / SEG_PALABRA + 1e-9))
            if np_ > cabe:
                mal.append(f"texto de {np_} palabras en {dur:g} s (caben {cabe})")
        if c_r is not None:
            r = plano(c[c_r]).strip()
            if r not in RECETAS:
                mal.append(f"receta «{c[c_r]}» fuera de la lista ({', '.join(RECETAS)})")
            else:
                por_receta[r] = por_receta.get(r, 0.0) + dur
                racha = racha + dur if r == "tarjeta" else 0.0
                racha_max = max(racha_max, racha)
        casos.append((f"toma {n} ({a:g}–{b:g} s)", not mal, "; ".join(mal)))
    if not filas:
        return [], "la tabla no tiene filas"
    casos.append(("suma de las tomas", abs(suma - total) <= TOLERANCIA,
                  f"{suma:g} s contra una duración total de {total:g} s"))
    if c_r is None:
        casos.append(("recetas", False, "falta la columna «Receta» (una palabra por toma: " + ", ".join(RECETAS) + ")"))
    elif suma > 0:
        tarjeta = por_receta.get("tarjeta", 0.0) / suma
        distintas = len(por_receta)
        mal = []
        if tarjeta > TARJETA_MAX + 1e-9:
            mal.append(f"«tarjeta» ocupa {tarjeta:.0%} del tiempo (tope {TARJETA_MAX:.0%})")
        if racha_max > RACHA_TARJETA + TOLERANCIA:
            mal.append(f"{racha_max:g} s seguidos de «tarjeta» (tope {RACHA_TARJETA:g} s)")
        if len(filas) >= MIN_TOMAS_VARIEDAD and distintas < MIN_RECETAS:
            mal.append(f"sólo {distintas} recetas distintas en {len(filas)} tomas (mínimo {MIN_RECETAS})")
        reparto = ", ".join(f"{k} {v / suma:.0%}" for k, v in sorted(por_receta.items(), key=lambda x: -x[1]))
        casos.append(("recetas", not mal, "; ".join(mal) + (" · " if mal else "") + reparto))
    return casos, None


def coma(s):
    return re.sub(r"(\d)\.(\d)", r"\1,\2", s)


def informe(casos):
    for caso, ok, det in casos:
        print(coma(f"{'ok   ' if ok else 'FALLA'}  {caso}" + (f": {det}" if det and (not ok or caso.startswith(('suma', 'recetas'))) else "")))
    nf = sum(not ok for _, ok, _ in casos)
    print(f"Total: {len(casos) - nf} ok, {nf} FALLA")
    return nf


EJEMPLO = """Video: Por qué hierve el agua · Duración: 20 s · Formato: 16:9
Estilo: canvas plano, tinta azul sobre papel crema, un solo acento naranja

| Tiempo | Héroe (qué se ve) | Qué hace | Cámara | Texto en pantalla | Técnica | Receta |
|---|---|---|---|---|---|---|
| 0–3 | la olla en la hornalla | la llama se enciende debajo | quieta | | 1 canvas | mecanismo |
| 3–7 | una molécula de agua | vibra cada vez más rápido | acercamiento rápido | Más calor, más vibración | 1 canvas | acercamiento |
| 7–11,5 | la burbuja del fondo | nace en una raya de la olla y sube | paneo | | 1 canvas | mecanismo |
| 11,5–15 | el termómetro | la aguja se clava en 100 grados | golpe | 100 °C | 1 canvas | dato |
| 15–20 | la olla | hierve entera y el vapor tapa el cuadro | se aleja | Al nivel del mar | 1 canvas | transformacion |
"""

ROTURAS = [  # (qué se rompe, texto viejo, texto nuevo, estricto, caso que tiene que fallar); viejo y nuevo pueden ser listas
    ("toma de 9 s en el carril estricto", "| 15–20 | la olla |", "| 15–24 | la olla |", True, "toma 5"),
    ("dos héroes en una toma", "| una molécula de agua |", "| una molécula y la llama |", False, "toma 2"),
    ("héroe que es maqueta", "| el termómetro |", "| título |", False, "toma 4"),
    ("acción débil", "| vibra cada vez más rápido |", "| aparece |", False, "toma 2"),
    ("texto que no cabe", "| Más calor, más vibración |", "| Cuanto más calor le das al agua más rápido vibra cada molécula |",
     False, "toma 2"),
    ("hueco entre tomas", "| 7–11,5 |", "| 8–11,5 |", False, "toma 3"),
    ("suma distinta del total", "Duración: 20 s", "Duración: 22 s", False, "suma de las tomas"),
    ("receta fuera de la lista", "| golpe | 100 °C | 1 canvas | dato |", "| golpe | 100 °C | 1 canvas | bonita |", False, "toma 4"),
    ("racha de tarjeta", ["Duración: 20 s", "| 15–20 | la olla |", "| 1 canvas | transformacion |"],
     ["Duración: 61 s", "| 15–61 | la olla |", "| 1 canvas | tarjeta |"], False, "recetas"),  # 41 s seguidos (tope 40)
    ("demasiada tarjeta", ["| 1 canvas | acercamiento |", "| 1 canvas | dato |"],
     ["| 1 canvas | tarjeta |", "| 1 canvas | tarjeta |"], False, "recetas"),   # 7,5 s de 20 = 38 %
    ("poca variedad", ["| 1 canvas | dato |", "| 1 canvas | transformacion |"],
     ["| 1 canvas | acercamiento |", "| 1 canvas | mecanismo |"], False, "recetas"),
    ("sin columna Receta", [" Receta |\n|---|---|---|---|---|---|---|"], ["\n|---|---|---|---|---|---|"], False, "recetas"),
]


def probar():
    """La tabla de ejemplo pasa entera; cada rotura hace fallar justo su caso. Si una regla se apaga, esto da FALLA."""
    bien = True
    casos, err = revisar(EJEMPLO)
    ok = err is None and casos and all(c[1] for c in casos)
    print(f"{'ok   ' if ok else 'FALLA'}  ejemplo sano: {len(casos)} casos, ninguno falla")
    bien &= bool(ok)
    casos, err = revisar(EJEMPLO, estricto=True)
    ok = err is None and all(c[1] for c in casos)
    print(f"{'ok   ' if ok else 'FALLA'}  ejemplo sano en el carril estricto")
    bien &= bool(ok)
    for nombre, viejo, nuevo, estricto, debe in ROTURAS:
        roto = EJEMPLO
        for v, w in zip(*((viejo, nuevo) if isinstance(viejo, list) else ([viejo], [nuevo]))):
            assert roto.count(v) == 1, v
            roto = roto.replace(v, w)
        casos, err = revisar(roto, estricto=estricto)
        caidos = [c for c, ok_, _ in casos if not ok_]
        ok = err is None and any(c.startswith(debe) for c in caidos)
        print(coma(f"{'ok   ' if ok else 'FALLA'}  rotura «{nombre}» → falla {'; '.join(caidos) or 'nada'}"))
        bien &= ok
    _, err = revisar(EJEMPLO.replace("Duración: 20 s", "Formato: 20 s"))
    ok = err is not None
    print(f"{'ok   ' if ok else 'FALLA'}  sin duración total → no revisa ({err})")
    bien &= ok
    print("PRUEBA", "PASA" if bien else "FALLA")
    return bien


if __name__ == "__main__":
    args = sys.argv[1:]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args[:1] == ["--probar"]:
        sys.exit(0 if probar() else 1)
    if not args or args[0].startswith("-"):
        print(__doc__)
        sys.exit(2)
    total = float(args[args.index("--total") + 1].replace(",", ".")) if "--total" in args else None
    ruta = Path(args[0])
    if not ruta.is_file():
        print(f"no existe {ruta}")
        sys.exit(2)
    casos, err = revisar(ruta.read_text(encoding="utf-8"), total, "--estricto" in args)
    if err:
        print(err)
        sys.exit(2)
    sys.exit(1 if informe(casos) else 0)
