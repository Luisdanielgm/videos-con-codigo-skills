---
name: video-blender
description: 'Hace un video narrado con render real de Blender (EEVEE), manejado sólo por un script de Python, con personajes animados por captura de movimiento de actores reales (base pública de CMU). Los personajes salen de dos caminos - Blender puro por código o modelos hechos con IA (hoja de modelo generada → malla 3D generada) con esqueleto y cara animable. Técnica 6 del proyecto, la de mejor aspecto visual. Usar para historias o escenas que necesiten luz, agua, materiales y movimiento natural.'
---

# Video en Blender con captura de movimiento (técnica 6)

Resultado: `06-blender/<video>/escena.py` (+ `guion.json`, audio, `tiempos.js`, `montaje.json`) y el MP4
en `render/06-blender_<video>.mp4`. Este paquete trae las **herramientas** de la técnica (biblioteca de
personajes, retargeting, lector de BVH, montaje) pero no una escena de ejemplo: la del proyecto original
adaptaba un libro con derechos. La estructura de `escena.py` está descrita abajo.

## Qué hace falta (todo gratis; lo pesado va en `externos/`, fuera de git)

- **Blender portable 4.5 LTS**: de download.blender.org (carpeta `release/Blender4.5/`), el zip de Windows
  (`blender-4.5.x-windows-x64.zip`) o el `.tar.xz` de Linux. Comparar su sha256 con el archivo `.sha256`
  publicado en la misma carpeta (`certutil -hashfile <zip> SHA256` en Windows, `sha256sum` en Linux) y
  descomprimirlo en `externos/` (p. ej. `externos/blender-4.5.14-windows-x64/blender.exe`). No se instala.
  Los comandos de abajo usan esa ruta: cámbiala por la tuya.
- **Captura de movimiento**: `python herramientas/bajar_mocap.py` baja los clips BVH elegidos de la base
  de CMU (mocap.cs.cmu.edu, libre para cualquier uso; conversión a BVH de cgspeed publicada en el repositorio
  `una-dinosauria/cmu-mocap`) a `externos/mocap/`. El índice de los ~2.500 clips está en
  `cmu-mocap-index-text.txt` de ese repositorio; para agregar clips, sumarlos a `CLIPS` en `bajar_mocap.py`.
- **numpy** dentro del Python de Blender (ya viene con Blender 4.5).
- Una GPU cualquiera (se probó con una de 4 GB): EEVEE renderiza sin ventana. **Blender no se corre junto con
  otra cosa que use la GPU** (otro render, HyperFrames, un modelo local): se traba o se cae.
- Para montar: el `.venv` del proyecto con pillow y ffmpeg. `componer.py` usa fuentes de Windows
  (`C:/Windows/Fonts`: Segoe UI, Georgia); en otro sistema, cambiar `FUENTES` al principio del archivo.

## Cómo está armado

- `herramientas/bvh.py`: lee BVH y hace cinemática directa (sólo numpy).
- `herramientas/actor.py`: **retargeting propio, sin el esqueleto de Blender**: toma las rotaciones del
  actor y las aplica a un esqueleto con otras longitudes (un niño). `Pista` + `Segmento` dicen qué clip
  actúa cuándo, con fundidos, bucles sin salto, y el torso de un clip sobre las piernas de otro
  (`arriba=`). `mirar()` orienta la cabeza con límites de cuello y sin torcerla.
- `escena.py` (lo escribes tú, uno por video) se corre con
  `externos/blender-4.5.14-windows-x64/blender.exe -b --factory-startup -P 06-blender/<video>/escena.py -- <modo>`
  y tiene que:
  1. armar el lugar (p. ej. cielo físico Nishita + tinte de atardecer, mar con el modificador Ocean, rocas,
     árboles, una casa);
  2. traer los personajes de la biblioteca (`personajes.cargar(nombre)`);
  3. calcular la pose de cada cuadro en Python (`Pista.pose` → `Actor.fk`) y cargarla como animación de los
     huesos (`personajes.bases(esq, R, P)` da la `matrix_basis` de cada hueso);
  4. animar cámara, luces, ojos (escala Z = parpadeo) y boca (escala Z = habla) según `tiempos.js`;
  5. aceptar modos: `--capturas t1,t2,…` (cuadros sueltos a `render/blender_crudo/<video>_<t>.jpg`) y
     `--exportar` (todos los cuadros a `render/blender_cuadros/c_0001.jpg…`, retomando si se corta).
  La historia y los planos se calculan con Y hacia arriba (como el BVH y como la versión three.js) y se pasan
  a Blender (Z arriba) al final.
- **Biblioteca de personajes** (`herramientas/personajes.py` → `biblioteca/personajes.blend`, fuera de
  git; se rearma en ~20 s con `-P herramientas/personajes.py -- --construir`, y `-- --prueba <carpeta>`
  renderiza de frente, caminando, sentados, la cara y el perfil de cada uno). **No trae personajes**: `ESTILOS`
  viene vacío, con una plantilla comentada al principio del archivo (escala del esqueleto, grosor, colores de
  piel, ojos y pelo, tamaño de ojos y cabeza, y uno de dos tipos de ropa: de calle —camiseta con franja, short,
  medias, zapatillas y pelo en mechones— o traje entero —traje, cinturón metálico, botas y pelo en rizos—, con
  `brillo` opcional). Cada personaje que agregues sale así: esqueleto de Blender con los huesos del BVH, cuerpo
  de UNA malla (metaballs convertidos, sin costuras) con pesos calculados por cercanía a cada volumen, ropa por
  zonas con cortes derechos (en la pose en T), cabeza rígida en el hueso Head con ojos, boca, cejas, mejillas y
  pelo en volumen. **Lo que se pule en la biblioteca sale en todas las escenas.** Lo propio de cada historia (un
  accesorio, un brillo en los ojos, una luz) lo agrega la escena; un accesorio rígido se arma con `elipsoide()` y
  se pega a un hueso con `a_hueso()`.
- **Armar un personaje por código (camino A), paso a paso**: 1) copiar la plantilla de `ESTILOS` con un nombre
  propio y elegir el tipo de ropa; 2) `blender.exe -b --factory-startup -P herramientas/personajes.py -- --construir`;
  3) `-- --prueba <carpeta>` y mirar los renders (proporciones al caminar y sentado, ropa sin bordes dentados,
  cara de frente y de perfil); 4) ajustar `grosor`, `cabeza`, `ojo`, `manga`, `pierna` o los radios de `PARTES` y
  repetir; 5) `-- --hoja <carpeta>` saca las vistas de una hoja de modelo (cuerpo y cabeza, ortográficas) para
  compararlas lado a lado con un dibujo de referencia.
- `herramientas/componer.py`: título, subtítulos del color de quien habla, fundidos, «Continuará…» y audio
  → MP4, a partir de `montaje.json` (formato en el encabezado del archivo).

## Personajes: dos caminos (elegir con quien dirige; el recomendado primero)

| | A. Blender puro (`personajes.py`) | B. Modelos hechos con IA (`personaje_ia.py`) |
|---|---|---|
| Cómo | Metaballs + curvas por código | Hoja de modelo generada → malla con textura generada → esqueleto y cara en Blender |
| Aspecto | Muñeco estilizado, «de goma» | **Como la hoja de modelo** (nivel de estudio): pelo, orejas, ropa, zapatos reales |
| Costo | Nada | Las generaciones del servicio 3D que uses (cuenta propia, con cuota) |
| Cuándo | Extras, fondos, pruebas rápidas, algo que cambia seguido | Protagonistas y todo lo que sale en primer plano (**recomendado**) |

**Camino B, paso a paso:**

1. **Hoja de modelo** con un generador de imágenes: cuerpo en pose A en 5 vistas (frente, tres cuartos,
   perfil, espalda, tres cuartos de espalda) y cabeza en 6 (con arriba y abajo), fondo gris liso, misma
   escala. Opciones: si tienes una suscripción de ChatGPT, puedes conectar Codex (`codex exec`, el prompt por
   stdin) para que genere las imágenes; o cualquier generador de imágenes, en la nube o local, que se pueda
   llamar desde la terminal (el agente busca cómo conectarlo). Van a `biblioteca/referencias/crudas/`.
   Recortar frente, perfil y espalda sueltos (1024², centrados) a `recursos/modelos3d/entradas/`.
2. **Malla 3D desde varias imágenes** con un generador 3D (p. ej. Hunyuan3D 3.1 en 3d.hunyuan.tencent.com:
   «Imágenes múltiples», **~500 mil caras**, que más no se nota en video y hace lento el esqueleto). En ese
   servicio, la casilla del frente es la del centro; la espalda, la de abajo; el perfil va a la izquierda si
   la nariz apunta a la izquierda de la imagen. Bajar en GLB a `recursos/modelos3d/<nombre>.glb`. Mirar la
   licencia de uso de lo generado antes de publicar. Otros servicios parecidos existen; los gratuitos en
   Hugging Face suelen quedarse sin cuota diaria de GPU en pocos minutos, y en una GPU de 4 GB no corre local
   nada de este nivel.
3. **Medir y ubicar articulaciones**: `herramientas/medir_glb.py` (cortes por altura:
   `blender.exe -b --factory-startup --python herramientas/medir_glb.py -- <archivo.glb>`) y
   `personaje_ia.py -- --foto <nombre> <carpeta>` (bolitas rojas en frente y perfil). Anotarlas en `AJUSTES`,
   que viene vacío con una plantilla comentada: nombre del .glb, la escala que deja la cabeza a la altura que
   esperan las cámaras de la escena, la escala del actor, la altura de la cara, las 17 articulaciones del lado
   izquierdo (el derecho es el espejo), dónde empieza la cabeza rígida, ojos y boca. Para `--foto`, anotar primero
   el .glb y unas juntas aproximadas, y corregirlas mirando las bolitas.
4. `personaje_ia.py -- --construir` y `-- --prueba <carpeta>` (reposo, camina, sentado, ojos cerrados y
   boca abierta, perfil, la cara de cada uno y sus expresiones). La escena los trae con `personaje_ia.cargar`
   y los pone en pose con `ActorIA`.
5. **La boca es la del modelo, no una agregada** (`boca_real`): la zona de los labios se subdivide, la malla
   se corta justo sobre la curva de la sonrisa pintada (cada arista que la cruza se parte en el cruce) y se
   separa por ahí; una deformación «abrir» baja el labio de abajo, y por dentro van un fondo oscuro y los
   dientes. Las expresiones (`sonrisa`, `tristeza`, `sorpresa`) son otras deformaciones manejadas por
   propiedades del vacío `boca` (0 a 1); la escena las anima según el guion.
6. De noche, una **luz de cara** suave que sigue a cada personaje desde el lado de la cámara. Medir el brillo de
   la cara y del cielo antes y después (no a ojo: con la cara más clara, lo demás *parece* más oscuro).

**Lo que falló en el camino B (revisar siempre):**
- El calor de Blender (pesos automáticos) **falla entero** en mallas de IA: 0 vértices con peso y el
  cuerpo no se mueve (sólo la cabeza). Se calcula en una copia rehecha con vóxeles de 8 mm y se pasa.
- La malla viene en pose A y con otras proporciones que el actor: el esqueleto se arma con las
  articulaciones de la malla y cada hueso guarda `Q` (T del BVH → pose A); `ActorIA` recalcula las
  posiciones con esos largos. Si se usan los largos del actor, el personaje se estira.
- Cuello: si la cabeza gira sola (lo que hace `mirar`), el cuello corto se estira como un elástico. El
  giro se reparte en tercios entre Neck, Neck1 y Head (`personajes.repartir_cuello`), y la zona rígida de
  la cabeza empieza en la barbilla con una transición ancha.
- Boca y párpados agregados: cerrados tienen que desaparecer en los tres ejes. Una boca aplastada sólo
  en alto quedó como un disco que se veía como **bigote**. Y una boca agregada se abre encima de la pintada,
  que queda cerrada: se ve burda. Por eso la boca va cortada en la malla (paso 5).
- Corte de la boca: borrar caras deja un hueco negro con la boca cerrada; cortar por las aristas que ya
  tiene la malla deja el borde dentado, astillas y huecos sueltos en las comisuras. Un fondo de boca más
  ancho que ~0,9 del ancho de la boca asoma por las mejillas con la boca cerrada.
- Las comisuras pintadas en la textura no se mueven con las expresiones (en la tristeza quedan rayitas).
- El modelo puede inventar detalles (una franja de más en la ropa): comparar con la hoja y corregir la
  textura (`arreglar_textura`, con la banda en `AJUSTES[...]["franja"]`). La imagen del .glb viene empaquetada:
  para editarla se crea una imagen nueva; la malla reducida tiene cuadriláteros.

## Pasos

1. Guion, narración y sonido: skills `video-historia` y `narrar-guion`.
2. **Elegir los clips mirando los números, no el nombre**: para cada clip candidato imprimir por
   segundo la altura de la cadera y de los pies, el ángulo de rodilla y la altura de las manos respecto
   de la cabeza (con `Bvh.pose(f)`, fuera de Blender, con el Python del proyecto). Así se encuentra el tramo útil.
3. `blender.exe -b --factory-startup -P 06-blender/<video>/escena.py -- --capturas 12,35,63` →
   `render/blender_crudo/`; `.venv/Scripts/python herramientas/componer.py 06-blender/<video> --capturas` →
   `render/capturas/`; revisar con `hoja.py` (skill `exportar-video`).
4. **Borradores por partes** (720p, con la GPU libre) antes del final: `componer.py <carpeta> --video --borrador`
   toma `render/blender_borrador/` y `--tramo 26.8 47.3` monta sólo un tramo con su audio.
5. `escena.py -- --exportar` (horas; en segundo plano; retoma donde quedó) y después
   `componer.py 06-blender/<video> --video` → `render/06-blender_<video>.mp4`. `componer.py` avisa si faltan cuadros.

## Lo que falló en el proyecto original (revisar siempre)

0. **Personajes de piezas sueltas** (versión 1): una esfera por hueso dejaba las piernas separadas del
   cuerpo al sentarse y sin cuello ni manos. Por eso la biblioteca usa una malla continua con esqueleto.
   Y los pesos por hueso dominante dejaban los bordes de la ropa dentados: la ropa se corta por zonas.
0b. **Sentarse en un borde**: la columna de roca era más ancha que la cima y las rodillas quedaban
   adentro de la piedra. Ubicar el asiento en el borde real (el de la malla más ancha) y la cadera
   ~17 cm sobre la superficie.
1. **Clips con otra cosa de la que dice el nombre**: «sentado» tenía los brazos arriba agarrado a
   un juego; «de pie» era un estiramiento con los brazos en cruz; «brazos arriba» duraba medio segundo
   (saludaba). Medirlos (paso 2). Para poses sostenidas, tomar un clip quieto y poner a mano las
   rotaciones que faltan.
2. **Blender 4.4+ guarda la animación en «ranuras» (slots)**: si se anima un objeto y después sus
   datos (la lámpara, la cámara), comparten acción; leer `action.fcurves` sólo trae la primera ranura
   y lo demás se pierde sin error (quedaron el lente de la cámara y las luces sin animar). Leer las curvas de
   la ranura de cada id con la API de acciones por ranuras de Blender 4.4+, no sólo `action.fcurves`.
3. **numpy modifica en el lugar**: `np.asarray(v); v /= norma` cambió el vector de quien llamaba (el
   emblema terminó flotando sobre la cabeza). Copiar con `np.array`.
4. **El cielo físico mide el giro del sol desde otro eje**: `sun_rotation = atan2(x, y)` (medido con un
   render de prueba). Si no coincide con la lámpara del sol, aparecen dos soles.
5. **Nada de luz de luna antes de que salga la luna**: el reflejo en el agua la delata.
6. Los primeros planos se apuntan a la **altura real** de cada cabeza (calculada con la pose), no a
   números copiados de otra técnica con personajes de otro tamaño.
7. Temblores rápidos + desenfoque de movimiento = cara borroneada: temblar lento.
8. La cámara con interpolación constante: los cortes no se desenfocan.
9. Una luz muy fuerte cerca del agua + brillo (glare) = mancha blanca: apagarla rápido.

## Verificar

- Capturas compuestas de todas las frases sin los defectos de arriba ni los de `exportar-video`.
- El MP4 dura lo mismo que `TIEMPOS.total`; `saltos.py` sobre el MP4.

## Herramientas externas (opcional)

- Generador de imágenes para las hojas de modelo y generador 3D para las mallas (camino B, arriba).
- **Mixkit** (música y ambiente) si la historia lo pide; bajar a `recursos/`, cada archivo con su licencia.
