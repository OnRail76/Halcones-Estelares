# HALCONES ESTELARES · Código fuente 1.4

**ZX Spectrum 48K · Z80 · © 2026 Tony C. Ware**

Esta es la única edición distribuida del banco de fuentes. Conserva los módulos Z80, las herramientas, los recursos que emplea el constructor y los tests de regresión. Ciertos nombres internos `v11`, `v12`, `v19`, `V281` se mantienen porque son referencias técnicas del constructor **1.4**: no representan ediciones publicadas.

## Construcción reproducible

Necesitas Python 3 y Pillow (`python3 -m pip install Pillow`). Desde esta carpeta ejecuta:

```bash
python3 build.py
sha256sum build/HALCONES_ESTELARES_V281.tap
cmp build/HALCONES_ESTELARES_V281.tap HALCONES_ESTELARES_1_4.tap
```

**SHA-256 del TAP oficial:** `7c595b9d7f61cba9145ce6a16e883ca0653750ac52a3cc2845066045967d1cad`.

La compilación se ha verificado fuera del directorio original, con `build/` vacío. El resultado es idéntico byte a byte al TAP proporcionado para publicar.

## Contenido

- `src/`: fuente Z80 que se ensambla para 1.4.
- `assets/`: entradas gráficas de esta compilación.
- `tools/`: generadores de recursos, ensamblador y escritor TAP.
- `tests/`: comprobaciones y regresiones del juego.
- `build.py`: construcción automática.
- `build/`: directorio de salida regenerable (no contiene ediciones antiguas).
- `HALCONES_ESTELARES_1_4.tap`: binario oficial de referencia.

Los TAP y los parches de anteriores versiones se han excluido intencionadamente. La memoria histórica resumida está dentro del libro del juego, no en ediciones jugables paralelas.

**Licencia:** MIT (código y herramientas); los gráficos y carátulas conservan los derechos reservados del autor, según `LICENCIA_GRAFICOS.md`.
