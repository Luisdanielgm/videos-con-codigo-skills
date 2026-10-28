---
name: adecuaciones-cognitivas
description: Skill de APOYO para videos educativos con adecuaciones (neurodivergencia y discapacidad - autismo, TDAH, dislexia, ansiedad, discapacidad intelectual o procesamiento lento, sordera, baja visión, daltonismo, motora, fotosensibilidad). Sólo actúa si el usuario lo pidió al responder la pregunta de `director-educacion`; sin pedido no lee ni cambia nada y el video sale igual que hoy. Trae el DUA base, las reglas por perfil con su nivel de evidencia, cómo resolver las contradicciones con parámetros y la lista de verificación.
---

# Adecuaciones cognitivas (skill de apoyo de `director-educacion`)

**Fuente**: una guía interna de DUA y adecuaciones multimedia para neurodivergencia (no publicada: cuatro lectores, ~82
fuentes con texto completo, niveles de evidencia por regla); esta skill es su resumen. Si tienes una guía propia, manda
sobre este resumen. Es una **propuesta revisable, no una guía clínica**: nada está validado con personas ni por un
especialista.

## 0. Cuándo actúa (y cuándo no)

1. **Sólo con pedido explícito.** `director-educacion` pregunta siempre; si la respuesta es «normal», esta skill no se
   lee y el video sale exactamente igual que antes de que existiera.
2. **Dos niveles que no se mezclan**: **DUA base** (sección 1, sirve a todos) y **adecuación por perfil** (sección 2,
   sólo el perfil pedido).
3. **No toca ninguna skill de técnica.** Todo lo que cambia va en el guion, la escena y el `brief.md` de ESE video
   (paleta, pausas, nivel de movimiento, subtítulos), como parámetros.
4. **Ofrecer, no etiquetar**: las adecuaciones se ofrecen sin pedir diagnóstico (criterio DUA). Nunca se atribuye un
   diagnóstico ni se generaliza a «todas las personas autistas» (o con TDAH, etc.).
5. **Gustos personales ≠ regla**: si a la persona le gustan los pasteles, va en su `brief.md` como preferencia suya.
6. **Privacidad**: ningún dato personal (casos, nombres de menores, diagnósticos) entra al repo; sólo reglas generales.

## 1. DUA base (si se pidió DUA base o cualquier perfil)

| Regla | Evidencia (según la guía) |
|---|---|
| Señalar lo clave justo cuando se nombra (flecha, resaltado, énfasis de voz) | Alta (meta-análisis, efecto pequeño-medio) |
| Quitar lo que no explica: música decorativa, fondos recargados, animación de relleno | Alta [NV] |
| Tramos cortos con parada clara entre ideas | Alta [NV] |
| La voz dice lo que se dibuja y lee textos, resultados y ecuaciones; nada de «aquí»/«allí» | Estándar (WCAG 1.2.3/1.2.5) |
| Contraste de texto ≥ 4,5:1 y ≥ 3:1 en trazos e iconos esenciales; sin líneas muy finas. **Medido** (`critico.py --textos cajas.json`, con las cajas de texto en píxeles), no a ojo | Estándar (WCAG 1.4.3/1.4.11) |
| El color nunca es el único canal: etiqueta, forma o patrón; verde/rojo sólo con otra marca; nada de rojo sobre negro | Estándar (WCAG 1.4.1) |
| Nada destella más de 3 veces por segundo (revisar bucles a pantalla completa) | Estándar (WCAG 2.3.1) |
| Subtítulos sincronizados en **pista aparte** (SRT/VTT o pista del MP4), ≤ 2 líneas, cortados por frases con sentido; no quemados en la imagen | Estándar (WCAG 1.2.2) |

## 2. Por perfil (sólo el que se pidió)

| Perfil | Qué cambiar en el video | Evidencia |
|---|---|---|
| Autismo | Anunciar lo que viene con frase literal + señal visual fija; ejemplo completo antes de pedir respuesta; metáfora siempre con su frase literal; sin sonidos sorpresa ni música; **color funcional y fijo** con leyenda que no cambia; ejemplos con los intereses de la persona si se conocen | Alta en apoyos visuales y previsibilidad (en habilidades, no en video académico); el resto opinión. «Sin animaciones» NO está respaldado ni descartado |
| TDAH | Señalar lo relevante; nada decorativo moviéndose mientras se explica un paso; tramos cortos; confirmar cada paso; no basar la atención en la novedad | Media a baja |
| Dislexia | Narrar todo texto en pantalla; poco texto; sans serif clara; evitar fondo blanco puro; **no** fuentes «para dislexia» ni filtros de color | Alta para narrar; mixta para la fuente |
| Ansiedad | Anunciar lo que sigue; si se muestra tiempo, indicador visual no numérico | Media-baja |
| Discapacidad intelectual / procesamiento lento | Voz calmada, frases cortas, la misma palabra para lo mismo, repetir lo importante, pausas, sin porcentajes ni números grandes innecesarios | Opinión (guías de consenso) |
| Sordera / hipoacusia | Subtítulos como en DUA base, con quién habla y sonidos necesarios; respiro tras cada cambio de imagen (están leyendo); señalar con claridad qué se explica | Estándar y baja |
| Baja visión / ceguera | Descripción integrada en la voz; contraste alto; texto grande en lo central | Estándar |
| Daltonismo | Color con etiqueta o forma; nombrar el color en la voz cuando importe; colores con significado que difieran también en luminosidad | Estándar |
| Fotosensibilidad / vestibular | Sin destellos; versión con movimiento reducido: cortes o fundidos en vez de zoom, paneos y giros | Estándar y opinión |

**Vacíos sin evidencia** (color, movimiento y ritmo concretos para autismo y TDAH; tamaño mínimo de letra; volumen;
velocidad de subtítulos en español): se resuelven con opciones y probando con la persona, no con una cifra inventada.

## 3. Contradicciones: con parámetros, no con muchas versiones

- **Paleta** como parámetro del video: **calma** (pocos colores) o **con más color**, con la misma leyenda fija en las
  dos. En Manim: un diccionario de paleta arriba de `escena.py`. Para probar con una persona, dos renders de un minuto;
  para producción, el que elija.
- **Movimiento** en tres niveles: completo, reducido (en `motor_manim`: `RESPIRA = False`, cortes o fundidos en vez de
  zoom y paneos) y estático.
- **Subtítulos** activables (pista aparte), encendidos por omisión.
- **Ritmo**: narración escrita a ritmo cómodo; el control de velocidad lo da el reproductor del teléfono.
- Música: ninguna por omisión.

## 4. Lista de verificación (un video con adecuación no se entrega sin pasarla)

1. ¿Una idea principal por tramo y un orden visible?
2. ¿Los cambios se anuncian antes, con frase literal y una señal visual?
3. ¿Hay un ejemplo completo antes de pedir una respuesta?
4. ¿Se puede pausar, y el retorno no lo decide un cronómetro?
5. ¿Sin música, voces simultáneas ni sonidos sorpresa?
6. ¿Las metáforas llevan su frase literal?
7. ¿Se entiende sin depender del color?
8. ¿Contraste medido: 4,5:1 en texto y 3:1 en trazos?
9. ¿Sin destellos de más de 3 por segundo?
10. ¿La voz describe lo que se dibuja?
11. ¿No se atribuye un diagnóstico ni se generaliza a todo un perfil?

El `brief.md` del video anota: qué nivel se pidió (DUA base o perfil), qué parámetros se usaron (paleta, movimiento,
subtítulos), qué reglas se aplicaron con su evidencia y el resultado de la lista.

## 5. Probar con la persona

Un fragmento de un minuto en las dos paletas; preguntarle a ella qué le sirve y anotarlo como **su** preferencia.

## 6. Si el video es para una plataforma de cursos

Entregar además: capítulos autocontenidos de 1–2 min (uno por concepto, cada uno con estado inicial limpio), las
fuentes del proyecto, la narración con sus tiempos, los subtítulos en archivo aparte (WebVTT o SRT), la leyenda de
colores y una ficha por capítulo (concepto, nivel, duración, adecuaciones que cubre, reparto aproximado de canales).
