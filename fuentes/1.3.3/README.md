# HALCONES ESTELARES — Fuentes definitivas v1.3.3

**ZX Spectrum 48K · Z80 · © 2026 Tony C. Ware**

Esta carpeta es el **único banco de código fuente válido**. Contiene los recursos, ensamblador, generadores y pruebas de la edición definitiva **1.3.3**. No se distribuyen ni mantienen versiones previas ni sus TAP.

## Contenido

- `src/`: código fuente Z80 que forma el juego 1.3.3.
- `assets/`: recursos necesarios para generar gráficos y datos durante la compilación.
- `tools/`: herramientas y ensamblador utilizados por `build.py`; ciertos nombres internos con números antiguos permanecen porque forman parte del proceso de compilación actual.
- `build.py`: construcción reproducible del TAP definitivo.
- `tests/`: pruebas de la edición actual, sin regresiones externas archivadas.
- `RELEASE_NOTES_v1.3.3.md`: características y cambios de la edición publicada.

## Compilación y comprobación

Requiere Python 3 y Pillow. Desde `fuentes/1.3.3/`:

```bash
python3 -m pip install Pillow pytest
python3 build.py
sha256sum build/HALCONES_ESTELARES_V281.tap
cmp build/HALCONES_ESTELARES_V281.tap HALCONES_ESTELARES_1_3_3.tap
python3 -m pytest -q
```

El nombre interno `HALCONES_ESTELARES_V281.tap` se conserva por compatibilidad con el constructor; **su contenido es la versión 1.3.3**, no otro juego.

**SHA-256 oficial:** `0db551592d01900287f0dad4754b840589075fb50ae3e7405ea66dbf21266ddf`.

La comprobación automática en GitHub Actions recompila el juego y compara byte a byte el resultado con el TAP publicado. No se ha cambiado el código del juego en esta limpieza.

## Derechos y créditos

Autor y dirección creativa: **Tony C. Ware**, 2026. Asistencia de desarrollo: OpenAI GPT y Anthropic Claude. Código y herramientas con licencia MIT asistida por IA. Las carátulas, sprites, logotipos y demás recursos gráficos conservan sus derechos según `LICENCIA_GRAFICOS.md`.

**Única release válida: [v1.3.3](https://github.com/OnRail76/Halcones-Estelares/releases/tag/v1.3.3).**
