---
name: video-hyperframes
description: 'Técnica 14. Comercial con HyperFrames (framework libre de HeyGen, Apache 2.0): brief → capturas → 3 storyboards con escenas probadas («blueprints») → un subagente por escena → ensamblado → cuadros fijos → render, con música propia y videos reales adentro. Usar cuando se quiere dirigir con storyboards y referencias, o meter grabaciones reales en un diseño.'
---

# HyperFrames (técnica 14)

Antes: leer la skill base **`video-lanzamiento`** (sobre todo «Dirigir como director»). No hay ejemplo
publicado (los originales eran comerciales de un producto propio). Versión fija probada: `npx hyperframes@0.8.78`.
Método: el de @rexan_wong en X (tres storyboards, un cuadro fijo por escena antes de animar).

## Qué hace falta

- **Node.js 22 o más nuevo** (nodejs.org) y `npx`.
- Chrome (lo usa el renderizador) y una GPU libre durante el render (no correrlo junto con Blender).
- `herramientas/musica.py` o una canción libre para el audio; las capturas con `herramientas/capturar_web.py`.

## Flujo (skill global `product-launch-video` de HyperFrames)

1. `npx hyperframes@0.8.78 init <carpeta>`. **Ojo**: instala sus propias skills de forma GLOBAL
   (`~/.claude/skills/hyperframes*`, `media-use`, `product-launch-video`) y las enlaza para otros agentes; si no
   lo quieres, hazlo en una cuenta o máquina de prueba.
2. `BRIEF.md` → captura → `frame.md` desde un preset (ajustar los colores a la marca) → `STORYBOARD.md` con
   blueprints → paquetes por escena → **un subagente por escena** → ensamblado → transiciones.
3. `npx hyperframes@0.8.78 lint` y `check` → `snapshot --at 1.5,3.5,...` (cuadros fijos y hoja de contacto)
   → revisar → `render --skill=product-launch-video --quality high --output renders/video.mp4` → copiar a
   `render/14-hyperframes_<nombre>.mp4`.

## Lo que hay que saber

- Música propia: `musica.py` y `<audio id="musica" src="assets/musica.wav" data-start="0" data-duration="N"
  data-track-index="10">` en el `index.html` raíz; en el storyboard, `music: none`. **Todo `<audio>` lleva `id`.**
- Cada frame del storyboard necesita `src:`; `asset_candidates` simples («archivo — descripción»); las
  coordenadas aparte (`coordinates:`).
- **Los `<video>` van en el `index.html` raíz**, no dentro de las escenas (`assemble-index` los rechaza); su
  movimiento en la línea de tiempo principal.
- Fuentes: no trae archivos de Space Grotesk; se usa Inter (la trae el renderizador). Otra fuente: `.woff2` en
  `assets/fonts/` antes de despachar los subagentes.
- **Contadores**: con `onUpdate` se congelan al saltar en la línea de tiempo; usar un tween de propiedad o un
  «driver» que calcule el valor desde el tiempo.
- Render: 1,5–2,5 min por 22 s. Usa la GPU.
- `.gitignore` de cada proyecto: `renders/`, `snapshots/`, `public/`, `.hyperframes/history/`.

## Verificar

- `lint` y `check` sin errores; la hoja de `snapshot` revisada escena por escena (textos que no se salen,
  contadores que llegan a su valor, videos que arrancan ya cargados).
- El MP4 con `ffprobe` (duración) y `saltos.py`; mirarlo entero con sonido.

## Nivel de estudio

- **60 fps**: `render --fps 60` (lo documenta la skill global `hyperframes-cli`; no está probado con la versión
  fija 0.8.78).
- **Canción real** en el `<audio>` del `index.html` raíz, con los tiempos de `cancion.py`, en vez de `musica.wav`;
  efectos reales como `<audio>` con `id` en el tiempo de cada evento.
- **Transiciones de estudio del registro** (`sdf-iris`, `glitch`, `grain-overlay`, `transitions-mechanical`) en vez
  de fundidos. Mirar cada bloque antes de usarlo: la guía del registro marca algunos como rotos (p. ej.
  `frosted-glass-wipe`).

## Herramientas externas (opcional)

- **Registro de HyperFrames** (libre): buscar primero con la skill global `hyperframes-registry`. Los bloques de
  vidrio líquido piden WebGPU (Brave o Chrome Canary): no se probaron.
- **Mixkit** (canción y efectos; bajar a `recursos/`).
- **No conviene**: voces o música de servicios de pago aparte si la pieza puede salir con lo local.
