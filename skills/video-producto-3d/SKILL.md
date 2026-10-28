---
name: video-producto-3d
description: 'Técnica 9. Comercial (25–30 s) con objetos 3D del mundo del producto (un recibo, fichas, una cesta) y datos reales convertidos en objeto (una curva 3D que la cámara sigue), en three.js local, en grilla de pulsos con música calculada. Usar para productos con algo físico o con datos que se pueden volver objeto.'
---

# Producto en 3D (técnica 9)

Antes: leer la skill base **`video-lanzamiento`** y la de 3D **`video-threejs`** (three.js local, contrato de dos
lienzos). Ejemplo: `09-producto-3d/libreta/` (una app de notas inventada: la libreta se abre, los renglones
saltan como fichas que se dan vuelta, barras con cifras de ejemplo rotuladas, una campana; `index.html` +
`musica.json` + `pulsos.js`, **leerlo entero**). Con datos reales del producto se suma `datos.js`.

## Qué hace falta

- El entorno `.venv`, ffmpeg y Chrome con WebGL (sin GPU, cae a WebGL por software: más lento).
- three.js 0.170 local en `herramientas/vendor/three.module.min.js` (viene en el paquete, licencia MIT).
- Datos reales y **públicos** del producto (nunca datos de usuarios).

## Idea

El producto se cuenta con objetos: p. ej. un recibo de papel curvado que un escáner recorre, precios que saltan
como fichas y giran de una moneda a otra, una cesta que se llena, y la curva real de datos dibujándose
mientras la cámara la sigue. Cierra con tarjetas de funciones y el logo.

**El objeto es un `.glb` propio (modelo o escaneo del producto)** y hay que mostrarlo limpio, sin sus texturas y con una sola parte
encendida: `herramientas/iso3d.py glb <archivo.glb> --acentos "<parte>"` y un visor de `.glb` como el de
`video-maquina-isometrica` («Variante 3D real»). Un modelo de decenas de MB se decima antes en Blender.

## Motor y pasos

1. Datos reales del producto a `datos.js` (sólo públicos, con su fuente). three.js local en `herramientas/vendor/`.
2. Cámara con resortes por pulso (`movimiento.js`); cada escena, sus claves.
3. `musica.py` (o `pista.py` con canción real), capturas por pulso, hoja de contacto, `navegador.py exportar`.

## Objetos impresos o con letras en 3D (p. ej. un llavero impreso en 3D, en un reel vertical)

- **Geometría de verdad, no planos apilados**: se dibuja la silueta en un lienzo 2D (texto engordado con
  `strokeText` + oreja con agujero), se saca el contorno con **marching squares**, se simplifica (RDP), se
  arman `Shape` con agujeros por contención y se extruye con **bisel** (`ExtrudeGeometry`). Los planos apilados
  con `alphaTest` se veían dentados y con letras gruesas.
- **Pulido**: entorno de estudio propio (`PMREMGenerator.fromScene` con cajas de luz), `MeshPhysicalMaterial`
  con `clearcoat`, y **líneas de capa** en los costados (textura de rayas como `map` y `bumpMap`: en los
  costados de `ExtrudeGeometry` la coordenada v es la altura).
- **Imprimir capa por capa**: plano de recorte en z (mundo) + tapa de la capa recién puesta + capa en curso
  recortada hasta la boquilla; la boquilla recorre el perímetro y después rellena.
- **Efectos de referencia que sumaron**: brillo (bloom barato en 2D: la imagen 3D a media resolución con
  `brightness contrast blur` sumada con `lighter`), iris de 6 hojas como transición, **goo** con un filtro SVG
  (`ctx.filter = 'url(#goo)'`), tipografía variable (p. ej. Bahnschrift de 250 a 700 y de normal a condensada),
  chispas en la punta, fotos como tarjetas 3D con paneo por dentro si son anchas.

## Lo que falló

- **La punta de un `TubeGeometry` va por largo de arco**: usar `curva.getPointAt(k)` para la punta (y la
  fracción en X), o el tubo se adelanta a la punta.
- Un viaje de cámara largo entre escenas se ve como objetos cruzando la pantalla: mejor un **corte** (otra
  lista de resortes que arranca en ese pulso).
- Etiquetas de la escala que se salen del cuadro: ubicarlas del lado donde hay espacio.
- Cifras que cambian: calcular con `Reproductor.cuadro(t)` (igual en todos los subcuadros; redondear a 1/30 no
  alcanza a 60 fps).
- **`material.clone()` clona también los `clippingPlanes`**: el costado quedó cortado por un plano fijo a la
  mitad de la pieza. Después de clonar, reasignar el mismo arreglo de planos.
- Los planos de recorte en el mundo se calculan con `matrixWorld`: llamar `scene.updateMatrixWorld(true)`
  antes, o salen con la posición del cuadro anterior.
- Un lienzo que quedó con `globalCompositeOperation = 'destination-out'` (para el agujero) **borra** lo que
  se le dibuje después: volver a `source-over` antes de redibujarlo.
- Con luz fuerte y tono ACES, el naranja se lavaba a blanco: bajar las luces o darle emisivo al color.
- En vertical (1080×1920) el ancho visible es chico: calcularlo (`2·d·tan(fov/2)·aspecto`) antes de ubicar.
- Una etiqueta que viaja con la cámara salió en cuatro copias (desenfoque de movimiento con pocos subcuadros): en
  esos tramos, 60 fps o más subcuadros.
- **Texturas de lienzo 2D que salen negras o transparentes en el exporte** (Libreta): con la GPU NVIDIA
  (`--use-angle=vulkan`) una textura subida a la GPU por primera vez tarde (la hoja, las fichas, la etiqueta, que
  aparecen en el pulso 8 o 30) salía negra; las capturas rápidas no lo muestran (hay que pedir 45 cuadros seguidos y
  después uno de los tardíos). Arreglo: pasar el lienzo a `DataTexture` (`getImageData`, `flipY = true`, mipmaps) y
  `renderer.initTexture` de todas al arrancar. No usar `initTexture` con `CanvasTexture`: salió peor.
- Un canvas con esquinas redondeadas sobre `MeshBasicMaterial` sin alfa deja las esquinas negras: rellenar todo el lienzo.
- **Cuadro 0 terminado y sin tomas quietas**: nada entra desde fuera del cuadro ni desde negro (el objeto ya está,
  el título ya está puesto); la cámara «respira» siempre (suma de senos chicos sobre los resortes, función de `t`), la
  luz recorre la pieza y lo que flota se mece. Con eso el cierre de 5 s medía 0 s quietos (cambio ≥ 300 px por cuadro).

## Verificar

- Hoja de cuadros por pulso (la de `video-threejs` además: nada tapado, etiquetas en zona útil).
- Cada dato en pantalla sale de `datos.js` con su fuente; `saltos.py` y duración del MP4.

## Nivel de estudio

- **Canción real** analizada con `cancion.py` (con la caída en el salto de la escena) en vez de música calculada.
- **Vertical**: el contenido entre ~250 y ~1500 px de alto (arriba y abajo lo tapa la interfaz de la red social).
- **Fotos reales sin filtros encima** (el brillo lavó una foto).
- **Sin fantasmas** (ver arriba) y **60 fps con efectos reales**.

## Herramientas externas (opcional)

- **Generador 3D desde imágenes** (p. ej. Hunyuan3D, con cuenta propia y cuota de generaciones): sólo para
  objetos del producto que no se pueden hacer por código (una bolsa, un producto). Un logo o un texto se extruye
  por código como el llavero. Para cargar el GLB hace falta `GLTFLoader` de three.js 0.170
  (`examples/jsm/loaders/GLTFLoader.js` del repositorio de three.js, MIT) en `herramientas/vendor/`. Revisar la
  licencia comercial de lo generado.
- **Fotos de clientes o de terceros**: pedir permiso antes de usarlas o de mandarlas a un servicio externo; si
  tienen nombres de personas, taparlos.
- **Mixkit**: canción y efectos (licencia gratuita de Mixkit; bajar a `recursos/`).
