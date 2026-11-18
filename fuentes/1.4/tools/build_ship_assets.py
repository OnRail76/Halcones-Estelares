#!/usr/bin/env python3
"""Create *actual* 1bpp Z80 sprite + AND masks from native pixel geometry.
No concept-art, fake game screenshot or AI image: only source raster -> bytes.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
R=Path(__file__).resolve().parents[1]
B=R/'build';B.mkdir(exist_ok=True)
S=R/'assets'/'sprites';S.mkdir(exist_ok=True,parents=True)

def mirror_polygon(pts,w):return [(w-1-x,y) for x,y in pts]
def new(w,h):
 im=Image.new('1',(w,h),0)
 return im,ImageDraw.Draw(im)

# Variant D re-engineered as ACTUAL 24x24 ZX bitmap, not an AI sheet.
# Airframe: long tapered MiG-like nose, slender fuselage, dramatically swept
# wings with smooth trailing edge and split twin exhausts. NO red wing motifs.
p,d=new(24,24)
# Central needle and fuselage: symmetrical, no anti-alias pixels.
d.polygon([(11,0),(12,0),(13,3),(14,8),(14,14),(15,17),(15,18),
           (13,18),(13,17),(10,17),(10,18),(8,18),(9,13),(9,8),(10,3)], fill=1)
# Longer, genuinely wing-like leading edges and swept trapezoidal wings.
wing=[(9,9),(10,15),(8,17),(6,19),(3,21),(0,23),
      (0,20),(3,17),(6,13),(8,11)]
d.polygon(wing, fill=1)
d.polygon(mirror_polygon(wing,24), fill=1)
# Wing-root intakes and discreet edge breaks (small, silhouette remains solid).
d.line([(8,12),(9,15)],fill=0,width=1)
d.line(mirror_polygon([(8,12),(9,15)],24),fill=0,width=1)
# ZX-compatible wing 'metal grey': checker-dither interior at true bitmap
# resolution; the white leading/trailing-edge pixels are preserved.
wingmask=p.copy()
for yy in range(12,23):
 for xx in list(range(0,9))+list(range(15,24)):
  if (xx+yy)%2==0 and all(wingmask.getpixel((xx+dx, yy+dy))
      for dx,dy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]
      if 0<=xx+dx<24 and 0<=yy+dy<24):
   d.point((xx,yy),fill=0)
# Pointed front canopy negative slit, intake pair, vertical fuselage accents.
d.rectangle((11,4,12,6),fill=0)
d.point((10,12),fill=0);d.point((13,12),fill=0)
d.line([(10,14),(10,16)],fill=0)
d.line([(13,14),(13,16)],fill=0)
# Left/right engine exhausts only occupy the BOTTOM MIDDLE 8x8 cell.
d.rectangle((9,19,10,21),fill=1)
d.rectangle((13,19,14,21),fill=1)
d.rectangle((9,22,10,23),fill=1)
d.rectangle((13,22,14,23),fill=1)

# Enemy-1: fast needle-interceptor, 16x16
q,d=new(16,16)
d.polygon([(7,0),(8,0),(10,9),(12,11),(15,12),(15,15),(11,14),(9,13),(6,13),(4,14),(0,15),(0,12),(3,11),(5,9)],fill=1)
d.line([(7,6),(7,10)],fill=0);d.line([(8,6),(8,10)],fill=0)
# Enemy-2: wide blade formation ship
r,d=new(16,16)
d.polygon([(7,2),(8,2),(10,5),(14,5),(15,11),(13,13),(10,11),(9,15),(6,15),(5,11),(2,13),(0,11),(1,5),(5,5)],fill=1)
d.point((7,6),fill=0);d.point((8,6),fill=0)
d.line([(2,8),(5,10)],fill=0);d.line([(13,8),(10,10)],fill=0)
# Enemy-3: heavy drone with two nacelles
s,d=new(16,16)
d.polygon([(6,0),(9,0),(11,3),(11,6),(14,5),(15,8),(14,13),(11,14),(10,11),(9,15),(6,15),(5,11),(4,14),(1,13),(0,8),(1,5),(4,6),(4,3)],fill=1)
d.rectangle((7,5,8,7),fill=0)
d.point((3,10),fill=0);d.point((12,10),fill=0)
# Variant D heavy enemy: real 32x24 ZX sprite inspired by B-21 Raider:
# stealth flying wing without visible tall tail, inward-notched rear edge.
t,d=new(32,24)
d.polygon([(15,1),(16,1),(18,4),(21,6),(24,9),(28,12),(31,15),
           (31,17),(28,17),(26,16),(23,17),(21,20),(18,18),
           (16,16),(15,16),(13,18),(10,20),(8,17),(5,16),(3,17),
           (0,17),(0,15),(3,12),(7,9),(10,6),(13,4)],fill=1)
# Swept leading edge and inset panel/engine intakes, both mirrored.
leftcut=[(5,15),(10,10),(12,9),(11,15),(9,17),(6,16)]
d.polygon(leftcut,fill=0)
d.polygon(mirror_polygon(leftcut,32),fill=0)
d.line([(6,13),(11,8),(14,6)],fill=0,width=1)
d.line(mirror_polygon([(6,13),(11,8),(14,6)],32),fill=0,width=1)
# Subtle shadow pattern inside the flying wing, no new ULA ink needed.
heavy_mask=t.copy()
for yy in range(9,20):
 for xx in list(range(0,14))+list(range(18,32)):
  if (xx+yy)%2==0 and all(heavy_mask.getpixel((xx+dx, yy+dy))
      for dx,dy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]
      if 0<=xx+dx<32 and 0<=yy+dy<24):
   d.point((xx,yy),fill=0)
# Pilot/sensor window and twin underbody weapon exhausts.
d.rectangle((15,5,16,8),fill=0)
d.line([(12,14),(14,15)],fill=0,width=1)
d.line([(19,14),(17,15)],fill=0,width=1)
d.rectangle((14,21,17,22),fill=1)
d.rectangle((15,23,16,23),fill=1)

sprites=[
 ('esf_interceptor',p,[[7,5,7],[7,7,7],[7,6,7]]),
 ('enemy_needle',q,[[3,3],[7,7]]),
 ('enemy_blade',r,[[6,6],[2,2]]),
 ('enemy_drone',s,[[5,5],[3,3]]),
 ('enemy_heavy',t,[[7,7,7,7],[7,7,7,7],[7,3,3,7]])
]

def byte_rows(im):
 w,h=im.size
 assert w%8==0
 return [[sum((1<<(7-bit)) for bit in range(8) if im.getpixel((bx*8+bit,y))) for bx in range(w//8)] for y in range(h)]

def as_db(name,im,attrs):
 rows=byte_rows(im);assert len(attrs)==im.height//8 and all(len(a)==im.width//8 for a in attrs)
 lines=[f'; {name} :: {im.width}x{im.height} at 1bpp; pixel and inverse masks interleaved',f'{name}_width: db {im.width}',f'{name}_height: db {im.height}',f'{name}_pixels_masked:']
 for row in rows:
  packed=[]
  for v in row:packed+=[255^v,v]
  lines.append(' db '+','.join(str(v) for v in packed))
 lines.append(f'{name}_attributes:')
 for a in attrs:lines.append(' db '+','.join(str(64|v) for v in a))
 return '\n'.join(lines)+'\n',rows

manifest={}; out=['; GRIT ENGINE / ESF : ZX Spectrum 48K native sprite atlas v0.4 (Variant D true-native)']
for name,im,attrs in sprites:
 a,rows=as_db(name,im,attrs);out.append(a)
 im.convert('1').save(S/(name+'.png'))
 manifest[name]={'width':im.width,'height':im.height,'bytes_per_row':im.width//8,'pixel_bytes':[b for row in rows for b in row],'mask_bytes':[b^255 for row in rows for b in row],'ink':attrs,'purpose':'integrated in static Z80 scroll demonstrator' if name in ('esf_interceptor','enemy_heavy') else 'code-ready unchanged asset, not yet spawned'}
(B/'ship_assets.asm').write_text('\n'.join(out))
(S/'sprite_manifest.json').write_text(json.dumps(manifest,indent=2))

# Reference sheet: visualizes EXACT same pixel bytes written above, with
# Sinclair hardware cell attributes. NOT a screenshot from an emulator.
PALETTE=[(0,0,0),(0,0,205),(205,0,0),(205,0,205),(0,205,0),(0,205,205),(205,205,0),(205,205,205)]
BRIGHT=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
def raw_color_sprite(im,attrs):
 w,h=im.size;pixels=byte_rows(im)
 pic=Image.new('RGB',(w,h),(0,0,0))
 for y in range(h):
  for x in range(w):
   if pixels[y][x//8]&(128>>(x%8)):pic.putpixel((x,y),BRIGHT[attrs[y//8][x//8]])
 return pic
# Neutral sprite asset contact sheet, programmatic labels in outer sheet
sheet=Image.new('RGB',(680,375),(8,13,25));dr=ImageDraw.Draw(sheet)
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',14)
except OSError:font=ImageFont.load_default()
locations=[(14,14),(260,14),(465,14),(260,198),(465,198)]
for (name,im,attrs),(x,y) in zip(sprites,locations):
 pic=raw_color_sprite(im,attrs).resize((im.width*6,im.height*6),Image.Resampling.NEAREST)
 sheet.paste(pic,(x,y+26));dr.text((x,y),f'{name}  {im.width}x{im.height}',font=font,fill=(210,225,245))
sheet.save(B/'ATLAS_SPRITES_DATOS_REALES.png')
print('ASSET_BUILD: 5 authentic 1bpp sprites + AND masks / deterministic ASM / 8x8 attribute colors')
