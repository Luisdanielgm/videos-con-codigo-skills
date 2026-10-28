---
name: video-showreel
description: 'Técnica 13. Showreel vertical para reels (1080×1920, ~17 s) de ocho escenas de un compás - letras que golpean, frases, forma que se transforma con palabras, cubo de alambre con una cifra, marquesinas, ráfaga, logo con glitch y cierre con la URL (herramientas/showreel.js). Usar para Instagram/TikTok - sólo palabras, colores y logo.'
---

# Showreel vertical (técnica 13)

Antes: leer la skill base **`video-lanzamiento`**. Ejemplo: `13-showreel/libreta/` (una app de notas inventada):
su `index.html` tiene unas 25 líneas, sólo la configuración; el motor es `herramientas/showreel.js`.

## Qué hace falta

- El entorno `.venv`, ffmpeg y Chrome. El logo en PNG (con permiso de la marca) y los textos del producto.
- Para la canción real: una canción libre en `recursos/musica/` y el banco de efectos (README).

## Motor

```
Showreel.video({canvas, colores, logo, nombre, gancho, sub, lineas, formas, numero, marquesina, rafaga, cierre, url})
```
Ocho escenas de un compás cada una (gancho, frases, forma que se transforma, cubo con una cifra, marquesinas,
ráfaga, logo con glitch, cierre). Esqueleto:

```html
<canvas id="c" width="1080" height="1920"></canvas>
<script src="pulsos.js"></script>
<script src="../../herramientas/movimiento.js"></script>
<script src="../../herramientas/reproductor.js"></script>
<script src="../../herramientas/showreel.js"></script>
<script>
Showreel.video({ canvas: document.getElementById('c'),
  colores: { fondo: '#101418', acento: '#ffcc33', acento2: '#3fa7ff', texto: '#ffffff' },
  logo: 'marca/logo.png', nombre: ['Nota', 'Fácil'], gancho: ['¿DÓNDE', 'ANOTASTE', 'ESO?'], sub: 'una app de notas',
  lineas: ['Escribe', 'Encuentra', 'Comparte'], formas: ['rápida', 'simple', 'tuya', 'gratis'],
  numero: { valor: 1200, etiqueta: 'notas de ejemplo' }, marquesina: 'NOTAFÁCIL',
  rafaga: ['Todo lo que anotas, a mano', 'En el teléfono y en la web'], cierre: 'Anota una vez.', url: 'notafacil.example' });
</script>
```
El prompt viral que lo originó: «showreel de 15 s que muestre qué increíble motion designer eres… go all out»,
cambiando «résumé» por el producto.

Opciones del arreglo del crítico (todas apagadas por omisión; detalle en la cabecera de `herramientas/showreel.js`):
`ganchoTerminado:true` (cuadro 0 con el titular terminado, letras que golpean), `entradaNegra:false` y
`salidaNegra:false` (sin fundidos a negro), `empuje:true` (cámara que se acerca en el gancho y la ráfaga),
`cierreVivo:true` (empuje en el cierre y brillo en el botón), `cubo:{radio, cy, etiquetaY, halo}` (cubo acotado que no
cruza la etiqueta y halo de la cifra; p. ej. `{radio:250, cy:760, etiquetaY:1390, halo:36}`).

## Pasos

1. Elegir textos verdaderos del producto (gancho en pregunta, 3–4 frases cortas, una cifra real, la URL).
2. `musica.json` (un compás por escena, 8 compases) → `musica.py`; después
   `pista.py <carpeta> recursos/musica/<cancion>.mp3 --energia` (la subida de la canción cae en el golpe del logo,
   pulso 24; `--energia` escribe `energia.js` y las barras de la ráfaga siguen la música de verdad).
3. Capturas por escena y exportar a 60 fps (`VIDEOS_PARAMS="fps=60&sub=4"`). Para revisar la zona segura, la hoja
   de `hoja.py` deforma los cuadros verticales (los pone en 16:9): juntarlos a mano a 216×384 con las líneas de
   250 y 1500 px dibujadas.

## Tipografía y cámara (reglas finas)

- **El texto que sale se va antes de que entre el nuevo**: nunca dos frases a la vez en el mismo lugar ni una
  cruzando a otra; la salida termina en el pulso donde empieza la entrada.
- **Desfase de impresión de 2–4 px** (los canales o una copia de color corridos, como plancha mal registrada)
  **sólo en los impactos**, unos pocos cuadros; el resto del tiempo el texto está limpio. Incluye el glitch del logo.
- **Letras revueltas con semilla**: el carácter de cada letra sale de `Movimiento.azar(...)` con una semilla que
  combina la del video, el número de letra y el instante de `Reproductor.cuadro(t)`; así cada render y cada
  subcuadro dan lo mismo.
- **Cámara a la mitad de la velocidad que parece bien** (por omisión) y movimientos de 1,5–3 s; los giros y
  alejamientos rápidos sólo en un golpe.
- **Excepción a la gramática de fragmentos de `video-lanzamiento`** (texto ≤ 65 % de los cuadros, imagen pura entre
  fragmentos): aquí el texto **es** la imagen, así que ese tope no aplica. Sí valen los fragmentos de 1 a 4 palabras
  por golpe y la prueba de especificidad (¿esta frase sería igual de cierta para otro producto?). Si un showreel se
  monta sobre material real (capturas o producto), vuelve a valer la regla entera.

## Lo que falló

- El corte de líneas tenía los argumentos invertidos (`ancho(pr, 130, 900)`): partir frases midiendo con el
  tamaño real de la letra.
- Un logo cuadrado tapaba el nombre: **limitar el logo por alto** (máx. 480 px).
- Una palabra larga en la escena tocaba el borde con 60 px de margen: `ajustar()` deja 100 px a cada lado.
- Nada de textos chiquitos en las esquinas.
- **Crítico ciego sobre «Libreta»: congelado 6,3 s/30 s, cierre quieto 1,2 s, cuadro 0 vacío, cubo sobre la
  etiqueta.** Lecciones: (1) el cuadro 0 es el titular ya terminado y las letras «golpean» (suben y vuelven) en vez
  de entrar; nada de fundido desde el color de fondo (`neg` lo volvía marrón). (2) Toda escena que queda quieta al
  terminar sus entradas lleva un empuje lento de cámara (escala 1→1,012–1,05 con parte lineal + cúbica) y el brillo
  de una pasada en el botón: se midieron 7 tramos quietos, no sólo el que dijo el crítico. Antes del primer pulso
  `u` es negativo: acotar con `max(0, …)` o la escala < 1 deja un borde sin cubrir que depende del cuadro anterior.
  (3) El cubo de alambre llega a ±2 radios por la perspectiva: con radio 250 px cae en y≈260–1260 y la etiqueta va
  en y=1390; la cifra lleva un halo del color de fondo. (4) Sin fundido a negro al final. Esos arreglos ya son
  **opciones del motor compartido** (apagadas por omisión: los showreels ya hechos salen idénticos; medido con
  capturas antes/después). Un showreel nuevo debe encenderlas todas (ver las opciones en «Motor»). El ejemplo
  publicado `13-showreel/libreta/` es anterior a esas opciones y no las enciende.

## Verificar

- Todo el contenido entre ~250 y ~1500 px de alto (arriba y abajo lo tapa la interfaz de la red social) y a más
  de 100 px de los bordes laterales.
- La subida de la canción cae en el golpe del logo (escuchar); `saltos.py` (los cortes entre escenas son a
  propósito: `--cortes`).

## Nivel de estudio

- Canción real por producto con `pista.py`, un efecto real por golpe y 60 fps.
- Barras de audio con la energía real de la canción (`--energia`), como en «EVERY BEAT» de @prasenx en X.
- (Opcional) acabado riso (`acabado-riso`): funciona bien sobre colores planos como éstos.

## Herramientas externas (opcional)

- **Mixkit** (canción y efectos; bajar a `recursos/`).
- **No conviene**: mandar fotos de clientes a un servicio externo sin preguntar.
