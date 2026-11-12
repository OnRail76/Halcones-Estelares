#!/usr/bin/env python3
"""Extract the user's Jupiter reference into a 56x56 native 1bpp bitmap.
Cyan/black crop is re-sampled; source unchanged and reproducible. No mockups.
"""
from pathlib import Path
from PIL import Image
import json
R=Path(__file__).resolve().parents[1]
src=Image.open(R/'assets/JUPITER_REFERENCIA_USUARIO.jpg').convert('RGB')
# Find the true cyan-pixel bounding box and use a square crop.
coords=[]
for y in range(src.height):
    for x in range(src.width):
        r,g,b=src.getpixel((x,y))
        if g>95 and b>110 and b>r*1.7:
            coords.append((x,y))
x0=min(x for x,y in coords); x1=max(x for x,y in coords)+1
y0=min(y for x,y in coords); y1=max(y for x,y in coords)+1
crop=src.crop((x0,y0,x1,y1))
mask=Image.new('L',crop.size)
for y in range(crop.height):
    for x in range(crop.width):
        r,g,b=crop.getpixel((x,y))
        mask.putpixel((x,y),255 if g>95 and b>110 and b>r*1.7 else 0)
W,H=56,56
occupancy=mask.resize((W,H),Image.Resampling.BOX)
out=Image.new('1',(W,H))
for y in range(H):
    for x in range(W):
        v=occupancy.getpixel((x,y))
        on=v>54 and (((x+y)&1)==0 or v>150)
        out.putpixel((x,y),1 if on else 0)
# V1.2: luz y sombra para que se lea como una esfera. Luz desde arriba a la
# izquierda: lado iluminado con las bandas mas llenas y borde nitido; lado de
# noche con el tramado cada vez mas abierto. Las bandas originales se conservan.
import math
LX,LY,LZ=-0.62,-0.55,0.56
lit=Image.new('1',(W,H))
for y in range(H):
    for x in range(W):
        nx=(x-27.5)/28.0;ny=(y-27.5)/28.0;rr=nx*nx+ny*ny
        on=out.getpixel((x,y))
        if rr>1.0:lit.putpixel((x,y),0);continue
        nz=math.sqrt(1-rr);sh=nx*LX+ny*LY+nz*LZ
        if sh>0.80 and (x+2*y)%4==0:on=1                  # brillo suave arriba a la izquierda
        if sh<0.05 and on and (x*3+y*5)%4!=0:on=0         # penumbra: se abre el tramado
        if sh<-0.30 and on and (x+y*3)%3!=0:on=0         # noche: casi vacio
        if 0.93<rr<=1.0 and sh>-0.15:on=1                # borde nitido por el lado iluminado
        lit.putpixel((x,y),on)
out=lit
bits=bytes(sum((0x80>>bit) for bit in range(8) if out.getpixel((bx*8+bit,y)))
           for y in range(H) for bx in range(W//8))
assert len(bits)==392
(R/'build/jupiter_bitmap_v20.bin').write_bytes(bits)
(R/'build/JUPITER_56x56_NATIVO.png').write_bytes(b'') if False else None
out.convert('RGB').resize((448,448),Image.Resampling.NEAREST).save(R/'build/JUPITER_56x56_AMPLIADO.png')
(R/'build/jupiter_manifest_v20.json').write_text(json.dumps({
  'source':'assets/JUPITER_REFERENCIA_USUARIO.jpg', 'source_box':[x0,y0,x1,y1],
  'native_size':[56,56], 'placement':[128,96], 'sprite_bytes':len(bits),
  'process':'cyan threshold + BOX occupancy + pixel checker/dither',
  'spectrum_color':'BRIGHT cyan attribute 0x45',
  'source_memory':'$F611',
},indent=2))
print('JUPITER native asset',len(bits),'bytes')
