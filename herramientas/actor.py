"""Actuación con captura de movimiento: aplica clips BVH (actores reales) a un esqueleto con otras
proporciones, mezcla clips y parte el cuerpo (piernas de un clip, brazos de otro). Sólo numpy.

    bib = Biblioteca(RAIZ / "externos" / "mocap")
    act = Actor(bib.clip("01_06"), escala=0.034)      # el esqueleto (longitudes) sale de este clip
    pista = Pista(bib, [ Segmento(t0=0, t1=5, clip="01_06", desde=7.6, hasta=11.2, bucle=True), ... ])
    rot, pos = act.fk(pista.pose(t, rumbo), cadera=(x, y, z))   # rotación 3×3 y posición (m) por articulación

Todo en ejes del BVH (Y hacia arriba, mirando a +Z con rumbo 0). Rumbo = ángulo hacia donde mira el
cuerpo, como en three.js: dirección (sen r, 0, cos r).
"""
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from bvh import Bvh


# ───────────── cuaterniones (w, x, y, z) ─────────────
def q_mul(a, b):
    w1, x1, y1, z1 = np.moveaxis(a, -1, 0); w2, x2, y2, z2 = np.moveaxis(b, -1, 0)
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], -1)


def q_eje(eje, rad):
    h = np.asarray(rad) / 2
    q = np.zeros(np.shape(h) + (4,)); q[..., 0] = np.cos(h); q[..., "XYZ".index(eje) + 1] = np.sin(h)
    return q


def q_mat(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def mat_q(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1) * 2; return np.array([s / 4, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s])
    i = int(np.argmax([m[0, 0], m[1, 1], m[2, 2]])); j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
    q = np.zeros(4); q[0] = (m[k, j] - m[j, k]) / s; q[i + 1] = s / 4; q[j + 1] = (m[j, i] + m[i, j]) / s; q[k + 1] = (m[k, i] + m[i, k]) / s
    return q


def slerp(a, b, u):
    """Interpolación suave entre dos cuaterniones (o arreglos de cuaterniones)."""
    d = np.sum(a * b, -1, keepdims=True)
    b = np.where(d < 0, -b, b); d = np.abs(d)
    r = a * (1 - u) + b * u                                   # nlerp: de sobra entre poses cercanas
    return r / np.linalg.norm(r, axis=-1, keepdims=True)


def rot_y(rad):
    c, s = math.cos(rad), math.sin(rad)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def ang(a):
    return math.atan2(math.sin(a), math.cos(a))


# ───────────── clips ─────────────
class Clip:
    """Un BVH con las rotaciones locales de todos los cuadros ya pasadas a cuaterniones."""
    def __init__(self, ruta):
        self.b = Bvh(ruta)
        self.nombre, self.fps, self.n = self.b.nombre, self.b.fps, self.b.n
        self.joints = [j for j in self.b.joints if j in self.b.canales]
        self.q = np.zeros((self.n, len(self.joints), 4))
        for k, j in enumerate(self.joints):
            q = np.tile([1.0, 0, 0, 0], (self.n, 1)); d = self.b.datos[j]
            for c, canal in enumerate(self.b.canales[j]):
                if canal.endswith("rotation"):
                    q = q_mul(q, q_eje(canal[0], np.radians(d[:, c])))
            self.q[:, k] = q
        self.cadera = self.b.datos["Hips"][:, :3]
        self.idx = {j: k for k, j in enumerate(self.joints)}

    def cuadro(self, t):
        """t en segundos desde el primer cuadro con movimiento (el cuadro 0 es la pose en T)."""
        return min(max(1 + t * self.fps, 1), self.n - 1)

    def muestra(self, t):
        f = self.cuadro(t); f0 = int(f); f1 = min(f0 + 1, self.n - 1); u = f - f0
        return slerp(self.q[f0], self.q[f1], u), self.cadera[f0] * (1 - u) + self.cadera[f1] * u


class Biblioteca:
    def __init__(self, carpeta):
        self.carpeta, self.cache = Path(carpeta), {}

    def clip(self, nombre):
        if nombre not in self.cache:
            self.cache[nombre] = Clip(self.carpeta / f"{nombre}.bvh")
        return self.cache[nombre]


# ───────────── pistas de actuación ─────────────
@dataclass
class Segmento:
    t0: float                  # desde cuándo (s del video)
    t1: float                  # hasta cuándo
    clip: str
    desde: float               # tramo del clip (s)
    hasta: float
    bucle: bool = False        # repetir el tramo (con fundido en la costura)
    vel: float = 1.0
    ref: str = "cadera"        # cómo medir hacia dónde mira el actor: "cadera" o "cabeza" (acostado)
    arriba: tuple = None       # (clip, desde, hasta, bucle): el torso y los brazos salen de otro clip
    peso_arriba: object = 1.0  # número o función t → 0..1
    fundido: float = .4        # fundido de entrada desde el segmento anterior (s)
    fijo: dict = field(default_factory=dict)   # articulación → cuaternión fijo (p. ej. piernas quietas al planear)


class Pista:
    ARRIBA = None  # se llena con las articulaciones del torso para arriba

    def __init__(self, bib, segmentos):
        self.bib, self.segs = bib, segmentos
        self._yaw = {}

    def _muestra(self, clip, desde, hasta, bucle, s, t):
        c = self.bib.clip(clip)
        ct = desde + (t - s.t0) * s.vel
        if not bucle:
            q, cad = c.muestra(min(ct, hasta)); return c, q, cad
        # bucle sin salto: el ciclo dura L - F y, al empezar cada vuelta, el final del tramo se funde con el principio
        F = min(.5, (hasta - desde) / 3); Lc = hasta - desde - F
        v = ct - desde; u = v % Lc
        q, cad = c.muestra(desde + u)
        if v >= Lc and u < F:
            q0, cad0 = c.muestra(desde + u + Lc); w = u / F
            q = slerp(q0, q, w); cad = cad0 * (1 - w) + cad * w
        return c, q, cad

    def _yaw_ref(self, clip, t, ref):
        key = (clip, round(t, 3), ref)
        if key not in self._yaw:
            c = self.bib.clip(clip); R, P = c.b.pose(c.cuadro(t))
            if ref == "cabeza":
                d = P["Head"] - P["Hips"]; self._yaw[key] = math.atan2(d[0], d[2])
            else:
                f = R["Hips"] @ np.array([0, 0, 1.0]); self._yaw[key] = math.atan2(f[0], f[2])
        return self._yaw[key]

    def _pose_seg(self, s, t, rumbo):
        c, q, cad = self._muestra(s.clip, s.desde, s.hasta, s.bucle, s, t)
        q = q.copy()
        if s.arriba:
            ca, da, ha, ba = s.arriba
            clip_a = self.bib.clip(ca)
            _, qa, _ = self._muestra(ca, da, ha, ba, s, t)
            w = s.peso_arriba(t) if callable(s.peso_arriba) else s.peso_arriba
            for j in Pista.ARRIBA:
                if j in c.idx and j in clip_a.idx:
                    q[c.idx[j]] = slerp(q[c.idx[j]], qa[clip_a.idx[j]], w)
        for j, qf in s.fijo.items():
            q[c.idx[j]] = qf
        # la cadera gira para que el actor mire hacia `rumbo`
        corr = rumbo - self._yaw_ref(s.clip, s.desde, s.ref)
        q[c.idx["Hips"]] = q_mul(q_eje("Y", corr), q[c.idx["Hips"]])
        return {j: q[k] for j, k in c.idx.items()}, cad, c

    def pose(self, t, rumbo):
        """Rotaciones locales (cuaterniones) de cada articulación, la cadera del clip y el clip actual."""
        i = next((k for k, s in enumerate(self.segs) if s.t0 <= t < s.t1), len(self.segs) - 1 if t >= self.segs[-1].t0 else 0)
        s = self.segs[i]
        loc, cad, c = self._pose_seg(s, t, rumbo)
        if i > 0 and t < s.t0 + s.fundido:
            u = (t - s.t0) / s.fundido; u = u * u * (3 - 2 * u)
            loc0, cad0, _ = self._pose_seg(self.segs[i - 1], t, rumbo)
            loc = {j: slerp(loc0[j], q, u) if j in loc0 else q for j, q in loc.items()}
            cad = cad0 * (1 - u) + cad * u
        return loc, cad, s


# ───────────── el esqueleto que actúa ─────────────
class Actor:
    def __init__(self, clip_esqueleto, escala):
        self.b = clip_esqueleto.b
        self.s = escala
        self.joints = self.b.joints
        # alto de la cadera sobre el suelo en la pose en T (para apoyar los pies)
        R, P = self.b.pose(0)
        self.suelo_bvh = min(P["LeftToeBase"][1], P["RightToeBase"][1]) - .6
        if Pista.ARRIBA is None:
            arriba, pila = [], ["LowerBack"]
            while pila:
                j = pila.pop(); arriba.append(j); pila += self.b.hijos[j]
            Pista.ARRIBA = [j for j in arriba if not j.endswith("_fin")]

    def fk(self, locales, cadera):
        """Rotaciones globales (3×3) y posiciones (m) con las longitudes de ESTE esqueleto."""
        R, P = {}, {}
        for j in self.joints:
            q = locales.get(j)
            Rl = q_mat(q) if q is not None else np.eye(3)
            p = self.b.padre[j]
            if p is None:
                R[j] = Rl; P[j] = np.asarray(cadera, float)
            else:
                R[j] = R[p] @ Rl; P[j] = P[p] + R[p] @ (self.b.offset[j] * self.s)
        return R, P

    def alto_cadera(self, cad_clip):
        """Altura de la cadera sobre el suelo para un clip de pie (la del actor, a esta escala)."""
        return (cad_clip[1] - self.suelo_bvh) * self.s


def mirar(R, P, junta, objetivo, peso=1.0, max_giro=80, max_cabeceo=40, torso="Spine1"):
    """Orienta la cabeza hacia el objetivo manteniéndola derecha (sin torcerla de costado), con los
    límites de un cuello: giro y cabeceo medidos respecto del torso."""
    d = np.asarray(objetivo, float) - P[junta]; n = np.linalg.norm(d)
    if n < 1e-6 or peso <= 0:
        return
    T = R[torso]; dl = T.T @ (d / n)
    giro = max(-math.radians(max_giro), min(math.radians(max_giro), math.atan2(dl[0], dl[2])))
    cab = max(-math.radians(max_cabeceo), min(math.radians(max_cabeceo), math.asin(max(-1, min(1, dl[1])))))
    d2 = T @ np.array([math.sin(giro) * math.cos(cab), math.sin(cab), math.cos(giro) * math.cos(cab)])
    arriba = np.array([0, 1.0, 0])
    x = np.cross(arriba, d2); x /= np.linalg.norm(x); y = np.cross(d2, x)
    Rt = np.column_stack([x, y, d2])
    R[junta] = q_mat(slerp(mat_q(R[junta]), mat_q(Rt), peso))
