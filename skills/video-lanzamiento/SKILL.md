---
name: video-lanzamiento
description: 'Base común de todos los comerciales de producto (20–35 s) — material verdadero del repo, plan en grilla de pulsos, música calculada con la misma grilla, efectos de sonido, dirección con referencias y storyboards, reglas anti-«slop» y verificación. Leerla SIEMPRE antes de la skill de la técnica elegida (forma única, producto 3D, partículas, datos y mapa, pantalla real, showreel, HyperFrames, app real).'
---

# Comerciales de producto: la base común

Los comerciales del proyecto original eran de productos propios y no se publican; el método sí.

## Elegir la técnica (cada una tiene su skill)

| Técnica | Skill | Carpeta | Cuándo |
|---|---|---|---|
| 8 · Forma única que se transforma | `video-forma-unica` | `08-lanzamiento/<producto>/` | Apps con interfaz: chats, botones, listas |
| 9 · Producto en 3D | `video-producto-3d` | `09-producto-3d/<producto>/` | Algo físico o datos que se vuelven objeto |
| 10 · Partículas y tipografía | `video-particulas` | `10-particulas/<producto>/` | Logo fuerte, IA, educación |
| 11 · Datos y mapa | `video-datos-mapa` | `11-datos-mapa/<producto>/` | Gestión, finanzas, logística |
| 12 · Pantalla real (web) | `video-pantalla-real` | `12-pantalla-real/<producto>/` | La web ya se ve bien: lo más creíble |
| 13 · Showreel vertical | `video-showreel` | `13-showreel/<producto>/` | Reels de 17 s: palabras, colores, logo |
| 14 · HyperFrames | `video-hyperframes` | `14-hyperframes/<producto>/` | Dirigir con storyboards; meter videos reales |
| 15 · App real del teléfono | `video-app-real` | `15-app-real/<producto>/` | Mostrar la app verdadera funcionando |

## Qué hace falta

- El entorno `.venv` (README), ffmpeg y Chrome.
- Para la pista con canción real: una canción libre en `recursos/musica/` (p. ej. de Mixkit, licencia gratuita)
  y el banco de efectos en `recursos/efectos/listos` + `indice.json` (se arma con
  `herramientas/preparar_efectos.py`; ver README). Sin ellos, `musica.py` calcula música y efectos (respaldo).
- El repositorio del producto, para sacar el material verdadero (sólo lectura).

Herramientas comunes: `herramientas/movimiento.js` (pulsos, curvas, resortes, formas, puntos de texto),
`herramientas/musica.py` (música → `musica.wav` + `pulsos.js`) y el `desenfoque` del reproductor. **La pista
final va con canción real**: `herramientas/pista.py` toma los eventos de `musica.json`, elige el tramo de la
canción para que su mayor subida caiga en el golpe del video y pone un efecto real del banco en cada evento
(→ `pulsos.js` con el BPM de la canción, `mezcla.json`, `mezcla.wav`). `musica.py` queda para los eventos sin
equivalente real y como respaldo.

```
.venv/Scripts/python herramientas/musica.py <carpeta>                    # musica.wav + pulsos.js
.venv/Scripts/python herramientas/pista.py <carpeta> recursos/musica/<cancion>.mp3 [--golpe P] [--compas N] [--energia]
VIDEOS_PARAMS="fps=60&sub=4" .venv/Scripts/python herramientas/navegador.py exportar <carpeta>   # 60 fps
.venv/Scripts/python herramientas/saltos.py render/<tecnica>_<video>.mp4
.venv/Scripts/python herramientas/navegador.py capturas <carpeta> 1.2,3.4,...
.venv/Scripts/python herramientas/hoja.py <tecnica>_<video> [t1,t2]      # hoja de contacto
.venv/Scripts/python herramientas/navegador.py exportar <carpeta>        # → render/<tecnica>_<video>.mp4
```
Una exportación a la vez (el servidor lleva una sola); capturas sí se pueden sacar mientras exporta.

## Flujo (en este orden)

1. **Material verdadero.** Leer el repositorio del producto **sin tocarlo**: landing, README, roadmap,
   instrucciones para agentes, estado de madurez, paleta, logos. Contar números reales con git. **Anotar lo que
   NO está listo** (próximamente, apagado por defecto, no probado, datos de demostración) y no afirmarlo nunca.
   Clientes reales, empresas, colegios, alumnos: no aparecen. Cifras de ejemplo: **se dice en pantalla**.
   Escribir en el plan una lista de «lo que no se dice» de ese producto (promesas que el código no respalda).
2. **Plan en pulsos antes del código.** BPM 104–116, 11–14 compases (25–30 s): gancho (0–1), golpe con el
   logo (2), una idea por compás (la estrella con dos), números reales (uno), cierre con logo y llamada a
   la acción (dos). Cada evento lleva su pulso.
3. **Música y efectos** (`musica.json`): `bpm`, `compases`, `progresion`, `secciones` por compás (`pad`,
   `arpegio`, `bombo`, `hat`, `caja`, `bajo`), `riser` (su `pulso` es donde termina), `impacto`,
   `silencio_antes: [8, 48]` (0,1 s de nada antes de cada golpe). **Efectos de sonido** en el pulso exacto de lo
   que se ve: `clic` (un botón), `pop` (algo aparece), `whoosh` (algo cruza), `moneda`, `escaner`, `check`,
   `tecla`, `notificacion`, `burbuja`, `obturador`, `deslizar` (escucharlos: `musica.py --muestras <carpeta>`).
   Son de lo que más impresiona: cada acción visible con su sonido. Formato completo en el encabezado de
   `herramientas/musica.py`.
4. **Animación**: `P = Movimiento.pulsos(PULSOS.bpm, PULSOS.inicio)`, `T = b => P.t(b)`; todo en pulsos.
   `Reproductor.iniciar({..., audio: 'musica.wav', desenfoque: 4–6})` y arrancar sólo cuando cargaron imágenes
   y fuentes (`await img.decode()`, `document.fonts.ready`). Al exportar, el servidor usa `mezcla.wav` si
   existe, antes que `musica.wav`.
5. **Verificar e iterar**: capturas en los pulsos clave, hoja de contacto, recortes ampliados de lo dudoso,
   corregir, repetir. Recién ahí exportar y comprobar la duración con `ffprobe`. Si una parte sale mal, se
   rehace sólo esa parte.

## Dirigir como director (lo que recomienda @rexan_wong)

- **Nombrar un estilo con una referencia** funciona mejor que describirlo; sin referencia sale el estilo
  por defecto de la IA (texto centrado, fondo degradado, todo con fundido). Banco de referencias: whatships.com.
- **Tres storyboards** distintos antes de elegir; después **un cuadro fijo por escena** para aprobar antes de
  animar: corregir un cuadro cuesta mucho menos que un render.
- **Notas con palabras de cámara**, que aquí son parámetros: «zoom más lento» = bajar `hz` del resorte de
  cámara; «corte seco» = dos claves en el mismo pulso o una lista de resortes nueva; «acércate al botón» =
  `['zoom', ...]` sobre esa zona.
- Si hay UI inventada, usar componentes reales (los del producto o de una biblioteca pública como 21st.dev)
  antes que dibujarlos a ojo.

## Nivel de estudio (lo que hace impresionantes a los videos de referencia)

Fuente principal: el prompt de motion design de @twoclipping en X (de libre uso).
- **Una sola toma**: cada escena nace de la anterior (una forma que inunda el cuadro y se contrae en la
  siguiente, texto que sube de una línea de máscara, íconos que aparecen con resorte). Prohibido: fundidos,
  entradas con desenfoque, «revelado» de brillo, giros 3D gratuitos, pausas de más de 1 s. Una inundación
  sobrepasa las esquinas y dura ~0,3 s.
- **Efectos de estudio** cuando el estilo lo pide: vidrio líquido (copia de la escena de atrás + mapa de
  desplazamiento SVG en tres escalas para bordes cromáticos + luz de borde; no `backdrop-filter: url()`),
  goo (desenfoque + umbral de alfa), iris de 6 hojas, glitch cromático, grano de película, tipografía variable
  (ejes de ancho y peso).
- **Material real adentro**: fotos (dos tomas alineadas para «re-iluminar») y video de stock recodificado todo
  intra (`ffmpeg -g 1`), cargado como blob URL y dibujado sólo después de `seeked`.
- **Sonido real por evento** (Mixkit, Kenney, Sonniss) en su pico medido; canción libre con drop y breakdown
  (el zoom cae en el drop); `loudnorm` −14 LUFS. Los efectos de `musica.py` son el respaldo.
- **60 fps con 4 subcuadros** mezclados y **detector de saltos de un cuadro** (`saltos.py`: picos de diferencia
  entre cuadros 3× mayores que sus vecinos).
- **Antes de la película**: mapa de pulsos + 4 cuadros fijos clave aprobados.
- **Esfuerzo**: sesión larga en esfuerzo alto; varias vueltas de corrección con hojas de cuadros («ojos»).

## Reglas (lo que falló o critica la gente)

- **Nada de texto chiquito en las esquinas** (contadores, «01/05», marcos de cámara): firma de video hecho por IA.
- **No demasiado rápido**: una idea por compás (≈ 2 s). Rebote mínimo (amortiguación ≥ 0,6), un solo color de acento.
- **Cifras que cambian** (y azares por cuadro): calcularlas con `Reproductor.cuadro(t)`, el instante del cuadro
  que se dibuja, igual en todos sus subcuadros. No con `Math.round(t * 30) / 30`: a 60 fps los subcuadros de los
  cuadros impares caen a los dos lados del redondeo y la cifra sale doble (medido: 300 de 600 cuadros).
- Que el cursor no tape lo que aprieta; escalas de gráficos fijas (calculadas con el valor final).
- La música es más larga que el video: el servidor exporta con `-shortest`.
- Volumen: `musica.py` deja ≈ −14/−15 LUFS con picos bajo −2 dBFS. Si sólo cambia la música, se remezcla sin
  volver a exportar: `ffmpeg -i video.mp4 -i musica.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest salida.mp4`.

## Verificar (todos los comerciales)

- Cada frase y cifra en pantalla está respaldada por el repositorio del producto (o dice «cifras de ejemplo»).
- Hoja de cuadros por pulso sin textos encimados, cortados ni chiquitos en las esquinas.
- MP4: duración con `ffprobe`, `saltos.py` sin defectos fuera de `--cortes`, escucharlo entero.
- Publicar es decisión de quien es dueño del producto: el video se entrega, no se sube.

## Si el video es de una persona hablando (pendiente de probar con material real)

1) transcribir con tiempos por palabra (p. ej. faster-whisper, local); 2) cortar silencios y errores; 3) planear
los golpes sobre la transcripción (dónde entra cada palabra clave, cada gráfico); 4) animar encima con este
mismo sistema; 5) verificar e iterar. Si un resultado gusta, se vuelve skill.
