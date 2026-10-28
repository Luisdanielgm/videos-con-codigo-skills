---
name: director-marketing
description: Subdirector de videos de marketing (comerciales, reels, piezas para las redes de un producto). Va entre `director-de-video` y las skills de técnica - reúne lo que sirve para vender un producto con material verdadero y propone las técnicas por tramo, sin restringir ninguna ni cambiar `video-lanzamiento`. Usar después de `director-de-video` en todo video cuyo fin sea mostrar o promocionar un producto.
---

# Director de marketing (subdirector)

Capa intermedia: `director-de-video` (general) → **esta skill** → `video-lanzamiento` (base de los comerciales) → skill
de la técnica. No reemplaza ni modifica `video-lanzamiento` ni ninguna técnica: las ordena para que cada pieza salga con
la calidad de las ya hechas. Todas las técnicas siguen disponibles.

## 1. Lo que no se negocia

- **Material verdadero**: lo que el video muestra o afirma lo respalda el repo del producto (capturas, cifras contra git,
  funciones que existen hoy). Sin usuarios reales, sin datos de terceros, sin marcas ajenas (p. ej. nombres de
  aerolíneas en una app de vuelos).
- **Antes de cada pieza se lee la ficha de marca del producto** (`marca.md`, idea de `product-film`): identidad, lo que
  el dueño pidió, lo que rechazó y lo que no se dice, cada línea con su fecha y su fuente. **Cada corrección nueva sobre
  una pieza se suma ahí** en una línea (fecha · dónde se dijo), para que la siguiente arranque con ella. Las que valen
  para todos los productos van en una guía común de marketing.
- **Publicar es del dueño** (🔴). El agente deja el video listo; no sube nada.
- **Dos formatos por pieza**: vertical y horizontal, cada uno con su composición (no se recorta el 16:9).
- **Calidad de edición alta**: pieza editada, no informe animado, con 2–3 técnicas combinadas.
- Música: en marketing sí va (calculada con `musica.py` o canción libre en la grilla de pulsos); en explicativos no.

## 2. Qué técnica propone para cada función (no es una lista cerrada)

| Función del tramo | Proponer primero |
|---|---|
| Gancho de 1–3 s | `video-particulas`, `video-forma-unica`, `video-showreel` |
| Prueba de que existe (credibilidad) | `video-pantalla-real`, `video-app-real` |
| Datos, rutas, cifras vivas | `video-datos-mapa`, `video-calculo-real` |
| Producto como objeto | `video-producto-3d`; si el objeto es un `.glb` propio (de un modelo o escaneo), `video-maquina-isometrica` en 3D lo limpia y lo restiliza oscuro con brillo (`iso3d.py glb`) |
| «Cómo funciona» el producto, explicado como una máquina | `video-maquina-isometrica` (oscuro con brillo para reels y aperturas; lo encendido es lo que el producto hace) |
| Storyboard rápido con escenas probadas | `video-hyperframes` |
| Marca con alma, manifiesto | `video-ensayo`, `video-collage` |
| Reel vertical tipográfico | `video-showreel` |
| Cierre con marca | `video-showreel`, `video-forma-unica` |

Las combinaciones que ya funcionaron están en `director-de-video`.

## 3. Oficio (resumen; el detalle vive en `video-lanzamiento` y `director-de-video`)

- Plan en grilla de pulsos antes del código; gancho en los primeros 2 s; un momento fuerte cada 3–5 s.
- Cada efecto visible tiene una causa en pantalla (cursor, botón).
- Semana tipo: tres familias y tres estilos distintos.
- Legible a 360 px de ancho y comprensible sin sonido.
- Duración que mejor rinde: 15–32 s.

## 4. Render

Construir primero, exportar al final, por tandas. Reglas de render en `exportar-video` («Reglas de render»): calidad
antes que tiempo; por partes sólo si la página pasa `determinismo.py`; final con la PC vacía y preguntando antes.

## 5. Adecuaciones

Marketing no lleva adecuaciones por perfil salvo que se pidan. Si se piden, leer `adecuaciones-cognitivas` (las
reglas de contraste, subtítulos aparte y sin destellos sirven también para que un reel llegue a más gente).
