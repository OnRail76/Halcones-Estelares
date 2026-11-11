# Memoria creativa y técnica — transcripción

**HALCONES ESTELARES · ZX Spectrum 48K · © 2026 Tony C. Ware**

> Transcripción textual del documento aprobado. Las imágenes auténticas y la maquetación pertenecen al PDF ilustrado del paquete maestro, no a este archivo de texto.



---

### Página 1 de 15


HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K   01


---

### Página 2 de 15


01 / EL PUNTO DE PARTIDA



La historia del autor
1988, el futuro imaginado desde el arcade




     1988. El futuro.

     La recién formada Fuerza Espacial Europea, una facción secreta de los servicios
     de protección de Europa, detecta señales de radio y pulsos de energía que
     provienen de Europa, la luna de Júpiter.

     Tras perder el contacto con varias sondas enviadas para investigar, llegó el
     momento de estrenar el ESF-01, el caza espacial más poderoso del mundo.

     Nadie esperaba lo que se encontraron en el vacío sideral.

     Aves cósmicas con el único propósito de invadir, destruir y COMER.

     ¿Pero qué o quién las dirige?

     Sube a bordo del ESF-01, piloto. Es el momento de luchar.

     Sus gritos se oirán en el Cosmos.




  Relato de Tony C. Ware. El misterio de la invasión permanece abierto.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                    02


---

### Página 3 de 15


02 / DIRECCIÓN CREATIVA



La visión de Tony C. Ware
El arcade de 1984 como brújula




     Tony C. Ware no pidió un ejercicio técnico sin alma: pidió recuperar la
     magia inmediata de una recreativa de 1984. Su criterio ha sido constante
     durante todo el desarrollo: un juego de naves comprensible en segundos,
     pero con enemigos que tengan carácter, un ritmo reconocible y suficientes
     decisiones para querer volver a jugar.




     Su intervención fue práctica y continuada. Fijó el movimiento exclusivamente
     horizontal de la ESF-01, el disparo por pulsación y la función defensiva del
     escudo. Después se concentró en el ritmo de las oleadas, la lectura de los
     ataques, la expresividad del MOAI y el detalle gráfico del marcador. También fue
     quien identificó, reprodujo y confirmó la solución de la avería de cero puntos en
     Fuse.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                      03


---

### Página 4 de 15


03 / IDENTIDAD DEL JUEGO



La historia toma forma
Una ficción breve pero sugerente




      La Fuerza Espacial Europea, el año 1988 y las señales de Europa —la luna de
      Júpiter— forman una premisa deliberadamente sencilla: lo importante es despegar.
      La fórmula narrativa más eficaz aquí no es explicar cada amenaza, sino plantear
      una pregunta: «¿Pero qué o quién las dirige?». El MOAI MONOLITH concentra ese
      misterio en un rostro imposible, sin que el argumento afirme con certeza su
      identidad o sus intenciones.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                      04


---

### Página 5 de 15


04 / EVOLUCIÓN



Del prototipo al arcade
Las decisiones que fueron construyendo el juego




      V2.1
                               Referente temprano de estabilidad, antes del bloque de cambios
                               con CROW.




      V2.2
                               Llegada de CROW y nuevos procesos de muerte/reaparición.




      V2.4–V2.5
                               Formaciones, cazadores, kamikazes y estructura de circuitos.




      V2.6–V2.7
                               Reagrupación, presentación de MOAI, Júpiter y efectos
                               luminosos.




      V2.8.3–V2.8.4
                               Equilibrio del jefe, recarga de escudo y firma de vidas.




      V2.8.9
                               Pausa segura de lógica hostil al perder la última vida.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                             05


---

### Página 6 de 15


05 / ARQUITECTURA



La máquina y sus límites
Z80, memoria y presentación




      El juego trabaja sobre la pantalla bitmap y los atributos de color del ZX Spectrum 48K.
      El campo visible se separa del HUD de la derecha. El compositor utiliza planos de
      trabajo y atributos privados para reducir los defectos de repintado; una interrupción
      IM2 de 50 Hz sirve de reloj estable para escudo, explosiones y transiciones. El código
      se conserva en el banco reconstruible, con símbolos y pruebas de regresión.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                             06


---

### Página 7 de 15


06 / ASSETS



Identidad visual y nombres
El bestiario final no altera el código




        CROW
        Identificador histórico: CROW




        HARPY
        Identificador histórico: NEEDLE




        VULTURE
        Identificador histórico: BLADE




        OSPREY
        Identificador histórico: DRONE




        MOAI MONOLITH
        Identificador histórico: MOAI




      Cuatro sprites normales y un jefe; los nombres comerciales se definieron tras revisar los bytes y las
      imágenes auténticas.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                                           07


---

### Página 8 de 15


07 / AJUSTES DE JUGABILIDAD



El ritmo fue dirigido
Cómo se mejoró la sensación de juego




      El autor reclamó que la primera oleada respirase: formación arriba, descenso
      lento, disparos ocasionales y exploradores agresivos solo cuando toca. No quería
      que todo ocurriera demasiado deprisa. Las parejas de cazadores se hicieron más
      activas y los supervivientes quedaron autorizados a atacar por separado. Los
      kamikazes dejaron de abandonar la pantalla sin haber sido abatidos. El resultado
      es una progresión que exige aprender a dominar cada patrón.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                      08


---

### Página 9 de 15


08 / ARTE Y EQUILIBRIO



La firma y la justicia
Cada pequeño detalle fue una decisión consciente




      Tony C. Ware insistió en suavizar al MOAI para que el duelo fuera exigente sin
      resultar injusto. También decidió que el escudo se recargase en seis segundos y
      mantuviese los ocho segmentos de su barra. El smiley de las vidas se conservó
      exactamente en forma y expresión: solo se invirtieron sus colores para que quedase
      amarillo, con ojos y sonrisa negros. Esa cara se convirtió en firma gráfica para futuros
      Spectrum.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                              09


---

### Página 10 de 15


09 / REGRESIÓN



El fallo que casi lo impide
Cero puntos y tres vidas perdidas




      La avería aparecía al perder las tres vidas sin matar enemigos: en Fuse la
      secuencia de GAME OVER o el retorno al título podía bloquearse, quedar en
      negro o terminar con un puntero de pila anómalo. Con 10, 20 o 30 puntos no
      sucedía. Ese contraste fue observado por Tony C. Ware, que probó en más de un
      emulador, envió capturas del depurador y grabaciones y corrigió varias hipótesis
      equivocadas.




      La puntuación 000000 también implica que el jugador no ha destruido ninguno de los
      seis CROW. Por eso no se podía concluir que el cálculo de puntuación fallase al valer
      cero. Había una segunda variable: todos los enemigos podían seguir ejecutando su
      lógica mientras el jugador ya no tenía vidas. La relación causal exacta de la corrupción
      original no quedó demostrada a nivel de una instrucción Z80.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                              10


---

### Página 11 de 15


10 / INVESTIGACIÓN



Experimentos y descartes
La diferencia entre una hipótesis y una solución




      LO QUE SE COMPROBÓ
      •
          Pruebas parciales con tres muertes: el simulador alcanzaba GAME OVER, pero no
          reproducía el fallo real.
      •
          Parches del marcador y del retorno al título: no resolvieron el problema.
      •
          Códigos de color de alarma y testigos en RAM: aportaron información, pero no
          aislaron la instrucción causante.
      •
          Comenzar internamente con diez puntos ocultos tampoco solucionó la avería.
      •
          La prueba decisiva detuvo IA, proyectiles, colisiones y disparo en cuanto las vidas
          llegaron a cero.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                             11


---

### Página 12 de 15


11 / CORRECCIÓN



La V2.8.9 aprobada
Terminar el combate cuando termina la partida




      El cambio en combat_tick consulta player_lives. Si el contador vale cero, salta por
      encima de wave_update, bullet_update, enemy_bullet_update, shield_collisions,
      ship_hit_collisions y player_fire. Continúan el compositor, la explosión, el HUD y el
      temporizador IM2. No se alteraron los puntos iniciales ni el arte. La solución es
      funcional y además define una transición de estado más coherente: si ya no hay
      piloto, el combate hostil debe detenerse.




      Conclusión acotada: la V2.8.9 superó la regresión reproducida por el autor. Eso no
      prueba cuál de las rutinas antiguas corrompía originalmente el estado del Spectrum;
      sí confirma que no ejecutarlas después de la última muerte evita el síntoma
      verificado.




  TAP SHA-256

  fca50d5b7b1b81bbfdf5141853a5a490 5568ce660d2d57824162bfe0c4c8e648




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                           12


---

### Página 13 de 15


12 / FUSE



La validación de verdad
El criterio de aceptación lo puso el autor




      Tony C. Ware dejó morir a la ESF-01 cuatro partidas consecutivas sin tocar
      ninguna tecla ni conseguir puntos. Las cuatro veces apareció GAME OVER y
      pudo regresar al título sin reiniciar el ordenador. Fue él quien confirmó el cambio
      de resultado frente a las versiones anteriores. Las simulaciones del banco apoyan
      la prueba, pero no sustituyen esa comprobación interactiva en un emulador
      completo.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                         13


---

### Página 14 de 15


13 / CRITERIO Y APRENDIZAJE



Opinión del desarrollo
Lo que dejó este trabajo




      Mi valoración técnica es que la calidad final de HALCONES ESTELARES procede
      menos de un truco aislado que de la dirección sostenida del proyecto. Tony C.
      Ware corrigió ritmos, rechazó alteraciones de identidad gráfica, insistió en la
      justicia del juego y no aceptó declarar el hito mientras subsistía un reinicio. Esa
      exigencia fue especialmente valiosa cuando las pruebas automáticas parecían
      tranquilizadoras y Fuse decía lo contrario.




      El aprendizaje central es metodológico: una regresión debe reproducir la partida
      real, incluidas las entradas que NO suceden (sin disparar, sin puntos), los últimos
      estados y el retorno a la siguiente partida. También hay una lección editorial: las
      portadas deben ser arte comercial libre, mientras que las pantallas y los sprites del
      atlas se extraen de la obra auténtica. La memoria puede explicar decisiones y límites;
      el manual tiene que hablar al jugador.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                            14


---

### Página 15 de 15


14 / CIERRE



Hito arcade completado
El juego y su historia quedan documentados




      La edición final conserva la ESF-01, las seis oleadas, el escudo, la firma de las vidas y
      el MOAI MONOLITH. Se entrega con el TAP validado y un banco capaz de
      reconstruirlo byte por byte. GitHub y la posible transferencia de soluciones a GRIT
      CLAYMORE se tratarán después, de manera independiente. El objetivo aquí era
      conservar una obra completa y dejar constancia de cómo se llegó hasta ella.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                               15