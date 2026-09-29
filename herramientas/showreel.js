/* Showreel tipográfico VERTICAL (1080×1920, para reels): ocho escenas de un compás, cortadas a la
 * música, cada una con otra técnica de motion design (la receta de los tweets «showreel for …»):
 *   0 gancho: letras que golpean una por una          4 marquesinas: filas de texto en sentidos opuestos
 *   1 frases que entran por los lados, cámara que gira   5 ráfaga: dos frases de función a pantalla llena
 *   2 una forma que se transforma con una palabra        6 golpe: el logo con glitch (canales corridos)
 *   3 cubo 3D de alambre y una cifra real que se acerca  7 cierre limpio: logo, frase y dirección
 * Entre escenas, un barrido de color. Todo función pura del tiempo (grilla de pulsos de musica.py).
 *
 *   Showreel.video({ canvas, colores: { fondo, acento, acento2, texto }, logo: 'marca/x.png',
 *     nombre: ['Nota', 'Fácil'], gancho: ['¿DÓNDE', 'ANOTASTE', 'ESO?'], sub: 'una app de notas',
 *     lineas: [a, b, c], formas: [4 palabras], numero: { valor, etiqueta }, marquesina: 'NOTAFÁCIL',
 *     rafaga: [frase1, frase2], cierre: 'frase final', url: 'notafacil.example' })
 */
window.Showreel = (() => {
  const M = window.Movimiento, { clamp, lerp, escalon, tramo } = M;

  function video(cfg) {
    const cv = cfg.canvas, ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
    const P = M.pulsos(PULSOS.bpm, PULSOS.inicio), T = b => P.t(b), B = t => P.b(t);
    const C = cfg.colores, F = cfg.fuente || '"Segoe UI", system-ui, sans-serif';
    const LOGO = new Image(); LOGO.src = cfg.logo;
    const DUR = T(32) + .9;

    function tx(s, x, y, tam, peso, color, alinear = 'center') { ctx.font = `${peso} ${tam}px ${F}`; ctx.fillStyle = color; ctx.textAlign = alinear; ctx.textBaseline = 'middle'; ctx.fillText(s, x, y); }
    function ancho(s, tam, peso) { ctx.font = `${peso} ${tam}px ${F}`; return ctx.measureText(s).width; }
    // zona segura de los reels: nada más ancho que W − 200 (100 px de margen a cada lado; con 60 tocaba el borde)
    function ajustar(s, peso, max, tope) { max = Math.min(max, W - 200); let t = tope; while (t > 20 && ancho(s, t, peso) > max) t -= 4; return t; }
    function fondo(c) { ctx.fillStyle = c; ctx.fillRect(0, 0, W, H); }

    // 0 · gancho: cada letra entra grande y se asienta
    function gancho(u, t) {
      fondo(C.acento);
      const lineas = cfg.gancho, tam = Math.min(...lineas.map(l => ajustar(l, 900, W - 120, 260)));
      let n = 0;
      lineas.forEach((l, i) => {
        const y = H / 2 - (lineas.length - 1) * tam * .5 + i * tam * 1.0 - 120 * tramo(u, 2, 2.6, 'expo');
        let x = W / 2 - ancho(l, tam, 900) / 2;
        for (const ch of l) {
          const b0 = .1 + n * .09, k = escalon(t - T(b0), 3, .6); n++;
          const w = ancho(ch, tam, 900);
          if (t > T(b0)) { ctx.save(); ctx.translate(x + w / 2, y); ctx.scale(lerp(2.4, 1, k), lerp(2.4, 1, k)); ctx.globalAlpha = clamp(k * 2); tx(ch, 0, 0, tam, 900, C.fondo); ctx.restore(); }
          x += w;
        }
      });
      const k = escalon(t - T(2.2), 2.4, .8);
      if (t > T(2.2)) { ctx.globalAlpha = clamp(k * 1.5); tx(cfg.sub, W / 2, H / 2 + (lineas.length) * tam * .5 + 40 + 30 * (1 - k), 64, 700, C.fondo); ctx.globalAlpha = 1; }
    }
    // 1 · frases por los lados; al final la cámara gira y se aleja
    function frases(u, t) {
      fondo(C.fondo);
      const giro = tramo(u, 3, 4, 'expoIn');
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(-.18 * giro); ctx.scale(1 - .25 * giro, 1 - .25 * giro); ctx.translate(-W / 2, -H / 2);
      cfg.lineas.forEach((l, i) => {
        const b0 = 4 + i, k = escalon(t - T(b0), 2.2, .72); if (t < T(b0)) return;
        const tam = ajustar(l, 900, W - 120, 150), lado = i % 2 ? 1 : -1;
        tx(l, W / 2 + lado * (1 - k) * W, H / 2 - 260 + i * 260, tam, 900, [C.texto, C.acento, C.acento2][i % 3]);
      });
      ctx.restore();
    }
    // 2 · una forma que se transforma en cada pulso, con la palabra adentro
    function formas(u, t) {
      fondo(C.acento2);
      const cx = W / 2, cy = H / 2 - 80, r = 360;
      const figs = [M.forma.circulo(cx, cy, r), M.forma.rectRedondo(cx, cy, r * 1.7, r * 1.7, 90), M.forma.estrella(cx, cy, r * 1.15, 5, 240, .55), M.forma.poligono(cx, cy, r * 1.05, 6)];
      const i = clamp(Math.floor(u), 0, 3), k = tramo(u - i, 0, .45, 'expo');
      const pts = M.morph(figs[(i + 3) % 4], figs[i], i === 0 && u < 1 ? 1 : k);
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(u * .35); ctx.translate(-cx, -cy);
      ctx.fillStyle = C.fondo; M.trazar(ctx, pts); ctx.fill(); ctx.restore();
      const pal = cfg.formas[i], tam = ajustar(pal, 900, r * 1.5, 150), ke = escalon(t - T(8 + i), 3, .7);
      ctx.save(); ctx.translate(cx, cy); ctx.scale(.6 + .4 * ke, .6 + .4 * ke); tx(pal, 0, 0, tam, 900, C.acento2); ctx.restore();
    }
    // 3 · cubo de alambre (perspectiva a mano) y la cifra que llega desde el fondo
    function cubo(u, t) {
      fondo(C.fondo);
      const a = t * 1.1, b = t * .7, V = [];
      for (const x of [-1, 1]) for (const y of [-1, 1]) for (const z of [-1, 1]) {
        let X = x * Math.cos(a) - z * Math.sin(a), Z = x * Math.sin(a) + z * Math.cos(a), Y = y * Math.cos(b) - Z * Math.sin(b); Z = y * Math.sin(b) + Z * Math.cos(b);
        const k = 3.4 / (3.4 + Z); V.push([W / 2 + X * 330 * k, H / 2 - 120 + Y * 330 * k]);
      }
      ctx.strokeStyle = C.acento; ctx.lineWidth = 6; ctx.lineCap = 'round';
      for (let i = 0; i < 8; i++) for (let j = i + 1; j < 8; j++) { const d = (i ^ j); if (d === 1 || d === 2 || d === 4) { ctx.beginPath(); ctx.moveTo(...V[i]); ctx.lineTo(...V[j]); ctx.stroke(); } }
      const tq = Reproductor.cuadro(t), kk = tramo(tq, T(12.2), T(14.2), 'expo'), acerca = escalon(t - T(12.1), 1.6, .8);
      const valor = Math.round(cfg.numero.valor * kk).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      ctx.save(); ctx.translate(W / 2, H / 2 - 120); ctx.scale(.2 + .8 * acerca, .2 + .8 * acerca);
      tx(valor, 0, 0, ajustar(cfg.numero.valor.toLocaleString('es'), 900, W - 260, 230), 900, C.texto); ctx.restore();
      const ke = escalon(t - T(13), 2.2, .85); ctx.globalAlpha = clamp(ke * 1.5);
      tx(cfg.numero.etiqueta, W / 2, H / 2 + 330 + 30 * (1 - ke), ajustar(cfg.numero.etiqueta, 700, W - 140, 64), 700, C.acento); ctx.globalAlpha = 1;
    }
    // 4 · marquesinas: la misma palabra en filas que corren en sentidos opuestos, con la cámara inclinada
    function marquesina(u, t) {
      fondo(C.fondo);
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(-.21); ctx.translate(-W / 2, -H / 2);
      const s = cfg.marquesina + '  ·  ', tam = 190, w = ancho(s, tam, 900);
      for (let f = -3; f <= 12; f++) {
        const y = f * 190, dir = f % 2 ? 1 : -1, x0 = ((t * 420 * dir) % w + w) % w - w;
        const lleno = f === 4 || f === 5;
        for (let x = x0 - w; x < W + w * 2; x += w) {
          ctx.font = `900 ${tam}px ${F}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
          if (lleno) { ctx.fillStyle = f === 4 ? C.acento : C.acento2; ctx.fillText(s, x - 400, y); }
          else { ctx.strokeStyle = 'rgba(255,255,255,.22)'; ctx.lineWidth = 3; ctx.strokeText(s, x - 400, y); }
        }
      }
      ctx.restore();
    }
    // 5 · ráfaga: dos frases a pantalla llena, colores invertidos
    function rafaga(u, t) {
      const i = u < 2 ? 0 : 1, frase = cfg.rafaga[i];
      fondo(i ? C.texto : C.acento);
      const pals = frase.split(' '), lineas = [];
      let l = '';
      for (const p of pals) { const pr = l ? l + ' ' + p : p; if (ancho(pr, 130, 900) > W - 140 && l) { lineas.push(l); l = p; } else l = pr; }
      lineas.push(l);
      let n = 0;
      lineas.forEach((ln, j) => {
        const y = H / 2 - (lineas.length - 1) * 75 + j * 150;
        let x = W / 2 - ancho(ln, 130, 900) / 2;
        for (const p of ln.split(' ')) {
          const k = escalon(t - T(20 + i * 2) - n * .05, 2.6, .75); n++;
          ctx.globalAlpha = clamp(k * 2);
          tx(p, x + ancho(p, 130, 900) / 2, y + 60 * (1 - k), 130, 900, C.fondo);
          x += ancho(p + ' ', 130, 900);
        }
      });
      ctx.globalAlpha = 1;
      barras(t, C.fondo);
    }
    // barras de audio con la energía REAL de la canción (energia.js de pista.py --energia), no dibujadas a mano
    function barras(t, color) {
      const E = window.ENERGIA;
      if (!E) return;
      const f = clamp(t * E.fps, 0, E.cuadros - 1.001), i0 = Math.floor(f), a = f - i0;
      const v = k => { const c = j => parseInt(E.datos[(j * E.bandas + k)], 36) / 35; return lerp(c(i0), c(i0 + 1), a); };
      const n = E.bandas, paso = (W - 200) / n, base = 1470, alto = 260;
      ctx.fillStyle = color;
      for (let k = 0; k < n; k++) {
        const h = 10 + alto * v(k);
        ctx.beginPath(); ctx.roundRect(100 + k * paso + paso * .15, base - h, paso * .7, h, paso * .35); ctx.fill();
      }
    }
    // 6 y 7 · el logo con glitch en el golpe, después el cierre limpio
    let tintes = null;
    function tintar(color) {
      const c = document.createElement('canvas'); c.width = LOGO.naturalWidth; c.height = LOGO.naturalHeight;
      const g = c.getContext('2d'); g.drawImage(LOGO, 0, 0); g.globalCompositeOperation = 'source-in'; g.fillStyle = color; g.fillRect(0, 0, c.width, c.height); return c;
    }
    function logo(u, t) {
      fondo(C.fondo);
      if (!tintes && LOGO.complete) tintes = [tintar('#ff2a4f'), tintar('#28e0ff')];
      const d = t - T(24), k = escalon(d, 1.8, .66), g = Math.max(0, 1 - d / .55) * (d > 0), f = Math.round(Reproductor.cuadro(t) * 30);
      const asp = LOGO.naturalHeight / LOGO.naturalWidth || 1, ancho_ = Math.min(W - 160, 820, 480 / asp), alto = ancho_ * asp, x = W / 2 - ancho_ / 2 * (.8 + .2 * k), y = H / 2 - 260 - alto / 2 * (.8 + .2 * k);
      const w = ancho_ * (.8 + .2 * k), h = alto * (.8 + .2 * k);
      if (g > 0 && tintes) {
        const az = M.azar(f + 7);
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = .8; ctx.drawImage(tintes[0], x - 26 * g, y, w, h); ctx.drawImage(tintes[1], x + 26 * g, y, w, h);
        ctx.restore();
        for (let i = 0; i < 7; i++) {                 // franjas corridas
          const sy = az() * h, sh = 8 + az() * 50, dx = (az() - .5) * 120 * g;
          ctx.drawImage(LOGO, 0, sy / h * LOGO.naturalHeight, LOGO.naturalWidth, sh / h * LOGO.naturalHeight, x + dx, y + sy, w, sh);
        }
      } else if (LOGO.complete) ctx.drawImage(LOGO, x, y, w, h);
      const k2 = escalon(d - .5, 2.2, .82);
      if (cfg.nombre) {
        const tam = 150, w1 = ancho(cfg.nombre[0], tam, 800), w2 = ancho(cfg.nombre[1], tam, 800), x0 = W / 2 - (w1 + w2) / 2;
        ctx.globalAlpha = clamp(k2 * 1.5);
        tx(cfg.nombre[0], x0, H / 2 + 90 + 30 * (1 - k2), tam, 800, C.texto, 'left'); tx(cfg.nombre[1], x0 + w1, H / 2 + 90 + 30 * (1 - k2), tam, 800, C.acento, 'left');
      }
      const k3 = escalon(t - T(28), 2.2, .85); ctx.globalAlpha = clamp(k3 * 1.5);
      tx(cfg.cierre, W / 2, H / 2 + 250 + 24 * (1 - k3), ajustar(cfg.cierre, 500, W - 140, 56), 500, C.texto);
      if (cfg.url) {
        const k4 = escalon(t - T(29), 2.2, .82), wb = ancho(cfg.url, 60, 800) + 120; ctx.globalAlpha = clamp(k4 * 1.5);
        ctx.fillStyle = C.acento; ctx.beginPath(); ctx.roundRect(W / 2 - wb / 2, H / 2 + 360 + 24 * (1 - k4), wb, 124, 62); ctx.fill();
        tx(cfg.url, W / 2, H / 2 + 424 + 24 * (1 - k4), 60, 800, C.fondo);
      }
      ctx.globalAlpha = 1;
    }

    const ESCENAS = [gancho, frases, formas, cubo, marquesina, rafaga, logo, logo];
    const BARRIDOS = [C.fondo, C.acento2, C.fondo, C.acento, C.acento, C.fondo];
    function render(t) {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
      const b = B(t), e = clamp(Math.floor(b / 4), 0, 7);
      ESCENAS[e](b - e * 4, t);
      // barrido de color en el último cuarto de pulso de cada escena (no antes del golpe del logo)
      const u = b - e * 4;
      if (e < 5 && u > 3.72) { const k = M.curva.expoIn(clamp((u - 3.72) / .28)); ctx.fillStyle = BARRIDOS[e]; ctx.fillRect(0, H * (1 - k), W, H * k); }
      const neg = Math.max(1 - clamp(t / .25), clamp((t - (DUR - .6)) / .6));
      if (neg > 0) { ctx.globalAlpha = neg; ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
    }
    // energia.js es opcional (sin él no hay barras): se carga antes de arrancar para que la exportación lo tenga
    const cargar = src => new Promise(res => { const s = document.createElement('script'); s.src = src; s.onload = s.onerror = res; document.head.appendChild(s); });
    LOGO.decode().catch(() => {}).then(() => document.fonts.ready).then(() => cargar('energia.js')).then(() =>
      Reproductor.iniciar({ canvas: cv, render, duracion: DUR, audio: 'musica.wav', desenfoque: 4 }));
  }
  return { video };
})();
