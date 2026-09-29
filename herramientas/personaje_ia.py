"""Personajes hechos con IA (Hunyuan3D: malla de una pieza con textura) llevados a la biblioteca de Blender
con el mismo contrato que `personajes.py`: esqueleto con los huesos del BVH de CMU, ojos que parpadean,
boca que habla. Se guardan en biblioteca/personajes_ia.blend (+ .json con las medidas del esqueleto).

    externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup -P herramientas/personaje_ia.py -- --foto <nombre> <carpeta>
    externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup -P herramientas/personaje_ia.py -- --construir
    externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup -P herramientas/personaje_ia.py -- --prueba <carpeta>

La malla viene en pose A (brazos abajo, piernas casi juntas) y con otras proporciones que el actor de la
captura (cabeza grande, piernas cortas). Por eso el esqueleto se arma con las articulaciones de ESTA malla
y cada hueso guarda Q: la rotación que lleva su dirección en el reposo del BVH (en T) a la de la malla.
Para posar: el actor de la captura da las rotaciones globales R; las posiciones se recalculan con los
largos de este esqueleto (`ActorIA.fk`) y cada hueso se lleva con R · Qᵀ (`bases`).
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "herramientas"))
import personajes as pj                                  # noqa: E402  (B, BR, C3, material, elipsoide, a_hueso…)

BLEND = RAIZ / "biblioteca" / "personajes_ia.blend"
MEDIDAS = RAIZ / "biblioteca" / "personajes_ia.json"
MODELOS = RAIZ / "recursos" / "modelos3d"
CARAS = 120_000                                            # la malla de 500 mil caras se baja a esto para animar

# Cada personaje hecho con IA se anota aquí después de medir su malla (medir_glb.py y --foto). Viene VACÍO.
# Coordenadas de Blender del .glb importado, antes de escalar: +X la izquierda del personaje, −Y adelante, Z arriba,
# los pies en 0. Sólo el lado izquierdo: el derecho es el espejo en X. Plantilla:
#   "mi_personaje": dict(
#       glb="mi_personaje.glb",          # en recursos/modelos3d/
#       escala=1.0,                      # lleva la malla a la altura que esperan las cámaras de la escena
#       escala_actor=.036,               # escala del esqueleto de la captura (.036 ≈ un niño de unos 10 años)
#       cara_z=.92,                      # altura de la cara en metros (para las cámaras de --prueba)
#       juntas={"Hips": (0, 0, z), "LeftUpLeg": (x, y, z), ...},
#       cabeza_desde=(z0, z1),           # de la barbilla para arriba la malla va rígida con Head
#                                        # (transición ancha: si es corta, al mirar arriba se abre el cuello)
#       ojo=(x, z), ojo_radio=(rx, rz), piel_sobre_ojo=-.035,   # centro del ojo (±x) y dónde tomar el color de la piel
#       boca=(x, z), boca_ancho=.02,
#       franja=(z0, z1),                 # opcional: banda donde el modelo inventó un detalle (arreglar_textura)
#   ),
# Juntas que hay que medir: Hips, LeftUpLeg, LeftLeg, LeftFoot, LeftToeBase, LeftToeBase_fin, Spine, Spine1, Neck1,
# Head, Head_fin, LeftArm, LeftForeArm, LeftHand, LeftHandIndex1, LeftHandIndex1_fin y LThumb_fin (las demás toman
# la posición de su padre: IGUAL_AL_PADRE).
AJUSTES = {}
IGUAL_AL_PADRE = ("LHipJoint", "RHipJoint", "LowerBack", "Neck", "LeftShoulder", "RightShoulder",
                  "LeftFingerBase", "RightFingerBase", "LThumb", "RThumb")


def espejo(j):
    for a, b in (("Left", "Right"), ("LThumb", "RThumb")):
        if j.startswith(a): return b + j[len(a):]
    return None


def juntas_bvh(nombre, b):
    """Posición de cada articulación del BVH en la malla escalada, en el marco del BVH (Y arriba, +Z adelante)."""
    aj = AJUSTES[nombre]; s = aj["escala"]; J = {}
    for j, p in aj["juntas"].items():
        J[j] = np.asarray(p, float)
        if espejo(j): J[espejo(j)] = J[j] * np.array([-1, 1, 1])
    out = {}
    for j in b.joints:                                     # en orden: el padre siempre antes que el hijo
        if j in J: out[j] = pj.C3.T @ (J[j] * s)
        elif j in IGUAL_AL_PADRE: out[j] = out[b.padre[j]].copy()
        else: raise KeyError(f"falta la articulación {j} de {nombre}")
    return out


# ───────────── malla ─────────────
def importar(nombre):
    """Importa el .glb, lo baja a CARAS caras y lo escala. Devuelve el objeto (Blender, Z arriba)."""
    aj = AJUSTES[nombre]
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(MODELOS / aj["glb"]))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    ob = next(o for o in nuevos if o.type == "MESH")
    for o in nuevos:
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None; ob.name = f"{nombre}_cuerpo"; ob.data.name = f"{nombre}_cuerpo"
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    md = ob.modifiers.new("bajar", "DECIMATE"); md.ratio = CARAS / len(ob.data.polygons)
    bpy.ops.object.modifier_apply(modifier=md.name)
    ob.data.transform(Matrix.Scale(aj["escala"], 4))
    ob.data.shade_smooth()
    # la luz entra un poco en la piel (dispersión subsuperficial, ~4 mm, roja más lejos): sin esto la cara se ve de
    # plástico. En la ropa casi no se nota con este radio
    bsdf = next(n for n in ob.data.materials[0].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Subsurface Weight"].default_value = .25
    bsdf.inputs["Subsurface Radius"].default_value = (1, .35, .2)
    bsdf.inputs["Subsurface Scale"].default_value = .004
    return ob


def arreglar_textura(nombre, ob):
    """Ejemplo de corrección de un detalle inventado por el modelo: una franja amarilla de más en una camiseta
    azul. Pinta de azul los texeles amarillos cuyo punto 3D cae en la banda `franja`, conservando las luces y
    sombras de la tela. Para otro caso, cambiar los colores de `amarillo` y de la referencia `azul`."""
    zona = AJUSTES[nombre].get("franja")
    if not zona: return
    s = AJUSTES[nombre]["escala"]; z0, z1 = zona[0] * s, zona[1] * s
    mat = ob.data.materials[0]
    img = next(n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and "normal" not in n.image.name
               and "metallic" not in n.image.name)
    W_, H_ = img.size
    px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
    me = ob.data
    Vc = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", Vc); Vc = Vc.reshape(-1, 3); Vz = Vc[:, 2]
    uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", lv)
    amarillo = lambda c: (c[..., 0] > .3) & (c[..., 2] < .5 * c[..., 0]) & (c[..., 1] > .6 * c[..., 0])   # la piel no: es menos saturada
    tocados = []
    tris = []
    for pol in me.polygons:                               # la malla reducida tiene cuadriláteros: en abanico
        ls = list(pol.loop_indices)
        tris += [(ls[0], ls[i], ls[i + 1]) for i in range(1, len(ls) - 1)]
    for ls in tris:
        ls = list(ls); zs = Vz[lv[ls]]
        if zs.max() < z0 or zs.min() > z1 or np.abs(Vc[lv[ls], 0]).min() > .15 * s: continue   # sólo el torso (no los brazos)
        T = uv[ls] * [W_, H_]
        x0, y0 = np.floor(T.min(0)).astype(int); x1, y1 = np.ceil(T.max(0)).astype(int)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        P = np.stack([gx.ravel() + .5, gy.ravel() + .5], 1)
        a, b_, c = T; M = np.array([b_ - a, c - a]).T
        if abs(np.linalg.det(M)) < 1e-9: continue
        l12 = np.linalg.solve(M, (P - a).T).T; l0 = 1 - l12.sum(1)
        dentro = (l0 >= -.02) & (l12[:, 0] >= -.02) & (l12[:, 1] >= -.02)
        z = l0 * zs[0] + l12[:, 0] * zs[1] + l12[:, 1] * zs[2]
        ok = dentro & (z > z0) & (z < z1)
        q = P[ok].astype(int); q[:, 0] = np.clip(q[:, 0], 0, W_ - 1); q[:, 1] = np.clip(q[:, 1], 0, H_ - 1)
        tocados.append(q)
    q = np.unique(np.concatenate(tocados), axis=0)
    c = px[q[:, 1], q[:, 0]]
    am = amarillo(c)
    azul = c[(c[:, 2] > c[:, 0] + .1)]
    lum = lambda c: c[..., :3] @ np.array([.3, .59, .11])
    ref = np.median(azul[:, :3], 0); la = np.median(lum(c[am]))
    nuevo = ref[None, :] * (lum(c[am]) / la)[:, None]
    qa = q[am]; px[qa[:, 1], qa[:, 0], :3] = np.clip(nuevo, 0, 1)
    # imagen nueva (la del .glb viene empaquetada: al re-empaquetarla vuelve la original)
    nueva = bpy.data.images.new(f"color_{nombre}", W_, H_, alpha=True)
    nueva.pixels.foreach_set(px.ravel())
    ruta = MODELOS / "texturas" / f"{nombre}_color.png"; ruta.parent.mkdir(parents=True, exist_ok=True)
    nueva.filepath_raw = str(ruta); nueva.file_format = "PNG"; nueva.save(); nueva.pack()
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image == img: n.image = nueva
    print(f"franja: {am.sum()} texeles de amarillo a azul {ref.round(3)}")


# ───────────── esqueleto ─────────────
def girar(a, b):
    """Rotación mínima (3×3) que lleva la dirección a a la dirección b."""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else -np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


def medidas(b, J):
    """Q de cada hueso (del reposo en T del BVH a la pose A de la malla) y los largos del esqueleto
    expresados en el reposo del BVH (lo que usa ActorIA.fk)."""
    Q, off = {}, {}
    for j in b.joints:
        p = b.padre[j]
        hijos = [c for c in b.hijos[j] if np.linalg.norm(b.offset[c]) > 1e-6 and np.linalg.norm(J[c] - J[j]) > 1e-4]
        if hijos:
            c = max(hijos, key=lambda c: np.linalg.norm(J[c] - J[j]))
            Q[j] = girar(np.asarray(b.offset[c], float), J[c] - J[j])
        else:
            Q[j] = Q[p] if p else np.eye(3)
        off[j] = np.zeros(3) if p is None else Q[p].T @ (J[j] - J[p])
    return Q, off


def pesos(ob, esq, voxel=.008):
    """Pesos por calor (los de Blender) calculados en una copia rehecha con vóxeles y pasados a la malla:
    en la malla de la IA el calor falla entero (0 vértices con peso; tiene caras que se cruzan)."""
    px = ob.copy(); px.data = ob.data.copy(); bpy.context.scene.collection.objects.link(px)
    px.data.remesh_voxel_size = voxel
    bpy.ops.object.select_all(action="DESELECT"); px.select_set(True); bpy.context.view_layer.objects.active = px
    bpy.ops.object.voxel_remesh()
    bpy.ops.object.select_all(action="DESELECT")
    px.select_set(True); esq.select_set(True); bpy.context.view_layer.objects.active = esq
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for g in px.vertex_groups: ob.vertex_groups.new(name=g.name)
    md = ob.modifiers.new("pasar", "DATA_TRANSFER"); md.object = px; md.use_vert_data = True
    md.data_types_verts = {"VGROUP_WEIGHTS"}; md.vert_mapping = "POLYINTERP_NEAREST"
    md.layers_vgroup_select_src = "ALL"; md.layers_vgroup_select_dst = "NAME"
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(px, do_unlink=True)
    sp = ob.vertex_groups["Spine"]                          # los pocos que quedan sin peso: al torso
    for v in ob.data.vertices:
        if not any(g.weight > 1e-4 for g in v.groups): sp.add([v.index], 1.0, "REPLACE")
    ob.parent = esq
    am = ob.modifiers.new("esqueleto", "ARMATURE"); am.object = esq


def conducir(obj, eje, objetivo, canal, expr):
    """Escala `eje` de obj calculada con una expresión simple de la escala `canal` de objetivo (sin Python)."""
    fc = obj.driver_add("scale", eje); d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "var"; v.type = "TRANSFORMS"
    v.targets[0].id = objetivo; v.targets[0].transform_type = canal; v.targets[0].transform_space = "LOCAL_SPACE"
    d.expression = expr


def color_textura(ob, img, px, hit_face):
    """Color (lineal) de la textura en una cara de la malla."""
    me = ob.data; pol = me.polygons[hit_face]
    u = np.mean([me.uv_layers.active.data[i].uv[:] for i in pol.loop_indices], 0)
    W_, H_ = img.size
    c = px[int(np.clip(u[1] * H_, 0, H_ - 1)), int(np.clip(u[0] * W_, 0, W_ - 1)), :3]
    return tuple(x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c)


def boca_real(nombre, ob, p0, bw, bo):
    """La boca DEL MODELO (una boca agregada se abría encima de la pintada, que quedaba cerrada, y se
    veía burda). Se corta una tira angosta de caras en la línea de los labios (cerrada se lee como la línea de la
    boca), una deformación «abrir» baja el labio de abajo con el mentón, sube un poco el de arriba y mete los labios
    hacia adentro, y por dentro, unos milímetros atrás, van el fondo oscuro y los dientes de arriba. La escena sigue
    igual: escala Z del vacío `boca` de 1 (cerrada) a ~3,6 (abierta) → valor de «abrir» = (Z − 1) / 2,6."""
    import bmesh
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    # la malla se SEPARA por la línea de los labios (sin borrar caras: cerrada no queda hueco): las aristas entre
    # una cara de arriba y una de abajo, dentro del ancho de la boca, se duplican
    # la línea sigue la sonrisa pintada: las comisuras suben (parábola), así el corte no queda recto ni corto
    curva = lambda x: p0.z + .22 * bw * ((x - p0.x) / (1.3 * bw)) ** 2
    # antes del corte, la zona de los labios se subdivide (dos pasadas: caras de ~4 mm → ~1 mm), si no el corte
    # sigue las aristas gruesas y el borde abierto queda dentado. Plana: UV y pesos se interpolan, la textura no se mueve
    def zona(f):
        c = f.calc_center_median(); return abs(c.x - p0.x) < 1.5 * bw and abs(c.z - curva(c.x)) < .02 and c.y < p0.y + .01
    for _ in range(2):
        aristas = list({e for f in bm.faces if zona(f) for e in f.edges})
        bmesh.ops.subdivide_edges(bm, edges=aristas, cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4 and zona(f)])
    # el corte va JUSTO sobre la curva (no por las aristas que haya): cada arista que la cruza se parte en el cruce,
    # los puntos nuevos se unen dentro de cada cara y esa línea es la que se separa. Si no, en las comisuras quedan
    # astillas y huecos sueltos
    h = lambda v: v.co.z - curva(v.co.x)
    en_x = lambda v: abs(v.co.x - p0.x) < 1.3 * bw and v.co.y < p0.y + .01 and abs(h(v)) < .02
    cruzan = [e for e in bm.edges if all(en_x(v) for v in e.verts) and h(e.verts[0]) * h(e.verts[1]) < 0]
    pct = {e: h(e.verts[0]) / (h(e.verts[0]) - h(e.verts[1])) for e in cruzan}
    nuevos = [x for x in bmesh.ops.bisect_edges(bm, edges=cruzan, cuts=1, edge_percents=pct)["geom_split"]
              if isinstance(x, bmesh.types.BMVert)]
    bmesh.ops.connect_verts(bm, verts=nuevos)
    en_linea = set(nuevos)
    corte = [e for e in bm.edges if all(v in en_linea for v in e.verts) and len(e.link_faces) == 2]
    bmesh.ops.split_edges(bm, edges=corte)
    print(f"boca de {nombre}: {len(corte)} aristas separadas, a {max(abs(h(v)) for v in nuevos) * 1000:.3f} mm de la curva")
    bm.to_mesh(me); bm.free()
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    d = V - np.array(p0[:])
    d[:, 2] -= .22 * bw * (d[:, 0] / (1.3 * bw)) ** 2                      # la altura, medida desde la curva de la sonrisa
    wx = np.clip(1 - (d[:, 0] / (1.3 * bw)) ** 2, 0, 1) ** 1.5             # campana a lo ancho: cero donde acaba el corte (comisuras en punta)
    cara = (d[:, 1] < .03) & (d[:, 2] > -3 * bw) & (d[:, 2] < 2 * bw)      # sólo la cara (-Y es adelante)
    A = .55 * bw                                                           # apertura máxima (~1 cm en un niño)
    # de qué lado del corte queda cada vértice: el de su cara (los duplicados del corte van cada uno con la suya)
    lado = np.zeros(len(V), bool)
    for p in me.polygons:
        if p.center.z <= curva(p.center.x):
            for i in p.vertices: lado[i] = True
    abajo = np.where(np.abs(d[:, 2]) < 1e-4, lado, d[:, 2] < 0)            # sobre el corte: el lado de su cara
    dz = np.where(abajo, -A * np.exp(-(d[:, 2] / (2.0 * bw)) ** 2), .22 * A * np.exp(-(d[:, 2] / (.7 * bw)) ** 2))
    dy = .35 * A * np.exp(-(d[:, 2] / (.45 * bw)) ** 2)                     # los labios se meten hacia adentro
    m = (wx * cara)[:, None]
    ob.shape_key_add(name="Basis", from_mix=False)
    k = ob.shape_key_add(name="abrir", from_mix=False)
    k.data.foreach_set("co", (V + m * np.stack([np.zeros_like(dz), dy, dz], 1)).ravel())
    fc = k.driver_add("value"); dr = fc.driver; dr.type = "SCRIPTED"
    v = dr.variables.new(); v.name = "var"; v.type = "TRANSFORMS"
    v.targets[0].id = bo; v.targets[0].transform_type = "SCALE_Z"; v.targets[0].transform_space = "LOCAL_SPACE"
    dr.expression = "min(1, max(0, (var - 1) / 2.6))"
    # expresiones: una deformación por cada una, manejada por una propiedad del vacío `boca` (0 a 1). Mueven los dos
    # labios juntos en las comisuras, así cerrada no se abre. Las escenas que no las usan quedan igual (valen 0)
    r = np.clip(np.abs(d[:, 0]) / (1.3 * bw), 0, 1.5)                        # 0 en el centro, 1 en la comisura
    fuera = np.exp(-(np.maximum(np.abs(d[:, 0]) - 1.3 * bw, 0) / (.7 * bw)) ** 2)
    zona_e = (cara * fuera * np.exp(-(d[:, 2] / (1.4 * bw)) ** 2))[:, None]
    sx = np.sign(d[:, 0])
    cero = np.zeros(len(V))
    exps = {
        # las comisuras suben, se abren un poco hacia afuera y se meten en el cachete
        "sonrisa": zona_e * np.stack([.12 * bw * sx * r, .12 * bw * r ** 2, .32 * bw * r ** 2], 1),
        # las comisuras bajan (más de lo que sube la sonrisa pintada) y el centro del labio de abajo sube un poco
        "tristeza": zona_e * np.stack([cero, .04 * bw * r ** 2, -.55 * bw * r ** 2
                                        + .12 * bw * abajo * np.clip(1 - r, 0, 1) ** 2], 1),
        # la boca se angosta y se abre (el 80 % de «abrir»)
        "sorpresa": zona_e * np.stack([-.3 * d[:, 0] * np.clip(1 - r / 1.5, 0, 1), cero, cero], 1)
                    + .8 * m * np.stack([cero, dy, dz], 1),
    }
    for nom, D in exps.items():
        bo[nom] = 0.0
        k = ob.shape_key_add(name=nom, from_mix=False)
        k.data.foreach_set("co", (V + D).ravel())
        dr = k.driver_add("value").driver; dr.type = "AVERAGE"
        v = dr.variables.new(); v.type = "SINGLE_PROP"; v.targets[0].id = bo; v.targets[0].data_path = f'["{nom}"]'
    # radios en el orden del BVH: (ancho, alto, fondo)
    fondo = pj.elipsoide(f"{nombre}_boca_fondo", (.9 * bw, .5 * bw, .006), pj.material(f"boca_{nombre}", "#2a0c10", .7))
    fondo.location = p0 + Vector((0, .016, -.15 * bw))             # 1 cm por dentro: no asoma con la boca cerrada
    dientes = pj.elipsoide(f"{nombre}_dientes", (.7 * bw, .14 * bw, .003), pj.material(f"dientes_{nombre}", "#e9e4da", .35))
    dientes.location = p0 + Vector((0, .009, .16 * bw))
    return [fondo, dientes]


def construir(nombre):
    from bvh import Bvh
    b = Bvh(RAIZ / "externos" / "mocap" / "01_06.bvh")
    aj = AJUSTES[nombre]; s = aj["escala"]
    ob = importar(nombre)
    arreglar_textura(nombre, ob)
    J = juntas_bvh(nombre, b)
    Q, off = medidas(b, J)
    esq = pj.crear_armadura(nombre, b, J)
    esq["ia_Q"] = json.dumps({j: Q[j].tolist() for j in Q})
    pesos(ob, esq)
    # la cabeza (con el pelo) rígida en Head
    V = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    ya, yb = aj["cabeza_desde"][0] * s, aj["cabeza_desde"][1] * s          # de aquí para arriba, todo a la cabeza
    k = np.clip((V[:, 2] - ya) / (yb - ya), 0, 1)
    gh = ob.vertex_groups.get("Head") or ob.vertex_groups.new(name="Head"); hid = gh.index
    for i in np.nonzero(k > 0)[0]:
        v = ob.data.vertices[int(i)]; tiene = False
        for ge in v.groups:
            if ge.group == hid: ge.weight = ge.weight * (1 - k[i]) + k[i]; tiene = True
            else: ge.weight *= (1 - k[i])
        if not tiene: gh.add([int(i)], float(k[i]), "REPLACE")
    # cara: ojos (vacíos que la escena escala para parpadear) con párpados que se cierran, boca que se abre
    img = next(n.image for n in ob.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image
               and "normal" not in n.image.name and "metallic" not in n.image.name)
    W_, H_ = img.size; px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
    dg = bpy.context.evaluated_depsgraph_get()
    def superficie(x, z):
        ok, loc, nor, f = ob.ray_cast(Vector((x * s, -2, z * s)), Vector((0, 1, 0)))
        assert ok, (x, z); return loc, f
    ex, ez = aj["ojo"]; rx, ry = aj["ojo_radio"]
    piel = superficie(ex, ez + aj["piel_sobre_ojo"])[1]
    mpiel = bpy.data.materials.new(f"parpado_{nombre}"); mpiel.use_nodes = True
    mpiel.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color_textura(ob, img, px, piel), 1)
    mpiel.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = .55
    mpest = pj.material(f"pestana_{nombre}", aj.get("pestana", "#2a1a14"), .6)
    ojos = []
    for l in (-1, 1):
        loc, _ = superficie(l * ex, ez)
        oj = bpy.data.objects.new(f"{nombre}_ojo{l}", None); bpy.context.scene.collection.objects.link(oj)
        oj.location = loc + Vector((0, .03, 0))                    # 3 cm adentro: ahí la escena puede poner un brillo en los ojos
        pa = pj.elipsoide(f"{nombre}_parpado{l}", (rx * s, ry * s, .01 * s), mpiel, (0, -ry * s, 0))
        pa.location = loc + Vector((0, -.004, ry * s))             # el borde de arriba del ojo: crece hacia abajo
        # pestañas: una línea oscura en el borde de abajo del párpado (el ojo cerrado se lee como ojo)
        pts = [pa.location + pj.B((.95 * rx * s * math.cos(a), -ry * s - .95 * ry * s * math.sin(a), .004))
               for a in np.linspace(.15, math.pi - .15, 9)]
        pe = pj.tubo(f"{nombre}_pest{l}", pts, [.5 + .5 * math.sin(a) for a in np.linspace(.15, math.pi - .15, 9)],
                     .0022, mpest)
        bpy.context.view_layer.update()                            # join usa matrix_world
        bpy.ops.object.select_all(action="DESELECT"); pe.select_set(True); pa.select_set(True)
        bpy.context.view_layer.objects.active = pa; bpy.ops.object.join()
        for e in range(3): conducir(pa, e, oj, "SCALE_Z", "(1 - var) * 1.14")
        ojos += [oj, pa]
    mx, mz = aj["boca"]; loc, _ = superficie(mx, mz)
    bo = bpy.data.objects.new(f"{nombre}_boca", None); bpy.context.scene.collection.objects.link(bo); bo.location = loc
    dentro = boca_real(nombre, ob, loc, aj["boca_ancho"] * s, bo)
    bpy.context.view_layer.update()                               # a_hueso lee matrix_world
    for o in ojos + [bo] + dentro: pj.a_hueso(o, esq, "Head")
    col = bpy.data.collections.new(nombre); bpy.context.scene.collection.children.link(col)
    for o in [esq, ob] + ojos + [bo] + dentro:
        for c_ in list(o.users_collection): c_.objects.unlink(o)
        col.objects.link(o)
    return dict(off={j: off[j].tolist() for j in off}, alto_cadera=float(J["Hips"][1]),
                cabeza=float(J["Head"][1]))


PIEL_MATE = True       # False: la piel como salió de la biblioteca (para comparar antes y después)


def piel_mate(ob):
    """La piel dejaba de parecer piel (en la revisión se veía «de cera»). Medido en la textura de la IA:
    la piel del visitante trae metal (medio 0,10, p90 0,24) y una aspereza casi igual en toda la cara (0,525–0,557).
    Se deja el metal sólo donde es metal de verdad (el dorado, > 0,3), la aspereza varía un poco (ruido fino),
    un relieve de poros muy suave y menos dispersión subsuperficial."""
    m = ob.data.materials[0]; nt = m.node_tree; N = nt.nodes
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    sep = next(n for n in N if n.type == "SEPARATE_COLOR")
    mayor = N.new("ShaderNodeMath"); mayor.operation = "GREATER_THAN"; mayor.inputs[1].default_value = .3
    metal = N.new("ShaderNodeMath"); metal.operation = "MULTIPLY"
    nt.links.new(sep.outputs["Blue"], mayor.inputs[0]); nt.links.new(sep.outputs["Blue"], metal.inputs[0])
    nt.links.new(mayor.outputs[0], metal.inputs[1]); nt.links.new(metal.outputs[0], b.inputs["Metallic"])
    coord = N.new("ShaderNodeTexCoord")
    ruido = N.new("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = 900; ruido.inputs["Detail"].default_value = 4
    nt.links.new(coord.outputs["Object"], ruido.inputs["Vector"])
    varia = N.new("ShaderNodeMath"); varia.operation = "MULTIPLY_ADD"
    varia.inputs[1].default_value = .16; varia.inputs[2].default_value = -.04     # ±0,08 alrededor de +0,04 (más áspera)
    nt.links.new(ruido.outputs["Fac"], varia.inputs[0])
    aspera = N.new("ShaderNodeMath"); aspera.operation = "ADD"; aspera.use_clamp = True
    nt.links.new(sep.outputs["Green"], aspera.inputs[0]); nt.links.new(varia.outputs[0], aspera.inputs[1])
    nt.links.new(aspera.outputs[0], b.inputs["Roughness"])
    nm = next(n for n in N if n.type == "NORMAL_MAP")
    poros = N.new("ShaderNodeBump"); poros.inputs["Strength"].default_value = .08; poros.inputs["Distance"].default_value = .0004
    nt.links.new(ruido.outputs["Fac"], poros.inputs["Height"]); nt.links.new(nm.outputs["Normal"], poros.inputs["Normal"])
    nt.links.new(poros.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Subsurface Weight"].default_value = .15


def cargar(nombre):
    """Como personajes.cargar: trae el personaje de biblioteca/personajes_ia.blend (copia, no enlace)."""
    with bpy.data.libraries.load(str(BLEND), link=False) as (src, dst):
        dst.collections = [nombre]
    col = dst.collections[0]; bpy.context.scene.collection.children.link(col)
    esq = next(o for o in col.objects if o.type == "ARMATURE")
    ob = {o.name.split(".")[0]: o for o in col.all_objects}
    if PIEL_MATE: piel_mate(ob[f"{nombre}_cuerpo"])
    return dict(esq=esq, ojos=[ob[f"{nombre}_ojo-1"], ob[f"{nombre}_ojo1"]], boca=ob[f"{nombre}_boca"],
                cabeza=ob[f"{nombre}_cuerpo"], objetos=ob)


def _actor_base():
    from actor import Actor
    return Actor


class ActorIA(_actor_base()):
    """El actor de la captura con los largos del esqueleto de la malla: mismas rotaciones, otras posiciones."""
    def __init__(self, clip_esqueleto, escala, nombre):
        super().__init__(clip_esqueleto, escala)
        m = json.loads(MEDIDAS.read_text(encoding="utf-8"))[nombre]
        self.off = {j: np.asarray(v, float) for j, v in m["off"].items()}
        R0, P0 = self.b.pose(0)
        self.k = m["alto_cadera"] / super().alto_cadera(P0["Hips"])   # piernas más cortas que las del actor

    def fk(self, locales, cadera):
        from actor import q_mat
        R, P = {}, {}
        for j in self.joints:
            q = locales.get(j)
            Rl = q_mat(q) if q is not None else np.eye(3)
            p = self.b.padre[j]
            if p is None: R[j] = Rl; P[j] = np.asarray(cadera, float)
            else: R[j] = R[p] @ Rl; P[j] = P[p] + R[p] @ self.off[j]
        return R, P

    def alto_cadera(self, cad_clip):
        return super().alto_cadera(cad_clip) * self.k


def _foto(nombre, carpeta):
    """Frente y perfil ortográficos de la malla con una bolita en cada articulación, para ajustarlas."""
    sys.path.insert(0, str(RAIZ / "herramientas"))
    from bvh import Bvh
    carpeta = Path(carpeta).resolve(); carpeta.mkdir(parents=True, exist_ok=True)   # absoluta: si no, Blender escribe en C:\render
    pj._limpiar()
    ob = importar(nombre)
    J = juntas_bvh(nombre, Bvh(RAIZ / "externos" / "mocap" / "01_06.bvh"))
    rojo = pj.material("marca", "#ff2040", .5, emision="#ff2040", fuerza=3)
    marcas = []
    for j, p in J.items():
        marcas.append(pj.elipsoide(f"m_{j}", (.008, .008, .008), rojo, p, seg=12))
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.render.resolution_x, sc.render.resolution_y = 768, 1024
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; alto = max(v.co.z for v in ob.data.vertices); cam.data.ortho_scale = alto * 1.05
    for clave, d in (("frente", Vector((0, -1, 0))), ("perfil", Vector((1, 0, 0)))):
        for m in marcas: m.location = d * .5            # delante de la malla: en ortográfica no cambia dónde se ven
        cam.location = Vector((0, 0, alto / 2)) + d * 5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        sc.render.filepath = str(carpeta / f"{nombre}_{clave}.png"); bpy.ops.render.render(write_still=True)
    print("FOTO_LISTA", len(ob.data.polygons), "caras")


def _prueba(carpeta):
    """Renders de control con captura de movimiento real: de pie, caminando, sentado, y la cara con los ojos
    cerrados y la boca abierta (para ver párpados y boca)."""
    from actor import Biblioteca, Pista, Segmento
    carpeta = Path(carpeta).resolve(); carpeta.mkdir(parents=True, exist_ok=True)   # absoluta: si no, Blender escribe en C:\render
    pj._limpiar()
    sc = bpy.context.scene
    nombres = [n for n in AJUSTES if (MODELOS / AJUSTES[n]["glb"]).exists()]
    ch = {n: cargar(n) for n in nombres}
    bib = Biblioteca(RAIZ / "externos" / "mocap")
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.35, .4, .5, 1); w.node_tree.nodes["Background"].inputs[1].default_value = .6
    bpy.ops.object.light_add(type="SUN"); sol = bpy.context.object; sol.data.energy = 3.5; sol.rotation_euler = (.9, .1, .6)
    bpy.ops.mesh.primitive_plane_add(size=20); bpy.context.object.data.materials.append(pj.material("suelo", "#9a8f80", .9))
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 50
    def enfoca(pos, obj):
        cam.location = Vector(pos); cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (Vector(obj) - Vector(pos)).to_track_quat("-Z", "Y")
    x0 = {n: (i - (len(nombres) - 1) / 2) * .7 for i, n in enumerate(nombres)}   # uno al lado del otro, a 70 cm
    def cara_de(n):                                                                 # cámara de frente a la cara
        z = AJUSTES[n].get("cara_z", .92); return ((x0[n], -1.1, z + .03), (x0[n], 0, z))
    tomas = [
        ("reposo", {}, ((0, -3.2, .7), (0, 0, .6)), False),
        ("camina", {n: ("07_01", 1.0 + .5 * i) for i, n in enumerate(nombres)}, ((1.6, -2.6, 1.0), (0, 0, .55)), False),
        ("sentado", {n: ("14_29", 18.0 - 7 * i) for i, n in enumerate(nombres)}, ((.2, -2.4, .7), (0, 0, .5)), False),
        ("perfil", {}, ((1.6, -.2, .9), (0, 0, .8)), False),
    ] + [(f"{c}-{n}", {}, cara_de(n), e) for n in nombres
         for c, e in (("cara", False), ("cara-parpadea-habla", True), ("sonrisa", "sonrisa"), ("tristeza", "tristeza"),
                      ("sorpresa", "sorpresa"))]
    for n_, (clave, poses, (cp, co), cara) in enumerate(tomas):
        for nombre in nombres:
            esq = ch[nombre]["esq"]; esq.location = (0, 0, 0)
            act = ActorIA(bib.clip("01_06"), AJUSTES[nombre].get("escala_actor", .036), nombre)
            if nombre in poses:
                clip, t = poses[nombre]
                pista = Pista(bib, [Segmento(0, 100, clip, t, t + 3)])
                loc, cad, _ = pista.pose(0, 0)
                altura = act.alto_cadera(cad) if clip != "14_29" else .45 + .1
                R, P = act.fk(loc, np.array([x0[nombre], altura, 0]))
                for hb, M in pj.bases(esq, R, P).items(): esq.pose.bones[hb].matrix_basis = M
            else:                                                  # reposo: la pose A de la malla
                for pb in esq.pose.bones: pb.matrix_basis = Matrix.Identity(4)
                esq.location = (x0[nombre], 0, 0)
            sz = .12 if cara is True else 1
            for oj in ch[nombre]["ojos"]: oj.scale = (1, 1, sz)
            ch[nombre]["boca"].scale = (1, 1, 3.4 if cara is True else 1)
            for e in ("sonrisa", "tristeza", "sorpresa"): ch[nombre]["boca"][e] = 1.0 if cara == e else 0.0
        enfoca(cp, co)
        bpy.context.view_layer.update()
        sc.render.filepath = str(carpeta / f"{n_}-{clave}.png")
        bpy.ops.render.render(write_still=True)
    print("PRUEBA_LISTA")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args[:1] == ["--foto"]:
        _foto(args[1], args[2])
    elif args[:1] == ["--construir"]:
        pj._limpiar()
        todas = json.loads(MEDIDAS.read_text(encoding="utf-8")) if MEDIDAS.exists() else {}
        pedidos = args[1:] or [n for n in AJUSTES if (MODELOS / AJUSTES[n]["glb"]).exists()]
        if not pedidos: sys.exit("AJUSTES está vacío o faltan los .glb en recursos/modelos3d/ (plantilla en el archivo)")
        for n in pedidos:
            todas[n] = construir(n)
        BLEND.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
        MEDIDAS.write_text(json.dumps(todas, indent=1), encoding="utf-8")
        print("BIBLIOTECA_IA_LISTA", BLEND)
    elif args[:1] == ["--prueba"]:
        _prueba(args[1])
