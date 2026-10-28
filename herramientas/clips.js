/* Clips reales dentro de una página de `render(t)` (técnica 27: material real con motion graphics encima).
 *
 *   await Clips.cargar(base, {chaqueta: 'chaqueta.mp4', tel1: 'chaqueta.mp4', ...})
 *       carga cada clip como blob (el servidor de Python no deja saltar dentro de un video servido) en su propio
 *       <video>; dos nombres con el mismo archivo son dos <video> (el mismo clip en dos lugares a la vez).
 *   Clips.antes(usos)       → async antes(t) para Reproductor.iniciar: lleva cada clip que se ve en t al cuadro
 *       exacto y espera `seeked`. `usos(t)` devuelve [[nombre, segundo del clip], ...].
 *   Clips.vivo(usos, t)     al mirar en vivo: corrige la posición sólo si se fue más de 0,12 s.
 *   Clips.dibujar(ctx, nombre, x, y, w, h, {zoom, cx, cy}) dibuja el clip cubriendo el rectángulo (como
 *       object-fit: cover), con zoom y centro (cx, cy de 0 a 1 sobre el clip).
 *
 * Los clips tienen que venir todo intra (`ffmpeg -g 1`) y a fps constante: así `currentTime` cae en el cuadro pedido.
 * Método de `17-archivo/revolucion-industrial` (que lo tomó de @twoclipping), sacado acá para reusarlo.
 */
window.Clips = (() => {
  const vids = {};
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

  async function cargar(base, lista) {
    const blobs = {};
    for (const [nombre, archivo] of Object.entries(lista)) {
      if (!blobs[archivo]) {
        const r = await fetch(base + archivo);
        if (!r.ok) throw new Error('falta el clip ' + archivo + ' (correr preparar.py)');
        blobs[archivo] = URL.createObjectURL(await r.blob());
      }
      const v = document.createElement('video');
      v.muted = true; v.preload = 'auto'; v.playsInline = true; v.src = blobs[archivo];
      await new Promise(ok => v.addEventListener('loadeddata', ok, { once: true }));
      vids[nombre] = v;
    }
    return vids;
  }

  // segundo del clip → el centro de su cuadro (30 fps), dentro del clip
  const alCuadro = (v, x, fps) => (Math.floor(clamp(x, 0, v.duration - 1 / fps) * fps) + .5) / fps;

  function antes(usos, fps = 30) {
    return async t => {
      for (const [n, x] of usos(t)) {
        const v = vids[n], c = alCuadro(v, x, fps);
        if (Math.abs(v.currentTime - c) < 1e-3) continue;
        // `seeked` puede llegar antes de que el cuadro nuevo esté listo para drawImage (en Chrome sin ventana, el primer
        // salto de un clip dio otro cuadro según el orden: determinismo.py): después de `seeked`, dos cuadros
        // de animación
        await new Promise(ok => { v.addEventListener('seeked', ok, { once: true }); v.currentTime = c; });
        await new Promise(ok => requestAnimationFrame(() => requestAnimationFrame(ok)));
      }
    };
  }

  function vivo(usos, t, fps = 30) {
    for (const [n, x] of usos(t)) {
      const v = vids[n], c = alCuadro(v, x, fps);
      if (Math.abs(v.currentTime - c) > .12 && !v.seeking) v.currentTime = c;
    }
  }

  function dibujar(ctx, n, x, y, w, h, { zoom = 1, cx = .5, cy = .5 } = {}) {
    const v = vids[n], vw = v.videoWidth, vh = v.videoHeight;
    const k = Math.max(w / vw, h / vh) * zoom;                  // cubrir el rectángulo y acercar
    const sw = w / k, sh = h / k;                               // lo que se ve del clip, en sus píxeles
    const sx = clamp(cx * vw - sw / 2, 0, vw - sw), sy = clamp(cy * vh - sh / 2, 0, vh - sh);
    ctx.drawImage(v, sx, sy, sw, sh, x, y, w, h);
  }

  // Dibuja una vez cada fuente que va a usar la página antes de arrancar: la primera vez que el lienzo pinta un peso de
  // una fuente del sistema puede salir con otra (determinismo.py dio FALLA justo en el primer cuadro con texto).
  async function calentarFuentes(fuentes) {
    await Promise.all(fuentes.map(f => document.fonts.load(f).catch(() => null)));
    const g = document.createElement('canvas').getContext('2d');
    for (const f of fuentes) { g.font = f; g.fillText('Áa¿?¡!0123', 0, 50); }
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  }

  return { cargar, antes, vivo, dibujar, calentarFuentes, get videos() { return vids; } };
})();
