#!/usr/bin/env python3
"""Regression: assembled ZX title, original yellow letterforms, integrated beak, ARC pulse."""
from pathlib import Path
from mini_z80 import VM,SYM
import hashlib,functools
R=Path(__file__).resolve().parents[1]
ref=(R/'assets/TITULO_01_IMPERIAL_SIN_PICO.scr').read_bytes()
v27=(R/'assets/TITULO_V27_ORIGINAL_INTACTO.scr').read_bytes()
new=(R/'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()
assert len(ref)==len(new)==6912
assert ref[:6144]!=new[:6144]
assert new[6144:6144+10*32]==v27[6144:6144+10*32], 'Original V2.7 title ATTRIBUTES must be byte-exact!'
assert new[6144+10*32:6144+13*32]==ref[6144+10*32:6144+13*32]
assert ref[6144+14*32:]==new[6144+14*32:]
# EXACT V2.7 title text + subtitle and rest unchanged; character bitmap & attrs through y=103.
for y in list(range(0,104))+list(range(112,192)):
    a=((y&0xC0)<<5)+((y&7)<<8)+((y&0x38)<<2)
    assert new[a:a+32]==(v27 if y<80 else ref)[a:a+32], ('Non-beak bitmap changed',y)
for y in range(104,112):
    a=((y&0xC0)<<5)+((y&7)<<8)+((y&0x38)<<2)
    for xbyte in range(32):
        if xbyte not in (15,16):
            assert new[a+xbyte]==ref[a+xbyte],('Outside beak cell modified',y,xbyte)
for j,(a,b) in enumerate(zip(new[6144:],ref[6144:])):
    assert a==(v27[6144+j] if j < 10*32 else b) or j in ((13*32+15),(13*32+16)),('Non-beak color modified',j)
print('PASS V2.7 original title 80 scanlines and attributes BYTE-EXACT; complete IMPERIAL bird below')
# Assemble executable, boot through title and test live animation exactly every 50Hz HALT.
v=VM()
v.run_to(lambda q:q.pc==SYM['title_wait_release'],steps=1_000_000)
assert bytes(v.m[0x4000:0x5b00])==new
v.keys=set()
v.run_to(lambda q:q.pc==SYM['title_wait_press'],steps=10000)
origbm=bytes(v.m[0x4000:0x5800]); origatr=bytes(v.m[0x5800:0x5b00]); source_attr=bytes(v.m[0x7d40:0x7e20])
assert source_attr==new[6144+32:6144+8*32]
yellow_cells=sum((x&7)==6 for x in origatr[32:256]);assert yellow_cells>100

def frames(num):
    for i in range(num):
        assert v.pc==SYM['title_wait_press'],(i,hex(v.pc))
        v.step()
        v.run_to(lambda q:q.pc==SYM['title_wait_press'],steps=15000)

def check_phase(p):
    a=bytes(v.m[0x5800:0x5b00]);
    assert bytes(v.m[0x4000:0x5800])==origbm,'Original font or hawk bitmap changed by pulse!'
    assert a[:32]==origatr[:32] and a[256:]==origatr[256:],'Subtitle or other text was recolored!'
    for col,(got,orig) in enumerate(zip(a[32:256],origatr[32:256])):
        expected=0x47 if (p&1 and orig&7==6) else orig
        assert got==expected,(p,col,hex(got),hex(expected))
    assert v.m[SYM['title_pulse_phase']]==p

check_phase(0)
for duration,phase in ((75,1),(6,2),(9,3),(3,0),(75,1)):
    frames(duration);check_phase(phase)
print('PASS native Z80 double arcade pulse: 75/yellow -> 6/white -> 9/yellow -> 3/white -> 75/yellow')
# Test boot and legacy beeper precisely, no input system change.
v.keys={'SPACE'}
v.run_to(lambda q:q.pc==SYM['title_wait_start_release'],steps=10000)
v.keys=set()
v.run_to(lambda q:q.pc==SYM['main_loop'],steps=900000)
assert v.sp==0xfff0 and v.im==2
oldwrites=v.port_writes;sp=v.sp;ret=v.pc
v.push(ret);v.pc=SYM['beep_enemy_destroy']
v.run_to(lambda q:q.pc==ret and q.sp==sp,steps=10000)
assert v.port_writes-oldwrites==14
# frame relocated immutable check
import json
frame=json.loads((R/'build/frame_manifest_v17.json').read_text())
assert v.m[0x7bc0:0x7d40]==bytes(frame['bitmap'])
print('PASS gameplay starts; brief 14 OUT blip retained; frame resource exact; IM2/SP intact')
# Binary reproducibility + valid TAP blocks
n=(R/'build/HALCONES_ESTELARES_V281.tap').read_bytes()
p=0;blocks=[]
while p<len(n):
    l=int.from_bytes(n[p:p+2],'little');p+=2
    block=n[p:p+l];p+=l
    assert len(block)==l and functools.reduce(int.__xor__,block,0)==0
    blocks.append(block)
assert len(blocks)==8 and p==len(n)
assert blocks[3][1:-1]==(R/'build/starter.bin').read_bytes()
print('PASS V281 TAP integrity and main Z80 segment identical to assembled code')
