---
name: director-de-video
description: 'Skill global de dirección. Conoce TODAS las técnicas del proyecto, elige la mejor para cada tramo de un video y COMBINA dos o tres en una misma pieza (p. ej. intro de partículas + pantalla real + cierre showreel; Blender + acabado riso + títulos; video de stock + datos encima), sobre una sola línea de tiempo y una sola pista de audio. Usar al empezar cualquier video, antes de la skill de cada técnica, y siempre que un video pueda verse mejor mezclando estilos.'
---

# Director de video (elige y combina técnicas)

Un video no tiene por qué salir de una sola técnica. Esta skill decide **qué técnica va en cada tramo** y
cómo se unen sin que se note la costura. Después se sigue la skill de cada técnica para su tramo.

**Subdirectores por área**: después de esta skill, leer el del área del video: `director-educacion`
(explicativos y estudio; pregunta siempre si lleva adecuaciones, ver `adecuaciones-cognitivas`), `director-marketing`
(comerciales y reels) o `director-reportes` (informes de trabajo). Proponen técnicas, no restringen ninguna, y no
cambian las skills de técnica.

## 1. Las técnicas disponibles (cada una tiene su skill con el detalle)

| Técnica | Skill | Lo que mejor hace | Render |
|---|---|---|---|
| 1 Canvas 2D | `video-html-canvas` | Diagramas y explicaciones limpias | min |
| 1 · gramática Kurzgesagt | `video-html-canvas` («Variante Kurzgesagt») | Escalas y mecanismos invisibles: la idea hecha objeto en formas planas, zoom logarítmico que atraviesa de una escala a otra | min |
| 2 three.js | `video-threejs` | 3D sencillo en el navegador | min |
| 3 Cálculo real | `video-calculo-real` | Lo que se ve se calcula de verdad | min |
| 4 Pizarra / cuento | `video-pizarra` | Trazo a mano, libro ilustrado | min |
| 5 Shader | `video-shader` | Cielos, luz, siluetas | min |
| 6 Blender | `video-blender` | Personajes que actúan, luz y agua reales | **horas** |
| 7 Riso | `acabado-riso` | Acabado de impresión sobre cualquier tramo | min |
| 8 Forma única | `video-forma-unica` | Interfaz que se transforma sin cortes | min |
| 9 Producto 3D | `video-producto-3d` | Objetos del producto, datos como objeto | min |
| 10 Partículas | `video-particulas` | Logos y palabras de partículas | min |
| 11 Datos y mapa | `video-datos-mapa` | Globo, rutas, gráficos vivos | min |
| 12 Pantalla real | `video-pantalla-real` | La web verdadera con zoom y cursor | min |
| 13 Showreel | `video-showreel` | Reels verticales tipográficos | min |
| 14 HyperFrames | `video-hyperframes` | Storyboards, escenas probadas, video adentro | 1–3 min |
| 15 App real | `video-app-real` | La app verdadera del teléfono | tiempo real |
| 16 Collage | `video-collage` | Libro ilustrado de papel: stickers generados, papel rasgado, carteles con cinta | min + imágenes |
| 17 Archivo | `video-archivo` | Documental con archivo real en B/N + interfaz de datos y glitch, al ritmo | min |
| 17 · gramática Vox | `video-archivo` («Mesa con evidencia») | Un argumento con pruebas reales sobre una mesa: recortes, fotos, documentos, hilo rojo; trazos a 12 fps sobre cámara suave | min |
| 18 Épica lineal | `video-epica-lineal` | Historia por épocas en trazos que se dibujan solos; papel → luz; final = principio | min |
| 19 Ensayo | `video-ensayo` | Tomas fotorrealistas lentas, 2,39:1, narración y casi nada de texto | min + imágenes |
| 20 Generativo | `video-generativo` | Una palabra decide todo (formas, colores, música); interactivo y exportable | min |
| 21 Galería de estilos | `video-galeria-estilos` | La historia de algo (o una mascota) en 15–20 estilos de época, en una sola toma por una pared de cuadros | min |
| 22 Ciencia con datos reales | `video-ciencia-real` | Una molécula o un virus de la base PDB átomo por átomo, con zoom de potencias de diez y cifras medidas | min |
| 23 Dibujo animado a mano | `video-dibujo-animado` | Un personaje que actúa (hoja de modelo, poses, emociones) en acuarela y tinta que tiembla | min–15 min |
| 24 Juego grabado | `video-juego` | Un juego chico que juega un programa, vertical, con gancho y marcador; sonido de los mismos eventos | min |
| 25 Explorable | `video-explorable` | Una ley o un mecanismo con cálculo real que el público manipula; el video es su recorrido guionado | min |
| 26 Máquina isométrica | `video-maquina-isometrica` | Un concepto técnico explicado con una **máquina inventada** cuyo funcionamiento ES la idea (caché = cajonera con reloj de arena). Dos acabados: **claro editorial** (Anatomy) y **oscuro con brillo** (ISO-GLOW). Dos motores: 2D en canvas (`iso.js`, 40–150 piezas, guardias de líneas/orden/cruces) y **3D real** (`iso3d.js`: sólidos biselados con luz, cámara isométrica, un acento que brilla, y el `.glb` propio limpiado y restilizado). El mismo código es video (`render(t)`) e interactivo (`?explorar=1`) y se entrega como paquete de código a otra aplicación | min |
| (post) ASCII | `acabado-ascii` | Acabado de terminal sobre cualquier tramo: glifos que siguen la forma, con revelado desde la imagen real | min |

Bases por familia (leerlas también): comerciales → `video-lanzamiento`; historias → `video-historia`; **médicos**
(anatomía real + implante + diagramas; combina 2 y 4) → `video-medico`;
voz → `narrar-guion`; exportar y revisar → `exportar-video` (con el **crítico ciego** de la sección 6).
**Números del oficio, prohibidos por su nombre y «un héroe por toma»** (Motion Lab): la tabla y la lista viva
están en `video-lanzamiento`; valen para cualquier video, no sólo para comerciales.
**Efectos compartidos** para cualquier técnica de navegador (`herramientas/efectos/`, deterministas): `disolver.js`
(sale un texto sin fundido), `velocidad.js` (desenfoque por velocidad), `vidrio.js` (vidrio líquido),
`simulaciones.js` (Physarum, Gray–Scott, marmoleado, cáusticas). three.js r186 con WebGPU es opcional (skill `video-threejs`).
**Dos motores en la técnica 4:** la pizarra Manim corre con **ManimCE** (por omisión, con render por tramos y caché) o con
**ManimGX** (`herramientas/render_gx.py`: ~4,6× más rápido y ~60 MB en disco contra 368, pero 1,7× más RAM, sin `-n` y salida a cuadros
fijos); la escena es la misma (`from motor_manim import *`). Elegir GX para escenas largas de 2D sin necesidad de reanudar; ManimCE si hace falta
el render por partes o LaTeX. **Páginas ajenas que animan con el reloj real** (los ejemplos de Anatomy) se graban a cuadros exactos con
`herramientas/grabar_reloj.py`; las propias no lo necesitan (cada cuadro es `render(t)`).
Las 26 técnicas tienen skill.
Por explorar: persona hablando + motion graphics y video generado con IA.

**Oficio narrativo** (de los videos que impresionan): arco con épocas o actos, una palabra de acento por
titular, estilo que cambia con el contenido, callbacks (el último cuadro repite el primero), piezas de 1:30–3:00
cuando el tema lo merece.

## 2. Decidir

1. **¿Qué tiene que sentir quien mira en cada tramo?** Gancho (sorpresa), explicación (claridad), prueba
   (credibilidad), emoción (personajes), cierre (marca). Partir el guion en tramos por esa función.
2. **Elegir por tramo la técnica que mejor hace eso** (tabla de arriba). Credibilidad → pantalla real o
   app real; emoción → Blender o cuento; gancho → partículas, forma única o showreel; datos → cálculo real
   o datos y mapa.
3. **Máximo 2–3 técnicas por video.** Más se ve como un collage.
4. **Presupuesto de render**: si un tramo necesita Blender, planear borradores por partes con la GPU libre
   (Blender no se corre junto con otra cosa que use la GPU, como un render de HyperFrames).
5. **Antes de elegir, leer de cada técnica candidata** sus secciones «Nivel de estudio» (lo que le falta
   para verse de estudio) y «Herramientas externas (opcional)» (qué la sube, qué hace falta y su límite).

## 3. Combinar sin costuras

- **Una sola línea de tiempo**: el guion con sus tiempos (`tiempos.js` en historias y explicativos,
  `pulsos.js` en comerciales). Cada tramo sabe su inicio y su fin en segundos o pulsos, y se renderiza
  **solo**, a la misma resolución y fps.
- **Una sola pista de audio para todo el video** (voz + música + efectos), hecha antes que los tramos.
  Los tramos se ajustan al audio, nunca al revés. Los efectos van en el pulso de lo que se ve, aunque el
  tramo lo haga otra técnica.
- **Biblia de estilo común**: paleta, tipografía, color de acento y forma de los títulos iguales en todas
  las técnicas (se anota en el plan antes de empezar).
- **Puentes entre técnicas**: el último cuadro de un tramo y el primero del siguiente comparten algo (un
  color que llena la pantalla, una forma, el logo, un zoom que continúa). Mejor que un fundido genérico.
- **Ensamblado**: tramos como clips en HyperFrames (`<video>` en el `index.html` raíz, con transiciones)
  o con ffmpeg + la pista de audio común. Con ffmpeg, dos tramos de igual resolución y fps:
  ```
  ffmpeg -i tramo1.mp4 -i tramo2.mp4 -i audio.wav -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.3:offset=<fin1-0.3>[v]" -map "[v]" -map 2:a -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -shortest salida.mp4
  ```
  (con cortes secos, `concat` en vez de `xfade`). El acabado (riso, grano) puede aplicarse a un tramo o a
  todo el video al final.

## 4. El plan que se escribe antes de tocar código

```
Video: <título> · <duración> · <formato>
Biblia de estilo: paleta, tipografía, acento, títulos
Audio: voz (modelo y voces), música (calculada o canción libre), efectos por pulso
Tramos:
  0,0–3,5  gancho       → técnica 10 (partículas): el logo se arma
  3,5–18,0 prueba       → técnica 12 (pantalla real): la web real con zoom
 18,0–22,0 cierre       → técnica 13 (showreel): marca y URL
Puentes: 3,5 el logo vuela a la esquina de la laptop; 18,0 zoom al botón que se vuelve el fondo
Render: qué tramos son largos (Blender) y cuándo se hacen
```

### Tabla de tomas: se revisa antes del código

Después del plan y **antes de escribir una línea de animación**, `<carpeta>/tomas.md`: una fila por toma. Si una fila no
se puede llenar (no hay un objeto que señalar o no hace nada), esa toma todavía no está pensada.

```markdown
Video: Por qué hierve el agua · Duración: 20 s · Formato: 16:9
Estilo: canvas plano, tinta azul sobre papel crema, un solo acento naranja

| Tiempo | Héroe (qué se ve) | Qué hace | Cámara | Texto en pantalla | Técnica | Receta |
|---|---|---|---|---|---|---|
| 0–3 | la olla en la hornalla | la llama se enciende debajo | quieta | | 1 canvas | mecanismo |
| 3–7 | una molécula de agua | vibra cada vez más rápido | acercamiento rápido | Más calor, más vibración | 1 canvas | acercamiento |
```

- **Héroe**: un sustantivo que se puede señalar en la imagen (no «título», «texto», «fondo», «lista»), y uno solo.
- **Qué hace**: un verbo del héroe («se parte», «sube»), no «aparece» ni «se muestra».
- **Cámara**: quieta, acercamiento rápido, paneo, golpe o corte; no una deriva lenta para rellenar.
- **Texto en pantalla**: lo que cabe en la toma (0,3 s por palabra + 0,5 s); la frase entera va en la voz.
- **Receta**: la composición, una palabra: `tarjeta` (texto, cajas o íconos quietos), `mecanismo` (la cosa funcionando),
  `construccion`, `transformacion`, `comparacion` (misma escala o antes y después), `acercamiento`, `escala`, `dato`
  o `real` (material real recorrido). `tarjeta` no pasa de un tercio del tiempo ni de 40 s seguidos, y con 5 tomas o
  más hay al menos 3 recetas distintas: es la guardia contra «puro cuadritos y texto» (calibrada con un video médico
  variado contra dos clases de repaso hechas de tarjetas). Repetir receta seguida sí vale.
  **Sólo para videos educativos**: en marketing la fuerza está en la pantalla real y los cortes (un comercial de pantalla
  real puede fallar la guardia y ser visualmente fuerte), así que ahí «recetas» se lee como aviso, no como bloqueo.
- La primera toma ya es una escena (alguien o algo haciendo algo del tema), no un título; la última termina en una
  acción del protagonista, no en una tarjeta centrada con la frase.

```
.venv/Scripts/python herramientas/tabla_tomas.py <carpeta>/tomas.md [--total 20] [--estricto]
.venv/Scripts/python herramientas/tabla_tomas.py --probar
```

Dice «ok» o «FALLA» por toma y el total: tiempos encadenados desde 0, cada toma de 0,5 a 12 s, un solo héroe que no es
maqueta, una acción que no es «aparece», el texto que cabe, la suma igual a la duración y las recetas (columna presente,
tope de `tarjeta` en tiempo y en racha, y variedad mínima). **Con una FALLA no se empieza el código.** `--estricto` es
el carril de los modelos que no son el más fuerte (y del benchmark): tomas de 8 s como máximo.
Lo que no mide (un mismo ejemplo de punta a punta, el mismo estilo en todas, que la receta declarada sea la que de
verdad se ve) se mira a ojo en la hoja de contacto. Idea de huashu-art-motion (alchaincyf, MIT: `镜头表模板.md` + `storyboard_lint.py`), escrita de
nuevo para este proyecto.

**Piezas largas (≥ 1 min): el guion del director** completa el plan con:
- **La película en una línea**: de qué trata y su gracia; cada decisión se contrasta con ella.
- **Referencias**: qué se conserva y qué se empuja de cada una (escalera abajo).
- **Herramientas**: skills, modelos y presupuesto.
- **Biblia del personaje**: proporciones, paleta medida de una hoja, expresiones y un **candado de identidad** (lo que
  no cambia nunca) que sobrevive a cada cambio de estilo.
- **Hoja de pulsos**: actos con tiempos, gancho en los primeros 2 s, un momento fuerte cada 3–5 s.
- **Texto en pantalla**: cuándo va enorme y cuándo como subtítulo; la composición le deja lugar.
- **Etapas que no se saltan**: plan → armado → cuadros fijos → animatic → pasada completa → pulido → audio → render.
- **Crítica**: cuadros fijos con puntaje, los 3 peores problemas, arreglar, repetir hasta que todos tengan ≥ 8; y el
  crítico ciego (sección 6) en cada render.
- **Entregables**: MP4, prueba de bucle (el último cuadro empalma con el primero, si es bucle), cuadro de póster,
  hoja de contacto y fuente limpia con su README.

**Escalera de referencias** (nombrar un estilo vale más que describirlo): *un cuadro* → decir qué se toma (paleta,
tipo, grano) y qué no (el sujeto); *un video* → desmontarlo antes de codificar con
`.venv/Scripts/python herramientas/desmontar.py <video.mp4>` (hoja de cuadros, diferencias entre cuadros, cortes, grilla
de pulsos si hay audio y un mapa de calor por toma: qué se mueve adentro de cada una; resumen en `render/desmontar/<video>/`)
y describir el ritmo toma por toma; sirve también sobre un MP4 propio, para ver si los cortes caen en el pulso; *una biblioteca propia* → escribir primero `style_guide.md` a partir de ella. **Contagio del brief**: el
prompt de una línea («showreel de…») sólo prueba el motor, no la idea; cientos de esos riman entre sí.

**Tercera pasada por X, GitHub y webs**, lo que sumó y no estaba:
- **Esfuerzo**: la guía de Anthropic para Sonnet 5.5 (claude.dev/blog/building-with-claude-sonnet-5-5) dice empezar en
  `high` (o `medium` si la tarea está bien especificada) y subir a `xhigh`/`max` sólo si una medición muestra ganancia;
  a esfuerzo bajo, pedir «comprobaciones reales que ejerciten el cambio» antes de dar algo por terminado. Los one-shot
  virales corrieron en `xhigh`/`max`: usarlos en la pasada larga de un video entero, no en cada arreglo.
- **No pedir el video en un prompt** (@borjaperfra, `launch-video-kit`, MIT): idea → guion de tomas con movimiento, texto
  y pausas → recursos (diseño en HTML/CSS) → música y voz → 2–3 iteraciones. Que el modelo no invente: «no son buenos
  creativos». La voz se genera **antes** de montar; **sólo se subtitula lo que no se ve** (no repetir el texto que ya
  está en pantalla); la cámara hace movimientos breves y de posición, no deriva continua; todo se verifica con métricas.
- **Reconstruir desde una referencia** (@JurgenPloeger): darle al modelo el video y el archivo de diseño (Figma) y que
  rearme cada escena en código con los cortes en el compás de la música; sirve para ver si la skill llega a un nivel humano.
- **Reglas de revisión de `motion-reel`** (alesha-pro/tools, sin licencia declarada: sólo leer): legibilidad a **360 px**
  de ancho; comprensible sin sonido; costura de bucle = mismo estado **y derivada** (posición, velocidad, visibilidad,
  cola de audio); **a lo sumo 3 rondas** de revisión; «8/10» sin una observación visual no es un criterio de aceptación
  (tabla de evidencia: tiempo, dimensión, defecto visto, cambio, cómo se verificó); la prueba de determinismo compara
  hashes de píxeles tras saltos fuera de orden y recargas (aquí: `herramientas/determinismo.py`).
- **Modelo sin visión = revisión visual NO hecha** (`javascript-animation`, iart-ai, MIT): si el modelo no recibe imágenes,
  lo dice en el informe y no da por revisadas las hojas; las guardias medidas (`critico.py`, `saltos.py`,
  `verificar_export.py`, `determinismo.py`) siguen valiendo y las hojas quedan para quien sí vea. Si el resultado sale tosco,
  decir que un modelo más fuerte probablemente ayudaría, no afirmar que es lo mejor posible.
- **Ritmo por forma y causa entre tomas** (mismo repo): toma típica de comedia o impacto 1–3 s, historia 2–5 s, explicador
  3–6 s (una idea por toma), ambiental o poema 5–10 s con fundidos largos; «una toma larga está bien, una larga donde nada
  vive no». Cada beat lo causa el anterior («hacer A provoca B», no «hace A y nota B»); la metáfora se dibuja en la imagen,
  no en una etiqueta al lado; el remate va en su propia toma y la reacción en otra, cortando en un pulso. Después del
  primer render: una captura en el instante de acción de **cada toma** leída contra su fila del storyboard.
- **Choque de textos como medida**: cada caja de texto y objeto clave se «reclama» con su tiempo y rectángulo, y una
  revisión lista los choques con sus tiempos (el ojo los pasa por alto: un rótulo sobre el borde de un monitor pasó dos
  miradas humanas). Aún no hay herramienta propia para Canvas (propuesta: `herramientas/disposicion.js` + chequeo);
  `critico.py --textos` sólo mide contraste.
- **Cada efecto visible, un cursor o una causa en pantalla** (productos): quien mira debe ver qué control lo disparó.
- **Referencias de diseño** que citan los que más vistas tienen: modulify.ai/templates, wedoflow.com, landdding.com,
  motionin.design (secciones de movimiento). Duración que más gusta: 15–32 s; las de 2+ min tienen menos «me gusta» y más vistas.

**Subagentes en paralelo**: el principal escribe primero `guia_animacion.md` (resortes, tipos, paleta, reglas) y
`storyboard.md`, y cada subagente los lee antes de su escena. En piezas largas, **un archivo por capítulo** (p. ej.
`cap/c01.js`) registrado con su inicio y fin; la guía es el contrato: cada subagente toca sólo su archivo, un
error en algo compartido se reporta y no se edita (la guía lista qué es compartido), funciones puras de `t`, zonas
prohibidas del cuadro (la de subtítulos), presupuesto de segundos por cuadro, y revisión del primer y último cuadro de
cada toma y de los bordes del capítulo. Cada uno usa **su propio puerto** del servidor (dos servidores en el mismo
puerto se roban los cuadros del exporte: ya pasó).

**Hoja de pulsos con columnas de oficio**: tiempo · qué nota quien mira · acción → estado final · cámara (y qué NO
se mueve) · exposición (de a uno, de a dos, pausa) · sonido (en el contacto: 1 cuadro **después** de la imagen, regla
de Motion Lab; el curso decía 0,03 s antes) · **salida** (cómo deja
la toma). El momento clave de una toma va en el medio, no al final; un corte tiene que sumar información; el
sentimiento se escribe como conducta («la antena cae, el cuerpo baja 6 px»).

**El guion es la única fuente de tiempo** en los narrados largos: cada escena con `pre`, `tail` y sus frases con
pausa; la duración medida de cada frase (`tiempos.json`) arma la línea de tiempo entera. El sonido se deriva de las
tomas (un golpe en la imagen da su efecto, con distancia y paneo respecto de la cámara). Render por bloques de ~10 s
reanudable (`VIDEOS_PARTE`), conservando los bloques ya hechos.

**Tres puertas con revisor**: storyboard y cuadros clave → **la muestra más difícil de 2–4 s** renderizada entera →
película. Y un registro de crédito: qué hizo cada herramienta y de dónde salió cada píxel (código, archivo, generado).

**Formatos**: 16:9, 9:16 y 1:1 salen de una función de composición (cada escena se acomoda al formato: tipo e
interfaz se reubican), nunca recortando el 16:9.

**Resortes por carácter** (`M.resorte` de `movimiento.js`): ágil (botones, toggles) `hz 3, amort .8`, rebote ~1,5 %;
normal (tarjetas, contenedores, cámara) `hz 2, amort .75`; pesado (tipo grande, 3D, logo) `hz 1.2, amort 1`, sin
rebote; juguetón (mascotas, stickers) `hz 2.5, amort .45`, rebote visible.

Fuente de esta parte: curso de @0xMovez «How to build motion design studio with Opus 5.5» (X).

## 5. Verificar

Cuadros fijos en cada puente y en el medio de cada tramo; revisar que paleta, tipografía y ritmo no cambien
de golpe entre técnicas. Si un tramo sale mal, se rehace **sólo ese tramo**.

## 6. Barra de calidad y cuándo se llama al crítico

Medida por `herramientas/critico.py` sobre el MP4 final (método completo y prompt: `exportar-video`, «Crítico ciego»):

| Medida | Meta |
|---|---|
| Pantalla congelada | ≤ ~1 s por cada 30 s; ningún tramo quieto > ~0,5 s (salvo pausas de voz ≥ 400 ms marcadas) |
| Primer cuadro | una composición terminada: ni negro, ni vacío, ni a medio entrar |
| Sonido | ≈ −14 LUFS integrados (± 2), pico verdadero ≤ −1 dBTP, sin recorte; ningún corte entra más de +8 dB sobre los 4 s anteriores (susto) |
| Texto | contraste ≥ 4,5:1; nada que choque o vuele a través de otro texto |

Lo que no se mide y también es barra: **se entiende sin sonido** (mirarlo en silencio) y **un video sin errores no
es un buen video** (pasar los números es el piso, no la meta).

**Crítico ciego** (un subagente nuevo cada vez): después del plan o storyboard, después de cada tramo o escena (en
los combinados, también en cada puente: las hojas densas de los cortes) y después de cada render. No se entrega con
un P0 o P1 abierto.
