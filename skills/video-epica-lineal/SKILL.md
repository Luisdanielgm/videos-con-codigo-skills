---
name: video-epica-lineal
description: 'Técnica 18. Épica histórica en dibujo lineal, sin imágenes: cada dibujo son trazos que se dibujan solos (canvas 2D), arco por épocas, el estilo cambia con la época (papel y tinta → luz sobre negro), una sola toma (la cámara recorre un panorama de papel y después sube), titulares con serifa y una palabra de acento, elementos repetidos en perspectiva y un final que repite el principio. Usar para historias de largo aliento (la historia de algo), explicativos épicos y aperturas.'
---

# Épica histórica en dibujo lineal (técnica 18)

Antes: leer **`director-de-video`**. Ejemplo publicado: `18-epica-lineal/historia-del-vuelo/` (60 s, 8 épocas:
Ícaro → Leonardo → Montgolfier → Wright → escuadra → Saturno V → James Webb → constelación de Ícaro) y su MP4
en `ejemplos/18-epica-lineal_historia-del-vuelo.mp4`. **Leer su `index.html` antes.** Referencia de estilo:
«la civilización occidental» en dibujo lineal de @IterIntellectus en X.

## Qué hace falta

- El entorno `.venv`, ffmpeg y Chrome. Sin imágenes ni GPU.
- Para la pista del ejemplo: la canción «Drawing the Sky» (Mixkit, `mixkit-272-drawing-the-sky.mp3`, bajada de
  mixkit.co a `recursos/musica/`) y el banco de efectos (`recursos/efectos/listos`, ver README). Sin ellos, la
  música calculada (`efectos/musica.json` → `musica.py`) sirve de respaldo.
- Tipografías: el ejemplo usa Georgia Pro (titulares) y una monoespaciada (rótulos); si no están instaladas, el
  navegador cae en otra serifa: cambiar las fuentes en el `index.html`.

## Reproducir el ejemplo

```
.venv/Scripts/python 18-epica-lineal/historia-del-vuelo/mezclar.py           # mezcla.json + mezcla.wav + pulsos.js
# sin la canción ni el banco (música calculada, el respaldo):
#   .venv/Scripts/python herramientas/musica.py 18-epica-lineal/historia-del-vuelo/efectos
#   cp 18-epica-lineal/historia-del-vuelo/efectos/pulsos.js 18-epica-lineal/historia-del-vuelo/pulsos.js
#   cp 18-epica-lineal/historia-del-vuelo/efectos/musica.wav 18-epica-lineal/historia-del-vuelo/mezcla.wav
python herramientas/navegador.py capturas 18-epica-lineal/historia-del-vuelo 2,10,20,30,40,50,58
VIDEOS_PARAMS="fps=60&sub=4" python herramientas/navegador.py exportar 18-epica-lineal/historia-del-vuelo
```

## Motor de trazos (en el `index.html` del ejemplo)

- `Dibujo`: lista de trazos (polilíneas). Constructores: `L_` (recta), `ARC` (arco/elipse), `BEZ` (cúbica),
  `QB` (cuadrática), `POLI` (polígono). Cada punto lleva un **temblor de pluma fijo** (a mano, sin «hervir»).
- `trazar(D, k, {color, brillo, grosor})` dibuja hasta la fracción `k` del largo total y devuelve la punta:
  ahí va una gota de tinta (papel) o un punto de luz (noche).
- Objetos en perspectiva: una función `proyectar([x, y, z])` (giro + inclinación + perspectiva) y se trazan
  las aristas proyectadas (así se hizo el Flyer). Los repetidos (la escuadra) se escalan por 1/z y suben
  hacia el horizonte.

## Dirección

1. **Arco por épocas**, una por escena (12 pulsos = 3 compases), en orden. Fechas verdaderas en el rótulo.
2. **El estilo cambia con la época**: papel envejecido (fibras, manchas, viñeta, grano en `multiply`) con
   tinta para el pasado; una **mancha de tinta inunda el cuadro** y el futuro es luz sobre negro (líneas con
   `shadowBlur`, estrellas con parallax, oro para el acento).
3. **Una sola toma**: los dibujos del papel están uno al lado del otro y la cámara pasa de uno al siguiente;
   en la noche la cámara sube con el cohete, al telescopio y a las estrellas.
4. **Titulares**: serifa grande, palabra por palabra desde una máscara, **una palabra de acento** (bermellón
   en el papel, oro en la noche), rótulo en mono que se escribe letra por letra.
5. **El final repite el principio**: la constelación dibuja a Ícaro con la misma escala y lugar que en el
   papel; la noche se abre en un círculo de papel y el último cuadro es el primero, completo.
6. Dibujos entre y = 40 y 840 px: la franja de abajo es del titular.
7. **Sonido**: pluma sobre papel mientras se traza, hoja que pasa cuando la cámara va al dibujo siguiente, golpe
   cuando la tinta inunda (lista de efectos en el `mezclar.py` del ejemplo, en pulsos).

## Verificar

- Tira a 4 cuadros por segundo (`ffmpeg -i <mp4> -vf fps=4,scale=320:-1,tile=8x8 tira.png`): ningún tramo de
  papel casi vacío de más de ~1 s.
- Capturas: ningún dibujo pisa el titular; el último cuadro es igual al primero.
- `saltos.py` sobre el MP4.

## Lo que falló

- La portada y el primer titular salían a la vez: el primer titular espera a que la portada se vaya.
- Trazos de 1–2 px se veían débiles en 1920: `grosor` 1,4–1,5 en el papel.
- El biplano visto casi de frente parecía una viga: girarlo (yaw −1,0) y darle cuerda real a las alas.
- La constelación dibujaba también la greca: los adornos van en un dibujo aparte.
- Lo más cercano de la escuadra pisaba el titular: subir la formación.
- En la primera versión había ~1,5 s de papel casi vacío entre el Flyer y la escuadra y un titular que se fundía:
  el dibujo siguiente empieza a trazarse antes de que llegue la cámara, y los titulares salen por la máscara.

## Nivel de estudio

- **Nada de tiempo muerto** (se verifica con la tira de arriba).
- **Los titulares salen por la máscara, no con fundido.**
- **Efectos reales** en su pico (pluma, hoja, golpe), como en el ejemplo.
- 60 fps con 4 subcuadros.

## Herramientas externas (opcional)

- **Mixkit** (canción y efectos; bajar a `recursos/`, cada uno con su licencia).
- **No conviene**: ninguna imagen generada. La técnica es sin imágenes.
