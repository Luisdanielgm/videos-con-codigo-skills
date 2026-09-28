---
name: acabado-riso
description: 'Convierte cualquier video ya exportado en una impresión risográfica (cuatro tintas en trama de grano, planchas corridas, papel con grano), como acabado de estilo (técnica 7 del proyecto). Usar cuando un video simple necesita verse "de autor" sin rehacer la animación.'
---

# Acabado risográfico (técnica 7)

Es un filtro de posproducción: toma un MP4 terminado y devuelve otro MP4 con aspecto de impresión
risográfica. No toca la animación ni el audio (el audio se copia tal cual).

## Qué hace falta

- Python 3.12 con el entorno del proyecto (`.venv`, ver el README): usa **numpy** y, para las capturas,
  **pillow**.
- **ffmpeg** y **ffprobe** en el PATH.
- Nada más: corre en el procesador, sin GPU ni navegador.

## Pasos

1. **Probar primero con capturas** (segundos, no minutos). Crea la carpeta de capturas si no existe
   (el script no la crea):
   ```
   mkdir -p render/capturas
   .venv/Scripts/python herramientas/estilo.py render/<video>.mp4 render/07-riso_<video>.mp4 --capturas 3,35,72
   ```
   Deja `render/capturas/07-riso_<video>_<t>.jpg` (el punto del tiempo pasa a guion: `3.5` → `3-5`).
   En Linux o macOS el Python del entorno es `.venv/bin/python`.
2. **Revisar las capturas** con la lista de «Lo que hay que cuidar» (abajo). Si la noche sale gris o todo
   se ve barroso, el video de base no es bueno para riso: mejor no aplicarlo.
3. **Todo el video** (≈ 10 min para 1:49 de video en un procesador de escritorio):
   ```
   .venv/Scripts/python herramientas/estilo.py render/<video>.mp4 render/07-riso_<video>.mp4
   ```
   Imprime `cuadro N` cada 300 cuadros y termina con `estilo: listo -> <salida>`.
4. **Revisar el MP4 en movimiento** (no sólo cuadros sueltos) y su peso (`ffprobe` o el explorador).

Opción `--puntos`: trama regular de puntos (más «pop», pero hace moiré; ver abajo). Sin la opción se usa
trama de grano.

## Cómo funciona

Cada cuadro se separa en cuatro tintas (azul, rosa flúor, amarillo y negro), cada una se imprime como
trama de grano (o, con `--puntos`, de puntos con su ángulo: 15°, 75°, 0°, 45°), las planchas quedan corridas
un píxel y tiemblan cada cuatro cuadros, y las tintas se multiplican sobre papel crema con grano y fibras.
Todo es determinista: el mismo cuadro da siempre la misma imagen. Trabaja a 1920×1080: un video de otro
tamaño se escala a eso.

## Lo que hay que cuidar

- **La noche tiene que ser azul, no gris**: el negro sólo entra en lo muy oscuro; si no, todo lo
  oscuro se vuelve barro gris (pasó en la primera prueba).
- Funciona mejor sobre colores planos (Canvas 2D, cuento ilustrado, showreel) que sobre render realista.
- La trama pesa muchísimo en el MP4: con `-crf 22 -tune grain` salió de 858 MB; con `-crf 30` (sin
  `-tune grain`) 119 MB y se ve igual. Es lo que usa ahora `estilo.py`.
- **Moiré**: la trama regular de puntos (cuatro planchas con distinto ángulo) hacía círculos grandes al
  ver el video achicado o comprimido. Por omisión se usa trama de grano (estocástica, fija en el
  tiempo), como imprimen muchas risografías; `--puntos` vuelve a la regular.

## Verificar

- Las capturas no muestran barro gris en lo oscuro ni moiré.
- El MP4 dura lo mismo que el original (`ffprobe -v error -show_entries format=duration -of csv=p=0 <mp4>`)
  y tiene audio.
- En movimiento, la trama no «hierve» (es fija; sólo tiemblan las planchas cada cuatro cuadros).

## Nivel de estudio

- **El riso no arregla una base floja**: aplicarlo sobre un video que ya esté bien y de colores planos (un
  showreel, la forma única, la épica), o sólo en un tramo como puente (`director-de-video`).
- **Nada de riso sobre fotos que tienen que verse fieles** (productos, clientes): es un filtro encima de una foto.
- Recomprimir si pasa de ~50 MB: `ffmpeg -i entrada.mp4 -c:v libx264 -crf 30 -pix_fmt yuv420p -c:a copy salida.mp4`.

## Herramientas externas (opcional)

- No necesita ninguna: es numpy + ffmpeg en el procesador.
- **No conviene**: generar imágenes sólo para pasarlas por riso; mejor partir de un video propio.
