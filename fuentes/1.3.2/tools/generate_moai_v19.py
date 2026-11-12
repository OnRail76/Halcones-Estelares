#!/usr/bin/env python3
"""Create native monochrome Z80 bytes from the user's original MOAI image.
The source image is retained unmodified; this is a constrained 48x88 1bpp conversion,
with ZX Spectrum 8x8 eye attribute positions documented for eye animation.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json
R=Path(__file__).resolve().parents[1]
source=Image.open(R/'assets/MOAI_REFERENCIA_USUARIO.jpg').convert('L')
# Crop from visible content, leaving a narrow margin; do NOT redraw the source.
threshold=source.point(lambda v:255 if v>128 else 0)
bbox=threshold.getbbox()
assert bbox is not None and bbox[2]-bbox[0]>100
crop=threshold.crop(bbox)
# Height/width chosen to retain the original proportions closely at 1bpp.
W,H=48,88
small=crop.resize((W,H),Image.Resampling.NEAREST)
small.save(R/'build/MOAI_ORIGINAL_REDUCIDO_48x88.png')
# V2.7: Enlarge the two threatening red LED eyes ONLY inside their existing
# Spectrum BRIGHT RED attribute cells: x8..15 / x32..39, local y16..23.
# The 48x88 conversion retains the user's exact face as source; only these
# marked eye pixels are expanded. No third ink or FLASH, no colour clash.
for y, lo, hi in [
    (18,11,13),
    (19,10,14),
    (20,9,15),
    (21,9,15),
    (22,9,15),
    (23,10,14),
]:
    for x in range(lo,hi+1):
        small.putpixel((x,y),255)
        small.putpixel((W-1-x,y),255)
small.save(R/'build/MOAI_V27_OJOS_LED_48x88.png')
rows=[]
for y in range(H):
    for bx in range(W//8):
        rows.append(sum((0x80>>bit) for bit in range(8) if small.getpixel((bx*8+bit,y))>128))
out=['; MOAI DEL USUARIO: conversion binaria directa, 48x88, x=72 y=8.',
     '; Su estetica se conserva: no se genera ni se reinterpreta arte.',
     'boss_face_bitmap:']
for i in range(0,len(rows),24):out.append(' db '+','.join(str(x) for x in rows[i:i+24]))
(R/'build/moai_bitmap_v19.bin').write_bytes(bytes(rows))
(R/'build/moai_bitmap_v19.asm').write_text('\n'.join(out)+'\n')
(R/'build/moai_manifest_v19.json').write_text(json.dumps({'source':'assets/MOAI_REFERENCIA_USUARIO.jpg','bbox':bbox,'source_dimensions':source.size,'game_pixels':[72,8,W,H],'bytes':len(rows),'method':'original thresholded and nearest resized 1bpp; V2.7 adds two LED eye masks only inside existing red attribute cells'},indent=2))
print('MOAI user asset',bbox, '=>',W,H,len(rows),'bytes')
