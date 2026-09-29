"""Guardia de la versión pública: copia las skills, las herramientas y el código de los ejemplos desde el
proyecto de origen (privado), les aplica los reemplazos y los parches, y FALLA si queda algo personal.

    python herramientas/limpiar_publico.py --origen <carpeta-del-proyecto-de-origen>
        copia, reemplaza, parchea y revisa todo el destino. Sale con 1 si algo falla.
    python herramientas/limpiar_publico.py --origen <carpeta> --guardar-parches
        después de corregir a mano un archivo público, guarda la diferencia como parche (privado/parches/).
    python herramientas/limpiar_publico.py --revisar
        sólo revisa el destino (no copia nada).
    python herramientas/limpiar_publico.py --probar
        se rompe a propósito: un caso por patrón prohibido tiene que decir FALLA y el caso limpio, ok.

El origen también se puede dar con la variable VIDEOS_ORIGEN. Las reglas personales (la lista de patrones
prohibidos y los reemplazos) y los parches viven en `privado/`, que está en .gitignore: nunca se publican,
porque nombrarlos ya sería publicarlos. Este archivo sólo trae el motor y los patrones genéricos.

Cómo se lee cada caso: «FALLA <archivo>:<línea> <patrón> «texto»». Al final, el total de hallazgos.
"""
import argparse
import difflib
import fnmatch
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DESTINO = Path(__file__).resolve().parent.parent
PRIVADO = DESTINO / "privado"
PARCHES = PRIVADO / "parches"

# qué se copia: (patrón en el origen, carpeta en el destino). El destino conserva la ruta relativa, salvo las
# skills, que pasan de .claude/skills/ a skills/.
GRUPOS = [
    (".claude/skills/*/SKILL.md", lambda r: "skills/" + r[len(".claude/skills/"):]),
    ("herramientas/*.py", None),
    ("herramientas/*.js", None),
    ("herramientas/vendor/three.module.min.js", None),
    # código de los ejemplos que se publican (sin audio: la narración se regenera y la música es de terceros)
    ("01-html-canvas/red-neuronal/*", None),
    ("02-threejs/red-neuronal/*", None),
    ("03-calculo-real/red-neuronal/*", None),
    ("04-explicativo-narrado/red-neuronal/*", None),
    ("05-shader-webgl2/el-faro/*", None),           # cuento original del proyecto (29-sep)
    ("17-archivo/revolucion-industrial/*", None),
    ("18-epica-lineal/historia-del-vuelo/*", None),
    ("18-epica-lineal/historia-del-vuelo/efectos/*", None),
    ("19-ensayo/las-cosas-pequenas/*", None),
    ("19-ensayo/las-cosas-pequenas/imagenes/*.png", None),
    ("20-generativo/semilla/*", None),
    ("datos/optdigits.*", None),                    # UCI optdigits (CC BY 4.0) para la técnica 3
]
# nunca se copian: audio (narración propia que se regenera; mezclas con música de terceros), registros,
# imágenes crudas y pruebas sueltas atadas a una escena privada
EXCLUIR = ["*.wav", "*.mp3", "*.mp4", "*.webm", "*.log", "*/crudas/*", "mezcla_v*",
           "herramientas/prueba_voces.py", "herramientas/prueba_voces2.py"]
BINARIOS = {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".wav", ".mp3", ".glb", ".blend", ".pdf", ".webm", ".ico", ".woff2",
            ".tra", ".tes"}                             # datos: se copian tal cual

# patrones genéricos (sirven para cualquiera); los personales se suman desde privado/reglas.py
PROHIBIDOS_GENERICOS = [
    ("ruta de usuario de Windows", r"[A-Za-z]:[\\/]+(Users|Usuarios)[\\/]"),
    ("ruta de usuario de Linux o macOS", r"/(home|Users)/[a-z][\w.-]+/"),
    ("OneDrive", r"OneDrive"),
    ("correo", r"[\w.+-]{1,64}@[\w-]{1,63}\.(com|net|org|me|io|dev|app|co|es|ve|mx)\b"),   # acotado: rápido en archivos minificados
    ("clave o token", r"(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
]
# archivos que la revisión no mira: el motor (nombra los patrones) y lo privado (no se publica)
NO_REVISAR = ["herramientas/limpiar_publico.py", "privado/*", ".git/*"]


def reglas():
    """privado/reglas.py: PROHIBIDOS [(nombre, regex, ejemplo)], GLOBALES [(tipo, regex, reemplazo, globs|None)]."""
    f = PRIVADO / "reglas.py"
    if not f.exists():
        return [], []
    spec = importlib.util.spec_from_file_location("reglas_privadas", f)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return list(getattr(m, "PROHIBIDOS", [])), list(getattr(m, "GLOBALES", []))


def coincide(rel, patrones):
    return any(fnmatch.fnmatch(rel, p) for p in patrones)


def archivos_del_origen(origen):
    """(ruta en el origen, ruta relativa en el destino) de todo lo que se publica."""
    out = []
    for patron, mapa in GRUPOS:
        for f in sorted(origen.glob(patron)):
            if not f.is_file():
                continue
            rel = f.relative_to(origen).as_posix()
            if coincide(rel, EXCLUIR):
                continue
            out.append((f, mapa(rel) if mapa else rel))
    return out


def texto_normal(s):
    s = s.replace("\r\n", "\n")
    return s if s.endswith("\n") else s + "\n"


def aplicar_globales(rel, s, globales, cuenta):
    for tipo, rx, nuevo, globs in globales:
        if globs and not coincide(rel, globs):
            continue
        s, n = re.subn(rx, nuevo, s)
        if n:
            cuenta[tipo] = cuenta.get(tipo, 0) + n
    return s


def ruta_parche(rel):
    return PARCHES / (rel + ".diff")


def aplicar_parche(rel, base):
    """Aplica privado/parches/<rel>.diff sobre el texto base con `git apply` (en una carpeta temporal).
    Devuelve (texto, cantidad de tramos) o lanza RuntimeError si el parche ya no calza (el origen cambió)."""
    p = ruta_parche(rel)
    if not p.exists():
        return base, 0
    parche = p.read_text(encoding="utf-8")
    tramos = sum(1 for l in parche.splitlines() if l.startswith("@@"))
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / rel; f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(base, encoding="utf-8", newline="\n")
        r = subprocess.run(["git", "apply", "--whitespace=nowarn", "-p1", str(p)], cwd=tmp, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr.strip() or r.stdout.strip())
        return f.read_text(encoding="utf-8"), tramos


def hacer_parche(rel, base, publico):
    if base == publico:
        return None
    d = difflib.unified_diff(base.splitlines(keepends=True), publico.splitlines(keepends=True),
                             fromfile="a/" + rel, tofile="b/" + rel, n=3)
    return "".join(d)


def copiar(origen, guardar=False):
    prohibidos, globales = reglas()
    if not globales and not prohibidos:
        print("AVISO: no hay privado/reglas.py; sólo se usan los patrones genéricos")
    cuenta, fallas, tramos, n = {}, 0, 0, 0
    for f, rel in archivos_del_origen(origen):
        dst = DESTINO / rel; dst.parent.mkdir(parents=True, exist_ok=True); n += 1
        if f.suffix.lower() in BINARIOS or f.name.endswith(".min.js"):
            if not guardar:
                shutil.copyfile(f, dst)
            continue
        base = aplicar_globales(rel, texto_normal(f.read_text(encoding="utf-8")), globales, cuenta)
        if guardar:
            if not dst.exists():
                continue
            d = hacer_parche(rel, base, texto_normal(dst.read_text(encoding="utf-8")))
            p = ruta_parche(rel)
            if d:
                p.parent.mkdir(parents=True, exist_ok=True); p.write_text(d, encoding="utf-8", newline="\n")
                print(f"parche guardado: {rel}")
            elif p.exists():
                p.unlink(); print(f"parche borrado (ya no hace falta): {rel}")
            continue
        try:
            texto, t = aplicar_parche(rel, base)
            tramos += t
        except RuntimeError as e:
            print(f"FALLA {rel}: el parche ya no calza con el origen (cambió): {str(e).splitlines()[0]}")
            print(f"      corregir a mano el archivo público y correr con --guardar-parches")
            fallas += 1
            continue
        dst.write_text(texto, encoding="utf-8", newline="\n")
    if guardar:
        return 0
    print(f"copiados: {n} archivos · reemplazos automáticos: {sum(cuenta.values())} "
          + (f"({', '.join(f'{k} {v}' for k, v in sorted(cuenta.items()))})" if cuenta else "")
          + f" · tramos de parches: {tramos}")
    return fallas


def revisar(carpeta=DESTINO, patrones=None, silencioso=False):
    """Busca patrones prohibidos en todos los archivos de texto. Devuelve la cantidad de hallazgos."""
    if patrones is None:
        prohibidos, _ = reglas()
        patrones = [(n, rx) for n, rx, *_ in PROHIBIDOS_GENERICOS + prohibidos]
    comp = [(n, re.compile(rx, re.I)) for n, rx in patrones]
    hallazgos = 0
    for f in sorted(carpeta.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(carpeta).as_posix()
        if coincide(rel, NO_REVISAR):
            continue
        for n, rx in comp:                                  # el nombre del archivo y de sus carpetas también cuenta
            if rx.search(rel):
                hallazgos += 1
                if not silencioso:
                    print(f"FALLA {rel} (ruta) {n}")
        if f.suffix.lower() in BINARIOS:
            continue
        try:
            lineas = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, l in enumerate(lineas, 1):
            for n, rx in comp:
                m = rx.search(l)
                if m:
                    hallazgos += 1
                    if not silencioso:
                        print(f"FALLA {rel}:{i} {n} «{l[max(0, m.start() - 30):m.end() + 30].strip()}»")
    return hallazgos


def privado_ignorado():
    """privado/ tiene que estar en .gitignore: si no, un `git add` lo publicaría."""
    r = subprocess.run(["git", "check-ignore", "-q", "privado/reglas.py"], cwd=DESTINO)
    return r.returncode == 0


def probar():
    """Un guardián que nunca falló no se cree: un archivo por patrón prohibido (con su ejemplo) tiene que dar
    FALLA, y uno limpio, ok."""
    prohibidos, _ = reglas()
    casos = [(p[0], p[1], p[2]) for p in prohibidos if len(p) > 2 and p[2]]
    casos += [("ruta de usuario de Windows", PROHIBIDOS_GENERICOS[0][1], r"C:\Users\alguien\x"),
              ("correo", PROHIBIDOS_GENERICOS[3][1], "escribe a nadie@ejemplo.com")]
    bien = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "limpio.md").write_text("Una skill sin nada personal: una app de notas, un cuento propio.\n", encoding="utf-8")
        todos = [(n, rx) for n, rx, *_ in PROHIBIDOS_GENERICOS + prohibidos]
        h = revisar(tmp, todos, silencioso=True)
        print(f"{'ok' if h == 0 else 'FALLA'}  caso limpio -> {'como se esperaba' if h == 0 else 'MAL: dio hallazgos'}")
        bien += h == 0
        (tmp / "limpio.md").unlink()
        for k, (n, rx, ej) in enumerate(casos):
            f = tmp / f"caso{k}.md"; f.write_text(f"texto de prueba: {ej}\n", encoding="utf-8")
            h = revisar(tmp, todos, silencioso=True)
            print(f"{'FALLA' if h else 'ok'}  {n} -> {'como se esperaba' if h else 'MAL: no lo encontró'}")
            bien += bool(h); f.unlink()
    total = len(casos) + 1
    print(f"guardia: {bien}/{total} casos como se esperaba")
    return bien == total


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--origen", default=os.environ.get("VIDEOS_ORIGEN"))
    ap.add_argument("--guardar-parches", action="store_true")
    ap.add_argument("--revisar", action="store_true")
    ap.add_argument("--probar", action="store_true")
    a = ap.parse_args()
    if a.probar:
        sys.exit(0 if probar() else 1)
    fallas = 0
    if not a.revisar:
        if not a.origen:
            sys.exit("falta --origen (o la variable VIDEOS_ORIGEN)")
        origen = Path(a.origen).resolve()
        if a.guardar_parches:
            sys.exit(copiar(origen, guardar=True))
        fallas += copiar(origen)
    if not privado_ignorado():
        print("FALLA .gitignore: privado/ no está ignorado (se publicarían las reglas y los parches)")
        fallas += 1
    h = revisar()
    print(f"revisión: {h} hallazgos · {fallas} fallas de copia")
    sys.exit(1 if h or fallas else 0)


if __name__ == "__main__":
    main()
