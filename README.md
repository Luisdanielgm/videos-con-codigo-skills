# Creando skills para crear videos con código

Veinte técnicas para hacer videos **sólo con código**: un agente de programación escribe el guion, la
narración, la animación y la mezcla, y ffmpeg arma el MP4. No se usa ningún editor de video ni se genera video
con IA: cada cuadro sale de un programa (Canvas 2D, three.js, un shader, Python con cairo o Manim, Blender por
script).

Todo esto se hizo con **Claude Code (la app de escritorio) con el modelo Claude Opus 5.5**. Las skills están
pensadas para Claude Code, pero no dependen de él: **cualquier agente puede usarlas leyendo el `SKILL.md`
correspondiente antes de trabajar**.

Licencia: MIT para las skills, las herramientas y el código de los ejemplos (ver `LICENSE`). Los videos de
`ejemplos/` no están bajo MIT (ver más abajo).

## Qué hay aquí

```
skills/<nombre>/SKILL.md    las 25 skills (una por técnica + las de base)
herramientas/               lo que usan las skills: reproductor, narración, mezcla, exportación, motores
01-html-canvas/red-neuronal/ … 20-generativo/semilla/   código de los ejemplos publicados
datos/                      dígitos de UCI optdigits (para la técnica 3)
ejemplos/                   los MP4 de ejemplo y su LEEME.md con las licencias de terceros
requirements.txt            el entorno de Python principal
```

## Las 20 técnicas

| # | Técnica | Skill | Ejemplo publicado |
|---|---|---|---|
| 1 | Animación en un solo HTML con Canvas 2D | `video-html-canvas` | `01-html-canvas/red-neuronal/` |
| 2 | 3D en el navegador con three.js | `video-threejs` | `02-threejs/red-neuronal/` |
| 3 | Diagrama que calcula de verdad lo que muestra | `video-calculo-real` | `03-calculo-real/red-neuronal/` |
| 4 | Explicativo en Python: pizarra con cairo o diagramas con Manim | `video-pizarra` | `04-explicativo-narrado/red-neuronal/` (pizarra) |
| 5 | Todo el cuadro en un shader de WebGL2 | `video-shader` | `05-shader-webgl2/el-faro/` (cuento original) |
| 6 | Render real en Blender por script + captura de movimiento | `video-blender` | — (sí las herramientas) |
| 7 | Acabado risográfico sobre un video hecho | `acabado-riso` | — |
| 8 | Comercial: una sola forma que se vuelve cada pantalla | `video-forma-unica` | `08-lanzamiento/libreta/` (app de notas inventada) |
| 9 | Comercial: objetos y datos del producto en 3D | `video-producto-3d` | `09-producto-3d/libreta/` (app de notas inventada) |
| 10 | Comercial: partículas y tipografía cinética | `video-particulas` | `10-particulas/libreta/` (app de notas inventada) |
| 11 | Comercial: globo, rutas y gráficos que se calculan | `video-datos-mapa` | — |
| 12 | Comercial: capturas reales de la web en laptop y teléfono | `video-pantalla-real` | `12-pantalla-real/libreta/` (app de notas inventada) |
| 13 | Showreel vertical para reels | `video-showreel` | `13-showreel/libreta/` (app de notas inventada) |
| 14 | Comercial con HyperFrames (storyboards y escenas) | `video-hyperframes` | — |
| 15 | La app real grabada del teléfono (adb) | `video-app-real` | — |
| 16 | Collage de papel con imágenes generadas | `video-collage` | — |
| 17 | Documental con archivo real + motion graphics | `video-archivo` | `17-archivo/revolucion-industrial/` |
| 18 | Épica histórica en dibujo lineal | `video-epica-lineal` | `18-epica-lineal/historia-del-vuelo/` |
| 19 | Ensayo cinematográfico | `video-ensayo` | `19-ensayo/las-cosas-pequenas/` |
| 20 | Generativo por semilla (una palabra decide todo) | `video-generativo` | `20-generativo/semilla/` |

Las técnicas sin ejemplo publicado se hicieron sobre material que no se puede publicar (productos propios, un
libro con derechos, cuentas reales); sus skills describen el método completo y la estructura de archivos.

**Skills de base** (se leen además de la de la técnica):

| Skill | Para qué |
|---|---|
| `director-de-video` | Elegir la técnica de cada tramo y combinar 2–3 en un mismo video. Leerla primero. |
| `video-lanzamiento` | Base de los comerciales (técnicas 8–15): material verdadero, pulsos, música, reglas. |
| `video-historia` | Contar una escena con varias voces, ambiente y música. |
| `narrar-guion` | `guion.json` → `narracion.wav` + `tiempos.js` con voces locales. |
| `exportar-video` | Capturas, hoja de contacto, revisión visual y exportación a MP4. |

## Cómo usar las skills

**Con Claude Code**: abre este repositorio como carpeta de trabajo y copia (o enlaza) las skills a
`.claude/skills/`, que es donde Claude Code las busca:

```
mkdir -p .claude && cp -r skills .claude/skills        # o un enlace: ln -s ../skills .claude/skills
```
(También sirven en `~/.claude/skills/` para todos tus proyectos, pero las rutas de las skills son relativas a
la raíz de este repositorio.) Después pide el video: «haz un video explicativo de dos minutos sobre cómo funciona
una vacuna, con la técnica 1». Claude Code carga solo la skill que corresponde.

**Con cualquier otro agente o modelo**: dile que, antes de trabajar, lea `skills/director-de-video/SKILL.md`, la
skill de la técnica elegida y las de base que nombre (`narrar-guion`, `exportar-video`…). Todas las rutas de
las skills son relativas a la raíz del repositorio, y los comandos se corren desde ahí.

Cada skill tiene: qué hace falta, cómo reproducir el ejemplo (si lo hay), los pasos, qué se verifica y cómo, lo
que falló (errores conocidos), lo que le falta para verse «de estudio» y qué herramientas externas la mejoran.

## Requisitos e instalación

Lo mínimo (técnicas 1–4, 17–20): **Python 3.12**, **ffmpeg** y **Chrome, Chromium o Edge**.

1. **Python 3.12 y el entorno principal**:
   ```
   py -3.12 -m venv .venv                          # Linux/macOS: python3.12 -m venv .venv
   .venv/Scripts/python -m pip install -r requirements.txt
   ```
   En Linux o macOS el Python del entorno es `.venv/bin/python` (las skills escriben `.venv/Scripts/python`, la
   forma de Windows). pycairo en Linux pide antes `libcairo2-dev` y `pkg-config`.
2. **ffmpeg** en el PATH (ffmpeg.org; en Windows, una compilación «full», que trae el filtro `rubberband` que usa
   el cambio de tono de las voces).
3. **Chrome, Chromium o Edge**: `herramientas/navegador.py` los busca solo. `capturar_web.py` (Playwright) usa el
   Chrome instalado.
4. **Voces locales** (skill `narrar-guion`, con el detalle):
   - Kokoro v1.0 int8: `kokoro-v1.0.int8.onnx` y `voices-v1.0.bin` de los releases de `thewh1teagle/kokoro-onnx`
     (GitHub, etiqueta `model-files-v1.0`) en `modelos/`.
   - Piper: `es_MX-ald-medium` y `es_MX-claude-high` (`.onnx` + `.onnx.json`) de `rhasspy/piper-voices`
     (Hugging Face) en `modelos/`.
   - Supertonic-3 (la voz recomendada del narrador): entorno aparte, `py -3.12 -m venv externos/voz-env` y
     `externos/voz-env/Scripts/python -m pip install supertonic soundfile numpy`; el modelo se baja solo de Hugging
     Face (`Supertone/supertonic-3`) la primera vez.

Según la técnica, además:

| Para | Qué | Dónde |
|---|---|---|
| Técnica 4 con Manim | Manim Community 0.21 en un entorno aparte (`pip install manim soundfile`) | `video-pizarra` |
| Técnica 6 | Blender 4.5 LTS portable (download.blender.org, verificar sha256) y clips BVH de CMU (`python herramientas/bajar_mocap.py`) | `video-blender` |
| Técnica 11 | Natural Earth `ne_110m_land.geojson` (repositorio `nvkelso/natural-earth-vector`) | `video-datos-mapa` |
| Técnica 14 | Node.js 22+ y `npx hyperframes@0.8.78` | `video-hyperframes` |
| Técnica 15 | Android Platform-Tools (adb) y un teléfono con depuración USB | `video-app-real` |
| Técnicas 16, 19 y hojas de modelo | Un generador de imágenes (p. ej. Codex con una suscripción de ChatGPT, u otro que se llame desde la terminal) | `video-collage`, `video-ensayo` |
| Canción real y efectos | Canciones libres (p. ej. Mixkit) en `recursos/musica/`; banco de efectos (abajo) | `video-lanzamiento` |

**Banco de efectos** (`recursos/efectos/`): `mezclar.py`, `pista.py` y el motor de Manim buscan los efectos en
`recursos/efectos/listos/<categoría>/<nombre>.wav` con su `indice.json`. Para armarlo: bajar cada efecto de
Mixkit que lista `herramientas/seleccion.tsv` (id, categoría, nombre, página) desde
`https://assets.mixkit.co/active_storage/sfx/<id>/<id>.wav` a `recursos/efectos/mixkit/<categoría>/<nombre>.wav`,
bajar y descomprimir los tres paquetes de Kenney de `herramientas/preparar_efectos.py` (`KENNEY_ZIP`) en
`recursos/efectos/kenney/<paquete>/`, y correr `.venv/Scripts/python herramientas/preparar_efectos.py` (normaliza
a WAV 48 kHz, mide el pico de cada uno y arma `indice.json`; `--romper` prueba su guardia). Sin el banco, la
música y los efectos calculados de `musica.py` y `sonido.py` sirven de respaldo.

### Carpetas fuera de git y rutas configurables

Nada de esto viene en el repositorio (está en `.gitignore`); cada quien lo crea o lo baja:

| Carpeta | Qué va | Nota |
|---|---|---|
| `.venv/` | Entorno de Python principal | |
| `modelos/` | Voces de Kokoro y Piper | |
| `externos/` | Blender portable, clips BVH (`mocap/`), Natural Earth (`geo/`), entorno de Supertonic (`voz-env/`) | Puede ser un enlace a otro disco |
| `recursos/` | Canciones, banco de efectos, material de archivo, modelos 3D generados | Puede ser un enlace a otro disco |
| `render/` | MP4, capturas, la caché de voz y los registros | Se crea solo |
| `biblioteca/` | Bibliotecas de personajes de Blender (`.blend`) | Se rearman por script |

Variables de entorno: `VIDEOS_PARAMS` (parámetros de la página al exportar, p. ej. `fps=60&sub=4`),
`VIDEOS_PUERTO` (puerto del servidor local, 8790 por omisión) y `VIDEOS_VOZ_PYTHON` (el Python del entorno de
Supertonic, si no está en `externos/voz-env/`). La ruta de Blender va escrita en cada comando: cámbiala por la tuya.

Fuentes: varios motores usan fuentes que trae Windows (Segoe UI y Segoe Print, Georgia, Bahnschrift, Cambria,
Consolas). En Linux o macOS, instalar otras y cambiarlas donde lo dice cada skill.

### Probar que todo anda

```
.venv/Scripts/python herramientas/narrar.py 01-html-canvas/red-neuronal              # la voz
python herramientas/navegador.py capturas 01-html-canvas/red-neuronal 5,40,90         # el navegador sin ventana
.venv/Scripts/python 04-explicativo-narrado/red-neuronal/video.py --capturas 5,40     # cairo
.venv/Scripts/python herramientas/saltos.py --probar                                  # ffmpeg y el detector de saltos
```

## Videos de ejemplo

En `ejemplos/` (detalle y licencias en `ejemplos/LEEME.md`):

| Video | Técnica | Dura | Pesa |
|---|---|---|---|
| `01-html-canvas_red-neuronal.mp4` | 1 · Canvas 2D | 4:02 | 26 MB |
| `02-threejs_red-neuronal.mp4` | 2 · three.js | 4:02 | 41 MB |
| `03-calculo-real_red-neuronal.mp4` | 3 · cálculo real | 3:54 | 28 MB |
| `04-explicativo-narrado_red-neuronal.mp4` | 4 · pizarra (cairo) | 4:02 | 22 MB |
| `17-archivo_revolucion-industrial.mp4` | 17 · archivo + motion graphics | 0:48 | 53 MB |
| `18-epica-lineal_historia-del-vuelo.mp4` | 18 · épica lineal | 0:59 | 21 MB |
| `19-ensayo_las-cosas-pequenas.mp4` | 19 · ensayo | 0:41 | 22 MB |

Los cuatro de la red neuronal cuentan lo mismo («¿Cómo aprende una red neuronal?», para principiantes) con el
mismo guion y la misma voz, para comparar las técnicas de a iguales.

**Los videos no están bajo la licencia MIT**: se pueden ver, pero llevan música de Mixkit (licencia gratuita de
Mixkit, que no permite redistribuir los audios sueltos), efectos de Kenney (CC0) y de Mixkit, y material de
archivo de dominio público de Wikimedia Commons, cada uno con su licencia.

## Lo que no se puede reproducir sin algo propio

- **Imágenes generadas** (técnicas 16 y 19, hojas de modelo de la 6): hace falta un generador de imágenes propio
  (una suscripción o un modelo que corra en tu máquina). Las seis imágenes del ensayo vienen incluidas.
- **Modelos 3D generados** (camino B de la técnica 6, opcional en la 2 y la 9): una cuenta en un generador 3D
  desde imágenes, con su cuota. El paquete no trae personajes de ejemplo: la biblioteca de Blender
  (`herramientas/personajes.py`) y la de modelos generados (`herramientas/personaje_ia.py`) vienen vacías, con una
  plantilla comentada para armar el tuyo (skill `video-blender`).
- **Comerciales** (técnicas 8–15): necesitan un producto real con su repositorio, su web o su app; y la 15, un
  teléfono Android.
- **Canciones y efectos de Mixkit**: se bajan de mixkit.co con su licencia (no se redistribuyen aquí).

## Mantener la versión pública (la guardia)

Esta es la versión pública de un proyecto privado. `herramientas/limpiar_publico.py` copia las skills, las
herramientas y el código de los ejemplos desde el proyecto de origen, aplica los reemplazos y los parches, y
**falla** (código 1, una línea «FALLA» por hallazgo) si queda algo personal. Las reglas personales (la lista de
patrones prohibidos, los reemplazos automáticos) y los parches viven en `privado/`, que está en `.gitignore` y
nunca se publica: nombrar lo que no se publica ya sería publicarlo.

Cuando mejoran las skills del origen:

```
python herramientas/limpiar_publico.py --origen <carpeta-del-proyecto-de-origen>
```
1. Si dice `0 hallazgos · 0 fallas de copia`, la versión pública ya está al día: revisar el `git diff` y hacer
   commit.
2. Si un parche «ya no calza con el origen» (cambió esa parte del archivo), el archivo público queda como estaba:
   corregirlo a mano (o copiar la versión nueva del origen y limpiarla), y guardar la diferencia como parche nuevo:
   ```
   python herramientas/limpiar_publico.py --origen <carpeta> --guardar-parches
   ```
   y volver a correr el paso 1 hasta que diga 0.
3. Si aparece un `FALLA <archivo>:<línea>`, algo personal llegó al destino: corregirlo en el archivo público,
   `--guardar-parches` y repetir. Si hace falta un patrón o un reemplazo nuevo, va en `privado/reglas.py`.
4. `python herramientas/limpiar_publico.py --probar` rompe la guardia a propósito: un caso por patrón prohibido
   tiene que decir FALLA y el caso limpio, ok. Correrlo cada vez que se cambian las reglas.
5. `python herramientas/limpiar_publico.py --revisar` sólo revisa lo que hay en el destino, sin copiar.

Sin `privado/` (en un clon de este repositorio), `--revisar` y `--probar` corren con los patrones genéricos
(rutas de usuario, correos, claves).

## Créditos de terceros

- **three.js** 0.170 (MIT, Three.js Authors): `herramientas/vendor/three.module.min.js`.
- **HyperFrames** (HeyGen, Apache 2.0): framework de la técnica 14, se instala con `npx`.
- **Manim Community** (MIT), **Blender** (GPL), **Playwright** (Apache 2.0), **ffmpeg** (LGPL/GPL).
- **Voces**: Supertonic-3 (código MIT, modelo OpenRAIL-M, de Supertone), Kokoro (`kokoro-onnx`), Piper
  (`rhasspy/piper-voices`; cada voz trae su licencia en su ficha).
- **Mixkit**: canciones «Vastness» y «Drawing the Sky» y efectos, dentro de los videos de ejemplo (licencia
  gratuita de Mixkit).
- **Kenney**: efectos de interfaz e impacto, CC0.
- **Wikimedia Commons**: películas de los hermanos Lumière y grabados, pinturas y fotos de dominio público (lista
  en `ejemplos/LEEME.md`).
- **Our World in Data** (CC BY 4.0) y **UCI optdigits** (Alpaydin y Kaynak, CC BY 4.0).
- **Natural Earth** (dominio público) y **CMU Graphics Lab Motion Capture Database** (libre para cualquier uso;
  conversión a BVH de cgspeed).
- Ideas y referencias de estilo tomadas de videos públicos en X, citadas en cada skill (@twoclipping, @rexan_wong,
  @dirtman, @IterIntellectus, @danshipper, @MiaAI_lab, @scisterna, @prasenx, @aiehon_aya, @gcduncombe).
