---
name: video-datos-mapa
description: 'Técnica 11. Comercial (25–30 s) con un globo de puntos que se acerca a la región, una red de rutas y gráficos que se calculan en vivo (modelos, Monte Carlo), en Canvas 2D con Natural Earth, en grilla de pulsos con música calculada. Usar para software de gestión, finanzas, logística o aviación.'
---

# Datos y mapa (técnica 11)

Antes: leer la skill base **`video-lanzamiento`**. No hay ejemplo publicado (el original era el comercial
de un producto propio); la estructura es: `11-datos-mapa/<producto>/index.html` + `datos.js` con la tierra en
puntos, la región con más detalle, los lugares (p. ej. aeropuertos o almacenes) y las rutas.

## Qué hace falta

- **Natural Earth** (dominio público): `ne_110m_land.geojson` del repositorio `nvkelso/natural-earth-vector`
  en GitHub (carpeta `geojson/`), en `externos/geo/`. Para la región con más detalle, la versión `ne_50m_land`
  o `ne_10m_land` del mismo repositorio.
- El entorno `.venv`, ffmpeg y Chrome. Las coordenadas de los lugares, de una fuente abierta citable.

## Idea

Globo de puntos que gira y se acerca al país, rutas que se dibujan entre lugares, y gráficos que se
calculan de verdad en pantalla (costo por hora, simulación Monte Carlo). Las cifras de ejemplo se rotulan
«cifras de ejemplo».

## Motor y pasos

1. Tierra de `externos/geo/ne_110m_land.geojson` → puntos a `datos.js` (un script de Python que muestrea una
   grilla de latitud y longitud y se queda con los puntos dentro de los polígonos); una malla de más detalle
   para la región.
2. Globo en Canvas 2D: proyección ortográfica a mano (latitud/longitud → x, y, z; girar; dibujar sólo z > 0),
   con la cámara (giro y zoom) en resortes por pulso (`herramientas/movimiento.js`).
3. Modelo de cálculo real en JS (lo que se muestra sale de ahí; nada de números pegados a mano).
4. `musica.json` → `herramientas/musica.py <carpeta>` (o canción real con `pista.py`), capturas por pulso,
   hoja de contacto, `navegador.py exportar <carpeta>` (skills `video-lanzamiento` y `exportar-video`).

## Lo que falló

- Rutas cuyos lugares no tenían coordenadas: saltarlas, no inventarlas.
- La malla de detalle de la región se veía con borde recto: **que cubra más que el encuadre**.
- Escalas de gráficos que se salían al llenarse: escala fija calculada con el valor final.
- Etiquetas de lugares encimadas: desplazamiento a mano por lugar.

## Verificar

- Cada cifra en pantalla sale del modelo en JS o de `datos.js`; las de ejemplo dicen «cifras de ejemplo».
- Capturas en los pulsos clave sin etiquetas encimadas ni gráficos fuera del cuadro; `saltos.py` sobre el MP4.

## Nivel de estudio

- **Una sola toma**: el globo acerca a la región, una ruta se vuelve el eje del gráfico siguiente y las barras
  nacen de los puntos del mapa. Nada entra por opacidad.
- **Cierre sin tiempo muerto**: el logo quieto 1 s como máximo.
- **Cifras que ruedan** con `t` redondeado y un tic real por barra; las de ejemplo, rotuladas.
- Canción real, efectos reales y 60 fps (`video-lanzamiento`).

## Herramientas externas (opcional)

- **Mixkit** (canción y efectos; bajar a `recursos/`).
- **Datos abiertos** (Our World in Data, Natural Earth; citar la fuente) si el tema pide datos públicos. Los del
  producto salen de su repositorio.
- **No conviene**: modelos 3D generados de vehículos con colores o logos de una empresa real (sin permiso no se
  usan, y sin ellos no suman) ni imágenes generadas para el mapa (sale de Natural Earth).
