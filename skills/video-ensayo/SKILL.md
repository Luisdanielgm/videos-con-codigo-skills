---
name: video-ensayo
description: 'Técnica 19. Ensayo cinematográfico: tomas fotorrealistas generadas (una por frase), cámara lenta, formato de cine 2,39:1, gradación cálida, grano y vaivén de película, efectos que la foto no tiene (polvo en un rayo de sol, vapor, lluvia, destello, una lámpara que respira), narración con una voz fija y casi nada de texto. Usar para reflexiones, manifiestos, aperturas emotivas y videos de marca «con alma».'
---

# Ensayo cinematográfico (técnica 19)

Antes: leer **`director-de-video`**. Ejemplo publicado: `19-ensayo/las-cosas-pequenas/` (41 s, 6 tomas, voz
Supertonic M5 + «Vastness» de Mixkit) y su MP4 en `ejemplos/19-ensayo_las-cosas-pequenas.mp4`. Las 6 imágenes
del ejemplo vienen en `imagenes/`. Referencia de estilo: los «benchmarks personales» en video de @danshipper en X.

## Qué hace falta

- Un **generador de imágenes fotorrealistas** (paso 2).
- **Supertonic** para la voz (entorno `externos/voz-env`, skill `narrar-guion`). El `narrar.py` del ejemplo usa
  además `torch` y `torchaudio` (versión CPU) para remuestrear:
  `externos/voz-env/Scripts/python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`.
- Una canción libre (el ejemplo usa «Vastness», Mixkit, `mixkit-759-vastness.mp3`, bajada de mixkit.co a
  `recursos/musica/`), ffmpeg y Chrome.

## Reproducir el ejemplo

```
externos/voz-env/Scripts/python 19-ensayo/las-cosas-pequenas/narrar.py     # narracion.wav + tiempos.js
.venv/Scripts/python herramientas/mezclar.py 19-ensayo/las-cosas-pequenas  # mezcla.wav (lee mezcla.json)
python herramientas/navegador.py capturas 19-ensayo/las-cosas-pequenas 4,12,20,30,38
VIDEOS_PARAMS="fps=60&sub=4" python herramientas/navegador.py exportar 19-ensayo/las-cosas-pequenas
```
(El ejemplo trae también su `mezclar.py` propio, anterior a la mezcla compartida; `herramientas/mezclar.py` con
su `mezcla.json` hace lo mismo.)

## Pasos

1. **Guion corto**: 5–7 frases, una idea por frase, con silencios entre ellas (la imagen respira). La última
   vuelve al principio.
2. **Imágenes**: una por frase, todas con el mismo pedido de estilo («fotografía cinematográfica
   fotorrealista, 16:9, hora dorada, poca profundidad de campo, grano de 35 mm, sin texto, sin caras
   reconocibles»). Para el callback, pedir **«el MISMO lugar de la imagen 1, pero de noche»**. Si tienes una
   suscripción de ChatGPT, puedes conectar Codex (`codex exec`, como en `video-collage`) para que las haga
   (~1–2 min por imagen); o usa cualquier generador de imágenes, en la nube o local, que puedas llamar desde la
   terminal (el agente busca cómo conectarlo). Revisar la licencia de uso de lo generado.
3. **Narración**: con Supertonic M5 (en el procesador) → `narracion.wav` + `tiempos.js`, con una
   entrada de 2–3 s y un silencio propio después de cada frase (el `narrar.py` del ejemplo tiene las frases y
   sus silencios en `FRASES`; `herramientas/narrar.py` con `pausa` por frase sirve igual).
4. **Música**: canción libre que **baja sola cuando habla** el narrador: `sidechaincompress` con la voz como
   llave (`herramientas/mezclar.py`, con `"voz": "narracion.wav"` en `mezcla.json`) → `mezcla.wav` (fuera de git).
5. **Animar** (`index.html`): cada toma empieza 0,9 s antes de su frase; encuadre lento de → a; fundido con
   una fuga de luz cálida que cruza; gradación `soft-light` cálida, viñeta, grano a 24 fps, vaivén de ±0,8 px;
   franjas de 2,39:1 con la frase en cursiva dentro de la franja de abajo; título al final.
6. **Ubicar los efectos** mirando cada imagen en una hoja con cuadrícula (dónde está el rayo, la taza, el
   sol, la lámpara) y poner esas fracciones en `TOMAS`.

## Verificar

- Capturas de cada toma: la frase dentro de la franja, los efectos sobre su objeto (la lluvia sólo en el
  vidrio, el vapor sobre la taza).
- La música baja cuando habla la voz (escuchar el MP4 entero); duración ≈ `TIEMPOS.total`; `saltos.py`.

## Lo que falló

- `ffmpeg -ss .37` no lo acepta: escribir `0.37`.
- La lluvia encima de toda la toma también mojaba la taza: sólo sobre el vidrio.
- Las imágenes generadas ya traen parte del efecto (vapor, gotas): el del código va suave, encima.

## Nivel de estudio

- **Ambiente real por toma**, bajo y debajo de la voz: pájaro en la del gorrión, lluvia en el vidrio, pluma
  sobre el papel. En el ejemplo la mezcla es voz + canción + pocos efectos.
- **Entre tomas, algo que une** (la luz de la lámpara se vuelve el sol de la siguiente, un color que llena el
  cuadro) en vez de la fuga de luz genérica, que sigue siendo un fundido.
- **60 fps con 4 subcuadros**: la cámara lenta es donde más se nota.
- **Si va vertical**: la frase entre ~250 y ~1500 px, no en la franja de 2,39:1.

## Herramientas externas (opcional)

- **Generador de imágenes** (paso 2).
- **Mixkit** o **Sonniss** para el ambiente (cada uno con su licencia; bajar a `recursos/`).
- **Pexels / Pixabay** para tomas con movimiento real (licencia comercial sin atribución; piden una clave de API
  gratuita, propia).
- **No conviene**: generadores 3D (son tomas fotográficas, no 3D).
