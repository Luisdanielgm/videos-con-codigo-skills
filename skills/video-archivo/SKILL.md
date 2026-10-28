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
- `bajar.py` (en la carpeta del ejemplo) baja por título y guarda `creditos.json` (autor, fecha, licencia, página):
  de ahí salen los créditos del final y los rótulos con año. Para otro tema, cambiar su diccionario `ARCHIVOS`.
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

## Variante «mesa con evidencia» (gramática Vox)

La otra forma de usar el archivo: en vez de película vieja con interfaz de datos, **un argumento armado sobre una mesa** con
las pruebas reales (recortes, fotos, documentos, mapas, citas) y una cámara que las recorre como la mirada de un periodista.
La credibilidad sale de que esas cosas están de verdad ahí. Rige todo lo de arriba sobre buscar y acreditar el material:
**una prueba inventada no es una variante de estilo, es mentir**.

- **Cuándo sí**: «cómo pasó esto», «quién dijo qué y cuándo», una cifra o una cita que el público tiene que ver de dónde
  sale. **Cuándo no**: un mecanismo sin material que pegar (eso es la variante Kurzgesagt de `video-html-canvas`), los pasos
  de un razonamiento (pizarra) o mucha actuación de personajes.
- **La mesa**: papel o corcho que la cámara recorre; el material real **lleva el cuadro**: cuando algo se lee, ocupa ≥ 60 %
  del ancho (dos tomas seguidas con la prueba más chica que eso ya es un portarretratos, no una mesa). Tres colores: casi
  negro, blanco papel y un rojo en dos tonos (el claro para líneas, el oscuro para rellenos), más un amarillo resaltador
  apagado sólo para subrayar. Ni blanco ni negro puros. Fotos en gris con trama de puntos a 45°, borde blanco y dos tiras de
  cinta; sombra apenas visible; la textura del papel **quieta** (no tiembla por cuadro). Un poco imperfecto a propósito: lo
  perfecto se lee como aviso publicitario.
- **Dos ritmos (lo que la define)**: la cámara se mueve suave a los fps del video; los trazos (líneas que se dibujan, letras
  que se escriben, círculos a mano, resaltador, un mapa que se llena) avanzan **a 12 por segundo, de a dos cuadros**:
  `const tq = Math.floor(t * 12) / 12` y el avance se calcula con `tq`. Todo suave parece video institucional; todo a 12
  marea.
- **Cámara**: nunca lineal. Recorridos de 0,7–2 s (mediana ≈ 1,3): ida y vuelta suave (`expoInOut`) para ir a buscar la
  prueba siguiente; arranque rápido con cola larga para seguir un hilo o abrir el plano. Mientras algo se dibuja dentro de
  una prueba, la cámara está quieta. Una foto quieta no se mira con una deriva lenta: en la palabra clave de la voz, un
  acercamiento rápido corto (≈ 0,3 s, 18–32 % más cerca) y quieta otra vez.
- **Entradas**: la prueba ya está en el corte (sin rebote ni caída). Sólo al seguir una línea de tiempo la siguiente
  entra deslizando, inclinada 5–15°, y se endereza al llegar (≈ 0,8 s).
- **Trazos**: subrayado rojo en 0,5–1 s; círculo a mano de un trazo en ≈ 1 s, sin cerrar y con las puntas cruzadas;
  resaltador de 1,5–3 s por renglón, al paso de la voz; escritura a ≈ 13 letras por segundo; **hilo rojo** entre pruebas,
  un poco caído, con un punto en cada punta.
- **Transiciones**: casi todas cortes secos en la puntuación de la voz; seguir el hilo rojo hasta la prueba siguiente
  (1,3–1,8 s); acercarse a una foto hasta llenar el cuadro y cortar a la misma foto en un escaneo mejor; abrir de una foto a
  toda la mesa (≈ 1 s). El papel que se rasga **no** es de esta gramática (es de plantilla).
- **Ritmo**: lento, ≈ 3,3 s por toma (≈ 12 cortes por minuto; la prueba se sostiene con sus trazos) o rápido, 1,4–1,8 s
  (25–33 cortes por minuto, imágenes casi quietas). Cada palabra clave de la voz tiene su acción en la imagen.
- **Seis cuidados** (lo que más se rompe): (1) el texto que se lee va **arriba de todo y se dibuja último**: una foto o una
  cinta que lo tapa es el error que más vuelve; (2) el encuadre se calcula desde el rectángulo de lo que se lee ahora más un
  margen, no con coordenadas a mano, y el rótulo de una prueba vecina a medio entrar queda fuera; (3) cada vez que se suma
  una prueba, leer en orden todo lo que hay en pantalla: dos rótulos juntos pueden armar una frase falsa; (4) un hecho se
  anima una sola vez (si pasó en el plano general, al acercarse no se repite); (5) variar el revelado: «desliza → rótulo →
  círculo rojo» no más de 3 veces seguidas (también: ya estar en el corte, acercarse, resaltar, unir con hilo, sellar);
  (6) el ritmo de los trazos va con las palabras de la voz, no con los pulsos de la música.

Gramática de huashu-art-motion (alchaincyf, MIT), `references/动画语法/y2_vox.md`, contada con palabras propias; sus cifras
salen de medir cinco videos de Vox y Johnny Harris cuadro a cuadro. Desmontar una referencia propia antes de imitarla:
`herramientas/desmontar.py`.

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
