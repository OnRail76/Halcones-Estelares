# HALCONES ESTELARES — Código fuente 1.3.2

**ZX Spectrum 48K · Z80 · © 2026 Tony C. Ware**

Este es el **banco fuente de la versión 1.3.2**, separado de los binarios y pruebas históricas anteriores. Se ha reconstruido desde los archivos `src/`, `assets/`, `tools/` y `build.py`, partiendo de `build/` vacío.

## Compilar

```bash
python3 build.py
```

Resultado (nombre de salida histórico del ensamblador): `build/HALCONES_ESTELARES_V281.tap`.

**SHA-256 esperado:** `456d80834563321eb171b6f52e1f23d7c467b6f330b7b2d9e13eb9894605fe6b`.

Puedes comprobarlo con:

```bash
sha256sum build/HALCONES_ESTELARES_V281.tap
```

## Estructura
- `src/`: código completo Z80.
- `assets/`: recursos originales necesarios para reconstruir el TAP.
- `tools/`: ensamblador y generadores de recursos.
- `tests/`: pruebas e intérpretes Z80 usados durante el desarrollo.
- `historial/`: parches históricos y README de versiones antiguas, **no son el juego actual**.
- `docs/`: pruebas antiguas separadas.
- `CAMBIOS_1_3_2.md`: resumen de la evolución.
- `build/`: salida generada por el script, excluida del repositorio salvo `.gitkeep`.

**Nota:** el antiguo nombre `V281` en `build/` es solo un nombre de archivo que se conserva por compatibilidad. El hash identifica inequívocamente 1.3.2.

## Derechos y créditos
- `LICENSE`: MIT (edición asistida por IA), en inglés.
- `LICENSE_ES.md`: traducción al castellano.
- `LICENCIA_GRAFICOS.md`: derechos reservados sobre el material artístico y el logotipo.

El código es reutilizable según MIT; las carátulas y los recursos artísticos no pasan por ello a ser de uso libre.
