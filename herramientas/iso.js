/* Iso: dibujo isométrico en Canvas 2D para la técnica 26 («máquina isométrica»). Script clásico, sin dependencias.
 *
 * Ideas (no código) de Anatomy (wheresryan22/anatomy, MIT): sólidos rellenos y no alambres, tonos por cara con una
 * sola luz, orden del pintor medido y no a ojo, ninguna línea termina en el aire, un solo acento iluminado; y de
 * ISO-GLOW (isoglow.dev, MIT): el tema oscuro donde lo encendido brilla.
 *
 *   const cam = Iso.camara({ escala, cx, cy, giro, centro });   // giro en radianes alrededor del eje z
 *   const E = Iso.escena(cam, Iso.TEMAS.oscuro);
 *   E.caja({ x, y, z, w, d, h }, { nombre, tono: 'lo'|'mid'|'hi', lit, grupo, detalle(ctx, E) })
 *   E.cilindro({ x, y, z, r, h }, estilo)        // cilindro vertical
 *   E.tubo([[x,y,z], …], { nombre, r, toca: [nombres] })   // cable de tramos paralelos a los ejes, con codos de bola
 *   E.pieza(aabb, { nombre }, (ctx, E) => …)      // pieza a medida (brazo, aguja) que entra al orden con su caja
 *   E.pintar(ctx)                                 // ordena de atrás hacia adelante (por separación de cajas) y dibuja
 *   dentro de detalle(): E.linea(ctx, pts3, { tono, libre }), E.contorno(ctx, pts3), E.punto(ctx, p3, r),
 *                        E.textoEnCara(ctx, texto, p3, tam, { sobre }) (texto grabado en una tapa)
 *   Iso.texto(ctx, texto, x, y, { tam, peso, fuente, color, alinear, sobre, grupo })   // texto de pantalla, registrado
 *
 * Registro para las guardias (herramientas/maquina_iso.py): Iso.grabar(cam) antes de dibujar un cuadro y
 * Iso.terminar() después devuelven sólidos (caja 3D, silueta y bordes en pantalla, orden de dibujo), líneas (con sus
 * extremos y si son libres), terminales, textos, encendidos y ciclos del orden. Fuera de la grabación no cuesta nada.
 *
 * Todo es función pura de lo que se le pasa: nada de reloj ni azar. El mismo t da el mismo cuadro.
 */
window.Iso = (() => {
  const C30 = Math.cos(Math.PI / 6), RX = Math.SQRT2 * C30, RY = Math.SQRT2 * 0.5;   // un círculo del suelo → elipse

  // Tonos: cada tono tiene su relleno en sombra y en luz (la cara se mezcla según mire a la luz) y su línea.
  const TEMAS = {
    oscuro: {                                     // ISO-GLOW: casi negro, línea fina clara, lo encendido brilla en ámbar
      nombre: 'oscuro', fondo: '#0b0e13', halo: 'rgba(0,0,0,.6)', papel: '#141922',
      relleno: { lo: ['#10141b', '#1b212b'], mid: ['#151a23', '#252c38'], hi: ['#1b212b', '#323b4a'] },
      linea: { faint: 'rgba(170,186,212,.20)', lo: 'rgba(170,186,212,.42)', mid: 'rgba(196,208,228,.66)', hi: 'rgba(226,233,245,.92)' },
      lit: { relleno: ['#7a4a10', '#ffbf5c'], linea: '#ffd89a', brillo: 'rgba(255,176,64,.85)', blur: 26 },
      texto: '#e6ebf3', texto2: '#8f9bb0', acento: '#ffb547',
    },
    claro: {                                      // Anatomy editorial: papel, tinta, el acento en tinta llena
      nombre: 'claro', fondo: '#f3f0e8', halo: 'rgba(60,50,30,.16)', papel: '#f3f0e8',
      relleno: { lo: ['#d9d4c8', '#e9e5db'], mid: ['#e2ddd2', '#f2efe7'], hi: ['#ebe7de', '#fbfaf6'] },
      linea: { faint: 'rgba(30,34,43,.22)', lo: 'rgba(30,34,43,.45)', mid: 'rgba(30,34,43,.72)', hi: 'rgba(30,34,43,.95)' },
      lit: { relleno: ['#14171d', '#3a4150'], linea: '#0e1014', brillo: null, blur: 0 },
      texto: '#1d222b', texto2: '#6b6f78', acento: '#c8643b',
    },
  };

  function mezcla(a, b, k) {
    const h = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16)), A = h(a), B = h(b);
    return 'rgb(' + A.map((x, i) => Math.round(x + (B[i] - x) * k)).join(',') + ')';
  }

  function camara({ escala = 1, cx = 960, cy = 540, giro = 0, centro = [0, 0, 0] } = {}) {
    const c = Math.cos(giro), s = Math.sin(giro);
    const p2 = p => {
      const x = p[0] - centro[0], y = p[1] - centro[1], z = p[2] - centro[2];
      const xr = x * c - y * s, yr = x * s + y * c;
      return [cx + (xr - yr) * C30 * escala, cy + ((xr + yr) * 0.5 - z) * escala];
    };
    const v = [c + s, c - s, 1];                  // hacia quien mira, en el mundo (el (1,1,1) del marco girado)
    const prof = p => p[0] * v[0] + p[1] * v[1] + p[2] * v[2];
    return { p2, prof, v, escala, giro, cx, cy, centro };
  }

  // ───────── registro (para las guardias) ─────────
  let R = null;
  function grabar(cam) {
    R = { camara: { v: cam.v, giro: cam.giro, escala: cam.escala }, solidos: [], lineas: [], terminales: [], textos: [],
          encendidos: [], ciclos: [], orden: 0 };
  }
  function terminar() { const r = R; R = null; if (r) r.encendidos = [...new Set(r.encendidos)]; return r; }
  const siguiente = () => (R ? R.orden++ : 0);
  const r2 = a => a.map(p => [Math.round(p[0] * 100) / 100, Math.round(p[1] * 100) / 100]);

  function casco(pts) {                            // envolvente convexa (Andrew), para la silueta
    const P = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const cruz = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const abajo = [], arriba = [];
    for (const p of P) { while (abajo.length >= 2 && cruz(abajo[abajo.length - 2], abajo[abajo.length - 1], p) <= 0) abajo.pop(); abajo.push(p); }
    for (let i = P.length - 1; i >= 0; i--) { const p = P[i]; while (arriba.length >= 2 && cruz(arriba[arriba.length - 2], arriba[arriba.length - 1], p) <= 0) arriba.pop(); arriba.push(p); }
    return abajo.slice(0, -1).concat(arriba.slice(0, -1));
  }
  function dentroDe(poli, x, y) {                   // punto en polígono convexo (o casi)
    let dentro = false;
    for (let i = 0, j = poli.length - 1; i < poli.length; j = i++) {
      const [xi, yi] = poli[i], [xj, yj] = poli[j];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) dentro = !dentro;
    }
    return dentro;
  }

  // ───────── la escena ─────────
  function escena(cam, tema = TEMAS.oscuro) {
    const items = [];
    const L = cam.escala;
    const luz = [-0.55, 0.83];                     // luz fija del mundo (horizontal); la tapa siempre es la más clara
    const anchoLinea = 1.5;

    function colorCara(tono, n, lit) {
      const par = lit ? tema.lit.relleno : tema.relleno[tono];
      const k = n === 'tapa' ? 1 : 0.18 + 0.55 * Math.max(0, n[0] * luz[0] + n[1] * luz[1]);
      return mezcla(par[0], par[1], k);
    }
    const colorLinea = (tono, lit) => (lit ? tema.lit.linea : tema.linea[tono] || tema.linea.mid);

    function poligono(ctx, pts, relleno, trazo, ancho = anchoLinea) {
      ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
      if (relleno) { ctx.fillStyle = relleno; ctx.fill(); }
      if (trazo) { ctx.strokeStyle = trazo; ctx.lineWidth = ancho; ctx.lineJoin = 'round'; ctx.stroke(); }
    }
    function brillo(ctx, sil, lit) {               // el resplandor del acento (sólo en el tema oscuro)
      if (!lit || !tema.lit.brillo) return;
      ctx.save(); ctx.shadowColor = tema.lit.brillo; ctx.shadowBlur = tema.lit.blur;
      poligono(ctx, sil, tema.lit.relleno[1]); ctx.restore();
    }
    function registrarSolido(e, tipo, aabb, sil, bordes) {
      if (!R) return;
      R.solidos.push({ nombre: e.nombre, grupo: e.grupo || e.nombre, tipo, aabb, sil: r2(sil), bordes: bordes.map(b => b.map(v => Math.round(v * 100) / 100)),
                       orden: siguiente(), lit: !!e.lit, dentro: e.dentro || null, cable: e.cable || null, toca: e.toca || [] });
      if (e.lit) R.encendidos.push(e.grupo || e.nombre);
    }

    // caja paralela a los ejes: tapa + las caras laterales que miran a quien mira
    function caja(b, e = {}) {
      const x0 = b.x, y0 = b.y, z0 = b.z, x1 = b.x + b.w, y1 = b.y + b.d, z1 = b.z + b.h;
      const aabb = [x0, y0, z0, x1, y1, z1];
      items.push({ nombre: e.nombre, aabb, e, dibujar(ctx) {
        const P = (x, y, z) => cam.p2([x, y, z]);
        const caras = [];
        if (cam.v[0] > 1e-6) caras.push([[1, 0], [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)]]);
        if (cam.v[0] < -1e-6) caras.push([[-1, 0], [P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1)]]);
        if (cam.v[1] > 1e-6) caras.push([[0, 1], [P(x1, y1, z0), P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1)]]);
        if (cam.v[1] < -1e-6) caras.push([[0, -1], [P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)]]);
        caras.push(['tapa', [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)]]);
        const sil = casco(caras.flatMap(c => c[1]));
        brillo(ctx, sil, e.lit);
        const tl = colorLinea(e.tono || 'mid', e.lit);
        for (const [n, pts] of caras) poligono(ctx, pts, colorCara(e.tono || 'mid', n, e.lit), null);
        for (const [, pts] of caras) poligono(ctx, pts, null, tl, e.ancho || anchoLinea);
        const bordes = [];
        for (const [, pts] of caras) for (let i = 0; i < 4; i++) bordes.push([...pts[i], ...pts[(i + 1) % 4]]);
        registrarSolido(e, 'caja', aabb, sil, bordes);
        if (e.detalle) e.detalle(ctx, api);
      } });
    }

    // cilindro vertical: costado con degradé (superficie curva sin escalones) y tapa elíptica
    function cilindro(c, e = {}) {
      const aabb = [c.x - c.r, c.y - c.r, c.z, c.x + c.r, c.y + c.r, c.z + c.h];
      items.push({ nombre: e.nombre, aabb, e, dibujar(ctx) {
        const T = cam.p2([c.x, c.y, c.z + c.h]), B = cam.p2([c.x, c.y, c.z]), rx = c.r * RX * L, ry = c.r * RY * L;
        const sil = [];
        for (let i = 0; i <= 12; i++) { const a = Math.PI + Math.PI * i / 12; sil.push([T[0] + rx * Math.cos(a), T[1] + ry * Math.sin(a)]); }
        for (let i = 0; i <= 12; i++) { const a = Math.PI * i / 12; sil.push([B[0] + rx * Math.cos(a), B[1] + ry * Math.sin(a)]); }
        brillo(ctx, sil, e.lit);
        const tono = e.tono || 'mid', tl = colorLinea(tono, e.lit);
        // costado: la normal recorre el frente; la luz decide cada parada del degradé
        const g = ctx.createLinearGradient(B[0] - rx, 0, B[0] + rx, 0);
        for (let i = 0; i <= 6; i++) {
          const u = i / 6, sx = u * 2 - 1;                          // posición en pantalla, -1..1
          const ang = Math.asin(Math.max(-1, Math.min(1, sx)));       // ángulo de la normal desde el frente de la vista
          const vh = Math.atan2(cam.v[1], cam.v[0]) - ang;            // la normal, en el mundo
          g.addColorStop(u, colorCara(tono, [Math.cos(vh), Math.sin(vh)], e.lit));
        }
        ctx.beginPath(); ctx.moveTo(T[0] - rx, T[1]); ctx.lineTo(B[0] - rx, B[1]); ctx.ellipse(B[0], B[1], rx, ry, 0, Math.PI, 0, true);
        ctx.lineTo(T[0] + rx, T[1]); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
        ctx.strokeStyle = tl; ctx.lineWidth = e.ancho || anchoLinea; ctx.lineJoin = 'round';
        ctx.beginPath(); ctx.moveTo(T[0] - rx, T[1]); ctx.lineTo(B[0] - rx, B[1]); ctx.ellipse(B[0], B[1], rx, ry, 0, Math.PI, 0, true); ctx.lineTo(T[0] + rx, T[1]); ctx.stroke();
        ctx.beginPath(); ctx.ellipse(T[0], T[1], rx, ry, 0, 0, Math.PI * 2); ctx.fillStyle = colorCara(tono, 'tapa', e.lit); ctx.fill(); ctx.stroke();
        const bordes = [];
        for (let i = 0; i < 16; i++) {
          const a = Math.PI * 2 * i / 16, b = Math.PI * 2 * (i + 1) / 16;
          bordes.push([T[0] + rx * Math.cos(a), T[1] + ry * Math.sin(a), T[0] + rx * Math.cos(b), T[1] + ry * Math.sin(b)]);
        }
        bordes.push([T[0] - rx, T[1], B[0] - rx, B[1]], [T[0] + rx, T[1], B[0] + rx, B[1]]);
        for (let i = 0; i < 8; i++) {
          const a = Math.PI * i / 8, b = Math.PI * (i + 1) / 8;
          bordes.push([B[0] + rx * Math.cos(a), B[1] + ry * Math.sin(a), B[0] + rx * Math.cos(b), B[1] + ry * Math.sin(b)]);
        }
        registrarSolido(e, 'cilindro', aabb, sil, bordes);
        if (e.detalle) e.detalle(ctx, api);
      } });
    }

    // cable: tramos paralelos a los ejes (rutas ortogonales, junto a la estructura), codos de bola en cada quiebre
    function tubo(pts, e = {}) {
      const r = e.r || 3;
      for (let i = 0; i < pts.length - 1; i++) {
        const a = pts[i], b = pts[i + 1];
        const aabb = [0, 1, 2].map(k => Math.min(a[k], b[k]) - r).concat([0, 1, 2].map(k => Math.max(a[k], b[k]) + r));
        items.push({ nombre: `${e.nombre}#${i}`, aabb, e, dibujar(ctx) {
          const A = cam.p2(a), B = cam.p2(b), w = 2 * r * L;
          ctx.save(); ctx.lineCap = 'butt';
          if (e.lit && tema.lit.brillo) { ctx.shadowColor = tema.lit.brillo; ctx.shadowBlur = tema.lit.blur; }
          ctx.strokeStyle = colorLinea(e.tono || 'mid', e.lit); ctx.lineWidth = w + 2 * anchoLinea;
          ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();
          ctx.shadowBlur = 0;
          ctx.strokeStyle = colorCara(e.tono || 'mid', [0.3, 0.9], e.lit); ctx.lineWidth = w;
          ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke(); ctx.restore();
          const dx = B[0] - A[0], dy = B[1] - A[1], n = Math.hypot(dx, dy) || 1, ox = -dy / n * (r * L + anchoLinea / 2), oy = dx / n * (r * L + anchoLinea / 2);
          const sil = [[A[0] + ox, A[1] + oy], [B[0] + ox, B[1] + oy], [B[0] - ox, B[1] - oy], [A[0] - ox, A[1] - oy]];
          registrarSolido({ ...e, nombre: `${e.nombre}#${i}`, grupo: e.nombre, cable: e.nombre }, 'tubo', aabb, sil,
                          [[sil[0][0], sil[0][1], sil[1][0], sil[1][1]], [sil[2][0], sil[2][1], sil[3][0], sil[3][1]]]);
        } });
      }
      for (let i = 1; i < pts.length - 1; i++) {                   // codo de bola
        const p = pts[i], rb = r * 1.35;
        items.push({ nombre: `${e.nombre}@${i}`, aabb: [p[0] - rb, p[1] - rb, p[2] - rb, p[0] + rb, p[1] + rb, p[2] + rb], e, dibujar(ctx) {
          const P = cam.p2(p), rr = rb * L * 1.05;
          ctx.save(); ctx.beginPath(); ctx.arc(P[0], P[1], rr, 0, Math.PI * 2);
          const g = ctx.createRadialGradient(P[0] - rr * .35, P[1] - rr * .4, rr * .1, P[0], P[1], rr);
          g.addColorStop(0, colorCara(e.tono || 'mid', 'tapa', e.lit)); g.addColorStop(1, colorCara(e.tono || 'mid', [0, -1], e.lit));
          ctx.fillStyle = g; ctx.fill(); ctx.strokeStyle = colorLinea(e.tono || 'mid', e.lit); ctx.lineWidth = anchoLinea; ctx.stroke(); ctx.restore();
          if (R) R.terminales.push({ x: P[0], y: P[1], r: rr, orden: siguiente(), nombre: `${e.nombre}@${i}` });
        } });
      }
      // el cable entero, como línea con extremos, para la guardia de líneas sueltas y la de cruces
      items.push({ nombre: `${e.nombre}:linea`, aabb: null, e, dibujar() {
        if (R) R.lineas.push({ nombre: e.nombre, pts: r2(pts.map(cam.p2)), pts3: pts, r, libre: false, cerrada: false,
                               toca: e.toca || [], cable: true, orden: siguiente() });
      } });
    }

    // detalles (se llaman dentro de detalle(), en el lugar del sólido que los lleva)
    function linea(ctx, pts3, e = {}) {
      const P = pts3.map(cam.p2);
      ctx.save(); ctx.strokeStyle = e.color || colorLinea(e.tono || 'lo', e.lit); ctx.lineWidth = e.ancho || 1.1; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.beginPath(); P.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); if (e.cerrada) ctx.closePath(); ctx.stroke(); ctx.restore();
      if (R) R.lineas.push({ nombre: e.nombre || 'linea', pts: r2(P), libre: e.libre || false, cerrada: !!e.cerrada, toca: e.toca || [], orden: siguiente() });
      if (R && e.lit) R.encendidos.push(e.grupo || e.nombre);
    }
    const contorno = (ctx, pts3, e = {}) => linea(ctx, pts3, { ...e, cerrada: true });
    function punto(ctx, p3, r = 1.6, e = {}) {                       // tornillo o terminal: un punto con anillo
      const P = cam.p2(p3), rr = r * L;
      ctx.save(); ctx.beginPath(); ctx.arc(P[0], P[1], rr, 0, Math.PI * 2); ctx.fillStyle = e.color || colorLinea(e.tono || 'mid'); ctx.fill(); ctx.restore();
      if (R) R.terminales.push({ x: P[0], y: P[1], r: rr, orden: siguiente(), nombre: e.nombre || 'punto' });
    }
    function textoEnCara(ctx, s, p3, tam, e = {}) {                  // grabado en una tapa (plano z): se lee a lo largo de x
      const O = cam.p2(p3), X = cam.p2([p3[0] + 1, p3[1], p3[2]]), Y = cam.p2([p3[0], p3[1] + 1, p3[2]]);
      ctx.save(); ctx.transform(X[0] - O[0], X[1] - O[1], Y[0] - O[0], Y[1] - O[1], O[0], O[1]);
      ctx.font = `${e.peso || 700} ${tam}px ${e.fuente || '"Segoe UI", Arial, sans-serif'}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = e.color || colorLinea('hi'); const w = ctx.measureText(s).width; ctx.fillText(s, 0, 0); ctx.restore();
      if (R) {
        const esq = [[-w / 2, -tam / 2], [w / 2, -tam / 2], [w / 2, tam / 2], [-w / 2, tam / 2]].map(([u, v]) => cam.p2([p3[0] + u, p3[1] + v, p3[2]]));
        const xs = esq.map(p => p[0]), ys = esq.map(p => p[1]);
        R.textos.push({ texto: s, caja: [Math.min(...xs), Math.min(...ys), Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)],
                        poli: r2(esq), sobre: e.sobre || null, grupo: e.grupo || null, orden: siguiente() });
      }
    }

    // orden del pintor: A va antes que B si una cara de separación entre sus cajas deja a A detrás (mirando según v)
    function detras(A, B) {
      const eps = 0.01; let r = 0;
      for (let k = 0; k < 3; k++) {
        const vk = cam.v[k]; if (Math.abs(vk) < 1e-6) continue;
        const aDet = vk > 0 ? A[k + 3] <= B[k] + eps : A[k] >= B[k + 3] - eps;
        const bDet = vk > 0 ? B[k + 3] <= A[k] + eps : B[k] >= A[k + 3] - eps;
        if (aDet && !bDet) { if (r === -1) return 0; r = 1; } else if (bDet && !aDet) { if (r === 1) return 0; r = -1; }
      }
      return r;
    }
    function rectDe(aabb) {
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const x of [aabb[0], aabb[3]]) for (const y of [aabb[1], aabb[4]]) for (const z of [aabb[2], aabb[5]]) {
        const p = cam.p2([x, y, z]); x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]);
      }
      return [x0, y0, x1, y1];
    }
    function pintar(ctx) {
      const S = items.filter(it => it.aabb), sueltos = items.filter(it => !it.aabb);
      const n = S.length, rect = S.map(it => rectDe(it.aabb));
      const pr = S.map(it => cam.prof([(it.aabb[0] + it.aabb[3]) / 2, (it.aabb[1] + it.aabb[4]) / 2, (it.aabb[2] + it.aabb[5]) / 2]));
      const sal = S.map(() => []), ent = new Array(n).fill(0);
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        const a = rect[i], b = rect[j];
        if (a[2] <= b[0] || b[2] <= a[0] || a[3] <= b[1] || b[3] <= a[1]) continue;
        const d = detras(S[i].aabb, S[j].aabb);
        if (d === 1) { sal[i].push(j); ent[j]++; } else if (d === -1) { sal[j].push(i); ent[i]++; }
      }
      const hecho = new Array(n).fill(false), orden = [];
      for (let paso = 0; paso < n; paso++) {
        let m = -1;
        for (let i = 0; i < n; i++) if (!hecho[i] && ent[i] === 0 && (m < 0 || pr[i] < pr[m] - 1e-9 || (Math.abs(pr[i] - pr[m]) <= 1e-9 && i < m))) m = i;
        if (m < 0) {                                                 // ciclo: se rompe por profundidad y queda registrado
          for (let i = 0; i < n; i++) if (!hecho[i] && (m < 0 || pr[i] < pr[m])) m = i;
          if (R) R.ciclos.push(S[m].nombre);
        }
        hecho[m] = true; orden.push(S[m]); for (const j of sal[m]) ent[j]--;
      }
      for (const it of orden) it.dibujar(ctx);
      for (const it of sueltos) it.dibujar(ctx);
    }

    // pieza a medida (un brazo, una aguja): entra al orden del pintor con su caja y se dibuja con detalles
    const pieza = (aabb, e, dibujar) => items.push({ nombre: e.nombre, aabb, e, dibujar: ctx => {
      dibujar(ctx, api);
      const [x0, y0, z0, x1, y1, z1] = aabb;          // la pieza a medida también se registra (con la silueta de su caja) para las guardias
      registrarSolido(e, 'pieza', aabb, casco([x0, x1].flatMap(x => [y0, y1].flatMap(y => [z0, z1].map(z => cam.p2([x, y, z]))))), []);
    } });

    const api = { cam, tema, caja, cilindro, tubo, pieza, linea, contorno, punto, textoEnCara, pintar, items };
    return api;
  }

  // texto de pantalla (titulares, tarjetas): se registra para la guardia del 90 % central y de los encimados
  function texto(ctx, s, x, y, e = {}) {
    const tam = e.tam || 32;
    ctx.save(); ctx.font = `${e.peso || 600} ${tam}px ${e.fuente || '"Segoe UI", "Helvetica Neue", Arial, sans-serif'}`;
    ctx.fillStyle = e.color || '#fff'; ctx.textAlign = e.alinear || 'left'; ctx.textBaseline = 'alphabetic';
    if (e.alfa !== undefined) ctx.globalAlpha *= e.alfa;
    ctx.fillText(s, x, y); const m = ctx.measureText(s); ctx.restore();
    const w = m.width, x0 = e.alinear === 'center' ? x - w / 2 : e.alinear === 'right' ? x - w : x;
    if (R && (e.alfa === undefined || e.alfa > 0.05) && s.trim())
      R.textos.push({ texto: s, caja: [x0, y - tam * 0.8, w, tam * 1.05], sobre: e.sobre || null, grupo: e.grupo || null, orden: siguiente() });
    return w;
  }
  function caja2d(nombre, x, y, w, h, e = {}) {                    // una caja de pantalla que no es texto (p. ej. el subtítulo)
    if (R) R.textos.push({ texto: nombre, caja: [x, y, w, h], sobre: null, grupo: e.grupo || nombre, orden: siguiente() });
  }

  // qué pieza está bajo el puntero (la de arriba en el orden de dibujo)
  function tocar(registro, x, y) {
    let mejor = null;
    for (const s of registro.solidos) if (dentroDe(s.sil, x, y) && (!mejor || s.orden > mejor.orden)) mejor = s;
    return mejor;
  }

  return { TEMAS, camara, escena, grabar, terminar, texto, caja2d, tocar, casco, mezcla };
})();
