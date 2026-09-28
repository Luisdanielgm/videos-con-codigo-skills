"""Lector de captura de movimiento BVH y cinemática directa (sin Blender, sólo numpy).

    from bvh import Bvh
    b = Bvh("externos/mocap/01_06.bvh")
    b.fps, b.n                     # cuadros por segundo y cantidad de cuadros
    R, P = b.pose(f)               # rotación global (3×3) y posición (en unidades del archivo) de cada articulación

Convenciones: ejes del archivo BVH (Y hacia arriba). En la conversión de cgspeed del CMU, el cuadro 0
es una pose en T mirando hacia +Z, y los marcos de cada articulación son paralelos al mundo en reposo:
por eso una rotación local significa lo mismo en cualquier sujeto, y se puede aplicar a otro esqueleto
(el de un niño) con otras longitudes.
"""
import math
from pathlib import Path

import numpy as np


def _rot(eje, grados):
    a = math.radians(grados); c, s = math.cos(a), math.sin(a)
    if eje == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if eje == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Bvh:
    def __init__(self, ruta):
        self.nombre = Path(ruta).stem
        tok = Path(ruta).read_text().split()
        self.joints, self.padre, self.offset, self.canales = [], {}, {}, {}
        i, pila, ultimo = 0, [], None
        while tok[i] != "MOTION":
            t = tok[i]
            if t in ("ROOT", "JOINT"):
                nom = tok[i + 1]; self.joints.append(nom)
                self.padre[nom] = pila[-1] if pila else None
                ultimo = nom; i += 2
            elif t == "End":
                ultimo = pila[-1] + "_fin"; self.joints.append(ultimo); self.padre[ultimo] = pila[-1]; i += 2
            elif t == "{":
                pila.append(ultimo); i += 1
            elif t == "}":
                pila.pop(); i += 1
            elif t == "OFFSET":
                self.offset[ultimo] = np.array([float(x) for x in tok[i + 1:i + 4]]); i += 4
            elif t == "CHANNELS":
                n = int(tok[i + 1]); self.canales[ultimo] = tok[i + 2:i + 2 + n]; i += 2 + n
            else:
                i += 1
        self.n = int(tok[i + 2]); self.fps = round(1 / float(tok[i + 5]))
        datos = np.array([float(x) for x in tok[i + 6:]]).reshape(self.n, -1)
        self.datos, col = {}, 0
        for j in self.joints:
            if j in self.canales:
                k = len(self.canales[j]); self.datos[j] = datos[:, col:col + k]; col += k
        self.hijos = {j: [c for c in self.joints if self.padre[c] == j] for j in self.joints}

    def local(self, j, f):
        """Rotación local y traslación (si la tiene) de la articulación j en el cuadro f (puede ser fraccionario)."""
        if j not in self.datos:
            return np.eye(3), None
        f0 = int(min(max(f, 0), self.n - 1)); f1 = min(f0 + 1, self.n - 1); u = min(max(f - f0, 0), 1)
        v = self.datos[j][f0] * (1 - u) + self.datos[j][f1] * u   # (interpolar ángulos cerca es aceptable a 120 fps)
        R, pos = np.eye(3), None
        for c, x in zip(self.canales[j], v):
            if c.endswith("rotation"):
                R = R @ _rot(c[0], x)
            elif c == "Xposition":
                pos = np.array(v[:3])
        return R, pos

    def pose(self, f):
        R, P = {}, {}
        for j in self.joints:
            Rl, pos = self.local(j, f)
            p = self.padre[j]
            if p is None:
                R[j] = Rl; P[j] = pos if pos is not None else self.offset[j]
            else:
                R[j] = R[p] @ Rl; P[j] = P[p] + R[p] @ self.offset[j]
        return R, P


def yaw(R):
    """Hacia dónde mira (ángulo alrededor de Y) una rotación global: su eje +Z proyectado en el suelo."""
    fwd = R @ np.array([0, 0, 1.0])
    return math.atan2(fwd[0], fwd[2])
