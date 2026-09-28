---
name: video-collage
description: 'Técnica 16. Collage de papel con imágenes generadas: cada elemento se genera aparte (fondo sin personajes; personajes y objetos sobre verde croma), se recortan como sticker con borde blanco (herramientas/recortar.py) y el código los anima en canvas: fondo partido en capas de papel rasgado con parallax, sombras de papel, entradas con resorte, carteles con cinta, estrellas de papel y temblor de stop motion. Usar para historias y cuentos con aspecto de libro ilustrado, y para explicar algo con personajes.'
---

# Collage de papel con imágenes generadas (técnica 16)

Antes: leer **`director-de-video`** y, si es una historia, **`video-historia`** (voces y guion). No hay
ejemplo publicado de esta técnica (el del proyecto original era una escena de un libro con derechos).
Referencia de estilo: mitos contados con imágenes generadas y animación en código publicados en X (p. ej. los
de @scisterna).

## Qué hace falta

- Un **generador de imágenes** (ver paso 1), el entorno `.venv` (README: numpy, scipy y pillow para
  `recortar.py`), ffmpeg y Chrome.

## 1. Imágenes: una por elemento, nunca la escena armada

- **Fondo**: el lugar SIN personajes, sin texto, 16:9. Pedir dónde va el horizonte y cuánto ocupa el
  suelo (p. ej. «horizonte a un 45 %, arena en el cuarto inferior»): el código lo parte ahí en capas.
- **Personajes y objetos**: cada uno en su imagen, de cuerpo entero, **sobre verde croma liso #00FF00** sin
  sombras ni degradado. Pedir hacia qué lado mira (igual puede salir al revés: el código lo espeja).
- **Mismo estilo en todas**, escrito igual en cada pedido: «collage de papel recortado y fieltro de libro
  ilustrado infantil, textura de papel visible, colores cálidos».
- **Generador**: si tienes una suscripción de ChatGPT, puedes conectar Codex para que haga las imágenes:
  ```
  codex exec --skip-git-repo-check -s workspace-write -C <carpeta> "Usa tu herramienta de generación de imágenes (no dibujes con código). Genera ... Guárdala como PNG en imagenes/crudas/<nombre>.png"
  ```
  Tarda ~2 min por imagen; se pueden pedir varias en una llamada. A veces devuelve transparencia en vez del
  verde y después «lo corrige»: `recortar.py` sirve para los dos casos. O usa cualquier otro generador de
  imágenes, en la nube o local, que se pueda llamar desde la terminal (el agente busca cómo conectarlo). Elegir
  por: que respete el verde liso, que mantenga el estilo entre pedidos y que su licencia permita el uso que le
  vas a dar (algunos modelos locales son sólo para uso no comercial).
- Crudas en `imagenes/crudas/` (fuera de git), listas en `imagenes/`.

## 2. Recortar

```
.venv/Scripts/python herramientas/recortar.py imagenes/crudas/nina.png imagenes/nina.png [--borde 14]
```
Quita el verde con borde suave, le saca el reflejo verde al contorno, borra motas sueltas, pone el borde
blanco de sticker y recorta al contenido. **Revisar cada recorte sobre un fondo oscuro** antes de animar.

## 3. Audio y tiempos

Como en `video-historia`: `guion.json` con personajes → `herramientas/narrar.py` → `narracion.wav` +
`tiempos.js`. Después `herramientas/sonido.py <carpeta>` (ambiente y música sintetizados) → `mezcla.wav`.
Si las voces vienen de otro modelo que ya entrega un fragmento entero, sacar los tiempos de cada frase de sus
silencios (pausas de ≥ 0,6 s; algunos modelos dejan silencios internos más cortos) y escribir `tiempos.js` con el
mismo formato (`narrar-guion`).

## 4. Animar (canvas 2D, `herramientas/reproductor.js`)

- **Capas de papel rasgado**: el fondo se dibuja 3 veces, recortado por un borde rasgado (ondas grandes +
  dientes chicos) en cielo, mar y suelo. Cada pieza lleva sombra hacia la de atrás y un filo blanco (el
  alma del papel roto). Encima, textura de papel en `multiply`.
- **Parallax**: la cámara mueve x y zoom según la profundidad de la capa (cielo .2, mar .5, suelo .8,
  personajes 1). La inclinación hacia el cielo mueve todas igual (es un giro, no un desplazamiento).
  Detrás del cielo, papel azul de noche para cuando la cámara sube.
- **Stickers**: sombra de papel (desenfoque 18, desfase 9/12), entrada con resorte que se pasa y vuelve.
- **Stop motion**: las poses cambian 8 veces por segundo (`paso(t)`), con un temblor chico por sticker;
  un personaje asustado tiembla más. El grano del papel también cambia con cada pose.
- **Carteles con cinta** para los diálogos y las palabras clave; van en coordenadas de pantalla (no se
  mueven con la cámara). El narrador va en una tira de papel abajo, frase por frase.
- **Efectos de papel**: humo de bolitas, destellos de cuatro puntas, estrellas y planetas que se pegan uno
  por uno con resorte. Todo con azar con semilla (el mismo t da el mismo cuadro).
- Nada de fundidos: todo entra y sale moviéndose.

## 5. Revisar y exportar

Capturas (`navegador.py capturas <carpeta> t1,t2,...`) → `herramientas/hoja.py <prefijo> t1,t2` para una hoja
de contacto; mirar que ningún cartel tape una cara y que la cámara no deje ver el borde del fondo. Exportar con
`navegador.py exportar <carpeta>` → `render/<tecnica>_<video>.mp4` (skill `exportar-video`).

## Verificar

- Todos los recortes limpios sobre fondo oscuro (sin halo verde ni motas).
- Ningún cartel tapa una cara; el borde del fondo nunca se ve; el diálogo está en un solo lugar.
- MP4 ≈ `TIEMPOS.total` y `saltos.py` sin defectos (el stop motion da cambios parejos, no saltos).

## Lo que falló

- La textura de papel dibujada normal tapó el fondo entero: va en `multiply` con alfa baja.
- Las estrellas quedaron debajo del cielo rasgado y casi no se veían: se pegan después del cielo.
- El cartel final dependía de `SIG()` de la última frase, que es el final del video: nunca salía. Usar
  `A(id) + D(id)`.
- Los personajes salieron mirando al lado contrario del pedido: espejarlos en el código.
- La exportación se cortó en el primer cuadro: el desenfoque de movimiento pide instantes apenas negativos y
  `paso(t) % 3` dio un índice negativo. Todo lo que dependa de `paso(t)` tiene que aceptar t < 0.

## Nivel de estudio

- **Canción real** (Mixkit) con sidechain bajo las voces (`herramientas/mezclar.py`) en vez de la música de
  `sonido.py`, y **efectos reales de papel** (pegar, cinta, rasgar) en cada entrada de sticker.
- **El diálogo va en un solo lugar**: si una frase sale a la vez en el cartel y en la tira del narrador, sobra
  una. La tira es sólo del narrador.
- **Al subir la cámara al cielo, los personajes no quedan cortados** por el borde de abajo.
- 60 fps con 4 subcuadros (`VIDEOS_PARAMS="fps=60&sub=4"`); el stop motion de 8 poses por segundo se mantiene (es el estilo).

## Herramientas externas (opcional)

- **Generador de imágenes** (paso 1). Fotos o dibujos de otras personas: preguntar antes de mandarlos a un
  servicio externo.
- **Voces de niños**: Kokoro con `tono` (skill `narrar-guion`) o un modelo de voz que permita diseñar voces
  por atributos; revisar su licencia (muchos son sólo para uso no comercial).
- **No conviene**: generadores 3D (el collage es papel 2D).
