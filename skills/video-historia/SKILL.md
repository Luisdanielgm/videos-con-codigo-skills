---
name: video-historia
description: 'Cuenta una escena de una historia (un cuento, un capítulo de un libro) en video narrado con varias voces, ambiente y música sintetizados, en cualquiera de las técnicas del proyecto (Canvas 2D, three.js, shader WebGL2 o cuento ilustrado con cairo). Usar cuando piden un video narrativo en vez de explicativo.'
---

# Video de una historia

En el proyecto original se hizo la misma escena (1:49, narrador + dos personajes, ambiente y música) en cuatro
técnicas con el mismo guion y el mismo audio: Canvas 2D, three.js, shader WebGL2 y cuento ilustrado con cairo.
Esa escena no se publica (adaptaba un libro con derechos); lo que sigue es el método y lo que falló.

## Qué hace falta

- El entorno `.venv` con las voces (skill `narrar-guion`), numpy y scipy (para `sonido.py`), ffmpeg y Chrome
  (o sólo Python y cairo si es cuento ilustrado, `video-pizarra`).
- **Una historia que se pueda usar**: propia, de dominio público o con permiso. Si la obra tiene derechos, se
  adapta con palabras propias y el video es de uso personal (ver paso 1).

## Qué cambia respecto de un video explicativo

| Explicativo | Historia |
|---|---|
| Una voz | Narrador + una voz por personaje (`personajes` en `guion.json`) |
| Silencio de fondo | Ambiente, música y efectos (`sonido.json` → `mezcla.wav`) |
| Escenas que se funden | **Un solo lugar** que la cámara recorre (planos, cortes), o páginas de libro |
| Títulos de sección | Nada de rótulos: sólo el título al principio y «Continuará…» al final |
| Subtítulos blancos | Subtítulos del color de quien habla |

## Pasos

1. **Elegir la escena** (60–120 s) y adaptarla **con palabras propias**: si la obra tiene derechos, no
   copiar frases del libro, sólo los hechos (quién, dónde, qué pasa). Diálogos cortos y reescritos.
2. **Guion** con personajes (`guion.json`, ver `narrar-guion`): el narrador cuenta, los personajes
   dicen frases de una línea. Una frase = un plano o un paso de la acción. Ejemplo:
   ```json
   {"voz": "supertonic:M5", "pausa": 0.6,
    "personajes": {"nina": {"voz": "ef_dora", "tono": 3}, "abuelo": {"voz": "em_santa", "tono": -1}},
    "segmentos": [
      {"id": "titulo", "texto": "El faro. Capítulo uno."},
      {"id": "llega", "texto": "Esa noche, el mar estaba más callado que nunca."},
      {"id": "pregunta", "quien": "nina", "texto": "Abuelo, ¿por qué se apagó la luz?"}]}
   ```
3. **Narración**: `.venv/Scripts/python herramientas/narrar.py <carpeta>` (skill `narrar-guion`).
4. **Sonido**: escribir `sonido.json` y correr
   `.venv/Scripts/python herramientas/sonido.py <carpeta>` → `mezcla.wav`. Pistas: `mar`, `viento`,
   `musica` (animo `calma` | `misterio` | `magia`), `descenso`, `silencio`, `brillo`, `nado`,
   `whoosh`, `latido`. Se ubican por frase (`desde`/`hasta`, o `en` + `f`). La mezcla baja sola la
   música cuando alguien habla. La exportación usa `mezcla.wav` si existe. Ejemplo:
   ```json
   {"pistas": [
     {"tipo": "mar", "desde": "titulo", "hasta": "fin", "vol": 0.5},
     {"tipo": "musica", "desde": "titulo", "hasta": "pregunta", "animo": "misterio", "vol": 0.4},
     {"tipo": "silencio", "en": "llega", "f": 0.1, "dur": 4, "vol": 0.3}]}
   ```
   Todo se sintetiza con numpy: no hay archivos de audio ajenos.
5. **Imagen** con la técnica elegida (su skill: `video-html-canvas`, `video-threejs`, `video-shader`,
   `video-pizarra`, `video-collage`, `video-blender`), con las reglas de abajo. En HTML: `audio: 'mezcla.wav'` y
   `Reproductor.subtitulos(ctx, t, TIEMPOS, { nina: '#ffd98a', abuelo: '#a9d4ff' })`; en cairo,
   `pz.colores = {"nina": (1, .85, .54)}`.
6. **Revisar** con capturas y hoja de contacto (skill `exportar-video`) y **exportar**.

Para repetir la misma escena en otra técnica, copiar `guion.json`, `sonido.json`, `narracion.wav`,
`mezcla.wav` y `tiempos.js`: todas quedan con el mismo audio y se comparan de a iguales.

## Reglas de continuidad (lo que falló en el proyecto original)

1. **Un mundo, una cámara.** Personajes y lugares con coordenadas fijas; los planos son movimientos
   de cámara (claves `[t, x, y, zoom]`; dos claves casi juntas = corte). Así nadie cambia de lugar entre planos.
2. **La cámara se calcula antes que los personajes** en cada cuadro. Si un personaje mira a la cámara
   y la cámara se mueve después, mira la del cuadro anterior y el video deja de ser determinista (pasó en 3D).
3. **Apuntar al punto correcto del cuerpo**: en un primer plano del pecho, la cámara mira el pecho,
   no la cabeza. Calcular la altura real de ojos y pecho a partir de la cadera y la pose.
4. **Lo que dice la voz se ve**: «no hizo ningún ruido» → anillos en el agua y el ambiente baja
   (`silencio`); «el corazón a mil» → el plano late y suena `latido`.
5. **La noche no puede dejar caras negras**: en 3D, luz de relleno que sigue a la cámara.
6. **Cambios de lugar grandes** (de la roca a la playa) con un fundido, no con un salto.
7. **Brazos y piernas**: comprobar el signo de la rotación de cada lado (en 3D el brazo izquierdo gira al revés).
8. **Personajes sentados en una repisa**: dibujar la roca debajo; si no, flotan sobre el mar.
9. **Franjas panorámicas** (si hay): nada importante detrás; la luna y lo que entra por arriba
   tienen que quedar dentro de la imagen.
10. **Trazos a mano en primer plano**: al ampliar un personaje, el grosor y el temblor del trazo no
    se amplían (dividir por la escala).

## Verificar

- Capturas de todas las frases; ninguna con los defectos de `exportar-video` ni de la lista de arriba.
- El subtítulo de cada frase sale del color de quien habla.
- El MP4 dura lo mismo que `TIEMPOS.total`; escucharlo entero (la música baja con cada voz).
