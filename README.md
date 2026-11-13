<p align="center">
  <img src="media/caratula-oficial.jpg" width="520" alt="Carátula oficial de HALCONES ESTELARES — Tony C. Ware, ZX Spectrum 48K">
</p>

# HALCONES ESTELARES

**ZX Spectrum 48K · Código máquina Z80 · © 2026 Tony C. Ware**

**[DESCARGAR TAP v1.3.3](JUEGO/HALCONES_ESTELARES_1_3_3.tap)** · [Releases oficiales](https://github.com/OnRail76/Halcones-Estelares/releases) · [Código fuente Z80 v1.3.3](fuentes/1.3.3/README.md)

## 1988. El futuro

La **Fuerza Espacial Europea** envía al **ESF-01** rumbo a **Europa, luna de Júpiter**, tras la desaparición de varias sondas. En el vacío aguardan aves cósmicas cuyo propósito es **invadir, destruir y COMER**. ¿Quién las dirige? **¡Sus gritos se oirán en el Cosmos!**

## El juego

Arcade de seis oleadas por fase contra **CROW, HARPY, VULTURE y OSPREY**, antes del temible **MOAI MONOLITH**. Tres vidas, escudo, marcador y récord. Primera formación con **10 CROW**; el resto de formaciones emplean seis enemigos. Dos disparos propios simultáneos y dificultad progresiva.

**v1.3.3:** efectos beeper reorganizados en golpes cortos; **16 estrellas móviles**; retirados los fondos espaciales lejanos para reducir choques de atributos. Se conservan Júpiter y la luna del jefe. La música del título se reproduce **una vez** al entrar en la pantalla. [Historial de cambios](docs/CAMBIOS_1_3_3.md).

## Controles

| Entrada | Acción |
|---|---|
| O / P | Mover a izquierda / derecha |
| ESPACIO | Disparar e iniciar con teclado |
| A o Q | Escudo |
| H | Pausa |
| Sinclair 6 / 7 / 0 | Mover y disparar; 8/9 para escudo |
| Kempston | Iniciar desde el título con FIRE |

## Descargas

- [Releases oficiales](https://github.com/OnRail76/Halcones-Estelares/releases): ediciones ya publicadas. La v1.3.3 está disponible en el repositorio como [TAP](JUEGO/HALCONES_ESTELARES_1_3_3.tap) y [fuentes reproducibles](fuentes/1.3.3/README.md).
- [Fuentes de v1.3.3](fuentes/1.3.3/README.md) y [TAP original](JUEGO/HALCONES_ESTELARES_1_3_3.tap).
- [Release v1.3.2](https://github.com/OnRail76/Halcones-Estelares/releases/tag/v1.3.2): cinco **carátulas aprobadas**, oficial ESF-01 negra y PDF históricos de la edición 1.0. **No modificar las carátulas ni colocarles número de versión.**
- [Release v1.0](https://github.com/OnRail76/Halcones-Estelares/releases/tag/v1.0): primera edición y documentación visual original.

Los PDF históricos no representan todos los ajustes de v1.3.3; el historial de cambios sí.

## Compilación e integridad

`python3 fuentes/1.3.3/build.py` reconstruye el TAP **idéntico byte a byte**. Las ocho secciones de la cinta tienen paridad XOR correcta; **24 pruebas vigentes superadas**. Tres regresiones viejas con rutas de desarrollo absolutas están archivadas, fuera de la suite actual; no se afirma verificación en hardware físico.

**SHA-256 de v1.3.3:** `0db551592d01900287f0dad4754b840589075fb50ae3e7405ea66dbf21266ddf`

## Licencias y créditos

**Autor y dirección creativa: Tony C. Ware.** Asistencia IA: OpenAI GPT y Anthropic Claude. Código y herramientas: MIT asistida por IA ([inglés](LICENSE), [castellano](LICENSE_ES.md)). Gráficos, sprites, logos y carátulas: [derechos reservados](LICENCIA_GRAFICOS.md).

**¡Sus gritos se oirán en el Cosmos!**
