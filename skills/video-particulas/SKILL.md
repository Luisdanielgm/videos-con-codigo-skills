---
name: video-particulas
description: 'Técnica 10. Comercial (20–25 s) con miles de partículas que pasan de forma en forma (esfera, palabras, el logo con sus colores) y tipografía cinética, en Canvas 2D con perspectiva calculada a mano, en grilla de pulsos con música calculada. Usar para marcas con logo fuerte o productos de IA y educación.'
---

# Partículas y tipografía cinética (técnica 10)

Antes: leer la skill base **`video-lanzamiento`**. Ejemplo: `10-particulas/libreta/` (una app de notas inventada:
`index.html` + `musica.json` + `pulsos.js`, música calculada con `musica.py`; **leerlo entero**). Las partículas son
el hilo de toda la toma y los rótulos suben desde su máscara. Con un logo de verdad se suma su PNG, muestreado por
color. La técnica 20 (`20-generativo/semilla/`) usa el mismo `puntosDeTexto`.

## Qué hace falta

- El entorno `.venv`, ffmpeg y Chrome. El **PNG real del logo** de la marca (con permiso de su dueño).

## Idea

Unas 9.000 partículas que forman una esfera, se deshacen en palabras y terminan dibujando el logo con sus
colores; títulos que entran palabra por palabra con resortes.

## Motor

- `movimiento.js` → `puntosDeTexto(texto, fuente, n, semilla)` (dibuja el texto oculto y toma n puntos de las
  letras, determinista) y puntos de una imagen (el logo) muestreados por color: dibujar el PNG en un lienzo oculto,
  leer `getImageData` y quedarse con los píxeles opacos, guardando su color.
- Perspectiva 3D a mano (proyección simple: `x' = x·f/(f+z)`), modo de mezcla `lighter`.
- Cada partícula va de su punto en la forma A a su punto en la forma B con una curva por pulso (`Movimiento.tramo`),
  con un pequeño retraso por índice para que la forma «fluya».

## Pasos

1. Recortar el PNG del logo a su contenido (los PNG traen margen) antes de muestrear.
2. Formas destino en la grilla de pulsos; `musica.json` → `musica.py` (o `pista.py` con canción real);
   capturas por pulso; exportar (`video-lanzamiento`).
3. Revisar el peso del MP4: con muchas partículas crece (se bajó de 54 MB a 16 MB recomprimiendo con `-crf` más alto).

## Lo que falló

- Con 6.000 partículas las letras se ven ralas: **9.000 a 2,4 px con `lighter`** queda bien.
- Un parámetro sin definir (`textoFinal`) rompía la escena final: probar el último pulso siempre.
- Recomprimir si el archivo queda pesado antes de entregar.

## Verificar

- Capturas en cada forma armada (esfera, cada palabra, el logo): las letras se leen y el logo tiene sus colores.
- El último pulso sin errores de consola; `saltos.py` y duración del MP4.

## Nivel de estudio

- **Las partículas son el hilo de la toma**: la frase se deshace y forma la siguiente palabra, el ícono o el
  logo. Los títulos no entran ni salen por opacidad y no hay tarjetas encima.
- **Canción real** con la grilla de `cancion.py`; un whoosh real cuando la forma se deshace y un golpe
  en la caída cuando se arma el logo.
- **60 fps con 4 subcuadros**, revisado en movimiento.
- **Frases verificadas en el repositorio del producto**: palabras como «se adapta a tu ritmo» pueden prometer
  más de lo que el producto hace; confirmarlas antes de publicar.

## Herramientas externas (opcional)

- **Mixkit** (canción y efectos; bajar a `recursos/`).
- **No conviene**: generar el logo con imágenes o 3D (se usa el PNG real de la marca).
