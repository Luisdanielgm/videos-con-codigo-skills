---
name: video-pantalla-real
description: 'Técnica 12. Comercial (27–35 s) con capturas REALES de la web del producto dentro de una laptop y un teléfono dibujados en código, con zoom, scroll, cursor, clics y notas, manejado por un guion de acciones en pulsos (herramientas/pantalla.js). Usar cuando el producto ya tiene una web que se ve bien: es lo más creíble.'
---

# Pantalla real (técnica 12)

Antes: leer la skill base **`video-lanzamiento`**. No hay ejemplo publicado (los originales mostraban las
webs de productos propios); un `index.html` de esta técnica tiene unas 80 líneas y casi todo es el guion.

## Qué hace falta

- El entorno `.venv` con **playwright** (README). `capturar_web.py` usa el Chrome instalado (canal `chrome`),
  así que no hace falta `playwright install`; si no hay Chrome, `python -m playwright install chromium` y
  cambiar `channel="chrome"` en el script.
- ffmpeg y Chrome para exportar.

## Capturas

```
.venv/Scripts/python herramientas/capturar_web.py <carpeta> <url> <nombre> [--movil] [--oscuro] [--espera ms] [--secciones 5] [--pantalla]
```
- Guarda `<carpeta>/capturas/<nombre>.png` con la página entera (o sólo lo visible con `--pantalla`).
  `--movil`: 390×844 a escala 3; `--oscuro`: pide el tema oscuro.
- Sólo páginas públicas o servidores locales del repositorio. **Nunca iniciar sesión en producción** ni capturar
  datos de usuarios. Sin cuentas ni cookies.
- Si la página desplaza un contenedor interno (sólo sale la portada): `--secciones N`, y en el guion se
  cambia de captura con `['imagen', ...]`.
- Si la landing dice lo que el producto no respalda, no mostrarla ni hacer zoom ahí; usar otras pantallas
  reales (p. ej. capturas de las pruebas de punta a punta o de una herramienta interna del producto).

## Motor

`Pantalla.video({canvas, colores, imagenes, dispositivos, guion, pantallaCompleta, duracion})` y
`Pantalla.titular(api, t, a, b, lineas, opciones)`. El guion es una lista de acciones en pulsos: `entra`, `sale`,
`imagen`, `scroll`, `mueve`, `zoom`, `general`, `camara`, `cursor`, `clic`, `texto`, `nota`, `ocultarCursor`. Se
compila después de que cargan las imágenes. La documentación de cada acción está en el encabezado de
`herramientas/pantalla.js`. Esqueleto:

```html
<canvas id="c" width="1920" height="1080"></canvas>
<script src="pulsos.js"></script>
<script src="../../herramientas/movimiento.js"></script>
<script src="../../herramientas/reproductor.js"></script>
<script src="../../herramientas/pantalla.js"></script>
<script>
Pantalla.video({
  canvas: document.getElementById('c'),
  colores: { fondo1: '#0e1116', fondo2: '#1b2230', acento: '#4f8cff', texto: '#ffffff', gris: '#8a93a3' },
  imagenes: { inicio: 'capturas/inicio.png' },
  dispositivos: { lap: { tipo: 'laptop', x: 410, y: 170, w: 1100 } },
  guion: [[0, 'entra', 'lap', 'inicio'], [4, 'zoom', 'lap', 100, 80, 700, 400], [6, 'cursor', 'lap', 320, 260], [7, 'clic'],
          [8, 'texto', 'Todo en un lugar'], [12, 'general']],
  duracion: 16,
});
</script>
```

## Lo que falló

- Ubicar los zooms con una vista de la captura con cuadrícula cada 100 px (coordenadas de la página).
- **Zoom tope 3,2×**: una fila ancha de tarjetas no se aísla (se ven las de abajo, con textos que no
  corresponden); encuadrar una tarjeta o no hacer ese zoom.
- El texto de abajo tapaba el subtítulo de la página: ajustar el zoom o mover la nota.
- Secciones con datos falsos o de otra etapa (equipo, ofertas) se borran del guion.
- Que el cursor no tape lo que aprieta.

## Verificar

- Hoja de cuadros en cada zoom y cada clic: la zona que se lee es la que dice el texto; nada se sale de la
  pantalla del dispositivo.
- Nada de datos personales en las capturas; `saltos.py` y duración del MP4.

## Nivel de estudio

- **Mejorar el motor sube todos los videos a la vez**: 60 fps (`VIDEOS_PARAMS="fps=60&sub=4"`), una onda en el
  punto de cada `clic` con un efecto real, y la canción real con `pista.py` (el ritmo de lectura cerca de 100 BPM).
- **Nunca una vista general con texto chico más de un compás**: la captura se lee sólo con zoom.
- **Recapturar cuando cambie el producto**: si la interfaz tiene un error de texto, no se retoca la captura; se
  recaptura cuando se corrija.

## Herramientas externas (opcional)

- **Mixkit** (canción, clic y whoosh; bajar a `recursos/`).
- **HyperFrames** tiene dispositivos en 3D (p. ej. una laptop en GLTF), pero piden WebGPU (Brave o Chrome Canary):
  no se probaron.
- **No conviene**: generar pantallas con imágenes. La técnica vale porque las capturas son reales.
