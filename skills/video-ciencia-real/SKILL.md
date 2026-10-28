---
name: video-ciencia-real
description: Técnica 22. Ciencia con datos reales - una estructura de la base PDB (virus, proteína, complejo) dibujada átomo por átomo desde el mmCIF, con su ensamblaje biológico, en three.js (cientos de miles de esferas impostoras a tiempo real), rótulos de instrumento con cifras medidas por un script, colores por cadena o por elemento y un zoom continuo de potencias de diez con regla de escala (de algo que se ve a simple vista a los átomos). Usar para «esto no es un dibujo» - virus, proteínas famosas, cualquier molécula con coordenadas públicas.
---

# Ciencia con datos reales (técnica 22)

Ejemplo (no publicado en este repositorio): `22-ciencia-real/virus-tomate/` (virus del enanismo arbustivo del tomate,
**PDB 2TBV**, 397.620 átomos, 180 cadenas, 354,2 Å; de una hoja de 2 cm a los átomos). Su `brief.md` tenía las cifras, la
fuente de cada frase, lo que es esquema y los comandos: armar uno igual para cada video. Referencia: @OliverNabani (T4
átomo por átomo, en X). Base: `video-threejs` (contrato del HTML) y `video-calculo-real`
(ningún número a mano; el guion sale de una plantilla con las cifras).

## La regla

**Todo lo que se dice que es real sale del archivo**: posiciones, cadenas, elementos, el ensamblaje, cada cifra del rótulo y
de la voz. Lo que no sale del archivo (el mundo alrededor del zoom, dónde están las partículas, la luz) se rotula «esquema» en
pantalla mientras se ve. Si el tema toca salud, además rige la skill `video-medico` (fuente por frase, nada clínico sin
revisión).

## Archivos de un video

| Archivo | Qué hace |
|---|---|
| `datos/<código>.cif.gz` | el mmCIF tal cual de `https://files.rcsb.org/download/<CÓDIGO>.cif.gz` (< 20 MB en el repo; más, en `externos/pdb/`, fuera de git) |
| `medir.py` | lee el mmCIF, arma el ensamblaje, **mide e imprime** las cifras, escribe `datos/atomos.bin`, `datos.js` y `guion.json` |
| `guion_plantilla.json` | el guion con `{marcadores}` y una `fuente` por frase (no se narra; `medir.py` la quita) |
| `verificar.py` | la voz dice las cifras de `datos.js`; el HTML no trae ninguna escrita a mano; el binario cuadra |
| `tiempos_provisionales.py` | `tiempos.js` a 2,6 palabras/s para armar la escena antes de narrar (`narrar.py` lo pisa) |
| `medir_ms.py` | ms por cuadro con la GPU obligada a terminar (`?medir=t1,t2`) |
| `index.html` | la escena (three.js local, `reproductor.js`) |
| `brief.md` | estructura, cita, sha256, cifras, fuente por frase, lo que es esquema, rendimiento y comandos |

## 1. De la base de datos a la escena

1. **Elegir la entrada**: en rcsb.org buscar la estructura y mirar el «Biological Assembly» (cuántos átomos tiene el
   ensamblaje completo). Rayos X o crio-ME; preferir resolución ≤ 3,5 Å. Bajar sólo el mmCIF (`.cif.gz`); el ensamblaje
   **no hace falta bajarlo aparte**: viene en el mismo archivo (`_pdbx_struct_assembly_gen` + `_pdbx_struct_oper_list`).
   Anotar URL, código, cita del artículo (`_citation`, la `primary`) y sha256 en el `brief.md`.
2. **Leer el mmCIF** sin dependencias (el lector de `medir.py`: fichas con comillas y campos `;`, bucles `loop_`). Ojo:
   - quedarse con el modelo 1 (`pdbx_PDB_model_num`) y, de los átomos con dos posiciones, **la primera letra que aparece**
     (en 2TBV son `P` y `S`, no `A`: filtrar por `A` borró 21 átomos sin avisar);
   - los valores de un bucle pueden partirse en varias líneas.
3. **Ensamblaje**: expandir `oper_expression` (`(1-60)`, `(1,2,6)`, `(X0)(1-5)` = producto, el de la derecha primero) y
   aplicar cada matriz a las cadenas de `asym_id_list`. **Comprobar**: cada matriz es una rotación (R·Rᵀ = I, det = 1); el
   número de copias × cadenas = `oligomeric_count`; los átomos de copias distintas no se pisan (pares a < 1,2 Å: en 2TBV
   salen 360, todos del mismo contacto Ile340–Asp348, que es del modelo y no del armado; si fueran miles, el armado está mal).
4. **Al navegador se manda la unidad asimétrica y las matrices**, no el ensamblaje: 6.627 átomos × 16 bytes = 106 KB en vez
   de 6 MB. La página multiplica al cargar (≈ 30 ms para 400 mil átomos).

## 2. Cuántos átomos aguanta el navegador y cómo dibujarlos

- **Un átomo = un cuadrado instanciado con una esfera impostora** (`InstancedBufferGeometry` + `ShaderMaterial`): el
  fragmento calcula la normal y escribe `gl_FragDepth`, así las esferas se cortan bien entre sí. Nada de `SphereGeometry`
  por átomo ni de `THREE.Points` (los puntos grandes desaparecen enteros al tocar el borde de la pantalla).
- **Cámara ortográfica** que el sombreador arma solo (`gl_Position` directo, la `THREE.Camera` no se usa): la regla de
  escala vale igual para todo lo que se ve, a cualquier profundidad.
- **El costo es de píxeles, no de vértices**: `gl_FragDepth` apaga el descarte temprano por profundidad y cada capa de
  átomos se pinta. Medido en 2TBV (Intel UHD 630, Chrome sin ventana): todos los átomos, 90–220 ms por cuadro; con los dos
  descartes de abajo, 20–30 ms (el corte, que necesita todos, 43 ms).
  1. **No dibujar la mitad de atrás** del cascarón (`v.z < -40 Å` en vista): la tapa la de adelante.
  2. **No dibujar los tapados**: `medir.py` calcula la superficie accesible (Shrake–Rupley, sonda 1,4 Å, 96 puntos por
     átomo) en el ensamblaje completo y marca los que se ven desde afuera (en 2TBV, 141.720 de 397.620). La página los
     ordena primero y dibuja sólo esos (`instanceCount`); todos sólo cuando un corte deja ver el interior. **Con sonda 0
     no sirve** (el 99,9 % «asoma» a huecos diminutos). Por las rendijas se ve sombra: debajo va un disco oscuro.
- Bordes suaves con `alphaToCoverage` y `fwidth` (con `antialias: true`).
- Colores sin `THREE.Color` (convierte a lineal y el `ShaderMaterial` no vuelve a sRGB): pasar los hex como vectores.
- **Sombreado con datos**: el «encierro» de cada átomo (vecinos a < 10 Å, de `medir.py`) oscurece lo hundido; luz de estudio
  fija; más oscuro lo de atrás.
- Radios: Van der Waals de Bondi (C 1,70; N 1,55; O 1,52; S 1,80 Å); iones con su radio iónico. Van en `datos.js`.
- Colores: por cadena (en una cápside T = 3, A/B/C muestra los pentámeros y hexámeros) y por elemento en el acercamiento
  (convención CPK: C gris, N azul, O rojo, S amarillo).
- Contar en el procesador lo que muestra un rótulo («átomos en el cuadro»), una vez por cuadro (`Reproductor.cuadro(t)`),
  **por copia**: si la esfera envolvente de la copia cae entera dentro o fuera, se suma o se salta sin mirar átomo por
  átomo (de 7,9 a 1,9 ms).

## 3. Cifras medidas desde los datos

`medir.py` imprime todo y lo deja en `datos.js` (`window.DATOS.cifras`); la página y el guion sólo leen de ahí:
átomos de la unidad y del total (× operadores), por elemento («sin hidrógenos: el archivo no los trae», si es rayos X),
cadenas, residuos vistos de la secuencia (`_entity_poly_seq`), diámetro (2 × radio máximo de los centros de átomo; decir
cómo se midió en el rótulo), radio mínimo, ejes de simetría **desde las matrices** (ángulo de giro: 180° → 2, 120° → 3, 72°
y 144° → 5; ojo, `round(360/144)` da 2) y qué cadenas rodean cada eje. Las citas del rótulo también salen del mmCIF.
Las cifras de la voz van en palabras con `palabras()` (0 a 999.999, «veintiún mil», «un mil» no).

## 4. Zoom de potencias de diez

- El ancho del cuadro `W` (en Å) manda todo: `log10 W` baja **a velocidad constante** (décadas por segundo), así cada
  década dura lo mismo: cada tramo dura en proporción a `log(zoom)`. Rampas cortas (1–1,4 s) al arrancar y frenar.
- **Dos anclas con la voz**: empieza al decir el objeto visible y llega a la escala del protagonista cuando la voz lo
  nombra; de ahí sale la velocidad, y el final se calcula. Si la narración cambia, se recalcula sola (`window.ZOOM`).
- El mundo de alrededor (hoja, células, cloroplastos) se dibuja en 2D con coordenadas en Å y la misma escala, por capas
  que entran y salen por década, con azar por celda (`hash(i, j)`), sólo lo que cae en el cuadro. **Rotulado «esquema».**
  Para que ese mundo no parezca un diagrama suelto, la variante Kurzgesagt de `video-html-canvas` (formas planas sin
  contorno, capas con parallax, quedarse quieto e iluminar el objeto antes de atravesarlo).
- Las partículas vecinas son un **sello** del modelo real (render del 3D a 768 px al cargar); la del centro pasa del sello
  al 3D vivo entre 2.000 y 1.400 Å de campo, con la misma orientación: no se nota el cambio.
- **Regla**: la mayor potencia de diez ≤ 20 % del campo; la barra crece y al cruzar la década salta a la marca siguiente
  («cada marca nueva es diez veces más chica»). Arriba a la derecha, el campo con su unidad y `× 10ⁿ m`; a la derecha, la
  pista de décadas con un triángulo.

## 5. Verificar

1. `medir.py` dos veces: mismos sha256 (`atomos.bin`, `datos.js`).
2. `verificar.py`: la voz dice las cifras de `datos.js`; ninguna cifra medida escrita a mano en el HTML.
3. Capturas (`navegador.py capturas`) de 6–12 instantes y hoja de contacto (`hoja.py`): una por década del zoom, el cambio
   de sello a 3D, el acercamiento, el virus entero (el contador tiene que dar el total), cada rótulo.
4. **Cuadro repetido igual**: capturar el mismo `t` dos veces y comparar sha256 del JPEG (en 2TBV, idénticos).
5. `medir_ms.py` en la GPU de destino. `herramientas/saltos.py` sobre el MP4.

## 6. Fuentes y licencias

- **PDB (RCSB)**: datos CC0 1.0; citar la entrada (`_citation` primary) y la PDB (Berman et al., Nucleic Acids Res 28,
  235, 2000). Bajar sólo los archivos que se usan; nunca cuentas ni formularios.
- Los hechos que no están en el archivo («el primero en…») llevan su fuente en la plantilla y en el `brief.md`.
- Lo que no se ve en los datos se dice («el ARN no se ve en estos datos»), no se dibuja.

## Lo que salió mal en el ejemplo (para no repetirlo)

- El filtro de posiciones alternativas por `A` borró 21 átomos; y `round(360/144) = 2` metió los ejes de 5 entre los de 3
  (16 ejes «de 3»). Las dos cosas las delató imprimir y comparar con lo esperado (6.648 filas en el archivo; 15/10/6 ejes).
- Con el descarte de tapados, por las rendijas se veía la célula verde del esquema: se puso un disco oscuro debajo.
- «Una sola proteína» iluminaba la cadena de la copia 1, que a esa hora quedaba de canto: se elige la más de frente.
- Rótulos que apuntan a objetos se iban sobre la pista de la derecha o la regla: se acotan a la zona útil.

## Qué no hacer

- Inventar átomos, cadenas o simetrías «para que se vea mejor».
- Hidrógenos que el archivo no trae; ARN o lípidos que el modelo no tiene.
- Bajar el ensamblaje ya expandido (pesa 60 veces más) si el mmCIF trae las matrices.
- Mostrar el mundo de alrededor sin el rótulo de esquema.
