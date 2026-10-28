---
name: video-maquina-isometrica
description: Técnica 26. Explica un concepto técnico inventando una máquina isométrica cuyo funcionamiento ES el concepto (una caché = una cajonera chica junto al servidor con un reloj de arena; un índice = un fichero con pestañas), dibujada pieza por pieza en Canvas 2D (40 a 150 piezas, tonos por cara, un solo acento encendido), en estilo claro editorial o en oscuro donde lo encendido brilla; y, en 3D real (`iso3d.js`), sólidos biselados con luz y cámara isométrica verdadera, o un `.glb` propio limpiado y restilizado (`iso3d.py glb`). La misma escena sirve de video (cada cuadro es render(t), con narración, subtítulos y efectos por contacto) y de interactivo (?explorar=1 - girar, tocar piezas, accionarlas), y se entrega como paquete de código para que otra aplicación (una pizarra, una plataforma de cursos) la monte. Usar para «cómo funciona» de sistemas, algoritmos, protocolos y productos, e instrumental o implantes en los médicos. No para personas, emociones ni hueso real.
---

# Máquina isométrica (técnica 26)

Antes: leer **`director-de-video`** (y `director-educacion` si es para estudiar). Ejemplo (no publicado; los
comandos de abajo lo llaman `26-maquina-isometrica/cache`): «¿Cómo funciona una caché?» (65 s, 1920×1080, voz local Kokoro,
87–90 piezas). Origen: la skill Anatomy (`wheresryan22/anatomy`, MIT) y la variante oscura de ISO-GLOW (isoglow.dev, MIT).
**De ninguna se copió código**: se tomaron
las ideas y las guardias, reescritas para nuestro canvas (`herramientas/iso.js`, `herramientas/maquina_iso.py`).
La diferencia con ellas: Anatomy e ISO-GLOW hacen figuras para una página y se mueven con el reloj real; aquí cada cuadro
es una **función pura de `t`** (nada de `Date.now`, `performance.now`, `setTimeout` ni `Math.random` sin semilla en el
video), hay voz, subtítulos y sonido, y la misma escena también se manipula.

## Cuándo sí y cuándo no

| Sí | No |
|---|---|
| Un sistema con partes que se pasan algo (caché, cola, índice, balanceador, DNS, un compilador) | Personas, emociones, historias (→ dibujo animado, collage, Blender) |
| Un algoritmo con estado visible (cajones, fichas, rieles, contadores) | Hueso o anatomía real (→ `video-medico`: BodyParts3D) |
| Instrumental o implante en un médico (la placa, el tornillo, la guía), nunca el cuerpo | Datos con muchas cifras que comparar (→ cálculo real, datos y mapa) |
| «Cómo funciona» de un producto (p. ej. cómo Libreta sincroniza las notas) | Algo que no tiene mecanismo: si no hay una máquina que lo sea, no se fuerza |

## El método (en este orden; la mitad de la calidad se decide antes de la geometría)

1. **Dimensionar** y decirlo antes de empezar: **Figura** (un mecanismo, 40–80 piezas, ~1–2 h de agente), **Héroe**
   (80–150 piezas, varias estaciones, ~3–5 h), **Épica** (planta o vehículo entero: no se empieza; se propone un Héroe con
   el núcleo y se lista lo que agregaría). A la hora, la página ya abre y se mueve.
2. **Cifras reales primero**, en `hechos.md`: cada dato con su fuente leída (no de memoria), lo aproximado rotulado
   («≈», «no va a escala»). Las cifras de pantalla salen del mismo modelo que mueve las piezas.
3. **Inventar la máquina**: una cosa que se podría construir y cuyo movimiento **es** el concepto. Decir en una frase qué
   se mueve y qué significa. Malos: cajas con flechas, losas apiladas, una losa grande con rayas. Ejemplos:

   | Concepto | Máquina |
   |---|---|
   | Caché (acierto, fallo, expiración) | Vía con un carro-pedido; cajonera chica junto al servidor con reloj de arena; archivo grande con disco al fondo |
   | Clave de caché que evita trabajo (Anatomy) | Cerradura de pines: si todos calzan, el tambor gira |
   | Cola de mensajes | Cinta con bandejas y un brazo que toma la primera |
   | Índice de base de datos | Fichero con pestañas de letras frente a un archivo sin orden |
   | Balanceador | Distribuidor de canicas con compuertas a varias canaletas |

4. **Lista de piezas (≥ 40) antes de dibujar**, agrupada: base (mesa, patas, zapatas, ranura, tornillos, regla, placa con
   rótulo), estructura (rieles, durmientes, topes, tapas, costuras), mecanismo (carro, asiento, mástil, cajones, bandejas,
   brazo), controles (botón, manija, luces) y el **sujeto** (lo que se explica, tono `hi`). Cada pieza se apoya en otra.
5. **Plano del mundo**: unidades ≈ px de la cosa real, x e y en el piso, z arriba. Cámara isométrica (elevación fija;
   `giro` = azimut): 0 da los ejes a ±30°; **girar 20–30°** pone de frente la cara que trabaja (la caché usa −25°: la vía
   casi horizontal, que llena el 16:9). Encuadre automático: los puntos extremos (con su altura) en un rectángulo.
6. **Dibujar con `herramientas/iso.js`** (Canvas 2D, sin dependencias): `E.caja`, `E.cilindro`, `E.tubo` (cables de tramos
   paralelos a los ejes con codos de bola y collarín en cada punta), `E.pieza` (brazo, aguja), y dentro de `detalle()`
   `E.linea`, `E.contorno` (ranuras y rejillas cerradas: no tienen puntas), `E.punto` (tornillos), `E.textoEnCara` (el
   número grabado en una placa). `E.pintar(ctx)` **ordena solo** (cajas separables, de atrás hacia adelante): no se
   ajusta el orden a ojo. Lo que se mueve se rearma en cada cuadro en su lugar.
7. **Movimiento por `t`**: un modelo puro, `simular(eventos, ttl)` → viajes con sus fases y copias con su vencimiento, y
   `estado(t, sim)` → posición del carro, apertura de cajones, tarjetas en tránsito (`camino(pts, k)` por largo de arco).
   El video pasa los eventos atados a las frases (`tiempos.js`); el modo explorable pasa los que genera quien toca. Curvas
   suaves, sin fundidos; lo que entra a un cajón se **recorta en la boca** (como un vástago que sale de su guía), no aparece.
   La pantalla nunca queda quieta: el disco gira, la arena cae, la cámara deriva ±2° en 40 s.
8. **Narración y sonido**: `guion.json` → `narrar-guion` (voz **local**; nada pago sin el OK del usuario). Sin música de
   fondo: efectos **por contacto** que salen del mismo modelo (`escena.efectos()` → `maquina_iso.py efectos` →
   `efectos.json` → `mezclar.py`, −14 LUFS): el carro toca la parada, el cajón se abre, la tarjeta cae.
9. **Textos fuera del dibujo y composición**: titular arriba a la izquierda, una línea de «momento» por frase (entra
   barriendo, sin fundido) y, en horizontal, una **columna a la derecha** con la leyenda de las placas (1 cliente,
   2 servidor…), el contador, la última latencia y la nota de fuentes, a la altura media del cuadro: la máquina va a la
   izquierda y la columna equilibra el cuadro. Nada de una tarjeta chica en una esquina con media pantalla vacía.
   **Tamaños mínimos a 1080p (se mira en un teléfono)**: titular ≥ 56 px, momento ≥ 34, leyenda y contador ≥ 28 (el
   ejemplo usa 32 y 30), nota de fuentes ≥ 20 (el ejemplo, 22); una línea que no cabe en la columna se parte en dos, no
   se achica. En el dibujo sólo los números grabados. Subtítulos con `Reproductor.subtitulos`, subidos 40 px para
   quedar en el 90 % central.
10. **Verificar** (abajo) y, si la carga de la PC lo permite, exportar con `exportar-video`.

## Oficio (de Anatomy, para canvas)

- **Sólidos, no alambres**: cada cara se rellena; lo de adelante tapa lo de atrás. Nada de aristas ocultas punteadas.
- **Tonos**: base `lo`, estructura `mid`, sujeto `hi`, y **un solo `lit`** (el acento): la pieza que hay que mirar ahora.
  En el video el acento es el pedido cuando viaja; quieto, la pieza de la que habla la voz (`focoVideo`).
- **Una luz fija** decide el tono de cada cara (y el degradé del costado de los cilindros: sin escalones).
- **Toda línea termina en algo**: borde, punto, otra línea o la pieza que toca. Una costura va de arista a arista, las marcas
  cuelgan del borde de la regla, rejillas y ranuras son contornos cerrados. Libres sólo los rótulos (`libre: true`) y la
  punta de una aguja o brazo (`libre: 'fin'`).
- **Ningún cable atraviesa nada**: rutas ortogonales junto a la estructura, por encima de lo que cruzan, con `toca` para
  sus dos puntas.
- **Detalle con propósito**: ranura, tornillos en las esquinas, regla con marcas mayores cada 5, placa con tres renglones,
  costuras, manijas, luces. A 1× se lee una máquina; a 4× cada región tiene algo verdadero.

## Estilos

| | Claro editorial (Anatomy) | Oscuro con brillo (ISO-GLOW) |
|---|---|---|
| Fondo / línea | papel `#f3f0e8`, tinta | casi negro `#0b0e13`, línea fina clara |
| Acento | la pieza en tinta llena (sin color) | la pieza en ámbar con resplandor (`shadowBlur`) |
| Cuándo | documentos, clases, lo que se imprime | reels, aperturas, «lo que está encendido» es el tema |

Los dos son el mismo dibujo con otro juego de tokens (`Iso.TEMAS`); se elige con `&tema=claro`. **Vertical (1080×1920)**:
la misma escena con el lienzo vertical, `RECT_VIDEO` alto y angosto y `giro` cercano a 0 o a 90° (la vía en diagonal ocupa
el alto), tarjeta de cifras abajo del dibujo y subtítulo encima de ella; el encuadre es automático. (El ejemplo es horizontal;
el vertical está **no demostrado**.)

## Doble modo: video e interactivo con el mismo código

`escena.js` expone `Escenas.<nombre>.crear(canvas, { tema, tiempos })` → `{ duracion, render(t), explorar(), registro(t),
efectos(), ficha() }`. `index.html` sólo la monta: sin parámetros, `Reproductor` + subtítulos; `?explorar=1`, arrastrar
gira (escala fija, la menor de todas las vueltas, para que no salte), tocar una pieza muestra qué hace y algunas la accionan
(el botón manda un pedido, el reloj vence la copia), teclas P, E, ← → y R. En el modo explorable el reloj real sólo genera
**eventos**; el cuadro sigue siendo `estado(t, simular(eventos))`, así que lo que se ve se puede repetir.

## Variante 3D real (ISO-GLOW 3D): `iso3d.js`

Mismo contrato (cada cuadro es `render(t)`, función pura de `t`; el ejemplo lleva voz, sonidos por contacto, vertical y modo
explorable) pero con **sólidos 3D
iluminados** en vez de caras dibujadas a mano: three.js local (r170, sin descargar nada), cámara ortográfica **isométrica verdadera**
(45° / 35,264°, `Mundo.camara({ az, el })`; se puede girar y el ajuste «Iso view» vuelve a la exacta), piezas con bisel y contorno
(`caja`, `cilindro`), **un solo acento** que brilla (`acentuar(geo)`; el resplandor se suma borroso, ancho y fino) y rótulos 2D
encima. Ejemplo (no publicado; abajo, `26-maquina-isometrica/glow-indice`): «Un índice» (archivero de seis cajones y una sonda; 14 s sin voz, 421
cuadros exportados en 59 s; **con voz 33,2 s**). Se hace con la **receta de la técnica** (cifras primero, inventar la máquina, tabla de tomas con
`tabla_tomas.py`); lo que cambia es el motor.

**Voz, vertical y explorable en 3D**, todo con la misma `escena.js`: (1) **voz**: `guion.json` → `narrar.py` → `tiempos.js`; la escena
lee los tiempos (`tiemposDe(TIEMPOS)`: cada fase arranca con su frase y el paso de la sonda se ajusta para llegar justo a la siguiente), los sonidos
salen de la propia escena (`esc.efectos()` → `iso3d.py efectos <carpeta>` → `efectos.json`, 1 cuadro después de la imagen) y `mezclar.py` arma
`mezcla.wav`; sin música. (2) **vertical**: `?formato=vertical` pone el lienzo en 1080×1920 (cámara más cerrada, título arriba, contador y
subtítulo abajo; la página dibuja su propio subtítulo de ≤ 38 letras). (3) **explorable**: `?explorar=1` pone dos botones que accionan la
búsqueda («sin índice» abre cajones hasta el buscado; «con índice» abre uno), un selector del cajón buscado y arrastrar para girar; el contador y
la tabla «sin índice: N · con índice: 1» salen del mismo `poner(t, c)` del video.

| Cuándo 2D (`iso.js`) | Cuándo 3D (`iso3d.js`) |
|---|---|
| 40–150 piezas con guardias de líneas, orden y cruces; claro editorial o impreso; paquete de código ya listo para otra aplicación | Pocas piezas grandes con volumen, luz y giro de cámara; apertura o reel oscuro con brillo; **un `.glb` propio** que hay que limpiar |

**Un `.glb` propio, limpio y restilizado** (`herramientas/iso3d.py glb <archivo.glb> [--acentos "regex"] [--objetivo 4]`; el visor del
ejemplo, no publicado, es `26-maquina-isometrica/glow-glb/index.html?glb=<ruta>&acentos=<regex>&giro=1&suave=0`): lee el `.glb` con un lector propio (nodos con
traslación, giro y escala; índices de 16 o 32 bits; **sin** Draco ni meshopt: lo rechaza y dice que se descomprima en Blender), suelda
vértices repetidos, quita triángulos degenerados, tira texturas y materiales, centra, lo apoya en y = 0 y lo escala a `objetivo`
unidades. Las mallas cuyo nombre (`nodo/malla`) coincide con `--acentos` quedan encendidas. Probado con un `.glb` armado aquí (respuesta
conocida) y con uno real con textura (el pato de Khronos: 2.399 → 2.108 vértices, 1 textura tirada). **Límites**: una pieza orgánica
lisa marca pocos bordes (`&suave=0` los marca más); un modelo de 50 MB como los personajes de Hunyuan tarda y pide decimar antes en Blender;
**no es para personas ni hueso real** (esos van por `video-medico`).

```
.venv/Scripts/python herramientas/iso3d.py --probar     # 15 casos (12 con 17 mutaciones atrapadas + efectos, vertical y explorable); lee el ejemplo glow-indice y el visor glow-glb
.venv/Scripts/python herramientas/determinismo.py 26-maquina-isometrica/glow-indice --instantes 1,4.3,9.5,12
.venv/Scripts/python herramientas/navegador.py exportar 26-maquina-isometrica/glow-indice     # 14 s → render/…mp4
.venv/Scripts/python herramientas/verificar_export.py 26-maquina-isometrica/glow-indice       # ¿el MP4 es el video de la página?
```

| Guardia (`iso3d.py --probar`) | Qué exige |
|---|---|
| `lector` · `limpieza` · `comprimido` · `acentos` | el `.glb` sale con la misma caja que calcula numpy con las mismas matrices; 48 → 16 vértices y 26 → 24 triángulos en el fixture; Draco rechazado con mensaje; sólo se enciende lo pedido |
| `un-acento` | exactamente una pieza encendida en cada instante (cada 0,25 s) |
| `encuadre` | ninguna pieza visible sale del cuadro (el ejemplo y el `.glb` dando la vuelta) |
| `isometrica` | la vista termina en 45° / 35,264° exactos y la guardia ve la diferencia cuando no lo es |
| `resplandor` | alrededor de lo encendido hay más luz con el resplandor que sin él (+9 niveles de gris en el anillo) |
| `determinismo` | el cuadro no depende del orden en que se piden |
| `efectos` · `encuadre (vertical)` · `explorable` | cada sonido cae dentro del video y en orden; nada visible sale del cuadro de 1080×1920; los botones accionan (sin índice abre 5 y 2 cajones según el buscado, con índice abre 1) |

Lo que falló al hacerlo (trampa → arreglo): el acento salía amarillo casi blanco (resplandor sumado dos veces: brillo .5 y color
`#ff8a1f`); la máquina quedaba chica, cortada abajo y bajo el texto (mover el punto mirado, no el zoom; la ficha detrás); `evaluate`
con dos argumentos los pasa en una lista, y una función `(t, b)` los recibe mal (`([t, b])`); dos Playwright a la vez fallan (uno solo
compartido); mutando el lector, el caso «lector» seguía en ok porque comparaba el tamaño y no la caja entera (ahora compara los dos
extremos). **Pendiente**: el paquete de código aún sólo existe para 2D (`maquina_iso.py paquete`); el 3D necesitaría
llevar `three.module.min.js` (690 KB) y WebGL en el navegador del alumno, y eso se mide antes de ofrecerlo; crítico ciego sobre el MP4:
se corre al exportar la pieza con voz. En el vertical y el explorable salió un tropiezo de prueba, no de escena: `select_option("select", "1")`
de Playwright calza «1» con el **texto** de la primera opción antes que con el valor (elige el cajón 1, no el 2): usar `index=`.

## Páginas de Anatomy tal cual (camino A)

Un ejemplo de Anatomy (o de cualquier página que anime con el reloj real: `requestAnimationFrame`, `setTimeout`, animaciones CSS) se
graba **sin reescribirlo** con `herramientas/grabar_reloj.py <url> <salida.mp4> --selector .iso-figure`: congela y adelanta el reloj del
navegador cuadro por cuadro (4 grabaciones idénticas del `dial-indicator`, `--probar` 3 ok). Es lento (13,2 s tardan 2 min 49 s) y no
trae audio. Sirve para meter una figura de Anatomy en un video tal cual; si hace falta voz, subtítulos o `?explorar=1`, se rehace con
`iso.js` o `iso3d.js` (camino B).

## Paquete de código para otra aplicación

Una aplicación que muestra la escena (una pizarra de clases, por ejemplo) recibe **código, no video**, y renderiza cada escena por separado. `maquina_iso.py paquete <carpeta>` arma
`render/paquetes/<técnica>_<video>/`: `escena.js` + `lib/iso.js` (la escena y su única dependencia), `tiempos.js` y
`guion.json` (frases con inicio y duración), `narracion.wav` (voz sola) y `mezcla.wav` (voz + efectos), `subtitulos.vtt`
(aparte, para que la pizarra los ponga a su modo o con adecuaciones), `efectos.json`, `hechos.md` (fuentes) y
`manifiesto.json` (técnica, skill, contrato, lienzo, duración, temas, leyenda de colores y la lista de frases).
Para cargarla, la pizarra necesita: un `<canvas>` (1920×1080 o el que pida el manifiesto), cargar `lib/iso.js`, `tiempos.js`
y `escena.js` como scripts clásicos (sin módulos ni red), llamar `Escenas.<nombre>.crear(canvas, { tema, tiempos })` y
después **o** `render(t)` en su propio bucle con su reloj de audio (escena narrada) **o** `explorar()` (escena para
manipular; devuelve `detener`). Nada de la escena llama a la red ni guarda estado entre cuadros. El contrato es éste; la
integración la hace la aplicación que lo recibe.

## Verificar (todo por terminal; «ok»/«FALLA» por caso)

```
.venv/Scripts/python herramientas/maquina_iso.py --probar                         # 23 casos: cada guardia, rota a propósito
.venv/Scripts/python herramientas/maquina_iso.py auditar 26-maquina-isometrica/cache [--instantes …] [--params tema=claro]
.venv/Scripts/python herramientas/maquina_iso.py cerca 26-maquina-isometrica/cache --t 27.9      # primeros planos a 4×
.venv/Scripts/python herramientas/determinismo.py 26-maquina-isometrica/cache --instantes 0,12,25.8,27.9,33.1,48.9,57.4,64
.venv/Scripts/python herramientas/navegador.py capturas 26-maquina-isometrica/cache 3,12,25.5,33,47.5,49
.venv/Scripts/python herramientas/hoja.py 26-maquina-isometrica_cache
```

| Guardia (`auditar`) | Qué exige |
|---|---|
| `lineas` | ningún extremo en el aire (borde, punto, otra línea, pieza que toca, o tapado por algo dibujado después) |
| `orden` | donde dos siluetas se pisan y una cara de separación dice cuál está detrás, ésa se dibujó antes |
| `cruces` | ninguna pieza ni cable se mete > 0,5 unidades en otra; el orden no tiene ciclos |
| `acento` | un solo grupo encendido por cuadro |
| `texto90` · `encimados` · `sobre` | texto en el 90 % central; ningún texto pisa otro (el subtítulo cuenta) ni pisa el dibujo, salvo el grabado en su placa |
| `piezas` | ≥ 40 piezas distintas (un cable cuenta una vez) |

Instantes: los de `auditar` por omisión (70 % de cada frase) **más** los de cada fase de un viaje (tarjeta en tránsito,
cajón abierto, copia a la papelera). Los **primeros planos a 4×** (`cerca`) eligen solos las puntas de cables, los codos y
el acento: se mira la hoja entera, junta por junta (no lo juzga una máquina). Cada guardia se probó rompiendo la escena a
propósito, una mutación por guardia (9 de 9 atrapadas). Después del MP4: `verificar_export.py` y el crítico ciego (`exportar-video`).

## Lo que falló (trampa → arreglo)

| Trampa | Arreglo |
|---|---|
| El primer cuadro de cada página salía distinto (media 0,45) con `willReadFrequently: true` | Lienzo 2D sin esa opción: 8 de 8 instantes idénticos |
| Postes del reloj de arena 4 unidades dentro de la tapa (a ojo no se ve) | `cruces` lo encontró; postes a la altura exacta |
| Los números de las placas al pie de cada estación quedaban tapados por el mástil del carro | Placas en la tapa de cada estación (`sobre` exige que el grabado quepa en su placa y nada lo tape) |
| La caja del subtítulo llegaba a y = 1042 (fuera del 90 %) | Subtítulo subido 40 px y su caja real medida con la misma partición que `reproductor.js` |
| Primera hoja: máquina cargada a la izquierda, mitad derecha vacía y leyenda a 20–26 px (ilegible en un teléfono) | Columna de cifras a la derecha, a media altura, a 28–32 px; la nota de fuentes a 22 |
| Los collarines y la punta del cable «se atravesaban» | El cable declara `toca` y sus sólidos lo heredan |
| Playwright: `evaluate(expr, [t])` pasa una lista; `[21.5]` funciona por casualidad, `[[t, x, y, z]]` no | Un argumento solo va solo; varios, en una lista |

## Nivel de estudio (lo que falta)

- Más densidad de Anatomy en el sujeto (perillas moleteadas, resortes partidos atrás/adelante, guías con bujes).
- Superficies curvas mayores (lathe) y sombras de contacto en 2D (en 3D ya hay luz real: `iso3d.js`).
- Un ejemplo 3D con voz, subtítulos y tabla de tomas (el actual es mudo y de 14 s) y una máquina de 40+ piezas en 3D.
- Sonido en el modo explorable (WebAudio con los mismos eventos) y un ejemplo vertical.
- Crítico ciego sobre el MP4 (no corrido en el ejemplo).
