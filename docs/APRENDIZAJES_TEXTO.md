# Aprendizajes — transcripción

**HALCONES ESTELARES · ZX Spectrum 48K · © 2026 Tony C. Ware**

> Transcripción textual del documento aprobado. Las imágenes auténticas y la maquetación pertenecen al PDF ilustrado del paquete maestro, no a este archivo de texto.



---

### Página 1 de 5


ANEXO TÉCNICO



Qué merece conservarse
HALCONES ESTELARES como banco de aprendizaje para GRIT CLAYMORE




      Esta memoria no supone ninguna modificación de GRIT CLAYMORE. Reúne
      ideas que deben evaluarse frente a su motor, su mapa de memoria y sus
      pruebas. La única aplicación correcta es comparativa: nunca pegar rutinas de
      un juego en otro sin reconstruir sus dependencias ni su estado de máquina.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                  01


---

### Página 2 de 5


01 / MÁQUINA DE ESTADOS



Un estado final inequívoco
No ejecutar IA hostil después de la última vida




      En HALCONES, el guardia player_lives==0 de combat_tick evita wave_update,
      bullet_update, enemy_bullet_update, shield_collisions, ship_hit_collisions y
      player_fire. Continúan el render, la explosión del jugador y el reloj IM2. En GRIT
      habría que localizar los equivalentes de estos subsistemas y comprobar si ya
      existe una separación comparable entre combate, muerte y fin de partida.




      Criterio de aceptación propuesto: sin entradas de teclado, marcador en cero, tres
      muertes consecutivas, pantalla de fin de partida persistente, retorno al menú y
      nueva partida. Añadir casos con puntuación, con proyectiles activos, al morir junto a
      bordes de pantalla y en plena transición entre oleadas.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                           02


---

### Página 3 de 5


02 / VALIDACIÓN



Límites de una prueba parcial
Simulador Z80 frente a emulador completo




      COMPROBACIONES REUTILIZABLES
      •
          Probar secuencias completas en el emulador real; no solo saltos a rutinas aisladas.
      •
          Instrumentar SP, I, IM2, dirección de retorno, guardas de RAM y escritura fuera de
          zonas válidas.
      •
          Mantener una versión idéntica del TAP para comparar los resultados de pruebas
          diferentes.
      •
          Registrar exactamente qué condiciones provocan el fallo y cuáles no (000000
          frente a 000010).
      •
          Guardar vídeos o capturas de Fuse asociados a una compilación y un SHA
          concretos.




      Una hipótesis de corrupción de pila o IM2 puede ser razonable, pero no debe
      convertirse en conclusión sin la instrucción o escritura culpable capturada.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                             03


---

### Página 4 de 5


03 / GRÁFICOS



Pantalla y recursos
Reutilizar el método, no los bytes




      El pipeline útil para GRIT es la extracción trazable de sprites y fotogramas de los
      assets del programa. Las ampliaciones para documentación se hacen por vecino
      más cercano, sin inventar siluetas ni reorganizar imágenes en falsas capturas. En
      paralelo se conserva un SHA-256 del TAP final y se verifica que el banco
      recompila exactamente el mismo archivo.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                         04


---

### Página 5 de 5


04 / PLAN DE TRANSFERENCIA



Una futura comparación con GRIT
Decisiones para otra sesión, no para esta edición




     ORDEN SEGURO
     •
         1. Auditar cómo maneja GRIT sus estados de vida, muerte, pausa y fin de partida.
     •
         2. Revisar sus vectores de interrupción, reservas de pila, buffers y rutinas de
         repintado.
     •
         3. Añadir tests de cero puntos y varias partidas consecutivas, incluso si hoy no hay
         fallo.
     •
         4. Adaptar únicamente ideas verificadas que realmente hagan falta.
     •
         5. Probar en el emulador completo y medir los efectos sobre sonido, tiempos y
         gráficos.
     •
         6. Comparar hashes y conservar una copia estable anterior a cualquier modificación.




     GRIT CLAYMORE queda intacto. El siguiente paso será una auditoría separada; GitHub
     sigue reservado para una conversación posterior.




HALCONES ESTELARES · TONY C. WARE · ZX SPECTRUM 48K                                             05