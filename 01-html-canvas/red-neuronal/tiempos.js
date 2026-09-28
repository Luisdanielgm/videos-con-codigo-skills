window.TIEMPOS = {
 "total": 242.275,
 "orden": [
  "titulo",
  "idea",
  "numeros",
  "neurona",
  "pesos",
  "suma",
  "activacion",
  "red",
  "partes",
  "intento",
  "error",
  "retro",
  "ajuste",
  "montana",
  "repetir",
  "resultado",
  "cierre"
 ],
 "seg": {
  "titulo": {
   "inicio": 0.6,
   "dur": 6.478,
   "texto": "¿Cómo aprende una red neuronal? Vamos a verlo paso a paso, sin matemáticas difíciles."
  },
  "idea": {
   "inicio": 7.778,
   "dur": 13.096,
   "texto": "Una red neuronal es un programa que aprende con ejemplos. Igual que un niño aprende a reconocer los números viendo muchos, la red mira miles de dibujos hasta que aprende a distinguirlos."
  },
  "numeros": {
   "inicio": 21.574,
   "dur": 14.977,
   "texto": "Pero hay un detalle: la computadora no ve un dibujo, ve números. Cada cuadrito de la imagen es un número: uno si está pintado, y cero si está vacío. Este siete son sesenta y cuatro números."
  },
  "neurona": {
   "inicio": 37.251,
   "dur": 8.498,
   "texto": "La pieza básica de la red es la neurona. Una neurona recibe varios números. En este ejemplo, recibe tres."
  },
  "pesos": {
   "inicio": 46.45,
   "dur": 14.698,
   "texto": "Cada número llega por una conexión que tiene un peso. El peso es como una perilla de volumen: dice cuánto importa esa entrada. Un peso grande la hace sonar fuerte, y un peso negativo la resta."
  },
  "suma": {
   "inicio": 61.848,
   "dur": 16.37,
   "texto": "La neurona multiplica cada entrada por su peso. Por ejemplo, cero coma ocho por cero coma nueve da cero coma setenta y dos. Hace lo mismo con las otras dos, suma todo, y le agrega un pequeño ajuste. En total, cero coma noventa."
  },
  "activacion": {
   "inicio": 78.918,
   "dur": 15.604,
   "texto": "Después, la neurona decide cuánto encenderse, como un regulador de luz. Si la suma es alta, brilla más. Si es baja, brilla menos. Pero nunca pasa del cien por ciento. Aquí se enciende un setenta y uno por ciento."
  },
  "red": {
   "inicio": 95.222,
   "dur": 11.076,
   "texto": "Una red neuronal es esto mismo, repetido muchas veces: neuronas organizadas en capas, donde cada capa le pasa sus resultados a la siguiente."
  },
  "partes": {
   "inicio": 106.998,
   "dur": 18.042,
   "texto": "A la izquierda entran los sesenta y cuatro números del dibujo, uno por neurona. En el medio hay capas ocultas, que buscan patrones. Y a la derecha hay diez neuronas, una por cada dígito, del cero al nueve. La que más se enciende es la respuesta de la red."
  },
  "intento": {
   "inicio": 125.74,
   "dur": 12.399,
   "texto": "Al principio, los pesos son números al azar, así que la red no sabe nada. Le mostramos el siete, la información pasa de capa en capa, y la red responde: tres."
  },
  "error": {
   "inicio": 138.839,
   "dur": 15.186,
   "texto": "Nosotros sabemos que era un siete. Así que medimos el error. La neurona del siete debía encenderse al cien por ciento, y solo llegó al dieciocho. La del tres debía quedar apagada, y se encendió al cuarenta y uno."
  },
  "retro": {
   "inicio": 154.725,
   "dur": 17.276,
   "texto": "Ahora viene la parte clave. El error viaja hacia atrás, desde la salida hasta la entrada. En el camino, cada conexión recibe su parte de culpa: cuánto contribuyó a la equivocación. A esto se le llama retropropagación."
  },
  "ajuste": {
   "inicio": 172.7,
   "dur": 10.24,
   "texto": "Con eso, cada peso se mueve un poquito en la dirección que reduce el error. Algunos suben y otros bajan. Solo un poquito, para no pasarse."
  },
  "montana": {
   "inicio": 183.64,
   "dur": 19.644,
   "texto": "¿Y cómo sabe hacia dónde moverse? Imagina que estás en una montaña, con los ojos vendados, y quieres bajar al valle. Tanteas el suelo con el pie y das un paso hacia donde baja. Paso a paso, llegas abajo. El valle es donde el error es más pequeño. Esto se llama descenso de gradiente."
  },
  "repetir": {
   "inicio": 203.984,
   "dur": 12.817,
   "texto": "Todo esto se repite con miles de dibujos distintos. Al principio, la red acierta muy poco. Pero con cada ejemplo ajusta sus pesos un poquito, y sus aciertos van subiendo."
  },
  "resultado": {
   "inicio": 217.502,
   "dur": 10.519,
   "texto": "Después de ver sesenta mil ejemplos, le mostramos el mismo siete, y ahora responde: siete, con un noventa y tres por ciento de seguridad."
  },
  "cierre": {
   "inicio": 228.72,
   "dur": 11.355,
   "texto": "En resumen: adivinar, medir el error, repartir la culpa hacia atrás, ajustar un poquito, y repetir. Eso es aprender, para una red neuronal."
  }
 }
};
