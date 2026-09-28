---
name: video-html-canvas
description: 'Hace un video explicativo o narrativo narrado, dibujado con Canvas 2D en un solo HTML, sin librerías (técnica 1 del proyecto). Usar cuando piden un video nuevo con esta técnica, sobre cualquier tema.'
---

# Video en un solo HTML con Canvas 2D (técnica 1)

Resultado: una carpeta `01-html-canvas/<video>/` con `guion.json`, `narracion.wav`, `tiempos.js`
e `index.html`, más el MP4 en `render/01-html-canvas_<video>.mp4`. Ejemplo de referencia completo:
`01-html-canvas/red-neuronal/` («¿Cómo aprende una red neuronal?», 4 min) y su MP4 en
`ejemplos/01-html-canvas_red-neuronal.mp4`. **Leerlo antes de empezar**: muestra cada convención de abajo.

## Qué hace falta

- El entorno `.venv` con las voces (skill `narrar-guion`), ffmpeg y Chrome, Chromium o Edge.
- Nada más: el HTML no usa librerías. Para mirarlo en vivo, `python herramientas/servidor.py` y abrir
  `http://localhost:8790/01-html-canvas/<video>/` (abrir el archivo directo con `file://` no carga el audio).

## Reproducir el ejemplo

```
.venv/Scripts/python herramientas/narrar.py 01-html-canvas/red-neuronal        # narracion.wav + tiempos.js
python herramientas/navegador.py capturas 01-html-canvas/red-neuronal 5,40,90,150,220
python herramientas/navegador.py exportar 01-html-canvas/red-neuronal
```
El `tiempos.js` que viene en la carpeta ya sirve para mirar la animación sin narración. La música bajo la voz
es opcional: `mezcla.json` apunta a una canción de Mixkit en `recursos/musica/` (README) y se mezcla con
`herramientas/mezclar.py 01-html-canvas/red-neuronal`.

## Pasos

1. **Guion** (`guion.json`), para un público principiante:
   - Una idea por frase. Explicar cada concepto con una comparación cotidiana
     (peso = perilla de volumen, activación = regulador de luz, gradiente = bajar una montaña a ciegas).
   - Antes de lo abstracto, lo concreto: mostrar el ejemplo (un dibujo, un número) y después la regla.
   - Nombrar el término técnico **después** de explicarlo ("…a esto se le llama retropropagación").
   - Números en palabras. Cerrar con un resumen de los pasos.
2. **Narración**: skill `narrar-guion`.
3. **Animación** (`index.html`), con el contrato de abajo.
4. **Revisión visual**: skill `exportar-video`, sección de capturas. Una captura por frase; revisar
   la lista de defectos y corregir hasta que no quede ninguno.
5. **MP4**: skill `exportar-video`, sección de exportar.

## Contrato de `index.html`

- `<canvas width="1920" height="1080">`, escalado con CSS para caber en la ventana.
- Carga, en este orden: `tiempos.js` y `../../herramientas/reproductor.js`. Al final:
  `Reproductor.iniciar({ canvas, render, duracion: TIEMPOS.total, audio: 'narracion.wav' })`.
- `render(t)` dibuja el instante `t` **desde cero y de forma determinista**: sin `Math.random()`
  (usar un generador con semilla), sin estado que dependa del cuadro anterior. Así se puede exportar
  y revisar cualquier instante.
- **Todo se ubica relativo a la narración**, nunca con segundos fijos. `Reproductor.ayudantes(TIEMPOS)` da:
  - `A(id)` inicio de la frase, `D(id)` duración, `F(id, f)` instante en la fracción `f` de la frase.
  - `P(t, id, f0, f1)` avance suavizado de 0 a 1 entre dos fracciones de la frase.
  - `vis(t, desde, hasta)` visibilidad de una escena que abarca varias frases (con fundidos); `SIG(id)` inicio
    de la frase siguiente.
- Subtítulos: `Reproductor.subtitulos(ctx, t, TIEMPOS)` al final de `render`. Ocupan y ≥ 960.
- Título de sección arriba a la izquierda (y ≈ 70). El contenido va entre y ≈ 120 y y ≈ 930.
- Una escena = una función `escenaX(t)` que sale enseguida si su visibilidad es 0.
- Colores con significado constante: positivo azul, negativo naranja, correcto verde, error rojo,
  énfasis dorado. Nada de texto menor a 24 px.

## Consistencia (lo que más falla)

- Lo que se dibuja tiene que coincidir con lo que se dice: si el dibujo tiene 64 píxeles, la capa de
  entrada tiene 64 neuronas, cada una unida a su píxel. Si la voz dice "setenta y uno por ciento",
  la pantalla muestra 71 % antes o al mismo tiempo.
- Cada recorrido animado llega a su final (si va de 0 a N capas, el valor final supera N).
- Porcentajes y etiquetas nunca encima de barras, cables u otras etiquetas.

## Verificar antes de entregar

- `python herramientas/navegador.py capturas …` sale con código 0 (sin errores de consola).
- Ninguna captura muestra los defectos de la lista de `exportar-video`.
- El MP4 existe y dura lo mismo que `TIEMPOS.total` (±1 s); `saltos.py` sobre el MP4.

## Nivel de estudio

- **Una sola toma**: en vez de `vis()` con fundidos, las escenas viven una al lado de la otra en un lienzo
  grande y la cámara pasa de una a la siguiente, o un elemento se vuelve la escena siguiente (el 7 de píxeles
  se vuelve la capa de entrada). En la hoja de contacto, ningún cuadro con dos escenas semitransparentes.
- **Narrador con Supertonic** (`"voz": "supertonic:M5"` en `guion.json`; skill `narrar-guion`).
- **Canción bajo la voz** que baja sola cuando habla (`herramientas/mezclar.py` con `"voz"` y `"cancion"` en
  `mezcla.json`, como en el ejemplo), y un efecto real por evento en su pico.
- **60 fps con desenfoque de movimiento**: `VIDEOS_PARAMS="fps=60&sub=4"` al exportar.
- **Revisar el MP4 en movimiento**, no sólo las capturas: fundidos y saltos no se ven en un cuadro suelto.

## Herramientas externas (opcional)

- **Mixkit** (canciones y efectos con licencia gratuita de Mixkit; las marcadas como restringidas son sólo para
  uso personal): música bajo la voz y efectos. Se bajan a `recursos/` (fuera de git). Tempo y compases con
  `herramientas/cancion.py`.
- **No conviene**: imágenes generadas ni modelos 3D. El canvas es dibujo limpio por código, y una imagen
  generada rompe el estilo y la comparación con las otras técnicas del mismo guion.
