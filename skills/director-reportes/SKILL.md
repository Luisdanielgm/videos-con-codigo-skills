---
name: director-reportes
description: Subdirector de videos de reporte (informe semanal o diario de un proyecto, video para una reunión, estado de un sistema, qué se hizo y qué falta). Va entre `director-de-video` y las skills de técnica - pone la regla de verdad (cada cifra contra git), la estructura del informe y propone técnicas por tramo, sin restringir ninguna. Usar después de `director-de-video` en todo video que rinda cuentas de un trabajo.
---

# Director de reportes (subdirector)

Capa intermedia: `director-de-video` (general) → **esta skill** → skill de cada técnica. No cambia ninguna técnica ni
limita cuáles se usan. Cada reporte lleva su `brief.md` en la carpeta del video, con el pedido y las reglas de ese
proyecto (qué se dice y qué no). (Los ejemplos hechos con esta skill son de proyectos propios y no se publican.)

## 1. La regla de verdad

- **Cada cifra se contrasta con git** del repo del proyecto (sólo lectura) antes de narrarla. Si el resumen del agente y
  git no coinciden, manda git y la diferencia se anota en el `brief.md`.
- No se dice «verificado», «en producción» ni «funciona» si el repo no lo prueba. Lo que falta se cuenta: un reporte
  honesto tiene su escena de pendientes (p. ej. «el sistema prefiere no publicar un dato antes que inventarlo»).
- Sin nombres de clientes, usuarios reales, dominios no confirmados ni datos de terceros (ninguna empresa cliente por
  su nombre). Las reglas «Lo que no se dice» de cada proyecto mandan.

## 2. Estructura

1. Gancho con la cifra o el hecho más importante de la semana.
2. Qué se hizo, agrupado por lo que le importa a quien mira (no por commit).
3. Una prueba en pantalla real (captura del sistema) por cada logro grande.
4. Qué falta, con la misma honestidad.
5. Cierre: qué sigue.

Para una reunión con alguien que no conoce el sistema: primero qué es (una idea), después un recorrido concreto (un
caso de punta a punta) y al final lo que falta.

## 3. Qué técnica propone por tramo (no es una lista cerrada)

| Tramo | Proponer primero |
|---|---|
| Cifras, avance, conteos | `video-pizarra` (Manim: números que cuentan), `video-calculo-real` |
| El sistema real funcionando | `video-pantalla-real`, `video-app-real` |
| Rutas, geografía, flujos entre áreas | `video-datos-mapa` |
| Cómo funciona una parte del sistema (una cola, una caché, un flujo entre servicios) o qué cambió en ella | `video-maquina-isometrica` (2D claro si el reporte se imprime o se proyecta en una sala; oscuro con brillo si es para pantalla) |
| Titulares y transición entre capítulos | `video-showreel` (tipografía cinética) |

Los reportes que se muestran a otras personas son pieza editada, no informe animado: combinar 2–3 técnicas
(`director-de-video`).

**Nada de puro cuadritos y texto**: un reporte de cajas, contadores y barras sale correcto pero monótono. Cada tramo
elige un objeto que se mueva y cause algo: un paso del sistema contado como una **línea de armado isométrica** (una pieza pasa
por cada control y se queda ante un portón cerrado), una compuerta de lista negra contra una de lista
blanca, una torre que sube con las líneas añadidas y un núcleo al que se acoplan las pantallas. Es el lenguaje de la técnica 26 (`bloque`,
`vista`, `pintar` en su `escena.py`) dentro del motor Manim: una sola línea de tiempo, voz y efectos como siempre, y el texto sólo para cifras y
rótulos cortos. Para la vista previa, renderizar sólo unas escenas en baja calidad (`-ql`); el render final va por tramos (`-n a,b`) en paralelo con la PC libre.

## 4. Formato

- Versión de teléfono primero si es para mandar (1280×720, < 16 MB); horizontal 1080p cuando haga falta.
- Sin música de fondo (explicativo): voz + efectos por contacto.
- 2–4 min por semana de trabajo; 3–5 min para una reunión.
- Render: reglas de `exportar-video` («Reglas de render»).
