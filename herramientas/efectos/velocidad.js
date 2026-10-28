/* Velocidad: desenfoque por velocidad analítico. El objeto tiene su posición como función de t; la estela se
 * calcula entre t − obturador/fps y t, sin subcuadros de toda la escena (sólo se redibuja el objeto).
 *
 * Canvas 2D:
 *   Velocidad.copias(ctx, t, { estado: t => ({ x, y, ang }), dibujar: (g, est, t) => {...},
 *                              fps: 30, obturador: 1, n: 12, peso: 'caja' | 'cola', caja: { x, y, w, h } })
 *     N copias del objeto repartidas en el obturador, sumadas con 'lighter' a peso w_k (Σ w = 1). Con 'caja' es la
 *     integral del obturador de una cámara (el objeto queda translúcido donde pasó una parte del tiempo);
 *     con 'cola' pesa más la posición actual (cometa). `caja` (opcional) limita el trabajo a esa región; con
 *     `margen` (px) y un estado con x, y se calcula sola (lo que recorre el objeto en el obturador ± margen; ojo:
 *     las cinco muestras de la caja no ven una curva cerrada dentro del obturador). Sin caja ni margen se trabaja el
 *     cuadro entero. Medido (n = 14, lienzos de CPU): una franja de 1920×240 tarda ~150 ms por cuadro.
 *     Ojo: 8 bits por canal, con n = 12 la suma pierde ~1 % de brillo.
 *   Velocidad.barrido(ctx, t, { posicion: t => [x, y], radio, color, fps: 30, obturador: 1, muestras: 8 })
 *     Para un disco: una cápsula a lo largo del camino con degradado de cola (transparente) a cabeza (lleno).
 *
 * three.js («object smearing» de Maxime Heckel, «Shading Motion»: la velocidad sale de la posición en t y en
 * t − 1/fps, analítica; escrito desde cero):
 *   const mancha = Velocidad.manchaThree(THREE, material, { fuerza: 1, ruido: .35 });
 *   cada cuadro: mancha.actualizar(mesh, posicion(t).sub(posicion(t - 1 / fps)));   // desplazamiento en el mundo
 *   El vértice cuya normal mira hacia atrás (de donde viene el objeto) se corre hacia la posición anterior, con un
 *   poco de ruido por vértice: el objeto se estira en su estela. Sirve con materiales que tienen normales
 *   (Standard, Physical, Lambert, Phong; no Basic). Sólo traslación: el giro no se mancha. Con esto no hacen falta
 *   los subcuadros de Reproductor (sub=1).
 */
window.Velocidad = (() => {
  let acc = null, capa = null;
  function lienzos(w, h) {
    if (!acc || acc.width !== w || acc.height !== h) {
      acc = document.createElement('canvas'); acc.width = w; acc.height = h;
      capa = document.createElement('canvas'); capa.width = w; capa.height = h;
    }
    // de CPU: pegarlos no cambia el modo del lienzo del video (ver la nota de demo.html sobre cuadros idénticos)
    return [acc.getContext('2d', { willReadFrequently: true }), capa.getContext('2d', { willReadFrequently: true })];
  }

  function copias(ctx, t, op) {
    const o = Object.assign({ fps: 30, obturador: 1, n: 12, peso: 'caja', caja: null, margen: null }, op);
    const W = ctx.canvas.width, H = ctx.canvas.height;
    const [a, c] = lienzos(W, H);
    if (!o.caja && o.margen != null) {          // caja automática: lo que recorre (x, y) en el obturador ± margen
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (let k = 0; k <= 4; k++) {
        const e = o.estado(t - o.obturador / o.fps * k / 4);
        x0 = Math.min(x0, e.x); y0 = Math.min(y0, e.y); x1 = Math.max(x1, e.x); y1 = Math.max(y1, e.y);
      }
      o.caja = { x: x0 - o.margen, y: y0 - o.margen, w: x1 - x0 + 2 * o.margen, h: y1 - y0 + 2 * o.margen };
    }
    const r = o.caja ? {
      x: Math.max(0, Math.floor(o.caja.x)), y: Math.max(0, Math.floor(o.caja.y)),
      w: Math.min(W, Math.ceil(o.caja.x + o.caja.w)) - Math.max(0, Math.floor(o.caja.x)),
      h: Math.min(H, Math.ceil(o.caja.y + o.caja.h)) - Math.max(0, Math.floor(o.caja.y)),
    } : { x: 0, y: 0, w: W, h: H };
    if (r.w <= 0 || r.h <= 0) return;
    const T = o.obturador / o.fps, n = Math.max(1, o.n | 0);
    const pesos = Array.from({ length: n }, (_, k) => o.peso === 'cola' ? k + 1 : 1);
    const suma = pesos.reduce((x, y) => x + y, 0);
    a.save(); a.setTransform(1, 0, 0, 1, 0, 0); a.clearRect(r.x, r.y, r.w, r.h); a.restore();
    for (let k = 0; k < n; k++) {
      const tk = n === 1 ? t : t - T * (1 - k / (n - 1));
      c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(r.x, r.y, r.w, r.h); c.restore();
      c.save(); o.dibujar(c, o.estado(tk), tk); c.restore();
      a.save(); a.setTransform(1, 0, 0, 1, 0, 0);
      a.globalCompositeOperation = 'lighter'; a.globalAlpha = pesos[k] / suma;
      a.drawImage(capa, r.x, r.y, r.w, r.h, r.x, r.y, r.w, r.h);
      a.restore();
    }
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    ctx.drawImage(acc, r.x, r.y, r.w, r.h, r.x, r.y, r.w, r.h);
    ctx.restore();
  }

  function barrido(ctx, t, op) {
    const o = Object.assign({ radio: 30, color: '#fff', fps: 30, obturador: 1, muestras: 8 }, op);
    const T = o.obturador / o.fps, pts = [];
    for (let k = 0; k <= o.muestras; k++) pts.push(o.posicion(t - T * (1 - k / o.muestras)));
    const [cx, cy] = pts[pts.length - 1], [tx, ty] = pts[0];
    ctx.save();
    ctx.fillStyle = o.color;
    if (Math.hypot(cx - tx, cy - ty) > .5) {
      // la cola: el mismo color con alfa que crece hacia la cabeza (un solo trazo: los alfas no se suman)
      ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = o.radio * 2;
      ctx.strokeStyle = gradienteColor(ctx, tx, ty, cx, cy, o.color);
      ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(cx, cy, o.radio, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  // degradado de transparente al color (mismo tono: evita que la cola se oscurezca)
  function gradienteColor(ctx, x0, y0, x1, y1, color) {
    const g0 = document.createElement('canvas').getContext('2d'); g0.fillStyle = color;
    const h = g0.fillStyle, r = parseInt(h.slice(1, 3), 16), g = parseInt(h.slice(3, 5), 16), b = parseInt(h.slice(5, 7), 16);
    const gr = ctx.createLinearGradient(x0, y0, x1, y1);
    gr.addColorStop(0, `rgba(${r},${g},${b},0)`); gr.addColorStop(.6, `rgba(${r},${g},${b},.45)`); gr.addColorStop(1, `rgba(${r},${g},${b},1)`);
    return gr;
  }

  function manchaThree(THREE, material, { fuerza = 1, ruido = .35 } = {}) {
    const uniforms = { uDesp: { value: new THREE.Vector3() }, uFuerza: { value: fuerza }, uRuido: { value: ruido } };
    material.onBeforeCompile = sh => {
      Object.assign(sh.uniforms, uniforms);
      sh.vertexShader = 'uniform vec3 uDesp;\nuniform float uFuerza;\nuniform float uRuido;\n' +
        sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
        {
          float largo = length(uDesp);
          if (largo > 1e-6) {
            vec3 dir = uDesp / largo;
            float atras = max(0.0, -dot(normalize(objectNormal), dir));      // cara que mira hacia de donde viene
            float h = fract(sin(dot(position, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
            transformed -= uDesp * uFuerza * atras * (1.0 - uRuido + uRuido * h);
          }
        }`);
    };
    material.customProgramCacheKey = () => 'mancha-velocidad';
    const m3 = new THREE.Matrix3();
    return {
      uniforms,
      // desplazamiento en el mundo de un cuadro (pos(t) − pos(t − 1/fps)) → espacio del objeto
      actualizar(mesh, despMundo) {
        mesh.updateMatrixWorld();
        m3.setFromMatrix4(mesh.matrixWorld).invert();
        uniforms.uDesp.value.copy(despMundo).applyMatrix3(m3);
      },
    };
  }

  return { copias, barrido, manchaThree };
})();
