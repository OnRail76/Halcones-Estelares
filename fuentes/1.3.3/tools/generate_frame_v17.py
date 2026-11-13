#!/usr/bin/env python3
"""Original 16px GRIT-style decorative frame, exact ZX bitmap+attribute data.
Never uses non-ZX color bitplanes. Every 8x8 cell has one INK and BLACK PAPER.
Called at build time; emitted Z80 tables are the ground-truth display source.
"""
from pathlib import Path
from PIL import Image
import json
R=Path(__file__).resolve().parents[1]; B=R/'build'; B.mkdir(exist_ok=True)
# 16x192, two pixel bytes per scanline, and 48 color attributes (2*24).
im=Image.new('1',(16,192),0);p=im.load()
def put(x,y):
    if 0<=x<16 and 0<=y<192:p[x,y]=1
for y in range(192):
    # Cyan inner rail plus bright-yellow backbone (one color PER cell).
    if 5<=y<187:
        put(5,y);put(6,y); put(15,y)
        if (y//8)%3==0:
            put(12+(y&3),y)
        elif (y//8)%3==1:
            put(9+(y&3),y)
        else:
            put(9+((7-y)&3),y)
    # trim along the outside of right rail
    if 5<=y<187 and y%8 in (0,7):put(13,y)
# Strengthen top/bottom terminating clasps; all within 16px reserved columns.
for top in (0,184):
    for dx in range(3,16):put(dx,top)
    for dx in range(2,16):put(dx,top+7)
    for yy in range(top+1,top+7):
        put(2,yy);put(15,yy)
        put(4 if yy<top+4 else 3,yy)
# 8px yellow mechanical collars roughly at thirds, magenta signal dots.
for top in (49,96,143):
    for y in range(top,top+7):
        put(1,y);put(7,y);put(8,y);put(15,y)
    for x in range(1,16):put(x,top);put(x,top+6)
    for y in range(top+2,top+5):
        put(3,y);put(5,y);put(10,y);put(12,y)
# Tiny mechanical hatches inside 8x8 cells.
for y in (24,32,40,64,72,80,112,120,128,160,168,176):
    for dy in (2,4):
        put(2,y+dy);put(11,y+dy)
# Each screen 8x8 cell gets exactly one constant INK: alt gold / turquoise / magenta.
# Colors: BLACK PAPER (0), BRIGHT bit 6, color ink 6 yellow/5 cyan/3 magenta.
attrs=[];bmap=[]
for by in range(24):
    for cx in range(2):
        if by in (0,23):ink=6
        elif by in (6,12,18) and cx==0:ink=2
        elif cx==0:ink=6
        else:ink=5
        attrs.append(0x40|ink)
for y in range(192):
    for cx in range(2):
        b=0
        for xx in range(8):
            if p[cx*8+xx,y]:b|=1<<(7-xx)
        bmap.append(b)
assert len(bmap)==384 and len(attrs)==48
# Left frame *bitmap* bytes are appended to the low sprite CODE block by the
# relocation builder; only its small attribute table remains in main program.
# This frees 384 main-code bytes for the approved RLE title without touching game logic.
out=['; HALCONES V2.8: left rail bitmap relocated to low CODE at $7BC0.',
     '; Label frame_attr_data remains in the main program; bytes unchanged.',
     'frame_attr_data:']
for a in range(0,len(attrs),24):out.append(' db '+','.join(map(str,attrs[a:a+24])))
(B/'frame_data_v17.asm').write_text('\n'.join(out)+'\n')
(B/'frame_manifest_v17.json').write_text(json.dumps(dict(width=16,height=192,bitmap=bmap,attributes=attrs,bitmap_bytes=len(bmap),attr_bytes=len(attrs)),indent=2))
# Python-only proof from the same exact 1bpp bytes and attributes, not image-generation.
palette=[(0,0,0),(0,0,192),(192,0,0),(192,0,192),(0,192,0),(0,192,192),(192,192,0),(192,192,192)]
bright=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
preview=Image.new('RGB',(16,192))
for y in range(192):
 for x in range(16):
    bit= bmap[y*2+(x//8)] & (1<<(7-(x&7)))
    att=attrs[(y//8)*2+x//8]
    pal=bright if att&64 else palette
    preview.putpixel((x,y),pal[(att&7) if bit else ((att>>3)&7)])
preview.resize((96,1152),Image.Resampling.NEAREST).save(B/'FRAME_REAL_NATIVE_V17.png')
print('FRAME: 384 bitmap bytes, 48 native attributes, two reserved character columns')
