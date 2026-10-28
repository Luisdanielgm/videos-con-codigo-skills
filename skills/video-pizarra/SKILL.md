---
name: video-pizarra
description: 'Hace un video explicativo narrado desde Python, sin navegador (técnica 4 del proyecto), con uno de dos motores - pizarra con cairo (marcador sobre fondo blanco, trazos que se dibujan, letra manuscrita) o Manim al estilo 3Blue1Brown (diagramas que se construyen y se transforman, números que cuentan, al compás de la voz, con control automático de textos encimados). Usar para videos educativos, y para explicar un tema técnico o un informe (seguridad, redes, algoritmos) con diagramas en vez de imágenes.'
---

> **Dos motores, una técnica.** Pizarra (cairo, `herramientas/pizarra.py`): estética de clase. **Manim**
> (`herramientas/motor_manim.py`): diagramas de estilo 3Blue1Brown; ver la sección «Motor Manim» al final.

# Video en pizarra (Python + cairo)

Resultado: `04-explicativo-narrado/<video>/` con `guion.json`, `narracion.wav`, `tiempos.js` y
`video.py`, y el MP4 en `render/04-explicativo-narrado_<video>.mp4`. Ejemplo de referencia:
`04-explicativo-narrado/red-neuronal/video.py` (mismo guion que las técnicas 1 y 2) y su MP4 en
`ejemplos/04-explicativo-narrado_red-neuronal.mp4`. **Leerlo antes.**

## Qué hace falta

- El entorno `.venv` con **pycairo** (README; en Windows la rueda de pip ya trae cairo; en Linux,
  `sudo apt install libcairo2-dev pkg-config` antes de `pip install pycairo`) y las voces (`narrar-guion`).
- **ffmpeg** en el PATH. No hace falta navegador.
- Fuentes: la letra manuscrita es **Segoe Print** (o Ink Free) y los subtítulos **Segoe UI**, que trae Windows.
  En otro sistema, instalar una manuscrita (p. ej. una de Google Fonts) y cambiar `FUENTE` al principio de
  `herramientas/pizarra.py`; si la fuente no existe, cairo cae en una genérica sin avisar.

## Por qué es distinta

No hay navegador ni HTML: `herramientas/pizarra.py` dibuja cada cuadro con cairo (el mismo motor de
dibujo de Manim) y los manda crudos a ffmpeg junto con la narración. Es la técnica más fácil de correr
en cualquier máquina y la más rápida de revisar (una captura tarda milisegundos).

## Pasos

1. **Guion**: mismas reglas que `video-html-canvas`. Si el video ya existe en otra técnica, copiar su
   `guion.json` (la narración sale de la caché).
2. **Narración**: skill `narrar-guion`.
3. **`video.py`**: importa el motor y define `escenas(pz, t)`:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "herramientas"))
   from pizarra import Pizarra, clamp, ease, lerp, seg
   pz = Pizarra(__file__)                 # lee tiempos.js de esta carpeta
   def escenas(pz, t):
       pz.texto("1 · Aprender con ejemplos", 60, 70, 40, "azul", p=pz.P(t, "idea", 0, .3))
       ...
   if __name__ == "__main__": pz.main(escenas)
   ```
4. **Revisar**: `.venv/Scripts/python <carpeta>/video.py --capturas 3.5,40,…` → PNG en `render/capturas/`.
5. **MP4**: `.venv/Scripts/python <carpeta>/video.py --exportar` (unos minutos; en segundo plano). Con
   `--exportar --fps 60`, a 60 fps.

## El motor (`herramientas/pizarra.py`)

- Tiempos relativos a la narración: `pz.A`, `pz.D`, `pz.F`, `pz.P(t, id, f0, f1)`, `pz.vis`, `pz.SIG`.
- Trazos a mano, todos con `p` (cuánto ya se dibujó, 0..1) y `semilla` (temblor fijo):
  `linea`, `trazo` (polilínea), `circulo` (con `relleno`), `rect`, `flecha`, `resaltar` (resaltador
  amarillo), `texto` (se escribe letra a letra; `alinear="izq"|"centro"|"der"`), `ancho_texto`.
- Tintas: `negro`, `azul`, `rojo`, `verde`, `naranja`, `gris`, `amarillo`.
- `pz.capa(alpha, dibujar)` funde una escena entera (se usa con `vis`).
- Subtítulos y fundido final los pone el motor; `pz.colores = {"quien": (r, g, b)}` colorea el subtítulo por
  personaje en historias (cuento ilustrado).

## Convenciones del estilo

- Cada cosa **aparece dibujándose**: líneas que crecen, texto que se escribe, círculos que se cierran.
  Nada aparece de golpe salvo lo que ya estaba en el pizarrón.
- Colores con significado: azul positivo o título, naranja negativo, rojo error o énfasis, verde
  correcto, amarillo resaltado.
- El temblor de mano tiene que ser **suave** (pocas ondas por trazo). Ruido punto a punto hace
  círculos dentados: ya pasó.
- Un pizarrón no aguanta cientos de líneas: en capas muy densas, dibujar sólo una parte de las
  conexiones y decirlo en el código.
- Misma zona útil que las otras técnicas: título arriba a la izquierda, subtítulos en la franja de abajo.

## Recetas de `iart-ai` (diagramas, infografía, pizarra con mano, láminas; MIT)

- **Divulgación progresiva en diagramas**: nodos → aristas → rótulos, nunca todo junto; el elemento activo a opacidad 1 y
  el resto a ≈ 0,35 (foco y contexto); cada paso se sostiene 0,5–1,5 s; la arista se dibuja con `p` (como `stroke-dashoffset`
  de 1 a 0) en 0,4–0,7 s y el dato que fluye es un punto sobre la ruta.
- **Infografía animada**: primero se diseña el **cuadro final estático** y equilibrado (una idea central, 3–5 datos, 30–90 s);
  el orden de aparición es la jerarquía: título solo → ícono (rebote con resorte poco amortiguado) → cifra (cuenta,
  `easeOutCubic`) → rótulo (sin drama) → conector que se dibuja y lleva el ojo al siguiente. Escalonado entre hermanos
  de 0,2–0,33 s con la misma curva; **una sola cifra se mueve a la vez**; el cuadro completo queda quieto 2–3 s.
- **Mano con marcador** (pizarra): la punta de la mano va **exactamente** en el punto del trazo que se dibuja (medir el
  desfase de la punta una vez); la mano se levanta entre trazos y no se desliza por la pizarra vacía; los trazos se
  dibujan en el orden en que lo haría una mano (abiertos, continuos, sólo se corta donde se levantaría el lápiz); los
  rellenos entran **después** del contorno; el trazo largo va lineal o casi (ease-in-out hace que el marcador dé tirones);
  un solo modo de borrar (siempre barrido de izquierda a derecha, o dibujar al revés); un dibujo por frase de la voz y
  la palabra que se nombra termina de escribirse al decirse. Comprobar con una captura **a mitad de un trazo**.
- **Láminas y presentaciones**: entrada de elemento = aparecer + subir 12–24 px en 0,25–0,5 s con 0,15–0,4 s entre viñetas;
  nada de volar, girar, rebotar ni máquina de escribir (compiten con la voz); título 56–80 px y cuerpo ≥ 28–32 px a 1080p;
  contenido dentro del 90 % central; si hace falta una nota de 16 px, se parte en dos láminas; transición fuerte sólo
  entre secciones.

## Verificar

- Las capturas no muestran los defectos de la lista de `exportar-video`.
- El MP4 dura lo mismo que `TIEMPOS.total` (±1 s): `ffprobe -v error -show_entries format=duration -of csv=p=0 <mp4>`.

## Nivel de estudio

- **Una sola pizarra grande que la cámara recorre** (las escenas dibujadas una al lado de la otra) en vez de
  capas que se funden con `pz.capa`.
- **Una mano con marcador** que sigue la punta del trazo (imagen recortada como sticker, ver abajo) y un
  **sonido real de marcador** mientras dibuja.
- Narrador con Supertonic y canción bajo la voz, como en `video-html-canvas`.
- `FPS = 30` está fijo en `pizarra.py`: pasarlo a parámetro para exportar a 60.

## Herramientas externas (opcional)

- **Generador de imágenes** para la mano con marcador sobre verde croma #00FF00 → `herramientas/recortar.py`: si
  tienes una suscripción de ChatGPT, Codex (`codex exec`, como en `video-collage`); o cualquier generador que se
  pueda llamar desde la terminal. Una sola imagen, reutilizable en todos los videos.
- **Mixkit**, Kenney o Sonniss para el sonido de marcador (bajar a `recursos/`). Si no hay uno bueno, no
  inventarlo con `musica.py`.
- **No conviene**: generadores 3D (la pizarra es 2D).

## Motor Manim (estilo 3Blue1Brown)

Resultado: `04-explicativo-narrado/<video>/` (`narrar.py`, `escena.py`, `tiempos.json`, `narracion.wav`,
`efectos.json`, `mezcla.json`) y el MP4 en `render/04-explicativo-narrado_<video>.mp4`. No hay ejemplo
publicado (el original explicaba la seguridad de un producto propio, con datos internos); abajo está cómo se
arma cada archivo.

### Segundo motor: ManimGX

La misma escena (`from motor_manim import *`) corre con **ManimGX** (Rust + wgpu; venv aparte `<venv-manimgx>`, Python
3.13): `python herramientas/render_gx.py <escena.py> <Clase> [-o salida.mp4] [--fps 30] [-r 1920x1080]` (`VIDEOS_MOTOR=gx` cambia el
import). Medido en una escena de diagramas de 5:44 (con carga de otros procesos): **134 s contra 611 s** (4,6×), RAM pico 1.100 MB contra 644,
disco ~60 MB contra 368, SSIM 0,963, `efectos.json` a ≤ 0,036 s. Compatibilidad probada también con una escena de ejes (`Axes`, `always_redraw`,
tablas): compila sin cambios, 124 efectos a ≤ 0,017 s. **Elegir GX** para una escena larga de 2D que se renderiza de una vez; **ManimCE**
si hace falta el render por partes (`-n`), LaTeX o 3D ya probado. Salida a cuadros fijos (GX se salta los cuadros quietos y `render_gx.py`
los repite). No usar `self.say` (manda texto a fal.ai). Su `inspect` marca «problemas» de maquetación: los de altura de glifos (`−`, `=`, `…`)
son falsos. `render_gx.py --probar`: 6 ok, mutado. **Medido con la PC vacía (la escena de ejes, 1920×1080 a 30 fps)**: ManimCE 495,6 s y 666 MB contra
ManimGX 196,1 s (**2,5×**, con la conversión a cuadros fijos) y 1.063 MB; con `Axes` y `always_redraw` la ventaja es menor que en la escena de
diagramas (4,6×). El render por partes (`-n`) y el 60 fps a 1080p sólo están en ManimCE: un informe de 2:55 con 155 animaciones tardó
3 min a 720p30 y ~9 min a 1080p60 con ManimCE.

### Qué hace falta

- **Manim Community 0.21** en un entorno aparte (pesa ~370 MB con scipy, PyAV, pycairo y manimpango), en la
  carpeta que quieras (aquí se llama `<venv-manim>`):
  ```
  py -3.12 -m venv <venv-manim>                        # en Linux/macOS: python3.12 -m venv <venv-manim>
  <venv-manim>/Scripts/python -m pip install manim soundfile
  ```
  En Linux hacen falta antes las bibliotecas de desarrollo de cairo y pango (ver la guía de instalación de
  Manim Community). Las fuentes que usa el motor: Cambria y Consolas (Windows); cambiarlas en `SERIF` y `MONO`
  al principio de `motor_manim.py` si no están.
- **Sin LaTeX** (no hace falta): todo texto con `Text` (Pango). `Integer`, `DecimalNumber`, `MathTex` y
  `NumberLine(include_numbers=True)` **piden LaTeX** y se caen con `FileNotFoundError`. Contador: `contador()`
  del motor (`ValueTracker` + `always_redraw(Text)`); ejes: `NumberLine(include_numbers=False)` + números con `Text`.
- Los símbolos raros (☁ ⚷ 🔒) no están en Cambria y salen como cuadrados blancos: el motor los dibuja con formas
  (`nube_ic`, `llave_ic`, `candado_ic`, `escudo_ic`, `lupa_ic`, `reloj_ic`, `persona_ic`, `telefono_ic`, …).
- Voz: Supertonic (entorno `externos/voz-env`, skill `narrar-guion`) con el `narrar.py` del video.
- El banco de efectos (`recursos/efectos/listos`, README) para los sonidos que anota el motor.

### El criterio (lo que funcionó en los videos de la red neuronal)

La primera versión del video con Manim tenía mucho texto chico, una leyenda en la esquina y rótulos encimados
en las formas, y se rehízo con estas reglas:
- **Una idea por pantalla** y diagramas grandes. Lo que ya se dijo se va (`salen`) antes de lo siguiente.
- **Poco texto**: rótulos de 1 a 4 palabras, de 24 puntos para arriba. Las cifras y los pendientes van a la voz
  y a **una tabla final** (sólo música, ~12 s después de la voz).
- **Colores que significan lo mismo en todo el video**, en vez de leyenda: p. ej. rojo = lo que podía salir mal,
  azul = la defensa, verde = comprobado, amarillo con reloj = sigue sin probarse.
- **Sin cortes**: entre capas, `capa()` corre toda la pizarra a la izquierda y la cabecera nueva entra por la
  derecha, con un barrido.
- **Efectos reales en cada animación** (`sfx`, y ya los ponen `aparece`, `uno_a_uno`, `bien`, `mal` y `capa`):
  barrido al cambiar de capa, pop por caja, clic en contadores y viajes, golpe en el sello. La canción, baja
  (volumen 0,25) y en bucle, se agacha sola con la voz.

### Cómo está armado

1. `narrar.py` (del video): una frase por momento, `(id, texto, silencio)`, con Supertonic (como el `narrar.py`
   de `19-ensayo/las-cosas-pequenas/`). Los términos en inglés se escriben como se dicen (la voz pronuncia mal
   las siglas); en pantalla van con su nombre técnico. Escribe `narracion.wav` + `tiempos.json` (mismo formato
   que `tiempos.js`, en JSON puro). Si la voz sale más larga que la duración pedida, acelerarla con el filtro
   `atempo` de ffmpeg y reescalar los tiempos (en el original, la voz a velocidad 1 dio 7:00 para un guion de
   5:30).
2. `escena.py`: `from motor_manim import *` (con `herramientas/` en `sys.path`) y `class <Video>(Explicativo)` con
   `CARPETA = Path(__file__).resolve().parent`, UNA escena. `self.en(id, frac)` espera al momento `frac` de esa
   frase (y la anota para el control); el resto de las piezas está en el motor (`tx`, `caja`, `contador`,
   `encima`, los íconos, `aparece`, `salen`, `uno_a_uno`, `bien`, `mal`, `capa`, `sfx`).
3. **Control de textos encimados** (`motor_manim.revisar`): después de cada `play` mira lo que queda en pantalla y
   falla si un texto toca otro texto, si una línea o el borde de una forma pasa por un texto (muestrea los trazos,
   no sólo las cajas), si un texto se sale del cuadro o si queda más chico que 24 puntos (también cuando se
   achica un grupo). Lo que se encima a propósito (un sello, una tachadura) se marca con `encima(m)`. Al terminar
   imprime «ok»/«FALLA» por frase y, si hay fallas, **la escena se cae antes de juntar el video**. En el
   original encontró lo mismo que se había visto a ojo (cabecera sobre el borde de la ventana, textos cortados).
4. **Pantalla nunca quieta y portada**. Medido con `critico.py`: un video de informe daba 14,7 s quietos cada
   30 s (tramos de hasta 3,3 s sin un píxel distinto) y empezaba en negro. Ahora la escena base es un
   `MovingCameraScene` y la cámara **flota**: un círculo de .04 unidades que pasa por el centro, alejándose lo justo
   (≤ 2 %) para que nada del cuadro original quede afuera, a .08 unidades/s (lo mínimo que el MP4 deja ver). Flota
   durante cada animación (así no quedan cuadros quietos en sus bordes suaves) y durante las esperas de más de
   `RESPIRA_MIN` (0,5 s), **salvo en las pausas de voz** (≥ 400 ms entre frases de `tiempos.json`, la misma regla de
   `critico.py --quietos`): ahí sí queda quieta. Entre una espera y otra la cámara queda donde estaba: no hay saltos.
   No cambia posiciones ni tiempos (el control y `efectos.json` dan lo mismo). El **cuadro 0 es una portada**
   (`TITULO = "título"` o `("título", "subtítulo")`; sin él, el nombre de la carpeta) que se va en ≤ 0,5 s con la
   primera animación. En la escena de prueba (15 s, 720p30): congelado 14,07 → 0,00 s cada 30 s, tramo más largo
   2,60 → 0,00 s, primer cuadro negro → 151 % de detalle.
   **Apagar**: `RESPIRA = False` y/o `PORTADA = False` en la clase (vuelve exacto a lo de antes); una sola espera
   quieta: `self.wait(d, respira=False)`. Si el video necesita otra respiración (un parpadeo del elemento que se
   explica, el número que sigue contando), se pone en la escena y se apaga esta.

### Pasos

1. Guion en `narrar.py` → `externos/voz-env/Scripts/python 04-explicativo-narrado/<video>/narrar.py`.
2. **Control** (~1 min, no dibuja cuadros): `<venv-manim>/Scripts/python -m manim render
   04-explicativo-narrado/<video>/escena.py <Escena> -s -ql --media_dir <carpeta-temporal> --disable_caching
   --progress_bar none` → hasta que diga `0 FALLA`. También escribe `efectos.json`.
3. **Prueba** en 480p15 (`-ql`, ~2 min para 6 min de video) con `--media_dir <carpeta-temporal-de-manim>` → hoja de
   cuadros con ffmpeg (`-vf fps=1/6,scale=400:-1,tile=6x6`; sin `drawtext`) y revisar pantallas vacías, lo que el
   control no ve (formas encimadas) y el ritmo.
4. Mezcla: `mezcla.json` (canción con `"bucle": true`, `"voz": "narracion.wav"`, `"efectos_de": "efectos.json"`,
   `"duracion"` = total de la voz + la tabla) → `.venv/Scripts/python herramientas/mezclar.py 04-explicativo-narrado/<video>`.
5. Final: `--resolution 1920,1080 --frame_rate 60` y juntar: `ffmpeg -i <Escena>.mp4 -i mezcla.wav -map 0:v
   -map 1:a -c:v copy -c:a aac -b:a 192k -shortest render/04-explicativo-narrado_<video>.mp4`.
6. `herramientas/saltos.py` sobre el MP4, y `.venv/Scripts/python herramientas/critico.py render/<video>.mp4
   --quietos 04-explicativo-narrado/<video>/tiempos.json` (congelado, primer cuadro, sonido).

### Verificar

- El control dice `0 FALLA` en todas las frases, y `<venv-manim>/Scripts/python herramientas/motor_manim.py --probar` da 18 ok (12 del control de textos y 6
  de la respiración: el cuadro original siempre cabe, se aleja ≤ 2 %, se mueve lo bastante; cada guardia tiene su
  caso roto).
- El MP4 dura lo mismo que `mezcla.json → duracion`, sin pantallas vacías más de ~1 s mientras hay voz (salvo
  justo después de un cambio de capa).
- Ningún cuadrado blanco (glifo faltante) ni número de LaTeX.
- **No conviene** para esto: imágenes generadas (el estilo es de diagramas; si hace falta un ícono, se dibuja).
