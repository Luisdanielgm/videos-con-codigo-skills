# Videos de ejemplo

Estos MP4 salieron de las skills de este repositorio, sólo con código (un agente + ffmpeg). **No están bajo la
licencia MIT del repositorio**: se pueden ver, pero no se pueden reutilizar como si fueran libres, porque llevan
material de terceros con su propia licencia.

| Video | Técnica (skill) | Dura | Pesa | Material de terceros adentro |
|---|---|---|---|---|
| `01-html-canvas_red-neuronal.mp4` | 1 · Canvas 2D (`video-html-canvas`) | 4:02 | 26 MB | Canción «Vastness» (Mixkit) |
| `02-threejs_red-neuronal.mp4` | 2 · three.js (`video-threejs`) | 4:02 | 41 MB (recomprimido) | Canción «Vastness» (Mixkit) |
| `03-calculo-real_red-neuronal.mp4` | 3 · cálculo real (`video-calculo-real`) | 3:54 | 28 MB | «Vastness» (Mixkit); dígitos de UCI optdigits (CC BY 4.0) |
| `04-explicativo-narrado_red-neuronal.mp4` | 4 · pizarra con cairo (`video-pizarra`) | 4:02 | 22 MB | Canción «Vastness» (Mixkit) |
| `17-archivo_revolucion-industrial.mp4` | 17 · archivo + motion graphics (`video-archivo`) | 0:48 | 53 MB (recomprimido) | Películas y grabados de dominio público (Wikimedia Commons); datos de Our World in Data (CC BY 4.0) |
| `18-epica-lineal_historia-del-vuelo.mp4` | 18 · épica lineal (`video-epica-lineal`) | 0:59 | 21 MB | Canción «Drawing the Sky» (Mixkit); efectos de Mixkit y de Kenney (CC0) |
| `19-ensayo_las-cosas-pequenas.mp4` | 19 · ensayo (`video-ensayo`) | 0:41 | 22 MB | Canción «Vastness» y efectos (Mixkit); imágenes generadas con IA |

Las voces de los videos narrados son de Supertonic-3 (voz M5), generadas en local. La música del 17 es
calculada (`herramientas/musica.py`).

## Licencias de lo que llevan

- **Mixkit** (canciones y efectos): licencia gratuita de Mixkit (mixkit.co/license). Permite usarlos dentro de
  un proyecto propio, pero **no redistribuirlos sueltos**: por eso este repositorio no trae los archivos de audio,
  sólo los videos que los usan. Para rehacer los videos, cada quien los baja de mixkit.co.
- **Kenney** (efectos): CC0 (dominio público), kenney.nl.
- **Wikimedia Commons**: películas de los hermanos Lumière (1895 y 1897), grabados y pinturas de P. J. de
  Loutherbourg (1801), T. Allom y J. Tingle (1835), W. Wyld (1852), J. McNeven (1851), un grabado anónimo de hacia
  1830 y fotos de Lewis Hine (1909 y 1910): todos de dominio público.
- **Our World in Data**: población del Reino Unido (Gapminder, HYDE y ONU), CC BY 4.0.
- **UCI optdigits** (Alpaydin y Kaynak, 1998): CC BY 4.0.

Las cifras de tamaño son las de estos archivos; los videos 02 y 17 se recomprimieron con libx264 (crf 27; el 17
con `-tune grain`) para que cada uno quede por debajo del límite de 100 MB de GitHub.
