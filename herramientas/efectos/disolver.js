/* Disolver: texto (o cualquier imagen) que se deshace en polvo, o que se arma desde el polvo. Canvas 2D.
 * Reemplaza los fundidos de opacidad. Todo es función pura de (t, semilla): el mismo t da el mismo cuadro.
 *
 *   Disolver.texto(ctx, t, { texto: 'Hola', fuente: '800 160px system-ui', x: 960, y: 540, color: '#fff',
 *                            desde: 1, hasta: 3, semilla: 7, modo: 'deshacer' | 'armar' })
 *   Disolver.imagen(ctx, t, { fuente: <canvas|img>, x, y, desde, hasta, semilla, modo })   (x, y = centro)
 *
 * Cómo funciona (idea del «Gommage» de Codrops, escrita desde cero):
 *   - máscara m(x, y) en [0, 1]: ruido fbm con semilla mezclado con un barrido en la dirección `direccion`;
 *   - umbral q = progreso · (1 + borde): el píxel con m < q − borde ya se fue, el que está entre q − borde y q
 *     brilla (brasa, color `brasa`), el resto queda igual;
 *   - partículas: cada una nace en un píxel de la imagen y se suelta cuando el umbral pasa por su m; su
 *     posición es una fórmula cerrada de su edad (viento, empuje hacia arriba y un vaivén con semilla).
 *   - `armar` es `deshacer` con el tiempo espejado (t' = desde + hasta − t): el polvo llega y la imagen se completa.
 * Opciones: borde (.08), escala del ruido en px (90), direccion ([1, -.3]) y peso del barrido (.55), particulas
 *   (5000), viento ([-220, -140] px/s: el polvo se va hacia donde ya no hay letras), vida (1.4 s), tam (2.6 px), brasa ('#ffb35c'), polvo (color de la imagen),
 *   curva (k → k', por omisión suave).
 * Los lienzos internos son de CPU (willReadFrequently): pegarlos no cambia el modo del lienzo del video (ver
 * la nota de demo.html sobre cuadros idénticos).
 */
window.Disolver = (() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const suave = k => k * k * (3 - 2 * k);

  function mulberry32(a) {
    return () => {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  // hash entero de una celda → [0, 1)
  function hash(x, y, s) {
    let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 1274126177) | 0;
    h = Math.imul(h ^ h >>> 13, 1103515245); h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  }
  function ruido(x, y, s) {
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
    const a = hash(xi, yi, s), b = hash(xi + 1, yi, s), c = hash(xi, yi + 1, s), d = hash(xi + 1, yi + 1, s);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  function fbm(x, y, s) {
    let v = 0, amp = .5, f = 1;
    for (let o = 0; o < 4; o++) { v += amp * ruido(x * f, y * f, s + o * 101); f *= 2.03; amp *= .5; }
    return v / .9375;
  }
  const colores = new Map();
  function rgb(col) {
    if (colores.has(col)) return colores.get(col);
    const g = document.createElement('canvas').getContext('2d');
    g.fillStyle = col; const h = g.fillStyle;   // normaliza a #rrggbb
    const c = [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
    colores.set(col, c);
    return c;
  }

  // Prepara (una vez por fuente y opciones) la máscara y las partículas.
  const cache = new WeakMap();
  function preparar(fuente, o) {
    const clave = [o.semilla, o.escala, o.direccion, o.peso, o.particulas, o.vida, o.tam].join('|');
    let porFuente = cache.get(fuente);
    if (!porFuente) { porFuente = new Map(); cache.set(fuente, porFuente); }
    if (porFuente.has(clave)) return porFuente.get(clave);
    const w = fuente.width, h = fuente.height;
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(fuente, 0, 0);
    const img = g.getImageData(0, 0, w, h), px = img.data;
    const m = new Float32Array(w * h), llenos = [];
    const [dx, dy] = o.direccion, dl = Math.hypot(dx, dy) || 1, ux = dx / dl, uy = dy / dl;
    const proy = (x, y) => (x - w / 2) * ux + (y - h / 2) * uy;
    const pmax = Math.abs(w / 2 * ux) + Math.abs(h / 2 * uy) || 1;
    let mn = Infinity, mx = -Infinity;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x;
      if (px[i * 4 + 3] < 8) continue;
      const v = (1 - o.peso) * fbm(x / o.escala, y / o.escala, o.semilla) + o.peso * (proy(x, y) / pmax * .5 + .5);
      m[i] = v; llenos.push(i);
      if (v < mn) mn = v; if (v > mx) mx = v;
    }
    const rango = mx - mn || 1;
    for (const i of llenos) m[i] = (m[i] - mn) / rango;
    // partículas: nacen en píxeles llenos elegidos con la semilla
    const az = mulberry32(o.semilla * 7919 + 13), n = llenos.length ? o.particulas : 0;
    const P = {
      n, x: new Float32Array(n), y: new Float32Array(n), m: new Float32Array(n), vida: new Float32Array(n),
      vx: new Float32Array(n), vy: new Float32Array(n), f: new Float32Array(n), fase: new Float32Array(n),
      amp: new Float32Array(n), tam: new Float32Array(n), col: new Array(n),
    };
    for (let k = 0; k < n; k++) {
      const i = llenos[Math.floor(az() * llenos.length)];
      P.x[k] = i % w; P.y[k] = Math.floor(i / w); P.m[k] = m[i];
      P.vida[k] = o.vida * (.55 + az() * .9);
      P.vx[k] = (az() - .5) * 80; P.vy[k] = (az() - .5) * 80;
      P.f[k] = 2 + az() * 5; P.fase[k] = az() * Math.PI * 2; P.amp[k] = 10 + az() * 40;
      P.tam[k] = o.tam * (.5 + az());
      P.col[k] = [px[i * 4], px[i * 4 + 1], px[i * 4 + 2]];
    }
    const salida = document.createElement('canvas'); salida.width = w; salida.height = h;
    const prep = { w, h, img, m, P, copia: c, salida, sg: salida.getContext('2d', { willReadFrequently: true }), out: new ImageData(w, h) };
    porFuente.set(clave, prep);
    return prep;
  }

  function imagen(ctx, t, op) {
    const o = Object.assign({
      x: 0, y: 0, desde: 0, hasta: 2, semilla: 1, modo: 'deshacer', borde: .08, escala: 90,
      direccion: [1, -.3], peso: .55, particulas: 5000, viento: [-220, -140], vida: 1.4, tam: 2.6,
      brasa: '#ffb35c', polvo: null, curva: suave,
    }, op);
    const p = preparar(o.fuente, o);
    const dur = Math.max(1e-6, o.hasta - o.desde);
    const te = o.modo === 'armar' ? o.desde + o.hasta - t : t;      // tiempo espejado para armar
    const prog = o.curva(clamp((te - o.desde) / dur));
    const b = o.borde, q = prog * (1 + b);
    const x0 = Math.round(o.x - p.w / 2), y0 = Math.round(o.y - p.h / 2);
    const brasa = rgb(o.brasa), polvo = o.polvo ? rgb(o.polvo) : null;

    // 1) la imagen con la máscara
    if (prog <= 0) ctx.drawImage(p.copia, x0, y0);
    else if (q - b < 1) {
      const src = p.img.data, dst = p.out.data, m = p.m;
      dst.fill(0);
      for (let i = 0, n = p.w * p.h; i < n; i++) {
        const a = src[i * 4 + 3];
        if (a < 8) continue;
        const v = m[i];
        if (v <= q - b) continue;
        const j = i * 4;
        if (v < q) {                                     // brasa: el borde que se está yendo
          const s = 1 - (v - (q - b)) / b, s2 = s * s;
          dst[j] = src[j] + (brasa[0] - src[j]) * s; dst[j + 1] = src[j + 1] + (brasa[1] - src[j + 1]) * s;
          dst[j + 2] = src[j + 2] + (brasa[2] - src[j + 2]) * s; dst[j + 3] = a * (1 - s2 * .35);
        } else { dst[j] = src[j]; dst[j + 1] = src[j + 1]; dst[j + 2] = src[j + 2]; dst[j + 3] = a; }
      }
      p.sg.putImageData(p.out, 0, 0);
      ctx.drawImage(p.salida, x0, y0);
    }

    // 2) el polvo: edad de cada partícula desde que el umbral pasó por ella
    const P = p.P, extra = Math.max(0, te - o.hasta), [wx, wy] = o.viento;
    if (prog <= 0) return;
    ctx.save();
    for (let k = 0; k < P.n; k++) {
      const suelta = Math.min(1, (P.m[k] + b) / (1 + b));        // progreso en que se suelta
      if (prog < suelta) continue;
      const e = (prog - suelta) * dur + extra;                     // edad en segundos
      const vida = P.vida[k];
      if (e >= vida) continue;
      const k01 = e / vida;
      const px = x0 + P.x[k] + (wx + P.vx[k]) * e + 30 * e * e * Math.sign(wx) + P.amp[k] * Math.sin(P.f[k] * e + P.fase[k]) * k01;
      const py = y0 + P.y[k] + (wy + P.vy[k]) * e - 60 * e * e + P.amp[k] * .6 * Math.cos(P.f[k] * .8 * e + P.fase[k]) * k01;
      const tam = P.tam[k] * (1 - k01 * .7);
      const brillo = Math.max(0, 1 - k01 * 3);                    // al soltarse brilla y después es polvo
      const c = polvo || P.col[k];
      const r = c[0] + (brasa[0] - c[0]) * brillo, g = c[1] + (brasa[1] - c[1]) * brillo, bl = c[2] + (brasa[2] - c[2]) * brillo;
      ctx.globalAlpha = (1 - k01) * (1 - k01) * .95;
      ctx.fillStyle = `rgb(${r | 0},${g | 0},${bl | 0})`;
      ctx.fillRect(px - tam / 2, py - tam / 2, tam, tam);
    }
    ctx.restore();
  }

  // El texto se dibuja una vez en un lienzo propio (con margen) y se disuelve como imagen.
  const textos = new Map();
  function lienzoTexto(texto, fuente, color) {
    const clave = texto + '|' + fuente + '|' + color;
    if (textos.has(clave)) return textos.get(clave);
    const g0 = document.createElement('canvas').getContext('2d'); g0.font = fuente;
    const mt = g0.measureText(texto);
    const alto = Math.ceil((mt.actualBoundingBoxAscent || 100) + (mt.actualBoundingBoxDescent || 30));
    const c = document.createElement('canvas');
    c.width = Math.ceil(mt.width) + 40; c.height = alto + 40;
    const g = c.getContext('2d', { willReadFrequently: true }); g.font = fuente; g.fillStyle = color; g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    g.fillText(texto, 20, 20 + (mt.actualBoundingBoxAscent || 100));
    textos.set(clave, c);
    return c;
  }
  function texto(ctx, t, op) {
    const o = Object.assign({ fuente: '800 160px system-ui, "Segoe UI", sans-serif', color: '#f2f5fa' }, op);
    const lienzo = lienzoTexto(o.texto, o.fuente, o.color);
    return imagen(ctx, t, Object.assign({}, o, { fuente: lienzo }));
  }

  return { imagen, texto, fbm, mulberry32 };
})();
