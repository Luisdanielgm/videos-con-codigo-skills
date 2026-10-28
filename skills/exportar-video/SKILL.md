---
name: exportar-video
description: 'Revisa cuadros sueltos de un video HTML del proyecto y lo exporta a MP4 con su narración, todo por terminal con un navegador sin ventana. Usar para la revisión visual (QA) y para entregar el MP4.'
---

# Revisar y exportar un video

Todos los videos en navegador usan `herramientas/reproductor.js`, que dibuja cuadro a cuadro con
`render(t)`. Eso permite pedir cualquier instante exacto, sin reproducir en tiempo real.

## Qué hace falta

- **Python 3** (el entorno `.venv` del README; `hoja.py` necesita pillow).
- **ffmpeg** en el PATH (la exportación le manda los cuadros directo).
- **Chrome, Chromium o Edge** instalado. `navegador.py` busca, en este orden, las rutas de instalación
  normales de Chrome y Edge en Windows y después `google-chrome`, `chromium`, `chromium-browser` y
  `microsoft-edge` en el PATH (Linux y macOS). Si no encuentra ninguno, termina con «No encontré Chrome…».
- El servidor local (`herramientas/servidor.py`, puerto 8790) se levanta solo si no está corriendo. Otro
  puerto: variable `VIDEOS_PUERTO`.

## Sacar capturas para revisar

```
python herramientas/navegador.py capturas <carpeta-del-video> 3.5,21,45,119
```

Deja `render/capturas/<tecnica>_<video>_<t>.jpg` (1920×1080; el punto del tiempo pasa a guion: `3-5`).
Termina con código 1 si la página tuvo errores de consola (los imprime como `error de consola: …`).
El registro completo del navegador queda en `render/navegador-capturas-<puerto>.log`.

Para mirarlas de una vez: `.venv/Scripts/python herramientas/hoja.py <tecnica>_<video> [t1,t2]` junta
hasta 12 capturas por hoja (`render/capturas/hoja_…jpg`), cada una con su tiempo arriba a la izquierda.
Revisar la hoja y ampliar sólo las dudosas. (En Linux o macOS: `.venv/bin/python`.)

**Cómo elegir los instantes**: uno por frase del guion, hacia el 60–80 % de su duración (cuando la
escena ya está armada). Los tiempos están en `tiempos.js` de la carpeta del video (en comerciales, los
pulsos clave de `pulsos.js`). Que los cuadros de prueba
**crucen cada traspaso** (justo antes, en y justo después de cada puente).

**Determinismo, en orden y fuera de orden**: pedir los mismos instantes dos veces y en otro orden
(`…capturas <video> 21,3.5,45` y después `3.5,21,45`) tiene que dar los mismos píxeles. Si no, hay estado entre
cuadros (un azar sin semilla, una simulación que avanza al dibujar): se arregla antes de exportar. Si difieren
apenas (±1–2 niveles en el texto grande o el primer cuadro distinto), es el lienzo 2D acelerado por GPU de Chrome:
crear el lienzo del video con `getContext('2d', {willReadFrequently: true})` y no pegarle con `drawImage` un
lienzo de GPU grande (un efecto WebGL devuelve su cuadro con `readPixels`).
**Pero no siempre** (en un showreel de 13 tomas con `sub=2`): con `willReadFrequently` el primer cuadro de cada
orden dio FALLA en los bordes del texto (peor bloque 2,4–3,6) y sin él, 8 de 8 ok. Medir los dos con `determinismo.py` y quedarse
con el que pase; no darlo por sentado.

**Trampas vivas**: la sección «Lo que falló» de la skill de cada técnica es la tabla «trampa → arreglo» de lo que
costó un render (cuadro 0 vacío, una vista previa en caché que engaña, dos servidores en el mismo puerto: cada
exportación en paralelo usa su `VIDEOS_PUERTO`). Se lee antes de exportar y se le suma la trampa nueva al cerrar.

## Revisión visual: qué buscar en cada captura

Son los defectos que más aparecieron. Revisarlos todos, en todas las capturas:

1. **Texto encima de líneas u otro texto**: etiquetas sobre cables, números sobre barras, dos rótulos
   en el mismo lugar.
2. **Cosas fuera del cuadro o recortadas**: barras o porcentajes que pasan del borde derecho, curvas
   que se aplanan en el techo del gráfico.
3. **Animaciones congeladas a medias**: puntos o pulsos quietos cuando la escena ya terminó (el
   recorrido tiene que llegar hasta el final, no quedarse en 0.8).
4. **Inconsistencias con lo que se dice**: la cifra en pantalla distinta de la narrada, o un
   contador que no se mueve.
5. **Zonas reservadas**: el subtítulo ocupa la franja inferior (y ≥ 960) y el título de sección la
   superior izquierda (y ≤ 110). Nada importante ahí.
6. **Flechas y conectores** que entran dentro de las cajas en vez de tocar el borde.
7. **Objetos apoyados** (una bolita sobre una curva) desplazados según la normal de la curva, no
   sólo hacia arriba.

Corregir y volver a capturar **sólo** los instantes que fallaron, hasta que no quede ninguno.

## Exportar a MP4

```
python herramientas/navegador.py exportar <carpeta-del-video>
VIDEOS_PARAMS="fps=60&sub=4" python herramientas/navegador.py exportar <carpeta-del-video>   # 60 fps con desenfoque de movimiento
```

Tarda varios minutos (unos 5.600 cuadros para 3 minutos a 30 fps): conviene correrlo en segundo plano.
Deja `render/<tecnica>_<video>.mp4` (H.264, con `mezcla.wav` o, si no hay, `narracion.wav`, o si no
`musica.wav`) y `render/<tecnica>_<video>.listo` con el número de cuadros. Los cuadros van directo a ffmpeg,
no se guardan en disco. El límite de espera es 1 hora; una sola exportación a la vez por servidor (para exportar
en paralelo, cada una con su `VIDEOS_PUERTO`), pero se pueden sacar capturas mientras exporta.

`VIDEOS_PARAMS` pasa parámetros a la página: `fps` (cuadros por segundo), `sub` (subcuadros de desenfoque
mezclados por cuadro) y los propios del video (p. ej. `palabra=luz` en la técnica 20).

Alternativa sin terminal: el HTML tiene el botón **Grabar** (graba en tiempo real a `.webm`); después
`ffmpeg -i entrada.webm -c:v libx264 -pix_fmt yuv420p -c:a aac salida.mp4`. Es menos exacto que la
exportación cuadro a cuadro.

**No exportar con Vulkan (`VIDEOS_CHROME_ARGS="--use-angle=vulkan …"`)**: en una tanda de 15 exportes con esa
opción salieron con texturas negras, fondos prerrenderizados faltantes o cuelgues sin aviso (con capturas cortas y con la
gráfica Intel no pasa); con la Intel por omisión, bien. Es lo más probable detrás de los «bloques», manchas y páginas negras que
encontró el crítico ciego. Después de exportar, **`verificar_export.py`** compara el MP4 con capturas del mismo instante:

```
python herramientas/verificar_export.py <carpeta-del-video> [--mp4 ruta] [--instantes 0.3,12] [--params "fps=60&sub=4"]
```

Seis instantes por omisión; «ok»/«FALLA» por instante (diferencia media ≤ 5, píxeles con diferencia > 48/255 ≤ 1 %, peor
bloque de una rejilla 16×9 ≤ 14) y código de salida 1 si hay FALLA; `--probar` lo rompe a propósito. Límite: un defecto sutil en
un cuadro oscuro puede pasar. Pasarlo **antes** del crítico ciego: un MP4 corrupto se juzga como si fuera el diseño.

**Color.** También da FALLA si el MP4 no lleva etiqueta de color (yuv420p, rango tv, matriz bt709 o smpte170m). Sin ella el
navegador y el teléfono leen el HD como BT.709 y el color se corre (medido en Chromium: diferencia media 21 contra la página en
un comercial de mapa de la técnica 11; con la etiqueta, 1,2). Todo `ffmpeg` que codifique un MP4 final agrega `COLOR_709` de
`herramientas/color_mp4.py` antes del archivo de salida (las herramientas del repo ya lo hacen); si se copia sin recodificar el
video de Manim, `ETIQUETA_601`. Los comandos a mano de esta skill (versión para teléfono, música aparte) recodifican o copian un
MP4 ya etiquetado y conservan la etiqueta.

**El cuadro es una función pura de `t`**: `determinismo.py` lo comprueba sacando las mismas capturas en el orden dado y en el
inverso (cada una en una página nueva) y comparando cada instante consigo mismo. Atrapa un contador que sube, hilos o
partículas que se acumulan, `Math.random` sin semilla y `Date.now()`; sin esto, lo que revisaste con capturas y el MP4
exportado en orden o por tramos pueden no ser el mismo video.

```
python herramientas/determinismo.py <carpeta-del-video> [--instantes 2,10,25,40] [--params "fps=60&sub=4"]
python herramientas/determinismo.py --probar     # una página pura da ok; contador, azar y reloj dan FALLA
```

**Una página ajena que anima con el reloj real** (los ejemplos de Anatomy) no es función pura de `t`: `determinismo.py` la
rechazaría. Se graba con `herramientas/grabar_reloj.py <url> <salida.mp4> --selector <caja>`, que congela el reloj del navegador y lo
adelanta cuadro por cuadro (`--probar`: 3 ok); queda a cuadros exactos pero sin audio y lento (13 s ≈ 3 min).
**3D de la técnica 26** (`iso3d.js`): `iso3d.py --probar` (12 casos) + `determinismo.py` + `verificar_export.py` después de exportar.

Pasarlo cuando el video guarda estado entre cuadros (simulaciones, partículas, hilos, física) y antes de exportar por
tramos. Umbrales: media ≤ 0,5, fracción grande ≤ 0,1 %, peor bloque ≤ 2. Límite: un estado que sólo se nota entre
cuadros contiguos no aparece si los instantes están lejos; ahí el arreglo es escribir el cuadro como función pura de `t`.

**Exportes que se cuelgan** (6 veces en dos días de tandas; con varios Chrome a la vez la máquina va ~5 veces más lenta):
`navegador.py` vigila los cuadros que recibe el servidor y corta con `COLGADO` si no llegan cuadros nuevos en
300 s (`VIDEOS_SIN_AVANCE`). Para videos largos o pesados, exportar **por tramos reanudables**:

```
VIDEOS_TRAMO=10 python herramientas/navegador.py exportar <carpeta-del-video>
```

Cada tramo de 10 s es una exportación normal con su propio navegador y vigilante (180 s sin cuadros); si uno se cuelga
se repite sólo ése, y si el comando se corta, volver a correrlo continúa donde quedó. Al final une los tramos y pega el
audio entero (duración = la del audio de la carpeta, o `VIDEOS_DURACION=<s>`; `VIDEOS_SALIDA=<nombre>` cambia el nombre
del MP4). Los tramos hechos quedan en `render/tramos/<video>/`. Si un tramo falla dos veces, el mensaje dice cuál.

### Reglas de render: primero la calidad, después el tiempo

- **Borrador para revisar**: 720p a 30 fps, sólo para ver y chequear. El **final** se renderiza en su calidad (1080p, 60 fps
  si el video lo pide) y nunca sale de un borrador reescalado.
- **Al volver a exportar una pieza ya hecha** (p. ej. tras rehacer su pulso): antes de lanzar, `ffprobe` del MP4 anterior (`r_frame_rate`) y se
  exporta con los mismos parámetros (`VIDEOS_PARAMS="fps=60"`); en una tanda, diez piezas de 60 fps salieron a 30 por exportar «por omisión».
  El MP4 anterior se renombra `<nombre>_antes-<fecha>.mp4`, no se pisa.
- **Por partes sólo donde es seguro**; si es dudoso o engorroso, render **completo**:
  - Manim: seguro con `-n inicio,fin` (probado: la parte sale idéntica píxel a píxel y el tiempo de la escena,
    la deriva de la cámara y los `sfx` quedan bien). Ojo: con `-n` la escena termina antes, así que `efectos.json` y el
    control de textos salen de una pasada completa.
  - Navegador (canvas, three.js, GSAP) e HyperFrames: por tramos sólo si `determinismo.py` da ok.
  - Blender: por rangos de cuadros, si las simulaciones están horneadas.
  - **Nunca por partes**: el acabado ASCII (la histéresis depende del cuadro anterior), simulaciones que integran paso a
    paso y todo lo que falle en `determinismo.py`.
  - El audio (voz, música y efectos) nunca se parte: se pega entero al final. Al unir partes, recomprimir una sola vez
    (no `-c copy` con ajustes distintos) para que no haya un «pulso» de calidad en el empalme.
- **El final se renderiza con la PC vacía**: sin suites de otros proyectos ni otros renders a la vez. Antes de lanzarlo,
  medir la carga (núcleos libres, RAM, qué suites o renders corren) y **preguntarle al usuario** si puede dejar la PC libre.
- Un video complejo (muchas capas, efectos que se acumulan, varias técnicas mezcladas) va en una sola tanda.
- Después de cada render, comparar con ffprobe la duración del MP4 y la de `mezcla.wav` (que no se corte el final).

**Versión liviana para compartir por teléfono** (sin recortar, mismo 1920×1080, a 30 fps; ~45 % del peso):

```
ffmpeg -i render/<video>.mp4 -vf fps=30 -c:v libx264 -preset slow -crf 26 -tune stillimage -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart render/<video>_telefono.mp4
```

No usar HandBrake con su preajuste tal cual: su **recorte automático** toma el fondo oscuro de los explicativos
por franjas negras y corta los bordes (un explicativo quedó en 1590×832 y en el teléfono se veía recortado). Si
se usa HandBrake: Dimensiones → Recorte → Ninguno, y comprobar que el tamaño diga 1920×1080.

## Crítico ciego

Quien construye **nunca** juzga su obra. Después del storyboard, de cada escena y de cada render la juzga un
**subagente nuevo** que no vio la construcción y al que no se le dice qué se arregló. (Método del kit
`echris6/motion-video-kit`.)

**La medida** (sobre el MP4 final, nunca sobre capturas del navegador):

```
.venv/Scripts/python herramientas/critico.py render/<video>.mp4 --salida render/critica/<video>/ronda<N>
      [--quietos <carpeta>/tiempos.json | --quietos 12.0-12.6,30-31] [--textos cajas.json] [--paso 0.2]
.venv/Scripts/python herramientas/critico.py --probar      # cada «ok» tiene su caso que dice «FALLA»
```

Dice ok o FALLA por caso y el total: congelado por cada 30 s y tramo quieto más largo, primer cuadro terminado,
sonoridad y pico, **sobresalto del audio en los cortes** (nivel de los 0,3 s siguientes menos la mediana de los 4 s
anteriores ≤ +8 dB; el +6 del `sync-check` de iart-ai sale corto para showreels con golpes a propósito), contraste en las
cajas de texto que se le den (`[{"x","y","w","h","t"}]` en píxeles del video), y los cortes (info, con `saltos.py`). `--quietos tiempos.json` deja fuera las pausas de voz de ≥ 400 ms. Deja en la
carpeta las hojas (una cada 0,2 s y una densa de 1 s a 18 cuadros/s en cada corte, con `hoja.py`) y `medidas.json`.
Las metas están en `director-de-video` («Barra de calidad»).

**El bucle**:
1. El crítico corre `critico.py`, mira **todas** las hojas y devuelve problemas **P0** (rompe el video), **P1** (se
   nota) y **P2** (detalle), cada uno con su tiempo, y termina en «se entrega» u «otra pasada». Con un P0 o P1
   abierto no se entrega. Después del storyboard (todavía sin MP4) revisa la tabla y los cuadros fijos.
2. Se arregla de lo más grave a lo menos. **Respaldo antes de cada arreglo** (copia del archivo o commit); si los
   números o el crítico siguiente dicen que empeoró, se vuelve atrás.
3. El crítico siguiente es **otro nuevo**: recibe la lista anterior, no lo que se tocó, y marca cada punto
   **arreglado / a medias / igual**, más lo nuevo que encuentre.
4. **Registro de rondas** en `critica.md` de la carpeta del video: una fila por ronda con fecha, números de
   `medidas.json` antes → después, P0/P1 abiertos y veredicto.
5. El **informe final separa** lo medido (los números) de lo que tiene que ver u oír una persona (si se entiende
   sin sonido, la voz, el gusto, el ritmo). Lo segundo lo decide una persona.
6. Se exporta también una **versión sólo música** (para redes con otra voz o subtítulos): la mezcla sin la voz
   (una copia de `mezcla.json` sin `"voz"`, o `musica.wav`) montada sobre el mismo video:
   `ffmpeg -i render/<video>.mp4 -i <musica>.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest render/<video>_solo-musica.mp4`

**Las seis formas de fallar** (de huashu-art-motion, alchaincyf, MIT, `SKILL.md`; con palabras propias). Se repasan al
escribir la tabla de tomas y otra vez en las hojas antes de entregar; el crítico las busca por nombre:

1. **Diapositivas que pasan**: encabezado y número de página fijos, puntos que entran uno por uno con fundido, cada toma
   con el mismo acercamiento lento y parejo, final en una tarjeta centrada con la frase. → Un suceso de imagen por toma;
   cámara a pulsos (quieta → empuje rápido → quieta); terminar en una acción del protagonista; el texto, escrito sobre un
   objeto de la escena.
2. **Copiar el ejemplo**: la composición, los personajes o el material del ejemplo o de la referencia pasan tal cual a la
   pieza. → Se toma el método; composición y objetos se diseñan de nuevo para el tema.
3. **Sin objeto concreto**: la idea abstracta sólo en palabras e íconos. → Cada toma con un objeto y lo que hace (si no se
   puede escribir esa fila de la tabla de tomas, la toma no está lista).
4. **Fondo muerto o cuadro vacío**: un fondo plano o estrellado que no cambia mientras se mueve un pedacito en el centro;
   o tramos sólo de color, negro o vacío, sin el protagonista. → El sujeto ocupa la mitad del cuadro o más, el fondo cambia
   con el contenido y el protagonista está en cada toma.
5. **Material real dibujado con código**: había captura, foto, grabación o el texto original, y se dibujó una imitación. →
   El material real a pantalla llena; el código explica, señala y mueve la cámara.
6. **Cara de IA**: degradado azul-violeta, cielo violeta con estrellas, neón cian y violeta; un estilo distinto en cada
   toma (collage de estilos); muñequitos o robots dibujados por código; monedas o bolitas con cara. → Un estilo y una paleta
   para todo el video; un video parejo que se parece un poco a una presentación es mejor que un collage vistoso.

Ojo con la quietud: en un explicativo a pulsos (quieto → empuje → quieto) estar quieto no es un defecto. `critico.py`
castiga los tramos quietos de más de 0,5 s: en los narrados, pasarle las pausas con `--quietos <carpeta>/tiempos.json`.

**Prompt del crítico** (para pegar en un subagente nuevo; llenar lo que va entre `<>`):

```
Eres el crítico de un video. No viste cómo se hizo y no se te dirá qué se cambió. Tu trabajo es encontrar lo que
está mal, no aprobar. No arregles nada.
Video: render/<video>.mp4 · Para qué es: <público y objetivo en una línea> · Skill de la técnica: <skill>
Ronda: <N> · Lista de la ronda anterior: <pegarla, o «es la primera»>
1. Corre: .venv/Scripts/python herramientas/critico.py render/<video>.mp4 --salida render/critica/<video>/ronda<N> <opciones>
2. Mira TODAS las hojas de esa carpeta (hoja_general_* en orden y cada hoja_corte*). Si dudas de un cuadro, sácalo
   grande: ffmpeg -ss <t> -i render/<video>.mp4 -frames:v 1 dudoso.png
3. Busca, además de cada FALLA: texto que choca, cruza otro texto, queda cortado o no se lee; primer cuadro a medio
   armar; cortes que saltan (cambia tamaño, dirección o sujeto); animaciones congeladas a medias; dos tomas iguales
   seguidas; cifras distintas de lo que se narra; lo que pide la skill de la técnica; cara de plantilla (todo
   centrado, fundidos, degradado de fondo); y cada una de las seis formas de fallar de `exportar-video` (diapositivas
   que pasan, copia del ejemplo, sin objeto concreto, fondo muerto o cuadro vacío, material real dibujado con código,
   cara de IA), nombrando cuál. ¿Se entiende sin sonido?
4. Si hay lista anterior, marca cada punto: arreglado / a medias / igual.
5. Devuelve: los números de critico.py; la lista ordenada P0 / P1 / P2, cada uno con tiempo en segundos, qué se ve y
   qué haría falta; qué le falta para ser BUENO (un video sin errores no es un buen video); y como última línea
   «se entrega» u «otra pasada». Con un P0 o P1 abierto, «otra pasada».
```

## Verificar el MP4

- Duración: `ffprobe -v error -show_entries format=duration -of csv=p=0 render/<video>.mp4` ≈ `TIEMPOS.total`.
- Saltos o cuadros repetidos: `.venv/Scripts/python herramientas/saltos.py render/<video>.mp4 [--cortes t1,t2]`
  (los cortes a propósito van en `--cortes`). `saltos.py --probar` comprueba que el detector encuentra un
  salto y un cuadro repetido puestos a propósito.
- Mirarlo entero con sonido: los fundidos y tirones no se ven en cuadros sueltos.

## Errores conocidos

- **Capturas negras en 3D**: `navegador.py` lanza Chrome sin `--disable-gpu` y con
  `--enable-unsafe-swiftshader` (WebGL por software si no hay GPU). Revisar el registro `render/navegador-*.log`.
- **No exportar desde una pestaña oculta** del navegador de escritorio: con la pestaña en segundo plano,
  `toBlob` tarda más de un segundo por cuadro. El navegador sin ventana no tiene ese problema.
- Si el servidor quedó corriendo con código viejo (p. ej. sin la ruta `/audio` de la técnica 20), da 404:
  cerrarlo y volver a correr.
