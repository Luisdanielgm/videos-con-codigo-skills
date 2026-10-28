---
name: video-forma-unica
description: 'Técnica 8. Comercial de app (25–30 s) donde UNA sola forma recorre todo el video sin cortes y se vuelve cada pantalla o componente (botón, lista, chat, toggle…), con cursor, cámara que acerca y bucle, en Canvas 2D, sobre la grilla de una canción real con efectos reales. Usar para lanzamientos de apps con interfaz.'
---

# Forma única que se transforma (técnica 8)

Antes: leer la skill base **`video-lanzamiento`** (material verdadero, plan en pulsos, música, reglas,
dirección). Ejemplo: `08-lanzamiento/libreta/` (una app de notas inventada, con música calculada por
`musica.py`: `index.html` + `musica.json` + `pulsos.js`; **leerlo entero**). Con canción real se suma `mezcla.json`
(`pista.py`).
Referencia: el prompt de motion design de @twoclipping en X (una forma que nunca se corta, cursor con clics y
arrastres reales, cámara que acerca, el último cuadro igual al primero).

## Qué hace falta

- El entorno `.venv`, ffmpeg y Chrome.
- Una canción libre cerca de 120 BPM (p. ej. de Mixkit, en `recursos/musica/`) y el banco de efectos
  (`recursos/efectos/listos`, ver README). Sin ellos, `musica.py` calcula música y efectos (respaldo).
- Los estados reales de la app: capturas o el código de su interfaz (nunca inventados).

## Idea

Un solo elemento que nunca se corta: cambia tamaño, radio y color mientras su contenido se cambia con su
propia máscara (sube, se desliza o se disuelve), sin desenfoque de entrada: la base de los comerciales lo
prohíbe (el ejemplo publicado todavía usa un desenfoque corto). Un cursor maneja cada cambio (clics, arrastres). La cámara se acerca para que cada estado
llene el cuadro. Si se puede, el último cuadro igual al primero (bucle).

## Motor

- `herramientas/movimiento.js`: `pulsos(bpm, inicio)`, curvas con nombre (`expo`, `backSuave`…),
  **resortes en forma cerrada** (un valor que cambia de destino muchas veces es la suma de un resorte por
  cambio: sigue siendo función pura del tiempo), `formas` (círculo, polígono, estrella, rectángulo redondo,
  240 puntos cada una) y `morph` punto a punto.
- Todo se calcula desde `t` dentro del dibujo: nada de transiciones CSS, temporizadores ni estado entre cuadros.
- **Un resorte por cada cambio de objetivo** (la suma de arriba): si el destino cambia a mitad de camino, se
  agrega un cambio `[pulso, destino anterior, destino nuevo]`; nunca se reinicia el resorte ni se salta el valor.
- **Cada borde en su propio resorte** (izquierdo, derecho, arriba, abajo; no un centro y un ancho): en un
  indicador (pestañas, interruptor) el de adelante sale antes y el de atrás lo alcanza, y la forma se estira sola.
- **Rebote < 2 %** (`amort ≥ 0,78`).

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
  arrastres, contenido que cambia con su propia máscara dentro de la forma.
- Rótulos de una línea que **suben desde su máscara**; nunca «título a la izquierda + tarjeta a la derecha»
  (es la plantilla que delata un video hecho por IA).
- **Inundaciones**: la forma pasa las esquinas en ~0,3 s (crece más allá de la diagonal del cuadro, no sólo
  hasta los bordes) y se contrae en el estado siguiente, una o dos veces, en la subida de la canción.
- **Nunca de negro (o del fondo) al color de acento con un fundido**: el acento entra porque un elemento de ese
  color se mueve y lo cubre todo (la forma, una inundación).
- **La máscara de la palabra que entra sale del contorno de la que se va**: el rótulo nuevo se recorta dentro
  de la caja del anterior y crece desde ahí, así el texto también es una sola toma.
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
- Contadores con `Reproductor.cuadro(t)` (el instante del cuadro, igual en sus subcuadros): con desenfoque
  salían dobles, y redondear a 1/30 no alcanza a 60 fps.
- Rebotes: con amortiguación 0,6 se notaban (~9 %); ver «Motor». Sin destellos ni degradados en la interfaz.
- La primera versión no era una sola forma (tarjetas que entraban por opacidad): se rehízo con la receta.

## Verificar

- Hoja de cuadros por pulso: la forma nunca se corta ni desaparece; ningún texto encimado ni fuera de su caja.
- Cuadro 0 = último cuadro (si hay bucle); `saltos.py` sin defectos fuera de `--cortes`.
- Cada estado mostrado existe en la app real.

## Lecciones del crítico ciego sobre «Libreta»

Primera pasada: congelado 9,9 s cada 30 s, tarjeta final quieta 3,7 s, destello gris, cursor sobre un rótulo.
- **La cámara nunca se detiene**: multiplica el zoom por una deriva `1 + 0,03·sin(2π·t/DUR)` (vale 0 en el primer y
  el último cuadro: el bucle sigue empalmando). Con eso ningún tramo queda «quieto» para `critico.py`; los holds
  largos (la tarjeta final) además llevan movimiento propio del logo cada 4 pulsos (respira, renglones que se
  escriben, peso variable) y, antes del golpe, el punto se comprime (anticipación).
- **Una inundación no se mezcla de color a pantalla llena**: el resorte de tamaño cubre el cuadro en ~0,07 s, así que
  un cambio de color de 0,3 s deja un cuadro entero gris. Dale a la inundación su propio `hz` (≈1,1: ~0,25 s hasta
  pasar las esquinas), cambia el color al empezar (`cd` ~0,1 s, forma aún chica) y, al contraerse, espera a que la
  forma quepa en el cuadro (`cs` ~0,1 s) antes de mezclar. Un objeto del siguiente estado (la campana) nace grande
  dentro de la inundación y se encoge a su sitio: así la pantalla oscura no queda sin contenido.
- **El cursor llega desde fuera del texto**: su posición de entrada no puede caer sobre un rótulo ni sobre una
  palabra; revisa el punto de partida (visible) y no sólo el destino.
- **«La interfaz ocupa poco»**: zoom por estado para que la forma llene 60–80 % del alto, con desplazamiento
  vertical por estado (`dy`) y rótulos en espacio de pantalla (tamaño fijo, siguen al borde de la forma y se
  sujetan a 100–985 px) en vez de a tamaño de mundo. Lo que sale «desde arriba» (un aviso) se coloca con el zoom final.
- **Exportar por partes**: `VIDEOS_PARTE` sólo nombra el marcador; para que el MP4 parcial no pise al completo hay
  que pasar `parte=<nombre>` también en `VIDEOS_PARAMS` (si no, `render/<video>.mp4` queda reemplazado por el tramo).
- **Primeros cuadros en negro** (visto en dos comerciales con la máquina cargada: 19–22 cuadros negros tras el
  cuadro 0): el cuadro 0 de la página es correcto (captura y exporte corto de 1 s salen bien); el fallo es del
  exporte y no se reprodujo, así que no se arregla en la página (un calentamiento con `render(0)` + `toBlob` antes
  de `Reproductor.iniciar` se probó y además rompía la repetibilidad de los cuadros). Mira siempre los primeros 40
  cuadros del MP4 y reexporta si salen negros.
- **Texto de más de ~160 px en pantalla no es repetible**: la marca a 150 px × zoom 1,4–1,9 (con un empuje lento
  de cámara) salió distinta entre dos exportaciones iguales (47 de 170 cuadros, ≤ 2/255 en los bordes de las letras),
  mientras que a 150 px sin zoom el original era idéntico (0 de 170). Deja el texto de marca ≤ 155 px en pantalla
  (zoom base 1 en la tarjeta final, con la deriva de ±3 %); el zoom lento de esa tarjeta se descartó por eso.
  Prueba la repetibilidad: dos pasadas de `navegador.py capturas` con los mismos instantes y `md5sum`.

## Tipografía en movimiento: números de `kinetic-typography-skills` (`iart-ai`, MIT)

- Primero la tipografía **quieta**: interlineado 1,1–1,2 en títulos (1,4–1,6 en texto), espaciado de letras −1 % a −3 %
  en títulos grandes, alineación y peso fijados antes de animar; el movimiento no rescata una tipografía mala.
- **Granularidad**: por línea = lo más sereno y caro (titulares largos); por palabra = enérgico (eslóganes, letras de
  canción); por letra = lo más cinético y sólo para cadenas cortas. Escalonado: líneas 60–100 ms, palabras 40–70 ms,
  letras 20–40 ms; duración de cada fragmento 400–600 ms y el revelado total ≲ 800 ms (en cadenas largas, subir de
  granularidad en vez de alargar).
- **Máscara que sube** (cada línea en una caja recortada y el texto sube desde su línea base) es el revelado más robusto
  y barato; desenfoque a nitidez es suave pero caro (radio chico, duraciones cortas); el barrido por recorte revela sin mover glifos.
- **Peso variable** animando el eje (`font-variation-settings`, no `font-weight`), y comprobar que la fuente cargada sí
  es variable y trae ese eje.

## Herramientas externas (opcional)

- **Mixkit** (canción y efectos, licencia gratuita de Mixkit) y **Kenney** (clics de interfaz, CC0); bajar a
  `recursos/`.
- **No conviene**: generar la interfaz con imágenes (los estados tienen que ser los reales del producto) ni
  generadores 3D (es 2D). Para mostrar la app de verdad, técnica 15.
