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
- **Todo se ubica relativo a la narración**, nunca con segundos fijos ni con una grilla de pulsos: en un
  narrado la coreografía va **por frases**, y la música se acomoda debajo. `Reproductor.ayudantes(TIEMPOS)` da:
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

## Dirección de un narrado (reglas finas)

Recetas tomadas de videos y guías públicas (citadas en cada punto).
- **≥ 400 ms de quietud cuando hay voz**: mientras la voz dice la idea, lo que la muestra está quieto al menos
  400 ms para que se pueda mirar; el movimiento va entre ideas (al principio o al final de la frase, `P(t, id, 0, .3)`).
- **La metáfora tiene que contar sola**: sin voz ni subtítulos, alguien que no leyó el guion tiene que poder decir
  qué pasa (referencia: el video sin texto de @TheSpacerr, una figura con un hilo a una esfera que crece hasta
  envolverla). Si la imagen sólo acompaña a la voz, falta la metáfora.
- **Simular lo real en vez de dibujarlo**: si se habla de un paseo al azar, una caída o una red que aprende, la
  imagen sale de calcularlo de verdad (con semilla y paso fijo, en función de `t`), no de una curva a ojo.
- **Cambios de escala con un zoom continuo de potencias de diez**: una sola cámara que acerca de forma
  exponencial (la escala es `10^k`, con `k` que avanza parejo), cada tramo dura en proporción a `log10` del
  zoom que recorre, y una **regla de escala** en pantalla («1 m», «1 mm», «1 µm») que cambia con él.

## Variante Kurzgesagt (escalas y mecanismos en formas planas)

Para explicar **escalas** («¿qué hay adentro?»: de la hoja a la célula, del píxel al modelo) y **mecanismos que no se ven**
(defensas del cuerpo, una red, la energía): la idea se vuelve un objeto plano en un mundo que se puede acercar sin fin, y la
cámara viaja entre escalas. **No** para personas o hechos reales con pruebas (eso es la «mesa con evidencia» de
`video-archivo`) ni para los pasos de un razonamiento (pizarra).

- **Primero la metáfora**: cada frase abstracta se escribe como un objeto (célula, engranaje, tubería, ciudad, gota). Si
  una frase no tiene objeto, no se tapa el hueco con una esfera brillante y dos etiquetas.
- **Formas**: planas, sin contorno, todo redondeado. Sombra = el mismo color un escalón más oscuro, en una franja abajo a
  la derecha (desplazar la forma dentro de sí misma ≈ 10 px); luz = un borde fino claro arriba a la izquierda. Lo que
  brilla lleva su halo radial. **Un fondo oscuro con 2–3 acentos saturados que contrastan** (naranja contra azul, cian
  contra magenta), nunca gris para sombrear. El violeta oscuro con estrellas del original **no**: es lo primero que delata
  «hecho por IA» y está en los prohibidos (`video-lanzamiento`); fondo tinta o azul marino plano.
- **Profundidad**: 4–6 capas con parallax (estrellas 0,05 · lejos 0,3 · medio 0,65 · sujeto 1,0 · frente 1,5, oscuro y
  desenfocado). La capa se desplaza según su factor y se escala con `zoom^factor`: al acercar mucho, lo lejano casi no se
  mueve.
- **Movimiento**: el sujeto cambia de estado en cada frase (aparece, se transforma, se entra en él, se aleja) y **después
  se queda quieto** (encaja con los ≥ 400 ms de quietud de arriba). Lo que no para es el ambiente: estrellas que titilan,
  partículas que derivan; nada de «todo respira». Curva de la casa: arranque y llegada muy suaves con el medio rápido,
  `cubic-bezier(.75,0,.25,1)`. Un rótulo que salta llega al 90 % en 0,25 s, se pasa a ≈ 108 % y vuelve en ≈ 0,5 s
  (`M.resorte` con `amort` ≈ 0,5). Escalonado: los de la misma clase 10–20 cuadros a 60 fps; las partes de un cuerpo 3–4.
- **Atravesar de una escala a otra** (la firma): el zoom es logarítmico (la regla de «Cambios de escala» de arriba). Antes
  de entrar, el objeto elegido se queda quieto ≥ 0,3 s y se ilumina, para que se sepa adónde se va. Después la cámara se
  lanza hacia él hasta que su color llena el cuadro y del otro lado está la escena nueva (≈ 1–1,4 s, rápido en el medio:
  `expoInOut` o la curva de la casa, **no** `expo`, que en el primer cuadro ya salta media escala). Variante: entrar por una
  «ventana» (un círculo que crece y deja ver la escena siguiente). Al alejarse, arranque rápido y cola larga. **Cada escala
  se vuelve a dibujar en su zoom**: ampliar la imagen de la escala anterior se ve en mosaico.
- **Ritmo**: tomas de 7–9 s, pero algo cambia en la imagen cada 4,6–6,7 s; el corte cae 0–0,2 s antes de la frase nueva.
  Un rótulo = una línea fina que sale del objeto + un texto que se escribe a ≈ 40 letras por segundo; queda ≈ 3 s y se borra.

Gramática de huashu-art-motion (alchaincyf, MIT), `references/动画语法/y1_kurzgesagt.md`, con palabras propias; sus cifras
salen de medir tres videos de Kurzgesagt y del curso oficial. Con átomos reales en vez de formas planas: `video-ciencia-real`.

## Receta 2.5D isométrica (de `isometric-animation`, `iart-ai`, MIT)

Ejemplo propio (24,7 s, no publicado): una isla de 8×8 a ±30° donde suben con resorte cuatro edificios-función (se extruyen en z, nunca escalan),
caminos que se dibujan, una luz que los recorre y la libreta en la plaza; tres polígonos por caja con una sola luz, sombras
planas en una dirección, orden topológico de atrás hacia adelante; determinismo 6 de 6. Lo que falló: las tarjetas de nombre
tocaban el titular y entre sí (se movió la ciudad y se achicó el titular).

Para pilas de capas, torres de tecnología, bloques extruidos y diagramas que se abren y se arman, en Canvas 2D o SVG:
- **Ejes**: isométrico verdadero = ejes del suelo a ±30° de la horizontal; «dimétrico 2:1» (pixel-art) = ±26,57°
  (`atan(0.5)`). Se elige uno y no se mezclan. Baldosa (col, fila) → pantalla `(col − fila, col + fila)·(ancho/2, alto/2)`.
- **Proyección paralela**: lo lejano **no** se achica. En three.js, `OrthographicCamera` (con `PerspectiveCamera` no es isométrico).
- **Volumen con tres polígonos**: tapa más clara, cara izquierda media, derecha más oscura, con **una luz fija** en toda la
  escena; es el truco que más pesa en la profundidad.
- **Alturas**: subir por Z, nunca escalar (escalar rompe la proyección paralela). Explotado = el mismo apilado con una
  separación `gap` compartida que se interpola; armar = llevar cada capa a su asiento. Construir de abajo arriba por
  posición física (resorte con rebote ligero, 0,12–0,15 s entre capas), no por el orden del código.
- **Cámara**: a lo sumo una deriva chica y lenta (unos grados, 6–12 s); un movimiento grande delata que es un plano.

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
