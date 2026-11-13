# HALCONES ESTELARES V2.8.4 — Firma de vidas invertida

Base estable para revisión: **V2.8.3 candidata al hito**.

## Único cambio gráfico
El smiley **original** de Tony C. Ware que representa cada vida en ZX Spectrum 48K mantiene su forma, contorno, posiciones, ojos y sonrisa. Únicamente se invierten amarillo/negro **dentro del contorno** para mostrar una cara amarilla rellena, con ojos y sonrisa negros. No se ha diseñado otro icono.

Esta representación queda fijada como la firma gráfica de las vidas para futuros juegos Spectrum de Tony C. Ware.

El cambio afecta a los datos de 1) los iconos iniciales del HUD generados por tools/generate_assets.py y 2) los cuatro estados precalculados de vidas de build/shield_assets_v23.asm. Se cambian 108 bytes de datos de la imagen final ensamblada (36+72), **ninguna instrucción de motor**. Se han invertido 96 píxeles interiores en la previsualización del HUD (los contornos permanecen idénticos).

## Inalterado
- Pantalla de título original, halcón, pulso arcade y todos los rótulos.
- Modo de juego: movimiento, disparo y sonido de destrucción; 6 oleadas, primera fase moderada, jefe MOAI, avance de fases, GAME OVER.
- Escudo: activo 3 s, recarga 6 s en 8 segmentos.
- Kempston **NO** añadido todavía.
- Las 192 celdas de atributos del HUD son idénticas a V2.8.3.
- Tamaño de código 15683 B, hueco disponible antes de $C000: 701 B.

## Comprobaciones
- Prueba de firma: píxeles, zonas intactas, 4 fases de vidas en Z80 real, checksum del TAP.
- Batería de 10 pruebas automatizadas aprobadas, con Z80 parcial en las escenas aplicables.
- Dos compilaciones consecutivas idénticas, SHA256 TAP a0810e90f8ef058f5858a37826377b18033c9e7617f89a5c0ca27e8357c3cd1d.
- **No comprobado todavía en Fuse real**: es una candidata visual para que el usuario confirme la inversión y ausencia de incidencias.

IMPORTANTE: herramientas del banco se ejecutan con `python build.py` desde la raíz del banco, creando también `build/HALCONES_ESTELARES_V281.tap` (nombre interno histórico conservado para compatibilidad). El artefacto externo versionado es `HALCONES_V284_FIRMA_SMILEY.tap`.
