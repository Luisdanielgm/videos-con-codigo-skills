---
name: video-app-real
description: 'Técnica 15. Graba la app REAL del teléfono Android con adb screenrecord (scroll, taps, búsquedas) y la monta dentro de un teléfono dibujado, con textos al lado (en HyperFrames o en pantalla.js). Usar para mostrar la app verdadera funcionando.'
---

# App real grabada del teléfono (técnica 15)

Antes: leer **`video-lanzamiento`** (base de los comerciales) y **`video-hyperframes`** (montaje). No hay
ejemplo publicado de esta técnica: las grabaciones del proyecto original muestran cuentas reales.

## Qué hace falta

- Un teléfono **Android** con las opciones de desarrollador y la **depuración por USB** activadas, conectado
  por cable (o por depuración inalámbrica).
- **adb** (Android SDK Platform-Tools, gratis en developer.android.com). En Windows suele quedar en
  `$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe`; si no, en la carpeta donde lo descomprimas.
- `adb devices` tiene que listar el teléfono como `device` (la primera vez, aceptar la huella en el teléfono).
- ffmpeg para revisar las grabaciones y HyperFrames o `herramientas/pantalla.js` para el montaje.
- iPhone: esta técnica no lo cubre (grabar la pantalla desde el propio iPhone y seguir desde «Montar»).

## Permisos y cuidado (es un teléfono personal)

- Preguntar a su dueño antes de desinstalar, borrar datos o hacer algo que le llegue a otra persona o cueste dinero.
- No tocar botones que abran la cámara, manden mensajes o respondan (p. ej. respuestas rápidas automáticas).
- No abrir chats con mensajes sin leer (manda la confirmación de lectura).
- Si una captura muestra otra app o una notificación de otra app: borrarla sin usarla.
- **Grabar con una cuenta de demostración.** Si sólo hay datos reales, lo grabado es un borrador que no se
  publica ni se sube a git.
- Al terminar: dejar la app como estaba y borrar los temporales del teléfono.

## Grabar

```
ADB="$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"; export MSYS_NO_PATHCONV=1
"$ADB" shell monkey -p <paquete> -c android.intent.category.LAUNCHER 1     # abrir la app
"$ADB" exec-out screencap -p > captura.png                                  # ver dónde está
"$ADB" shell screenrecord --time-limit 14 /sdcard/v.mp4 &                   # en paralelo:
"$ADB" shell input swipe 360 1300 360 600 1400                              # scroll / tap / text
"$ADB" pull /sdcard/v.mp4 15-app-real/<producto>/crudo/v.mp4 && "$ADB" shell rm /sdcard/v.mp4
```
- El nombre del paquete sale de `"$ADB" shell pm list packages | grep <parte-del-nombre>`.
- En Git Bash de Windows, `MSYS_NO_PATHCONV=1` evita que se reescriban las rutas del teléfono (`/sdcard/…`);
  con eso, las rutas locales absolutas van estilo `C:/…` (con `/c/…` adb no las encuentra).
- Deslizar hacia arriba (1300 → 600) baja por la lista; al revés se queda arriba.
- Otras acciones: `input tap X Y`, `input text "hola"`, `input keyevent KEYCODE_BACK`.
- Si una pantalla tarda en cargar (el historial de un chat), esperar antes de grabar.

## Montar

- Recortar la barra de estado (notificaciones) y la del sistema: video más grande que la pantalla con
  `top` negativo (720×1612 → `left:-12.5px; top:-40.1px; width:385px; height:862px` en una pantalla de 360×779).
- Tira de cuadros para ver dónde termina de cargar: `ffmpeg -i v.mp4 -vf fps=4,scale=180:-1,tile=12x1 tira.png`;
  arrancar el clip ahí (`data-media-start` en HyperFrames), o entra con el «Cargando…».
- Los crudos no entran a git (`15-app-real/*/crudo/`); si tienen datos reales, tampoco las copias en `assets/`.

## Verificar

- Ninguna notificación, nombre ni dato de otra persona en ningún cuadro (hoja de cuadros de cada clip).
- El clip arranca ya cargado y el teléfono dibujado no deja ver bordes negros ni la barra de estado.
- El MP4 final con `saltos.py` y mirado entero con sonido.

## Nivel de estudio

- **El teléfono no se queda quieto al lado de un título**: zoom a la zona que se toca, en el tiempo de cada
  `input tap` o `swipe` (se saben: los manda el guion de adb).
- **Un indicador de toque y un efecto real de toque** en ese mismo tiempo; canción real con `cancion.py`.
- Antes de pedir 60 fps, mirar con `ffprobe` la tasa real de la grabación de `screenrecord` (no está medida).

## Herramientas externas (opcional)

- **adb** (arriba).
- **Mixkit** (toques y canción, licencia gratuita de Mixkit; se bajan a `recursos/`, fuera de git).
- **No conviene**: simular la app con un generador de imágenes o con pantallas dibujadas. Si no hay cuenta de
  demostración, no se graba.
