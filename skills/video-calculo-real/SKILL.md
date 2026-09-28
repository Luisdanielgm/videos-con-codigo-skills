---
name: video-calculo-real
description: 'Hace un video explicativo narrado donde todo lo que se muestra está calculado de verdad (un modelo real entrenado con datos reales) y la narración se escribe sola con las cifras obtenidas (técnica 3 del proyecto). Usar para explicar un algoritmo o fenómeno con rigor, sin números inventados.'
---

# Video con cálculo real (técnica 3)

Resultado: `03-calculo-real/<video>/` con `entrenar.py` (o el script que calcule), `guion_plantilla.json`,
`guion.json`, `datos.js`, `narracion.wav`, `tiempos.js` e `index.html`, y el MP4 en
`render/03-calculo-real_<video>.mp4`. Ejemplo de referencia: `03-calculo-real/red-neuronal/`
(una red 64 → 12 → 12 → 10 entrenada con dígitos reales de UCI optdigits, que vienen en `datos/`) y su MP4 en
`ejemplos/03-calculo-real_red-neuronal.mp4`. **Leerlo antes de empezar.**

## Qué hace falta

- El entorno `.venv` (README: numpy y las voces), ffmpeg y Chrome.
- Datos reales y chicos. El ejemplo usa **optdigits** (UCI Machine Learning Repository, CC BY 4.0; Alpaydin y
  Kaynak, 1998) en `datos/optdigits.tra` y `datos/optdigits.tes`.

## Reproducir el ejemplo

```
.venv/Scripts/python 03-calculo-real/red-neuronal/entrenar.py      # datos.js + guion.json (determinista)
.venv/Scripts/python herramientas/narrar.py 03-calculo-real/red-neuronal
python herramientas/navegador.py capturas 03-calculo-real/red-neuronal 10,60,120
python herramientas/navegador.py exportar 03-calculo-real/red-neuronal
```
Para la música bajo la voz del ejemplo (opcional): `mezcla.json` apunta a una canción de Mixkit en
`recursos/musica/` (ver README) y se mezcla con `herramientas/mezclar.py 03-calculo-real/red-neuronal`.

## La idea

La animación no inventa ningún número. Un script (Python con numpy, en `.venv`) calcula todo con
**semilla fija** y lo deja en `datos.js`; la página vuelve a hacer en el navegador las cuentas que
muestra (por ejemplo, la pasada hacia adelante de la red con los pesos reales). La narración sale de
una **plantilla con huecos** que el mismo script completa con las cifras reales en palabras.

## Pasos

1. **Datos reales y pequeños** en `datos/` (fuera de git si pesan mucho). Que encajen con lo que se va
   a dibujar (optdigits es de 8×8: calza con una cuadrícula de 64 entradas). Anotar su fuente y licencia.
2. **Script de cálculo** (`entrenar.py`): entrena o simula con semilla fija y escribe
   - `datos.js` → `window.DATOS = {…}` (pesos, curvas, ejemplos elegidos, cifras);
   - `guion.json` → a partir de `guion_plantilla.json`, reemplazando `{marcadores}` por las cifras en
     palabras (función `palabras(n)` del ejemplo: 0 a 999.999 en español).
3. **Narración**: skill `narrar-guion` (sobre el `guion.json` generado).
4. **Animación** (`index.html`): mismo contrato que `video-html-canvas`, más `datos.js` antes del
   reproductor. Toda cifra en pantalla sale de `DATOS` o de una cuenta hecha en la página.
5. **Revisión visual y de coherencia** (abajo) y **MP4**: skill `exportar-video`.

## Coherencia: lo que la técnica obliga a revisar

Con datos reales aparecen contradicciones que un video inventado esconde. En el ejemplo aparecieron
tres, y cada una se corrigió **cambiando el cálculo o el texto, nunca maquillando el número**:

1. **Lo que la voz afirma tiene que ser cierto en los datos.** "Ajustar un poquito" no cuadraba con un
   paso tres veces más grande que el del entrenamiento (el 7 saltaba de 3 % a 99 %): se usó el paso real.
2. **La forma que se describe tiene que existir.** "El fondo del valle": el error medido sobre un solo
   ejemplo no tiene valle (siempre baja); medido sobre un lote de 256 sí lo tiene.
3. **Las muestras tienen que ser representativas.** Los primeros 24 ejemplos daban 83 % de aciertos
   cuando el modelo tiene 94 %: se tomaron 24 al azar.
4. Elegir el ejemplo protagonista con un criterio escrito en el script (en el ejemplo: un 7 que al
   principio falla y al final acierta con 85–98 % de seguridad; un "100 %" suena irreal).
5. Si un gráfico amplía el eje para que se vea la forma, decirlo en la etiqueta ("eje ampliado: de … a …").
6. Unidades y medidas distintas llevan etiqueta distinta (el error de un ejemplo no es el error de un lote).

## Verificar

- Correr el script dos veces da el mismo `datos.js` (determinismo): `git diff --stat` sin cambios, o
  comparar el hash del archivo.
- Cada número narrado aparece igual en pantalla (revisar las capturas de las frases con cifras).
- La lista de defectos visuales de `exportar-video` y la duración del MP4 ≈ `TIEMPOS.total`.

## Nivel de estudio

- **La cifra real es la protagonista**: el contador (aciertos, error) rueda con `t` redondeado al cuadro y suena
  un efecto real en cada época del entrenamiento.
- **Una sola toma**: las escenas nacen del mismo objeto (la cuadrícula del 7 se vuelve la entrada de la red, la
  red se vuelve la curva del error), sin fundidos.
- Narrador con Supertonic, canción bajo la voz y 60 fps, como en `video-html-canvas`.

## Herramientas externas (opcional)

- **Mixkit** (música y efectos, licencia gratuita de Mixkit; bajar a `recursos/`) y **Supertonic** (narrador,
  en el procesador; skill `narrar-guion`).
- **Manim** (motor de la técnica 4, `video-pizarra`): puede servir para dibujar el mismo cálculo con otra
  estética; no se mezcla en esta técnica.
- **No conviene**: nada generado (imágenes o modelos 3D). En esta técnica todo lo que se ve sale del cálculo.
