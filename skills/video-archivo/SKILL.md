---
name: video-archivo
description: 'Técnica 17. Documental con archivo real + motion graphics: material de dominio público (Wikimedia Commons, Internet Archive, NASA, Library of Congress) en blanco y negro con grano, rayas y parpadeo de película; encima una interfaz de datos (año que rueda, código de tiempo, marcas de seguimiento, gráfico con cifras reales, medidor); titulares con glitch cromático y una palabra de acento; cortes en cada compás. Las películas se dibujan cuadro a cuadro exacto (clips todo intra + seeked). Usar para temas históricos, documentales cortos y videos de «hype» con material real.'
---

# Archivo real + motion graphics (técnica 17)

Antes: leer **`director-de-video`** y, para la música, `video-lanzamiento` (pulsos). Ejemplo publicado:
`17-archivo/revolucion-industrial/` (45 s, 100 BPM, 9 escenas de archivo, sin narración) y su MP4 en
`ejemplos/17-archivo_revolucion-industrial.mp4`. **Leer su `index.html` antes de empezar.**
Referencias de estilo: videos de «hype» con archivo real publicados en X (p. ej. los de @dirtman y el método de
video de @twoclipping).

## Qué hace falta

- El entorno `.venv` (README), ffmpeg y Chrome (para exportar, `exportar-video`).
- Conexión a internet para bajar el archivo (una vez). Nada de GPU.

## Reproducir el ejemplo

```
.venv/Scripts/python 17-archivo/revolucion-industrial/bajar.py       # archivo de Wikimedia + CSV de Our World in Data → recursos/
.venv/Scripts/python 17-archivo/revolucion-industrial/preparar.py    # clips todo intra + datos.js
.venv/Scripts/python herramientas/musica.py 17-archivo/revolucion-industrial   # musica.wav + pulsos.js
python herramientas/navegador.py capturas 17-archivo/revolucion-industrial 3,12,24,40
python herramientas/navegador.py exportar 17-archivo/revolucion-industrial
```
`bajar.py` deja las películas y grabados en `recursos/archivo/revolucion-industrial/` (fuera de git; unos
cientos de MB) y un `creditos.json` con autor, fecha, licencia y página de cada archivo.

## 1. Buscar el material (verdadero y con licencia)

- **Wikimedia Commons** por API (sin bajar nada): `action=query&generator=search&gsrnamespace=6&gsrsearch=...
  &prop=imageinfo&iiprop=size|mime|extmetadata` da tamaño, formato, licencia, autor y fecha. Agregar
  `filetype:video` o `filetype:bitmap` a la búsqueda; buscar también por el título exacto de obras conocidas.
- Preferir **dominio público**; CC BY sirve con crédito. Descartar fotos modernas de museo (se ven de hoy).
- **Mirar tamaño y licencia antes de bajar**, y bajar a `recursos/` (fuera de git: puede ser un enlace a
  otro disco si el material pesa).
- `bajar.py` (en la carpeta del ejemplo) baja por título y guarda `creditos.json`: de ahí salen los
  créditos del final y los rótulos con año. Para otro tema, cambiar su diccionario `ARCHIVOS`.
- Las cifras, de una fuente citable (Our World in Data trae CSV por país). **Revisar la serie**: la de
  población del Reino Unido empalma fuentes y pega un salto falso de 12 a 17 millones hacia 1810; se usa
  sólo el tramo continuo (1820–1900) y se dice «con Irlanda».

## 2. Preparar

- Mirar cada película en una hoja de cuadros (`ffmpeg -i peli.webm -vf "fps=1/2,scale=320:-1,tile=6x4" hoja.png`)
  y elegir los tramos. Sin `drawtext` en ese filtro: en algunas instalaciones de ffmpeg en Windows se cae
  porque fontconfig no encuentra fuentes.
- `preparar.py`: recorta los tramos y los recodifica **todo intra** (`-g 1 -crf 18`, 1440 px) → cada cuadro es
  clave y el salto es exacto. Los datos van a `datos.js` (en git, chico).
- `musica.json` → `herramientas/musica.py` (una escena = 2 compases; `impacto` con `silencio_antes` en los
  golpes, `obturador` en las fotos, `escaner` en el gráfico, `riser` antes del clímax).

## 3. Animar (canvas 2D)

- **Video dentro del código**: `fetch` del clip → blob → `<video>` (el servidor de Python no deja saltar
  dentro de un archivo). `Reproductor.iniciar({..., antes})`: `antes(t)` pone `currentTime` en el centro del
  cuadro de 24 fps que toca y **espera `seeked`** antes de dibujar. Al mirar en vivo, se corrige sólo si se
  desfasa más de 0,12 s.
- **Película vieja**: `ctx.filter = grayscale sepia(.18) contrast(1.18) brightness(parpadeo)`, vaivén de
  ±1,5 px por cuadro, rayas verticales y polvo al azar por cuadro, grano en `overlay` que cambia a 24 fps,
  viñeta fuerte. Todo con azar con semilla por cuadro de película.
- **Cámara lenta** sobre las fotos: recorte `[cx, cy, ancho]` de → a (16:9, sin salirse de la imagen). No
  acercar de más: un grabado de 3.000 px a un 30 % de ancho se ve borroso.
- **Interfaz**: esquinas, «● ARCHIVO 03/9», código de tiempo, regla del borde que corre, línea de escaneo
  cada dos compases, **año que rueda** como cuentakilómetros (cada cifra centrada en su casilla), marcas de
  seguimiento en coordenadas de la fuente (siguen a la cámara), gráfico que se dibuja con la cifra que
  cuenta, medidor decorativo **sin números inventados**.
- **Titulares**: tipografía condensada (en el ejemplo, Bahnschrift Condensed, que trae Windows; en otro sistema,
  cualquier condensada instalada), suben desde una máscara, glitch cromático los primeros 0,3 s y algún tirón
  suelto en la palabra de acento; el rótulo de año y lugar se escribe letra por letra.
- **Cortes**: cada escena entra en el compás con 5 cuadros de glitch (canales corridos + franjas desplazadas).
- **Arco**: orden cronológico, clímax con las películas, quiebre sin batería (el costo), y **el final repite
  el principio** (aquí vuelve el fuego de 1801 y, sólo ahí, vuelve el color).

## 4. Revisar y exportar

Capturas (`navegador.py capturas`) → `hoja.py`; mirar que el rótulo no pise el titular y que los créditos se
lean. Exportar con `herramientas/navegador.py exportar <carpeta>` (Chrome sin ventana). **No exportar desde el
panel de un navegador con la pestaña oculta**: `toBlob` tarda más de 1 s por cuadro.

## Verificar

- Cada archivo usado está en `creditos.json` y en los créditos del final, con su licencia.
- Toda cifra en pantalla sale de `datos.js` (fuente citada en pantalla).
- `saltos.py` sobre el MP4 (los cortes en compás, a propósito, van en `--cortes`).

## Lo que falló

- La serie de población con salto falso (ver arriba).
- El año se veía «180 1»: cifras alineadas a la derecha en casillas del ancho del 0 → centrarlas.
- El rótulo de lugar pisaba el titular de dos líneas: ubicarlo sobre la primera línea.
- El grabado de trenes de 1830 muy ampliado se veía borroso: recorte más ancho.

## Nivel de estudio

- **Canción real** con `cancion.py` (el clímax de la canción en las películas) en vez de `musica.py`, y efectos
  reales (proyector, obturador) en su pico.
- **Textos chiquitos de esquina** («ARCHIVO 02/9», código de tiempo): son la firma de video hecho por IA que
  critica la gente (`video-lanzamiento`, «Reglas»). Probar sin contador ni código de tiempo, con el año grande y
  el rótulo.
- **Peso**: el grano cambia en cada cuadro y el MP4 sale pesado (el original, 159 MB). Recomprimir con
  `ffmpeg -i entrada.mp4 -c:v libx264 -crf 27 -tune grain -pix_fmt yuv420p -c:a aac salida.mp4`
  (así quedó el de `ejemplos/`).
- **60 fps sólo si la interfaz lo necesita**: la película va a 24; probar un tramo antes.

## Herramientas externas (opcional)

- **Wikimedia Commons** (API; dominio público o CC BY con crédito) y **Our World in Data** (CSV; citar la
  fuente): son las que usa el ejemplo.
- **Mixkit** o **Sonniss** para proyector y obturador (bajar a `recursos/`; cada uno con su licencia).
- **Pexels / Pixabay** para video de stock (licencia comercial sin atribución): piden una clave de API gratuita,
  propia.
- **No conviene**: imágenes generadas. En un documental, una foto inventada es mentir.
