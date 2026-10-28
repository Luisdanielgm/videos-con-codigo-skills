/* Vidrio: vidrio líquido sobre la escena de atrás, en WebGL2. Función pura de sus parámetros (y del fondo):
 * para animarlo, mueve las formas con t desde afuera.
 *
 *   Vidrio.dibujar(ctx, fondo, { formas: [{ x, y, w, h, radio }], ... })
 *     fondo  : <canvas> con la escena de atrás (puede ser el mismo ctx.canvas: se copia a una textura antes).
 *     formas : hasta 6 rectángulos redondeados (x, y = esquina sup. izq., en px); se funden entre sí con un
 *              mínimo suave de ancho `fusion` (px): dos paneles que se acercan se unen como líquido.
 *   Opciones (valores por omisión): bisel 70 (px de borde curvo), refraccion 55 (px que se corre la imagen en el
 *     borde), dispersion .25 (diferencia entre los tres índices: R lee menos corrido, B más → arcoíris en el
 *     borde), esmerilado 0 (px de desenfoque adentro), luz [-.6, -.8] (de dónde viene), brillo .55 (luz de
 *     borde), tinte [1, 1, 1, .06] (color y cuánto), sombra .22, fusion 60.
 *   El resultado (fondo + vidrio) reemplaza el cuadro de ctx entero (putImageData: no le afecta la transformación
 *   ni el modo de mezcla de ctx).
 *
 * Cómo funciona (idea del «Infinite Liquid Glass Grid» de Codrops, escrita desde cero): d = SDF de la unión
 * suave de los rectángulos; la normal es el gradiente de d; adentro, a profundidad e = −d, el perfil del bisel
 * da cuánto se corre la lectura: desp = refraccion · (1 − e/bisel)²; se lee el fondo tres veces (R, G, B) con
 * desp · (1 ∓ dispersion); luz de borde = franja junto al borde · (½ + ½ normal·luz), y un reflejo más débil
 * en el lado opuesto.
 */
window.Vidrio = (() => {
  const VERT = `#version 300 es
  in vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }`;
  const FRAG = `#version 300 es
  precision highp float;
  uniform sampler2D uFondo;
  uniform vec2 uRes;
  uniform vec4 uRect[6];      // centro x, y, medio ancho, medio alto
  uniform float uRadio[6];
  uniform int uN;
  uniform float uFusion, uBisel, uRefr, uDisp, uEsm, uBrillo, uSombra;
  uniform vec2 uLuz;
  uniform vec4 uTinte;
  out vec4 color;

  float caja(vec2 q, vec2 b, float r) {
    vec2 d = abs(q) - b + r;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;
  }
  float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
  }
  float sdf(vec2 p) {
    float d = 1e9;
    for (int i = 0; i < 6; i++) {
      if (i >= uN) break;
      float r = min(uRadio[i], min(uRect[i].z, uRect[i].w));
      float di = caja(p - uRect[i].xy, uRect[i].zw, r);
      d = (i == 0) ? di : smin(d, di, uFusion);
    }
    return d;
  }
  vec3 leer(vec2 p) { return texture(uFondo, clamp(p / uRes, vec2(0.0), vec2(1.0))).rgb; }
  vec3 leerEsm(vec2 p) {
    if (uEsm < 0.5) return leer(p);
    vec3 s = leer(p) * 0.2;
    for (int i = 0; i < 8; i++) {
      float a = float(i) * 0.785398 + 0.39;
      s += leer(p + vec2(cos(a), sin(a)) * uEsm) * 0.1;
    }
    return s;
  }

  void main() {
    // px con y hacia abajo, como el canvas 2D: la fila 0 de WebGL es la de arriba, así readPixels sale derecho
    vec2 p = gl_FragCoord.xy;
    vec3 atras = leer(p);
    float d = sdf(p);
    if (d > 60.0) { color = vec4(atras, 1.0); return; }
    // sombra suave por fuera
    float sombra = uSombra * (1.0 - smoothstep(0.0, 60.0, d)) * step(0.0, d);
    vec3 fuera = atras * (1.0 - sombra);
    if (d > 1.0) { color = vec4(fuera, 1.0); return; }
    vec2 e2 = vec2(1.0, 0.0);
    vec2 n = normalize(vec2(sdf(p + e2.xy) - sdf(p - e2.xy), sdf(p + e2.yx) - sdf(p - e2.yx)) + 1e-6);   // hacia afuera
    float prof = max(0.0, -d);
    float k = 1.0 - clamp(prof / uBisel, 0.0, 1.0);
    float desp = uRefr * k * k;
    vec2 dir = -n;                                            // lee desde adentro: el borde aumenta
    vec3 c;
    c.r = leerEsm(p + dir * desp * (1.0 - uDisp)).r;
    c.g = leerEsm(p + dir * desp).g;
    c.b = leerEsm(p + dir * desp * (1.0 + uDisp)).b;
    c = mix(c, uTinte.rgb, uTinte.a);
    // luz de borde: franja de ~6 px junto al borde, más fuerte del lado de la luz
    float franja = 1.0 - smoothstep(0.0, 6.0, prof);
    float lado = dot(n, normalize(uLuz));
    c += uBrillo * franja * (0.5 + 0.5 * lado);
    c += uBrillo * 0.35 * franja * max(0.0, -lado);
    // un brillo ancho y tenue en el bisel del lado de la luz
    c += uBrillo * 0.18 * k * k * max(0.0, lado);
    float cubre = clamp(0.5 - d, 0.0, 1.0);                   // antialias del borde
    color = vec4(mix(fuera, c, cubre), 1.0);
  }`;

  let lienzo = null, gl = null, prog = null, tex = null, U = {};
  function preparar(w, h) {
    if (!lienzo) {
      lienzo = document.createElement('canvas');
      gl = lienzo.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false, premultipliedAlpha: false });
      if (!gl) throw new Error('Vidrio: este navegador no tiene WebGL2');
      const sh = (tipo, src) => {
        const s = gl.createShader(tipo); gl.shaderSource(s, src); gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('Vidrio: ' + gl.getShaderInfoLog(s));
        return s;
      };
      prog = gl.createProgram();
      gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('Vidrio: ' + gl.getProgramInfoLog(prog));
      gl.useProgram(prog);
      const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      for (const n of ['uFondo', 'uRes', 'uRect', 'uRadio', 'uN', 'uFusion', 'uBisel', 'uRefr', 'uDisp', 'uEsm', 'uBrillo', 'uSombra', 'uLuz', 'uTinte'])
        U[n] = gl.getUniformLocation(prog, n);
    }
    if (lienzo.width !== w || lienzo.height !== h) { lienzo.width = w; lienzo.height = h; }
    gl.viewport(0, 0, w, h);
  }

  function dibujar(ctx, fondo, op) {
    const o = Object.assign({
      formas: [], bisel: 70, refraccion: 55, dispersion: .25, esmerilado: 0, luz: [-.6, -.8], brillo: .55,
      tinte: [1, 1, 1, .06], sombra: .22, fusion: 60,
    }, op);
    const W = ctx.canvas.width, H = ctx.canvas.height;
    preparar(W, H);
    gl.useProgram(prog);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, fondo);
    const n = Math.min(6, o.formas.length), rect = new Float32Array(24), radio = new Float32Array(6);
    for (let i = 0; i < n; i++) {
      const f = o.formas[i];
      rect.set([f.x + f.w / 2, f.y + f.h / 2, f.w / 2, f.h / 2], i * 4); radio[i] = f.radio ?? 40;
    }
    gl.uniform1i(U.uFondo, 0); gl.uniform2f(U.uRes, W, H);
    gl.uniform4fv(U.uRect, rect); gl.uniform1fv(U.uRadio, radio); gl.uniform1i(U.uN, n);
    gl.uniform1f(U.uFusion, Math.max(1e-3, o.fusion)); gl.uniform1f(U.uBisel, o.bisel); gl.uniform1f(U.uRefr, o.refraccion);
    gl.uniform1f(U.uDisp, o.dispersion); gl.uniform1f(U.uEsm, o.esmerilado); gl.uniform1f(U.uBrillo, o.brillo);
    gl.uniform1f(U.uSombra, o.sombra); gl.uniform2f(U.uLuz, o.luz[0], o.luz[1]); gl.uniform4f(U.uTinte, ...o.tinte);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    // El resultado vuelve por readPixels + putImageData (no con drawImage del lienzo WebGL): así el lienzo del
    // video sigue siendo de CPU y el cuadro sale idéntico en cada corrida (ver la nota de demo.html).
    if (!px || px.length !== W * H * 4) { px = new Uint8ClampedArray(W * H * 4); img = new ImageData(px, W, H); }
    gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(px.buffer));
    ctx.putImageData(img, 0, 0);
  }
  let px = null, img = null;

  return { dibujar };
})();
