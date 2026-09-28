---
name: director-de-video
description: 'Skill global de dirección. Conoce TODAS las técnicas del proyecto, elige la mejor para cada tramo de un video y COMBINA dos o tres en una misma pieza (p. ej. intro de partículas + pantalla real + cierre showreel; Blender + acabado riso + títulos; video de stock + datos encima), sobre una sola línea de tiempo y una sola pista de audio. Usar al empezar cualquier video, antes de la skill de cada técnica, y siempre que un video pueda verse mejor mezclando estilos.'
---

# Director de video (elige y combina técnicas)

Un video no tiene por qué salir de una sola técnica. Esta skill decide **qué técnica va en cada tramo** y
cómo se unen sin que se note la costura. Después se sigue la skill de cada técnica para su tramo.

## 1. Las técnicas disponibles (cada una tiene su skill con el detalle)

| Técnica | Skill | Lo que mejor hace | Render |
|---|---|---|---|
| 1 Canvas 2D | `video-html-canvas` | Diagramas y explicaciones limpias | min |
| 2 three.js | `video-threejs` | 3D sencillo en el navegador | min |
| 3 Cálculo real | `video-calculo-real` | Lo que se ve se calcula de verdad | min |
| 4 Pizarra / cuento / Manim | `video-pizarra` | Trazo a mano, libro ilustrado, diagramas estilo 3Blue1Brown | min |
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
| 18 Épica lineal | `video-epica-lineal` | Historia por épocas en trazos que se dibujan solos; papel → luz; final = principio | min |
| 19 Ensayo | `video-ensayo` | Tomas fotorrealistas lentas, 2,39:1, narración y casi nada de texto | min + imágenes |
| 20 Generativo | `video-generativo` | Una palabra decide todo (formas, colores, música); interactivo y exportable | min |

Bases por familia (leerlas también): comerciales → `video-lanzamiento`; historias → `video-historia`;
voz → `narrar-guion`; revisar y exportar → `exportar-video`.
Por explorar (sin skill todavía): persona hablando + motion graphics (ver el final de `video-lanzamiento`) y
video generado con IA.

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

## 5. Verificar

Cuadros fijos en cada puente y en el medio de cada tramo (`exportar-video`); revisar que paleta, tipografía
y ritmo no cambien de golpe entre técnicas. El MP4 final: duración con `ffprobe` y saltos con
`herramientas/saltos.py`. Si un tramo sale mal, se rehace **sólo ese tramo**.
