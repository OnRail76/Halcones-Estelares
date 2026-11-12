#!/usr/bin/env python3
"""V2.7 tests on the assembled Z80: LED eye pixel fill and Jupiter relocation.
Read-only comparison with V2.6 release assets. Fuse remains authoritative.
"""
from pathlib import Path
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
import hashlib
R=Path(__file__).resolve().parents[1]
OLD=R.parent/'HALCONES_V26.tap'
# Optional verification when the archived V2.6 release is present alongside this bank.
# The V2.7 test suite must also work from a standalone extracted ZIP.
if OLD.exists():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()=='2f144103cac2aa5782d41393736ec6dbd43dbe8734b91d56ecb5a817bfac49e8'

def tick(v):
    v.keys=set(); v.step();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=2600000)
    assert v.sp==0xfff0 and [v.m[x] for x in (0xf000,0xf400,0xfdfa,0xff01)]==[0xa5,0x3c,0x5a,0x5a]

def check_bitmap(v):
    for y in range(192):
        off=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)
        assert v.m[0x4000+off:0x4018+off]==v.m[0xc000+off:0xc018+off],('dirty screen row',y)

def enter_boss(v):
    for stage,repeat in [(0,1),(1,0),(1,1),(2,0),(2,1),(3,0)]:
        for i in range(10):v.m[SYM['enemy_slots']+6*i+2]=0
        v.set('wave_done',1);v.set('card_ticks',0);tick(v)  # V1.1: sin cartel
        assert (v.val('wave_stage'),v.val('wave_repeat'))==(stage,repeat)
    assert v.val('boss_hp')==18

# Native source pixel changes stay strictly inside the two original red 8x8 eye cells.
orig=Path(__file__).resolve().parents[1]/'assets'/'MOAI_REFERENCIA_USUARIO.jpg'
assert orig.exists()
from PIL import Image
im=Image.open(R/'build/MOAI_ORIGINAL_REDUCIDO_48x88.png').convert('L')
new=(R/'build/moai_bitmap_v19.bin').read_bytes()
changed=[]
for y in range(88):
    for x in range(48):
        before=im.getpixel((x,y))>128
        after=bool(new[y*6+x//8] & (128>>(x%8)))
        if before!=after:
            assert not before and after
            assert 18<=y<=23 and (8<=x<=15 or 32<=x<=39), (x,y)
            changed.append((x,y))
assert len(changed)==26,changed
print('PASS 26 added LED pixels only inside the original two red attribute cells')

v=boot_to_game(VM());enter_boss(v)
for colrow in range(7):
    for col in range(16,23):
        for screen in (0x5800,0xf100):
            assert v.m[screen+12*32+16 + colrow*32+(col-16)]==0x45, ('Jupiter cyan attr',screen,colrow,col)
# In old location x128..183 y32..87, the entire original reference occupied 56 rows;
# now native source must occur at x128..183 y96..151 in immutable background.
pixels=(R/'build/jupiter_bitmap_v20.bin').read_bytes()
assert len(pixels)==56*7
for y in range(96,152):
    offset=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)
    actual=v.m[0xd800+offset+16:0xd800+offset+23]
    expect=pixels[(y-96)*7:(y-95)*7]
    assert actual==expect,('Jupiter placed incorrectly',y,actual,expect)
print('PASS Jupiter 56x56 relocated exactly to (128,96), colour and immutable bitmap agree')

v.set('enemy_fire_cd',6);tick(v)   # V1.2: ojos encendidos antes del disparo
assert (v.m[0x586a],v.m[0x586d])==(0x42,0x42)
assert (v.m[0xf16a],v.m[0xf16d])==(0x42,0x42)
check_bitmap(v)
v.render(R/'build/V27_MOAI_LED_JUPITER_BAJO_Z80.png',scale=3)
# Normal magenta cell adjacent to eye stays unmodified.
assert v.m[0x586b]==0x43 and v.m[0x586c]==0x43
v.set('enemy_fire_cd',40);v.set('mouth_ticks',0);tick(v)   # V1.2: apagados
assert (v.m[0x586a],v.m[0x586d])==(0x40,0x40)
assert (v.m[0xf16a],v.m[0xf16d])==(0x40,0x40)
check_bitmap(v)
v.render(R/'build/V27_MOAI_OJOS_APAGADOS_Z80.png',scale=3)
print('PASS red LEDs on/off with black sockets and unchanged magenta face; compositor stays coherent')

# Victory must remove Jupiter at NEW location and restore colour to stars.
v.set('boss_hp',0);v.set('boss_death_left',0)
v.step();v.run_to(lambda q:q.pc==SYM['phase_interlude_wait'],steps=2600000)
for row in range(7):
 for col in range(16,23):
  idx=12*32+col+row*32
  assert v.m[0xf100+idx]==0x47, ('shadow Jupiter colour not cleared',row,col,hex(v.m[0xf100+idx]))
for y in range(96,152):
    off=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)
    assert v.m[0xd800+off+16:0xd800+off+23]==b'\0'*7, ('Jupiter not erased',y)
assert v.val('gameover_timer')==150 and v.val('phase_number')==2
print('PASS boss defeated: Jupiter erased in all 56 rows, 7x7 attributes restored, phase interlude 150 ticks')
print('ALL V2.7 Z80 BOSS SCENE TESTS PASSED (Fuse pending)')
