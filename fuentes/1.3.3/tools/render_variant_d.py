#!/usr/bin/env python3
"""Asset viewer built EXCLUSIVELY from the same byte/attribute manifest as Z80."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
M=json.loads((R/'assets/sprites/sprite_manifest.json').read_text())
COL=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
FONT_PATH='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
try:fnt=ImageFont.truetype(FONT_PATH,18)
except OSError:fnt=ImageFont.load_default()

def asset(name):
 s=M[name];w,h=s['width'],s['height'];out=Image.new('RGB',(w,h),'black')
 for y in range(h):
  for x in range(w):
   bit=s['pixel_bytes'][y*(w//8)+(x//8)] & (128>>(x&7))
   if bit:out.putpixel((x,y),COL[s['ink'][y//8][x//8]])
 return out

canvas=Image.new('RGB',(860,420),(5,8,16));d=ImageDraw.Draw(canvas)
for name,x,y,scale in [('esf_interceptor',35,62,11),('enemy_heavy',455,62,10)]:
 im=asset(name);w,h=im.size
 canvas.paste(im.resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,y))
 d.text((x,22),f'{name.upper()}  {w}x{h}',font=fnt,fill=(230,240,250))
 d.text((x,y+h*scale+10),f'PIXEL DATOS Z80  /  x{scale}',font=fnt,fill=(160,195,215))
canvas.save(R/'build/VARIANTE_D_DATOS_NATIVOS.png')
asset('esf_interceptor').save(R/'build/ESF_D_24x24.png')
asset('enemy_heavy').save(R/'build/HEAVY_D_32x24.png')
print('PREVIEW: real 1bpp sprite data with authentic 8x8 cell attributes (NOT a game screenshot)')
