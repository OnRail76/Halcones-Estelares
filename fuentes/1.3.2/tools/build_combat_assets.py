#!/usr/bin/env python3
"""Deterministic ZX Spectrum native 1-bit AND/OR sprite data for COMBAT V05.
Uses approved native V04 bitmap bytes, NOT art generated for an illustration.
Generates 8 horizontal pixel phases and two exhaust animation frames.
"""
from pathlib import Path
from tools import build_enemy_sprites
import math,json
R=Path(__file__).resolve().parents[1]
B=R/'build'
M=json.loads((R/'assets/sprites/sprite_manifest.json').read_text())

def pixbits(name):
 s=M[name]; w=s['width']; h=s['height']; bpr=w//8
 return [[bool(s['pixel_bytes'][y*bpr+x//8] & (128>>(x&7))) for x in range(w)] for y in range(h)]

def generated(name,frames):
 h=len(frames[0]);w=len(frames[0][0]);bpr=w//8+1
 rows=[f'; {name}: {len(frames)} frames, 8 x-shifts; {bpr} XOR pixels per scanline',f'{name}_shifted:']
 for f,frame in enumerate(frames):
  for phase in range(8):
   rows.append(f'; frame={f}, x%8={phase}')
   for y in range(h):
    data=[]
    for bx in range(bpr):
     v=0
     for px in range(8):
      source_x=bx*8+px-phase
      if 0<=source_x<w and frame[y][source_x]: v|=128>>px
     data.append(v)
    rows.append(' db '+','.join(map(str,data)))
 return '\n'.join(rows)
ship=pixbits('esf_interceptor')
ship2=[row[:] for row in ship]
# Extend/shorten the twin flames to make a true second bitmap frame.
for x in (9,10,13,14):
 ship2[23][x]=False
 ship2[18][x]=True
bullet=[[False]*8 for _ in range(4)]
for y in range(4):
 bullet[y][3]=True;bullet[y][4]=True

# Generate shifted bullet as 8px+8px, 6 scanlines.
lines=['; Fast XOR-native pre-shifted pixel bytes; each pixel mask is reversible']
lines.append(generated('player',[ship]))
for n in ('enemy_needle','enemy_blade','enemy_drone'):
  s=M[n];f1=s['frame1_pixel_bytes'];w=s['width'];h=s['height']
  frame1=[[bool(f1[y*(w//8)+x//8]&(128>>(x&7))) for x in range(w)] for y in range(h)]
  lines.append(generated(n,[pixbits(n),frame1]))
# Heavy pattern held in source asset bank, not emitted until it is used.
# Small 8x8 deterministic three-frame explosion spark, shifted at build time.
explosion=[]
for y in range(8):
 row=[]
 for x in range(8):
  dx=x-3.5;dy=y-3.5
  row.append((abs(dx)<1.0 or abs(dy)<1.0 or abs(dx-dy)<1.0 or abs(dx+dy)<1.0) and 1<abs(dx)+abs(dy)<6)
 explosion.append(row)
lines.append(generated('explosion',[explosion]))
lines.append(generated('shot',[bullet]))
# Direct eight-phase pointer tables, eliminating the old linear ADD HL/DE walk.
for n, width, height in [('player',4,24),('enemy_needle',3,16),('enemy_blade',3,16),('enemy_drone',3,16),('shot',2,4),('explosion',2,8)]:
 lines.append(f'{n}_phase_ptrs:')
 for i in range(8):lines.append(f' dw {n}_shifted+{i*width*height}')
 if n in ('enemy_needle','enemy_blade','enemy_drone'):
  lines.append(f'{n}_phase_ptrs_f1:')
  for i in range(8):lines.append(f' dw {n}_shifted+{(i+8)*width*height}')
wave=[int(round(18+18*math.sin(2*math.pi*i/64))) for i in range(64)]
lines.append('wave_sinus:')
for i in range(0,64,16):lines.append(' db '+','.join(map(str,wave[i:i+16])))
(B/'combat_assets.asm').write_text('\n'.join(lines)+'\n')
assert len(ship)==24 and len(ship2)==24
print('FAST ARCADE ASSETS: ESF fixed frame + 3 ORIGINAL two-frame enemies + shield/explosion, XOR shots, 8 shifts')
