# HALCONES ESTELARES — Código fuente v1.3.3

**ZX Spectrum 48K · 2026 · Tony C. Ware · Ensamblador Z80**

Esta es la versión **v1.3.3** del juego, NO la anterior v1.3.2 ni la versión experimental V2.5. El TAP oficial es `HALCONES_ESTELARES_1_3_3.tap`. Conservamos la denominación histórica `build/HALCONES_ESTELARES_V281.tap` porque `build.py` todavía utiliza ese nombre **para la compilación actual**; el fichero que produce es idéntico al TAP 1.3.3. No se ha modificado ninguna instrucción Z80 al preparar esta edición para GitHub.

## Argumento

**1988. El futuro.** La Fuerza Espacial Europea envía el **ESF-01** hacia Europa, la luna de Júpiter, tras la desaparición de sondas. Allí aguardan aves cósmicas decididas a invadir, destruir y **COMER**. El enemigo final es **MOAI MONOLITH**.

## Controles

| Entrada | Acción |
|---|---|
| O / P | Izquierda / derecha |
| ESPACIO | Disparar e iniciar con teclado |
| A o Q | Escudo |
| H | Pausa / reanudar |
| Sinclair 6 / 7 / 0 | Mover / disparar; 8 o 9: escudo |
| Kempston | Pulsar FIRE en el título para utilizar joystick |

Enemigos: **CROW, HARPY, VULTURE, OSPREY** y **MOAI MONOLITH**. Seis oleadas por fase antes del jefe; 10 CROW en la primera formación y 6 oponentes en las siguientes. Hasta 2 disparos propios simultáneos. La música del título suena una sola vez por entrada.

## Cambios de v1.3.3 respecto a v1.3.2

- Efectos beeper de disparo, proyectiles enemigos, impacto del MOAI y explosiones reestructurados en **golpes cortos** de unos 5 ms en vez de fragmentos largos interrumpidos.
- Campo de estrellas móviles reducido de **32 a 16**, conservando los distintos ritmos.
- Retirados los **cuatro fondos lejanos** introducidos en v1.3 (nebulosa, galaxia, planeta y cúmulo) para eliminar interferencias de color. **Júpiter y la luna del MOAI se mantienen**.
- Se conservan la jugabilidad, sprites originales, smileys de las vidas, carátulas oficiales y arreglos históricos.

Véase `RELEASE_NOTES_v1.3.3.md` y `LEEME_FUENTES_FINAL_1_0.md` para el historial técnico.

## Recompilación verificable

Requiere Python 3 y **Pillow** para generar los recursos: `python3 -m pip install Pillow`. Desde esta misma carpeta:

```bash
python3 build.py
sha256sum build/HALCONES_ESTELARES_V281.tap
cmp build/HALCONES_ESTELARES_V281.tap HALCONES_ESTELARES_1_3_3.tap
```

La suma SHA-256 debe ser exactamente:

`0db551592d01900287f0dad4754b840589075fb50ae3e7405ea66dbf21266ddf`

Las ocho secciones de la cinta TAP tienen paridad XOR correcta. La compilación fue repetida y resultó idéntica byte por byte.

## Pruebas

```bash
python3 -m pip install -r requirements-dev.txt
python3 build.py
python3 -m pytest -q
```

**24 pruebas vigentes superadas** en la auditoría de esta entrega. Tres pruebas antiguas (V2.8.2 / V2.8.3 / V2.8.4) exigían carpetas absolutas de un banco anterior y se han archivado sin alterarlas en `docs/legacy_regressions/`; no deben presentarse como errores actuales ni como pruebas superadas. Estas verificaciones **no sustituyen una partida real en Fuse ni hardware**.

## Estructura

- `src/`: código Z80 (sin cambios respecto al ZIP recibido).
- `assets/`: recursos gráficos originales empleados por los generadores.
- `tools/`: ensamblador, conversores y generadores.
- `build.py`: construcción completa.
- `build/`: datos generados de apoyo y TAP de salida de nombre histórico.
- `tests/`: 24 pruebas vigentes.
- `docs/taps_historicos/`: copias anteriores **no destinadas a esta release**.
- `CAMBIOS_*.patch`: parches auténticos de evolución; el v1.3.3 tiene su parche independiente.

## Derechos y créditos

Autor y dirección creativa: **Tony C. Ware**, 2026. Asistencia IA: **OpenAI GPT y Anthropic Claude**. Código y herramientas bajo licencia **MIT asistida por IA**, con textos en `LICENSE` y `LICENSE_ES.md`. Los gráficos, ilustraciones, logotipos, carátulas y recursos visuales originales **no** se publican bajo MIT: `LICENCIA_GRAFICOS.md`.

La **única release final v1.3.3** reúne el manual y el atlas actualizados, la [carátula oficial original](https://github.com/OnRail76/Halcones-Estelares/releases/download/v1.3.3/HALCONES_ESTELARES_CARATULA_OFICIAL.png) y las cuatro alternativas aprobadas. No se conservan ni redistribuyen PDF y documentos obsoletos. La portada oficial no se ha redibujado ni reemplazado.
