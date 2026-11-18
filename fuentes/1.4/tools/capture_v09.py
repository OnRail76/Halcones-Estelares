#!/usr/bin/env python3
"""Only executable Z80-derived pixels, not artwork or a mockup."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from mini_z80 import VM,SYM
B=R/'build'
v=VM()
v.run_to(lambda q:q.pc==SYM['main_loop'],steps=400000)
pix={0:(0,0,0),3:(255,0,255),5:(0,255,255),6:(255,255,0)}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',17)
sheet=Image.new('RGB',(690,515),(7,12,23));d=ImageDraw.Draw(sheet)
d.text((20,14),'ESF 48K - 2 FRAMES / DATOS DEL Z80',font=font,fill=(238,245,255))
for i,(name,label,ink) in enumerate((('enemy_needle','FALCON',6),('enemy_blade','RAPTOR',3),('enemy_drone','WRAITH',5))):
 y=60+i*148
 d.text((20,y+20),label,font=font,fill=pix[ink]);d.text((20,y+47),"16 x 16",font=font,fill=(180,195,208))
 for f in (0,1):
  xx=220+f*215
  addr=SYM[name+'_shifted']+f*(8*3*16)
  im=Image.new('RGB',(16,16),(0,0,0))
  for yy in range(16):
   for x in range(16):
    bb=v.m[addr+yy*3+x//8]
    if bb&(128>>(x&7)):im.putpixel((x,yy),pix[ink])
  sheet.paste(im.resize((128,128),Image.Resampling.NEAREST),(xx,y))
  d.text((xx+139,y+55),f'F{f}',font=font,fill=(220,220,220))
  # byte-for-byte check against the manifest source (signed-off by assembler).
  from json import loads
  src=loads((R/'assets/sprites/sprite_manifest.json').read_text())[name]
  want=src['pixel_bytes'] if f==0 else src['frame1_pixel_bytes']
  assert all(v.m[addr+row*3+b]==want[row*2+b] for row in range(16) for b in range(2))
sheet.save(B/'SPRITES_ESF_REAL_Z80_DOS_FRAMES.png')
frames=[]
for t in range(1,81):
 v.keys={'SPACE'}
 v.step();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=450000)
 if t%2==0:
  p=B/f'VM_ACTUAL_{t:03}.png'
  v.render(p,scale=2)
  frames.append(Image.open(p).convert('P',palette=Image.Palette.ADAPTIVE,colors=16))
  if t not in (8,16,24,32,48,64,80):p.unlink()
frames[0].save(B/'ESF_V09_ALETEO_COMBATE_VM.gif',save_all=True,append_images=frames[1:],duration=90,loop=0,optimize=False)
print('Generated atlas (compiled Z80 data) and 40 actual executed RAM frames / GIF')
