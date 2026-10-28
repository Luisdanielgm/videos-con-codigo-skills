---
name: video-dibujo-animado
description: Técnica 23. Dibujo animado pintado a mano con p5.brush (acuarela, aguada, tinta, papel con grano) - un personaje con hoja de modelo (proporciones fijas en «cabezas»), hoja de poses y 4–6 emociones que se mezclan según el guion, storyboard primero, 4–6 planos con cámara que se mueve poco, tinta que tiembla con semilla («boiling» a 12 dibujos por segundo dentro de 60 fps), todo determinista. Se verifica con hojas de contacto, tiras cuadro a cuadro, medición de proporciones en las capturas, saltos.py y el mismo cuadro pintado dos veces. Usar para cuentos cortos con un personaje que actúa, escenas emotivas y piezas «hechas a mano» sin imágenes generadas.
---

# Dibujo animado pintado a mano (técnica 23)

Antes: leer **`director-de-video`** y, si es una historia, **`video-historia`** (guion, voces, continuidad).
Ejemplo: `23-dibujo-animado/el-faro/` (35 s, Lía sola en el faro; cuento original «El faro»), con su motor compartido
`23-dibujo-animado/motor.js` (**no publicados en este repositorio**: la skill describe el método y la estructura de
archivos para armarlos). Librerías locales (sí vienen): `herramientas/vendor/p5/` (p5.js 2.3.4, LGPL-2.1; p5.brush 2.2.3,
MIT; ver `VERSION.txt`). Método de origen: JohnHeibel/ClaudeAnimationBase (MIT) y p5.brush de acamposuribe.

## 1. Primero el personaje: hoja de modelo, poses y emociones

Todo el personaje vive en UN archivo (`lia.js`) y nada más lo dibuja.
- **Hoja de modelo**: la unidad es `u` = alto de la cabeza; pies en (0, 0), y hacia abajo. Escribir las medidas en
  `M` (alto total 3,45 u, hombros 2,42, cadera 1,05, ojos 2,92…) y no tocarlas entre planos: un plano general y un
  primer plano sólo cambian `u` y la cámara. Vistas: de frente (`g` = 0), tres cuartos (`g` = .8) y espejada (`dir` = −1).
- **Hoja de poses**: números, no dibujos (`g`, `inclina`, `cabeza`, `dy`, `sq`, `[hombro, codo]` de cada brazo).
  Las manos que tienen que tocar algo van por cinemática inversa: `manoN`/`manoL` en coordenadas del modelo
  (pecho, cadera, frente) o `Lia.ik(...)` hacia un punto del mundo (el aro de la rueda).
- **Emociones (4–6)**: también números (apertura del ojo, ojo feliz, ceja alta y su ángulo, curva y apertura de la
  boca, dientes, temblor, rubor, hacia dónde mira). `Lia.actuar(t, [[t0, 'contenta'], [t1, 'sorpresa', {…}, dur]], tabla)`
  mezcla de una a otra en ~0,3 s: nada salta de una cara a otra. Una sorpresa entra más rápido (0,12 s).
- Renderizar las tres hojas **antes** de animar (en el ejemplo, `?capturas=901,902,903`) y corregirlas ahí:
  es lo más barato.

## 2. Storyboard antes del código (`storyboard.md`)

Idea en una frase, mundo con coordenadas fijas, paleta corta, un motivo que vuelve, arco de emociones, y por plano:
tiempo, tamaño, qué pasa (un evento por plano), qué siente el personaje. Listar las **lecturas** en orden y darle a
cada una tiempo para verse. **La causa antes que la reacción** (la luz se para y 0,2 s después reacciona). Sin texto
en pantalla. Los planos se ubican con `tiempos.js` (un segmento del guion por plano): al narrar, se acomodan solos.

## 3. Pinceles y papel (`motor.js`)

- p5.brush pinta en un lienzo WEBGL oculto; el dibujo se copia a un lienzo 2D y el reproductor lo compone.
  **`redraw()` de p5 2.x es asíncrono**: se pinta en el `antes(t)` del reproductor (`await Dibujo.asegurar(...)`),
  y `render(t)` sólo compone (cámara, luces, papel). Un cuadro cuesta ~1 s de pintura; 12 por segundo de video.
- `Dibujo.forma(pts, {wash | fill, tinta, w})`: **aguada** (`wash`, plana) para personajes y objetos;
  **acuarela** (`fill` con `bleed` .03–.3 y textura) para cielos, sombras y niebla; **tinta** de contorno con el
  pincel propio `tinta` (o `HB`, `fina`). Las coordenadas son del mundo (`Dibujo.vista(cx, cy, z)` por plano).
- La luz no es pigmento: brillos y haces van **aditivos** en el lienzo 2D (`Dibujo.luz`, cuña con degradé).
- Papel: grano generado una vez con semilla, en `multiply` sobre todo el cuadro, que se corre unos píxeles con cada
  dibujo (cada dibujo es otra hoja). Viñeta suave. Entrada y salida desde el papel.

## 4. Boiling con semilla

- `nDibujo(t) = floor(t·12)`: la pintura cambia 12 veces por segundo; la cámara se mueve a 60 sobre el dibujo
  (escala 1–1,1 y un corrimiento chico; nunca deja ver el borde).
- `Dibujo.semilla(elemento, n)` antes de cada elemento: así algo que se mueve no hace hervir lo que está quieto.
  Fondos grandes con `floor(n/3)` (hierven a 4 por segundo: menos ruido en las acuarelas grandes).
- Valores que no deben hervir (posición de estrellas, olas): `Dibujo.rnd(clave)`. Nada de `Math.random`.
- La actuación también va a 12 (se calcula con `n/12`): es animación «en cincos» a 60 fps.
- **Hoja de exposición con dibujos enteros** (de `hand-drawn-canvas-animation` de alesha-pro): decidir antes qué
  dibujos existen y cuánto dura cada uno (de a uno, de a dos o de a tres). Un cuerpo que se comprime, se cruza o se tapa
  **se redibuja** (silueta clara en cada dibujo), no se interpola entre dos poses: lo interpolado sale blando y pierde la
  silueta. Cada trazo con id estable (`elemento-parte-n`) para que la misma semilla dé el mismo trazo. Revisar el MP4 a
  velocidad normal y cuadro a cuadro (tira de 12 cuadros seguidos) y mirar los cambios de material (tinta a lápiz) por
  parpadeo no querido.

## 5. Que el personaje sea el mismo en todos los planos

- Una sola función, unas solas medidas (sección 1). El grosor de la tinta crece con la **raíz** del tamaño en
  pantalla (si crece con el zoom, el primer plano parece otro dibujo); el temblor, igual.
- **El aplaste y el estirón van al cuerpo; la cabeza se traslada rígida.** Si no, la cara cambia de forma (medido:
  +12 % en la sorpresa).
- **Control en las capturas**: `23-dibujo-animado/medir.py <prefijo> 901 t1,t2,…` busca por color la cara y las botas
  en cada JPG, mide alto/ancho de la cara y «cuántas caras mide» el cuerpo, y lo compara con la figura de tres cuartos
  de la hoja de modelo; marca lo que se aparta más del 8 %. Medir cuadros de pie (un salto cambia el cuerpo a
  propósito). En el ejemplo, todo quedó entre −2 % y +5 %.

## 6. Audio

Sin narración: `narracion.wav` muda del largo del video + `tiempos.js` provisional (con `"provisional": true`: no se
muestran subtítulos) → `herramientas/sonido.py <carpeta>` → `mezcla.wav` (mar, viento, música por ánimo, silencio,
latido, brillo). Con narración: `herramientas/narrar.py <carpeta>` reescribe `narracion.wav` y `tiempos.js` (sin
`provisional`, aparecen los subtítulos) y después otra vez `sonido.py`. Si un plano queda corto para su acción, subir su `pausa`.

## 7. Verificar (sin exportar todo)

1. **Hojas** de modelo, poses y emociones (`?capturas=901,902,903`).
2. **Hoja de contacto** de 6–12 cuadros clave: `navegador.py capturas <carpeta> t1,…` y `herramientas/hoja.py <prefijo> t1,…`.
   Usar tiempos con un decimal (caen en la grilla de 1/30 y la pintura pedida es la que se compone).
3. **Tira** cuadro a cuadro de cada acción (cada 0,1 s): anticipación, salto, giro, que no haya poses que saltan.
4. **Proporciones**: `medir.py` (sección 5).
5. **Mismo t, mismos píxeles**: capturar dos veces en orden inverso y comparar el md5 de cada JPG (en el ejemplo, 17 de 17 iguales).
6. **Saltos**: exportar un tramo de 3 s que cruce un corte (`VIDEOS_PARAMS="fps=60&sub=4&desde=5&hasta=8&parte=prueba"
   VIDEOS_PARTE=prueba`) y `herramientas/saltos.py render/<video>_prueba.mp4 --cortes 1.0`. El boiling da un cambio de
   ~1 % cada 5 cuadros y no se marca; el corte sí, si no se lo excluye. Borrar el tramo de prueba después.

## 8. Exportar

```
VIDEOS_PARAMS="fps=60&sub=4" .venv/Scripts/python herramientas/navegador.py exportar 23-dibujo-animado/el-faro
```
→ `render/23-dibujo-animado_el-faro.mp4` con `mezcla.wav`. Medido con una gráfica Intel integrada: 3 s en 91 s → ~18 min
para 35 s. No exportar con `--use-angle=vulkan` (en la NVIDIA de esa máquina): en exportes largos deja fondos faltantes
y cuelgues. Mejor `VIDEOS_TRAMO=10` con la gráfica por omisión.

## Lo que falló (y cómo se arregló)

- **La pared, el piso y el cielo de la ventana no salían** (se veía el papel): p5.brush pierde las formas que se van
  muy lejos del lienzo con zoom. Los fondos grandes van con `Dibujo.rectV(...)` (recortado a lo visible).
- **`brush.clip` sólo recorta trazos**, no aguadas ni acuarelas: la ventana y las celdas de la hoja se salían. El
  motor recorta los polígonos (Sutherland–Hodgman) con `Dibujo.recorte(...)`.
- **`brush.spline` con dos puntos no dibuja nada** (rayos de la rueda, pasto, reflejo de la luna): el motor agrega el
  punto medio. Y un trazo de tinta grueso queda fino: lo grueso (rayos, aro) se arma con formas.
- **Una forma de cuatro puntos sale con esquinas redondas** (curvatura .35 por omisión): los rectángulos van con curvatura 0.
- **El codo daba la vuelta**: la cinemática inversa devolvía −4,1 rad y al mezclar con la pose anterior el brazo
  giraba de más. Normalizar los ángulos a (−π, π] y resolver las manos ANTES de mezclar poses.
- **La mano iba a la cara** al empujar la rueda: el aro estaba a la altura de la cara. Ubicar los objetos que se
  agarran a la altura del pecho y comprobar con la tira.
- **El antebrazo de la visera tapaba un ojo**: la mano va al borde de la frente. Revisar la silueta en la hoja de poses.
- **El haz pintado parecía una nube**: el haz es luz (aditiva, cuña con degradé); la acuarela debajo, apenas.
- **Capturas cortadas a la mitad** por otro proceso que capturaba a la vez: `navegador.py capturas` termina con el
  primer `render/capturas/.listo`, que es compartido. Si hay otras capturas corriendo, esperar o comprobar que
  estén todas las pedidas (fecha del archivo) antes de mirar la hoja.

## Nivel de estudio (lo que falta)

- Narrar el guion (Supertonic M5) y comprobar que cada plano alcanza para su acción.
- Transiciones pintadas (barrido de pincel) en vez de cortes directos en p1→p2 y p5→p6.
- Caminar (ciclo de marcha en la hoja de poses) y parpadeo con anticipación.
- Canción real y efectos reales con `mezclar.py` (la rueda que cruje, el clic de la luz que se para).

## Herramientas externas (opcional)

- **Ninguna hace falta**: todo es código y librerías locales. **No conviene** un generador de imágenes (el estilo
  es el pincel; para papel recortado ya está la técnica 16).
