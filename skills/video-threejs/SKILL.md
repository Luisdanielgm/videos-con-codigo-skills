---
name: video-threejs
description: 'Hace un video explicativo o narrativo narrado en 3D con three.js en un solo HTML (técnica 2 del proyecto). Usar cuando piden un video nuevo con esta técnica, o pasar un guion existente a 3D.'
---

# Video 3D con three.js (técnica 2)

Resultado: `02-threejs/<video>/` con `guion.json`, `narracion.wav`, `tiempos.js` e `index.html`, y el
MP4 en `render/02-threejs_<video>.mp4`. Ejemplo de referencia: `02-threejs/red-neuronal/` (mismo guion que la
técnica 1, para comparar) y su MP4 en `ejemplos/02-threejs_red-neuronal.mp4`. **Leerlo antes de empezar.**

## Qué hace falta

- **three.js 0.170** local: `herramientas/vendor/three.module.min.js` (viene en el paquete; licencia MIT,
  Copyright 2010-2024 Three.js Authors). Otra versión se baja del paquete `three` de npm (`build/three.module.min.js`).
- El entorno `.venv` con las voces (`narrar-guion`), ffmpeg y Chrome con WebGL.
- Para mirarlo en vivo: `python herramientas/servidor.py` y abrir `http://localhost:8790/02-threejs/<video>/`
  (los módulos ES no cargan desde `file://`).

## Reproducir el ejemplo

```
.venv/Scripts/python herramientas/narrar.py 02-threejs/red-neuronal
python herramientas/navegador.py capturas 02-threejs/red-neuronal 5,40,90,150,220
python herramientas/navegador.py exportar 02-threejs/red-neuronal
```

> **Una máquina o un objeto con el look «oscuro con brillo»** (sólidos biselados, cámara isométrica verdadera, un acento que
> brilla, o un `.glb` propio limpiado y restilizado): no se arma desde cero con esta receta; usar el kit `herramientas/iso3d.js`
> de la técnica 26 (`video-maquina-isometrica`, «Variante 3D real»), que ya trae el contrato `render(t)`, las guardias
> (`iso3d.py --probar`) y el lector de `.glb` (este three.js local no trae `GLTFLoader`).

## Pasos

1. **Guion**: mismas reglas que `video-html-canvas` (principiantes, una idea por frase, números en
   palabras). Si el video ya existe en otra técnica, **copiar su `guion.json`**: la narración sale
   idéntica de la caché y la comparación es justa.
2. **Narración**: skill `narrar-guion`.
3. **Escena 3D** (`index.html`), con el contrato de abajo.
4. **Revisión visual**: skill `exportar-video`. En 3D revisar además la lista de abajo.
5. **MP4**: skill `exportar-video`.

## Contrato de `index.html`

- three.js **local**, no desde internet: `import * as THREE from '../../herramientas/vendor/three.module.min.js'`
  dentro de un `<script type="module">`. Así exportar no depende de la red.
- Dos lienzos: three.js dibuja en su propio lienzo WebGL (`preserveDrawingBuffer: true`, 1920×1080,
  `setPixelRatio(1)`); cada cuadro se copia al `<canvas>` final con `drawImage`, y encima van en 2D los
  textos, títulos y `Reproductor.subtitulos`. El lienzo final es el que recibe `Reproductor.iniciar`.
- Tiempos relativos a la narración con `Reproductor.ayudantes(TIEMPOS)` → `{ A, D, F, P, SIG, vis, … }`.
- `render(t)` determinista: posiciones, cámara y colores salen sólo de `t` (generador con semilla, nada
  de `Math.random()` ni de estado entre cuadros).
- **Una escena = un `THREE.Group` con materiales propios.** Para fundir una escena se cambia la
  opacidad de sus materiales (`transparent: true`); si dos escenas comparten materiales, se funden juntas.
  Una escena que reaparece (la red en "intento" y en "resultado") es un solo grupo que actualizan varias.
- Cada escena devuelve `{ a, cam, mira, dibujar2D }`: su visibilidad, la cámara que quiere y sus textos.
  La cámara sigue a la escena más visible; entre escenas hay un fundido a oscuro.
- **Textos siempre en 2D**, nunca como geometría: se proyecta el punto 3D a la pantalla
  (`vector.project(cam)`) y se dibuja con sombra para que se lea sobre cualquier fondo.

## Revisión específica del 3D (además de la lista de `exportar-video`)

1. **Lo que tiene que leerse, de frente a la cámara**: una cuadrícula vista de canto no muestra el
   dibujo. Planos con información (el 7 en píxeles, tarjetas) miran a la cámara.
2. **Encuadre**: la cámara no puede quedar dentro de un objeto ni tan cerca que el objeto tape el
   título. Si una superficie es muy alta, escalar su altura (constante) antes que alejar mucho la cámara.
3. **Etiquetas sobre cosas tapadas**: las etiquetas 2D no saben de oclusión; si la cámara se inclina y
   un objeto tapa a otro, ocultar las etiquetas de los tapados.
4. **Guardia de zonas**: al proyectar, recortar la posición de la etiqueta a la zona útil
   (y entre 135 y 935, x entre 60 y 1860), para que nunca pise título ni subtítulo.
5. **Colores con significado también en 3D**: los pulsos de ida en blanco y los de vuelta (el error)
   en rojo, con mallas separadas.
6. Texto sobre una superficie de colores: ponerle un panel oscuro detrás.

## Exportar sin ventana

`herramientas/navegador.py` lanza Chrome sin `--disable-gpu` y con `--enable-unsafe-swiftshader`:
usa la GPU si hay, y si no, WebGL por software. Si las capturas salen negras, revisar
`render/navegador-capturas-<puerto>.log` (queda sólo si la corrida tuvo un problema). El MP4 de 3D pesa más que el
de 2D (el del ejemplo salió de 145 MB a 60 fps); recomprimir con
`ffmpeg -i entrada.mp4 -c:v libx264 -crf 27 -pix_fmt yuv420p -c:a aac salida.mp4` (así quedó el de `ejemplos/`, en 41 MB).

## Verificar

- `navegador.py capturas` con código 0 y ninguna captura negra.
- Ninguna captura con los defectos de `exportar-video` ni de la lista de 3D; MP4 ≈ `TIEMPOS.total`; `saltos.py`.

## three.js r186 (WebGPU/TSL), opcional

Los videos que ya existen siguen con r170 (`three.module.min.js`); r186 es sólo para videos nuevos que necesiten
**materiales y posprocesado en TSL** (bloom, DOF, desenfoque…) o **cientos de miles de partículas en un compute
shader**. Si no hace falta nada de eso, r170 alcanza. **No viene en este paquete**: bajarlo del paquete `three@0.186`
de npm (`build/three.webgpu.js`, `build/three.tsl.js`, `build/three.core.js` y los addons que se usen, de
`examples/jsm/`; MIT) a `herramientas/vendor/three-r186/`, y anotar la versión y el sha256 de cada archivo en un
`VERSION.txt`. Una página de prueba con TSL + bloom + 131 mil partículas en compute anduvo con las medidas de abajo.

- **Importar** (r186 ya no trae `.min.js`; los módulos se piden entre sí por nombre): importmap con
  `"three/webgpu": "../../herramientas/vendor/three-r186/three.webgpu.js"`, `"three/tsl": "…/three.tsl.js"` y
  `"three/addons/": "…/three-r186/addons/"`. Un addon nuevo se copia del paquete y su sha256 va a `VERSION.txt`.
- **Navegador**: con los parámetros de siempre de `navegador.py` (sin `VIDEOS_CHROME_ARGS`) Chrome sin ventana dio
  **WebGPU en una Intel UHD 630**. Una NVIDIA de la misma máquina no se consiguió para WebGPU: `--use-angle=vulkan
  --enable-features=Vulkan` deja sin adaptador WebGPU (cae a WebGL2 en la NVIDIA, y es más lento),
  `--use-webgpu-power-preference=force-high-performance` también, y `--use-adapter-luid` cuelga la página.
- **Respaldo**: si no hay WebGPU, el `WebGPURenderer` cae solo a WebGL2 (avisa en consola); `forceWebGL: true` lo
  fuerza. El compute anda en los dos (en WebGL2 por transform feedback). Mismo cuadro, píxeles algo distintos.
- **Tiempos** (1920×1080, 131 mil partículas, bloom; varía con la carga de la GPU): WebGPU 25–41 ms por cuadro,
  WebGL2 32–69 ms, más 50–150 ms del JPEG del reproductor. El primer cuadro tarda 1–3 s (compila los shaders).

Trampas (todas medidas con la página de prueba):
1. **`await renderer.init()` antes de nada.** Después `render()` es síncrono y el lienzo se copia con `drawImage`
   en el mismo turno, así que `render(t)` sigue el contrato del reproductor. `renderAsync` está obsoleto en r186.
2. **El posprocesado se congela si se dibujan varios t en el mismo turno**: `pass()` y `bloom()` se actualizan una
   vez por «frame» de three, que sólo avanza con `requestAnimationFrame`. Subcuadros de desenfoque, capturas seguidas
   o una medición salen con la escena del primer t. Arreglo: `renderer._nodes.nodeFrame.update()` al principio de
   cada `render(t)` (campo privado: revisarlo al cambiar de versión), o `updateBeforeType = THREE.NodeUpdateType.RENDER`
   en el pass y el bloom (público, pero dibuja la escena dos veces: 72 contra 41 ms).
3. **Compute sin estado**: la posición de cada partícula sale de `(instanceIndex, t)`, nunca integrando el cuadro anterior.
4. **En WebGL2 el dibujo puede leer el búfer de compute del turno anterior** (son dos que se turnan): el mismo t salía
   distinto según cuántos cuadros iban. Arreglo: llamar `renderer.compute(...)` dos veces por cuadro cuando `!renderer.backend.isWebGPUBackend`.
5. **Verificar el determinismo**: el hash de los píxeles de un mismo t tiene que dar igual con otros t en medio y en
   dos sesiones del navegador (`determinismo.py` compara el mismo t en orden y en orden inverso).

## Nivel de estudio

Lo que le falta al ejemplo:
- **Materiales ricos**: `MeshPhysicalMaterial` (clearcoat, transmisión, iridiscencia) con un entorno de estudio
  propio (`PMREMGenerator.fromScene`) y brillo barato en 2D (ver `video-producto-3d`).
- **Geometría de verdad** (extrusión con bisel) en vez de cajas, esferas o planos apilados.
- **Sin fundido a oscuro entre escenas**: la cámara viaja o un objeto se vuelve el siguiente; si el viaje es
  largo, corte seco (otra lista de resortes que arranca en ese instante).
- Narrador con Supertonic, canción que baja con la voz, efectos reales y 60 fps, como en `video-html-canvas`.

## Toma firma, cámara de cine y trampas (de la plantilla 3D de prompt-motion.com)

- **Primero la toma firma**: antes de modelar nada se decide y se describe la imagen que la gente recordaría (el plano
  del póster), y todo el video se construye hacia ella; se prueba esa toma sola antes que las demás.
- **Un movimiento de cámara nombrado por toma** (dolly, grúa, órbita, empuje, cambio de foco), escrito en la columna
  «Cámara» de la tabla de tomas; nunca `OrbitControls` ni una cámara que deriva sin intención.
- **Luz de tres puntos** (principal, relleno y contorno) más el entorno PMREM y ACES que ya trae el ejemplo; **lo que
  se golpea se mueve** (un choque sin reacción del objeto se ve falso).
- **Tres trampas que ya costaron renders en otros proyectos**: (1) **sesgo de sombra**: `shadow.bias` ≈ −0,0005 y
  `normalBias` ≈ 0,02 contra las rayas («acné» de sombra); (2) **planos cercano y lejano ajustados** a la escena
  (`near` tan grande y `far` tan chico como se pueda): con 0,01–10000 la profundidad parpadea; (3) **semilla en todo
  azar** (posiciones, partículas, ruido): `Math.random` rompe el determinismo de `render(t)`.
- **Recorrido guiado por una instalación real** (receta: el centro de datos, la línea del primer
  down): la cámara es el guía y va de parada en parada; en cada una, **un rótulo corto (1–4 palabras) y una cosa que
  funciona** (el ventilador gira, el líquido circula); entre paradas, un viaje de cámara sin corte. Lo real se modela
  con sus proporciones verdaderas y la fuente en `brief.md`. Todavía no tiene ejemplo en el repo.

## Herramientas externas (opcional)

- **Generador 3D desde imágenes** (p. ej. Hunyuan3D, con cuenta propia y cuota): personajes y objetos en GLB con
  textura PBR. Hace falta `GLTFLoader` de three.js 0.170 (`examples/jsm/loaders/GLTFLoader.js` del repositorio de
  three.js, MIT) en `herramientas/vendor/`, la animación (el esqueleto lo arma `personaje_ia.py` en Blender:
  habría que exportar un GLB animado) y medir si 500 mil caras andan en WebGL (conviene reducirlas). Revisar la
  licencia comercial de lo generado.
- **Mixkit** y **Supertonic**: como en `video-html-canvas`.
- **No conviene**: fondos generados como imagen plana. En 3D el fondo es la escena, y una imagen plana se nota al
  mover la cámara.
