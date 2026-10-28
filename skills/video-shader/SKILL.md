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
- **Hash entero, nunca `fract(sin(dot(p,v))*43758)`**: ese hash cambia por completo con 1 ulp de diferencia en `sin()`,
  y cada GPU lo redondea distinto. En la NVIDIA el ruido sale en **bloques rectangulares** de brillo distinto (cada celda
  da otro valor en sus bordes); en la Intel sale liso, así que las capturas por omisión no lo muestran. Usa PCG con `uint`
  (`precision highp int;`, `uvec2(ivec2(floor(p)))`): idéntico en cualquier GPU. Comprobación: la misma captura en la
  Intel y con `VIDEOS_CHROME_ARGS="--use-angle=vulkan --enable-features=Vulkan"` debe dar píxeles iguales (±grano).
  El grano de película también va por hash entero con el cuadro como semilla (`uint(t*240.)`), no por un corrimiento.

## Que ningún plano quede quieto

El crítico mide el MP4 ya comprimido (x264 borra los cambios de menos de ~0,3 px por cuadro): un plano fijo con sólo
nubes lentas cuenta como quieto (en «El faro», 1,3 s). Reglas:
- **Deriva de cámara** en `camara(t)` para todos los planos: ±8 px y un respiro de zoom de 0,6 %, en función de `t`
  (suma de dos senos, en píxeles: `px / zoom` en mundo). Medido: el tramo quieto más largo bajó de 1,33 s a 0,20 s.
- **Personajes con vida**: respirar (pecho y cabeza ±0,3–0,5 unidades), peso de un pie al otro, mirada que vaga,
  parpadeo (uniform que achata el ojo cada ~3,4 s), cabeceo y un brazo que gesticula mientras hablan, y al empujar el
  cuerpo sube y baja con el ritmo de la manivela. Un `habla(t, quien)` de 0 a 1 sale de `tiempos.js`.
- **Primer cuadro terminado**: sin fundido desde negro; título y escena ya compuestos en `t = 0` (sólo el final se funde).
- **Destellos acotados**: un halo aditivo que cruza la cámara se come el cuadro en planos cerrados (zoom > 3) y borra a
  los personajes. Radio y pico se reducen con el zoom (`1 - .5*smoothstep(2., 5., z)`), pico aditivo ≤ 0,75.

## Sonoridad

La mezcla de `sonido.py` sale a −26 LUFS (casi muda en redes). Antes de exportar, normalizar a −14 LUFS con pico ≤ −2 dBTP
sin aplastar la voz (compresor suave + limitador; `loudnorm` solo no alcanza: el pico de la voz queda 12 dB sobre el nivel):

    ffmpeg -i mezcla.wav -af "highpass=f=45,acompressor=threshold=0.1:ratio=2.5:attack=10:release=200:makeup=1,volume=18.4dB,alimiter=limit=0.6:attack=3:release=60:level=disabled,aresample=24000" -c:a pcm_s16le mezcla_n.wav

(El `volume` depende de la mezcla: medirla con `ebur128=peak=true` y ajustar hasta −14 ± 0,5. En «El faro»: −25,7 → −14,3 LUFS,
pico −5,0 → −2,0 dBTP.) Re-correr `sonido.py` pisa `mezcla.wav`: normalizar de nuevo después.

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
