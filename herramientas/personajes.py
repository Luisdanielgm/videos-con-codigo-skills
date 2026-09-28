"""Biblioteca de personajes para Blender: se construyen una vez, se guardan en biblioteca/personajes.blend
y cada escena los trae con `cargar()` en vez de rearmarlos.

    externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup -P herramientas/personajes.py -- --construir
    externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup -P herramientas/personajes.py -- --prueba <carpeta>

Cada personaje es un esqueleto de Blender con los huesos del BVH de CMU (01_06) a la escala del niño,
un cuerpo de UNA malla (metaballs convertidos: sin costuras en codos ni rodillas) con pesos por hueso,
y la cabeza rígida en el hueso Head (malla propia, ojos, boca, cejas, pelo).
Para animarlo: `bases(esq, R, P)` pasa las rotaciones y posiciones del mundo que da actor.fk (Y arriba)
a la pose de cada hueso.

Nombres que usan las escenas: esqueleto `<n>`, ojos `<n>_ojo-1` / `<n>_ojo1` (se parpadea escalando Z),
boca `<n>_boca` (se habla escalando Z), cejas `<n>_ceja-1` / `<n>_ceja1`.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

RAIZ = Path(__file__).resolve().parents[1]
BLEND = RAIZ / "biblioteca" / "personajes.blend"
C3 = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)      # Y arriba (BVH) → Z arriba (Blender)


def B(p): return Vector(C3 @ np.asarray(p, float))
def BR(R): return Matrix((C3 @ R @ C3.T).tolist())
def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c)


# Estilos de personaje: uno por personaje, se construyen con --construir. Viene VACÍO: agrega los tuyos.
# Hay dos tipos de ropa, según tenga o no la clave "traje":
#   - ropa de calle (sin "traje"): camiseta con una franja en el pecho, short, medias y zapatillas; pelo en mechones;
#   - traje entero (con "traje"): traje de una pieza, cinturón metálico ("oro") y botas; pelo en rizos.
# Plantilla (los valores son de muestra; cambia colores y medidas):
#   "mi_personaje": dict(
#       escala=.036,           # escala del esqueleto de CMU (.036 ≈ un niño de unos 10 años; más grande = más alto)
#       grosor=1.0,            # multiplica los radios del cuerpo (PARTES)
#       piel="#e8b894", iris="#5a3a22", iris2="#1e120a", pelo="#3a2618", ceja="#2e1c10", pestana="#1c1414",
#       ojo=(.051, .06), ojo_x=.072, ceja_grosor=.0105,   # tamaño de los ojos, separación, cejas
#       cuello=.35, cabeza=.86,                          # alto del cuello (fracción) y escala de la cabeza
#       # ropa de calle:
#       camisa="#2e7d5b", franja="#ffffff", short="#3b3f46", media="#f4f4f0", zapato="#eeeeee", suela="#6b7280",
#       manga=.55, pierna=.8,  # largo de manga (0–1 hasta el codo) y de short (0–1 hasta la rodilla)
#       # o, en vez de la ropa de calle, traje entero: traje="#dfe4ee", oro="#c9a23a",
#       brillo=None,           # opcional, un color: la ropa y el pelo emiten un poco de esa luz
#   ),
ESTILOS = {}

# cuerpo: (articulación, tipo, desde, hasta, radio) — desde/hasta son articulaciones o puntos relativos
# a una articulación; radios en metros para escala .036 (cada estilo los multiplica por `grosor`)
PARTES = [
    ("Hips", "elip", ("Hips", (0, -.01, 0)), (.138, .095, .1)),
    ("Spine", "elip", ("Spine", (0, 0, .006)), (.132, .095, .1)),
    ("Spine1", "elip", ("Spine1", (0, .025, 0)), (.13, .075, .094)),
    ("Neck", "caps", "Neck", ("Head", (0, .05, 0)), .05),
    ("LeftShoulder", "caps", ("Spine1", (.05, .02, 0)), "LeftArm", .056),
    ("RightShoulder", "caps", ("Spine1", (-.05, .02, 0)), "RightArm", .056),
    ("LeftArm", "caps", "LeftArm", "LeftForeArm", .056),
    ("RightArm", "caps", "RightArm", "RightForeArm", .056),
    ("LeftForeArm", "caps", "LeftForeArm", "LeftHand", .055),
    ("RightForeArm", "caps", "RightForeArm", "RightHand", .055),
    ("LeftUpLeg", "caps", "LeftUpLeg", "LeftLeg", .084),
    ("RightUpLeg", "caps", "RightUpLeg", "RightLeg", .084),
    ("LeftLeg", "caps", "LeftLeg", "LeftFoot", .066),
    ("RightLeg", "caps", "RightLeg", "RightFoot", .066),
]


# ───────────── esqueleto ─────────────
def esqueleto_bvh(escala):
    sys.path.insert(0, str(RAIZ / "herramientas"))
    from bvh import Bvh
    b = Bvh(RAIZ / "externos" / "mocap" / "01_06.bvh")
    P = {}
    for j in b.joints:
        p = b.padre[j]
        P[j] = np.zeros(3) if p is None else P[p] + b.offset[j] * escala
    alto = -min(P["LeftToeBase"][1], P["RightToeBase"][1]) + .02
    for j in P: P[j] = P[j] + np.array([0, alto, 0])
    return b, P


def crear_armadura(nombre, b, P):
    arm = bpy.data.armatures.new(nombre); esq = bpy.data.objects.new(nombre, arm)
    bpy.context.scene.collection.objects.link(esq)
    bpy.context.view_layer.objects.active = esq
    bpy.ops.object.mode_set(mode="EDIT")
    huesos = {}
    for j in b.joints:
        if j.endswith("_fin"): continue
        e = arm.edit_bones.new(j); e.head = B(P[j])
        hijos = [c for c in b.hijos[j] if np.linalg.norm(P[c] - P[j]) > 1e-4]
        if hijos:
            c = max(hijos, key=lambda c: np.linalg.norm(P[c] - P[j])); e.tail = B(P[c])
        else:
            p = b.padre[j]; d = P[j] - P[p] if p and np.linalg.norm(P[j] - P[p]) > 1e-4 else np.array([0, 1.0, 0])
            e.tail = B(P[j] + d / np.linalg.norm(d) * .04)
        if b.padre[j]: e.parent = huesos[b.padre[j]]
        e.use_connect = False
        huesos[j] = e
    bpy.ops.object.mode_set(mode="OBJECT")
    return esq


def repartir_cuello(R, P):
    """El giro de la cabeza (lo que la escena pone con `mirar` en Head) repartido en tercios entre Neck,
    Neck1 y Head: si lo hace todo Head, el cuello corto de los niños de IA se estira como un elástico.
    La cabeza termina con la misma orientación; su posición se corre lo que corresponde al doblar el cuello."""
    from mathutils import Quaternion
    R = dict(R); P = dict(P)
    Rn, Rn1 = Matrix(R["Neck"].tolist()), Matrix(R["Neck1"].tolist())
    rel = (Rn.transposed() @ Matrix(R["Head"].tolist())).to_quaternion()
    n = Rn @ Quaternion().slerp(rel, 1 / 3).to_matrix(); n1 = Rn @ Quaternion().slerp(rel, 2 / 3).to_matrix()
    a = np.array(n) @ R["Neck"].T; b = np.array(n1) @ R["Neck1"].T
    p1 = P["Neck"] + a @ (P["Neck1"] - P["Neck"])
    P["Head"] = p1 + b @ (P["Head"] - P["Neck1"]); P["Neck1"] = p1
    R["Neck"], R["Neck1"] = np.array(n), np.array(n1)
    return R, P


def bases(esq, R, P):
    """Pose de cada hueso (matrix_basis) para que cada articulación quede con la rotación R[j] y en la
    posición P[j] del mundo (Y arriba, como devuelve actor.fk). Esqueleto en el origen, sin rotar."""
    D = {}
    Q = json.loads(esq["ia_Q"]) if "ia_Q" in esq else None    # personajes de IA (personaje_ia.py): reposo en pose A
    if Q: R, P = repartir_cuello(R, P)
    for b in esq.data.bones:
        Rb = BR(R[b.name])
        if Q: Rb = Rb @ BR(np.array(Q[b.name])).transposed()
        W = Matrix.Translation(B(P[b.name])) @ Rb.to_4x4()
        D[b.name] = W @ Matrix.Translation(-b.head_local)
    out = {}
    for b in esq.data.bones:
        Dp = D[b.parent.name].inverted() if b.parent else Matrix.Identity(4)
        out[b.name] = b.matrix_local.inverted() @ Dp @ D[b.name] @ b.matrix_local
    return out


# ───────────── materiales ─────────────
def material(nombre, color, rugosidad=.6, metal=0.0, emision=None, fuerza=0.0, sss=0.0, tela=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(color), 1)
    b.inputs["Roughness"].default_value = rugosidad
    b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1, .35, .2)
        b.inputs["Subsurface Scale"].default_value = .02
    if emision:
        b.inputs["Emission Color"].default_value = (*srgb(emision), 1); b.inputs["Emission Strength"].default_value = fuerza
    if tela:                                              # trama fina de tela: relieve de ruido muy chico
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 320; nz.inputs["Detail"].default_value = 1   # más fina brilla en puntos sueltos
        bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = tela * .3;   # más fuerte hace puntos brillantes sueltos bm.inputs["Distance"].default_value = .002
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bm.inputs["Height"])
        nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Sheen Weight"].default_value = .25
    return m


# ───────────── volúmenes blandos (metaballs → malla) ─────────────
def metaball(nombre, elementos, resolucion=.005):
    """elementos: (tipo, centro, radios|radio, dirección|None) en coordenadas de Blender."""
    mb = bpy.data.metaballs.new(nombre); mb.resolution = resolucion; mb.render_resolution = resolucion
    mb.threshold = .6
    o = bpy.data.objects.new(nombre, mb); bpy.context.scene.collection.objects.link(o)
    for tipo, c, r, d in elementos:
        el = mb.elements.new(); el.co = Vector(c); el.stiffness = 2.0
        if tipo.endswith("-"):                            # negativo: resta volumen (huecos, cortes)
            el.use_negative = True; tipo = tipo[:-1]
        if tipo == "ball":
            el.type = "BALL"; el.radius = r
        elif tipo == "elip":
            el.type = "ELLIPSOID"; el.radius = 1.0
            el.size_x, el.size_y, el.size_z = r
        else:                                             # cápsula: size_x = medio largo sobre X local
            L, rad = r
            el.type = "CAPSULE"; el.radius = rad; el.size_x = L
            el.rotation = Vector((1, 0, 0)).rotation_difference(Vector(d))
    dg = bpy.context.evaluated_depsgraph_get()
    malla = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o); bpy.data.metaballs.remove(mb)
    malla.name = nombre
    import bmesh                                          # soldar: si quedan vértices repetidos, al inflar la ropa se abren grietas
    bm = bmesh.new(); bm.from_mesh(malla); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=2e-4, edges=bm.edges); bm.to_mesh(malla)   # caras de menos de 0,2 mm: normales torcidas (brillo de tela en puntos); bm.free()
    ob = bpy.data.objects.new(nombre, malla); bpy.context.scene.collection.objects.link(ob)
    malla.shade_smooth()
    return ob


def punto(P, ref):
    if isinstance(ref, str): return np.array(P[ref], float)
    j, off = ref; return np.array(P[j], float) + np.array(off, float)


def cuerpo(nombre, est, b, P):
    g = est["grosor"]; els, formas = [], []
    for j, tipo, *datos in PARTES:
        if tipo == "elip":
            c = punto(P, datos[0]); r = np.array(datos[1]) * g
            els.append(("elip", B(c), (r[0], r[2], r[1]), None))          # radios del BVH (x, y, z) → Blender (x, z, y)
            formas.append((j, "elip", c, r))
        else:
            a, z, rad = punto(P, datos[0]), punto(P, datos[1]), datos[2] * g
            d = z - a; L = np.linalg.norm(d)
            els.append(("caps", B((a + z) / 2), (L / 2, rad), B(d / L)))
            formas.append((j, "caps", a, z, rad))
    for lado, s in (("Left", 1), ("Right", -1)):
        L_ = "L" if s > 0 else "R"
        # mano en mitón: palma y dedos juntos, pulgar aparte
        h, fb = P[f"{lado}Hand"], P[f"{lado}HandIndex1"]
        dmano = (fb - h) / np.linalg.norm(fb - h)
        cm = h + dmano * .03
        els.append(("elip", B(cm), (.07 * g, .056 * g, .04 * g), None))
        formas.append((f"{lado}Hand", "elip", cm, np.array([.07, .04, .056]) * g))
        pul = P[f"{L_}Thumb_fin"] * .7 + h * .3 + np.array([0, .005, 0])
        els.append(("ball", B(pul), .032 * g, None)); formas.append((f"{L_}Thumb", "elip", pul, np.array([.026, .026, .026]) * g))
        # zapato: del tobillo a la punta, apoyado en el suelo
        f, tf = P[f"{lado}Foot"], P[f"{lado}ToeBase_fin"]
        dz = tf - f; cz = f + dz * .55 + np.array([0, -.02, -.012])
        rz = np.array([.078 * g, .058, np.linalg.norm(dz) * .92])          # zapato grueso, como en las hojas de modelo
        els.append(("elip", B(cz), (rz[0], rz[2], rz[1]), None)); formas.append((f"{lado}Foot", "elip", cz, rz))
    ob = metaball(f"{nombre}_cuerpo", els)
    return ob, formas


def pesos(ob, formas, P, sigma=.016):
    """Peso de cada vértice por hueso según lo cerca que esté del volumen de ese hueso: donde dos
    volúmenes se funden (codo, rodilla, hombro) el vértice queda repartido y dobla suave."""
    n = len(ob.data.vertices)
    V = np.empty(n * 3); ob.data.vertices.foreach_get("co", V); V = V.reshape(-1, 3) @ C3   # a Y arriba
    juntas = sorted({f[0] for f in formas}); W = np.zeros((n, len(juntas)))
    for f in formas:
        j = juntas.index(f[0])
        if f[1] == "elip":
            c, r = f[2], f[3]; q = (V - c) / r
            d = (np.linalg.norm(q, axis=1) - 1) * r.min()
        else:
            a, z, rad = f[2], f[3], f[4]; ab = z - a
            u = np.clip((V - a) @ ab / (ab @ ab), 0, 1)
            d = np.linalg.norm(V - (a + u[:, None] * ab), axis=1) - rad
        W[:, j] = np.maximum(W[:, j], np.exp(-(np.maximum(d, 0) / sigma) ** 2))
    cx = P["Hips"][0]
    for k, j in enumerate(juntas):                        # nada de la pierna izquierda en la derecha (entrepierna)
        lado = 1 if j.startswith(("Left", "LHip", "LThumb")) else -1 if j.startswith(("Right", "RHip", "RThumb")) else 0
        if lado: W[(V[:, 0] - cx) * lado < -.004, k] = 0
    W[W < .04] = 0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    grupos = {j: ob.vertex_groups.new(name=j) for j in juntas}
    for k, j in enumerate(juntas):
        idx = np.nonzero(W[:, k])[0]
        for i in idx: grupos[j].add([int(i)], float(W[i, k]), "REPLACE")
    return V, W, juntas


def ropa(ob, est, V, W, juntas, P, mats):
    """Material de cada cara por su lugar en la pose de reposo (en T): cortes derechos de mangas,
    short, medias y cuello, en vez de seguir al hueso dominante (dejaba los bordes dentados)."""
    cx = P["Hips"][0]
    hombro = abs(P["LeftArm"][0] - cx); codo = abs(P["LeftForeArm"][0] - cx); muñeca = abs(P["LeftHand"][0] - cx)
    axila = P["Spine1"][1] - .07
    cintura = P["Hips"][1] + .035; entrep = P["Hips"][1] - .07
    rodilla = P["LeftLeg"][1]; tobillo = P["LeftFoot"][1]
    suelo = min(P["LeftToeBase_fin"][1], P["RightToeBase_fin"][1]) - .02
    cuello = P["Neck"][1] + est["cuello"] * (P["Head"][1] - P["Neck"][1])
    ruedo = entrep + .018                                    # camiseta larga: tapa la cadera y el borde del short
    fin_short = entrep - est.get("pierna", 0) * (entrep - rodilla)
    bota = tobillo + .1
    def prenda(v):
        """Material y cuánto se separa la tela de la piel (hacia afuera) en el punto v (Y arriba)."""
        x = abs(v[0] - cx); y = v[1]
        brazo = x > hombro - .03 and y > axila
        if brazo: zona = "mano" if x > muñeca + .005 else "antebrazo" if x > codo else "brazo"
        elif y < tobillo + .02: zona = "pie"
        elif y < entrep: zona = "pierna"
        elif y < cintura: zona = "cadera"
        elif y > cuello: zona = "cara"
        else: zona = "torso"
        if "traje" in est:                                    # traje entero: cuello alto y botas; manos y cara a la vista
            m = "piel" if zona in ("mano", "cara") else "traje"; sep = .003 if m == "traje" else 0
            if zona in ("cadera", "torso") and abs(y - cintura) < .011: m, sep = "oro", .007
            if zona == "torso" and y > cuello - .03: sep = .009                                   # cuello alto enrollado
            if zona in ("pie", "pierna") and y < bota: m, sep = "bota", .011 + .004 * (y < tobillo + .02)
            if zona == "pie" and y < suelo + .012: m, sep = "suela", .013
            return m, sep
        m = {"mano": "piel", "antebrazo": "piel", "cara": "piel", "torso": "camisa", "cadera": "short"}.get(zona); sep = 0
        if zona == "brazo":
            k = (x - hombro) / (codo - hombro)
            m = "camisa" if k < est["manga"] else "piel"
            if m == "camisa": sep = .008 + .01 * max(0, k) / est["manga"]                         # manga suelta, más abierta en el borde
        if zona == "pierna":
            if y > fin_short: m, sep = "short", .01 + .013 * (entrep - y) / (entrep - fin_short)     # short ancho hasta cerca de la rodilla
            else: m = "media" if y < tobillo + .1 else "piel"
        if zona == "cadera": m, sep = ("camisa", .02) if y > ruedo else ("short", .01)
        if zona == "torso": sep = .016
        if zona == "pie": m, sep = ("suela", .016) if y < suelo + .014 else ("zapato", .012) if y < tobillo + .01 else ("media", .004)
        if zona == "pierna" and m == "media": sep = .004
        if m == "camisa" and zona == "torso" and abs(y - (P["Spine1"][1] - .052)) < .017: m = "franja"          # franja derecha, alrededor del pecho
        return m, sep
    nombres = list(mats); idx = []
    for pol in ob.data.polygons:
        idx.append(nombres.index(prenda(V[list(pol.vertices)].mean(0))[0]))
    for n_ in nombres: ob.data.materials.append(mats[n_])
    ob.data.polygons.foreach_set("material_index", idx)
    # la tela se separa de la piel siguiendo la normal: en el borde de cada prenda queda un escalón (el ruedo)
    n = len(ob.data.vertices)
    N_ = np.empty(n * 3); ob.data.vertices.foreach_get("normal", N_); N_ = N_.reshape(-1, 3)
    Ed = np.empty(len(ob.data.edges) * 2, dtype=np.int64); ob.data.edges.foreach_get("vertices", Ed); Ed = Ed.reshape(-1, 2)
    for _ in range(3):                                    # normal promediada con los vecinos: una cara degenerada
        A = N_.copy()                                     # deja un vértice con la normal torcida, que salía como punta brillante
        np.add.at(A, Ed[:, 0], N_[Ed[:, 1]]); np.add.at(A, Ed[:, 1], N_[Ed[:, 0]])
        N_ = A / np.maximum(np.linalg.norm(A, axis=1, keepdims=True), 1e-9)
    Co = np.empty(n * 3); ob.data.vertices.foreach_get("co", Co); Co = Co.reshape(-1, 3)
    sep = np.array([prenda(v)[1] for v in V])
    ob.data.vertices.foreach_set("co", (Co + N_ * sep[:, None]).ravel())
    ob.data.update()


# ───────────── cabeza ─────────────
K = 1 / .575                                              # un metaball se ve de 0,575 × su radio (medido)


def slerp_v(a, b, t):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    w = math.acos(max(-1, min(1, float(a @ b))))
    if w < 1e-6: return a
    return (math.sin((1 - t) * w) * a + math.sin(t * w) * b) / math.sin(w)


def pelo_mechones(nombre, H, est, calle):
    """Pelo en mechones: curvas afinadas que salen de la coronilla y siguen el cráneo hasta el borde del
    pelo (flequillo, sienes, nuca), sobre un casco del mismo color con entradas en la cara y las orejas."""
    def W(p): return B(H + np.array(p, float))
    Cc = np.array([0, .14, -.02]); R = .17
    rng = np.random.default_rng(3 if calle else 5)
    # casco: el cráneo un poco más grande (con rizos: más, para su volumen), recortado en la cara
    # y sobre las orejas, que quedan a la vista como en las hojas de modelo
    extra = .014 if calle else .03
    cas = [("ball", W(Cc), (R + extra) * K, None),
           ("ball-", W((0, .005 if calle else -.01, .2)), .19 * K, None),
           ("ball-", W((0, -.12, .02)), .2 * K, None)]
    for l in (-1, 1): cas.append(("ball-", W((l * .205, .075, .01)), .1 * K, None))
    casco = metaball(f"{nombre}_pelo", cas, .005)
    cu = bpy.data.curves.new(f"{nombre}_mechones", "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = .03; cu.bevel_resolution = 3; cu.use_fill_caps = True
    corona = np.array([0, 1, -.35]); corona /= np.linalg.norm(corona)
    def borde(fi, baja):                                  # altura del borde del pelo alrededor de la cabeza
        e = .0225 + .575 * math.cos(fi) - .0975 * math.cos(2 * fi) - baja
        return np.array([math.sin(fi) * math.cos(e), math.sin(e), math.cos(fi) * math.cos(e)])
    def curva(puntos, radios):
        sp = cu.splines.new("NURBS"); sp.points.add(len(puntos) - 1); sp.order_u = 4; sp.use_endpoint_u = True
        for p, q, r in zip(sp.points, puntos, radios): p.co = (*W(q), 1); p.radius = r
    def mechon(u0, u1, vol, barrido=0.0, grueso=1.0, punta=.02, n=16):
        """Mechón que sale de la coronilla con volumen, sigue el cráneo y termina en punta que se
        levanta hacia afuera (`punta`): el pelo despeinado del niño."""
        lado = np.cross(np.array([0, 1.0, 0]), u1); lado = lado / (np.linalg.norm(lado) + 1e-9)
        pts, rad = [], []
        for i in range(n):
            t = i / (n - 1)
            u = slerp_v(u0, u1, t) + lado * barrido * math.sin(math.pi * t); u /= np.linalg.norm(u)
            r = R - .012 + (.024 + vol) * (1 - (1 - min(1, t * 1.6)) ** 2) + punta * max(0, (t - .72) / .28) ** 2 + .026 * math.sin(math.pi * min(1, t * 1.3))   # raíz hundida en el casco; volumen arriba
            pts.append(Cc + u * r); rad.append(grueso * (.08 + .92 * (1 - t ** 1.7)) * min(1, .5 + t * 4))
        curva(pts, rad)
    def rizo(u, eje, radio, vueltas, largo, grueso, n=18):
        """Rizo en espiral apoyado en el volumen del pelo: nace en `u` y baja por `eje` girando."""
        base = Cc + u * (R + extra + rng.uniform(-.004, .012))
        b = np.cross(eje, u); b /= np.linalg.norm(b)
        pts, rad = [], []
        for i in range(n):
            t = i / (n - 1); a = 2 * math.pi * vueltas * t + rng.uniform(0, .3)
            rr = radio * (1 - .45 * t)
            pts.append(base + eje * largo * t + u * (rr * math.cos(a) + .004) + b * rr * math.sin(a))
            rad.append(grueso * (.25 + .75 * (1 - t) ** .6))
        curva(pts, rad)
    if calle:
        for k in range(40):                               # capa principal, del remolino al borde, largos distintos
            fi = -math.pi + 2 * math.pi * (k + rng.uniform(-.4, .4)) / 40
            costado = abs(math.sin(fi)) > .7 and math.cos(fi) > -.4
            u1 = borde(fi, rng.uniform(-.14, 0) if costado else rng.uniform(-.1, .06))   # sobre las orejas: más corto
            frente = max(0, math.cos(fi))
            mechon(corona + rng.normal(0, .1, 3), u1, .012 + .034 * frente + rng.uniform(0, .01), barrido=.2 * frente + rng.uniform(-.06, .06),
                   grueso=rng.uniform(1.25, 1.6), punta=rng.uniform(.004, .012) + .016 * frente)
        for k in range(0):                                # (sin mechones parados arriba: se veían como gusanos)
            fi = rng.uniform(-1.6, 1.6)
            u1 = np.array([math.sin(fi) * .55, .8, math.cos(fi) * .55 + .2]); u1 /= np.linalg.norm(u1)
            mechon(corona + rng.normal(0, .07, 3), u1, .055 + rng.uniform(0, .02), barrido=rng.uniform(-.2, .3), grueso=rng.uniform(1.3, 1.7),
                   punta=rng.uniform(.015, .03), n=12)
    else:
        rng_fi = (1 + 5 ** .5) / 2
        for k in range(130):                              # rizos repartidos sobre el volumen (espiral de Fibonacci)
            y = 1 - 2 * (k + .5) / 130; rr_ = math.sqrt(max(0, 1 - y * y)); th = 2 * math.pi * k / rng_fi
            u = np.array([rr_ * math.sin(th), y, rr_ * math.cos(th)])
            fi, e = math.atan2(u[0], u[2]), math.asin(y)
            lim = math.asin(borde(fi, .1 + .08 * (1 - math.cos(fi)) / 2)[1])
            if abs(math.sin(fi)) > .7 and math.cos(fi) > -.45: lim = max(lim, .16)        # las orejas quedan a la vista
            if e < lim - .04: continue
            abajo = np.array([0, -1.0, 0]) - u * -u[1]; abajo /= np.linalg.norm(abajo) + 1e-9
            eje = abajo * .8 + rng.normal(0, .35, 3); eje -= u * (eje @ u); eje /= np.linalg.norm(eje)
            rizo(u, eje, rng.uniform(.028, .04), rng.uniform(1.0, 1.4), rng.uniform(.05, .08), rng.uniform(.62, .8))
        for k, (fx, fy) in enumerate(((-.35, .45), (-.1, .55), (.18, .5), (.4, .4))):   # remolino del flequillo, hacia un lado
            u = np.array([fx, fy, .8]); u /= np.linalg.norm(u)
            eje = np.array([-.8, -.5, 0]); eje -= u * (eje @ u); eje /= np.linalg.norm(eje)
            rizo(u, eje, .04, 1.4, .07, .7)
    oc = bpy.data.objects.new(f"{nombre}_mechones", cu); bpy.context.scene.collection.objects.link(oc)
    dg = bpy.context.evaluated_depsgraph_get()
    malla = bpy.data.meshes.new_from_object(oc.evaluated_get(dg)); bpy.data.objects.remove(oc); bpy.data.curves.remove(cu)
    malla.shade_smooth()
    om = bpy.data.objects.new(f"{nombre}_mechones", malla); bpy.context.scene.collection.objects.link(om)
    # material: dos tonos que cambian a lo largo, brillo suave de pelo
    m = bpy.data.materials.new(f"pelo_{nombre}"); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60
    nz.inputs["Detail"].default_value = 3
    rp = nt.nodes.new("ShaderNodeValToRGB")
    c = srgb(est["pelo"]); oscuro = tuple(x * .55 for x in c); claro = tuple(min(1, x * 1.35) for x in c)
    rp.color_ramp.elements[0].color = (*oscuro, 1); rp.color_ramp.elements[1].color = (*claro, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = .38; bs.inputs["Coat Weight"].default_value = .15
    bs.inputs["Sheen Weight"].default_value = .3
    if est.get("brillo"):
        bs.inputs["Emission Color"].default_value = (*srgb(est["brillo"]), 1); bs.inputs["Emission Strength"].default_value = .3
    casco.data.materials.append(m); om.data.materials.append(m)
    om.parent = casco
    return casco


def cabeza(nombre, est, P, calle):
    """Cabeza con perfil de niño (cráneo, frente, cachetes, mentón, nariz, orejas con hueco y cuencas para
    los ojos) en una sola malla; ojos, boca, cejas y pelo aparte. Todo se arma en el marco de la
    articulación Head (Y arriba, +Z es la cara) y se lleva al mundo. Medidas: lo que se ve (× K)."""
    H = P["Head"]
    def W(p): return B(H + np.array(p, float))
    def E(c, r): return ("elip", W(c), (r[0] * K, r[2] * K, r[1] * K), None)   # radios (x, y, z) del BVH
    piel = bpy.data.materials[f"piel_{nombre}"]
    els = [("ball", W((0, .14, -.02)), .17 * K, None),                         # cráneo
           E((0, .085, .05), (.145, .15, .13)),                                 # cara (llega a la frente)
           ("ball", W((0, -.02, .085)), .055 * K, None),                        # mentón
           E((0, .078, .18), (.03, .026, .028))]                              # nariz de botón (se ve de perfil)
    ox = est["ojo_x"]
    for l in (-1, 1):
        els.append(("ball", W((l * .075, .035, .08)), .068 * K, None))          # cachetes
        els.append(E((l * .186, .098, -.012), (.024, .06, .046)))                # oreja grande, a la altura de los ojos
        els.append(("ball-", W((l * .208, .098, .004)), .022 * K, None))          # hueco de la oreja
        els.append(("ball-", W((l * ox, .128, .2)), .032 * K, None))            # cuenca del ojo
    cab = metaball(f"{nombre}_cabeza", els); cab.data.materials.append(piel)
    # dónde está la superficie de la cara (para apoyar ojos, boca y cejas)
    def cara(x, y):
        dg = bpy.context.evaluated_depsgraph_get()
        ok, loc, *_ = cab.ray_cast(W((x, y, .5)), Vector(C3 @ np.array([0, 0, -1.0])), depsgraph=dg)
        return np.array(C3.T @ np.array(loc)) - H if ok else np.array([x, y, .17])
    blanco = material(f"ojo_{nombre}", "#ffffff", .25); negro = material(f"pupila_{nombre}", "#101018", .15)
    iris = material(f"iris_{nombre}", est["iris"], .2); boca_m = material(f"boca_{nombre}", "#5a2028", .5)
    rosa = material(f"mejilla_{nombre}", "#ef9a92", .6, sss=.1)
    ceja_m = material(f"ceja_{nombre}", est["ceja"], .6)
    pest_m = material(f"pestana_{nombre}", est.get("pestana", "#1c1414"), .5)
    iris2 = material(f"iris2_{nombre}", est["iris2"], .3)
    piezas = [cab]
    ojos = []
    rx, ry = est["ojo"]
    for l in (-1, 1):
        s = cara(l * ox, .128); c = s + np.array([0, 0, -.014])
        oj = elipsoide(f"{nombre}_ojo{l}", (rx, ry, .022), blanco)
        iy = ry * .1                                          # el iris toca el borde de arriba, como en las hojas
        ir2 = elipsoide(f"{nombre}_irisb{l}", (rx * .8, ry * .8, .01), iris2, (0, iy, .0155))   # aro oscuro del iris
        ir = elipsoide(f"{nombre}_iris{l}", (rx * .68, ry * .68, .01), iris, (0, iy - ry * .03, .0165))
        pu = elipsoide(f"{nombre}_pup{l}", (rx * .34, ry * .34, .006), negro, (0, iy, .024))
        br = elipsoide(f"{nombre}_brillo{l}", (rx * .2, rx * .2, .004), blanco, (-rx * .28, iy + ry * .24, .027))
        br2 = elipsoide(f"{nombre}_brillo2{l}", (rx * .1, rx * .1, .003), blanco, (rx * .24, iy - ry * .26, .026))
        # línea de pestañas en el borde de arriba: más gruesa hacia afuera; va con el ojo (parpadea con él)
        pts = []
        for i in range(9):
            a = math.radians(12 + 156 * i / 8)
            x, y = math.cos(a) * rx * .9 * l, math.sin(a) * ry * .9
            z = .022 * math.sqrt(max(0, 1 - (x / rx) ** 2 - (y / ry) ** 2)) + .002
            pts.append(((x, y, z), .35 + .65 * (1 - i / 8) ** .7))
        pe = tubo(f"{nombre}_pest{l}", [B(p) for p, _ in pts], [r for _, r in pts], .0055, pest_m)
        for x in (ir2, ir, pu, br, br2, pe): x.parent = oj
        oj.location = W(c); oj.parent = cab; ojos.append(oj)
        # ceja: arco que sigue la frente (una curva apoyada punto por punto en la superficie)
        pts = []
        for i in range(7):
            u = i / 6 - .5
            q = cara(l * (ox + .004 + u * .066), .196 + .012 * math.cos(u * math.pi) - l * u * .02) + np.array([0, 0, .002])
            pts.append((W(q), .45 + .55 * math.cos(u * math.pi) ** .5))
        ce = tubo(f"{nombre}_ceja{l}", [p for p, _ in pts], [r for _, r in pts], est["ceja_grosor"], ceja_m); ce.parent = cab
        sm = cara(l * .11, .055)
        mj = elipsoide(f"{nombre}_mej{l}", (.03, .02, .01), rosa); mj.location = W(sm - np.array([0, 0, .006])); mj.parent = cab
    sb = cara(0, .022)
    bo = elipsoide(f"{nombre}_boca", (.024, .0075, .012), boca_m)
    for v in bo.data.vertices: v.co.z += 9 * v.co.x ** 2                 # sonrisa: las comisuras suben
    bo.location = W(sb - np.array([0, 0, .004])); bo.parent = cab
    pelo = pelo_mechones(nombre, H, est, calle)
    pelo.parent = cab
    return cab, ojos, bo, piezas


def elipsoide(nombre, radios, mat, centro=(0, 0, 0), rot=None, seg=24):
    """Esfera estirada con la malla en coordenadas del BVH (Y arriba, +Z adelante) llevadas a Blender."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1)
    o = bpy.context.object; o.name = nombre
    Rr = np.eye(3)
    if rot is not None:
        rx, ry, rz = rot
        Rr = (np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]]))
    M = np.eye(4); M[:3, :3] = C3 @ Rr @ np.diag(radios); M[:3, 3] = C3 @ np.asarray(centro, float)
    o.data.transform(Matrix(M.tolist()))
    o.data.materials.append(mat); o.data.shade_smooth()
    return o


def tubo(nombre, puntos, radios, grueso, mat):
    """Malla de un tubo que pasa por `puntos` (Blender), con grosor `grueso` × radios[i] en cada punto."""
    cc = bpy.data.curves.new(nombre, "CURVE"); cc.dimensions = "3D"
    cc.bevel_depth = grueso; cc.bevel_resolution = 2; cc.use_fill_caps = True
    sp = cc.splines.new("NURBS"); sp.points.add(len(puntos) - 1); sp.order_u = 4; sp.use_endpoint_u = True
    for p, q, r in zip(sp.points, puntos, radios): p.co = (*q, 1); p.radius = r
    oc = bpy.data.objects.new(nombre, cc); bpy.context.scene.collection.objects.link(oc)
    m = bpy.data.meshes.new_from_object(oc.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(oc); bpy.data.curves.remove(cc); m.shade_smooth(); m.materials.append(mat)
    o = bpy.data.objects.new(nombre, m); bpy.context.scene.collection.objects.link(o)
    return o


def escalar_cabeza(cab, centro, s, sube=0.0):
    """Achica la cabeza entera (piel, ojos, pelo…) alrededor de la articulación del cuello, en la malla y
    no en la escala del objeto: las escenas animan la escala de ojos y boca (parpadeo, habla). `sube` la
    levanta sobre el cuello (el esqueleto de CMU tiene los hombros casi a la altura del mentón)."""
    bpy.context.view_layer.update()
    objs = [cab] + list(cab.children_recursive)
    antes = {o.name: o.matrix_world.translation.copy() for o in objs}
    for o in objs:
        if o.data: o.data.transform(Matrix.Scale(s, 4))
    nuevo = {n: centro + (p - centro) * s + Vector((0, 0, sube)) for n, p in antes.items()}
    for o in objs:
        o.location = nuevo[o.name] - (nuevo[o.parent.name] if o.parent and o.parent.name in nuevo else Vector())


def a_hueso(obj, esq, hueso):
    """Pega el objeto a un hueso sin moverlo de donde está en reposo."""
    b = esq.data.bones[hueso]; mw = obj.matrix_world.copy()
    obj.parent = esq; obj.parent_type = "BONE"; obj.parent_bone = hueso
    obj.matrix_parent_inverse = (esq.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
    obj.matrix_basis = mw


# ───────────── armar un personaje ─────────────
def construir(nombre):
    est = ESTILOS[nombre]; calle = "traje" not in est      # ropa de calle o traje entero (ver ESTILOS)
    b, P = esqueleto_bvh(est["escala"])
    esq = crear_armadura(nombre, b, P)
    mats = {"piel": material(f"piel_{nombre}", est["piel"], .5, sss=.25)}
    if calle:
        mats.update(camisa=material(f"camisa_{nombre}", est["camisa"], .75, tela=.4),
                    franja=material(f"franja_{nombre}", est["franja"], .7, tela=.4),
                    short=material(f"short_{nombre}", est["short"], .8, tela=.5),
                    media=material(f"media_{nombre}", est["media"], .8, tela=.3),
                    zapato=material(f"zapato_{nombre}", est["zapato"], .45),
                    suela=material(f"suela_{nombre}", est["suela"], .7))
    else:
        mats.update(traje=material(f"traje_{nombre}", est["traje"], .32, emision=est.get("brillo"), fuerza=.25, tela=.15),
                    oro=material(f"oro_{nombre}", est["oro"], .3, metal=.8, emision="#b08010", fuerza=.6),
                    bota=material(f"bota_{nombre}", "#eef0f6", .28, emision=est.get("brillo"), fuerza=.15),
                    suela=material(f"suela_{nombre}", "#cfd4de", .5))
    ob, formas = cuerpo(nombre, est, b, P)
    V, W, juntas = pesos(ob, formas, P)
    ropa(ob, est, V, W, juntas, P, mats)
    ob.parent = esq
    md = ob.modifiers.new("esqueleto", "ARMATURE"); md.object = esq
    cab, ojos, bo, _ = cabeza(nombre, est, P, calle)
    escalar_cabeza(cab, B(P["Head"]), est["cabeza"], .055)
    a_hueso(cab, esq, "Head")
    # (un accesorio rígido, p. ej. un emblema en el pecho, se arma con elipsoide() y se pega al hueso con a_hueso())
    col = bpy.data.collections.new(nombre); bpy.context.scene.collection.children.link(col)
    for o in [esq, ob, cab] + list(cab.children_recursive) + [o for o in bpy.data.objects if o.parent == esq]:
        for c_ in list(o.users_collection): c_.objects.unlink(o)
        if o.name not in col.objects: col.objects.link(o)
    return esq


def cargar(nombre):
    """Trae el personaje de biblioteca/personajes.blend a la escena actual (copia, no enlace: la
    escena lo anima)."""
    with bpy.data.libraries.load(str(BLEND), link=False) as (src, dst):
        dst.collections = [nombre]
    col = dst.collections[0]; bpy.context.scene.collection.children.link(col)
    esq = next(o for o in col.objects if o.type == "ARMATURE")
    ob = {o.name.split(".")[0]: o for o in col.all_objects}
    return dict(esq=esq, ojos=[ob[f"{nombre}_ojo-1"], ob[f"{nombre}_ojo1"]], boca=ob[f"{nombre}_boca"],
                cabeza=ob[f"{nombre}_cabeza"], objetos=ob)


# ───────────── construir la biblioteca y probarla ─────────────
def _limpiar():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)


def _prueba(carpeta):
    """Renders de control: de frente en reposo, caminando y sentado (con captura de movimiento real)."""
    sys.path.insert(0, str(RAIZ / "herramientas"))
    from actor import Actor, Biblioteca, Pista, Segmento
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
    _limpiar()
    sc = bpy.context.scene
    nombres = list(ESTILOS)
    ch = {n: cargar(n) for n in nombres}
    xs = {n: (i - (len(nombres) - 1) / 2) * .7 for i, n in enumerate(nombres)}   # uno al lado del otro, a 70 cm
    bib = Biblioteca(RAIZ / "externos" / "mocap")
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.35, .4, .5, 1); w.node_tree.nodes["Background"].inputs[1].default_value = .6
    bpy.ops.object.light_add(type="SUN"); sol = bpy.context.object; sol.data.energy = 3.5; sol.rotation_euler = (.9, .1, .6)
    bpy.ops.object.light_add(type="AREA", location=(-2, -3, 2)); rel = bpy.context.object; rel.data.energy = 150; rel.data.size = 3
    rel.rotation_euler = (1.1, 0, -.6)
    bpy.ops.mesh.primitive_plane_add(size=20); suelo = bpy.context.object
    suelo.data.materials.append(material("suelo", "#9a8f80", .9))
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 50
    def enfoca(pos, obj):
        cam.location = Vector(pos); cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (Vector(obj) - Vector(pos)).to_track_quat("-Z", "Y")
    def posar(nombre, R, P):
        esq = ch[nombre]["esq"]
        for hb, M in bases(esq, R, P).items(): esq.pose.bones[hb].matrix_basis = M
    lado = lambda x: 1.0 if x > 0 else -1.0                   # el perfil se toma desde afuera del grupo
    tomas = [
        ("reposo", {}, ((0, -3.2, .75), (0, 0, .6))),
        ("camina", {n: ("07_01", 1.0 + .5 * i, (xs[n], 0, 0)) for i, n in enumerate(nombres)}, ((1.6, -2.6, 1.0), (0, 0, .55))),
        ("sentado", {n: ("14_29", 18.0 - 7 * i, (xs[n], .45, 0)) for i, n in enumerate(nombres)}, ((.2, -2.4, .7), (0, 0, .5))),
        ("cara", {}, ((.25, -.9, .95), (0, 0, .92))),
        ("espalda", {}, ((.7, 1.6, 1.25), (0, 0, .9))),
    ] + [(f"perfil-{n}", {}, ((xs[n] + lado(xs[n]), -.12, .98), (xs[n], 0, .95))) for n in nombres]
    for n, (clave, poses, (cp, co)) in enumerate(tomas):
        for nombre in nombres:
            esq = ch[nombre]["esq"]; esq.location = (xs[nombre], 0, 0) if not poses else (0, 0, 0)
            for pb in esq.pose.bones: pb.matrix_basis = Matrix.Identity(4)
            if nombre in poses:
                clip, t, off = poses[nombre]
                act = Actor(bib.clip("01_06"), ESTILOS[nombre]["escala"])
                pista = Pista(bib, [Segmento(0, 100, clip, t, t + 3)])
                loc, cad, _ = pista.pose(0, 0)
                altura = act.alto_cadera(cad) if clip != "14_29" else .45 + .1
                R, P = act.fk(loc, np.array([off[0], altura, 0]))
                posar(nombre, R, P)
        enfoca(cp, co)
        bpy.context.view_layer.update()
        sc.render.filepath = str(carpeta / f"{n}-{clave}.png")
        bpy.ops.render.render(write_still=True)
    print("PRUEBA_LISTA")


def _hoja(carpeta):
    """Las mismas vistas de las hojas de modelo (biblioteca/referencias/): cuerpo entero de frente, tres
    cuartos, perfil, espalda y tres cuartos de espalda, y la cabeza de frente, perfil, tres cuartos,
    espalda, arriba y abajo. Cámara ortográfica, brazos bajados a pose A, para comparar lado a lado."""
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
    _limpiar()
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.render.resolution_x, sc.render.resolution_y = 512, 768
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.5, .52, .55, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    bpy.ops.object.light_add(type="SUN"); sol = bpy.context.object; sol.data.energy = 2.5; sol.rotation_euler = (.7, 0, -.4)
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.type = "ORTHO"; cam.rotation_mode = "QUATERNION"
    for nombre in ESTILOS:
        ch = cargar(nombre); esq = ch["esq"]
        for l, s in (("Left", 1), ("Right", -1)):                     # pose A: brazos 55° abajo desde la T
            pb = esq.pose.bones[f"{l}Arm"]; pb.rotation_mode = "XYZ"
        bpy.context.view_layer.update()
        for l, s in (("Left", 1), ("Right", -1)):
            pb = esq.pose.bones[f"{l}Arm"]
            eje = (esq.matrix_world @ pb.bone.matrix_local).to_3x3().inverted() @ Vector((0, 1, 0))
            pb.rotation_mode = "AXIS_ANGLE"; pb.rotation_axis_angle = (s * math.radians(55), *eje)
        bpy.context.view_layer.update()
        hc = esq.matrix_world @ esq.pose.bones["Head"].head + Vector((0, .02, .14))   # centro del cráneo
        pies = min((esq.matrix_world @ esq.pose.bones[f"{l}ToeBase"].head).z for l in ("Left", "Right")) - .03
        alto = hc.z + .2 - pies; mitad = Vector((0, 0, pies + alto / 2))
        vistas = [("frente", 0), ("tres-cuartos", 40), ("perfil", 90), ("espalda", 180), ("tres-cuartos-espalda", 220)]
        for k, (clave, ang) in enumerate(vistas):
            a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0))
            cam.location = mitad + d * 6; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            cam.data.ortho_scale = alto * 1.08
            sc.render.filepath = str(carpeta / f"{nombre}_cuerpo{k}-{clave}.png"); bpy.ops.render.render(write_still=True)
        cabezas = [("frente", 0, 0), ("perfil", 90, 0), ("tres-cuartos", 35, 0), ("espalda", 180, 0), ("arriba", 0, 80), ("abajo", 0, -60)]
        for k, (clave, ang, alt) in enumerate(cabezas):
            a, e = math.radians(ang), math.radians(alt)
            d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            cam.location = hc + d * 3; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            cam.data.ortho_scale = .8 * ESTILOS[nombre]["escala"] / .036
            sc.render.filepath = str(carpeta / f"{nombre}_cabeza{k}-{clave}.png"); bpy.ops.render.render(write_still=True)
        esq.location = (0, 0, -50)
    print("HOJA_LISTA")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args[:1] == ["--hoja"]:
        _hoja(args[1])
    if args[:1] == ["--construir"]:
        if not ESTILOS: sys.exit("ESTILOS está vacío: agrega tu personaje (plantilla al principio del archivo)")
        _limpiar()
        for n in ESTILOS: construir(n)
        BLEND.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
        print("BIBLIOTECA_LISTA", BLEND)
    elif args[:1] == ["--prueba"]:
        _prueba(args[1])
