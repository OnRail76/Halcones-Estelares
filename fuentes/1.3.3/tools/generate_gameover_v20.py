#!/usr/bin/env python3
"""Native ZX Spectrum 48K GAME OVER artwork, no ROM text and no mockup.
Shows PRESS SPACE only after a 150-interrupt lockout, by recolouring row 21.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
from tools.generate_title import GLYPHS
R=Path(__file__).resolve().parents[1]
BL=(0,0,0); RED=(255,0,0);Y=(255,255,0);CY=(0,255,255); W=(255,255,255);G=(0,255,0)
im=Image.new('RGB',(256,192),BL);d=ImageDraw.Draw(im)
def word(s,y,scale,color,x=None,gap=None):
 gap=scale if gap is None else gap
 width=len(s)*(5*scale+gap)-gap
 if x is None:x=(256-width)//2
 for ch in s:
  for yy,row in enumerate(GLYPHS[ch]):
   for xx,c in enumerate(row):
    if c=='1':
     d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=color)
  x+=5*scale+gap
 return width
# Single-color 8x8-pixel bands as in old commercial Spectrum cassette games.
# Decorative outer 1px double border that never touches title letters.
for y in (7,8,190,191):
 for x in range(16,240):
  if (x+y)&1==0: im.putpixel((x,y),RED if y<100 else CY)
word('ESF',14,1,CY)
word('GAME OVER',31,3,RED)
d.line([(41,60),(215,60)], fill=Y, width=1)
# V2.1: ESF-01 side-on fighter, taken DIRECTLY from the user's supplied
# blue fighter image. No fabricated mockup: its native 1-bit pixel art is
# baked into the same ROM-free Spectrum .SCR used by the actual game.
# Source crop excludes the surrounding black background, preserving the
# cockpit, swept wings, twin vertical stabilisers and battle-scarred hull.
ship_source = Image.open(R/'assets/ESF01_GAMEOVER_REFERENCIA.jpg').convert('RGB')
ship_crop = ship_source.crop((20,510,814,731))
ship_small = ship_crop.resize((132,38),Image.Resampling.LANCZOS)
# One-pixel JPEG speckles from the supplied poster inflate the RLE data.
# Binary closing removes only sub-3-pixel chips, preserving large hull details.
mask = ship_small.convert('L').point(lambda v: 255 if v>65 else 0).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
# RGB criterion retains the cyan blue fuselage and rejects almost-black gaps,
# giving a monochrome Spectrum-native sprite with real holes/battle damage.
# Image is confined to y=64..115; the score caption moves to y=116.
for py in range(ship_small.height):
 for px in range(ship_small.width):
  r,g,b=ship_small.getpixel((px,py))
  if mask.getpixel((px,py)) and b>70 and g>42 and b>r*1.23:
   im.putpixel((62+px,69+py),CY)
# Tiny separation highlights in white near the cockpit and fuselage.
# Keep the aircraft the focus: no explosion or unrelated symbols.
word('PUNTUACION FINAL',117,1,Y)
# Six score digits are drawn at x=104..151, y=126..132 by the actual Z80.
word('MISION TERMINADA',149,1,W)
# Draw prompt pixels now, but hide in native attribute RAM until 150 50Hz IRQs.
word('PULSA SPACE',168,1,G)
word('2026 TONY C. WARE',183,1,W)
# Native SCR packing into non-linear pixel memory + 768 attrs.
pix=im.load();bitmap=bytearray(6144);attrs=bytearray(768)
ink={BL:0,RED:2,Y:6,CY:5,W:7,G:4};order=(RED,Y,CY,G,W)
for cy in range(24):
 for cx in range(32):
  count={c:0 for c in order}
  for yy in range(cy*8,cy*8+8):
   for xx in range(cx*8,cx*8+8):
    c=pix[xx,yy]
    if c!=BL:count[c]+=1
  best=max(order,key=lambda c:count[c])
  attrs[cy*32+cx]=0x40 | ink[best]
  if cy in (15,16) and 13<=cx<=18:
   attrs[cy*32+cx]=0x45   # Prepared cyan score cells: pixels drawn by Z80.
  # All ten cells of row 21 containing the PULSA SPACE bitmap start hidden.
  if cy==21 and 11<=cx<=20: attrs[cy*32+cx]=0x40
  for yy in range(cy*8,cy*8+8):
   addr=((yy&0xc0)<<5)+((yy&7)<<8)+((yy&0x38)<<2)+cx
   bitmap[addr]=sum((0x80>>bit) for bit in range(8) if pix[cx*8+bit,yy]!=BL)
scr=bytes(bitmap+attrs)
(R/'assets/GAME_OVER_V20.scr').write_bytes(scr)
def pack(data):
 out=bytearray();i=0
 while i<len(data):
  run=1
  while i+run<len(data) and data[i+run]==data[i] and run<255:run+=1
  if run>=4 or data[i]==255:
   out.extend((255,run,data[i]));i+=run
  else:
   out.append(data[i]);i+=1
 return bytes(out)
rle=pack(scr)
(R/'build/gameover_rle_v20.bin').write_bytes(rle)
# Render actual Spectrum attributes (prompt invisible in this proof).
colors=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
out=Image.new('RGB',(256,192));dst=out.load()
for yy in range(192):
 for xx in range(256):
  a=((yy&0xc0)<<5)+((yy&7)<<8)+((yy&0x38)<<2)+(xx>>3)
  bit=(bitmap[a]>>(7-(xx&7)))&1
  attr=attrs[(yy>>3)*32+(xx>>3)]
  dst[xx,yy]=colors[(attr&7) if bit else ((attr>>3)&7)]
out.resize((768,576),Image.Resampling.NEAREST).save(R/'build/V20_GAME_OVER_BLOQUEADO.png')
# Recolour the ten cells of row21, what the IRQ-gated Z80 will do.
for cx in range(11,21):attrs[21*32+cx]=0x44
for yy in range(168,176):
 for xx in range(88,168):
  a=((yy&0xc0)<<5)+((yy&7)<<8)+((yy&0x38)<<2)+(xx>>3)
  bit=(bitmap[a]>>(7-(xx&7)))&1
  attr=attrs[(yy>>3)*32+(xx>>3)]
  dst[xx,yy]=colors[(attr&7) if bit else ((attr>>3)&7)]
out.resize((768,576),Image.Resampling.NEAREST).save(R/'build/V20_GAME_OVER_PULSA_SPACE.png')
print('GAME OVER native SCR',len(scr),'RLE supplement',len(rle),'bytes')
