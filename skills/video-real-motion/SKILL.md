---
name: video-real-motion
description: Técnica 27. Material real con motion graphics: clips del negocio o de stock con gráficos que reaccionan a lo que se ve y se dice (círculos en el detalle que nombra la voz, palabras que entran en su sílaba, una foto que crece hasta ser video, teléfonos con video real, una persona recortada delante o detrás de los gráficos), en una página de `render(t)` exportada cuadro a cuadro. Usar para reels de producto con voz, una persona sobre mundos que cambian y comerciales de una sola toma con material verdadero.
---

# Material real con motion graphics (técnica 27)

Antes: leer **`director-de-video`** y **`director-marketing`** (el material tiene que ser verdadero: ver `video-lanzamiento`).
No hay ejemplo publicado (el material era de un negocio real). Los que se hicieron: un reel vertical de 30 s con voz para un
taller de impresión 3D, una persona de stock sobre 7 mundos (21 s) y teléfonos con video real (15 s, a 60 fps). La estructura:
`27-real-motion/<video>/` con `preparar.py`, `index.html`, `guion.json`, `palabras.js` y `mezcla.json`. Hecha a partir de reels
públicos de @sab8a y @samuel_yostt; de ellos se toma la gramática, nunca el prompt ni el código.

## Pasos

1. **Material primero.** Hace falta el archivo antes de planear la toma: clips del negocio (los baja o autoriza el dueño;
   viven en `recursos/27-real-motion/`, fuera de git) o de stock (Pexels sirve los videos **sin audio**: una persona
   hablando de verdad hay que grabarla). La tabla de tomas (`tomas.md`, con `tabla_tomas.py`) dice por toma qué material usa;
   si no existe el archivo, la toma es «dibujada en código» o no va.
2. **Preparar los clips** (un `preparar.py` por video): sin audio, a **30 fps constantes** y
   **todo intra** (`ffmpeg … -g 1 -an -c:v libx264 -crf 16 -pix_fmt yuv420p`). Marcas de terceros (TikTok) fuera con `delogo` o
   recorte. **Material corto se alarga** con encuadres distintos del mismo clip y el clip al revés (se lee como el mismo paneo
   hacia el otro lado).
3. **Guion y voz**: `narrar-guion` (una voz de pago como ElevenLabs, sólo con permiso de quien paga; antes `auditar_voz.py`).
   Una palabra mal pronunciada se arregla en el `texto` de la voz del `guion.json` («porta lápices»), sin cambiar lo que se ve.
4. **Tiempo de cada palabra**: `<venv-vision>/Scripts/python herramientas/palabras.py <carpeta>` →
   `palabras.js` (`PALABRAS = [{t, f, p, seg}]`). Si hay `guion.json`, el texto manda y whisper sólo pone los tiempos.
5. **Recortar una persona** (si la hay): `<venv-vision>/Scripts/python herramientas/recortar_persona.py entrada.mp4 salida`
   → `salida.mp4` (color) y `salida_mascara.mp4`, los dos todo intra. En la página se dibuja la máscara y encima el color con
   `source-in`.
6. **Animar** (`index.html`, con `herramientas/clips.js` y `reproductor.js`): `Clips.cargar(base, {nombre: 'archivo.mp4'})` y
   `Reproductor.iniciar({canvas, render, duracion, audio, antes: Clips.antes(usos)})`, donde `usos(t)` devuelve los clips que se
   ven en `t` y el segundo de cada uno. `Clips.dibujar(ctx, nombre, x, y, w, h, {zoom, cx, cy})` los pone en el cuadro. Los
   gráficos van **sobre** lo que se ve: círculo en el detalle, palabra grande en su sílaba, foto que crece hasta ser el video.
   Todo en `render(t)` puro (sin estado entre cuadros; ver las trampas).
7. **Música y efectos**, según «Que cada pieza suene distinta» en `video-lanzamiento`: si la marca no quiere canción en el
   MP4 (o la agrega al publicar), sólo efectos; si su canción está sin decidir, preguntar antes. Fuera de marketing, una pista
   distinta por video; en explicativos, sin cama musical. Efectos: **kit propio** (`herramientas/kit_efectos.py <carpeta>` →
   `sfx/`, afinado a la tónica de la canción; en el `efectos.py`, `Kit(AQUI)("whoosh", t, db)` pone el pico en `t`), escrito
   en `mezcla.json` desde las palabras de la voz (`palabras.js`). `mezclar.py` avisa si la canción o los efectos repiten los
   de las piezas recientes.
8. **Exportar y calificar** (`exportar-video`): `determinismo.py <carpeta>` y `verificar_export.py <carpeta>` al exportar, y
   `critico.py <mp4>` sobre el MP4 final. Una pasada con la hoja de cuadros pidiendo aparte la **coherencia entre texto e
   imagen** («¿lo que dice el texto se ve en el cuadro?») y revisar que ningún texto tape la cabeza de la persona.

## Trampas que ya costaron tiempo

- **Clips que no son todo intra o no van a fps fijo**: el exporte salta o repite cuadros. `-g 1` y `fps=30` siempre.
- **faster-whisper 1.2.1**: decodificar el audio con ffmpeg (PyAV no acepta `metadata_errors`) y **sin `vad_filter`** (rompe la
  alineación de palabras). Whisper confunde nombres propios: por eso el guion manda.
- **ACE-Step 1.5 en una GPU de 4 GB**: en float16 el VAE desborda a NaN y la pista sale entera en NaN **sin error**;
  generar con el VAE en float32 (DiT en bfloat16, 1–3 min por pista) y descartar la pista si trae NaN; aun así, revisar el WAV.
  Medir el BPM con autocorrelación de los golpes (un detector simple dio 81 BPM en una pista de 126). Va en `externos/ace-step`;
  si la GPU es compartida, no correrla junto con otro render. **Al oído no alcanzó**: una funk de ACE-Step medía 5 cents de
  afinación y aun así sonó «incoherente o desafinada» (armonía poco clara); el reel quedó sin canción.
- **Estado entre cuadros**: `determinismo.py` atrapó un `textAlign` suelto. Cada cuadro fija todo lo que usa. Un clip puede
  quedar con una diferencia mínima (peor bloque 6,8) en su primer salto en Chrome sin ventana.
- **Un efecto demasiado débil no lo ve nadie en una hoja chica** (pasó con el pixel art de la persona): se mide o se compara
  contra la referencia, no se le pide al crítico. **Nada de gráficas sin datos**: sin serie real se muestra la cifra sola.
- **El crítico visual inventa**: DeepSeek v4.1 Flash acierta lo mismo que Sonnet y Opus (2 de 4 defectos sembrados) pero confunde
  fotos con emojis; que Sonnet confirme sólo lo que él marca.

## Reglas de verdad y derechos

- El material de un cliente **no se publica sin permiso del dueño**; los nombres de terceros visibles en el
  material (clientes en un llavero, por ejemplo) se confirman antes de publicar. Precios estimados se rotulan como estimados.
- Nada se publica ni se sube desde aquí (🔴: lo hace el dueño). Una persona de stock no es nadie del negocio: no se presenta
  como tal.
- Se copia la **gramática** de las referencias (qué se mueve, cuándo y por qué), no su prompt, su código ni su material.

## Nivel de estudio

Lo que falta:
- Una columna **«Material»** en `tabla_tomas.py` con una guardia que rechace una toma «real» sin archivo (el criterio se
  acuerda antes con 2 o 3 ejemplos buenos y malos).
- Medir con varios modelos quién escribe bien una escena nueva y quién alarga material real.
- Ningún ejemplo usa a **una persona del negocio hablando a cámara** (hace falta material grabado) ni una canción de ACE-Step con letra.
