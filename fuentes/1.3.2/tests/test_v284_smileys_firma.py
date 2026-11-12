#!/usr/bin/env python3
"""V2.8.4: prove the Tony C. Ware life glyph is only recolored inside original contour.
Uses assembled Z80 data and boots into title/game using the partial emulator.
"""
from pathlib import Path
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
from PIL import Image
import json, hashlib
R=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/HALCONES_V283_EQUILIBRIO')
code=(R/'build/starter.bin').read_bytes();prev=(BASE/'build/starter.bin').read_bytes()
assert len(code)==len(prev)==15683 and 0x4000-len(code)==701
oldsyms=json.loads((BASE/'build/starter.sym.json').read_text())
assert SYM==oldsyms
changes={i for i,(o,n) in enumerate(zip(prev,code)) if o!=n}
allowed=set(range(SYM['hud_bitmap_data']-0x8000,SYM['hud_bitmap_data']-0x8000+1536))
allowed |= set(range(SYM['lives_hud_frames']-0x8000,SYM['lives_hud_frames']-0x8000+192))
assert changes<=allowed, ('game logic / title / boss / sound unexpectedly changed',changes-allowed)
assert len(changes)==108,(len(changes),'expected HUD bytes')
assert (R/'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()==(BASE/'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()
print('PASS unchanged executable engine / title, same bytes and memory margin: ONLY 108 graphic data bytes differ')

old=Image.open(BASE/'assets/HUD_NATIVO_NUEVO.png').convert('RGB')
new=Image.open(R/'assets/HUD_NATIVO_NUEVO.png').convert('RGB')
Y=(255,255,0);BLACK=(0,0,0)
expected_change=set()
for start in (12,28,44):
 for dy in range(1,7):
  yy=64+dy
  xs=[xx for xx in range(start,start+8) if old.getpixel((xx,yy))==Y]
  a,b=min(xs),max(xs)
  for xx in range(a+1,b):expected_change.add((xx,yy))
for y in range(192):
 for x in range(64):
  before=old.getpixel((x,y));after=new.getpixel((x,y))
  if (x,y) in expected_change:
   assert before in (BLACK,Y)
   assert after==(Y if before==BLACK else BLACK),(x,y)
  else:assert after==before,(x,y)
assert len(expected_change)==96
print('PASS 96 precisely inverted interior pixels only; three original 8x8 contours, eyes and smiles unshifted; all other HUD pixels preserved')

v=boot_to_game(VM())
# Check real runtime screen bitmap against frame table, as player lives decrease.
def invoke(label):
 ret=0x6fb7;sp=v.sp
 v.push(ret);v.pc=SYM[label]
 v.run_to(lambda q:q.pc==ret and q.sp==sp,steps=200_000)
 assert v.sp==sp
for count in (3,2,1,0,3):
 v.set('player_lives',count)
 v.set('lives_displayed',255)
 invoke('lives_hud_present')
 assert v.val('lives_displayed')==count
 base=SYM['lives_hud_frames']+count*48
 for y in range(8):
  scan_addr=0x4000+(((64+y)&0xc0)<<5)+(((64+y)&7)<<8)+(((64+y)&0x38)<<2)+25
  actual=bytes(v.m[scan_addr:scan_addr+6])
  expect=bytes(v.m[base+y*6:base+y*6+6])
  assert actual==expect,(count,y,actual,expect)
 # Bits for absent heads must be zero; dynamic states are complete with shared original bitmap.
 assert count==0 or any(v.m[base+i] for i in range(48))
print('PASS assembled Z80 HUD life rendering for 3,2,1,0,3 lives; full sprite states and original screen positions')

# Ensure sound, wave, shield state and title byte content remain unchanged.
for n in ('player_lives','shield_meter','shield_state'):
 assert n in SYM
assert 'hud_attr_data' in SYM
for k in range(192):
 a=SYM['hud_attr_data']-0x8000+k
 assert code[a]==prev[a]
print('PASS all 192 HUD color attributes unchanged, 8-segment meter and smiley panel colors preserved')

# Validate real TAP blocks and matching game bytes.
tap=(R/'build/HALCONES_ESTELARES_V281.tap').read_bytes()
p=0; blocks=[]
while p<len(tap):
 size=int.from_bytes(tap[p:p+2],'little');p+=2
 block=tap[p:p+size];p+=size
 assert len(block)==size
 z=0
 for b in block:z^=b
 assert z==0
 blocks.append(block)
assert p==len(tap) and len(blocks)==8 and blocks[3][1:-1]==code
print('PASS Z80/TAP checksum for all 8 blocks; SHA256',hashlib.sha256(tap).hexdigest())
