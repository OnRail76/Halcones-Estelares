# HALCONES ESTELARES V2.5 — Afinado de la segunda y tercera oleada

**Versión experimental, ZX Spectrum 48K.** Derivada de una copia íntegra de V2.4; **ni el TAP ni el banco V2.4 han sido alterados**. Todos los cambios de esta versión están en `src/gameplay.asm`, más los nuevos tests. Se conserva la estructura: CROW x2 → CAZADORES x2 → KAMIKAZES x2 → MOAI → pantalla ¡MUY BIEN! tres segundos → siguiente fase.

## Segunda oleada (cazadores)

- Vaivén horizontal **ligeramente más rápido**: fase de oscilación original + una posición extra cada dieciséis actualizaciones (aproximadamente **12,5 %** más de avance por la tabla, no un 12,5 % garantizado de velocidad en pantalla).
- Ataques más frecuentes: en vez de una única oportunidad cada 128 actualizaciones, la primera incursión espera 48 actualizaciones tras iniciar formación; luego, al regresar/morir una pareja, la próxima maniobra puede empezar tras **16 actualizaciones**.
- Si queda una pareja válida en cualquiera de las dos filas, **dos pájaros atacan en paralelo**, disparando a la posición capturada del ESF-01 al comenzar su descenso y sin seguir sus posteriores movimientos.
- Si **no hay ninguna pareja completa**, **un solo superviviente, en cualquiera de los seis registros**, puede atacar y disparar de forma independiente. Después de regresar espera 12 actualizaciones para la siguiente tentativa. No se revive ningún enemigo destruido.
- Mismo límite de **tres proyectiles enemigos simultáneos**; mismo compositor y tamaño de registros.

## Tercera oleada (kamikazes)

- Se reduce suavemente su velocidad: **1 píxel menos cada cuatro actualizaciones** (aprox. de 3 px a 2,75 px por actualización en la primera fase; el incremento por fase se mantiene, hasta el tope ya existente).
- Al alcanzar la parte inferior **no desaparecen tras dos pasadas**: regresan desde la parte superior y continúan atacando hasta ser destruidos por los disparos o por el escudo. Sus reapariciones conservan el escalonamiento de entrada.
- **La oleada solo termina cuando los seis enemigos hayan sido abatidos**, y sus explosiones hayan concluido. La regla se aplica tanto a KAMIKAZES I como a KAMIKAZES II. Solo entonces se abre el MOAI.
- Tras cada MOAI la velocidad de ataque continúa incrementándose según `wave_cycle`, con tope cuatro, como en versiones anteriores.

## No tocado

CROW, escudo parabrisas, explosiones, sonidos, atributos, color estable, MOAI/Júpiter, pantalla de fase, GAME OVER de 3 segundos, movimiento horizontal, disparo por pulsación. **No hay cambios gráficos ni de sonido en esta V2.5.**

## Validaciones

Ejecutadas con el intérprete Z80 parcial del banco (no equivale a probar Fuse):

```bash
python3 build.py
PYTHONPATH=tests:. python3 tests/test_v25_behaviour.py
PYTHONPATH=tests:. python3 tests/test_v25_full_phase.py
PYTHONPATH=tests:. python3 tests/test_v24_gameover.py
PYTHONPATH=tests:. python3 tests/test_v18_arcade.py
PYTHONPATH=tests:. python3 tests/test_v16_color_stability.py
```

`test_v25_behaviour.py` comprueba un kamikaze vivo tras múltiples reentradas, terminación solo tras abatir el último, frecuencia de parejas y ataque individual desde el registro 6, congelación de objetivo y secuencia completa de las seis oleadas. `test_v25_full_phase.py` comprueba escenario de parejas y 150 interrupciones de pantalla ¡MUY BIEN!, vuelta a fase 02, centinelas y paridad de los ocho bloques del TAP.

**Dos tests heredados de versiones previas contienen expectativas incompatibles** (fin del ataque de pareja V2.4 exactamente tras 115 actualizaciones y paso de oleada de un solo ciclo en V2.3). No se deben utilizar sin actualizar sus aserciones. Están conservados, sin borrar evidencia.

## Rendimiento

Perfil sintético en la primera oleada (Crow) **idéntico a V2.4**: 146.386 T-states por actualización de media, 130 de 180 por encima del presupuesto teórico de 25 Hz (139.776 T-states), sin ISR ni contención ULA. La nueva lógica de cazadores y kamikazes requiere medir percepción real en Fuse antes de considerar cerrada la optimización.

## Compilación

`python3 build.py` desde la carpeta raíz. El paquete incluye el miniensamblador Z80 del banco y todas las imágenes/recursos necesarios. Código en `$8000..$BBDF` aprox. con compositor `$C000..$EFFF`, sprites `$6000..$7BBF`, IM2 y pila con sus centinelas. Se carga el `.tap` completo, no `starter.bin` por sí solo.
