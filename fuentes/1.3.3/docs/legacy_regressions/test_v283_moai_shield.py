#!/usr/bin/env python3
"""V2.8.3: real assembled Z80 branch tests in the bundled partial emulator.
Does not claim full Fuse cycle/timing/sound validation.
"""
from pathlib import Path
import hashlib, json
from mini_z80 import VM,SYM

R=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/HALCONES_V282_KAMIKAZES_SUAVES')

def invoke(v,label,maxsteps=100_000):
    ret=0x6fb7
    sp=v.sp
    v.push(ret)
    v.pc=SYM[label]
    v.run_to(lambda q:q.pc==ret and q.sp==sp,steps=maxsteps)
    assert v.sp==sp,(label,'stack imbalanced')

# V1.1 (sustituye la regla V2.8.3 por frame_index): el MOAI dispara con un
# temporizador en ticks de 25/s -48 ticks en la fase 01, 28 en la siguiente y
# 3 menos por cada MOAI mas- y los ojos se alternan SIEMPRE, uno y otro.
def boss_volley(cycle,ticks):
    v=VM();v.sp=0xfff0
    v.set('wave_stage',3);v.set('wave_cycle',cycle);v.set('boss_hp',18)
    v.set('enemy_fire_cd',0);v.set('boss_eye',0)
    slots=SYM['enemy_bullet_slots'];shots=[]
    for t in range(ticks):
        v.m[slots:slots+9]=bytes(9)
        invoke(v,'enemy_bullet_update')
        if v.m[slots+2]:shots.append((t,v.m[slots],v.m[slots+1]))
    return shots
for cycle,period in ((0,48),(1,28),(2,25),(4,19)):
    shots=boss_volley(cycle,period*4+3)
    assert [t for t,x,y in shots]==[0,period+1,2*(period+1),3*(period+1),4*(period+1)][:len(shots)] and len(shots)>=4,(cycle,shots)
    assert [x for t,x,y in shots]==[109,85,109,85,109][:len(shots)] and all(y==48 for t,x,y in shots),(cycle,shots)
for cycle in (0,1):
    v=VM();v.sp=0xfff0;v.set('wave_stage',3);v.set('wave_cycle',cycle)
    v.set('boss_hp',0);v.set('enemy_fire_cd',0)
    slots=SYM['enemy_bullet_slots'];v.m[slots:slots+9]=bytes(9)
    invoke(v,'enemy_bullet_update')
    assert not any(v.m[slots+i*3+2] for i in range(3))
print('PASS V1.1 MOAI: cadencia en tiempo real (48/28/25/19 ticks), ojos alternos, sin disparos tras su derrota')

# Full exact 50Hz countdown, including active, 38/37 eight segments, state READY.
from boot_v15 import boot_to_game
v=boot_to_game(VM());assert v.val('shield_state')==0 and v.val('shield_meter')==8
v.keys={'A'}
invoke(v,'input_poll',maxsteps=30_000)   # V1.1: los mandos se leen una vez por tick
invoke(v,'shield_try_activate',maxsteps=30_000)
assert v.val('shield_state')==1 and v.val('shield_meter')==0
assert v.m[SYM['shield_timer']:SYM['shield_timer']+2]==bytes([150,0])

# Invoke actual IM2 handler to RETI to check it conserves full registers.
def irq():
    pc=v.pc;sp=v.sp;regs=tuple(v.r);f=v.f;ix=v.ix;iy=v.iy
    v.push(pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=1000)
    assert tuple(v.r)==regs and v.f==f and v.ix==ix and v.iy==iy and v.sp==sp
for tick in range(149):
    irq()
    assert v.val('shield_state')==1 and v.val('shield_meter')==0,tick
irq()
assert v.val('shield_state')==2 and v.val('shield_meter')==0
segment_ends=[38,75,113,150,188,225,263,300]
for t in range(1,301):
    irq()
    should=sum(t>=n for n in segment_ends)
    assert v.val('shield_meter')==should,(t,should,v.val('shield_meter'))
    assert v.val('shield_state')==(0 if t==300 else 2),(t,v.val('shield_state'))
    rem=300-t
    assert v.m[SYM['shield_timer']:SYM['shield_timer']+2] == bytes([rem&255, rem>>8]),(t,'timer')
assert v.val('shield_ready_pending')==1
assert v.val('shield_meter')==8
v.keys=set();invoke(v,'input_poll');invoke(v,'shield_try_activate');v.keys={'A'};invoke(v,'input_poll');invoke(v,'shield_try_activate')  # V1.1
assert v.val('shield_state')==1 and v.val('shield_meter')==0
print('PASS actual IM2, full 150 active IRQ + 300 recharge IRQ: 38/37*4 -> exactly eight original stages, reg/SP unchanged, subsequent activation')

# No other existing sources/assets or title modified, preserve source-level game loop.
changed=[]
for folder in ('src','tools','assets'):
    for p in (R/folder).rglob('*'):
        if not p.is_file() or p.suffix=='.pyc' or '__pycache__' in p.parts:continue
        base=BASE/p.relative_to(R)
        assert base.is_file(),('source added outside test',p)
        if p.read_bytes()!=base.read_bytes():changed.append(str(p.relative_to(R)))
assert set(changed)=={'src/arcade_rules_v18.asm','tools/generate_assets.py','assets/HUD_NATIVO_NUEVO.png'},('unrequested source modification',changed)
assert (R/'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()==(BASE/'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()
print('PASS only intentional V2.8.3 MOAI/shield source change plus V2.8.4 signature generator/PNG; original title and all other assets preserved')
# Verify resulting program fits existing memory map and all 8 TAP blocks checksum.
code=(R/'build/starter.bin').read_bytes()
assert len(code)<0x4000
n=(R/'build/HALCONES_ESTELARES_V281.tap').read_bytes()
p=0;blocks=[]
while p<len(n):
    length=int.from_bytes(n[p:p+2],'little');p+=2
    b=n[p:p+length];p+=length
    assert len(b)==length and __import__('functools').reduce(int.__xor__,b,0)==0
    blocks.append(b)
assert p==len(n) and len(blocks)==8 and blocks[3][1:-1]==code
print('PASS TAP 8 blocks XOR integrity; code=',len(code),'free before C000=',0x4000-len(code),'SHA=',hashlib.sha256(n).hexdigest())
