/* Videos con la pantalla REAL del producto: capturas de verdad (herramientas/capturar_web.py) dentro de
 * una laptop y un teléfono dibujados en código, con cámara que hace zoom, scroll, cursor que hace clic,
 * cambios de página y textos. Cada video es un GUION de acciones en pulsos; este motor lo anima todo con
 * resortes (función pura del tiempo: se puede exportar cuadro a cuadro).
 *
 *   Pantalla.video({
 *     canvas, colores: { fondo1, fondo2, acento, texto, gris }, fuente,
 *     imagenes: { inicio: 'capturas/inicio.png', ... },
 *     dispositivos: { lap: { tipo: 'laptop', x: 410, y: 170, w: 1100 }, tel: { tipo: 'telefono', cx: 1480, cy: 560, h: 800 } },
 *     guion: [ [pulso, accion, ...argumentos], ... ],
 *     pantallaCompleta(t, api),   // opcional: lo que se dibuja encima sin cámara (títulos, logo final)
 *     duracion,                   // en pulsos
 *   })
 *
 * Acciones (coordenadas de página = píxeles de la captura; de mundo = el lienzo de 1920×1080 sin zoom):
 *   ['entra', disp, img]               el dispositivo aparece (sube con resorte) mostrando esa captura
 *   ['sale', disp]                     se va hacia abajo
 *   ['imagen', disp, img]              cambia de página (fundido corto)
 *   ['scroll', disp, y]                desplaza la página hasta y
 *   ['mueve', disp, {x, y, w} | {cx, cy, h}]   cambia de lugar o de tamaño
 *   ['zoom', disp, x0, y0, x1, y1, margen?]    la cámara encuadra esa zona de la página
 *   ['general'] | ['camara', cx, cy, z]        vuelve al plano completo | cámara libre
 *   ['cursor', disp, x, y]             el cursor viaja a ese punto de la página
 *   ['clic']                           clic donde esté el cursor (anillo + pulsación)
 *   ['texto', 'frase' | null]          frase grande abajo (hasta la próxima)
 *   ['nota', disp, x, y, 'frase' | null]      globo que señala un punto de la página
 *   ['ocultarCursor']
 */
window.Pantalla = (() => {
  const M = window.Movimiento, { clamp, lerp, escalon, resorte, tramo } = M;

  function video(cfg) {
    const cv = cfg.canvas, ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
    const P = M.pulsos(PULSOS.bpm, PULSOS.inicio), T = b => P.t(b);
    const C = cfg.colores, F = cfg.fuente || '"Segoe UI Variable Display", "Segoe UI", system-ui, sans-serif';
    const IMG = {};
    for (const [k, src] of Object.entries(cfg.imagenes)) { IMG[k] = new Image(); IMG[k].src = src; }

    // ── geometría ──
    const pantallaDe = d => d.tipo === 'laptop'
      ? { x: d.x, y: d.y, w: d.w, h: d.w * .625 }
      : (() => { const h = d.h - 28, w = h * 390 / 844; return { x: d.cx - w / 2, y: d.cy - h / 2, w, h }; })();
    const escalaDe = (d, img) => pantallaDe(d).w / (IMG[img]?.naturalWidth || (d.tipo === 'laptop' ? 1440 : 1170));
    const aMundo = (d, img, scroll, px, py) => { const s = pantallaDe(d), k = escalaDe(d, img); return [s.x + px * k, s.y + (py - scroll) * k]; };

    const api = { ctx, T, P, M, C, F, W, H, IMG };
    // el guion se compila cuando cargaron las capturas: los zooms necesitan su ancho real
    Promise.all(Object.values(IMG).map(i => i.decode().catch(() => {}))).then(() => document.fonts.ready).then(arrancar);
    return api;

    function arrancar() {
    // ── el guion se convierte en listas de cambios para resortes ──
    const G = [...cfg.guion].sort((a, b) => a[0] - b[0]);
    const est = {}, pistas = {};
    for (const [n, d] of Object.entries(cfg.dispositivos)) {
      est[n] = { ...d, scroll: 0, img: null, visible: 0 };
      pistas[n] = { geo: {}, scroll: [], img: [], vis: [] };
      for (const k of ['x', 'y', 'w', 'cx', 'cy', 'h']) if (k in d) pistas[n].geo[k] = [];
    }
    let cam = [W / 2, H / 2, 1], cursorEn = null;
    const camP = [[], [], []], curP = [[], []], clics = [], textos = [], notas = [], cursorVis = [];
    const empuja = (lista, tb, desde, hasta) => lista.push([tb, desde, hasta]);
    for (const [b, acc, ...a] of G) {
      const tb = T(b);
      if (acc === 'entra' || acc === 'sale') {
        const e = est[a[0]]; pistas[a[0]].vis.push([tb, acc === 'entra' ? 1 : 0]);
        if (acc === 'entra') { e.img = a[1]; pistas[a[0]].img.push([tb, a[1]]); }
      } else if (acc === 'imagen') { est[a[0]].img = a[1]; pistas[a[0]].img.push([tb, a[1]]); empuja(pistas[a[0]].scroll, tb, est[a[0]].scroll, 0); est[a[0]].scroll = 0; }
      else if (acc === 'scroll') { const e = est[a[0]]; empuja(pistas[a[0]].scroll, tb, e.scroll, a[1]); e.scroll = a[1]; }
      else if (acc === 'mueve') { const e = est[a[0]]; for (const [k, v] of Object.entries(a[1])) { empuja(pistas[a[0]].geo[k], tb, e[k], v); e[k] = v; } }
      else if (acc === 'zoom' || acc === 'general' || acc === 'camara') {
        let nuevo;
        if (acc === 'general') nuevo = [W / 2, H / 2, 1];
        else if (acc === 'camara') nuevo = a;
        else {
          const e = est[a[0]], [x0, y0] = aMundo(e, e.img, e.scroll, a[1], a[2]), [x1, y1] = aMundo(e, e.img, e.scroll, a[3], a[4]), m = a[5] || 1.3;
          nuevo = [(x0 + x1) / 2, (y0 + y1) / 2, Math.min(W / ((x1 - x0) * m), H / ((y1 - y0) * m), 3.2)];
        }
        nuevo.forEach((v, i) => empuja(camP[i], tb, i === 2 ? Math.log(cam[i]) : cam[i], i === 2 ? Math.log(v) : v)); cam = nuevo;
      } else if (acc === 'cursor') {
        const e = est[a[0]], p = aMundo(e, e.img, e.scroll, a[1], a[2]);
        if (!cursorEn) { cursorEn = [p[0] + 260, p[1] + 380]; cursorVis.push([tb - .5, 1]); empuja(curP[0], tb - .6, cursorEn[0], cursorEn[0]); empuja(curP[1], tb - .6, cursorEn[1], cursorEn[1]); }
        empuja(curP[0], tb, cursorEn[0], p[0]); empuja(curP[1], tb, cursorEn[1], p[1]); cursorEn = p;
      } else if (acc === 'clic') clics.push(tb);
      else if (acc === 'ocultarCursor') { cursorVis.push([tb, 0]); cursorEn = null; }
      else if (acc === 'texto') textos.push([tb, a[0]]);
      else if (acc === 'nota') notas.push([tb, a[0], a[1], a[2], a[3]]);
    }
    const ultimo = (lista, t, def) => { let v = def, tv = -1e9; for (const [tb, x] of lista) if (t >= tb) { v = x; tv = tb; } return [v, tv]; };

    // estado de un dispositivo en t
    function estado(n, t) {
      const d = cfg.dispositivos[n], p = pistas[n], s = { tipo: d.tipo };
      for (const k of Object.keys(p.geo)) s[k] = p.geo[k].length ? resorte(t, p.geo[k], { hz: 1.1, amort: .92 }) : d[k];
      s.scroll = p.scroll.length ? resorte(t, p.scroll, { hz: .9, amort: 1 }) : 0;
      const [vis, tv] = ultimo(p.vis, t, 0);
      s.aparece = vis ? escalon(t - tv, 1.6, .78) : 1 - escalon(t - tv, 1.8, 1);
      if (tv < -1e8) s.aparece = 0;
      const imgs = p.img.filter(([tb]) => t >= tb);
      s.img = imgs.length ? imgs[imgs.length - 1][1] : null;
      s.imgPrev = imgs.length > 1 ? imgs[imgs.length - 2][1] : null;
      s.fundido = imgs.length > 1 ? clamp((t - imgs[imgs.length - 1][0]) / .3) : 1;
      return s;
    }

    // ── dibujo de los dispositivos ──
    function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
    function contenido(s, scr, radio) {
      ctx.save(); rr(scr.x, scr.y, scr.w, scr.h, radio); ctx.clip();
      ctx.fillStyle = '#fff'; ctx.fillRect(scr.x, scr.y, scr.w, scr.h);
      for (const [img, a] of [[s.imgPrev, 1], [s.img, s.fundido]]) {
        const im = IMG[img]; if (!im || !im.complete || a <= 0) continue;
        const k = scr.w / im.naturalWidth;
        ctx.globalAlpha = a;
        ctx.drawImage(im, 0, s.scroll, im.naturalWidth, scr.h / k, scr.x, scr.y, scr.w, scr.h);
      }
      ctx.restore();
    }
    function laptop(s) {
      const scr = pantallaDe(s);
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = 80; ctx.shadowOffsetY = 40;
      ctx.fillStyle = '#0c0d10'; rr(scr.x - 20, scr.y - 20, scr.w + 40, scr.h + 40, 26); ctx.fill();
      ctx.restore();
      ctx.fillStyle = '#2a2d33'; ctx.beginPath(); ctx.arc(scr.x + scr.w / 2, scr.y - 10, 3.5, 0, 7); ctx.fill();   // cámara
      contenido(s, scr, 6);
      const b = scr.y + scr.h + 20, g = ctx.createLinearGradient(0, b, 0, b + 30);
      g.addColorStop(0, '#c9ccd2'); g.addColorStop(1, '#8e9199');
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(scr.x - 110, b); ctx.lineTo(scr.x + scr.w + 110, b);
      ctx.lineTo(scr.x + scr.w + 70, b + 28); ctx.lineTo(scr.x - 70, b + 28); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#a3a6ad'; rr(scr.x + scr.w / 2 - 90, b, 180, 10, 5); ctx.fill();
    }
    function telefono(s) {
      const scr = pantallaDe(s), bx = scr.x - 14, by = scr.y - 14, bw = scr.w + 28, bh = scr.h + 28;
      ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = 70; ctx.shadowOffsetY = 36;
      ctx.fillStyle = '#0c0d10'; rr(bx, by, bw, bh, bw * .16); ctx.fill(); ctx.restore();
      ctx.strokeStyle = '#3a3d44'; ctx.lineWidth = 3; rr(bx + 1.5, by + 1.5, bw - 3, bh - 3, bw * .16); ctx.stroke();
      contenido(s, scr, scr.w * .13);
      ctx.fillStyle = '#000'; rr(scr.x + scr.w / 2 - scr.w * .16, scr.y + 12, scr.w * .32, scr.w * .085, scr.w * .05); ctx.fill();   // isla
    }
    function dispositivo(n, t) {
      const s = estado(n, t); if (s.aparece <= .001) return s;
      ctx.save();
      const scr = pantallaDe(s), cx = scr.x + scr.w / 2, cy = scr.y + scr.h / 2;
      ctx.globalAlpha = clamp(s.aparece * 1.4);
      ctx.translate(cx, cy + (1 - s.aparece) * 700); ctx.scale(.9 + .1 * s.aparece, .9 + .1 * s.aparece); ctx.translate(-cx, -cy);
      (s.tipo === 'laptop' ? laptop : telefono)(s);
      ctx.restore();
      return s;
    }

    // ── cursor, notas y textos ──
    function cursor(t, z) {
      const [vis, tv] = ultimo(cursorVis, t, 0), a = vis ? clamp((t - tv) / .25) : 1 - clamp((t - tv) / .25);
      if (a <= 0 || tv < -1e8 || !curP[0].length) return;
      const x = resorte(t, curP[0], { hz: 1.5, amort: .9 }), y = resorte(t, curP[1], { hz: 1.5, amort: .9 });
      let esc = 1;
      for (const tc of clics) {
        const d = t - tc;
        if (d > -.08 && d < .55) {
          esc = Math.min(esc, 1 - .2 * Math.exp(-Math.abs(d) * 14));
          if (d > 0) { ctx.save(); ctx.globalAlpha = a * (1 - d / .55); ctx.strokeStyle = C.acento; ctx.lineWidth = 4 / z; ctx.beginPath(); ctx.arc(x, y, (14 + d * 120) / z, 0, 7); ctx.stroke(); ctx.restore(); }
        }
      }
      ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(esc * 1.6 / z, esc * 1.6 / z);
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 30); ctx.lineTo(7.5, 23); ctx.lineTo(13, 35); ctx.lineTo(18, 33); ctx.lineTo(12.5, 21.5); ctx.lineTo(22, 21.5); ctx.closePath();
      ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.stroke();
      ctx.restore();
    }
    function nota(t, z, estados) {
      const vigentes = notas.filter(n => t >= n[0]); if (!vigentes.length) return;
      const [tb, d, px, py, s] = vigentes[vigentes.length - 1]; if (!s) return;
      const sig = notas.find(n => n[0] > tb), fin = sig ? sig[0] : 1e9;
      const a = Math.min(clamp((t - tb - .15) / .25), clamp((fin - t) / .2)); if (a <= 0) return;
      const e = estados[d], [x, y] = aMundo(e, e.img, e.scroll, px, py), k = escalon(t - tb - .15, 2.4, .75);
      ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(1 / z, 1 / z);
      ctx.fillStyle = C.acento; ctx.beginPath(); ctx.arc(0, 0, 10, 0, 7); ctx.fill();
      ctx.strokeStyle = C.acento; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 0, 18 + 6 * Math.sin(t * 5), 0, 7); ctx.stroke();
      ctx.font = `700 36px ${F}`; const w = ctx.measureText(s).width + 48;
      const bx = 34, by = -96 * k;
      ctx.beginPath(); ctx.moveTo(8, -8); ctx.lineTo(bx, by + 30); ctx.stroke();
      ctx.fillStyle = C.acento; rr(bx, by, w, 62, 31); ctx.fill();
      ctx.fillStyle = C.sobreAcento || '#fff'; ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.fillText(s, bx + 24, by + 32);
      ctx.restore();
    }
    function texto(t) {
      const vigentes = textos.filter(x => t >= x[0]); if (!vigentes.length) return;
      const [tb, s] = vigentes[vigentes.length - 1]; if (!s) return;
      const sig = textos.find(x => x[0] > tb), fin = sig ? sig[0] : 1e9;
      const k = escalon(t - tb, 2.3, .82), a = Math.min(clamp(k * 1.6), clamp((fin - t) / .18));
      ctx.save(); ctx.globalAlpha = a;
      ctx.font = `700 50px ${F}`; const w = Math.min(1700, ctx.measureText(s).width + 90), y = 950 + 30 * (1 - k);
      ctx.fillStyle = 'rgba(8,10,16,.82)'; rr(W / 2 - w / 2, y - 48, w, 96, 48); ctx.fill();
      ctx.fillStyle = C.texto; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, W / 2, y + 2, 1620);
      ctx.restore();
    }

    const DUR = T(cfg.duracion) + .9;
    function render(t) {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
      const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, C.fondo1); g.addColorStop(1, C.fondo2);
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      const cx = camP[0].length ? resorte(t, camP[0], { hz: .8, amort: .95 }) : W / 2;
      const cy = camP[1].length ? resorte(t, camP[1], { hz: .8, amort: .95 }) : H / 2;
      const z = camP[2].length ? Math.exp(resorte(t, camP[2], { hz: .8, amort: .95 })) : 1;
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-cx, -cy);
      const estados = {};
      for (const n of Object.keys(cfg.dispositivos)) estados[n] = dispositivo(n, t);
      nota(t, z, estados); cursor(t, z);
      ctx.restore();
      texto(t);
      if (cfg.pantallaCompleta) { ctx.save(); cfg.pantallaCompleta(t, api); ctx.restore(); }
      const neg = Math.max(1 - clamp(t / .4), clamp((t - (DUR - .7)) / .7));
      if (neg > 0) { ctx.globalAlpha = neg; ctx.fillStyle = C.fondo1; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
    }
    Reproductor.iniciar({ canvas: cv, render, duracion: DUR, audio: 'musica.wav', desenfoque: 4 });
    }
  }

  // Títulos grandes de pantalla completa (intro y cierre), palabra por palabra.
  function titular(api, t, a, b, lineas, { y = 470, tam = 96, centrado = true, color, acento } = {}) {
    const { ctx, T, M, C, F, W } = api, { clamp, escalon, tramo } = M;
    if (t < T(a) || t > T(b)) return;
    const salida = tramo(t, T(b) - .3, T(b), 'expoIn');
    ctx.save(); ctx.translate(0, -30 * salida);
    ctx.font = `800 ${tam}px ${F}`; ctx.textBaseline = 'middle';
    let n = 0;
    lineas.forEach((l, i) => {
      const pals = l.split(' '), anchos = pals.map(p => ctx.measureText(p.replace('*', '') + ' ').width);
      let x = centrado ? W / 2 - (anchos.reduce((s, v) => s + v, 0) - ctx.measureText(' ').width) / 2 : 120;
      pals.forEach((p, j) => {
        const k = escalon(t - T(a) - .08 - n * .07, 2.3, .8); n++;
        ctx.globalAlpha = (1 - salida) * clamp(k * 1.6);
        ctx.fillStyle = p.startsWith('*') ? (acento || C.acento) : (color || C.texto); ctx.textAlign = 'left';
        ctx.fillText(p.replace('*', ''), x, y + i * tam * 1.12 + 44 * (1 - k));
        x += anchos[j];
      });
    });
    ctx.restore();
  }

  return { video, titular };
})();
