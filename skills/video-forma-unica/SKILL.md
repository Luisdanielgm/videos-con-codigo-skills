---
name: video-forma-unica
description: 'Técnica 8. Comercial de app (25–30 s) donde UNA sola forma recorre todo el video sin cortes y se vuelve cada pantalla o componente (botón, lista, chat, toggle…), con cursor, cámara que acerca y bucle, en Canvas 2D, sobre la grilla de una canción real con efectos reales. Usar para lanzamientos de apps con interfaz.'
---

# Forma única que se transforma (técnica 8)

Antes: leer la skill base **`video-lanzamiento`** (material verdadero, plan en pulsos, música, reglas,
dirección). No hay ejemplo publicado (el original era el comercial de una app propia); la estructura es
`08-lanzamiento/<producto>/index.html` + `musica.json` + `pulsos.js` + `mezcla.json`.
Referencia: el prompt de motion design de @twoclipping en X (una forma que nunca se corta, cursor con clics y
arrastres reales, cámara que acerca, el último cuadro igual al primero).

## Qué hace falta

- El entorno `.venv`, ffmpeg y Chrome.
- Una canción libre cerca de 120 BPM (p. ej. de Mixkit, en `recursos/musica/`) y el banco de efectos
  (`recursos/efectos/listos`, ver README). Sin ellos, `musica.py` calcula música y efectos (respaldo).
- Los estados reales de la app: capturas o el código de su interfaz (nunca inventados).

## Idea

Un solo elemento que nunca se corta: cambia tamaño, radio y color mientras su contenido se cambia con un
desenfoque corto. Un cursor maneja cada cambio (clics, arrastres). La cámara se acerca para que cada estado
llene el cuadro. Si se puede, el último cuadro igual al primero (bucle).

## Motor

- `herramientas/movimiento.js`: `pulsos(bpm, inicio)`, curvas con nombre (`expo`, `backSuave`…),
  **resortes en forma cerrada** (un valor que cambia de destino muchas veces es la suma de un resorte por
  cambio: sigue siendo función pura del tiempo), `formas` (círculo, polígono, estrella, rectángulo redondo,
  240 puntos cada una) y `morph` punto a punto.
- Todo se calcula desde `t` dentro del dibujo: nada de transiciones CSS, temporizadores ni estado entre cuadros.
- Los dos bordes de un indicador (pestañas, interruptor) con resortes distintos: el de adelante se estira antes.

## Pasos

1. Lista de 8–12 estados de la app **reales** (del repositorio del producto) puestos en la grilla de pulsos.
2. Música:
   - `musica.json` con los eventos (un `clic` por clic, `pop`, `whoosh`, `impacto` en el logo) → `musica.py`
     da `musica.wav` + `pulsos.js`;
   - con canción real: `.venv/Scripts/python herramientas/cancion.py recursos/musica/<cancion>.mp3 28` da BPM,
     primer tiempo y energía por compás; `herramientas/pista.py <carpeta> recursos/musica/<cancion>.mp3 [--golpe P]`
     elige el tramo para que la mayor subida caiga en el golpe del video y pone un efecto real del banco en cada
     evento (→ `pulsos.js` con el BPM de la canción, `mezcla.json`, `mezcla.wav`). **Medir la subida** (la
     energía se duplica) y la fase antes de fijarla.
3. Dibujar estado por estado; revisar una hoja de cuadros por pulso antes de exportar: capturas en los pulsos
   clave (`navegador.py capturas <carpeta> t1,t2,…` con `t = inicio + pulso·60/bpm`) y `hoja.py`.
4. `VIDEOS_PARAMS="fps=60&sub=4" .venv/Scripts/python herramientas/navegador.py exportar <carpeta>` →
   `render/08-lanzamiento_<producto>.mp4` y `saltos.py` sobre el MP4 (los cortes en pulsos con golpe, a
   propósito, van en `--cortes`).

## Receta (lo que tiene que tener para verse de estudio)

- **El mismo elemento de principio a fin**: una lista de claves de tamaño, radio y color con resortes; el primer
  valor es el de reposo, así el cuadro 0 no se mueve y el último es igual al primero.
- Fondo claro con la forma en un color fuerte y **un solo** acento.
- **Cámara que se acerca a cada estado** (zoom con resortes), **cursor de tamaño fijo en pantalla** con clics y
  arrastres, contenido que cambia con un desenfoque corto dentro de la forma.
- Rótulos de una línea que **suben desde su máscara**; nunca «título a la izquierda + tarjeta a la derecha»
  (es la plantilla que delata un video hecho por IA).
- **Inundaciones**: la forma sobrepasa las esquinas (~0,3 s) y se contrae en el estado siguiente, una o dos
  veces, en la subida de la canción.
- Indicador de pestañas con dos bordes de resortes distintos; un texto que cambia rueda como un contador dentro
  de una ventana fija (si entra y sale por opacidad, se encima).
- Frase final con **tipografía variable** (p. ej. peso 300 → 600).
- Un efecto real por clic, pop y whoosh en su pico medido; 60 fps con 4 subcuadros.
- **Antes de la película**: mapa de pulsos + 4 cuadros fijos aprobados por quien dirige.
- Falta probar aquí: vidrio líquido y goo (ver «Efectos de estudio» en `video-lanzamiento`).

## Lo que falló

- Texto resaltado (una @mención) se dibuja por partes, no encima: quedaba impreso dos veces.
- Medir el texto de botones con `measureText` y dejar margen (el texto de un botón se salía de la caja).
- Texto que cambia dentro de una forma que se transforma necesita su propia entrada y salida, o se encima.
- Contadores con `t` redondeado al cuadro (`Math.round(t*30)/30`): con desenfoque salían dobles.
- Rebotes mínimos (amortiguación ≥ 0,6); sin destellos ni degradados en la interfaz.
- La primera versión no era una sola forma (tarjetas que entraban por opacidad): se rehízo con la receta.

## Verificar

- Hoja de cuadros por pulso: la forma nunca se corta ni desaparece; ningún texto encimado ni fuera de su caja.
- Cuadro 0 = último cuadro (si hay bucle); `saltos.py` sin defectos fuera de `--cortes`.
- Cada estado mostrado existe en la app real.

## Herramientas externas (opcional)

- **Mixkit** (canción y efectos, licencia gratuita de Mixkit) y **Kenney** (clics de interfaz, CC0); bajar a
  `recursos/`.
- **No conviene**: generar la interfaz con imágenes (los estados tienen que ser los reales del producto) ni
  generadores 3D (es 2D). Para mostrar la app de verdad, técnica 15.
