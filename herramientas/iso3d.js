// Kit de la técnica 26 en 3D real (variante «ISO-GLOW 3D»): sólidos biselados con contorno, cámara isométrica verdadera
// que se puede girar, un solo acento que brilla y limpieza/restilizado de un .glb propio. Sobre three.js (local, r170).
// El mismo contrato que iso.js: cada cuadro es una FUNCIÓN PURA de t (nada de Date.now, performance.now, Math.random sin
// semilla ni estado entre cuadros); la página llama a `mundo.dibujar(ctx2d)` desde su render(t).
//
//   import { Mundo, caja, cilindro, acentuar, GLB, restilizar } from '../../herramientas/iso3d.js';
//   const m = new Mundo({ ancho: 1920, alto: 1080, tema: 'oscuro' });
//   const base = m.agregar(caja({ w: 4, h: .4, d: 3, r: .08 }), 'base');            // base en y = 0
//   const luz  = m.agregar(acentuar(caja({ w: .3, h: .3, d: .3, r: .05 })), 'luz');  // lo que está encendido
//   m.camara({ az: 45, el: 35.264, zoom: 1 });  m.dibujar(ctx);                       // 45° / 35,264° = isométrica verdadera
//
// Origen de las ideas: ISO-GLOW 3D (isoglow.dev, @Aprilzz423): órbita, ajuste isométrico, botones que funcionan y un .glb
// propio limpiado y restilizado. No se copió código; el lector de .glb es propio (no hay GLTFLoader en el three.js local).
import * as THREE from './vendor/three.module.min.js';

export { THREE };
export const ISO_EL = Math.atan(1 / Math.SQRT2) * 180 / Math.PI;      // 35,264°: los tres ejes se acortan igual

export const TEMAS = {
  oscuro: { fondo: '#0b0e13', cuerpo: '#1a2029', borde: '#5b6b80', suelo: '#10141b', acento: '#ff8a1f', brillo: .5 },
  claro:  { fondo: '#f3f0e8', cuerpo: '#e4e0d3', borde: '#23262b', suelo: '#ebe7da', acento: '#1c1c1c', brillo: 0 },
};

const GRADOS = Math.PI / 180;
const ANGULO_BORDE = 28;     // grados: más que esto entre dos caras es un borde que se dibuja

// ───────────── piezas ─────────────
// Todas nacen con la base en y = 0 y centradas en x y z. Dimensiones en unidades del mundo (1 unidad ≈ 1 cm de maqueta).
export function caja({ w = 1, h = 1, d = 1, r = .06 } = {}) {
  r = Math.min(r, w / 2 - 1e-3, d / 2 - 1e-3, h / 2 - 1e-3);
  const f = r * 2;
  const forma = new THREE.Shape();
  const x0 = -(w - f) / 2, x1 = (w - f) / 2, z0 = -(d - f) / 2, z1 = (d - f) / 2;
  forma.moveTo(x0, z0); forma.lineTo(x1, z0); forma.lineTo(x1, z1); forma.lineTo(x0, z1); forma.closePath();
  const g = new THREE.ExtrudeGeometry(forma, { depth: Math.max(h - f, 1e-3), bevelEnabled: true, bevelSize: r, bevelThickness: r,
                                               bevelSegments: 3, curveSegments: 1 });
  g.rotateX(-Math.PI / 2);                  // la extrusión (z) pasa a y; la forma (x, y) a (x, -z)
  g.translate(0, r, 0);                     // la base queda en y = 0
  return g;
}

export function cilindro({ r = .5, h = 1, seg = 40, bisel = .04 } = {}) {
  // revolución de un perfil con borde redondeado (lathe): lisa a 40 segmentos, el contorno sale en los bordes duros
  const p = [new THREE.Vector2(0, 0)];
  const b = Math.min(bisel, r / 2, h / 2);
  for (let i = 0; i <= 3; i++) { const a = i / 3 * Math.PI / 2; p.push(new THREE.Vector2(r - b + Math.sin(a) * b, b - Math.cos(a) * b)); }
  for (let i = 0; i <= 3; i++) { const a = i / 3 * Math.PI / 2; p.push(new THREE.Vector2(r - b + Math.cos(a) * b, h - b + Math.sin(a) * b)); }
  p.push(new THREE.Vector2(0, h));
  return new THREE.LatheGeometry(p, seg);
}

// marca una geometría como «lo encendido»: material propio que no recibe luz, brilla y se dibuja con su contorno claro
export function acentuar(geo) { geo.userData.acento = true; return geo; }

// ───────────── el mundo ─────────────
export class Mundo {
  constructor({ ancho = 1920, alto = 1080, tema = 'oscuro', escala = 1, cuerpo = null } = {}) {
    this.ancho = ancho; this.alto = alto; this.tema = { ...(TEMAS[tema] || TEMAS.oscuro) }; if (cuerpo) this.tema.cuerpo = cuerpo; this.nombreTema = tema in TEMAS ? tema : 'oscuro';
    this.escena = new THREE.Scene();
    this.escena.background = new THREE.Color(this.tema.fondo);
    this.gl = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.gl.setPixelRatio(1); this.gl.setSize(ancho, alto, false);
    this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -200, 200);
    this.cam.layers.enable(1);
    this.grupo = new THREE.Group(); this.escena.add(this.grupo);
    this.piezas = new Map();
    this.escalaVista = escala;
    this.luces();
    this.matCuerpo = new THREE.MeshStandardMaterial({ color: this.tema.cuerpo, roughness: .62, metalness: .12,
                                                     polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
    this.matBorde = new THREE.LineBasicMaterial({ color: this.tema.borde });
    this.matAcento = new THREE.MeshBasicMaterial({ color: this.tema.acento });
    this.matBordeAcento = new THREE.LineBasicMaterial({ color: new THREE.Color(this.tema.acento).lerp(new THREE.Color('#ffffff'), .25) });
    this.matNegro = new THREE.MeshBasicMaterial({ color: '#000000' });
    this.camara({});
  }

  luces() {
    const oscuro = this.nombreTema === 'oscuro';
    this.escena.add(new THREE.HemisphereLight(oscuro ? 0x8fa3bd : 0xffffff, oscuro ? 0x06080b : 0xcfc8b5, oscuro ? .85 : 1.05));
    const sol = new THREE.DirectionalLight(0xffffff, oscuro ? 2.2 : 1.7); sol.position.set(-3, 6, 4); this.escena.add(sol);
    const relleno = new THREE.DirectionalLight(oscuro ? 0x6f86a8 : 0xffffff, oscuro ? .7 : .35); relleno.position.set(5, 2, -3); this.escena.add(relleno);
    if (oscuro) { const borde = new THREE.DirectionalLight(0x9ab8ff, 1.4); borde.position.set(-1, 3, -6); this.escena.add(borde); }   // luz de contorno desde atrás
  }

  // Malla con su contorno. `geo` ya nace con la base en y = 0. Devuelve el grupo (se mueve con .position / .rotation).
  agregar(geo, nombre, { padre = this.grupo, pos = [0, 0, 0], giro = 0 } = {}) {
    const g = new THREE.Group(); g.name = nombre || ''; g.position.set(...pos); g.rotation.y = giro * GRADOS;
    const acento = !!geo.userData.acento;
    const malla = new THREE.Mesh(geo, acento ? this.matAcento : this.matCuerpo);
    const bordes = new THREE.LineSegments(new THREE.EdgesGeometry(geo, ANGULO_BORDE), acento ? this.matBordeAcento : this.matBorde);
    if (acento) { malla.layers.set(1); bordes.layers.set(1); }
    g.add(malla, bordes); g.userData.acento = acento;
    padre.add(g); this.piezas.set(nombre || g.id, g);
    return g;
  }

  // Cámara: az gira alrededor del eje vertical (45° es la vista isométrica), el = elevación, zoom y punto mirado.
  camara({ az = 45, el = ISO_EL, zoom = 1, mira = [0, 1, 0], ancho = 14 } = {}) {
    const a = az * GRADOS, e = el * GRADOS, d = 60;
    this.cam.position.set(mira[0] + Math.sin(a) * Math.cos(e) * d, mira[1] + Math.sin(e) * d, mira[2] + Math.cos(a) * Math.cos(e) * d);
    this.cam.up.set(0, 1, 0); this.cam.lookAt(...mira);
    const mitad = ancho / 2 / zoom, rel = this.alto / this.ancho;
    this.cam.left = -mitad; this.cam.right = mitad; this.cam.top = mitad * rel; this.cam.bottom = -mitad * rel;
    this.cam.updateProjectionMatrix(); this.cam.updateMatrixWorld(true);
    this.estado = { az, el, zoom, mira, ancho };
  }

  // Cuánto se alejó la vista de la isométrica verdadera (para el ajuste «Iso view»): 0 es exacta.
  desvioIso() { const { az, el } = this.estado; return Math.max(Math.abs(((az - 45) % 90 + 90 + 45) % 90 - 45), Math.abs(el - ISO_EL)); }

  // Pasa un punto del mundo a píxeles del cuadro (para rótulos 2D que siguen a una pieza)
  aPantalla(v) {
    const p = new THREE.Vector3(...v).project(this.cam);
    return [(p.x + 1) / 2 * this.ancho, (1 - p.y) / 2 * this.alto];
  }

  // Dibuja el cuadro en `ctx` (2D, del tamaño del mundo): el sólido y encima el resplandor del acento.
  dibujar(ctx) {
    this.cam.layers.enable(0); this.cam.layers.enable(1);
    this.gl.render(this.escena, this.cam);
    ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none'; ctx.globalAlpha = 1;
    ctx.drawImage(this.gl.domElement, 0, 0, this.ancho, this.alto);
    if (this.tema.brillo > 0 && this.hayAcento()) this.resplandor(ctx);
  }

  hayAcento() { let n = 0; this.grupo.traverse(o => { if (o.userData.acento && o.visible) n++; }); return n > 0; }

  // Resplandor: se vuelve a dibujar sólo lo encendido (lo demás en negro, para que lo tape) y se suma borroso, ancho y fino.
  resplandor(ctx) {
    const guardados = [];
    this.grupo.traverse(o => { if (o.isMesh && o.material === this.matCuerpo) { guardados.push(o); o.material = this.matNegro; } });
    const fondo = this.escena.background; this.escena.background = new THREE.Color('#000000');
    this.gl.render(this.escena, this.cam);
    this.escena.background = fondo;
    guardados.forEach(o => { o.material = this.matCuerpo; });
    const lienzo = this.pequeno || (this.pequeno = Object.assign(document.createElement('canvas'), { width: this.ancho / 4, height: this.alto / 4 }));
    const c = lienzo.getContext('2d');
    c.globalCompositeOperation = 'copy'; c.filter = 'none'; c.drawImage(this.gl.domElement, 0, 0, lienzo.width, lienzo.height);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.filter = 'blur(18px)'; ctx.globalAlpha = this.tema.brillo; ctx.drawImage(lienzo, 0, 0, this.ancho, this.alto);
    ctx.filter = 'blur(5px)'; ctx.globalAlpha = this.tema.brillo * .45; ctx.drawImage(lienzo, 0, 0, this.ancho, this.alto);
    ctx.restore();
  }

  // Encuadra todo lo que hay en el mundo en la vista actual (ajusta zoom y punto mirado; no toca az ni el)
  encuadrar(margen = 1.15) {
    const caja = new THREE.Box3().setFromObject(this.grupo);
    const c = caja.getCenter(new THREE.Vector3()), v = [];
    for (const x of [caja.min.x, caja.max.x]) for (const y of [caja.min.y, caja.max.y]) for (const z of [caja.min.z, caja.max.z]) v.push(new THREE.Vector3(x, y, z));
    const { az, el } = this.estado;
    this.camara({ az, el, zoom: 1, mira: [c.x, c.y, c.z], ancho: 10 });
    let mx = 0, my = 0;
    for (const p of v) { const q = p.clone().applyMatrix4(this.cam.matrixWorldInverse); mx = Math.max(mx, Math.abs(q.x)); my = Math.max(my, Math.abs(q.y)); }
    const ancho = Math.max(mx * 2, my * 2 / (this.alto / this.ancho)) * margen;
    this.camara({ az, el, zoom: 1, mira: [c.x, c.y, c.z], ancho });
  }

  // Lo que la guardia mira: cada pieza con su caja en pantalla y si está encendida
  registro() {
    const lista = [];
    this.grupo.traverse(o => {
      if (!o.isMesh) return;
      const caja = new THREE.Box3().setFromObject(o);
      const pts = [];
      for (const x of [caja.min.x, caja.max.x]) for (const y of [caja.min.y, caja.max.y]) for (const z of [caja.min.z, caja.max.z]) pts.push(this.aPantalla([x, y, z]));
      lista.push({ nombre: o.parent.name || String(o.parent.id), acento: !!o.parent.userData.acento, visible: o.visible && o.parent.visible,
                   x0: Math.min(...pts.map(p => p[0])), x1: Math.max(...pts.map(p => p[0])), y0: Math.min(...pts.map(p => p[1])), y1: Math.max(...pts.map(p => p[1])) });
    });
    return lista;
  }
}

// ───────────── lector de .glb (propio: el three.js local no trae GLTFLoader) ─────────────
const TIPOS = { 5120: [Int8Array, 1], 5121: [Uint8Array, 1], 5122: [Int16Array, 2], 5123: [Uint16Array, 2], 5125: [Uint32Array, 4], 5126: [Float32Array, 4] };
const COMPONENTES = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT2: 4, MAT3: 9, MAT4: 16 };

export const GLB = {
  // ArrayBuffer de un .glb → { mallas: [{ nombre, geometria (en coordenadas del mundo, con índice) }], texturas, materiales }
  leer(buf) {
    const dv = new DataView(buf);
    if (dv.getUint32(0, true) !== 0x46546C67) throw new Error('no es un .glb (falta «glTF» al inicio)');
    if (dv.getUint32(4, true) !== 2) throw new Error('sólo glTF 2');
    let json = null, bin = null, pos = 12;
    while (pos < dv.byteLength) {
      const largo = dv.getUint32(pos, true), tipo = dv.getUint32(pos + 4, true);
      const datos = buf.slice(pos + 8, pos + 8 + largo);
      if (tipo === 0x4E4F534A) json = JSON.parse(new TextDecoder().decode(datos)); else if (tipo === 0x004E4942 && !bin) bin = datos;
      pos += 8 + largo;                                        // los trozos ya vienen alineados a 4
    }
    if (!json || !bin) throw new Error('el .glb no trae JSON o datos binarios (¿viene con archivos externos?)');
    const usadas = [...(json.extensionsRequired || [])];
    if (usadas.some(x => /draco|meshopt/i.test(x))) throw new Error('el .glb está comprimido (' + usadas.join(', ') + '): descomprimirlo antes (Blender: importar y exportar sin compresión)');
    const leerAccesor = i => {
      const a = json.accessors[i], vista = json.bufferViews[a.bufferView];
      if (a.sparse) throw new Error('accesor disperso (sparse): no soportado');
      const [Tipo, bytes] = TIPOS[a.componentType], n = COMPONENTES[a.type], paso = vista.byteStride || bytes * n;
      const base = (vista.byteOffset || 0) + (a.byteOffset || 0), out = new Float64Array(a.count * n), d = new DataView(bin);
      const lector = { 5120: 'getInt8', 5121: 'getUint8', 5122: 'getInt16', 5123: 'getUint16', 5125: 'getUint32', 5126: 'getFloat32' }[a.componentType];
      for (let k = 0; k < a.count; k++) for (let c = 0; c < n; c++) out[k * n + c] = d[lector](base + k * paso + c * bytes, true);
      return { datos: out, n, count: a.count };
    };
    const mallas = [], m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), t = new THREE.Vector3();
    const visitar = (i, padre) => {
      const nodo = json.nodes[i], local = new THREE.Matrix4();
      if (nodo.matrix) local.fromArray(nodo.matrix);
      else local.compose(t.set(...(nodo.translation || [0, 0, 0])), q.set(...(nodo.rotation || [0, 0, 0, 1])), s.set(...(nodo.scale || [1, 1, 1])));
      const mundo = padre.clone().multiply(local);
      if (nodo.mesh !== undefined) {
        const malla = json.meshes[nodo.mesh];
        malla.primitives.forEach((p, k) => {
          if ((p.mode ?? 4) !== 4) return;                          // sólo triángulos
          const pos = leerAccesor(p.attributes.POSITION), ind = p.indices !== undefined ? leerAccesor(p.indices).datos : Uint32Array.from({ length: pos.count }, (_, j) => j);
          const v = new Float32Array(pos.count * 3), w = new THREE.Vector3();
          for (let j = 0; j < pos.count; j++) { w.set(pos.datos[j * 3], pos.datos[j * 3 + 1], pos.datos[j * 3 + 2]).applyMatrix4(mundo); v.set([w.x, w.y, w.z], j * 3); }
          const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(v, 3)); g.setIndex(Array.from(ind));
          mallas.push({ nombre: [nodo.name, malla.name].filter(Boolean).join('/') + (malla.primitives.length > 1 ? '#' + k : ''), geometria: g, material: p.material });
        });
      }
      (nodo.children || []).forEach(h => visitar(h, mundo));
    };
    const escena = json.scenes?.[json.scene ?? 0];
    (escena ? escena.nodes : json.nodes.map((_, i) => i).filter(i => !json.nodes.some(n => (n.children || []).includes(i)))).forEach(i => visitar(i, m4.clone().identity()));
    return { mallas, texturas: (json.images || []).length, materiales: (json.materials || []).length, nodos: json.nodes.length };
  },
};

// Limpieza y restilizado de lo que salió de GLB.leer: suelda vértices, quita triángulos degenerados, centra, apoya en y = 0,
// escala a `objetivo` unidades de lado mayor, tira materiales y texturas y pone el cuerpo oscuro con su contorno.
// `acentos`: expresión regular sobre el nombre de cada malla; las que coinciden quedan encendidas.
export function restilizar(mundo, leido, { objetivo = 4, acentos = null, suave = true, tolerancia = 1e-4 } = {}) {
  const antes = { vertices: 0, triangulos: 0 }, despues = { vertices: 0, triangulos: 0 }, caja = new THREE.Box3();
  leido.mallas.forEach(m => { antes.vertices += m.geometria.attributes.position.count; antes.triangulos += m.geometria.index.count / 3; caja.expandByObject(new THREE.Mesh(m.geometria)); });
  const c = caja.getCenter(new THREE.Vector3()), tam = caja.getSize(new THREE.Vector3()), k = objetivo / Math.max(tam.x, tam.y, tam.z, 1e-9);
  const raiz = new THREE.Group(); raiz.name = 'glb';
  const re = acentos ? new RegExp(acentos, 'i') : null, nombres = [];
  leido.mallas.forEach((m, i) => {
    const p = m.geometria.attributes.position, idx = m.geometria.index.array, mapa = new Map(), v = [], ind = [];
    const paso = tolerancia * Math.max(tam.x, tam.y, tam.z, 1);
    const unico = j => {
      const llave = [0, 1, 2].map(e => Math.round(p.getComponent(j, e) / paso)).join(',');
      let r = mapa.get(llave);
      if (r === undefined) { r = v.length / 3; mapa.set(llave, r); v.push((p.getX(j) - c.x) * k, (p.getY(j) - caja.min.y) * k, (p.getZ(j) - c.z) * k); }
      return r;
    };
    for (let j = 0; j < idx.length; j += 3) {
      const a = unico(idx[j]), b = unico(idx[j + 1]), d = unico(idx[j + 2]);
      if (a !== b && b !== d && a !== d) ind.push(a, b, d);        // un triángulo con dos vértices soldados juntos no se ve
    }
    if (!ind.length) return;
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(ind);
    g.computeVertexNormals();
    despues.vertices += v.length / 3; despues.triangulos += ind.length / 3;
    const acento = !!(re && re.test(m.nombre));
    if (acento) { g.userData.acento = true; nombres.push(m.nombre); }
    const geo = suave ? g : g.toNonIndexed();            // toNonIndexed no copia userData
    geo.userData.acento = acento;
    const pieza = mundo.agregar(geo, m.nombre || 'malla' + i, { padre: raiz });
    pieza.userData.original = m.nombre;
  });
  mundo.grupo.add(raiz);
  return { raiz, antes, despues, texturasTiradas: leido.texturas, materialesTirados: leido.materiales, acentos: nombres, escala: k, tam: [tam.x * k, tam.y * k, tam.z * k] };
}
