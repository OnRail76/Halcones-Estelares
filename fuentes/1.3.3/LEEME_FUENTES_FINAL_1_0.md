# HALCONES ESTELARES — Código fuente (edición final 1.0 y versiones 1.1, 1.2, 1.3, 1.3.1, 1.3.2 y 1.3.3)

**Autor y dirección:** Tony C. Ware · **Plataforma:** ZX Spectrum 48K · **Lenguaje:** Z80 ensamblador · **Año:** 2026.

Este paquete contiene el código y los recursos de la **versión 1.3.3 actual**, junto con el historial desde V2.8.9 / FINAL 1.0. La edición 1.3.3 se ha recompilado y verificado byte a byte. Las secciones históricas describen sus versiones correspondientes, no la versión vigente.

## VERSIÓN 1.3.3: sonido a golpes, 16 estrellas y sin fondos

Parte de la 1.3.2. El cambio exacto respecto a la 1.3.2 está en `CAMBIOS_V1_3_3.patch`.

### Sonido a golpes
- Medido en partida: las 32 estrellas gastaban un 11 % de la CPU y el sonido solo podía oírse un 22-25 % del tiempo, troceado. Por mucho que se le dé, entre el trozo de mitad de tick y el del final siempre hay ~20 ms de juego sin sonido: los efectos largos se oían cortados.
- Nuevo tipo de segmento **golpe** (bit 7 del modo: `0x80` tono, `0x81` ruido): en cada tick suena **una sola ráfaga de unos 5 ms** (`snd_burst_len`, 700 unidades de 26 T), casi siempre entera en el trozo de mitad de tick, y el resto del tick silencio. Cada tick es un golpe limpio y un efecto largo es una serie de golpes con ritmo.
- Disparo (chasquido + tiu), disparo enemigo (pip-pip), disparo e impactos del MOAI y explosión (estallido + cuatro golpes cada vez más graves) son ahora golpes. Escudo, vida extra, carteles y sirena siguen igual. El trozo de mitad de tick cuenta lo que de verdad toca (`snd_mid`).
- Medido: el 97 % de los ticks con golpe suenan en una o dos ráfagas de 5,6 ms (mediana); ticks de más de 2 fotogramas: 0-0,3 %.

### 16 estrellas
- 16 estrellas en vez de 32 (`star_n`/`star_half` en `src/main.asm`), elegidas de las 32 para no dejar huecos, con los mismos tres ritmos y moviéndose igual de suave. El tiempo que liberan queda para el sonido.

### Sin fondos lejanos
- Fuera la nebulosa, la galaxia, el planeta y el cúmulo (y `tools/v12_fondos.py`): compartían celdas de color con cuervos, balas y explosiones. La luna y Júpiter del MOAI siguen igual. Memoria baja libre: 890 bytes.

### Pruebas
- `tests/test_v13_galaga.py`: el cielo de las oleadas queda vacío en las fases 1 y 2, Júpiter sigue en el MOAI, y el disparo suena como 2-3 ráfagas de menos de 8 ms.
- Pasa toda la batería salvo los tres antiguos de siempre (`test_v282`, `test_v284` y el final de `test_v283`).
- Memoria: principal `8000..BF32` (205 bytes libres), baja `76E0..7C85` (890 libres).

**SHA-256 del TAP 1.3.3:** `0db551592d01900287f0dad4754b840589075fb50ae3e7405ea66dbf21266ddf` (`HALCONES_ESTELARES_1_3_3.tap`).

## VERSIÓN 1.3.2: melodía del título una sola vez

Parte de la 1.3.1. El cambio exacto respecto a la 1.3.1 está en `CAMBIOS_V1_3_2.patch`.

- La melodía del título suena **una vez** cada vez que se llega al título (al cargar y al volver tras el Game Over) y después silencio hasta pulsar fuego. Antes se repetía sin fin (`title_screen.asm`: punto de vuelta 0 en `music_start`). Las músicas de Game Over, récord y fase superada ya sonaban una sola vez.
- `tests/test_v13_galaga.py` añade `test_musica_titulo_una_vez`: suena al llegar, silencio desde el segundo 10 hasta el 25, y lo mismo al volver al título tras una partida.
- Batería completa: pasa todo salvo los tres antiguos de siempre (`test_v282`, `test_v284` y el final de `test_v283`).

**SHA-256 del TAP 1.3.2:** `456d80834563321eb171b6f52e1f23d7c467b6f330b7b2d9e13eb9894605fe6b` (`HALCONES_ESTELARES_1_3_2.tap`).

## VERSIÓN 1.3.1: sonido más seguido e insignia que brilla

Parte de la 1.3. El cambio exacto respecto a la 1.3 está en `CAMBIOS_V1_3_1.patch`.

### Sonido (A): dos trozos por tick
- En el 48K el altavoz lo mueve la CPU, así que el efecto solo puede sonar en el rato que sobra de cada tick: antes, todo al final, y el efecto se oía a ráfagas con huecos de hasta 26-35 ms.
- Ahora la espera cuenta ese rato libre (`snd_idle`, en unidades de 26 T) y, en la interrupción de mitad de tick, `snd_mid` toca 3/4 de lo que sobró en el tick anterior menos un margen (tope 10 ms, siempre menos de un fotograma). El final del tick sobra eso menos, así que el tiempo total de sonido es el mismo y el juego no va más lento.
- Medido con reloj de interrupciones real: el silencio más largo dentro de un tick con efecto baja de 26,5 ms a 19,8 ms de mediana y de 35 ms a 20 ms en el 10 % peor; ticks de más de 2 fotogramas: 0-0,5 % (como en la 1.3).
- La espera ya no usa `DI`/`HALT`: compara `tick_irqs` sin parar, y así ninguna interrupción se pierde cuando el trabajo acaba justo al cambiar de fotograma.

### Sonido (B): efectos rehechos para el beeper troceado
- Disparo, estallido, impacto en el MOAI (y el de cuando le queda poco) y disparo del MOAI empiezan con un golpe de ruido corto, que es lo que mejor se oye a trozos, y siguen con barridos más cortos. El trino del disparo enemigo, el escudo, la vida extra y los carteles siguen igual.

### Insignia ESF
- Una franja diagonal cian-amarillo-cian cruza la insignia de esquina a esquina en 0,6 s. Solo cambian atributos (pantalla y sombra), nunca píxeles.
- Brilla al empezar cada oleada, con la vida extra, cuando el escudo vuelve a estar listo y, si no pasa nada, cada 8 s (`badge_tick`, `badge_shine` en `src/v12_bajo.asm`).
- Para hacer sitio, las rutinas de los LEDs (`led_*`) pasan a la memoria baja.

### Pruebas
- `tests/test_v13_galaga.py` añade el trozo de sonido a mitad de tick y el brillo de la insignia.
- `mini_z80.py` simula la interrupción en la nueva espera; `test_v18_arcade` deja más pasos a la interrupción (puede tocar sonido).
- Pasa toda la batería salvo los tres antiguos de siempre (`test_v282`, `test_v284` y el final de `test_v283`).
- Memoria: principal `8000..BF6A` (149 bytes libres), baja `76E0..7EB5` (330 libres).

**SHA-256 del TAP 1.3.1:** `cb45c1889200fb89119093290373329f17b75a45ec43789683d976a3c110f96a` (`HALCONES_ESTELARES_1_3_1.tap`).

## VERSIÓN 1.3: disparo a lo Galaga, 10 cuervos y fondos de fase

Parte de la 1.2. El cambio exacto respecto a la 1.2 está en `CAMBIOS_V1_3.patch`.

### Disparo
- Como mucho **2 balas tuyas** en pantalla a la vez (antes 9). Al desaparecer una (impacto o borde) puedes volver a disparar al momento.
- Las balas van a **12 px por tick** (antes 8): cruzan la pantalla en ~1/2 s, así que acertar es rápido y fallar se paga, pero no se pierde el ritmo.
- Constantes en `src/main.asm`: `bullet_n`, `bullet_bytes`.

### Formación de cuervos
- La primera oleada de cada fase trae **10 cuervos en dos filas de 5** (antes 6). Las demás oleadas siguen con 6 enemigos; `enemy_count` dice cuántos recorre cada bucle, así que las oleadas de 6 no pagan por las 10 casillas.
- Para mantener los 25 ticks/s: el cuervo usa una caja de 2×2 celdas (antes 3×3), la imagen de trabajo copia una sola caja que cubre la huella vieja y la nueva, y un enemigo que no se ha movido ni cambiado de aleteo no se vuelve a copiar.
- Rendimiento medido (emulador completo, partida con bot): entre el 0,4 % y el 4 % de los ticks pasan de 2 fotogramas, en los momentos de más explosiones; el resto va a 25/s.

### Fondos lejanos
- Cada fase tiene su fondo en blanco tramado en la franja central (y=88..151), por debajo de las formaciones: **nebulosa**, **galaxia inclinada**, **planeta con anillo** y **cúmulo de estrellas**; después se repiten (`tools/v12_fondos.py` → `build/v12_fondos.asm`, rutinas `bg_*` en `src/v12_bajo.asm`).
- Van en el cielo inmóvil (`D800`), como las estrellas: no cuestan tiempo por tick ni tocan el color. Durante el MOAI se borran (el cielo es para el MOAI, Júpiter y la luna) y el de la fase siguiente se pinta en la pantalla de ¡MUY BIEN!.

### Correcciones
- El atajo «misma celda» al copiar los colores de un enemigo comparaba x,y en bruto; con la caja del cuervo desplazada podían quedar celdas rojas en pantalla. Ahora la huella vieja se copia siempre (`color_shadow_present`).
- El récord se guarda también al acabar la partida (`record_check`), no solo al redibujar los puntos.

### Pruebas
- Nueva: `tests/test_v13_galaga.py` (2 balas a 12 px, 10 cuervos / 6 enemigos, fondo distinto por fase y borrado con el MOAI, pantalla y sombra de color iguales tras cada tick).
- Adaptadas a 10 cuervos y 2 balas: `boot_v15.py`, `test_v11_justicia`, `test_v12_remozado`, `test_v18_arcade`, `test_v26`, `test_v27_led_jupiter`.
- Pasan todas las demás, más `test_101` a las tres velocidades. Siguen fallando, como siempre, `test_v282`, `test_v284` y el final de `test_v283` (rutas `/mnt/data` antiguas).
- Memoria: principal `8000..BF76` (137 bytes libres), baja `76E0..7D88` (631 libres), extras `F401..FD8D` (107 libres).

**SHA-256 del TAP 1.3:** `2dd9b9f442544e8a792db3b747c946fc452404ecdfa0f3d597a445ce4adf36d7` (`HALCONES_ESTELARES_1_3.tap`).

## VERSIÓN 1.2: remozado gráfico completo y sonido

Parte de la 1.1. La jugabilidad es la misma (25 ticks/s, controles, justicia); cambia todo lo que se ve y se oye. El cambio exacto respecto a la 1.1 está en `CAMBIOS_V1_2.patch`.

### Título
- Halcón nuevo (`tools/v12_hawk.py`): alas desplegadas con coberteras blancas y remeras doradas, ceja fiera, pico ganchudo amarillo sobre la cara cian, cola blanca y garras. Los colores cambian justo en los bordes de las celdas 8×8.
- Letras HALCONES ESTELARES con degradado metálico (amarillo con filo rojo); el destello blanco de siempre sigue.
- Estrellas que titilan, controles nuevos (O-P/6-7, A/8, SPACE/0, H, Kempston), RÉCORD de la sesión y PULSA FUEGO parpadeando.

### Juego
- Enemigos nuevos con dos aleteos: cuervo (rojo), cazador (amarillo) y halcón (cian); cuervos pequeños de la primera oleada redibujados.
- Explosión en tres tiempos (las fases desplazadas se generan al arrancar en `$5B00`).
- Disparo enemigo en rombo magenta oscuro, distinto del tuyo; llama de motores que parpadea.
- LEDs del marco con información: barrido verde con el escudo listo, rojo si no; los tres parpadean si un enemigo baja cerca; fijos durante el MOAI.

### Marcadores
- Cabeceras en banda de color, cifras gruesas, RÉCORD debajo de los puntos.
- Caras: sonrientes; con la última vida, cara de apuro; las perdidas, círculo azul punteado.
- Escudo: 8 segmentos; LISTO (verde parpadeando), ACTIVO (cian) y CARGANDO con la barra en rojo, amarillo y verde.
- Panel de FASE con seis casillas de oleada, mini MOAI y OLEADA n.

### MOAI y Júpiter
- Grietas que aparecen al bajarle la vida a 12, 6 y 3.
- Los ojos se encienden justo antes de cada disparo y la boca se abre al disparar.
- Al derrotarlo se derrumba por bloques (3 por tick, en orden salteado) en vez de borrarse de golpe.
- Júpiter con luz desde arriba a la izquierda y lado de noche; una luna cruza por delante, 1 px cada 8 ticks.

### Pantallas
- ¡MUY BIEN!: «¡MOAI DERROTADO!», puntos, vidas y récord, con fanfarria.
- GAME OVER: récord y «¡NUEVO RÉCORD!» cuando se bate, con su melodía.

### Sonido
- Motor de efectos que suena en el tiempo que sobra de cada tick (`tick_wait`), así que no cuesta fotogramas: láser, zumbido enemigo, explosión, golpe de piedra del MOAI (más agudo cuando está a punto de caer), sirena de llegada, escudo, vida extra, cartel de oleada y pausa.
- Música en el título, en ¡MUY BIEN! y en GAME OVER (dos variantes).
- Muestra grabada del beeper: `HALCONES_1_2_SONIDO_MUESTRA.wav` (se entrega aparte).

### Memoria
- Pantallas y marcador comprimidos con LZ (`tools/lz.py`, descompresor `lz_unpack`).
- La explosión del ESF se queda con las fases pares (1.152 bytes libres en memoria baja para el código del MOAI y la luna, `src/v12_bajo.asm`).
- Bloque principal `8000..BEAD`; memoria baja hasta `7DD2`; extras `F401..FDAA`; variables en `F001..F0FF`; explosiones en `5B00..5F7F` (en tiempo de ejecución).

### Pruebas
- Nueva: `tests/test_v12_remozado.py` (título, marcador, LEDs, MOAI con grietas, boca, luna y derrumbe, sonido a 25 ticks/s, récord).
- Adaptadas por cambio intencionado: ojos y LEDs (`test_v26`, `test_v27_led_jupiter`).
- `test_v281_logo_bird_pulse.py` comprobaba byte a byte el título antiguo: se ha movido a `docs/legacy_regressions/`.
- Siguen pasando todas las demás, más `test_101` a las tres velocidades. Siguen fallando, como siempre, `test_v282`, `test_v284` y el final de `test_v283` (rutas `/mnt/data` antiguas).

**SHA-256 del TAP 1.2:** `014e470ca2462b798242041e7fbc46f5b4eccedeb1756858af38f48695c4934f` (`HALCONES_ESTELARES_1_2.tap`).

## VERSIÓN 1.1: jugabilidad, justicia y controles

Parte de la 1.0.1 (que ya corrige el fallo del CROW). Los gráficos, los sonidos, la pantalla de título, el MOAI y la estructura de las fases (CROW ×2, CAZADORES ×2, KAMIKAZES ×2, MOAI) no se han tocado. El cambio exacto está en `CAMBIOS_V1_1.patch`.

### Velocidad constante: 25 imágenes por segundo
- Antes el juego iba a unos 17 ticks por segundo con los CROW y bajaba a 12,5 con cazadores y kamikazes, porque cada vuelta del bucle tardaba 3 o 4 fotogramas. Como todo se mueve por tick, el juego entero se ralentizaba en las oleadas cargadas.
- **Compositor reescrito** (`arcade_compositor.asm`): los bucles de pintar, restaurar y presentar llevan el estado en registros, en vez de leer y escribir variables y `scanline_table` en cada línea. La siguiente línea de pantalla se calcula con la aritmética del Spectrum. Las balas tienen rutinas propias de 2×4 bytes, las estrellas bucles especializados y el color solo copia la huella antigua de un enemigo si no coincide con la nueva. La imagen resultante es idéntica byte a byte (comprobado tick a tick frente a la 1.0.1).
- **Ritmo fijo** (`tick_wait`): cada tick espera 2 interrupciones, así que el juego va siempre a 25 ticks por segundo, también en las escenas ligeras (el MOAI ya no se acelera). Solo el 2-3 % de los ticks de las oleadas más cargadas (6 enemigos, 9 disparos y escudo a la vez) tarda un fotograma más.

### Controles
- **Kempston automático:** si empiezas pulsando el fuego del joystick en el título, se juega con Kempston. Si empiezas con SPACE, con teclado, y el puerto del Kempston no se vuelve a leer. Sin interfaz (bus flotante) no se lee nunca.
- **Sinclair siempre activo:** 6 izquierda, 7 derecha, 0 fuego, 8 o 9 escudo.
- **Teclado:** O/P mover, SPACE disparar, A (o Q) escudo.
- **H = pausa**, con el borde azul. En pausa no corren ni el escudo, ni la invulnerabilidad, ni los reagrupamientos. Otra pulsación de H continúa.

### Más justo
- **Caja de impacto con la forma de la nave:** el morro estrecho arriba (x+9..x+14) y las alas debajo (x+3..x+20). Ya no matan los disparos que pasan junto a la punta de un ala ni los choques en esquinas vacías (enemigo x+2..x+13).
- **Ningún disparo enemigo nace a menos de 43 px del morro**, ni de los cuervos, ni de los cazadores en picado, ni de los kamikazes: siempre hay tiempo para esquivarlo.
- **Reaparición limpia:** al volver la nave desaparecen los disparos enemigos que quedaban en el aire y hay 2 s de invulnerabilidad parpadeando (antes 1 s).
- **Cadencia de disparo en tiempo real** (ticks de 25/s, antes máscaras de `frame_index` que dependían de la velocidad de cada escena), ojos del MOAI siempre alternos y ráfagas de los cazadores cada 1,28 s:

| Ticks entre disparos | CROW | Cazadores | Kamikazes | MOAI |
|---|---|---|---|---|
| Fase 01 | 80 | 64 | 32 | 48 |
| Fase 02 | 64 | 48 | 20 | 28 |
| Siguientes | −3 por cada MOAI | | | |

- El picado de los kamikazes sube 1 px cada **dos** MOAI derrotados (con 25 ticks por segundo, 1 px por MOAI lo llevaba a 175 px/s; el tope es ahora 125).

### Oleadas
- **Cartel «OLEADA n»** (1..6) en amarillo durante 1,6 s antes de cada formación, también al empezar la partida y después de cada MOAI. La formación entra cuando acaba el cartel.

### Marcador
- **Corregido: el marcador volvía a 0 a los 2.560 puntos** (era un byte). Ahora es de 16 bits, con 5 cifras en el HUD y en el GAME OVER, hasta 99.990 puntos.
- **Vida extra cada 1.000 puntos**, hasta 3 vidas.

### Memoria
- Bloque principal: `8000..BDE8` (535 bytes libres).
- Rutinas frías (título, pausa, marcador, cartel): `7E20..7FEC`, a continuación de los sprites reubicados. `build.py` ensambla y enlaza los dos bloques.
- Variables nuevas en `F001..F0FF`, entre los testigos `F000` y `F100`.
- El cargador BASIC hace `CLEAR 24575`, para que la pila de la ROM no se pise al cargar hasta `7FFF`.

### Pruebas
- **Nuevas:** `tests/test_v11_controles.py` (teclado, Sinclair, Kempston con y sin interfaz, pausa, 25 ticks/s fijos) y `tests/test_v11_justicia.py` (silueta, disparos esquivables, reaparición, marcador de 16 bits y vida extra, carteles, cadencias).
- `test_101_crow_reagrupacion.py` sigue pasando a las tres velocidades.
- **Pruebas antiguas:** pasan las mismas que con la 1.0.1, adaptadas donde la regla cambió a propósito (cartel inicial, caja de choque, cadencia del MOAI, mandos leídos una vez por tick). El `mini_z80` recibe las interrupciones del tick y las instrucciones nuevas. Siguen fallando, como en la 1.0, `test_v282`, `test_v284` y el final de `test_v283`, porque buscan rutas `/mnt/data` de versiones antiguas.
- **Sin probar todavía en un Spectrum real ni en Fuse, Speccy o Spectaculator.** Hay que confirmar la fluidez con la contención real de memoria y el Kempston de cada emulador.

**SHA-256 del TAP 1.1:** `65b241a332023fc7443991dae611fc070ee68de7555afaa97daf489696b925bb` (`HALCONES_ESTELARES_1_1.tap`).

## FINAL 1.0.1: causa real del fallo del CROW, corregida

**El fallo.** En la primera pantalla, si te mataban tres veces sin moverte ni disparar (0 puntos), el Spectrum se reseteaba o se colgaba en Fuse, Speccy y Spectaculator. La V2.8.9 lo evitaba congelando a los enemigos tras perder la última vida, sin saber qué lo causaba.

**La causa.**
1. Tras un picado fallido, el CROW vuelve a la formación subiendo 3 píxeles por paso (`crow_scout_return`, en `src/gameplay.asm`).
2. La resta `sub 3` no comprobaba el acarreo. Con Y=0, 1 o 2, la Y daba la vuelta a 253..255.
3. El compositor solo admite `0 <= spr_y <= 192 - spr_height`. Con esa Y, leía la `scanline_table` más allá de sus 192 líneas y tomaba un dato cualquiera como dirección de pantalla.
4. El `ldi` de `sprite_restore` escribía en 0x848B, dentro del propio bucle de combate: `call $8635` pasaba a ser `call $1035`.
5. El programa saltaba a la ROM y llegaba el reset o el cuelgue.

Solo pasaba con 0 puntos porque con alguna baja el CROW que volvía ya no existía. Y dependía de la temporización (contención de memoria) porque la Y desde la que vuelve depende de cuántos fotogramas tarda cada vuelta del bucle.

**La corrección** (`CAMBIO_EXACTO_V1_0_1.patch`):
- `crow_scout_return`: si la subida se pasa del borde superior, el CROW aterriza en su sitio.
- `sprite_render` y `composite_setup` comprueban `spr_y + spr_height <= 192` y no pintan lo que no cabe: ningún error de coordenadas puede volver a escribir sobre el código.
- El guardia de la V2.8.9 se mantiene como decisión de presentación (enemigos congelados durante la muerte final), pero ya no es necesario para evitar el fallo.

**Verificación.** `tests/test_101_crow_reagrupacion.py` usa un emulador Z80 completo (`tests/emulador_completo/`, todas las instrucciones, IM2 a 50 Hz, teclado) y barre la velocidad de la CPU respecto al fotograma para cubrir la contención.
- **1.0 sin guardia:** se resetea (PC en 0x0480, con sprites pintados con Y>=192).
- **1.0.1, con y sin guardia:** llega a GAME OVER a todas las velocidades, sin ningún sprite fuera de pantalla.
- **Pruebas del banco:** dan el mismo resultado que con la 1.0 (8 pasan; las 3 que fallan lo hacen igual en la 1.0, por rutas de ficheros antiguas).

**SHA-256 del TAP 1.0.1:** `f7c97be1720b383c068e1b91fde58756ed9829eccbaa760c23b369daf23177f4` (`HALCONES_ESTELARES_FINAL_1_0_1.tap`; `build.py` lo genera con el nombre histórico `build/HALCONES_ESTELARES_V281.tap`).

**Pendiente:** confirmarlo en Fuse, Speccy y Spectaculator con la prueba de siempre (cuatro partidas seguidas sin tocar nada, con 0 puntos).

## Estructura actual de la v1.3.3

- `src/`, `assets/`, `tools/`, `build.py`: banco Z80 y generadores originales.
- `tests/`: pruebas vigentes (24 superadas en esta auditoría).
- `docs/legacy_regressions/`: pruebas anteriores que dependen de rutas de un banco ausente; no ejecutarlas como parte de la suite vigente.
- `docs/taps_historicos/`: TAP antiguos archivados (no corresponden a la release v1.3.3).
- `CAMBIOS_V1_3_3.patch`: cambio exacto respecto a v1.3.2.

## Compilación actual v1.3.3

```bash
python3 build.py
sha256sum build/HALCONES_ESTELARES_V281.tap
cmp build/HALCONES_ESTELARES_V281.tap HALCONES_ESTELARES_1_3_3.tap
```

El fichero en `build/` conserva por compatibilidad **el nombre histórico V281**, pero la compilación actual produce **v1.3.3**. SHA-256 esperado:

`0db551592d01900287f0dad4754b840589075fb50ae3e7405ea66dbf21266ddf`

La primera publicación 1.0 se conserva en GitHub; los SHA y TAP históricos se encuentran en `SHA256_TAP_FINAL.txt`.

## Licencia

Código fuente y herramientas: MIT asistida por IA en `LICENSE` y `LICENSE_ES.md`; derechos de gráficos, logotipos, carátulas y sprites en `LICENCIA_GRAFICOS.md`.
