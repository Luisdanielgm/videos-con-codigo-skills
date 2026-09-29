/* Reproductor compartido de los videos del proyecto.
 *
 *   Reproductor.iniciar({ canvas, render, duracion, audio })
 *     canvas   : <canvas> de 1920×1080 donde se dibuja el cuadro final.
 *     render   : función render(t) que dibuja el instante t (segundos). Debe ser determinista:
 *                el mismo t siempre da el mismo cuadro (así se puede exportar y revisar).
 *     duracion : segundos totales.
 *     audio    : ruta de la narración (opcional), p. ej. 'narracion.wav'.
 *     desenfoque: subcuadros por cuadro al exportar (opcional, p. ej. 6): cada cuadro se dibuja varias
 *                veces con desfases mínimos y se promedia → desenfoque de movimiento como de cámara.
 *     antes    : async antes(t) (opcional): se espera antes de dibujar cada cuadro al exportar o capturar,
 *                p. ej. para llevar un <video> al cuadro exacto y esperar `seeked` (técnica 17).
 *
 *   Reproductor.cuadro(t)  el instante del cuadro que se dibuja (igual en todos sus subcuadros): usarlo para
 *     cifras que cuentan y azares por cuadro, nunca Math.round(t * 30) / 30.
 *
 *   Reproductor.subtitulos(ctx, t, TIEMPOS, colores)  dibuja la frase narrada en el instante t.
 *     colores (opcional): color del texto por personaje, p. ej. { visitante: '#ffd98a' } (usa `quien` de tiempos.js).
 *
 * Modos por URL:
 *   ?exportar          dibuja cuadro a cuadro (30 fps) y lo manda al servidor → render/<video>.mp4
 *   ?capturas=3,40.5   guarda esos instantes en render/capturas/<video>_<t>.jpg
 *   &fps=60            cuadros por segundo al exportar (30 por defecto; 60 = nivel de estudio)
 *   &sub=4             subcuadros de desenfoque (pisa el `desenfoque` del video; con 60 fps, 4 alcanzan)
 *   Con navegador.py: VIDEOS_PARAMS="fps=60&sub=4".
 */
window.Reproductor = (() => {
  const Q = new URLSearchParams(location.search);
  const FPS = Math.max(1, Number(Q.get('fps')) || 30);

  // Parte una frase larga en trozos de lectura cómoda.
  function trozos(texto, max = 80) {
    const partes = texto.split(/(?<=[.:;?!,])\s+/);
    const out = [];
    for (const p of partes) {
      if (out.length && (out[out.length - 1] + ' ' + p).length <= max) out[out.length - 1] += ' ' + p;
      else out.push(p);
    }
    return out;
  }
  const cache = new Map();

  function subtitulos(ctx, t, TIEMPOS, colores = {}) {
    for (const id of TIEMPOS.orden) {
      const s = TIEMPOS.seg[id];
      if (t < s.inicio - .1 || t > s.inicio + s.dur + .25) continue;
      if (!cache.has(id)) cache.set(id, trozos(s.texto));
      const ts = cache.get(id), total = ts.reduce((a, x) => a + x.length, 0);
      let a = s.inicio, i = 0;
      for (; i < ts.length; i++) {
        const b = a + s.dur * ts[i].length / total;
        if (t < b || i === ts.length - 1) break;
        a = b;
      }
      const linea = ts[i];
      ctx.save();
      ctx.font = '500 38px system-ui, "Segoe UI", sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const w = Math.min(1760, ctx.measureText(linea).width + 64);
      ctx.fillStyle = 'rgba(0,0,0,.72)';
      ctx.beginPath(); ctx.roundRect(960 - w / 2, 978, w, 64, 14); ctx.fill();
      ctx.fillStyle = colores[s.quien] || '#f2f5fa';
      ctx.fillText(linea, 960, 1011, 1700);
      ctx.restore();
      return;
    }
  }

  function rutaVideo() {
    return location.pathname.replace(/^\//, '').replace(/\/[^/]*\.html$/, '').replace(/\/$/, '');
  }

  // Un envío que falla se reintenta; si falla 5 veces seguidas, el error llega a la consola.
  async function enviar(url, body) {
    for (let i = 0; ; i++) {
      try {
        const r = await fetch(url, { method: 'POST', body });
        if (r.ok) return r;
        throw new Error(`HTTP ${r.status}`);
      } catch (e) {
        if (i >= 4) throw new Error(`no se pudo enviar ${url}: ${e.message}`);
        await new Promise(r => setTimeout(r, 300 * (i + 1)));
      }
    }
  }

  // Promedia `sub` subcuadros repartidos en medio cuadro (obturador de 180°): desenfoque de movimiento.
  let acumulado = null, enCuadro = null;
  function dibujarCuadro(canvas, render, t, sub) {
    if (sub <= 1) { render(t); return; }
    if (!acumulado) { acumulado = document.createElement('canvas'); acumulado.width = canvas.width; acumulado.height = canvas.height; }
    const a = acumulado.getContext('2d');
    enCuadro = t;
    for (let k = 0; k < sub; k++) {
      render(t + (k / sub - .25) * (.5 / FPS));
      a.globalAlpha = 1 / (k + 1); a.drawImage(canvas, 0, 0);     // promedio acumulado
    }
    enCuadro = null;
    a.globalAlpha = 1;
    const c = canvas.getContext('2d'); c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.drawImage(acumulado, 0, 0); c.restore();
  }

  async function exportar(canvas, render, duracion, sub = 1, antes = null) {
    const video = rutaVideo();
    await enviar(`/export/inicio?video=${encodeURIComponent(video)}&fps=${FPS}`);
    const n = Math.ceil(duracion * FPS);
    for (let f = 0; f <= n; f++) {
      if (antes) await antes(f / FPS);
      dibujarCuadro(canvas, render, f / FPS, sub);
      const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', .92));
      await enviar('/export/cuadro', blob);
      if (f % FPS === 0) document.title = `exportando ${Math.round(f / n * 100)}%`;
    }
    const r = await (await enviar('/export/fin')).json();
    document.title = r.ok ? `listo: ${r.salida}` : 'error al exportar';
    window.EXPORT_RESULTADO = r;
  }

  async function capturas(canvas, render, lista, sub = 1, antes = null) {
    const base = rutaVideo().replace(/\//g, '_');   // la técnica va en el nombre
    for (const t of lista) {
      if (antes) await antes(t);
      dibujarCuadro(canvas, render, t, sub);
      const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', .9));
      await fetch(`/captura?nombre=${base}_${String(t).replace('.', '-')}`, { method: 'POST', body: blob });
    }
    await fetch('/capturas/fin', { method: 'POST', body: JSON.stringify({ n: lista.length }) });
    document.title = `capturas listas (${lista.length})`;
    window.CAPTURAS_LISTAS = true;
  }

  function interfaz() {
    const css = document.createElement('style');
    css.textContent = `
      #rp-ui { position: fixed; left: 0; right: 0; bottom: 0; display: flex; gap: 10px; align-items: center;
        padding: 10px 16px; background: linear-gradient(transparent, rgba(0,0,0,.8)); color: #cfd6e4;
        font: 14px system-ui, sans-serif; opacity: 0; transition: opacity .3s; z-index: 5; }
      body:hover #rp-ui { opacity: 1; }
      #rp-ui button, #rp-grande { background: #1d2636; color: #e8ecf4; border: 1px solid #34425c;
        border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 14px; }
      #rp-ui input { flex: 1; }
      #rp-t { font-variant-numeric: tabular-nums; min-width: 110px; text-align: right; }
      #rp-grande { position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%); font-size: 26px;
        padding: 18px 36px; border-radius: 14px; z-index: 6; }`;
    document.head.appendChild(css);
    const ui = document.createElement('div');
    ui.id = 'rp-ui';
    ui.innerHTML = `<button id="rp-play">▶ Reproducir</button><input id="rp-barra" type="range" min="0" max="1000" value="0">
      <span id="rp-t">0:00</span><button id="rp-grabar" title="Graba en tiempo real a .webm">⏺ Grabar</button>`;
    document.body.appendChild(ui);
    const grande = document.createElement('button');
    grande.id = 'rp-grande'; grande.textContent = '▶ Reproducir';
    document.body.appendChild(grande);
    return { ui, grande };
  }

  function iniciar({ canvas, render, duracion, audio, desenfoque = 1, antes = null }) {
    const q = Q;
    if (q.has('sub')) desenfoque = Math.max(1, Number(q.get('sub')) || 1);
    if (q.has('exportar')) return exportar(canvas, render, duracion, desenfoque, antes);
    if (q.has('capturas')) return capturas(canvas, render, q.get('capturas').split(',').map(Number), desenfoque, antes);

    const { grande } = interfaz();
    const $ = id => document.getElementById(id);
    const snd = audio ? new Audio(audio) : null;
    let t = 0, playing = false, last = performance.now(), rec = null;
    const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

    function play(on) {
      playing = on;
      grande.style.display = 'none';
      $('rp-play').textContent = on ? '⏸ Pausa' : '▶ Seguir';
      if (snd) { if (on) { snd.currentTime = t; snd.play().catch(() => {}); } else snd.pause(); }
    }
    function ir(s) { t = Math.max(0, Math.min(duracion, s)); if (snd) snd.currentTime = t; }

    function cuadro(now) {
      const dt = Math.min(.1, (now - last) / 1000); last = now;
      if (playing) {
        if (snd && !snd.paused && !snd.ended) t = snd.currentTime; else t += dt;
        if (t >= duracion) {
          t = duracion; play(false); $('rp-play').textContent = '▶ Repetir';
          if (rec) { rec.stop(); rec = null; }
        }
      }
      render(t);
      $('rp-barra').value = Math.round(t / duracion * 1000);
      $('rp-t').textContent = `${mmss(t)} / ${mmss(duracion)}`;
      requestAnimationFrame(cuadro);
    }
    grande.onclick = () => play(true);
    $('rp-play').onclick = () => { if (t >= duracion) ir(0); play(!playing); };
    $('rp-barra').oninput = e => ir(e.target.value / 1000 * duracion);
    $('rp-grabar').onclick = () => {
      const stream = canvas.captureStream(FPS);
      if (snd) {
        const ac = new AudioContext(), src = ac.createMediaElementSource(snd), dst = ac.createMediaStreamDestination();
        src.connect(dst); src.connect(ac.destination);
        dst.stream.getAudioTracks().forEach(tr => stream.addTrack(tr));
      }
      const partes = [];
      rec = new MediaRecorder(stream, { mimeType: 'video/webm', videoBitsPerSecond: 12e6 });
      rec.ondataavailable = e => partes.push(e.data);
      rec.onstop = () => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob(partes, { type: 'video/webm' }));
        a.download = rutaVideo().split('/').pop() + '.webm'; a.click();
      };
      ir(0); play(true); rec.start();
    };
    window.seek = s => { play(false); ir(s); render(t); };
    requestAnimationFrame(cuadro);
  }

  // Ayudantes para ubicar la animación relativa a la narración (tiempos.js).
  function ayudantes(TI) {
    const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
    const lerp = (a, b, k) => a + (b - a) * k;
    const seg = (t, a, b) => clamp((t - a) / (b - a));
    const ease = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
    const A = id => TI.seg[id].inicio;                     // empieza la frase
    const D = id => TI.seg[id].dur;                        // dura la frase
    const F = (id, f) => A(id) + f * D(id);                // fracción f de la frase
    const P = (t, id, f0, f1) => ease(seg(t, F(id, f0), F(id, f1)));
    const SIG = id => { const i = TI.orden.indexOf(id); return i < TI.orden.length - 1 ? A(TI.orden[i + 1]) : TI.total; };
    const vis = (t, desde, hasta) => Math.min(seg(t, A(desde) - .5, A(desde)), 1 - seg(t, SIG(hasta) - .4, SIG(hasta)));
    return { clamp, lerp, seg, ease, A, D, F, P, SIG, vis };
  }

  // Instante del CUADRO que se está dibujando (el mismo en todos sus subcuadros). Para lo que no puede cambiar a
  // mitad de cuadro: una cifra que cuenta, un azar por cuadro. Redondear t a 1/30 no alcanza: a 60 fps los
  // subcuadros de los cuadros impares caen a los dos lados del redondeo y la cifra sale doble.
  const cuadro = t => enCuadro ?? Math.round(t * FPS) / FPS;

  return { iniciar, subtitulos, ayudantes, cuadro, dibujarCuadro };
})();
