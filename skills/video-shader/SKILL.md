---
name: video-shader
description: 'Hace un video narrado donde cada cuadro lo calcula un solo shader de WebGL2, sin librerías ni imágenes: cielos, mar, luces, partículas y personajes en silueta (técnica 5 del proyecto). Usar para piezas de aspecto cinematográfico o atmosférico.'
---

# Video en un shader (WebGL2, técnica 5)

Resultado: `05-shader-webgl2/<video>/index.html` (+ `guion.json`, audio, `tiempos.js`) y el MP4 en
`render/05-shader-webgl2_<video>.mp4`. Ejemplo: `05-shader-webgl2/el-faro/` (un cuento original: faro, niebla y
un bote, del atardecer a la noche y al alba). **Leerlo antes.** La narración y la mezcla no vienen en el repositorio:
se regeneran con `narrar.py` y `sonido.py`.

## Qué hace falta

- El entorno `.venv` con las voces (`narrar-guion`) y `sonido.py` (numpy, scipy), ffmpeg y Chrome con WebGL2.
  Sin GPU, Chrome cae a WebGL por software (`--enable-unsafe-swiftshader`): funciona, pero exporta mucho más lento.

## La idea

Un triángulo que cubre la pantalla y un fragment shader que decide el color de cada píxel. JavaScript
no dibuja nada: para cada instante calcula la cámara, las posiciones y las poses, y se las pasa al
shader como uniforms. Después se copia el lienzo WebGL al lienzo 2D final, donde van título y subtítulos.

## Pasos

1. Guion, narración y sonido: skills `video-historia` y `narrar-guion` (`mezcla.wav` con `sonido.py`).
2. `index.html` con el contrato de abajo; mirarlo con `python herramientas/servidor.py`.
3. Capturas y hoja de contacto (`exportar-video`), revisión (abajo), exportar y recomprimir.

## Contrato

- WebGL2 con `preserveDrawingBuffer: true`, 1920×1080, en un lienzo aparte; `ctx.drawImage` al final sobre el
  `<canvas>` que recibe `Reproductor.iniciar`.
- `render(t)` determinista: ruido por hash en el shader, nada de `Math.random()`.
- **Coordenadas de mundo** iguales a las de la versión Canvas 2D (si la hay): el shader pasa cada píxel a mundo
  con la cámara (`w = (píxel − centro) / zoom + cámara`). Así se reutilizan los planos de otra técnica.
- **Personajes = lista de cápsulas** (`uCa[i] = a.xy, b.xy`; `uCr[i] = radio, dueño`) armada en JS
  desde la pose; el shader toma la distancia mínima y rellena. Ojos, boca y emblemas van como uniforms aparte.
- Partículas con historia (chispas que deja algo al moverse): JS pasa las últimas N posiciones y su edad.
- Lazos acotados (N fijo) y detalles caros sólo cuando están activos (uniform en 0 = no se calcula).

## Estilo del original

Formato panorámico 2.39:1 con franjas negras, viñeta y grano. El personaje humano lleva sus colores (material
por cápsula: piel, pelo, camisa, short, zapatos), iluminado por el atardecer o la luna, con borde de luz y
contorno fino; un personaje fantástico puede ser una silueta luminosa.

**No dejar a un personaje humano como sombra negra lisa**: se rechazó en la revisión (no se reconoce quién es y
se lee mal). La silueta pura sirve para lo que es de otro mundo o para contraluces breves.

## Revisar

Skill `exportar-video` (capturas y hoja de contacto). Además:
1. Nada importante detrás de las franjas negras (la luna, algo que entra por arriba).
2. Reflejos en el agua como destellos **horizontales** (ruido con más frecuencia en profundidad que a lo ancho);
   al revés salen bloques verticales.
3. Si el shader no compila, el error sale en consola y `navegador.py` termina con código 1.
4. **El grano de película pesa**: cambia en cada cuadro y el MP4 sale de ~200 MB. Después de exportar,
   recomprimir: `ffmpeg -i entrada.mp4 -c:v libx264 -crf 27 -tune grain -pix_fmt yuv420p -c:a copy salida.mp4`
   (en el original, 195 MB → 26 MB sin diferencia visible).

## Verificar

- `navegador.py capturas` con código 0; ninguna cara negra lisa; nada detrás de las franjas.
- MP4 ≈ `TIEMPOS.total` después de recomprimir; `saltos.py`.

## Nivel de estudio

- **Voces actuales**: narrador con Supertonic y voces de personaje que suenen a su edad (Kokoro con `tono`, o un
  modelo que permita diseñar voces).
- **Canción libre con sidechain** bajo las voces (`mezclar.py`) y ambiente real (mar, viento) en vez de `sonido.py`.
- **Cambios de lugar sin fundido**: ya son coordenadas de mundo; la cámara viaja o corta seco.
- **60 fps**; después, recomprimir con `-tune grain` (arriba).

## Herramientas externas (opcional)

- **Voces de niños**: un modelo de voz con diseño de voces por atributos, local o en la nube; revisar su licencia
  (muchos son sólo para uso no comercial) y cuánto tarda sin GPU.
- **Supertonic** (narrador, procesador) y **Mixkit** (canción y ambiente; bajar a `recursos/`).
- **No conviene**: imágenes o modelos generados. El shader calcula cada píxel; meter una imagen ya es otra técnica.
