/* Movimiento «de estudio» para videos comerciales y motion graphics. Todo es función pura del tiempo:
 * el mismo t da siempre el mismo valor (así se puede exportar cuadro a cuadro y revisar).
 *
 *   const M = Movimiento;
 *   const P = M.pulsos(120, 0.4);          // grilla: 120 BPM, el pulso 0 cae a los 0,4 s
 *   P.t(8)                                 // segundo en que cae el pulso 8
 *   M.curva.expo(k), M.curva.back(k) …     // curvas de aceleración (k de 0 a 1)
 *   M.tramo(t, P.t(4), P.t(5), 'back')     // avance 0..1 entre dos instantes, con curva
 *   M.resorte(t, [[P.t(2), 0, 1], [P.t(6), 1, .3]], { hz: 2.2, amort: .72 })   // suma de resortes
 *   M.morph(puntosA, puntosB, k)           // una forma que se vuelve otra (mismos N puntos)
 *   M.forma.circulo(cx, cy, r, 240), M.forma.poligono(...), M.forma.estrella(...), M.forma.rectRedondo(...)
 *   M.puntosDeTexto('Hola', '900 160px Inter', 5000)   // puntos sobre las letras (para partículas)
 *   M.motas(ctx, t, { color: '240,164,58' })                 // polvo que flota: ningún tramo queda quieto
 *
 * Técnicas tomadas de videos comerciales de referencia hechos con agentes:
 * todo en grilla de pulsos, resortes en forma cerrada que se suman, morph por puntos, texto de partículas.
 */
window.Movimiento = (() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;

  // ── grilla de pulsos ──
  function pulsos(bpm, inicio = 0) {
    const s = 60 / bpm;
    return {
      bpm, s, inicio,
      t: b => inicio + b * s,                       // pulso → segundo
      b: t => (t - inicio) / s,                     // segundo → pulso (fraccionario)
      compas: (c, b = 0) => inicio + (c * 4 + b) * s,
      golpe: (t, b, dur = .12) => Math.exp(-Math.max(0, t - (inicio + b * s)) / dur) * (t >= inicio + b * s),   // destello que decae
    };
  }

  // ── curvas de aceleración (0→1) ──
  const curva = {
    lineal: k => k,
    suave: k => k * k * (3 - 2 * k),
    expo: k => k === 1 ? 1 : 1 - Math.pow(2, -10 * k),                   // arranca rápido y frena suave
    expoIn: k => k === 0 ? 0 : Math.pow(2, 10 * k - 10),
    expoInOut: k => k < .5 ? Math.pow(2, 20 * k - 10) / 2 : (2 - Math.pow(2, -20 * k + 10)) / 2,
    cubica: k => 1 - Math.pow(1 - k, 3),
    back: k => { const c = 1.70158, c3 = c + 1; return 1 + c3 * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },   // se pasa y vuelve
    backSuave: k => { const c = .9, c3 = c + 1; return 1 + c3 * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
    bounce: k => {                                                       // rebota al llegar
      const n = 7.5625, d = 2.75;
      if (k < 1 / d) return n * k * k;
      if (k < 2 / d) return n * (k -= 1.5 / d) * k + .75;
      if (k < 2.5 / d) return n * (k -= 2.25 / d) * k + .9375;
      return n * (k -= 2.625 / d) * k + .984375;
    },
  };
  function tramo(t, a, b, nombre = 'expo') {
    const k = clamp((t - a) / (b - a));
    return (curva[nombre] || curva.expo)(k);
  }

  // ── resortes en forma cerrada (respuesta a un escalón) ──
  function escalon(dt, hz, amort) {
    if (dt <= 0) return 0;
    const w = 2 * Math.PI * hz;
    if (amort >= 1) return 1 - Math.exp(-w * dt) * (1 + w * dt);
    const wd = w * Math.sqrt(1 - amort * amort);
    return 1 - Math.exp(-amort * w * dt) * (Math.cos(wd * dt) + (amort * w / wd) * Math.sin(wd * dt));
  }
  /** Valor que cambia de destino varias veces: cambios = [[t, desde, hasta], ...] ordenados.
   *  Es la suma de un resorte por cambio: sigue siendo función pura del tiempo. */
  function resorte(t, cambios, { hz = 2, amort = .75 } = {}) {
    if (!cambios.length) return 0;
    let v = cambios[0][1];
    for (const [tc, desde, hasta] of cambios) v += (hasta - desde) * escalon(t - tc, hz, amort);
    return v;
  }

  // ── formas como listas de N puntos (para transformarlas) ──
  const forma = {
    circulo: (cx, cy, r, n = 240) => Array.from({ length: n }, (_, i) => { const a = -Math.PI / 2 + i / n * 2 * Math.PI; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; }),
    poligono: (cx, cy, r, lados, n = 240, giro = -Math.PI / 2) => Array.from({ length: n }, (_, i) => {
      const u = i / n * lados, k = Math.floor(u), f = u - k;
      const a1 = giro + k / lados * 2 * Math.PI, a2 = giro + (k + 1) / lados * 2 * Math.PI;
      return [cx + lerp(Math.cos(a1), Math.cos(a2), f) * r, cy + lerp(Math.sin(a1), Math.sin(a2), f) * r];
    }),
    estrella: (cx, cy, r, puntas = 5, n = 240, interior = .45) => Array.from({ length: n }, (_, i) => {
      const u = i / n * puntas * 2, k = Math.floor(u), f = u - k;
      const rr = j => (j % 2 ? r * interior : r), a = j => -Math.PI / 2 + j / (puntas * 2) * 2 * Math.PI;
      return [cx + lerp(Math.cos(a(k)) * rr(k), Math.cos(a(k + 1)) * rr(k + 1), f), cy + lerp(Math.sin(a(k)) * rr(k), Math.sin(a(k + 1)) * rr(k + 1), f)];
    }),
    rectRedondo: (cx, cy, w, h, radio, n = 240) => {
      // recorre el borde por largo de arco: los puntos quedan parejos
      const r = Math.min(radio, w / 2, h / 2), rectos = [w - 2 * r, h - 2 * r], arco = Math.PI * r / 2;
      const tramos = [rectos[0], arco, rectos[1], arco, rectos[0], arco, rectos[1], arco];
      const total = tramos.reduce((a, b) => a + b, 0);
      const x0 = cx - w / 2, y0 = cy - h / 2;
      const esquinas = [[x0 + w - r, y0 + r, -Math.PI / 2], [x0 + w - r, y0 + h - r, 0], [x0 + r, y0 + h - r, Math.PI / 2], [x0 + r, y0 + r, Math.PI]];
      return Array.from({ length: n }, (_, i) => {
        let d = i / n * total, s = 0;
        while (d > tramos[s]) { d -= tramos[s]; s++; }
        const lado = s >> 1;
        if (s % 2 === 0) {
          const f = tramos[s] ? d / tramos[s] : 0;
          return [[x0 + r + f * rectos[0], y0], [x0 + w, y0 + r + f * rectos[1]], [x0 + w - r - f * rectos[0], y0 + h], [x0, y0 + h - r - f * rectos[1]]][lado];
        }
        const [ex, ey, a0] = esquinas[lado], a = a0 + (arco ? d / arco : 0) * Math.PI / 2;
        return [ex + Math.cos(a) * r, ey + Math.sin(a) * r];
      });
    },
  };
  function morph(A, B, k) { return A.map((p, i) => [lerp(p[0], B[i][0], k), lerp(p[1], B[i][1], k)]); }
  function trazar(ctx, puntos) {
    ctx.beginPath(); puntos.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath();
  }

  // ── texto hecho de partículas ──
  const cachePuntos = new Map();
  /** Dibuja el texto en un lienzo oculto y devuelve n puntos sobre las letras, centrados en (0,0). Determinista. */
  function puntosDeTexto(texto, fuente, n = 4000, semilla = 1) {
    const clave = texto + fuente + n + semilla;
    if (cachePuntos.has(clave)) return cachePuntos.get(clave);
    const c = document.createElement('canvas'); c.width = 2400; c.height = 600;
    const g = c.getContext('2d'); g.font = fuente; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#fff';
    g.fillText(texto, 1200, 300);
    const d = g.getImageData(0, 0, 2400, 600).data, llenos = [];
    for (let y = 0; y < 600; y += 2) for (let x = 0; x < 2400; x += 2) if (d[(y * 2400 + x) * 4 + 3] > 128) llenos.push([x - 1200, y - 300]);
    let s = semilla;
    const azar = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
    const out = Array.from({ length: n }, () => llenos[Math.floor(azar() * llenos.length)] || [0, 0]);
    cachePuntos.set(clave, out);
    return out;
  }
  function azar(semilla) { let s = semilla >>> 0; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }

  // ── motas: polvo que flota en el fondo para que ningún tramo quede quieto (función pura de t) ──
  // M.motas(ctx, t, { n: 26, color: '240,164,58', alfa: .35, tam: [2, 5], vel: [25, 60], semilla: 7 })
  // Cada mota tiene posición, dirección y velocidad fijas por semilla; cruza el cuadro y vuelve a entrar por el otro lado.
  function motas(ctx, t, { n = 26, color = '245,241,232', alfa = .3, tam = [2, 5], vel = [25, 60], semilla = 7, w = 1920, h = 1080 } = {}) {
    const a = azar(semilla);
    ctx.save();
    for (let i = 0; i < n; i++) {
      const x0 = a() * w, y0 = a() * h, ang = -Math.PI / 2 + (a() - .5) * 1.4, v = lerp(vel[0], vel[1], a());
      const s = lerp(tam[0], tam[1], a()), fase = a() * 6.283, m = 40;
      const x = ((x0 + Math.cos(ang) * v * t) % (w + 2 * m) + w + 2 * m) % (w + 2 * m) - m;
      const y = ((y0 + Math.sin(ang) * v * t) % (h + 2 * m) + h + 2 * m) % (h + 2 * m) - m;
      ctx.fillStyle = `rgba(${color},${alfa * (.55 + .45 * Math.sin(t * 1.3 + fase))})`;
      ctx.beginPath(); ctx.arc(x, y, s, 0, 6.283); ctx.fill();
    }
    ctx.restore();
  }

  return { clamp, lerp, pulsos, curva, tramo, escalon, resorte, forma, morph, trazar, puntosDeTexto, azar, motas };
})();
