---
name: video-galeria-estilos
description: Técnica 21. Galería de estilos - un mismo personaje u objeto recorre en UNA sola toma una pared de 15–20 cuadros enmarcados, cada uno en un estilo de la historia del arte en orden de época (rupestre, egipcio, mosaico, vitral… hasta hoy), dibujados en Canvas 2D; dentro de cada cuadro el personaje se dibuja y se mueve en el estilo de ese cuadro, sobre la pared es él mismo, y al cruzar un borde queda mitad en un estilo y mitad en el otro. Final - la cámara se aleja, se ven todos los cuadros juntos y cada uno recupera su personaje (callback). Usar para «la historia de X en N estilos», aperturas, piezas de marca con mascota y muestrarios de oficio.
---

# Galería de estilos (técnica 21)

Antes: leer **`director-de-video`** y la base **`video-lanzamiento`** (pulsos, efectos reales, reglas anti-«slop»).
Ejemplo (no publicado en este repositorio): `21-galeria-estilos/grulla-de-papel/` (46,4 s, 129,2 BPM, una grulla de
papel por 20 estilos, de la cueva a hoy). Referencia: @chetaslua, «3000 a. C. → 2020» (video público en X).
Más fichas de estilos y movimientos, con palabras propias: `fichas-huashu.md` en esta carpeta.
Catálogo de ideas de estilos (para leer, no para copiar): el repo `lemomo-ai/lemo-opuscar` (43 estilos con su ficha).

## 1. Elegir los estilos para un tema

1. **Un estilo por época, en orden.** 15–20 cuadros; menos no da «recorrido», más no se alcanza a mirar (≈ 2 s cada uno).
2. **Que cada uno se reconozca en un vistazo** por su *material*: piedra y ocre, teselas, vidrio y plomo, pan de oro,
   hilo, tipos de madera, tubo de gas, papel continuo, cuatro verdes de LCD… Si un estilo sólo se distingue por el
   color, no sirve: cambiarlo por otro con textura propia.
3. **Variar la superficie de un cuadro al siguiente** (claro/oscuro, liso/con grilla, cálido/frío): dos vecinos
   parecidos se leen como uno.
4. **Al menos cuatro estilos de grilla** (mosaico, punto de cruz, ASCII, píxeles): ahí el personaje se «rasteriza» y es
   lo que más impresiona. **Y uno de hoy** que cierre (en el ejemplo, arte generativo: el video está hecho con código).
5. **Personaje original y neutro** (sin derechos): una grulla de papel, un barquito, un farolero. Forma simple y de
   perfil claro: tiene que leerse dibujado con 20 técnicas, a 1/5 de tamaño en el final.
6. Fechas verdaderas y aproximadas con «c.»; nada de nombres de artistas que no hagan falta.

## 2. Ficha por estilo (escribirla antes del código; en el ejemplo, un objeto de `ESTILOS`)

| Campo | Qué decide | Ejemplo (vitral gótico) |
|---|---|---|
| nombre · época | El rótulo del museo | «Vitral gótico · siglo XIII · vidrio y plomo» |
| paleta | 3–5 colores, uno de acento | azules, rubí en las enjutas, oro en el anillo |
| trazo | Cómo es la línea | plomo negro de 8–16 px alrededor de cada pieza |
| textura | Lo que lo hace material | brillo radial por pieza, vetas, sol que se mueve detrás |
| tipografía | Si el estilo trae letra, la suya | (ninguna) · cartel: Rockwell · manuscrito: Old English · esténcil: Stencil |
| marco | La moldura de la pared | negro, madera, oro, plata, blanco, gris |
| **cómo se mueve el personaje** | Lo que más vende el estilo | alas quietas en la mitad de arriba; cada faceta, una pieza de vidrio |

Formas de moverse que funcionaron: rupestre «de a tres» (cambia de dibujo 3 veces por pulso y la línea tiembla);
egipcio rígido, de perfil, alas fijas; grillas que saltan de celda en celda; cuaderno con arrepentimientos (las alas
anteriores apenas marcadas); folioscopio de dos dibujos (cartel, esténcil); neón con dos tubos que se prenden por turnos
en cada pulso; serigrafía que se corre de registro en cada pulso; constructivismo en diagonal y aleteo de onda
triangular (a máquina); low poly con los vértices pegados a una grilla de 8 px; generativo como red de puntos.

Contrato del código (Canvas 2D, coordenadas del cuadro, 1440×810): `prep(g, R)` fondo fijo (prerrenderizado una vez),
`vivo(g, b, t)` lo que se mueve del fondo, `encima(g, R)` capa fija sobre lo vivo, `grulla(g, pose, b, t)`. El
personaje es **una sola geometría** (partes con contorno y facetas con su tono) que cada estilo dibuja a su manera; los
estilos de grilla la pasan por `mascara()` (id de la parte y borde por celda, un `getImageData` chico por cuadro).

## 3. La toma continua

- **La pared es el mundo**: cuadros en una grilla de 5 × 4 recorrida en zigzag (fila 1 a la derecha, fila 2 a la
  izquierda…), así el final cabe en 16:9. La cámara pasa por los centros con un Catmull-Rom (en las esquinas curva) y
  con velocidad que nunca llega a cero: baja al 25 % en el centro de cada cuadro y sube en los bordes.
- **Grilla de pulsos**: el cuadro i queda centrado en el pulso 4i+2 y el personaje **cruza al cuadro i en el pulso 4i**
  (el primer tiempo de cada compás), con el sonido del estilo nuevo en ese pulso.
- **Dentro de cada cuadro, el personaje en ese estilo (recortado al cuadro); sobre la pared, el personaje de verdad**
  (papel con su sombra), dibujado encima de las molduras con un recorte `evenodd` que excluye los cuadros. Al cruzar
  un borde se ve mitad y mitad: ése es el corte, sin fundido.
- Al bajar de fila: cruzar el borde **en picada, de frente**, y dar la vuelta (escala en x) ya dentro del cuadro de abajo.
- **Primer cuadro terminado**: en t = 0 la cámara ya está sobre el cuadro 1 con el personaje y su rótulo.
- Rótulos de museo en la pared, debajo de cada cuadro (número, nombre, época), **grandes** (nombre ≈ 50 px en pantalla de
  1080, época ≈ 36 px, casi negro sobre blanco): a 1/3 de tamaño en un teléfono todavía se leen. Son parte de la escena.
- **Gancho**: el título corto (chico, centrado, encima del primer cuadro) está desde t = 0 y se va hacia los 4–5 s, antes de
  que algo pase por debajo; así el primer cuadro sigue «terminado» y sin sonido se sabe de qué trata. El final lo repite
  grande (cierre).

## 4. El callback

La cámara se aleja (zoom en escala logarítmica y el centro llevado por el tamaño de lo que se ve) hasta ver los 20
cuadros, el título en la pared con **una palabra de acento** y aire alrededor. El personaje sale del último cuadro
hacia la cámara: **su camino se escribe en coordenadas de pantalla** y su tamaño en pantalla casi no cambia, así nunca
sale del cuadro mientras la cámara se aleja. Cada cuadro recupera su personaje con un resorte, uno cada 0,2 pulsos,
con un tintineo por cuadro; después entra el título palabra por palabra desde una máscara.
**La grulla no se despega de golpe**: mientras la cámara se aleja se queda anclada al último cuadro (en el mundo, con su
aleteo) y recién cuando el cuadro ya es chico parte en pantalla desde donde esté, con velocidad cero (bézier que arranca
en el ancla); si no, cruza el borde a toda velocidad con el cuadro todavía grande. **La vista general no queda quieta**:
empuje lento (+5 %) y una deriva mínima hasta el último cuadro; con rótulos grandes, repartir el aire entre el título
(arriba) y los rótulos de la fila de abajo (que no queden cortados).

## 5. Música y efectos

Canción real de `recursos/musica/` con `herramientas/cancion.py` (BPM, primer tiempo, energía por compás): elegir el
compás de arranque para que **la parte más fuerte caiga en el alejamiento**. Un `mezclar.py` en la carpeta escribe
`pulsos.js` (con `inicio` negativo si t = 0 no es el pulso 0) y `mezcla.json` (un efecto real del banco por estilo:
tesela, vidrio, hoja, ola, campana, tecla…) y llama a `herramientas/mezclar.py`. La `mezcla.wav` con canción de Mixkit
va fuera de git (como en las otras técnicas).

```
.venv/Scripts/python 21-galeria-estilos/<video>/mezclar.py
.venv/Scripts/python herramientas/navegador.py capturas 21-galeria-estilos/<video> 0,4.64,8.36,…
.venv/Scripts/python herramientas/hoja.py 21-galeria-estilos_<video>
VIDEOS_PARAMS="fps=60&sub=4" .venv/Scripts/python herramientas/navegador.py exportar 21-galeria-estilos/<video>
.venv/Scripts/python herramientas/saltos.py render/21-galeria-estilos_<video>.mp4
```

## 6. Verificar

1. **Un cuadro por estilo** en su centro (pulso 4i+2) → hoja de contacto: ¿se reconoce el estilo y se lee el personaje?
2. **Cada cruce** (pulso 4i) y **cada bajada de fila**: el personaje mitad y mitad, nunca de canto justo en el corte.
3. **Tira a 4 cuadros por segundo** sobre un cruce: sin tiempo muerto, el personaje siempre en pantalla.
4. **El final**: alejamiento a medias, la recuperación de los personajes y el último cuadro (título entero, nada cortado
   por el borde, el personaje sin tapar el título).
5. **Cuadro repetido igual**: capturar dos veces los mismos instantes y comparar los píxeles (en el ejemplo, diferencia
   media 0,0000–0,0001 sobre 255).
6. Consola sin errores (`navegador.py` los muestra) y, con el MP4, `saltos.py` sin defectos.

## Errores a evitar (pasaron en el ejemplo)

- **MP4 sin fondos** (muro crema, cuadros grises, manchas negras en el primer cuadro, franjas oscuras): no es el código, es
  pérdida de contexto de GPU en el navegador del export (otro proceso usando la GPU o la cola). Los cuadros sueltos salen
  bien. Reexportar con la GPU libre y comparar un cuadro del MP4 con su captura antes de pasarlo al crítico.
- **Glifos ASCII finos sobre franjas** (impresora): grulla ilegible. Celdas grandes (14 × 22), glifo casi negro, doble
  impresión (el mismo glifo a +1 px), grulla ×1,4 y rampa cargada al lado pesado (`@@%#*+`); el aleteo muestreado a 4 por
  pulso (no a 2: alterna ±1 y se lee como salto).
- **Alas angostas**: con la raíz corta el ala se leía como una espina; raíz a lo largo del lomo y un borde de atrás
  abierto. Cuello y cola con base ancha, si no desaparecen en las grillas.
- **Personaje del mismo tono que el fondo** (grulla blanca sobre teselas crema, roja sobre la banda roja del
  constructivismo): darle al fondo otro valor o cambiar los colores del personaje en ese estilo.
- **Umbral de la máscara alto** (> 120 de alfa) o celdas grandes: las partes finas se pierden; 70 y celdas de 14 px.
- **Dar la vuelta justo en el cruce**: en el corte el personaje queda de canto (una línea) y no se ve.
- **Camino final en coordenadas del mundo**: con el zoom el personaje se iba de la pantalla; escribirlo en pantalla.
- **Luces de la pared en un rectángulo más chico que su radio**: queda un borde de luz recto en el final.
- **Título y personaje pegados al borde** en el cuadro final: dejar aire (zoom final menor que el que «cabe justo»).
- **Texto chico en las esquinas**: el número y la época van en el rótulo del museo, no sueltos sobre la imagen.
