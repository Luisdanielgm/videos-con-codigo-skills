---
name: video-generativo
description: 'Técnica 20. Generativo por semilla: una palabra es la semilla y decide todo (paleta, formas, simetría, tonalidad, tempo, acordes, melodía; cada letra canta su nota). Misma palabra → mismo universo. Partículas que pasan de la palabra a tres formas matemáticas y vuelven; música sintetizada con WebAudio que se exporta igual que se oye. Usar para piezas interactivas, regalos personalizados («tu nombre como universo»), aperturas de marca y experimentos.'
---

# Generativo por semilla (técnica 20)

Antes: leer **`director-de-video`**. Ejemplo publicado: `20-generativo/semilla/index.html` (interactivo:
escribes una palabra y se genera; por omisión, «luz»). Referencia de estilo: «let there be» de @MiaAI_lab en X.

## Qué hace falta

- Sólo el navegador (Chrome) para mirarlo; para exportar, el entorno `.venv`, ffmpeg y
  `herramientas/servidor.py` (lo levanta `navegador.py`). Sin audio ajeno ni imágenes.

## Probarlo

```
python herramientas/servidor.py                      # y abrir http://localhost:8790/20-generativo/semilla/?palabra=luz
VIDEOS_PARAMS="palabra=luz" .venv/Scripts/python herramientas/navegador.py exportar 20-generativo/semilla
```
La salida se llama siempre `render/20-generativo_semilla.mp4`: renombrarla por palabra. Con 60 fps:
`VIDEOS_PARAMS="palabra=luz&fps=60&sub=4"`.

## Cómo funciona

- **Semilla**: FNV-1a de la palabra (sin distinguir mayúsculas) → `mulberry32`. De ahí salen, en orden fijo:
  tempo, raíz, modo (mayor, menor, dórico, lidio, pentatónico), progresión, patrón de arpegio, motivo
  melódico, tono y esquema de la paleta, simetría (3–11) y tres formas (rosa/estrella, lissajous/onda,
  espiral/flor), giro.
- **Estructura** (16 compases): las letras aparecen una por tiempo y cada una suena con su nota → se vuelven
  partículas (`Movimiento.puntosDeTexto`) → forma A (c2) → B (c6) → C (c10, gira más rápido) → la palabra otra
  vez (c13) con la ficha del universo y «misma palabra, mismo universo».
- **Música**: `OfflineAudioContext` (pad de sierras filtradas, arpegio de triángulos, bajo, bombo, hat de
  ruido, campanas, reverb con respuesta generada por la semilla) → WAV con volumen de plataforma (RMS +
  limitador tanh). En vivo se toca ese mismo WAV (blob) con el reproductor.
- **Exportar**: la página manda el WAV a `POST /audio?video=<ruta>` (el servidor lo guarda como
  `mezcla.wav`) y recién ahí exporta los cuadros.

## Verificar

- La misma palabra dos veces da el mismo video (comparar capturas en los mismos instantes).
- **Revisar en movimiento y con audio**: la nota de cada letra tiene que sonar cuando aparece esa letra.
- `saltos.py` sobre el MP4.

## Lo que falló

- La primera etapa de la secuencia apuntaba otra vez a la palabra: las formas arrancaban dos compases tarde.
- Una rosa con pocos puntos por pétalo se veía como una línea fina: darle grosor con un desfase por partícula.
- Normalizar sólo por pico dejaba el audio en −19 LUFS: normalizar por RMS con limitador.
- Si el servidor quedó corriendo con código viejo, `/audio` da 404: reiniciarlo.

## Nivel de estudio

- **60 fps** con 4 subcuadros: las partículas y las formas giran más suave.
- **En una pieza nueva, un gancho que diga de qué trata** (el ejemplo no lo tiene: es una excepción, no la regla).
- **Palabras personales**: si la palabra es el nombre de alguien (un regalo), no publicar el video sin su permiso.

## Herramientas externas (opcional)

- No necesita ninguna: la semilla decide todo y la música es WebAudio.
- **No conviene**: una canción ajena (la música es la semilla) ni imágenes generadas.
