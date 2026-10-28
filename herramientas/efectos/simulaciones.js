/* Simulaciones con semilla y paso fijo: el mismo t da el mismo cuadro, se llegue como se llegue.
 *
 *   const moho = Simulaciones.physarum({ semilla, puntos: [[x, y], ...] })      moho.dibujar(ctx, t)
 *   const coral = Simulaciones.grayScott({ semilla, f: .0545, k: .062 })       coral.dibujar(ctx, t)
 *   const marmol = Simulaciones.marmoleado({ semilla })                        marmol.dibujar(ctx, t)
 *   const agua = Simulaciones.causticas({ semilla })                           agua.dibujar(ctx, t)
 *
 * Las que tienen memoria (physarum, grayScott, marmoleado) no se pueden calcular en t sin pasar por los pasos
 * de antes. Por eso:
 *   - el tiempo se vuelve un número entero de pasos: n = floor(t · pasosPorSegundo) (con Reproductor.cuadro(t)
 *     si está cargado: los subcuadros de un mismo cuadro usan el mismo estado y no obligan a volver atrás);
 *   - cada paso depende sólo del estado y del número de paso (el azar de cada paso es un hash de (agente,
 *     paso, semilla), no una secuencia que haya que guardar);
 *   - se guarda una copia del estado cada `cadaClave` pasos (cuadros clave en memoria). Para ir a cualquier t se
 *     parte del estado actual si está antes, o de la última clave ≤ n, y se avanza desde ahí. Saltar hacia atrás
 *     cuesta como mucho `cadaClave` pasos; la primera vez que se va lejos hacia adelante hay que calcular todo.
 * Las cáusticas no tienen memoria: son una fórmula cerrada de t (superficie = suma de ondas con semilla).
 * Todo se dibuja escalado al tamaño de ctx.canvas (la grilla de las simulaciones es más chica que 1920×1080).
 */
window.Simulaciones = (() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  function mulberry32(a) {
    return () => {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  // hash de tres enteros → [0, 1) (lowbias32)
  function hash3(a, b, c) {
    let h = (a | 0) ^ Math.imul(b | 0, 0x9E3779B1) ^ Math.imul(c | 0, 0x85EBCA77);
    h ^= h >>> 16; h = Math.imul(h, 0x7feb352d); h ^= h >>> 15; h = Math.imul(h, 0x846ca68b); h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  }
  const pasoDe = (t, pps) => Math.max(0, Math.floor((window.Reproductor ? Reproductor.cuadro(t) : t) * pps + 1e-6));

  // Memoria por cuadros clave: estado(n) da el estado después de n pasos, siempre el mismo.
  function conMemoria({ inicial, paso, copiar, cadaClave }) {
    const claves = new Map();
    let actual = null, nActual = -1;
    return n => {
      if (!actual || nActual > n) {
        let mejor = -1;
        for (const k of claves.keys()) if (k <= n && k > mejor) mejor = k;
        if (mejor >= 0) { actual = copiar(claves.get(mejor)); nActual = mejor; }
        else { actual = inicial(); nActual = 0; claves.set(0, copiar(actual)); }
      } else {
        // una clave más adelante que el estado actual ahorra pasos
        let mejor = nActual;
        for (const k of claves.keys()) if (k <= n && k > mejor) mejor = k;
        if (mejor > nActual) { actual = copiar(claves.get(mejor)); nActual = mejor; }
      }
      while (nActual < n) {
        paso(actual, nActual); nActual++;
        if (nActual % cadaClave === 0 && !claves.has(nActual)) claves.set(nActual, copiar(actual));
      }
      return actual;
    };
  }

  // lienzo chico donde se pinta la grilla antes de escalarla
  function lienzoGrilla(w, h) {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d', { willReadFrequently: true }); return { c, g, img: g.createImageData(w, h) };
  }
  function paleta(stops) {         // [[pos, [r,g,b]], ...] → 256 colores
    const p = new Uint8ClampedArray(256 * 3);
    for (let i = 0; i < 256; i++) {
      const x = i / 255; let j = 0;
      while (j < stops.length - 2 && x > stops[j + 1][0]) j++;
      const [a, ca] = stops[j], [b, cb] = stops[j + 1], k = clamp((x - a) / (b - a || 1));
      for (let c = 0; c < 3; c++) p[i * 3 + c] = ca[c] + (cb[c] - ca[c]) * k;
    }
    return p;
  }

  // ───────────────────────── Physarum: moho que une puntos ─────────────────────────
  // Agentes que huelen el rastro con tres sensores, giran hacia el más fuerte, avanzan y dejan rastro; el rastro
  // se difunde y se evapora. Los `puntos` (comida) emiten rastro en cada paso: la red los termina uniendo.
  function physarum(op = {}) {
    const o = Object.assign({
      semilla: 1, ancho: 640, alto: 360, agentes: 70000, pasosPorSegundo: 45, cadaClave: 90,
      angSensor: .45, distSensor: 9, giro: .35, velocidad: 1.1, deposito: 1.2, evaporacion: .06,
      comida: 60, radioComida: 3, puntos: null, numPuntos: 9, fondo: [6, 8, 14],
      colores: [[0, [6, 8, 14]], [.25, [40, 30, 90]], [.55, [230, 120, 60]], [.85, [255, 220, 150]], [1, [255, 255, 240]]],
    }, op);
    const W = o.ancho, H = o.alto, N = o.agentes;
    const az0 = mulberry32(o.semilla);
    // puntos en coordenadas 0..1 (si no vienen, con la semilla, separados del borde)
    const puntos = o.puntos || Array.from({ length: o.numPuntos }, () => [.1 + az0() * .8, .14 + az0() * .72]);
    const celdasComida = [];
    for (const [px, py] of puntos) {
      const cx = Math.round(px * (W - 1)), cy = Math.round(py * (H - 1)), r = o.radioComida;
      for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++)
        if (x * x + y * y <= r * r && cx + x >= 0 && cx + x < W && cy + y >= 0 && cy + y < H) celdasComida.push((cy + y) * W + cx + x);
    }
    const tmp = new Float32Array(W * H);
    // cada agente guarda su dirección como vector unitario (dx, dy): girar es multiplicar por una rotación fija,
    // sin senos ni cosenos en el bucle (con ángulos, el paso tardaba ~45 ms con 70 000 agentes)
    const inicial = () => {
      const az = mulberry32(o.semilla * 31 + 7);
      const s = { x: new Float32Array(N), y: new Float32Array(N), dx: new Float32Array(N), dy: new Float32Array(N), rastro: new Float32Array(W * H) };
      // la mitad nace repartida y la otra mitad junto a las ciudades: la red crece desde ellas y las une
      for (let i = 0; i < N; i++) {
        const a = az() * Math.PI * 2;
        if (i % 2 && puntos.length) {
          const [px, py] = puntos[Math.floor(az() * puntos.length)], r = az() * 14;
          s.x[i] = clamp(px * (W - 1) + Math.cos(a) * r, 0, W - 1.001); s.y[i] = clamp(py * (H - 1) + Math.sin(a) * r, 0, H - 1.001);
        } else { s.x[i] = az() * W; s.y[i] = az() * H; }
        s.dx[i] = Math.cos(a); s.dy[i] = Math.sin(a);
      }
      return s;
    };
    const copiar = s => ({ x: s.x.slice(), y: s.y.slice(), dx: s.dx.slice(), dy: s.dy.slice(), rastro: s.rastro.slice() });
    const cs = Math.cos(o.angSensor), ss = Math.sin(o.angSensor), cg = Math.cos(o.giro), sg = Math.sin(o.giro);
    const paso = (s, n) => {
      const { x: X, y: Y, dx: DX, dy: DY, rastro: R } = s, sd = o.distSensor, v = o.velocidad, dep = o.deposito;
      const leer = (x, y) => {
        const xi = x | 0, yi = y | 0;
        return (x < 0 || y < 0 || xi >= W || yi >= H) ? 0 : R[yi * W + xi];
      };
      for (let i = 0; i < N; i++) {
        const x = X[i], y = Y[i], dx = DX[i], dy = DY[i];
        const f = leer(x + dx * sd, y + dy * sd);
        const l = leer(x + (dx * cs + dy * ss) * sd, y + (dy * cs - dx * ss) * sd);    // ángulo − sensor
        const r = leer(x + (dx * cs - dy * ss) * sd, y + (dy * cs + dx * ss) * sd);    // ángulo + sensor
        let giro = 0;                                   // −1 izquierda, +1 derecha
        if (f > l && f > r) giro = 0;
        else if (f < l && f < r) giro = hash3(i, n, o.semilla) < .5 ? -1 : 1;
        else if (l > r) giro = -1;
        else if (r > l) giro = 1;
        let ndx = dx, ndy = dy;
        if (giro) { ndx = dx * cg - giro * dy * sg; ndy = dy * cg + giro * dx * sg; }
        const largo = Math.sqrt(ndx * ndx + ndy * ndy); ndx /= largo; ndy /= largo;
        let nx = x + ndx * v, ny = y + ndy * v;
        if (nx < 0 || nx >= W || ny < 0 || ny >= H) {            // en el borde: rebota con una dirección nueva
          nx = clamp(nx, 0, W - 1.001); ny = clamp(ny, 0, H - 1.001);
          const a = hash3(i, n, o.semilla + 1) * Math.PI * 2; ndx = Math.cos(a); ndy = Math.sin(a);
        }
        X[i] = nx; Y[i] = ny; DX[i] = ndx; DY[i] = ndy;
        R[(ny | 0) * W + (nx | 0)] += dep;
      }
      for (const c of celdasComida) R[c] += o.comida;
      // difusión 3×3 (en dos pasadas: horizontal y vertical) y evaporación
      for (let y = 0; y < H; y++) {
        const b = y * W;
        for (let x = 0; x < W; x++) tmp[b + x] = R[b + (x > 0 ? x - 1 : 0)] + R[b + x] + R[b + (x < W - 1 ? x + 1 : W - 1)];
      }
      const k = (1 - o.evaporacion) / 9;
      for (let y = 0; y < H; y++) {
        const a = (y > 0 ? y - 1 : 0) * W, b = y * W, c = (y < H - 1 ? y + 1 : H - 1) * W;
        for (let x = 0; x < W; x++) {
          const v = (tmp[a + x] + tmp[b + x] + tmp[c + x]) * k;
          R[b + x] = v > 1e-4 ? v : 0;           // corta los valores muy chicos (los subnormales son lentos en la CPU)
        }
      }
    };
    const estado = conMemoria({ inicial, paso, copiar, cadaClave: o.cadaClave });
    const pal = paleta(o.colores), G = lienzoGrilla(W, H);
    function dibujar(ctx, t) {
      const s = estado(pasoDe(t, o.pasosPorSegundo)), R = s.rastro, d = G.img.data;
      for (let i = 0; i < W * H; i++) {
        const v = 1 - Math.exp(-R[i] * .045), j = Math.min(255, v * 255 | 0) * 3;
        d[i * 4] = pal[j]; d[i * 4 + 1] = pal[j + 1]; d[i * 4 + 2] = pal[j + 2]; d[i * 4 + 3] = 255;
      }
      G.g.putImageData(G.img, 0, 0);
      const CW = ctx.canvas.width, CH = ctx.canvas.height;
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(G.c, 0, 0, CW, CH);
      for (const [px, py] of puntos) {                            // las «ciudades»
        const x = px * CW, y = py * CH, gr = ctx.createRadialGradient(x, y, 0, x, y, 26);
        gr.addColorStop(0, 'rgba(255,255,240,1)'); gr.addColorStop(.35, 'rgba(255,200,120,.6)'); gr.addColorStop(1, 'rgba(255,160,80,0)');
        ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(x, y, 26, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }
    return { dibujar, puntos, estado: t => estado(pasoDe(t, o.pasosPorSegundo)) };
  }

  // ───────────────────────── Gray–Scott: reacción-difusión ─────────────────────────
  // u y v con laplaciano de 9 puntos (bordes que se tocan, como un toro). Paso dt = 1.
  // f = .0545, k = .062 da coral; f = .037, k = .06 da manchas; f = .029, k = .057 da laberinto.
  function grayScott(op = {}) {
    const o = Object.assign({
      semilla: 1, ancho: 480, alto: 270, f: .0545, k: .062, du: 1, dv: .5, pasosPorSegundo: 360, cadaClave: 720,
      semillas: 14, colores: [[0, [10, 14, 24]], [.3, [24, 60, 90]], [.5, [80, 170, 170]], [.7, [240, 200, 140]], [1, [255, 250, 235]]],
    }, op);
    const W = o.ancho, H = o.alto, Nc = W * H;
    const xm = new Int32Array(W), xp = new Int32Array(W);
    for (let x = 0; x < W; x++) { xm[x] = (x - 1 + W) % W; xp[x] = (x + 1) % W; }
    const inicial = () => {
      const az = mulberry32(o.semilla * 97 + 3);
      const s = { u: new Float32Array(Nc).fill(1), v: new Float32Array(Nc), u2: new Float32Array(Nc), v2: new Float32Array(Nc) };
      for (let k = 0; k < o.semillas; k++) {
        const cx = az() * W, cy = az() * H, r = 3 + az() * 6;
        for (let y = Math.floor(cy - r); y <= cy + r; y++) for (let x = Math.floor(cx - r); x <= cx + r; x++) {
          if ((x - cx) ** 2 + (y - cy) ** 2 > r * r) continue;
          const i = ((y + H) % H) * W + (x + W) % W; s.u[i] = .5; s.v[i] = .25 + az() * .05;
        }
      }
      return s;
    };
    const copiar = s => ({ u: s.u.slice(), v: s.v.slice(), u2: new Float32Array(Nc), v2: new Float32Array(Nc) });
    const paso = s => {
      const { u: U, v: V, u2: U2, v2: V2 } = s, F = o.f, K = o.k, Du = o.du, Dv = o.dv;
      for (let y = 0; y < H; y++) {
        const a = ((y - 1 + H) % H) * W, b = y * W, c = ((y + 1) % H) * W;
        for (let x = 0; x < W; x++) {
          const l = xm[x], r = xp[x], i = b + x;
          const lu = .2 * (U[b + l] + U[b + r] + U[a + x] + U[c + x]) + .05 * (U[a + l] + U[a + r] + U[c + l] + U[c + r]) - U[i];
          const lv = .2 * (V[b + l] + V[b + r] + V[a + x] + V[c + x]) + .05 * (V[a + l] + V[a + r] + V[c + l] + V[c + r]) - V[i];
          const u = U[i], v = V[i], uvv = u * v * v;
          U2[i] = u + Du * lu - uvv + F * (1 - u);
          const nv = v + Dv * lv + uvv - (F + K) * v;
          V2[i] = nv > 1e-12 ? nv : 0;               // corta los valores muy chicos (los subnormales son lentos)
        }
      }
      s.u = U2; s.v = V2; s.u2 = U; s.v2 = V;                     // intercambia los búferes
    };
    const estado = conMemoria({ inicial, paso, copiar, cadaClave: o.cadaClave });
    const pal = paleta(o.colores), G = lienzoGrilla(W, H);
    function dibujar(ctx, t) {
      const s = estado(pasoDe(t, o.pasosPorSegundo)), V = s.v, d = G.img.data;
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        const i = y * W + x;
        // relieve: la pendiente de v hacia la luz (arriba a la izquierda) aclara u oscurece
        const gx = V[y * W + xp[x]] - V[y * W + xm[x]], gy = V[((y + 1) % H) * W + x] - V[((y - 1 + H) % H) * W + x];
        const luz = clamp(1 - (gx + gy) * 2.2, .55, 1.45);
        const j = Math.min(255, clamp(V[i] * 2.6) * 255 | 0) * 3;
        d[i * 4] = pal[j] * luz; d[i * 4 + 1] = pal[j + 1] * luz; d[i * 4 + 2] = pal[j + 2] * luz; d[i * 4 + 3] = 255;
      }
      G.g.putImageData(G.img, 0, 0);
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(G.c, 0, 0, ctx.canvas.width, ctx.canvas.height);
      ctx.restore();
    }
    return { dibujar, estado: t => estado(pasoDe(t, o.pasosPorSegundo)) };
  }

  // ───────────────────────── Marmoleado vectorial ─────────────────────────
  // Cada gota es un polígono; una gota nueva en C con radio r empuja todo lo demás con la fórmula que conserva el
  // área: P' = C + (P − C)·√(1 + r²/|P − C|²). El peine (Jaffer, «Mathematical Marbling») corre cada punto a lo largo
  // de M según la distancia d a la púa más cercana: P' = P + z·λ/(d + λ)·M (un corte puro: también conserva el
  // área). Los eventos van uno detrás de otro; el estado después de cada evento queda en memoria, y el evento en
  // curso se aplica a medias (gota con radio r·√k, peine con z·k), así que el cuadro es función pura de t.
  // Los bordes se subdividen donde se estiran (máx. `segmento` px) y se ralean donde se juntan.
  function marmoleado(op = {}) {
    const o = Object.assign({
      semilla: 1, gotas: 16, segmento: 4, papel: '#f3ead8', eventos: null, ancho: 1920, alto: 1080,
      colores: ['#1d3557', '#e63946', '#f1c453', '#2a9d8f', '#f4a261', '#264653', '#fefae0', '#8d5a97'],
    }, op);
    const az = mulberry32(o.semilla * 13 + 5), Wd = o.ancho, Hd = o.alto;
    let eventos = o.eventos;
    if (!eventos) {
      eventos = []; let t = .3;
      for (let i = 0; i < o.gotas; i++) {
        eventos.push({ tipo: 'gota', t0: t, dur: .32, c: [Wd * (.3 + az() * .4), Hd * (.25 + az() * .5)], r: 80 + az() * 120, color: o.colores[i % o.colores.length] });
        t += .4;
      }
      t += .3;
      eventos.push({ tipo: 'peine', t0: t, dur: 2.2, b: [0, 0], m: [0, 1], separacion: 150, z: 220, lambda: 26 }); t += 2.5;
      eventos.push({ tipo: 'peine', t0: t, dur: 2.2, b: [0, 40], m: [1, 0], separacion: 110, z: 160, lambda: 20 }); t += 2.5;
      eventos.push({ tipo: 'peine', t0: t, dur: 2, b: [55, 0], m: [0, -1], separacion: 75, z: 110, lambda: 14 });
    }
    for (let i = 1; i < eventos.length; i++)
      if (eventos[i].t0 < eventos[i - 1].t0 + eventos[i - 1].dur - 1e-9) throw new Error('marmoleado: los eventos se pisan');

    function mapa(ev, k) {
      if (ev.tipo === 'gota') {
        const [cx, cy] = ev.c, r2 = ev.r * ev.r * k;               // radio r·√k → área proporcional a k
        return (x, y) => {
          const dx = x - cx, dy = y - cy, d2 = dx * dx + dy * dy || 1e-9, f = Math.sqrt(1 + r2 / d2);
          return [cx + dx * f, cy + dy * f];
        };
      }
      const ml = Math.hypot(...ev.m), mx = ev.m[0] / ml, my = ev.m[1] / ml, nx = -my, ny = mx, s = ev.separacion, z = ev.z * k;
      return (x, y) => {
        let d = ((x - ev.b[0]) * nx + (y - ev.b[1]) * ny) % s; if (d < 0) d += s;
        d = Math.min(d, s - d);                                    // distancia a la púa más cercana
        const desp = z * ev.lambda / (d + ev.lambda);
        return [x + desp * mx, y + desp * my];
      };
    }
    function transformar(poli, f) {
      const n = poli.length / 2, out = [], max2 = o.segmento * o.segmento, min2 = .64;
      let lx = NaN, ly = NaN;
      const empujar = (x, y) => { if (!((x - lx) ** 2 + (y - ly) ** 2 < min2)) { out.push(x, y); lx = x; ly = y; } };
      const partir = (ax0, ay0, ax, ay, bx0, by0, bx, by, prof) => {
        if (prof < 10 && (bx - ax) ** 2 + (by - ay) ** 2 > max2) {
          const mx0 = (ax0 + bx0) / 2, my0 = (ay0 + by0) / 2, [mx, my] = f(mx0, my0);
          partir(ax0, ay0, ax, ay, mx0, my0, mx, my, prof + 1);
          partir(mx0, my0, mx, my, bx0, by0, bx, by, prof + 1);
        } else empujar(ax, ay);
      };
      const im = []; for (let i = 0; i < n; i++) im.push(f(poli[2 * i], poli[2 * i + 1]));
      for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        partir(poli[2 * i], poli[2 * i + 1], im[i][0], im[i][1], poli[2 * j], poli[2 * j + 1], im[j][0], im[j][1], 0);
      }
      return out;
    }
    function aplicar(capas, ev, k) {
      const f = mapa(ev, k), nuevas = capas.map(c => ({ color: c.color, p: transformar(c.p, f) }));
      if (ev.tipo === 'gota' && k > 0) {
        const r = ev.r * Math.sqrt(k), m = Math.max(24, Math.ceil(2 * Math.PI * r / o.segmento)), p = [];
        for (let i = 0; i < m; i++) { const a = i / m * Math.PI * 2; p.push(ev.c[0] + Math.cos(a) * r, ev.c[1] + Math.sin(a) * r); }
        nuevas.push({ color: ev.color, p });
      }
      return nuevas;
    }
    const despues = [[]];                // despues[i] = capas tras los primeros i eventos
    function capasEn(t) {
      let i = 0;
      while (i < eventos.length && t >= eventos[i].t0 + eventos[i].dur) i++;
      while (despues.length <= i) despues.push(aplicar(despues[despues.length - 1], eventos[despues.length - 1], 1));
      const base = despues[i], ev = eventos[i];
      if (!ev || t <= ev.t0) return base;
      const k = (t - ev.t0) / ev.dur, s = k * k * (3 - 2 * k);
      return aplicar(base, ev, s);
    }
    function dibujar(ctx, t) {
      const capas = capasEn(window.Reproductor ? Reproductor.cuadro(t) : t);
      ctx.save(); ctx.setTransform(ctx.canvas.width / Wd, 0, 0, ctx.canvas.height / Hd, 0, 0);
      ctx.fillStyle = o.papel; ctx.fillRect(0, 0, Wd, Hd);
      for (const c of capas) {
        const p = c.p; if (p.length < 6) continue;
        ctx.beginPath(); ctx.moveTo(p[0], p[1]);
        for (let i = 2; i < p.length; i += 2) ctx.lineTo(p[i], p[i + 1]);
        ctx.closePath(); ctx.fillStyle = c.color; ctx.fill();
      }
      ctx.restore();
    }
    const puntos = t => capasEn(t).reduce((a, c) => a + c.p.length / 2, 0);
    return { dibujar, eventos, puntos };
  }

  // ───────────────────────── Cáusticas de agua (WebGL2) ─────────────────────────
  // Sin memoria. La superficie es una suma de ondas con semilla (ω = √(g·|k|), como el agua de verdad). Una malla
  // de rayos de luz cae vertical, se refracta en la superficie (índice ~1,333) y llega al fondo a `profundidad` px;
  // cada triángulo pinta su luz en el lugar al que llegó, con brillo = área antes / área después (la idea de la
  // «WebGL Water» de Evan Wallace, escrita desde cero). Mezcla aditiva: donde los rayos se juntan, la luz se suma.
  // Con dispersión, R, G y B se refractan con índices un poco distintos (bordes con arcoíris).
  function causticas(op = {}) {
    const o = Object.assign({
      semilla: 1, ondas: 9, malla: [512, 288], profundidad: 900, brillo: .3, dispersion: true,
      color: [.75, .95, 1], fondo: [0, 0, 0, 0], largo: [70, 340], pendiente: .2, velocidad: 1,
    }, op);
    const az = mulberry32(o.semilla * 101 + 1), K = Math.min(12, o.ondas);
    const ondas = new Float32Array(12 * 4);                       // kx, ky, amplitud, fase
    const omega = new Float32Array(12);
    const dir0 = az() * Math.PI * 2;
    let sumaPend = 0;
    const tmp = [];
    for (let i = 0; i < K; i++) {
      const L = o.largo[0] * Math.pow(o.largo[1] / o.largo[0], az()), kk = 2 * Math.PI / L;
      const a = dir0 + (az() - .5) * 2.2;
      const amp = L * (.4 + az() * .6);
      tmp.push([Math.cos(a) * kk, Math.sin(a) * kk, amp, az() * Math.PI * 2]);
      sumaPend += amp * kk;
      omega[i] = Math.sqrt(9.8 * kk * 120) * o.velocidad;       // g escalado a px
    }
    tmp.forEach(([kx, ky, amp, f], i) => ondas.set([kx, ky, amp * o.pendiente / sumaPend, f], i * 4));

    const VERT = `#version 300 es
    precision highp float;
    in vec2 q;                       // 0..1 sobre un área un poco más grande que el cuadro
    uniform vec2 uRes; uniform float uT, uProf, uEta;
    uniform vec4 uOnda[12]; uniform float uOmega[12]; uniform int uK;
    out vec2 vAntes; out vec2 vDespues;
    void main() {
      vec2 p = (q * 1.2 - 0.1) * uRes;
      vec2 g = vec2(0.0);
      for (int i = 0; i < 12; i++) {
        if (i >= uK) break;
        vec4 w = uOnda[i];
        g += w.z * w.xy * cos(dot(w.xy, p) - uOmega[i] * uT + w.w);     // gradiente de la altura
      }
      vec3 n = normalize(vec3(-g, 1.0));
      vec3 r = refract(vec3(0.0, 0.0, -1.0), n, 1.0 / uEta);
      vec2 d = p + r.xy * (uProf / -r.z);
      vAntes = p; vDespues = d;
      // y hacia abajo queda como fila 0 de WebGL: readPixels sale derecho, sin voltear
      gl_Position = vec4(d / uRes * 2.0 - 1.0, 0.0, 1.0);
    }`;
    const FRAG = `#version 300 es
    precision highp float;
    in vec2 vAntes; in vec2 vDespues;
    uniform vec3 uColor; uniform float uBrillo;
    out vec4 color;
    void main() {
      float antes = length(dFdx(vAntes)) * length(dFdy(vAntes));
      float despues = length(dFdx(vDespues)) * length(dFdy(vDespues));
      float luz = antes / max(despues, 1e-6) * uBrillo;
      color = vec4(uColor * luz, 1.0);
    }`;
    let lienzo, gl, prog, U = {}, nIdx = 0;
    function preparar(w, h) {
      if (!lienzo) {
        lienzo = document.createElement('canvas');
        gl = lienzo.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false, premultipliedAlpha: false });
        if (!gl) throw new Error('causticas: este navegador no tiene WebGL2');
        const sh = (tipo, src) => {
          const s = gl.createShader(tipo); gl.shaderSource(s, src); gl.compileShader(s);
          if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('causticas: ' + gl.getShaderInfoLog(s));
          return s;
        };
        prog = gl.createProgram();
        gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
        gl.linkProgram(prog);
        if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('causticas: ' + gl.getProgramInfoLog(prog));
        const [mx, my] = o.malla, v = new Float32Array((mx + 1) * (my + 1) * 2), idx = new Uint32Array(mx * my * 6);
        for (let y = 0; y <= my; y++) for (let x = 0; x <= mx; x++) { const i = y * (mx + 1) + x; v[i * 2] = x / mx; v[i * 2 + 1] = y / my; }
        let k = 0;
        for (let y = 0; y < my; y++) for (let x = 0; x < mx; x++) {
          const a = y * (mx + 1) + x, b = a + 1, c = a + mx + 1, d = c + 1;
          idx.set([a, b, c, b, d, c], k); k += 6;
        }
        nIdx = k;
        const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
        const bv = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bv); gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
        const loc = gl.getAttribLocation(prog, 'q'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
        const bi = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, bi); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
        for (const n of ['uRes', 'uT', 'uProf', 'uEta', 'uOnda', 'uOmega', 'uK', 'uColor', 'uBrillo']) U[n] = gl.getUniformLocation(prog, n);
      }
      if (lienzo.width !== w || lienzo.height !== h) { lienzo.width = w; lienzo.height = h; }
      gl.viewport(0, 0, w, h);
    }
    // modo: cómo se pega la luz sobre ctx ('lighter' suma, 'screen' aclara sin quemar tanto)
    function dibujar(ctx, t, modo = 'lighter') {
      const W = ctx.canvas.width, H = ctx.canvas.height;
      preparar(W, H);
      gl.useProgram(prog);
      gl.clearColor(...o.fondo); gl.colorMask(true, true, true, true); gl.clear(gl.COLOR_BUFFER_BIT);
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
      gl.uniform2f(U.uRes, W, H); gl.uniform1f(U.uT, t); gl.uniform1f(U.uProf, o.profundidad);
      gl.uniform4fv(U.uOnda, ondas); gl.uniform1fv(U.uOmega, omega); gl.uniform1i(U.uK, K);
      gl.uniform1f(U.uBrillo, o.brillo);              // agua quieta: área antes = área después → brillo
      const canales = o.dispersion ? [[1.329, [o.color[0], 0, 0]], [1.333, [0, o.color[1], 0]], [1.338, [0, 0, o.color[2]]]] : [[1.333, o.color]];
      for (const [eta, col] of canales) {
        gl.uniform1f(U.uEta, eta); gl.uniform3f(U.uColor, ...col);
        gl.drawElements(gl.TRIANGLES, nIdx, gl.UNSIGNED_INT, 0);
      }
      gl.disable(gl.BLEND);
      // vuelve por readPixels a un lienzo de CPU (no drawImage del lienzo WebGL): el lienzo del video sigue
      // siendo de CPU y el cuadro sale idéntico en cada corrida (ver la nota de demo.html)
      if (!cpu || cpu.c.width !== W || cpu.c.height !== H) cpu = lienzoGrilla(W, H);
      gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(cpu.img.data.buffer));
      cpu.g.putImageData(cpu.img, 0, 0);
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = modo;
      ctx.drawImage(cpu.c, 0, 0);
      ctx.restore();
    }
    let cpu = null;
    return { dibujar };
  }

  return { physarum, grayScott, marmoleado, causticas, mulberry32, hash3 };
})();
