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
El registro completo del navegador queda en `render/navegador-capturas.log`.

Para mirarlas de una vez: `.venv/Scripts/python herramientas/hoja.py <tecnica>_<video> [t1,t2]` junta
hasta 12 capturas por hoja (`render/capturas/hoja_…jpg`), cada una con su tiempo arriba a la izquierda.
Revisar la hoja y ampliar sólo las dudosas. (En Linux o macOS: `.venv/bin/python`.)

**Cómo elegir los instantes**: uno por frase del guion, hacia el 60–80 % de su duración (cuando la
escena ya está armada). Los tiempos están en `tiempos.js` de la carpeta del video (en comerciales, los
pulsos clave de `pulsos.js`).

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
no se guardan en disco. El límite de espera es 1 hora; una sola exportación a la vez (el servidor lleva
una), pero se pueden sacar capturas mientras exporta.

`VIDEOS_PARAMS` pasa parámetros a la página: `fps` (cuadros por segundo), `sub` (subcuadros de desenfoque
mezclados por cuadro) y los propios del video (p. ej. `palabra=luz` en la técnica 20).

Alternativa sin terminal: el HTML tiene el botón **Grabar** (graba en tiempo real a `.webm`); después
`ffmpeg -i entrada.webm -c:v libx264 -pix_fmt yuv420p -c:a aac salida.mp4`. Es menos exacto que la
exportación cuadro a cuadro.

## Verificar el MP4

- Duración: `ffprobe -v error -show_entries format=duration -of csv=p=0 render/<video>.mp4` ≈ `TIEMPOS.total`.
- Saltos o cuadros repetidos: `.venv/Scripts/python herramientas/saltos.py render/<video>.mp4 [--cortes t1,t2]`
  (los cortes a propósito van en `--cortes`). `saltos.py --probar` comprueba que el detector encuentra un
  salto y un cuadro repetido puestos a propósito.
- Mirarlo entero con sonido: los fundidos y tirones no se ven en cuadros sueltos.

## Errores conocidos

- **Capturas negras en 3D**: `navegador.py` lanza Chrome sin `--disable-gpu` y con
  `--enable-unsafe-swiftshader` (WebGL por software si no hay GPU). Revisar `render/navegador-capturas.log`.
- **No exportar desde una pestaña oculta** del navegador de escritorio: con la pestaña en segundo plano,
  `toBlob` tarda más de un segundo por cuadro. El navegador sin ventana no tiene ese problema.
- Si el servidor quedó corriendo con código viejo (p. ej. sin la ruta `/audio` de la técnica 20), da 404:
  cerrarlo y volver a correr.
