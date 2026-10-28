---
name: narrar-guion
description: 'Convierte el guion de un video en narración con una voz local (Supertonic, Kokoro o Piper) y genera los tiempos de cada frase para sincronizar la animación. Usar al crear o cambiar la narración de cualquier video del proyecto.'
---

# Narrar un guion

Produce `narracion.wav` y `tiempos.js` en la carpeta del video. La animación **no se escribe con
tiempos fijos**: se ubica relativa a `tiempos.js`, así que cambiar una frase no rompe el video.

## Entrada: `guion.json` en la carpeta del video

```json
{
  "voz": "supertonic:M5",
  "velocidad": 1.0,
  "pausa": 0.7,
  "segmentos": [
    {"id": "titulo", "texto": "¿Cómo aprende una red neuronal? Vamos a verlo paso a paso."},
    {"id": "idea",   "texto": "Una red neuronal es un programa que aprende con ejemplos.", "pausa": 1.0}
  ]
}
```

- `id`: corto, sin espacios. La animación lo usa para ubicar cada escena.
- `texto`: lo que se dice. **Los números van escritos en palabras** ("setenta y uno por ciento",
  "cero coma noventa"), porque la voz lee mal las cifras. Las siglas en inglés, como se pronuncian.
- `pausa` (opcional por frase): silencio después de esa frase. Por omisión, el `pausa` global.
- Frases de 1 a 3 oraciones. Una idea por frase: cada una suele ser una escena o un paso.

Historias con varias voces: `"personajes": {"narrador": {"voz": "supertonic:M5"}, "nina": {"voz": "ef_dora", "tono": 3},
"abuelo": {"voz": "em_santa", "tono": -2}}` y en cada segmento `"quien": "nina"`. `tono` sube o baja la voz en
semitonos (filtro `rubberband` de ffmpeg): así una voz adulta suena más joven. `quien` pasa a `tiempos.js`
(sirve para colorear el subtítulo y mover la boca de quien habla).

## Voces (todas locales, en el procesador)

| Voz en `guion.json` | Modelo | Cómo suena |
|---|---|---|
| `supertonic:M5` (otros estilos: `M1`–`M4`, `F3`…) | Supertonic-3 | **La recomendada** para el narrador: la más natural |
| `em_alex` (hombre), `ef_dora` (mujer), `em_santa` (hombre) | Kokoro v1.0 int8 | Buena, algo menos natural |
| `es_MX-ald-medium`, `es_MX-claude-high` | Piper | Español más claro, menos natural |

`narrar.py` decide por el nombre: `supertonic:<estilo>` → Supertonic; si existe `modelos/<nombre>.onnx` →
Piper; si no → Kokoro. Para escucharlas todas con la misma frase: `.venv/Scripts/python herramientas/muestras_voz.py`
(Kokoro y Piper; deja `render/muestras/*.wav`).

## Instalar (una sola vez)

1. **Entorno principal** (Kokoro y Piper), con Python 3.12:
   ```
   py -3.12 -m venv .venv                     # en Linux/macOS: python3.12 -m venv .venv
   .venv/Scripts/python -m pip install -r requirements.txt
   ```
2. **Modelos de Kokoro** en `modelos/` (fuera de git): `kokoro-v1.0.int8.onnx` (~88 MB) y `voices-v1.0.bin`,
   de los *releases* del repositorio `thewh1teagle/kokoro-onnx` en GitHub (etiqueta `model-files-v1.0`).
3. **Voces de Piper** en `modelos/` (~60 MB cada una): del repositorio `rhasspy/piper-voices` en Hugging Face,
   carpeta `es/es_MX/ald/medium/` (`es_MX-ald-medium.onnx` y `.onnx.json`) y `es/es_MX/claude/high/`.
   Van los dos archivos de cada voz, con el mismo nombre.
4. **Supertonic-3** en un entorno aparte (`externos/voz-env`, fuera de git), porque trae sus propias
   dependencias:
   ```
   py -3.12 -m venv externos/voz-env
   externos/voz-env/Scripts/python -m pip install supertonic soundfile numpy
   ```
   El paquete `supertonic` (código MIT) baja el modelo `Supertone/supertonic-3` de Hugging Face la primera vez
   (~0,4 GB, a su caché). El modelo tiene licencia OpenRAIL-M: leerla antes de un uso comercial.
   `narrar.py` llama a ese Python por su cuenta; si está en otro lugar (o en Linux/macOS, donde es
   `externos/voz-env/bin/python`), indicarlo con la variable `VIDEOS_VOZ_PYTHON`.
5. **ffmpeg** en el PATH. Para `tono` hace falta un ffmpeg con `rubberband` (las compilaciones «full» lo traen:
   `ffmpeg -filters | grep rubberband`).

## Estructura y tiempos de un explicador (de `explainer-video-skills` e `iart-ai`, MIT)

- **Una idea central** que quien mira pueda repetir en una frase; lo que no la sirve se corta, no se achica. El guion
  se escribe y se mide **antes** del storyboard: es más barato cortar una frase que una escena armada. Lo visual ilustra la
  frase que se dice, nunca se adelanta.
- **Arco** (y su parte del tiempo): problema ≈ 20 % (el dolor, con sus palabras) → solución ≈ 15 % (en una línea) →
  cómo funciona ≈ 45 % (1 a 3 pasos concretos) → resultado y una sola acción ≈ 20 %. Antes del «cómo», hacer sentir el costo
  del problema. Ritmo: rápido y algo tenso en problema y costo, una pausa de alivio en la solución, **lo más lento en el
  cómo** (cada paso se sostiene para leerse), cierre abierto y sostenido.
- **Una analogía por video**, del mundo de quien mira (una fila, un termostato), usada igual en lo visual y en las
  palabras; si necesita su propia explicación, es la equivocada. Cambiar de analogía a mitad reinicia la comprensión.
- **Medidas de voz**: ≈ 2,3 palabras por segundo (≈ 140 por minuto; líneas técnicas ≈ 2,0); un video de 60 s son ≈ 138
  palabras. Duración de una escena = palabras / 2,3 + ≈ 0,4 s de aire; una escena sin voz necesita ≥ 1,0 s para
  registrarse. (Con `narrar.py` la duración real sale del audio: esto sirve para escribir el guion a la medida.)
- **Subtítulos** (la mayoría mira sin sonido): ≤ 2 líneas, ≤ 42 caracteres por línea, ≥ 1,0 s en pantalla y fuera antes
  de que empiece la frase siguiente; salen del mismo arreglo de tiempos que los cortes, así no se desfasan.
- **Un solo sistema de estilo**: una escala tipográfica, un color por significado (nunca reasignado) y una curva de
  movimiento fijados antes de la escena 2; las mismas entradas y salidas en todas.
- **Presentación o pitch en video**: cada lámina dura lo que dura su audio más un margen chico (nunca a ojo); el título
  es la afirmación («la fuga de clientes es nuestro impuesto al crecimiento»), no la etiqueta («Fuga»); gancho en los
  primeros ~5 s (una pregunta o una cifra, no una agenda ni un logo); arco problema → idea que nadie ve → solución →
  prueba → una petición; el problema debe aterrizar antes de mostrar la solución.

## Comando

```
.venv/Scripts/python herramientas/narrar.py <carpeta-del-video>
```

(En Linux o macOS: `.venv/bin/python`.) Imprime el inicio y la duración de cada frase y el total.
Cada frase queda en caché (`render/voz_cache/`) por texto, voz, velocidad y tono: al cambiar una sola, sólo se
regenera esa. Las frases nuevas de Supertonic se generan todas juntas (el modelo se carga una vez).

## Salida

- `narracion.wav`: 24 kHz mono, con 0.6 s de silencio al inicio y 1.5 s al final.
- `tiempos.js`: define `window.TIEMPOS = { total, orden: [ids], seg: { id: { inicio, dur, texto, quien? } } }`.

## Verificar

- El comando termina en `total …s -> narracion.wav, tiempos.js`.
- Escuchar al menos la primera frase, una con números y una de cada personaje.
- Si una cifra suena rara, escribirla de otra forma en palabras y volver a correr (sólo se regenera esa frase).

## Errores conocidos

- «No such file» con Supertonic: falta el entorno `externos/voz-env` o `VIDEOS_VOZ_PYTHON` apunta mal.
- Kokoro no encuentra `voices-v1.0.bin`: los dos archivos del modelo tienen que estar en `modelos/`.
- La primera corrida de Supertonic tarda más: está bajando el modelo.
