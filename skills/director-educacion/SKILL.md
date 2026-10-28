---
name: director-educacion
description: Subdirector de videos educativos y explicativos (clases, repasos de examen, explicativos médicos o técnicos). Va entre `director-de-video` y las skills de técnica - propone qué técnicas sirven mejor para explicar cada tramo y cómo explicar para que se entienda, sin restringir ninguna técnica. Antes de empezar pregunta si el video lleva adecuaciones (`adecuaciones-cognitivas`). Usar después de `director-de-video` en todo video cuyo fin sea que alguien entienda o estudie algo.
---

# Director de educación (subdirector)

Capa intermedia: `director-de-video` (general) → **esta skill** → skill de cada técnica. No cambia ninguna skill de
técnica ni de estilo, y no limita cuáles se usan: todas siguen disponibles. Lo que hace es **proponer** las que mejor
explican cada tramo y poner el oficio de explicar por encima. Sin adecuación pedida, el video sale igual que antes de
que esta skill existiera.

## 0. La pregunta antes de empezar (obligatoria)

Antes del guion, preguntar al usuario (aunque no lo haya dicho, porque se le puede olvidar):

> «Es un video educativo. ¿Lo hago **normal** (con el director general y esta skill), con **DUA base** (lo que sirve a
> todos: subtítulos aparte, contraste medido, voz que describe), o con **adecuación para un perfil** (autismo, TDAH,
> dislexia, ansiedad, discapacidad intelectual, sordera, baja visión, daltonismo, fotosensibilidad)? ¿Para quién es?»

- Normal → seguir con esta skill y la de la técnica, sin cambios.
- DUA base o perfil → leer también `adecuaciones-cognitivas` y aplicar sólo lo que se pidió.
- Los gustos de una persona (p. ej. colores pastel) son **su preferencia**: van al `brief.md` de ese video, no a las
  skills ni como regla para un perfil.

## 1. Qué técnica propone para cada tramo (no es una lista cerrada)

| Necesidad del tramo | Proponer primero | Por qué |
|---|---|---|
| Fórmulas, diagramas que se construyen, números que cuentan, esquemas de examen | `video-pizarra` (motor Manim: ManimCE, o ManimGX con `render_gx.py` si es una escena larga de 2D y no hace falta reanudar) | Construye al compás de la voz; control de textos encimados; corrección por frase barata |
| Cuaderno, trazo a mano, «como si escribiera en la libreta» | `video-pizarra` (motor cairo) | Calidez de clase, mano que dibuja |
| Anatomía, objetos en 3D, implantes, piezas que se arman | `video-threejs`, `video-medico` (receta 2 + 4) | Forma real; el médico necesita ver el hueso de verdad |
| Cómo funciona un sistema, un algoritmo o un instrumento (caché, índice, cola, protocolo, una válvula) | `video-maquina-isometrica` (2D claro para clases e impresos; 3D oscuro con brillo para aperturas) | La idea es una máquina que se mueve: se ve qué pasa pieza por pieza, con guardias de geometría. También sirve de escena para una pizarra en vivo (paquete de código). **No** para hueso o cuerpo real ni para personas |
| Un modelo 3D que ya existe (`.glb`: un instrumento, un equipo, una pieza) y hay que dejarlo limpio y legible | `video-maquina-isometrica` (3D: `iso3d.py glb`) | Le tira texturas y materiales, lo centra y lo apoya; lo importante se enciende. Un `.glb` médico va con `video-medico` (precisión) y se restiliza sólo para instrumental |
| Un algoritmo o fenómeno con cifras reales | `video-calculo-real` | La narración sale de los números, nada inventado |
| Una ley o mecanismo que conviene tocar | `video-explorable` | El mismo código es video y página para jugar |
| Moléculas, virus, proteínas | `video-ciencia-real` | Átomo por átomo desde la PDB |
| Historia o proceso largo por etapas | `video-epica-lineal`, `video-galeria-estilos` | Arco por épocas, el estilo cambia con el contenido |
| Un personaje que guía o actúa la idea | `video-dibujo-animado`, `video-collage`, `video-historia` | Emoción y memoria |
| Apertura o puente con fuerza | `video-particulas`, `acabado-ascii`, `video-showreel` | Gancho corto; luego se explica con calma |

Máximo 2–3 técnicas por video (regla del general). Para combinarlas, `director-de-video` sección 3.

## 2. Cómo explicar (lo que funcionó en un video médico, la red neuronal y una serie de repasos de examen)

- **Una idea por pantalla.** Lo que ya se dijo sale antes de lo siguiente. Rótulos de 1 a 4 palabras, ≥ 24 pt.
- **Dinámico, no pregunta-respuesta.** Reglas para recordar, mnemotecnias, comparaciones lado a lado, esquemas que se
  arman. Varios datos que comparten idea salen de una sola frase; los datos sueltos, en un «repaso rápido» en una
  pantalla.
- **Colores con significado fijo** en todo el video (una categoría, un color) y siempre con etiqueta o forma además del
  color.
- **Señalar lo clave justo cuando se nombra** (flecha, resaltado, énfasis de voz) y **decir en voz alta lo que se
  dibuja** (evitar «aquí» y «allí»). Son las reglas con mejor evidencia y no cambian el estilo.
- **Ejemplo completo antes de pedir algo.** Un caso resuelto y luego la regla, o la regla y su caso, nunca la regla sola.
- **Metáforas con su frase literal** al lado.
- **Ritmo de explicador**: 3–6 s por toma, una idea por toma; pausa de voz de ≥ 0,4 s entre ideas.
- **Rigor**: cada dato con fuente en `brief.md` (frase → dato → fuente); lo aproximado se rotula; contenido médico con
  `video-medico` (revisión médica antes de publicar). Si un banco de preguntas trae una clave desactualizada, el video
  dice «el banco marca X; hoy se recomienda Y» y va a una lista aparte para quien pidió el video.
- **Cierre** con lo que se cubrió; en material médico, «Material de estudio · revisión médica pendiente».

**Mostrar la idea funcionando, no escribirla** (los repasos hechos de cajas y texto se vieron flojos y el video médico,
fuerte; reglas de `generative-film` y `vox-explainer`):
- **Un mecanismo por capítulo, no una imagen.** Prueba por capítulo, escrita en el plan: «¿se podría cambiar por una foto
  de archivo o una tarjeta?». Si la respuesta es sí, se rehace hasta que muestre algo que sólo el movimiento explica
  (la causa empujando al efecto, el antes y después a la misma escala, la pieza que se despega).
- **Un objeto conductor** del tema cruza el video y cambia de función en cada capítulo (en el video médico, el hueso; en una
  clase de coagulación, la plaqueta). Los efectos de sonido salen de lo que hace ese objeto.
- **Cuando la fuente sólo afirma, se construye la demostración.** «A es mayor que B» se muestra con A y B a la misma
  escala; «el fármaco bloquea X», con X funcionando y luego bloqueado. La frase del dato va igual a `brief.md`.
- **Si la cámara entra a una imagen, algo pasa adentro** (se anota, se despega, se mueve); entrar y cortar no vale.
- La tabla de tomas lleva la columna **Receta** y pasa `tabla_tomas.py` (ver `director-de-video`): `tarjeta` a lo
  sumo un tercio del tiempo y 40 s seguidos, y al menos 3 recetas distintas. Medido: el video médico, 27 % de tarjeta
  (pasa); dos repasos de examen (ECG y coagulación), 49 % y 76 % (fallan).

## 3. Formato y voz

- Para estudiar en el teléfono: 1280×720 a 30 fps, < 16 MB (ver `exportar-video`, «Reglas de render»).
- Voz: `narrar-guion` (Supertonic M5 por omisión; ElevenLabs, que es pago, sólo con el OK del usuario). Sin música de fondo en los
  explicativos: voz + efectos por contacto.
- Duración: lo que el tema pida; los repasos de examen, ≤ 6 min por video.

## 4. Verificar

Lo de cada técnica + `critico.py --quietos tiempos.json` + hoja de contacto. Pregunta extra de esta skill: **¿se
entiende sin sonido y sin saber el tema?** Si un tramo se entiende sólo con la voz, falta imagen; si sólo con la
imagen, la voz sobra.
