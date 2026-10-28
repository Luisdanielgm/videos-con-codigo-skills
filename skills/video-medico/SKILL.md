---
name: video-medico
description: Hace un video educativo médico con precisión (cirugía, anatomía, la cirugía de una fractura) combinando three.js (anatomía real en 3D, implante, cirugía paso a paso, radioscopia simulada) y Manim (clasificación, decisiones, cortes didácticos, recuperación). Todo dato sale de una fuente citada, el guion lo aprueba un médico antes de narrar, lo aproximado se rotula y la geometría del implante se verifica con números. Usar para cualquier video donde un error clínico sea grave; ejemplo hecho (no publicado), una placa bloqueada en el húmero proximal.
---

# Video médico con precisión (three.js + Manim)

Ejemplo completo (no publicado): «Fractura extraarticular del húmero proximal: la placa bloqueada» (5:42, 1080p60). Cada
video lleva un `brief.md` que se escribe antes de empezar: el pedido, las decisiones, la fuente de cada frase, lo que el video
no dice y la guía para el revisor. Base: la skill `director-de-video` (combina técnicas) y, para los motores, `video-threejs`
y la sección «Motor Manim» de `video-pizarra`.

**No es un video para publicar sin que lo revise un médico**: un especialista lo revisa antes de cualquier uso fuera de la
máquina. Publicar lo decide una persona, nunca el agente.

## Las seis reglas (por qué este video no se parece a los otros)

1. **Ningún dato clínico sin fuente.** Cada frase del guion lleva su fuente (tabla en `brief.md`: frase → afirmación →
   fuente). Si un número no está en una fuente, se escribe «sin fuente» y no se narra. Si las fuentes se contradicen (la AO
   dice 5–8 mm bajo el troquíter, la guía de Synthes 2010 dice 5–7, la de 2005 «al menos 8»), se elige una, se dice en el
   `brief.md` cuál y por qué, y se le pasa al revisor.
2. **El guion lo aprueba una persona antes de narrar.** Narrar y renderizar es lo caro; corregir una frase antes es gratis.
   Orden: investigación → guion con fuentes → OK → voz → imagen.
3. **Lo aproximado se rotula.** Lo que no viene de una medición o de una fuente (los tendones, el nervio, el esquema del
   paciente, la forma de la placa) lleva «esquema» o «modelo aproximado» en pantalla y en los créditos. Radioscopia: «simulación».
4. **Lo anatómico sale de un hueso real**, no de formas inventadas (ver «El hueso»). Las medidas en pantalla salen del
   modelo (`referencias.py`, `placa.py`), no se escriben a ojo.
5. **El implante se verifica con números**, no sólo mirándolo (ver «Verificar»). Un subagente de sólo lectura que no lo
   hizo lo revisa con rayos y distancias: en el ejemplo encontró 6 errores que a ojo no se veían.
6. **Lo que el video no dice también se documenta**: cifras de complicaciones de series mixtas, «la placa es mejor que el
   clavo», códigos que la fuente no usa. Va en el `brief.md` («Lo que el video no dice»).

## El flujo (con tiempos reales del ejemplo)

| # | Paso | Cómo | Tardó |
|---|---|---|---|
| 1 | **Investigación con fuentes** | Subagente de sólo lectura con el prompt de abajo («Prompt de investigación»); fuente primaria: AO Surgery Reference (surgeryreference.aofoundation.org); secundarias: guías técnicas del fabricante, PubMed/PMC, Radiopaedia, Orthobullets. Sin descargas ni cuentas | ~12 min |
| 2 | **Guion + tabla de fuentes** | `narrar.py` (frases `(id, texto, pausa)`) y `brief.md`. ~2,6 palabras por segundo con M5; 760 palabras ≈ 5:30. Cifras en palabras, siglas como se dicen | ~15 min |
| 3 | **OK del médico al guion** | Se le pasa `brief.md`. Lo aprobado queda anotado con fecha y hora | el médico |
| 4 | **Voz** | `externos/voz-env/Scripts/python <carpeta>/narrar.py` (Supertonic M5; acelera con `atempo` si pasa de `OBJETIVO`) | ~4 min |
| 5 | **El hueso real** | `malla.py` → `remallar.py` → `fracturar.py` → `referencias.py` (ver «El hueso») | ~40 min |
| 6 | **El implante** | `placa.py` (Blender sin ventana) con las medidas de la fuente | ~1 h |
| 7 | **La escena 3D** | `tres/index.html` (three.js, determinista: todo sale de `t`); revisar con cuadros sueltos (`?t=`) y hojas de contacto | ~2 h |
| 8 | **Los diagramas** | Un subagente escribe `escena.py` (Manim) con el criterio de `video-pizarra`; control de textos encimados hasta 0 FALLA | ~50 min (en paralelo con el 7) |
| 9 | **Verificación del implante** | Segundo subagente de sólo lectura (ver «Verificar») | ~20 min (en paralelo) |
| 10 | **Mezcla** | `mezcla_3d.py` (efectos del 3D en su momento) + `herramientas/mezclar.py` (canción baja, voz, efectos de Manim) | 1 min |
| 11 | **Render del 3D por partes** | Chrome en la NVIDIA, 3–4 partes a la vez (ver «Exportar») | ~10 min por tanda |
| 12 | **Juntar** | `juntar.py <salida.mp4>`: Manim encima del 3D en sus tramos, una sola pista de audio | ~8 min |
| 13 | **Revisión final** | Cuadros de cada corte entre técnicas, `herramientas/saltos.py`, y a que lo mire el médico | ~10 min |

## El hueso (anatomía real)

- **BodyParts3D 4.0** (DBCLS, malla de una tomografía): `partof_BP3D_4.0_obj_99.zip` (62 MB) de
  `dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/`, guardado en `recursos/modelos3d/bodyparts3d`
  (fuera de git). Cada pieza es un `FJxxxx.obj` en mm; la tabla `partof_element_parts.txt`
  da el `FJ` de cada nombre FMA (húmero derecho FMA23130 → FJ3368, escápula FJ3384, clavícula FJ3362, arterias circunflejas
  FJ2264/FJ2291/FJ2292, vena cefálica FJ2272).
- **Licencia**: el sitio dice CC BY 4.0 (texto de crédito: «BodyParts3D, © The Database Center for Life Science licensed
  under CC Attribution 4.0 International»); la cabecera de cada OBJ y el README de versiones anteriores dicen CC BY-SA 2.1
  Japón. **Si el video se llegara a compartir, comprobarlo antes** (SA obliga a compartir igual lo derivado).
- **Qué no trae**: músculos, tendones ni nervios (hay que dibujarlos como esquema y rotularlos así). Trae huesos, algunas
  arterias y venas.
- **Mallas reducidas**: la de 99 % viene con caras grandes y una grieta donde la cabeza se une al resto. `remallar.py`
  (Blender, voxel de 0,6 mm + cierre morfológico de 2,2 mm + suavizado que respeta el volumen + decimado) la deja cerrada y
  parejas; imprime la distancia al original (mediana 0,05 mm, máx 1,15 mm: la forma no cambia).
- **Ejes**: BodyParts3D usa x izquierda, y atrás, z arriba; `malla.py` los pasa a los de three.js (X = x, Y = z, Z = −y),
  1 unidad = 10 mm, origen en el centro de la cabeza (esfera ajustada por mínimos cuadrados, radio 21,4 mm).
- **Fractura**: `fracturar.py` parte el hueso real con un cortador de relieve (ruido) por el cuello quirúrgico, a 30 mm del
  centro de la cabeza, con una Boolean exacta; por vértice guarda `prof` (mm bajo la superficie) y el shader pinta cortical
  y esponjoso (celdas de Worley) en la cara de la fractura.
- **Puntos de referencia**: `referencias.py` mide el tope del troquíter, el tope de la cabeza y el calcar. **La corredera
  bicipital no salió de los cortes**: se fijó a 45° desde lateral mirando la malla con luz rasante (el surco entre los dos
  tubérculos); la arteria sube unos 7–10 mm por fuera. Para otro hueso, esto se vuelve a hacer a ojo con marcadores
  (`tres/vista.html?pts=x,y,z;...`).
- Alternativas si BodyParts3D no tiene la pieza: NIH 3D Print Exchange (entradas CC0, p. ej. 3DPX-000386, un húmero proximal
  fracturado; la calidad es dudosa), Z-Anatomy. No Hunyuan: la anatomía generada no es fiel.

## El implante

- `placa.py`: contorno, agujeros y espesor en un plano; se curva sobre el hueso con rayos (campo de alturas dilatado y
  suavizado: una placa precontorneada no copia cada bulto) y se ubica con las medidas de la fuente (aquí: borde 7 mm bajo el
  tope del troquíter, 3 mm detrás de la corredera). Los agujeros de cabeza se perforan **a lo largo de su tornillo** (como en
  una placa bloqueada real: ángulo fijo por agujero) con una Boolean exacta. Los tornillos se calculan con rayos: la punta queda a 6 mm
  de la superficie articular (AO 5–8 mm) y nunca a menos de 5 mm de la superficie en ninguna dirección.
- **Instrumental o implante como máquina** (cómo se mueve una guía, cómo traba un tornillo): la figura aparte, en el estilo de
  `video-maquina-isometrica` (2D o 3D oscuro con brillo; el `.glb` del implante se limpia con `iso3d.py glb`). **El hueso real sigue
  siendo de BodyParts3D** y no se restiliza ni se rehace con esa técnica; las cifras del implante siguen la regla de «Verificar».
- **Lo que el fabricante no publica** (ancho, grosor, radios, reparto por fila) se inventa razonable, se rotula «modelo
  aproximado» y no se muestran medidas de esa pieza.
- El orden de los tornillos en pantalla es el de la fuente primaria; si las guías difieren, se dice cuál se siguió.

## Verificar (lo que se repite en cada video médico)

1. **Guion**: cada frase contra su fuente (tabla en `brief.md`). Lo no verificado, a «Sin verificar» y fuera de la voz.
2. **Cantidades**: lo que dice la voz contra lo que se ve (la voz dice «nueve agujeros»; en pantalla, el rótulo dice
   «9 agujeros», no «9 tornillos»).
3. **Geometría del implante** (subagente): por tornillo, distancia al centro de su agujero, ángulo con el eje del agujero,
   holgura de la rosca y la cabeza dentro del agujero (negativa = entra en el metal), fracción dentro del hueso, punta →
   superficie, distancia mínima entre ejes de tornillos (≥ 3,5 mm), abanico (puntas más separadas que cabezas). Y los cuadros
   del video ya renderizado: cuántos tornillos se ven, si cada uno sale de su agujero.
4. **Cuadros fijos** por frase (`tres/index.html?t=…`, con `.venv/Scripts/python` + Playwright) y hoja de contacto cada ~3 s:
   rótulos encimados, cabeceras duplicadas, piezas cortadas por el borde, textos que pisan el recuadro de rayos X.
5. **Cortes entre técnicas** (3D ↔ Manim): un cuadro antes y uno después de cada uno; que el hueso sea el mismo.
6. `herramientas/saltos.py` sobre el MP4 final. Las marcas se anotan y se explican (en el ejemplo, 3 de 2,5–3,6 %).
7. Un médico mira el video y la tabla de fuentes.

## El truco de unir 3D y Manim

- Una sola línea de tiempo (`tiempos.json`) y una sola pista de audio (`mezcla.wav`). El 3D dibuja **negro** donde Manim
  dibuja; `juntar.py` pone Manim encima en esos tramos (`overlay=enable=between(t,…)`).
- **Puente por imagen**: el último cuadro 3D antes de un tramo de Manim se guarda como PNG con las posiciones en pantalla de
  los puntos clave (`window.puente(t)`); Manim empieza mostrando esa misma imagen y dibuja encima el contorno del mismo
  hueso: el corte no se nota. Las cabeceras de las dos técnicas se miden y se igualan (en el ejemplo, ±1 px).
- Un subagente de Manim con archivos exclusivos y el contrato escrito (tiempos de cada tramo, paleta, cabecera, puente) trabaja
  mientras el principal hace el 3D.

## Exportar (3D por partes)

- En una laptop con dos GPU, Chrome sin ventana puede usar la integrada (≈190 ms por cuadro). Con
  `VIDEOS_CHROME_ARGS="--use-angle=vulkan --enable-features=Vulkan --ignore-gpu-blocklist"` usa la dedicada (≈100 ms) —
  **pero Vulkan deja texturas negras, fondos faltantes y cuelgues en exportes largos** (ver `exportar-video`): un export
  hecho así **hay que verificarlo con `verificar_export.py` antes de compartirlo**; mejor exportar con la integrada y por
  tramos. No junto con Blender (los dos usan la GPU). `--force-high-performance-gpu` y `--use-angle=d3d11` no la toman.
- Por partes: `VIDEOS_PUERTO=8793 VIDEOS_PARTE=p2 VIDEOS_PARAMS="fps=60&desde=121.78&hasta=138.99&parte=p2" VIDEOS_CHROME_ARGS=…
  .venv/Scripts/python herramientas/navegador.py exportar <carpeta>/tres` → `render/<carpeta>_<parte>.mp4`. Cada parte, su
  puerto. 3 a 4 en paralelo andan bien. Dejan avances para ver mientras el resto sale (se les pega su tramo de la mezcla con
  `ffmpeg -ss <inicio> -i mezcla.wav`).

## Prompt de investigación (reutilizable para otro procedimiento)

> Investigación médica rigurosa (español de tú), para un guion de video educativo sobre **<procedimiento>** según la **AO
> Surgery Reference** (primero esa; si no carga, guías del fabricante, PubMed/PMC, Radiopaedia, Orthobullets; di cuál usaste
> en cada dato). Sólo lectura: sin descargas, sin formularios, sin cuentas. Con la URL de la fuente al lado de cada dato:
> 1. **Anatomía** relevante: estructuras, inserciones, irrigación, nervios en riesgo (a qué distancia de qué), medidas útiles
> para dibujar a escala. 2. **Clasificación** exacta (AO/OTA 2018 u otra), con subgrupos. 3. **Indicaciones** (y cuándo se
> prefiere otro tratamiento). 4. **Técnica paso a paso**: posición, abordaje, maniobras de reducción, colocación y medidas
> en mm, orden de los tornillos, control con fluoroscopia, errores típicos. 5. **Diseño del implante**: agujeros, tornillos,
> largos, material. 6. **Postoperatorio y rehabilitación** con plazos. 7. **Complicaciones** con cifras si la fuente las da.
> Al final: frases clave que el video debe decir, cosas que NO debe decir porque serían inexactas, y lo no verificado
> («sin fuente»). Nada inventado.

Hallazgo importante del primer ejemplo: **la AO Surgery Reference no usa los códigos 11A1/11A2…** en sus páginas; ordena
con nombres descriptivos. El video los usa porque vienen de la clasificación AO/OTA 2018 (Radiopaedia, Marongiu 2020), y lo dice.

## Lo que salió mal en el ejemplo (para no repetirlo)

- La cabeza de los tornillos entraba en el metal y las roscas rozaban la pared en 7 de 12: los agujeros se habían perforado
  perpendiculares a la placa, no en el ángulo de cada tornillo. Sólo lo encontró la verificación numérica.
- Los tornillos iban casi paralelos, y la voz decía «en distintas direcciones»: tampoco se veía a ojo.
- El rótulo decía «9 tornillos» con 3 en pantalla; la voz decía «9 agujeros».
- Dos cabeceras («3» y «4») se encimaron un cuadro por forzar una a mostrarse fuera de su tramo.
- Dos agujeros de sutura se juntaban con los de la fila A; la punta de un tornillo del calcar quedaba a 3,7 mm de la superficie.
- Manim: el casquete de cartílago sale como medialuna angosta porque el anillo se ve casi de canto en esa vista.

## Para hacer otro procedimiento

Cambia lo específico, no el método. Candidatos de cirugía de fracturas (todos con página en la AO Surgery Reference, que ordena por
hueso → segmento → tipo de fractura → tratamiento): placa volar en fractura de radio distal; clavo endomedular de fémur
(anterógrado) y de tibia; DHS o clavo cefalomedular en fractura pertrocantérea; tornillos canulados en el cuello femoral;
reducción abierta de maléolos (placa de peroné + tornillos de sindesmosis); clavo en fractura de húmero proximal (para
comparar con la placa de este video). Cada uno pide: el hueso real (BodyParts3D trae casi todos los huesos), el implante
modelado con las medidas publicadas, y su lista de «lo que se aproxima».

## Qué no hacer

- Publicar sin que un médico lo revise, o usar el video como indicación clínica (los créditos lo dicen).
- Dar cifras de complicaciones como si fueran del tipo de fractura del video (las series son mixtas).
- Comparar tratamientos («la placa es mejor que el clavo»): las fuentes no lo respaldan.
- Mostrar medidas de una pieza que el fabricante no publica.
- Narrar antes de que el guion esté aprobado.
