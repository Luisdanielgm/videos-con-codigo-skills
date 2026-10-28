---
name: video-juego
description: Técnica 24. Juego jugable grabado - un juego chico escrito en código (Canvas 2D) que juega un programa («bot») y se graba como video vertical. La partida se simula UNA vez con paso fijo y semilla; cada cuadro sólo lee la tabla, así cualquier instante da lo mismo en cualquier orden (exporte por tramos). Los eventos de la misma simulación (aleteo, puerta, casi, choque) arman los efectos visuales y el sonido. Usar para reels con gancho («¿cuántas puertas cruza?»), para explicar una regla simple viéndola jugar, y para piezas de marca con mascota.
---

# Juego jugable grabado (técnica 24)

Antes: leer **`director-de-video`**. Ejemplo (no publicado en este repositorio; los comandos de abajo muestran la
estructura): `24-juego/grulla-vuela/` (30 s, 1080×1920: una grulla de papel cruza puertas; 18 puertas, 0 choques,
semilla 5). Origen: los ~70 juegos de la biblioteca Skillry y los juegos «de un intento» que circulan en X.

## La regla que lo hace grabable

**Simular una vez, dibujar leyendo.** Un juego tiene estado (la posición depende de todo lo anterior); el exporte por
tramos pide cuadros en cualquier orden. Por eso:

1. `juego.js` simula la partida entera al cargar, con **paso fijo** (1/120 s) y **azar con semilla**, y guarda una
   tabla por paso (posición, velocidad, puntos, último aleteo) más una lista de **eventos** con su tiempo.
2. `render(t)` sólo lee la tabla (`J.en(t)`, interpolada) y los eventos. Nada se acumula entre cuadros.
3. El mismo `juego.js` corre en Node (`module.exports`): `sonidos.js` lee los MISMOS eventos y escribe `mezcla.json`.
   Imagen y sonido no pueden desfasarse porque salen de una sola simulación.

## El jugador (el bot)

- Una regla corta y explicable, que el video puede decir en la tarjeta final («aletea cuando cae por debajo del centro
  del hueco»). Si la regla no cabe en una frase, el video pierde su remate.
- **Probar semillas por terminal antes de dibujar** (`node -e` con `simular({ semilla })` para 8 semillas: choques,
  puertas, aleteos, «casi»). La primera versión del ejemplo chocaba en todas las puertas: el bot miraba 0,18 s adelante
  y apuntaba arriba del hueco; con el umbral en el centro + 75 px y 0,05 s de mirada, 0 choques en las 8.
- Un «casi» (holgura < 40 px) vale oro: lleva sacudida, rótulo y sonido. Elegir una semilla que tenga uno.
- Contar cada choque **una vez** por obstáculo (si no, un roce suma cientos de eventos).

## La pieza

- **Vertical 1080×1920** (lienzo de ese tamaño; `reproductor.js` toma el tamaño del lienzo). Marcador grande arriba,
  aviso honesto abajo («la juega un programa, no una persona»), el juego en el medio.
- **Cuadro 0 terminado**: título-pregunta, marcador en 0 y el personaje flotando antes de que empiece la partida.
- **Final sin corte**: el tiempo del juego frena con una curva (`juegoT(t)`), el cuadro se oscurece y entra la tarjeta
  (resultado, la regla del bot, la semilla). En `sonidos.js` va la inversa de esa curva para ubicar los eventos.
- Efectos por evento, todos función de `t`: papelitos al aletear, «+1» que sube, rebote del marcador, sacudida en el
  «casi». Polvo de fondo con `Movimiento.motas` para que nada quede quieto.
- Personaje que se lea: color propio y borde de tinta (en el ejemplo, una grulla pálida se perdía en el cielo claro).

## Verificar y exportar

```
node 24-juego/<video>/sonidos.js                              # eventos → mezcla.json
.venv/Scripts/python herramientas/mezclar.py 24-juego/<video>
.venv/Scripts/python herramientas/navegador.py capturas 24-juego/<video> 0,6.3,14,26.2,29
VIDEOS_TRAMO=10 .venv/Scripts/python herramientas/navegador.py exportar 24-juego/<video>
```

Después, las guardias de `exportar-video` (crítico, verificar, saltos, determinismo).

## Nivel de estudio (lo que falta)

- Música por cálculo en la grilla de los aleteos (`musica.py`), hoy sólo efectos.
- Cámara que acompaña (un poco de zoom en el «casi»), y un segundo personaje o un rival.
- Versión interactiva: la misma página jugable con el teclado (hoy sólo la juega el bot).
