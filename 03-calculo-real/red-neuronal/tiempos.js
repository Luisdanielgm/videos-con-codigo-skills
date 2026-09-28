window.TIEMPOS = {
 "total": 233.571,
 "orden": [
  "titulo",
  "real",
  "idea",
  "numeros",
  "neurona",
  "pesos",
  "suma",
  "activacion",
  "red",
  "intento",
  "error",
  "retro",
  "ajuste",
  "montana",
  "repetir",
  "resultado",
  "muestra",
  "cierre"
 ],
 "seg": {
  "titulo": {
   "inicio": 0.6,
   "dur": 6.478,
   "texto": "¿Cómo aprende una red neuronal? Vamos a verlo paso a paso, sin matemáticas difíciles."
  },
  "real": {
   "inicio": 7.778,
   "dur": 10.658,
   "texto": "Y esta vez, todo lo que vas a ver es de verdad: una red neuronal real, entrenada con dibujos reales de números, escritos a mano por personas."
  },
  "idea": {
   "inicio": 19.136,
   "dur": 13.096,
   "texto": "Una red neuronal es un programa que aprende con ejemplos. Igual que un niño aprende a reconocer los números viendo muchos, la red mira miles de dibujos hasta que aprende a distinguirlos."
  },
  "numeros": {
   "inicio": 32.932,
   "dur": 15.813,
   "texto": "Pero la computadora no ve un dibujo, ve números. Este siete lo escribió una persona. Cada cuadrito es un número del cero al dieciséis: más alto cuanto más oscuro. En total, sesenta y cuatro números."
  },
  "neurona": {
   "inicio": 49.445,
   "dur": 8.498,
   "texto": "La pieza básica de la red es la neurona. Una neurona recibe varios números. En este ejemplo, recibe tres."
  },
  "pesos": {
   "inicio": 58.644,
   "dur": 14.698,
   "texto": "Cada número llega por una conexión que tiene un peso. El peso es como una perilla de volumen: dice cuánto importa esa entrada. Un peso grande la hace sonar fuerte, y un peso negativo la resta."
  },
  "suma": {
   "inicio": 74.042,
   "dur": 16.37,
   "texto": "La neurona multiplica cada entrada por su peso. Por ejemplo, cero coma ocho por cero coma nueve da cero coma setenta y dos. Hace lo mismo con las otras dos, suma todo, y le agrega un pequeño ajuste. En total, cero coma noventa."
  },
  "activacion": {
   "inicio": 91.112,
   "dur": 15.604,
   "texto": "Después, la neurona decide cuánto encenderse, como un regulador de luz. Si la suma es alta, brilla más. Si es baja, brilla menos. Pero nunca pasa del cien por ciento. Aquí se enciende un setenta y uno por ciento."
  },
  "red": {
   "inicio": 107.416,
   "dur": 10.588,
   "texto": "Nuestra red real tiene sesenta y cuatro entradas, una por cuadrito, dos capas ocultas de doce neuronas, y diez salidas, una por cada dígito."
  },
  "intento": {
   "inicio": 118.704,
   "dur": 12.26,
   "texto": "Al principio, sus pesos son números al azar, así que no sabe nada. Le mostramos el siete, la red hace todas las cuentas, capa por capa, y responde: cuatro."
  },
  "error": {
   "inicio": 131.664,
   "dur": 13.653,
   "texto": "Era un siete. La neurona del siete debía encenderse al cien por ciento, y solo llegó al tres. La del cuatro debía quedar apagada, y se encendió al veinte. Esa diferencia es el error."
  },
  "retro": {
   "inicio": 146.017,
   "dur": 15.673,
   "texto": "Ahora el error viaja hacia atrás, desde la salida hasta la entrada, y calcula la culpa exacta de cada conexión. Las conexiones que más brillan son las que más contribuyeron a equivocarse. Esto es la retropropagación."
  },
  "ajuste": {
   "inicio": 162.391,
   "dur": 8.15,
   "texto": "Con esa culpa, cada peso se mueve un poquito en la dirección que reduce el error. Algunos suben y otros bajan."
  },
  "montana": {
   "inicio": 171.241,
   "dur": 16.161,
   "texto": "Tomemos una sola de esas conexiones. Esta curva es el error real de la red cuando cambiamos solo ese peso. El descenso de gradiente mira hacia dónde baja la curva y da un paso, y otro, y otro, hasta llegar al fondo del valle."
  },
  "repetir": {
   "inicio": 188.102,
   "dur": 13.514,
   "texto": "La red real hizo esto con cincuenta y siete mil ejemplos. Al principio acertaba el diez por ciento. Al final, acierta el noventa y cuatro por ciento de dibujos que nunca había visto."
  },
  "resultado": {
   "inicio": 202.316,
   "dur": 7.872,
   "texto": "Le mostramos el mismo siete, y ahora responde: siete, con un noventa y ocho por ciento de seguridad."
  },
  "muestra": {
   "inicio": 210.888,
   "dur": 8.429,
   "texto": "Y aquí hay otros dibujos que nunca vio. Casi todos los reconoce, aunque todavía se equivoca a veces, como una persona."
  },
  "cierre": {
   "inicio": 220.016,
   "dur": 11.355,
   "texto": "En resumen: adivinar, medir el error, repartir la culpa hacia atrás, ajustar un poquito, y repetir. Eso es aprender, para una red neuronal."
  }
 }
};
