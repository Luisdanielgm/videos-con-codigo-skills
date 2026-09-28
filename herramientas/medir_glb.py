"""Cortes por altura de un .glb (grupos en X con su rango en Y): para ubicar tiro, rodillas, tobillos,
hombros, codos, muñecas y cuello de un personaje hecho con IA antes de ponerle el esqueleto.

    externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup --python herramientas/medir_glb.py -- <archivo.glb>
"""
import bpy, numpy as np, sys
glb = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
n = len(ob.data.vertices); V = np.empty(n * 3); ob.data.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
print("bbox", V.min(0).round(3), V.max(0).round(3))
z0 = V[:, 2].min(); H = V[:, 2].max() - z0
for f in np.arange(0.02, 1.0, 0.02):
    z = z0 + f * H; s = V[np.abs(V[:, 2] - z) < .004]
    if len(s) == 0: continue
    xs = np.sort(s[:, 0]); gaps = np.nonzero(np.diff(xs) > .012)[0]
    grupos = []; a = 0
    for g in list(gaps) + [len(xs) - 1]:
        sel = s[(s[:, 0] >= xs[a]) & (s[:, 0] <= xs[g])]
        grupos.append((round(xs[a], 3), round(xs[g], 3), round(sel[:, 1].min(), 3), round(sel[:, 1].max(), 3))); a = g + 1
    print(f"z={z:.3f} ({f:.2f}) grupos x0,x1,y0,y1: {grupos}")
