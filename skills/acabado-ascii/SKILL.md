---
name: acabado-ascii
description: Convierte cualquier video ya exportado en ASCII que sigue la forma (cada celda elige, de 95 caracteres, el que mejor calza con su forma; en los bordes, glifos de dirección | / - \), en fósforo verde, ámbar, tinta sobre papel o con el color de la imagen, con histéresis para que los glifos no tiemblen y un modo «revelado» que pasa de la imagen real al ASCII. Posproducción, como el riso. Usar para aperturas, puentes entre tramos, estética de terminal o «hacker», y para darle otra lectura a un video de trazos o formas claras.
---

# Acabado ASCII

```
.venv/Scripts/python herramientas/ascii.py render/<video>.mp4 render/ascii_<video>.mp4 --capturas 3,12 --paleta fosforo   # probar
.venv/Scripts/python herramientas/ascii.py render/<video>.mp4 render/ascii_<video>.mp4 --tramo 36,10 --revelado 0.5,3   # 10 s
.venv/Scripts/python herramientas/ascii.py render/<video>.mp4 render/ascii_<video>.mp4 --paleta papel                    # todo
```

Prueba de referencia (los renders no vienen en el repositorio; se rehacen con los comandos de arriba): 10 s de la épica
lineal (`18-epica-lineal/historia-del-vuelo/`) desde el segundo 36, fósforo, revelado de 0,5 a 3 s, más la misma sin
histéresis para comparar, y capturas en las cuatro paletas.

## Cómo funciona

1. **Atlas**: los 95 caracteres imprimibles en Consolas (fuente del sistema, `C:/Windows/Fonts/consola.ttf`; si no está, Cascadia
   Mono, Courier, Menlo o DejaVu Sans Mono). Celda de N × 2N px (como una terminal). Cada glifo se mide en una grilla de
   **3 × 6**: cuánta tinta cae en cada parte. Es la idea de «ASCII que conoce la forma» (Codrops) y de
   `niccolofanton/morphing-ascii-shader` (MIT), hecha en numpy.
2. **Forma**: cada celda del cuadro se mide igual (con un realce de contraste adentro de la celda) y elige el glifo más
   parecido (distancia en las 18 partes, una multiplicación de matrices por cuadro). El glifo más denso equivale a un
   gris de 0,6, no al blanco, para que los trazos finos encuentren su `|`. Las celdas **planas** (sin forma
   adentro) sólo eligen en la rampa ` .:-=+*#%@`: si no, un cielo liso se llena de `jjjj`.
3. **Bordes**: Sobel sobre la misma grilla de forma (barato) vota la dirección de cada celda y le resta costo a `| / - \`.
4. **Histéresis**: la celda se queda con su glifo salvo que el nuevo sea mejor por más de `--histeresis` (0,015 por omisión).
5. **Color**: monocromo = una capa de brillo + tabla fondo → tinta (rápido); `color` = el color medio de la celda, aclarado.
   Fósforo y ámbar llevan un resplandor suave. El audio se copia; sale a 1080p (o 1080×1920 si es vertical) con el mismo fps.

## Opciones

| Opción | Qué hace |
|---|---|
| `--celda 10` | ancho de la celda en px (alto = doble). 8 = más detalle y más lento; 14–16 = más «terminal» |
| `--paleta` | `fosforo` (omisión) · `ambar` · `papel` (tinta donde la imagen es oscura) · `color` |
| `--invertir` | los glifos densos van en lo oscuro (trazos oscuros sobre fondo claro en fósforo, ámbar o color) |
| `--revelado 2,5` | de 2 s a 5 s cada celda pasa de la imagen real al ASCII, de izquierda a derecha con algo de azar |
| `--piso 0.1` | lo que queda bajo ese gris sale vacío: limpia cielos y viñetas (en la épica sobre papel, `0.3`) |
| `--bordes 0.3` | peso de los glifos de dirección; `0` los apaga |
| `--histeresis 0.015` · `--sin-histeresis` | margen para cambiar de glifo; sin él, para comparar |
| `--tramo 36,10` | sólo 10 s desde el 36 (los demás tiempos cuentan desde el tramo) |
| `--capturas 3,12` | no hace video: guarda esos cuadros en `render/capturas/<salida>_<t>.jpg` |

Al terminar imprime los segundos por cuadro y los **cambios de glifo por cuadro** (la medida de estabilidad).

## Tiempos y estabilidad medidos (sólo CPU, celda 10 = 10 368 celdas)

- **0,18 s/cuadro de cálculo, 0,23 s/cuadro en total** (con lectura y codificación) en fósforo: 10 s a 60 fps ≈ 2,3 min.
  Con la CPU al 100 % por una exportación en paralelo subió a ~0,7 s/cuadro. `color` cuesta ~1,5× (compone en RGB).
- **Cambios de glifo por cuadro**, mismo tramo, con y sin histéresis (0,015):
  épica lineal (trazos limpios que se dibujan solos: casi todo cambio es animación real) **92 → 79**;
  ensayo (foto generada con grano, tramo 20–30 s) **298 → 144** (−52 %). Calibrado con 0 · 0,002 · 0,004 · 0,008 ·
  0,015 · 0,03: con 0,004 casi no cambia nada; 0,03 ya deja glifos viejos en lo que se mueve.
- El MP4 pesa poco: 10 s de fósforo = 1,5 MB.

## Lo que hay que cuidar

- **Elegir bien el video**: rinde con trazos, siluetas, títulos grandes y fondos planos (épica lineal, pizarra, showreel,
  forma única). Sobre render realista o fotos con mucha textura sale ruido de letras.
- **Fondo claro + fósforo = pantalla llena de `@`**: con fondos claros usa `--paleta papel`, o `--invertir`.
- **Títulos chicos se pierden**: un texto de menos de ~3 celdas de alto no se lee en ASCII. Si el título importa, ponlo
  encima después (`herramientas/componer.py`) o usa el revelado para que se vea antes en la imagen real.
- **No apagar la histéresis**: sin ella los glifos hierven con el grano y el ruido del MP4 aunque la imagen esté quieta
  (el doble de cambios en el ensayo). Si sube mucho (≥ 0,03) las formas que se mueven dejan «estela» de glifos viejos.
- **Trazos finos que desaparecen** (pasó en la primera prueba: el enrejado de la torre del cohete se perdía): si el glifo
  más denso equivale al blanco, un trazo de 2 px queda más cerca del espacio que de `|`. Por eso equivale a un gris de 0,6
  (`DENSO`); con 0,35 aparecen letras sueltas (`r`, `Z`, `c`) en los trazos.
- **Cielos y viñetas llenos de `-` o `jjjj`**: un degradado suave no es forma. Las celdas planas sólo usan la rampa de
  densidad y `--piso` deja vacío lo más tenue; en fondos de papel con viñeta, `--piso 0.3`.
- **Revisar en movimiento** antes de entregar (se exporta con `-crf 24`), y mirar el contador de cambios que imprime.
- **Lento sin motivo**: indexar una tabla de color con `tabla[i]` costaba 250 ms por cuadro; `np.take(..., axis=0)` y
  Sobel sobre la grilla de forma (no sobre los 2 millones de píxeles) lo bajaron de ~2 s a 0,18 s.
- Glifos mal orientados en los bordes = el signo del gradiente: el eje y de la imagen va hacia abajo (gradiente
  abajo-derecha → borde `/`).

## Herramientas externas (opcional)

- No necesita ninguna: numpy + pillow + ffmpeg en el procesador. La fuente es del sistema; no se descarga nada.
- **No conviene**: un shader en el navegador para esto (la GPU suele estar ocupada exportando y el resultado es el mismo).
