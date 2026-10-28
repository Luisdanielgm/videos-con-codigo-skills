---
name: video-explorable
description: Técnica 25. Explicativo explorable - una sola escena con física o cálculo real que funciona de dos maneras con el mismo código de dibujo - en el navegador la persona la manipula (arrastra, gira, cambia un parámetro) y, sin parámetro, un recorrido guionado (cada valor en función de t) que el reproductor graba como video. Todo lo que se ve (rayos, imagen, cifras) sale del cálculo. Usar para explicar una ley o un mecanismo («dónde se forma la imagen», «cómo se desarma un motor») y dejar además la página para que el público juegue.
---

# Explicativo explorable (técnica 25)

Antes: leer **`director-de-video`**. Ejemplo (no publicado en este repositorio; los comandos de abajo muestran la
estructura): `25-explorable/lente/` (42 s, 1920×1080): una lente delgada; la vela se
acerca de 3,2 f a 0,62 f y se ven los tres rayos principales, la imagen (real o virtual) y las cifras dₒ, dᵢ y el aumento.
Abierta con `?explorar=1`, la vela se arrastra con el ratón y la rueda cambia el foco. Origen: los explicadores que se
desarman en el navegador (el motor Raptor 3 de @konstantinsaifo; el «plano de enfoque» de una lente), vistos en X.

## La forma

1. **`render(t, parametros)`**: dibuja la escena a partir de los parámetros (aquí dₒ y f). Nada sabe de si es video o
   explorable. Toda cifra y toda línea salen de la fórmula (lente: 1/f = 1/dₒ + 1/dᵢ, m = −dᵢ/dₒ).
2. **`GUION`**: lista de claves `[t, valor, texto]`; entre claves el valor se interpola con curva suave y el texto entra con
   resorte. El video es `render(t, guion(t))` + el texto + una tarjeta final con la fórmula y la invitación a explorar.
3. **Modo explorable** (`?explorar=1`): no arranca el reproductor; eventos de puntero (arrastrar) y rueda cambian los
   parámetros, y un `requestAnimationFrame` llama al mismo `render`.

## Cuidado

- **El cuadro 0**: el reproductor mezcla subcuadros y en el cuadro 0 pide un t un poco negativo; si el texto depende de
  `t >= 0`, el título sale a medio tono. Usar `Math.max(t, 0)` al buscar la clave activa.
- Los casos límite de la física se dibujan, no se esconden: en el foco (dᵢ = ∞) los rayos salen paralelos y no hay
  imagen; dentro del foco la imagen es virtual y sus rayos se prolongan punteados hacia atrás.
- Las cifras cambian rápido en los tramos de movimiento: con desenfoque de subcuadros se ven dobles en una captura suelta
  (en movimiento no se nota). Si molesta, redondear más o congelar la cifra mientras el valor viaja.
- Verificar la física contra la fórmula en tres puntos (aquí: 3,2 f → dᵢ = 1,45 f; 2 f → m = −1; 0,8 f → dᵢ = −4 f, m = 5)
  y probar el modo explorable en el navegador (arrastrar y leer la consola).

## Verificar y exportar

```
.venv/Scripts/python herramientas/mezclar.py 25-explorable/<video>
.venv/Scripts/python herramientas/navegador.py capturas 25-explorable/<video> 0,14,24,27,36,40.5
VIDEOS_TRAMO=10 .venv/Scripts/python herramientas/navegador.py exportar 25-explorable/<video>
```

## Nivel de estudio (lo que falta)

- Voz (`narrar-guion`) en vez de textos; y una versión 3D (three.js) que se desarma por capas, como el motor de referencia.
- Pantalla de enfoque: una pantalla fija y la imagen borrosa según cuánto le falta a dᵢ (el «plano de enfoque»).
