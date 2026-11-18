#!/usr/bin/env python3
"""ZX Spectrum HUD V0.2: source-faithful ESF mark, native 8x8 ink-safe layout.

All 64x192 HUD pixels and 192 attributes are regenerated from:
 - GRIT CLAYMORE original native HUD reference (labels, score, life icons, power meter)
 - The user's ESF_ORIGINAL_USUARIO.jpg (monochrome emblem, NOT a generated mockup).
Only one INK color is allowed per 8x8 character cell; conflicts fail the build.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from collections import defaultdict
R=Path(__file__).resolve().parents[1]
A=R/'assets'; B=R/'build'; B.mkdir(exist_ok=True)
orig=Image.open(A/'HUD_GRIT_REFERENCIA.png').convert('RGB').resize((64,192),Image.Resampling.NEAREST)
ESF=Image.open(A/'ESF_ORIGINAL_USUARIO.jpg').convert('L')
im=Image.new('RGB',(64,192),(0,0,0)); d=ImageDraw.Draw(im)
BLACK=(0,0,0); Y=(255,255,0); C=(0,255,255); M=(255,0,0); W=(255,255,255); G=(0,255,0)
# Each panel's horizontal border is in its OWN 8-pixel row. Every border
# is in x=0..7 / x=56..63 exclusively, distinct from content x=8..55.
PANELS=((0,39,Y),(40,79,C),(80,111,Y),(112,191,M))
for y0,y1,col in PANELS:
    # Draw clipped, chamfered thin frames; no overlap into adjacent panel.
    d.line([(4,y0),(59,y0),(61,y0+2),(61,y1-2),(59,y1),(4,y1),(2,y1-2),(2,y0+2),(4,y0)], fill=col,width=1)
# Paste original GRIT motifs, exact native pixels, without touching any border row.
def paste_original(x0,y0,x1,y1,dst_y):
    art=orig.crop((x0,y0,x1,y1))
    im.paste(art,((64-art.width)//2,dst_y))
# No skulls and no old TANQUE: original letter shapes preserved exactly.
paste_original(14,24,49,31,9)  # PUNTOS, yellow
paste_original(9,41,54,48,24)  # six white digits
paste_original(17,64,46,71,49) # VIDAS, cyan
paste_original(12,80,52,88,64) # three original 8px life icons
# Tony C. Ware ZX 48K life signature: original GRIT 8x8 smiley, negative interior.
# Keep every outline pixel and all sprite geometry unchanged. Only invert
# yellow/black *inside* its closed circle: filled yellow face, black eyes/mouth.
# Faces remain at the original x=12,28,44, y=64..71 positions.
for face_left in (12,28,44):
    for face_y in range(1,7):
        yy=64+face_y
        xs=[x for x in range(face_left,face_left+8) if im.getpixel((x,yy))==Y]
        assert len(xs)>=2, ('smiley contour missing',face_left,face_y)
        first,last=min(xs),max(xs)
        for xx in range(first+1,last):
            color=im.getpixel((xx,yy))
            assert color in (Y,BLACK),('unexpected signature ink',xx,yy,color)
            im.putpixel((xx,yy), BLACK if color==Y else Y)
# Native six-letter ESCUDO (5x7 pixels per glyph + one space), centered at x=14.
# Same yellow INK as the old label, no attribute conflict with the green meter.
ESCUDO_FONT={
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'S':['01111','10000','10000','01110','00001','00001','11110'],
 'C':['01111','10000','10000','10000','10000','10000','01111'],
 'U':['10001','10001','10001','10001','10001','10001','01110'],
 'D':['11110','10001','10001','10001','10001','10001','11110'],
 'O':['01110','10001','10001','10001','10001','10001','01110'],
}
label='ESCUDO';letter_width=5;letter_gap=1
label_width=6*letter_width+5*letter_gap
label_x=(64-label_width)//2
assert label_x==14 and label_width==35
for i,letter in enumerate(label):
 for yy,row in enumerate(ESCUDO_FONT[letter]):
  for xx,bit in enumerate(row):
   if bit=='1':im.putpixel((label_x+i*6+xx,88+yy),Y)
paste_original(16,128,48,136,96) # original green meter
# Crop EXACT original black emblem and ESF lettering, no substitute/drawn emblem.
source_binary=ESF.point(lambda p:255 if p<150 else 0)
bbox=source_binary.getbbox()
assert bbox and bbox[2]>bbox[0] and bbox[3]>bbox[1]
resized=ESF.crop(bbox).resize((48,64),Image.Resampling.LANCZOS)
# Antialiased area reduction, binary threshold for true ULA pixels.
mono=resized.point(lambda p:255 if p<180 else 0)
for yy in range(64):
    for xx in range(48):
        if mono.getpixel((xx,yy)):
            im.putpixel((xx+8,yy+120),W)
# Emit actual native pixel layout. This is not the final evidence image:
# evidence must be created by executing the assembled TAP in the Z80 VM.
im.save(A/'HUD_NATIVO_NUEVO.png')
inks={BLACK:0,(0,0,255):1,(255,0,0):2,M:2,G:4,C:5,Y:6,W:7}
bitmap=[[0]*8 for _ in range(192)]
attrs=[]
for cy in range(24):
  for cx in range(8):
    found=set()
    for y in range(cy*8,cy*8+8):
      for x in range(cx*8,cx*8+8):
        col=im.getpixel((x,y))
        if col!=BLACK:found.add(col)
    assert len(found)<=1, f'Forbidden attribute clash at HUD cell ({cx},{cy}): {found}'
    selected=next(iter(found)) if found else W
    attrs.append(0x40|inks[selected])
    for y in range(cy*8,cy*8+8):
      b=0
      for x in range(cx*8,cx*8+8):
        if im.getpixel((x,y)) !=BLACK:b|=1<<(7-(x-cx*8))
      bitmap[y][cx]=b
# Source data for main Z80 runtime, 1536 bitmap +192 attributes.
scanline=[0x4000+((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2) for y in range(192)]
lines=['; HUD V0.2: GRIT PUNTOS/VIDAS, centered ESCUDO + direct ESF2 image pixel conversion; attr-safe.','scanline_table:']
for i in range(0,192,8):lines.append(' dw '+','.join(str(w) for w in scanline[i:i+8]))
lines+=['bitmask_table: db 128,64,32,16,8,4,2,1','hud_bitmap_data:']
flat=[v for row in bitmap for v in row]
for i in range(0,len(flat),24):lines.append(' db '+','.join(str(v) for v in flat[i:i+24]))
lines.append('hud_attr_data:')
for i in range(0,len(attrs),24):lines.append(' db '+','.join(str(v) for v in attrs[i:i+24]))
(B/'assets.asm').write_text('\n'.join(lines)+'\n')
# Manifest of precise source geometry for regression tests, no visual fakes.
import json
(B/'hud_manifest.json').write_text(json.dumps({'native_width':64,'native_height':192,'panels':[{'top':a,'bottom':b,'ink':inks[c]} for a,b,c in PANELS],'logo_source':str(A.name+'/ESF_ORIGINAL_USUARIO.jpg'),'logo_crop':bbox,'logo_dest':[8,120,48,64],'attributes':attrs,'bitmap':flat},indent=2))
print('PASS ESF graphic sourced from uploaded image,',sum(bool(v) for v in mono.getdata()),'native pixels.')
print('PASS 192 8x8 attribute cells, ZERO color collisions; HUD occupies 64x192.')
