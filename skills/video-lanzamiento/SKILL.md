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
equivalente real y como respaldo. **Cada pieza suena distinta**: kit de efectos propio por pieza (sección «Que cada
pieza suene distinta», abajo). Si la marca no quiere canción en el MP4, van sólo los efectos.

## Que cada pieza suene distinta

Con muchas piezas hechas, la música y los efectos terminan siendo siempre los mismos. Medido en un banco de unas cien
piezas: un solo `pop` era el 62 % de todos los usos de efectos y un clic el 11 %; el mismo sintetizador de `musica.py`
sonaba en 60 piezas y 6 canciones en otras 42.

- **Efectos: un kit propio por pieza.** `.venv/Scripts/python herramientas/kit_efectos.py <carpeta>` escribe `sfx/` (30 efectos:
  subida, reves, whoosh, sub, clave, brillo, tarjeta, trazo, pop, clic, con variantes) y `sfx/kit.json`. La semilla sale de la
  carpeta y elige el timbre (claves de madera, marimba, vidrio o pulsadas, bandas del whoosh, caída del sub…); lo tonal va en la
  tónica de la canción de `mezcla.json` (perfiles de Krumhansl), en tónica, cuarta y quinta. En el `efectos.py` de la pieza:
  `k = Kit(AQUI)` y `k("whoosh", t, -17)` rota las variantes y deja el **pico** del efecto en `t` (el `"alinear": "pico"` de
  `mezclar.py` sólo conoce los picos del banco).
- **Del banco compartido**, sólo Kenney (`recursos/efectos/indice.json`), para lo que el kit no sintetiza. Nunca los
  efectos gastados de siempre (`burbuja-pop`, que además es de Mixkit, ni `kenney-click-001`).
- **Música por producto**: cada marca decide en su ficha (`marca.md`) si lleva canción en el MP4 y de qué fuente (hay
  marcas que no aceptan Mixkit, y otras que agregan la canción al publicar, desde la biblioteca de la red social). Si
  no está decidido, **preguntar antes de ponerla**. Explicativos: sin cama musical. Canciones generadas con ACE-Step en
  una GPU de 4 GB sonaron desafinadas. Sin canción, el kit toma la tónica de su semilla.
- **Guardia**: al terminar, `mezclar.py` imprime `AVISO sonido repetido` si la pieza repite la canción o el set de efectos
  (Jaccard ≥ 0,5) de alguna de las 12 piezas más recientes; a mano, `herramientas/sonido_repetido.py <carpeta>` (sale 1 si
  repite). Los formatos y versiones de una misma pieza (`horizontal/`, `-v2`) no cuentan. Avisa, no corta: se arregla con
  otro kit (y, si la marca no quiere canción, sacándola).

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
   Clientes reales, empresas, colegios, alumnos: no aparecen. **Archivo de hechos**: `hechos.md` en la carpeta
   del video, una línea por cifra o afirmación con su fuente (archivo del repo o comando de git); en pantalla
   sólo va lo que está ahí. Cifras de ejemplo y todo lo generado (imágenes, interfaz inventada) **se rotula en
   pantalla** («ejemplo», «concepto»).
   Escribir en el plan una lista de «lo que no se dice» de ese producto (promesas que el código no respalda).
2. **Plan en pulsos antes del código.** BPM 104–116, 11–14 compases (25–30 s): gancho (0–1), golpe con el
   logo (2), una idea por compás (la estrella con dos), números reales (uno), cierre con logo y llamada a
   la acción (dos). Cada evento lleva su pulso. Eso da **12–15 composiciones cada 30 s, de 1,4–3,5 s cada una**:
   menos se siente lento, más se vuelve ruido. El storyboard (abajo) sale de esta grilla.
3. **Música y efectos** (`musica.json`): `bpm`, `compases`, `progresion`, `secciones` por compás (`pad`,
   `arpegio`, `bombo`, `hat`, `caja`, `bajo`), `riser` (su `pulso` es donde termina), `impacto`,
   `silencio_antes: [8, 48]` (0,1 s de nada antes de cada golpe). **Efectos de sonido** en el pulso exacto de lo
   que se ve: `clic` (un botón), `pop` (algo aparece), `whoosh` (algo cruza), `moneda`, `escaner`, `check`,
   `tecla`, `notificacion`, `burbuja`, `obturador`, `deslizar` (escucharlos: `musica.py --muestras <carpeta>`).
   Son de lo que más impresiona, con medida: **un solo whoosh suave por cambio real de escena** (no uno por cada
   cosa que cruza), **clics sólo en acciones reales** (el cursor aprieta algo que responde), nada suena sin que se
   vea, y los cortes caen en un pulso. Entregar también una **versión sólo música** (la canción sin efectos,
   remezclada con el comando de «Volumen», abajo). Formato completo en el encabezado de `herramientas/musica.py`.
4. **Animación**: `P = Movimiento.pulsos(PULSOS.bpm, PULSOS.inicio)`, `T = b => P.t(b)`; todo en pulsos.
   La composición de cada toma sale del storyboard (no de la plantilla «título a la izquierda + imagen a la
   derecha»): títulos palabra por palabra con resortes, que se van hacia arriba; logo centrado en los golpes.
   `Reproductor.iniciar({..., audio: 'musica.wav', desenfoque: 4–6})` y arrancar sólo cuando cargaron imágenes
   y fuentes (`await img.decode()`, `document.fonts.ready`). Al exportar, el servidor usa `mezcla.wav` si
   existe, antes que `musica.wav`.
5. **Puertas antes del render caro**, cada una aprobada antes de la siguiente: (a) mapa de pulsos o lista de
   estados; (b) 4–10 cuadros fijos clave (los momentos firma, el primer y el último cuadro); (c) hoja de
   contacto del video entero, con recortes ampliados de lo dudoso. Corregir y repetir; recién ahí exportar a
   60 fps y comprobar la duración con `ffprobe`. Si una parte sale mal, se rehace sólo esa parte.

## Dirigir como director (lo que recomienda @rexan_wong)

- **Nombrar un estilo con una referencia** funciona mejor que describirlo; sin referencia sale el estilo
  por defecto de la IA (texto centrado, fondo degradado, todo con fundido). Banco de referencias: whatships.com.
- **Tres storyboards** distintos antes de elegir; después **un cuadro fijo por escena** para aprobar antes de
  animar: corregir un cuadro cuesta mucho menos que un render. Cada storyboard es una tabla, una fila por
  composición:

  | Tiempo (pulsos) | Qué se ve | Para qué (la idea) | Cómo sale | Qué objeto pasa a la toma siguiente |
  |---|---|---|---|---|
  | 0–4 | La burbuja de chat llena el cuadro | Gancho: es una app de mensajes | Se encoge hacia arriba | La burbuja se vuelve el botón |

  Debajo, **tres momentos firma** descritos por lo que pasa, sin nombrar efectos («la lista se dobla sobre sí
  misma y queda el logo», no «morph con brillo»). Si una fila no tiene objeto que pase, es un corte: que sea a
  propósito.
- **Notas con palabras de cámara**, que aquí son parámetros: «zoom más lento» = bajar `hz` del resorte de
  cámara; «corte seco» = dos claves en el mismo pulso o una lista de resortes nueva; «acércate al botón» =
  `['zoom', ...]` sobre esa zona.
- Si hay UI inventada, usar componentes reales (los del producto o de una biblioteca pública como 21st.dev)
  antes que dibujarlos a ojo.

## Reglas de dirección (las que se repiten en los mejores prompts)

- **Una idea por toma.** Tres momentos extraordinarios valen más que diez mediocres: si sobra tiempo, se
  alarga un momento firma, no se agrega otro efecto.
- **Un héroe por toma** (Motion Lab): un solo movimiento orquestado manda; lo demás espera, baja al 40 % o se queda
  quieto. Los secundarios recorren el 50–70 % de lo que recorre el héroe y arrancan 100–200 ms después; el movimiento
  de ambiente, menos del 5 % del recorrido del héroe, en un seno lento que no para. `tabla_tomas.py` frena la toma
  que nombra dos héroes («la olla y la llama»).
- **El sujeto llena el cuadro**: lo que importa ocupa la mayor parte de la imagen; nada de una tarjeta chica
  en un fondo vacío.
- **El primer cuadro es una composición terminada** (nada de negro ni de un vacío que se va armando) y el video
  **se entiende sin sonido**: probarlo mudo.
- **Ocho principios de movimiento**: (1) lo que está delante se vuelve la transición; (2) un objeto lleva la
  historia de una toma a la otra; (3) un movimiento manda y los chicos van debajo, solapados; (4) la velocidad
  siempre cambia (nada a velocidad constante); (5) se corta sólo con tamaño, dirección y sujeto iguales a los
  dos lados; (6) cada acción da un resultado visible; (7) el texto también es movimiento; (8) variar la escala
  (cerca, lejos, cenital, tipo a pantalla completa).
- **Prohibidos, por su nombre** (lista viva): fundidos de opacidad, entradas con desenfoque, «revelado» de brillo,
  destellos y destellos de lente, brillo (*glow*, *bloom*, orbes de luz, neón), partículas de adorno (en la técnica 10
  son el hilo, no adorno; `M.motas` es adorno: sólo con una causa en pantalla), rebote marcado, sacudida de cámara,
  giros 3D gratuitos y plato giratorio, vidrio en todo, degradados de fondo (sobre todo morado o azul), todo entrando
  a la vez, fundido-y-subida en cada elemento, todo centrado, texto que se mueve mientras se lee, texto chiquito en
  las esquinas (contadores, «01/05», marcos de cámara), la plantilla «título a la izquierda + tarjeta a la derecha»,
  más de un color de acento, tramos quietos de más de ~0,5 s.
  **La lista crece después de cada primer render**: se mira qué usó el modelo por su cuenta, se lo nombra y se lo
  suma acá. Pedir «que no parezca hecho por IA» no sirve: cambia un defecto por otro; sirve nombrarlos
  (guía de Anthropic para Opus 5.5, citada por Motion Lab).
- **Rechaza tu resultado si parece** una plantilla de presentación, un video de stock genérico o «hecho por IA»
  (texto centrado sobre degradado, todo entra con fundido, todo a la misma velocidad). Se rehace la toma, no se
  le agrega un efecto encima.
- **Versiones de 30, 15 y 6 s**: cada una es su propia lista de escenas (su storyboard, su gancho y su cierre),
  no un recorte de la larga. La de 6 s es una sola idea y el logo.

## Los números del oficio (Motion Lab de @flxrnc)

Cada adjetivo del pedido («premium», «moderno», «fluido») se cambia por un número: si no, decide el modelo y sale su
estilo por omisión. Fuente: el artículo «Opus 5.5 Motion Lab» de @flxrnc en X. Donde ya había una regla propia medida,
se dice cuál manda.

| Qué | Número | Aquí |
|---|---|---|
| Resortes (razón de amortiguación) | 1,0 sin rebote · 0,7–0,85 «premium» · 0,4–0,6 juguetón · < 0,3 caricatura. Posición y tamaño pueden rebotar; opacidad y color, nunca | `amort` de `M.resorte` **es** esa razón. En comerciales manda «rebote < 2 %» → 0,78–0,85 (abajo, «Reglas») |
| Entradas y salidas | Entra frenando (*ease-out*), sale acelerando (*ease-in*) y **40–50 % más corta** (entrada 400 ms → salida 200 ms); cruzar la pantalla, *ease-in-out*; lineal sólo en giros, barras de progreso y la fase de un bucle | `curva.expo`/`cubica` para entrar, `expoIn` para salir, `expoInOut` para cruzar |
| Duraciones | Respuesta de interfaz 100–200 ms · movimiento de interfaz 200–500 ms · revelado del héroe 600–900 ms. En video se dice en cuadros: a 60 fps, 400 ms = 24 | — |
| Escalonados | Letras 1 cuadro · palabras 60–120 ms · ítems de lista 40–80 ms; el siguiente arranca cuando el anterior va por el 30–50 % (en fila parece robot, todo junto parece barato) | `video-forma-unica` midió palabras 40–70 ms en su ejemplo: manda lo medido |
| Texto que se lee | Quieto **≥ 0,3 s por palabra + 0,5 s** (dos palabras = 1,1 s); durante la espera, a lo sumo un empuje lento del 2 % | `tabla_tomas.py` lo revisa en cada toma |
| Cuadros por pulso | fps × 60 / BPM, **cada pulso calculado desde el tiempo y redondeado**, nunca sumando el paso redondeado (128 BPM a 30 fps = 14,06: sumando 14, a los 32 pulsos va 2 cuadros tarde). Corte en el pulso, cambio de composición en el compás (cada 4); no cambiar todo en cada pulso | `P.t(b)` ya calcula desde el tiempo |
| Cámara | Las curvas más suaves son de la cámara (*ease-in-out quart*); los objetos llevan las más vivas. Parallax 1,0 frente · 0,5 medio · 0,2 fondo. En 3D, campo de visión de 35–50° | `curva.suave` o `expoInOut` para la cámara |
| Contraste y destellos (WCAG) | Texto ≥ 4,5:1 en **cada** cuadro, también sobre fondos que se mueven; nunca más de 3 destellos por segundo | `critico.py --textos` mide el contraste |
| Sonido | El golpe suena **1 cuadro después** de su imagen, nunca antes (la luz llega antes que el sonido); −14 LUFS integrados y pico ≤ −1 dBTP | `critico.py` mide los dos; al poner un efecto, sumar 1 cuadro al instante de su imagen |
| Texto en fragmentos (skill `cinetic`, medido en 8 películas de lanzamiento) | Fragmentos de **1 a 4 palabras**, cortados donde la gramática lo permite. Entre fragmento y fragmento, **1–3 s de pura imagen** (30–90 cuadros a 30 fps). Texto en pantalla **≤ 65 % de los cuadros**, y al menos **1,5 s sin texto cada 10 s**. Lo leído queda quieto max(2 s, 1,4 s + 0,27 s por palabra), con una deriva de 0,3–1 px por cuadro, no clavado | En la tabla de tomas, las tomas con «Texto en pantalla» vacío son la imagen pura: contarlas antes del código |
| Palabras e imagen | **«La animación es el verbo»**: las palabras nunca describen lo que la imagen ya muestra («Arrastra para ordenar» sobre una tarjeta que se arrastra sobra). Prueba en silencio: sin sonido y sin el texto, ¿un extraño diría la palabra de la función («racha», «división»)? Si no, falta imagen, no texto | Va con las tres pruebas del concepto (abajo) |

**Tres pruebas del concepto, antes del código** (de la skill `cinetic`); se escriben en el plan con su respuesta:
1. **Borrado**: si se quita la demostración, ¿se sigue entendiendo el valor? Si sí, la demostración es decorado.
2. **Especificidad**: ¿la pieza sería igual de cierta para un producto más tonto o para la competencia? Si sí, falta
   lo que sólo este producto hace (su pantalla real, su cifra, su gesto).
3. **Palabra de la función**: en silencio, ¿un extraño diría la palabra de lo que hace la función? Si no, la imagen no
   la muestra.

## Nivel de estudio (lo que hace impresionantes a los videos de referencia)

Fuente principal: el prompt de motion design de @twoclipping en X (de libre uso).
- **Una sola toma**: cada escena nace de la anterior (una forma que inunda el cuadro y se contrae en la
  siguiente, texto que sube de una línea de máscara, íconos que aparecen con resorte), sin nada de la lista
  de prohibidos de arriba. Una inundación sobrepasa las esquinas y dura ~0,3 s.
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
- **Antes de la película**: las tres puertas del paso 5 del flujo.
- **Esfuerzo**: sesión larga en esfuerzo alto; varias vueltas de corrección con hojas de cuadros («ojos»).

## Reglas (lo que falló o critica la gente)

- **No demasiado rápido**: una idea por compás (≈ 2 s). **Rebote < 2 %**: en `movimiento.js` eso es
  `amort ≥ 0,78` (0,75 da ~3 %, 0,6 da ~9 %).
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
