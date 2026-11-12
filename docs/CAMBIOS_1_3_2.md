# HALCONES ESTELARES — Historial de evolución a la versión 1.3.2

**Plataforma:** ZX Spectrum 48K · **Autor y dirección creativa:** Tony C. Ware · **Código:** ensamblador Z80.

## 1.3.2 — Melodía de título
La melodía de presentación se reproduce una única vez cada vez que se llega al título, al arrancar o después de un GAME OVER. Una vez terminada, permanece en silencio hasta que el jugador inicia la partida. No se modifica el comportamiento de las músicas de otras pantallas.

## 1.3.1 — Beeper y brillo de insignia
El sonido se distribuye entre la interrupción intermedia y el tiempo libre del tick para reducir las pausas entre fragmentos, sin introducir deliberadamente más tiempo de trabajo por actualización. Efectos de disparo e impactos ajustados para el beeper troceado. La insignia ESF incorpora un barrido cian-amarillo-cian, sincronizado con acontecimientos y períodos de reposo.

## 1.3 — Mayor intensidad y nuevos fondos
La primera oleada utiliza **10 CROW en dos filas de cinco**; las siguientes oleadas mantienen seis enemigos. Hasta **2 disparos aliados** simultáneos, avanzando **12 píxeles por actualización**. Cuatro fondos celestes alternos (nebulosa, galaxia inclinada, planeta con anillos y cúmulo estelar). Ajustes del compositor para preservar el color y evitar repintados innecesarios; actualización del récord al terminar la partida.

## 1.2 — Presentación y sonido
Rediseño visual del HUD, comportamiento de la insignia, escenas de jefe con grietas, ojos, boca, derrumbe y Júpiter con luna móvil. Música y efectos, compresión de pantallas y mejoras de presentación.

## 1.1 — Ritmo y controles
Actualizaciones de juego reguladas a 25 Hz, composición optimizada, joystick Kempston detectado al iniciar, controles Sinclair, pausa, colisiones ajustadas a silueta, protección al reaparecer, marcador de 16 bits, vida extra y carteles de oleada.

## 1.0.1 — Reparación del retorno de CROW
Corrección de la coordenada Y fuera de rango en el retorno de exploradores y límites del compositor. La solución se basa en el fallo real identificado en desarrollo; se conservan defensas de fin de partida y memoria. La versión 1.0 publicada previamente permanece disponible en GitHub.

## Verificación de 1.3.2
- `python3 build.py` reconstruye un TAP **idéntico byte a byte** al aportado, desde fuentes y recursos sin necesidad de conservar archivos generados.
- SHA-256: `456d80834563321eb171b6f52e1f23d7c467b6f330b7b2d9e13eb9894605fe6b`.
- TAP validado a nivel de estructura y paridad XOR.
- En esta preparación han pasado las pruebas de disparo, formaciones/fondos, coherencia de atributos, sonido intermedio e insignia. La prueba más larga de retorno y melodía de título agotó el límite de ejecución en este entorno y queda **pendiente de completar aquí**, por lo que no se declara una certificación integral en Fuse ni hardware.
- Algunas pruebas históricas del banco citan rutas antiguas: se conservan como material de desarrollo, no como garantía de que todas pasan sin adaptación.
