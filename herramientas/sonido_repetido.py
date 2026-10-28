"""Qué efectos y qué música usa cada pieza, y la guardia que avisa cuando una mezcla nueva suena como las recientes.

    .venv/Scripts/python herramientas/sonido_repetido.py                    # medición: conteo por archivo y tabla por pieza
    .venv/Scripts/python herramientas/sonido_repetido.py --informe <md>     # además la escribe en Markdown
    .venv/Scripts/python herramientas/sonido_repetido.py <carpeta>          # guardia: ¿repite canción o efectos de las recientes?
    .venv/Scripts/python herramientas/sonido_repetido.py --probar
    --raiz <repo>   lee las mezclas de otro checkout (en un worktree faltan los efectos.json de Manim, que no van a git)

Por qué: la música y los efectos de todos los videos sonaban siempre iguales. Lee cada mezcla.json (sus `efectos`, el
`efectos_de` y la `cancion`; `musica.json` o una pista `extra` musica*.wav cuentan como herramientas/musica.py). Una pieza es su
carpeta sin `/horizontal`, `/vertical` ni `-v2`: los formatos y versiones de una misma pieza pueden repetir sin aviso.
Recientes = las RECIENTES piezas cuya mezcla.json entró antes a git (las que no están en git cuentan como de ahora).
La guardia avisa si la pieza nueva usa una canción de una reciente, o si su set de efectos se parece a uno reciente
(Jaccard >= PARECIDO sobre los archivos distintos). mezclar.py la llama al final: avisa, no corta la mezcla.
"""
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RECIENTES = 12          # unas tres semanas de marketing (3 videos por semana por producto)
PARECIDO = 0.5          # Jaccard de sets de efectos desde el que dos piezas «suenan igual»
CALCULADA = "herramientas/musica.py (calculada)"


def recursos(raiz):
    r = raiz / "recursos"
    return r if r.exists() else Path(r"recursos")    # en un worktree, la carpeta recursos/ del directorio actual


def pieza_de(rel):
    """Carpeta de la pieza sin el formato ni la versión: marketing/x/semana-06/lunes/horizontal → marketing/x/semana-06/lunes."""
    rel = re.sub(r"/(horizontal|vertical)$", "", rel)
    return re.sub(r"-v\d+$", "", rel)


def normal(a, raiz):
    a = a.replace("\\", "/")
    p = Path(a)
    if p.is_absolute():
        for base in (recursos(raiz) / "efectos" / "listos", raiz):
            try:
                return p.relative_to(base).as_posix()
            except ValueError:
                pass
        return a
    for pre in ("recursos/efectos/listos/", "recursos/efectos/"):
        if a.startswith(pre):
            return a[len(pre):]
    return a.lstrip("./")


def leer(carpeta, raiz):
    """{efectos: [archivo por uso], musica: [fuentes]} de una carpeta con mezcla.json."""
    m = json.loads((carpeta / "mezcla.json").read_text(encoding="utf-8"))
    usos = list(m.get("efectos", []))
    if "efectos_de" in m and (carpeta / m["efectos_de"]).exists():
        extra = json.loads((carpeta / m["efectos_de"]).read_text(encoding="utf-8"))
        usos += extra.get("efectos", []) if isinstance(extra, dict) else extra
    musica = []
    if "cancion" in m:
        musica.append(normal(m["cancion"]["archivo"], raiz))
    for x in m.get("extra", []):
        nombre = Path(x["archivo"]).name
        if nombre.startswith("musica"):
            musica.append(CALCULADA)
        elif not nombre.startswith("silencio"):
            musica.append(normal(str(carpeta / x["archivo"]), raiz))         # pista propia: su ruta en el repo
    if (carpeta / "musica.json").exists() and CALCULADA not in musica:
        musica.append(CALCULADA)
    return {"efectos": [normal(e["archivo"], raiz) for e in usos], "musica": sorted(set(musica))}


def fechas(raiz):
    """Instante en que cada mezcla.json entró a git (la primera vez)."""
    r = subprocess.run(["git", "-C", str(raiz), "log", "--diff-filter=A", "--name-only", "--format=@%ct", "--", "*mezcla.json"],
                       capture_output=True, text=True, encoding="utf-8")
    out, t = {}, None
    for linea in r.stdout.splitlines():
        if linea.startswith("@"):
            t = int(linea[1:])
        elif linea.strip():
            out[linea.strip()] = t            # git log va del más nuevo al más viejo: queda la primera vez
    return out


def piezas(raiz=RAIZ):
    raiz = Path(raiz).resolve()
    f = fechas(raiz)
    ahora = time.time()
    lista = []
    # en git: las que están y las nuevas que no se ignoran (fuera tmp/ y pruebas); sin git, todas
    r = subprocess.run(["git", "-C", str(raiz), "ls-files", "--cached", "--others", "--exclude-standard", "--", "*mezcla.json"],
                       capture_output=True, text=True, encoding="utf-8")
    rutas = sorted(raiz / l for l in r.stdout.splitlines()) if r.returncode == 0 else sorted(raiz.rglob("mezcla.json"))
    for ruta in rutas:
        if not ruta.exists():
            continue
        rel = ruta.relative_to(raiz).as_posix()
        if any(p.startswith(".") or p in ("node_modules", "externos", "recursos") for p in rel.split("/")):
            continue
        try:
            d = leer(ruta.parent, raiz)
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError) as e:
            print(f"  (se salta {rel}: {type(e).__name__})")
            continue
        carpeta = ruta.parent.relative_to(raiz).as_posix()
        # sin git (las pruebas) vale la fecha del archivo; en git, lo que todavía no entró es de ahora
        d.update(carpeta=carpeta, pieza=pieza_de(carpeta), fecha=f[rel] if rel in f else ahora if f else os.path.getmtime(ruta))
        d["propios"] = [e for e in d["efectos"] if e.startswith(d["pieza"] + "/")]
        lista.append(d)
    return lista


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def revisar(carpeta, todas, recientes=RECIENTES, parecido=PARECIDO):
    """Avisos (lista de textos) para la pieza de `carpeta` frente a las `recientes` piezas más nuevas que no son ella."""
    yo = next(p for p in todas if p["carpeta"] == carpeta)
    otras = {}
    for p in sorted(todas, key=lambda p: -p["fecha"]):
        if p["pieza"] != yo["pieza"] and p["fecha"] <= yo["fecha"]:
            otras.setdefault(p["pieza"], p)          # una por pieza: su formato o versión más nueva
        if len(otras) >= recientes:
            break
    avisos = []
    for p in otras.values():
        for c in set(yo["musica"]) & set(p["musica"]):
            avisos.append(f"repite la música {c} de {p['carpeta']}")
        if len(set(yo["efectos"])) >= 3:
            j = jaccard(yo["efectos"], p["efectos"])
            if j >= parecido:
                comunes = sorted(set(yo["efectos"]) & set(p["efectos"]))
                avisos.append(f"repite el set de efectos de {p['carpeta']} (Jaccard {j:.2f}: {', '.join(comunes[:4])}"
                              f"{'…' if len(comunes) > 4 else ''})")
    return avisos


def avisar(carpeta, raiz=RAIZ):
    """Lo que llama mezclar.py: imprime los avisos y nunca corta."""
    try:
        raiz = Path(raiz).resolve()
        rel = Path(carpeta).resolve().relative_to(raiz).as_posix()
        av = revisar(rel, piezas(raiz))
    except (ValueError, StopIteration, OSError):
        return []                                     # carpeta fuera del repo (pruebas) o sin mezcla.json
    for a in av:
        print(f"AVISO sonido repetido: {a}")
    if av:
        print("  (kit propio: herramientas/kit_efectos.py; canción: ver «Música» en la skill video-lanzamiento)")
    return av


def medir(raiz=RAIZ, informe=None):
    raiz = Path(raiz).resolve()
    todas = piezas(raiz)
    usos, en_piezas = Counter(), defaultdict(set)
    for p in todas:
        for e in p["efectos"]:
            if e not in p["propios"]:
                usos[e] += 1
                en_piezas[e].add(p["pieza"])
    mus = defaultdict(set)
    for p in todas:
        for c in p["musica"]:
            mus[c].add(p["pieza"])
    indice = recursos(raiz) / "efectos" / "indice.json"
    banco = [e["archivo"][len("listos/"):] for e in json.loads(indice.read_text(encoding="utf-8"))] if indice.exists() else []
    nombres_piezas = {p["pieza"] for p in todas}
    con_kit = {p["pieza"] for p in todas if p["propios"]}
    sin_musica = {p["pieza"] for p in todas if not p["musica"]}
    total = sum(usos.values())
    L = [f"# Sonido repetido: medición del {time.strftime('%d-%m-%Y')}", "",
         f"Medido con `herramientas/sonido_repetido.py --raiz {raiz.name}`: {len(todas)} `mezcla.json` en {len(nombres_piezas)} piezas "
         f"(una pieza = su carpeta sin formato ni versión). {total} usos de efectos compartidos; "
         f"{len(con_kit)} piezas con kit propio; {len(sin_musica)} piezas sin música.", "",
         "## Efectos compartidos por archivo", "", "| Usos | Piezas | % de los usos | Archivo |", "|---:|---:|---:|---|"]
    for e, n in usos.most_common():
        L.append(f"| {n} | {len(en_piezas[e])} | {100 * n / max(total, 1):.1f} | `{e}` |")
    sin_usar = [b for b in banco if b not in usos]
    L += ["", f"Del banco (`recursos/efectos/indice.json`, {len(banco)} sonidos) nunca se usaron {len(sin_usar)}: "
          + ", ".join(f"`{b}`" for b in sin_usar), "",
          "## Música por fuente", "", "| Piezas | Fuente |", "|---:|---|"]
    for c, ps in sorted(mus.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {len(ps)} | `{c}` |")
    L += [f"| {len(sin_musica)} | (sin música) |", "", "## Por pieza (de la más nueva a la más vieja)", "",
          "| Entró | Carpeta | Música | Usos | Distintos | Propios | Aviso de la guardia |", "|---|---|---|---:|---:|---:|---|"]
    for p in sorted(todas, key=lambda p: -p["fecha"]):
        av = revisar(p["carpeta"], todas)
        L.append(f"| {time.strftime('%d-%m', time.localtime(p['fecha']))} | `{p['carpeta']}` | "
                 f"{', '.join(Path(c).name for c in p['musica']) or '—'} | {len(p['efectos'])} | {len(set(p['efectos']))} | "
                 f"{len(set(p['propios']))} | {len(av) and f'{len(av)}: ' + av[0] or ''} |")
    texto = "\n".join(L) + "\n"
    print("\n".join(L[:8]))
    print("\nEfectos compartidos más usados (usos · piezas · archivo):")
    for e, n in usos.most_common(15):
        print(f"  {n:5d} · {len(en_piezas[e]):3d} · {e}")
    print("\nMúsica (piezas · fuente):")
    for c, ps in sorted(mus.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(ps):3d} · {c}")
    print(f"  {len(sin_musica):3d} · (sin música)")
    print(f"\nBanco: {len(banco)} sonidos, {len(sin_usar)} nunca usados.")
    if informe:
        Path(informe).write_text(texto, encoding="utf-8")
        print(f"informe: {informe}")
    return todas, usos


def probar():
    """Un repo de mentira con piezas fechadas por su mtime (sin git). Cada caso dice si la guardia debe avisar."""
    import tempfile
    casos = []

    def caso(nombre, obtenido, esperado):
        casos.append(obtenido == esperado)
        print(f"  {'ok   ' if obtenido == esperado else 'FALLA'} {nombre}: {obtenido!r}" + ("" if obtenido == esperado else f" (debía ser {esperado!r})"))

    BANCO = [{"archivo": "pop/burbuja-pop.wav", "en": 1}, {"archivo": "interfaz/kenney-click-001.wav", "en": 2},
             {"archivo": "transicion/whoosh-rapido.wav", "en": 3}, {"archivo": "exito/kenney-confirmation-001.wav", "en": 4}]
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        t0 = time.time() - 100 * 86400

        def pieza(rel, dias, mezcla, efectos_json=None, musica_json=False):
            c = raiz / rel
            c.mkdir(parents=True, exist_ok=True)
            (c / "mezcla.json").write_text(json.dumps(mezcla), encoding="utf-8")
            if efectos_json is not None:
                (c / "efectos.json").write_text(json.dumps(efectos_json), encoding="utf-8")
            if musica_json:
                (c / "musica.json").write_text("{}", encoding="utf-8")
            os.utime(c / "mezcla.json", (t0 + dias * 86400, t0 + dias * 86400))
            return rel

        mixkit = lambda n: {"archivo": f"recursos/musica/mixkit-{n}.mp3"}
        pieza("viejo/c", 1, {"cancion": mixkit("543-the-journey"), "efectos": BANCO})          # fuera de las recientes
        for i in range(3):
            pieza(f"relleno/r{i}", 5 + i, {"cancion": mixkit(f"10{i}-otra"), "efectos": [{"archivo": f"relleno/r{i}/sfx/a.wav", "en": 1}]})
        pieza("reciente/a", 20, {"cancion": mixkit("759-vastness"), "efectos": BANCO[:3]})
        pieza("reciente/b", 21, {"extra": [{"archivo": "musica.wav"}], "efectos": []}, musica_json=True)
        nuevas = {
            "repite la canción de a": (pieza("nueva/cancion", 30, {"cancion": mixkit("759-vastness")}), True),
            "repite el set de efectos de a (por efectos_de)": (pieza("nueva/efectos", 31, {"cancion": mixkit("1-nueva"), "efectos_de": "efectos.json"},
                                                                       efectos_json=BANCO[:3] + BANCO[:2]), True),
            "musica.py otra vez (b también la usa)": (pieza("nueva/calculada", 32, {}, musica_json=True), True),
            "canción nueva y kit propio": (pieza("nueva/kit", 33, {"cancion": mixkit("2-nueva"), "efectos": [
                {"archivo": f"nueva/kit/sfx/{n}.wav", "en": 1} for n in ("whoosh_1", "clave_1", "sub_1")]}), False),
            "explicativo sin música, kit propio": (pieza("nueva/explica", 34, {"voz": "narracion.wav", "efectos": [
                {"archivo": f"nueva/explica/sfx/{n}.wav", "en": 1} for n in ("pop_1", "pop_2", "clic_1")]}), False),
            "el horizontal de a repite a a (misma pieza)": (pieza("reciente/a/horizontal", 35, {"cancion": mixkit("759-vastness"), "efectos": BANCO[:3]}), False),
            "la v2 de a repite a a (misma pieza)": (pieza("reciente/a-v2", 36, {"cancion": mixkit("759-vastness"), "efectos": BANCO[:3]}), False),
            "canción de una pieza vieja, fuera de las recientes": (pieza("nueva/vieja", 37, {"cancion": mixkit("543-the-journey")}), False),
            "un solo efecto compartido de tres": (pieza("nueva/poco", 38, {"cancion": mixkit("3-nueva"), "efectos": BANCO[:1] + [
                {"archivo": f"nueva/poco/sfx/{n}.wav", "en": 1} for n in ("a", "b")]}), False),
        }
        todas = piezas(raiz)
        caso("sin git, toma la fecha del archivo (6 + 9 mezclas leídas)", len(todas), 15)
        caso("efectos_de suma los usos de efectos.json (5)", len(next(p for p in todas if p["carpeta"] == "nueva/efectos")["efectos"]), 5)
        caso("pieza_de quita /horizontal y -v2", (pieza_de("x/y/horizontal"), pieza_de("x/y-v2")), ("x/y", "x/y"))
        for nombre, (rel, debe) in nuevas.items():
            # cada nueva se revisa contra las 4 piezas más nuevas que ella, sin contar las otras nuevas
            base = [p for p in todas if not p["carpeta"].startswith("nueva/") or p["carpeta"] == rel]
            av = revisar(rel, base, recientes=4)
            caso(f"{'avisa' if debe else 'no avisa'}: {nombre}", bool(av), debe)
        # rota a propósito: con el umbral en 1,0 el set casi igual ya no se ve (la guardia tiene que fallar este caso)
        av = revisar("nueva/efectos", [p for p in todas if not p["carpeta"].startswith("nueva/") or p["carpeta"] == "nueva/efectos"],
                     recientes=4, parecido=1.01)
        print(f"  (rota a propósito, umbral 1,01) {'FALLA' if not av else 'ok'}: el set repetido pasa sin aviso -> "
              f"{'como se esperaba' if not av else 'MAL'}")
        casos.append(not av)
        caso("fuera del repo, avisar no rompe nada", avisar(Path(tmp).parent, raiz), [])
    print(f"PRUEBA {'PASA' if all(casos) else 'FALLA'} ({sum(casos)} de {len(casos)})")
    return all(casos)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--probar"]:
        sys.exit(0 if probar() else 1)
    raiz = RAIZ
    if "--raiz" in args:
        i = args.index("--raiz"); raiz = Path(args[i + 1]).resolve(); del args[i:i + 2]
    informe = None
    if "--informe" in args:
        i = args.index("--informe"); informe = args[i + 1]; del args[i:i + 2]
    if args:
        av = avisar(Path(args[0]).resolve() if Path(args[0]).is_absolute() else (raiz / args[0]), raiz)
        print("ok: no repite canción ni set de efectos de las recientes" if not av else f"{len(av)} avisos")
        sys.exit(1 if av else 0)
    medir(raiz, informe)
