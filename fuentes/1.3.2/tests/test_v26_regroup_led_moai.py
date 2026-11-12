#!/usr/bin/env python3
"""V2.6 Z80 execution tests: real IM2 time, magenta boss and three border lamps.
Not a substitute for Fuse; all assertions use memory written by the assembled Z80.
"""
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def tick(v):
    v.keys=set()
    v.step()
    v.run_to(lambda q:q.pc==SYM['main_loop'],steps=2_600_000)
    assert v.sp==0xfff0,hex(v.sp)
    assert [v.m[x] for x in (0xf000,0xf400,0xfdfa,0xff01)]==[0xa5,0x3c,0x5a,0x5a]

def irq(v):
    pc,sp=v.pc,v.sp
    regs,f,ix,iy=list(v.r),v.f,v.ix,v.iy
    v.push(v.pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=2200)
    assert (v.r,v.f,v.ix,v.iy)==(regs,f,ix,iy)

def state(v,i):return v.m[SYM['enemy_slots']+i*6+2]
def y(v,i):return v.m[SYM['enemy_slots']+i*6+1]
def set_rush(v):
    v.set('wave_stage',2)
    v.set('wave_repeat',0)
    v.set('wave_done',0)
    v.set('rush_rest_ticks',0)
    v.set('rush_pause_active',0)
    v.set('enemy_count',6)
    for i in range(6):
        source=SYM['wave_rush']+i*6
        dest=SYM['enemy_slots']+i*6
        v.m[dest:dest+6]=v.m[source:source+6]

# One survivor: it MUST hover high for at least 100 physical 50Hz IRQs.
v=boot_to_game(VM());set_rush(v)
for i in range(1,6):v.m[SYM['enemy_slots']+i*6+2]=0
v.m[SYM['enemy_slots']+1]=166
v.set('shield_invulnerable',140)
tick(v)
assert state(v,0)==5 and y(v,0)<40,(state(v,0),y(v,0))
assert v.val('rush_pause_active')==1 and v.val('rush_rest_ticks')==100
start_y=y(v,0)
for i in range(99):irq(v)
assert v.val('rush_rest_ticks')==1
for i in range(24):
    tick(v)
    assert state(v,0)==5 and y(v,0)==start_y,('regroup cut short',i)
assert v.val('rush_rest_ticks')==1
# Render real screen from the executing VM, and assert native screen = renderer.
v.render(R/'build/V26_REPOSO_KAMIKAZES_Z80.png',scale=3)
for py in range(192):
    ofs=((py&0xc0)<<5)+((py&7)<<8)+((py&0x38)<<2)
    assert v.m[0x4000+ofs:0x4018+ofs]==v.m[0xc000+ofs:0xc018+ofs],('bitmap corruption',py)
irq(v);assert v.val('rush_rest_ticks')==0
tick(v)
assert state(v,0)==1 and v.val('rush_pause_active')==0
assert v.val('wave_done')==0 and v.val('wave_stage')==2
print('PASS one survivor: 100 IM2 IRQ rest, sway at constant height, then attack resumes')

# No timer until ALL surviving attackers return high.
v=boot_to_game(VM());set_rush(v)
for i in range(2,6):v.m[SYM['enemy_slots']+i*6+2]=0
v.m[SYM['enemy_slots']+0*6+2]=5
v.m[SYM['enemy_slots']+0*6+1]=5
v.m[SYM['enemy_slots']+1*6+1]=80
v.set('shield_invulnerable',140)
for i in range(4):tick(v)
assert v.val('rush_pause_active')==0 and v.val('rush_rest_ticks')==0
v.m[SYM['enemy_slots']+1*6+1]=166
tick(v)
assert [state(v,i) for i in (0,1)]==[5,5]
assert v.val('rush_rest_ticks')==100
print('PASS timer starts only AFTER the last living kamikaze returns')

# MOAI, its native 8x8 ink and its TWO red eyes.
v=boot_to_game(VM())
for expected in [(0,1),(1,0),(1,1),(2,0),(2,1),(3,0)]:
    for i in range(10):v.m[SYM['enemy_slots']+6*i+2]=0
    v.set('wave_done',1);v.set('card_ticks',0);tick(v)  # V1.1: sin cartel
    assert (v.val('wave_stage'),v.val('wave_repeat'))==expected
assert v.val('boss_hp')==18
for yy in range(11):
    for xx in range(6):
        addr=0x5829+yy*32+xx
        if addr not in (0x586a,0x586d):
            assert v.m[addr]==0x43,(hex(addr),hex(v.m[addr]))
            assert v.m[addr+0x9900]==0x43,(hex(addr),hex(v.m[addr+0x9900]))
assert v.m[0x586a] in (0x42,0x40) and v.m[0x586d] in (0x42,0x40)
# V1.2: los ojos se encienden justo antes de disparar (temporizador < 10) y se
# apagan el resto del tiempo (antes alternaban por frame_index).
v.set('enemy_fire_cd',6);tick(v)
assert v.m[0x586a]==0x42 and v.m[0x586d]==0x42
v.set('enemy_fire_cd',40);v.set('mouth_ticks',0);tick(v)
assert v.m[0x586a]==0x40 and v.m[0x586d]==0x40
v.render(R/'build/V26_MOAI_MAGENTA_Z80.png',scale=3)
print('PASS magenta MOAI face + independent red/black eye pulses, shadow synchronized')

# Independent LED sequence in real native Spectrum attrs, while bitmap stays fixed.
v=boot_to_game(VM())
lamps=(0x58c0,0x5980,0x5a40)
# V1.2: con el escudo listo el barrido es verde (0x44 encendido, 0x04 apagado).
assert [v.m[x] for x in lamps]==[0x44,0x04,0x04]  # Upper LED initially bright; other lamps dim.
for n,expected in [(8,[0x04,0x44,0x04]),(8,[0x04,0x04,0x44]),(8,[0x04,0x44,0x04]),(8,[0x44,0x04,0x04])]:
    for _ in range(n):tick(v)
    assert [v.m[x] for x in lamps]==expected,([hex(v.m[x]) for x in lamps],expected)
    assert [v.m[x+0x9900] for x in lamps]==expected
print('PASS 3 LEDs top-middle-bottom-middle-top; native/shadow attrs identical')
print('ALL V2.6 REGRESSION TESTS PASSED (headless Z80 only; Fuse pending)')
